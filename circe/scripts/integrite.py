"""CIRCÉ — les outils du logiciel sont-ils encore ceux que CDOW a livrés ?

  python integrite.py verifier            dit ce qui a été modifié, ajouté ou retiré dans le plugin (code de sortie 1 si écart)
  python integrite.py verifier --court    une seule ligne, pour le démarrage
  python integrite.py sceller             (CDOW seulement) écrit integrite.json et donne l'empreinte à signer

Pourquoi : un acheteur peut réutiliser CIRCÉ comme il veut — ses projets, ses schémas, ses réglages — mais s'il modifie un
outil du logiciel (par exemple pour ne plus être relancé par le système immunitaire), le logiciel ne fait plus ce qui est
vendu, et personne ne s'en aperçoit. Essai du 27/11/2026 : une ligne ajoutée dans `preuve.py` éteint le système immunitaire,
et rien ne le signalait.

Ce que ce contrôle NE fait pas : il n'empêche personne de modifier ses propres fichiers (c'est son ordinateur) et il ne
bloque jamais une session. Il DIT l'écart, et rappelle que `claude plugin update circe@circe-cdow` remet la version d'origine.
La seule garantie forte est la signature de CDOW : un client peut refabriquer le relevé, il ne peut pas le signer
(clé privée hors du plugin et hors du serveur, voir signature.py).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(ICI))

RELEVE = RACINE / "integrite.json"
SUFFIXES = {".py", ".md", ".json", ".txt"}
EXCLUS_DOSSIERS = {"tests", "__pycache__", ".circe", ".git"}
COMMANDE_REMISE = "claude plugin update circe@circe-cdow"


def a_retenir(chemin: Path, racine: Path = RACINE) -> bool:
    if chemin.suffix.lower() not in SUFFIXES:
        return False
    if ".backup-" in chemin.name or chemin.name == RELEVE.name:
        return False
    return not (set(chemin.relative_to(racine).parts) & EXCLUS_DOSSIERS)


def empreinte_fichier(chemin: Path) -> str:
    """Empreinte d'un fichier livré, insensible aux fins de ligne.

    Faille trouvée par le cerveau le 27/11/2026 : une installation depuis GitHub sous Windows reçoit les fichiers en
    CRLF (Git convertit par défaut, `core.autocrlf=true`) alors que la source est en LF. Mesuré sur le paquet signé :
    23 fichiers « modifiés » alors que rien n'avait changé — l'alerte aurait crié à chaque démarrage chez CHAQUE client
    Windows, et une alerte qui crie pour rien, personne ne la lit. Le contenu d'un fichier texte est donc normalisé
    (CRLF et CR isolés → LF) avant d'être haché. Un vrai changement, lui, se voit toujours.
    """
    octets = chemin.read_bytes()
    if chemin.suffix.lower() in SUFFIXES:
        octets = octets.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(octets).hexdigest()


def relever(racine: Path = RACINE) -> dict[str, str]:
    """Le relevé des fichiers livrés : chemin relatif (en barres obliques) -> empreinte."""
    sortie = {}
    for f in sorted(racine.rglob("*")):
        if f.is_file() and a_retenir(f, racine):
            sortie[f.relative_to(racine).as_posix()] = empreinte_fichier(f)
    return sortie


def corps(nom: str, version: str, fichiers: dict[str, str]) -> str:
    return json.dumps({"nom": nom, "version": version, "fichiers": fichiers}, sort_keys=True, ensure_ascii=False)


def empreinte_du_releve(nom: str, version: str, fichiers: dict[str, str]) -> str:
    return hashlib.sha256(corps(nom, version, fichiers).encode("utf-8")).hexdigest()


def version_du_plugin(racine: Path = RACINE) -> str:
    try:
        return str(json.loads((racine / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")).get("version", ""))
    except (OSError, ValueError):
        return ""


def sceller(racine: Path = RACINE) -> dict:
    fichiers = relever(racine)
    version = version_du_plugin(racine)
    releve = {"nom": "circe", "version": version, "fichiers": fichiers,
              "empreinte": empreinte_du_releve("circe", version, fichiers), "signature": ""}
    chemin = racine / RELEVE.name
    chemin.write_text(json.dumps(releve, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"releve": str(chemin), "fichiers": len(fichiers), "version": version,
            "empreinte_a_signer": releve["empreinte"],
            "suite": "Signer cette empreinte avec la clé de CDOW (nom « circe », la version ci-dessus), "
                     "puis recopier la signature dans le champ « signature » du relevé."}


def etat_signature(releve: dict) -> str:
    sig = (releve.get("signature") or "").strip()
    if not sig:
        return "absente"
    try:
        import signature  # noqa: PLC0415 (même dossier)
        bonne = signature.valide(releve.get("nom", "circe"), releve.get("version", ""), releve.get("empreinte", ""), sig)
    except Exception:                       # noqa: BLE001 — un contrôle ne doit jamais faire tomber la session
        return "invérifiable"
    return "valide" if bonne else "INVALIDE"


def verifier(racine: Path = RACINE) -> dict:
    chemin = racine / RELEVE.name
    try:
        releve = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"intact": True, "releve": "absent",
                "note": "aucun relevé d'origine dans cette version : rien à comparer."}
    attendus: dict[str, str] = releve.get("fichiers", {})
    actuels = relever(racine)
    modifies = sorted(f for f, h in attendus.items() if f in actuels and actuels[f] != h)
    absents = sorted(f for f in attendus if f not in actuels)
    ajoutes = sorted(f for f in actuels if f not in attendus)
    sig = etat_signature(releve)
    recalculee = empreinte_du_releve(releve.get("nom", "circe"), releve.get("version", ""), attendus)
    releve_touche = recalculee != releve.get("empreinte")
    # Une signature absente ou fausse compte comme un écart : sinon il suffit de vider le champ pour faire taire
    # l'alerte (point relevé par le cerveau le 27/11). « absente » n'est un écart que si quelqu'un l'a retirée d'un
    # relevé qui devait l'avoir : une copie de travail non signée le dit aussi, et c'est voulu — elle n'est pas officielle.
    return {"intact": not (modifies or absents or ajoutes or releve_touche or sig != "valide"), "modifies": modifies,
            "absents": absents, "ajoutes": ajoutes, "signature": sig, "releve_modifie": releve_touche,
            "version": releve.get("version", ""), "fichiers_verifies": len(attendus)}


def ligne_courte(r: dict) -> str:
    if r.get("releve") == "absent" or r.get("intact"):
        return ""
    quoi = []
    if r.get("modifies"):
        quoi.append(f"{len(r['modifies'])} outil(s) modifié(s) : " + ", ".join(r["modifies"][:3]))
    if r.get("ajoutes"):
        quoi.append(f"{len(r['ajoutes'])} fichier(s) ajouté(s)")
    if r.get("absents"):
        quoi.append(f"{len(r['absents'])} fichier(s) retiré(s)")
    if r.get("releve_modifie"):
        quoi.append("le relevé d'origine lui-même a été réécrit")
    if r.get("signature") == "absente":
        quoi.append("le relevé n'est pas signé par CDOW : cette copie n'est pas une version officielle")
    if r.get("signature") == "invérifiable":
        quoi.append("la signature n'a pas pu être vérifiée sur ce poste")
    if r.get("signature") == "INVALIDE":
        quoi.append("la signature de CDOW ne correspond plus")
    return ("[CIRCÉ, intégrité : " + " ; ".join(quoi) + ". Le logiciel ne fait plus exactement ce qui est vendu. "
            f"Pour remettre la version d'origine : `{COMMANDE_REMISE}`. "
            "Dis-le à l'utilisateur en une ligne, sans le bloquer.]")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="integrite.py", description="Les outils de CIRCÉ sont-ils ceux d'origine ?")
    sous = p.add_subparsers(dest="quoi", required=True)
    v = sous.add_parser("verifier")
    v.add_argument("--court", action="store_true", help="une ligne, pour le démarrage")
    sous.add_parser("sceller", help="CDOW seulement : écrire le relevé d'origine")
    a = p.parse_args(argv)
    if a.quoi == "sceller":
        print(json.dumps(sceller(), ensure_ascii=False, indent=1))
        return 0
    r = verifier()
    if a.court:
        ligne = ligne_courte(r)
        if ligne:
            print(ligne)
    else:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0 if r.get("intact") else 1


if __name__ == "__main__":
    sys.exit(main())
