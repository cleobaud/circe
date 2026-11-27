"""CIRCÉ — Sortie vers les automatisations de l'utilisateur (n8n, Make, Zapier, son propre outil).

  python sortie.py brancher <adresse https du webhook>     enregistre l'adresse (sur ce PC, hors du projet)
  python sortie.py debrancher                              oublie l'adresse
  python sortie.py etat                                     dit si une adresse est branchée (masquée)
  python sortie.py livrer --type video --titre "<titre>" --fichiers <f1> [<f2> ...] [--texte "<légende>"] [--reseau tiktok] [--essai]

`livrer` écrit TOUJOURS une fiche JSON dans `<projet>/.circe/sorties/`, puis l'envoie au webhook s'il y en a un branché.
À n'utiliser qu'APRÈS la validation du livrable par l'utilisateur. C'est l'automatisation de l'utilisateur qui publie, jamais CIRCÉ.
La fiche contient : la version de CIRCÉ, le type, le titre, les chemins des fichiers (pas leur contenu), leur taille, la légende,
le réseau visé et l'heure. Le contenu des fichiers ne part que sur demande (option --joindre, 100 Mo au plus) : sinon l'automatisation les reprend sur le PC ou dans un dossier partagé.
L'adresse du webhook est gardée dans `~/.circe/connexions.json` (jamais dans le projet, qui peut être partagé ou versionné).
Bibliothèque standard seulement.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent
TYPES = ("video", "image", "site", "texte", "objet-3d", "document", "autre")
DELAI_S = 10


def version() -> str:
    try:
        return json.loads((ICI / "config.json").read_text(encoding="utf-8")).get("version", "?")
    except (OSError, ValueError):
        return "?"


def fichier_connexions() -> Path:
    d = Path.home() / ".circe"
    d.mkdir(exist_ok=True)
    return d / "connexions.json"


def adresse_branchee() -> str:
    try:
        return json.loads(fichier_connexions().read_text(encoding="utf-8")).get("webhook", "")
    except (OSError, ValueError):
        return ""


def masquer(adresse: str) -> str:
    m = re.match(r"^(https?://[^/]+)", adresse)
    return (m.group(1) + "/…") if m else "…"


def brancher(adresse: str) -> str:
    adresse = adresse.strip()
    locale = re.match(r"^http://(127\.0\.0\.1|localhost)(:\d+)?/", adresse)
    if not (adresse.startswith("https://") or locale):
        raise SystemExit("adresse refusée : https:// obligatoire (http:// seulement pour 127.0.0.1 ou localhost)")
    fichier_connexions().write_text(json.dumps({"webhook": adresse}), encoding="utf-8")
    return masquer(adresse)


def fiche(type_: str, titre: str, fichiers: list[str], texte: str, reseau: str, essai: bool) -> dict:
    projet = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    liste = []
    for f in fichiers:
        p = Path(f).expanduser()
        p = p if p.is_absolute() else projet / p
        if not p.exists():
            raise SystemExit(f"fichier introuvable : {f}")
        liste.append({"chemin": str(p.resolve()), "nom": p.name, "octets": p.stat().st_size})
    return {"source": "circe", "version": version(), "essai": essai, "type": type_, "titre": titre.strip(),
            "fichiers": liste, "texte": texte.strip(), "reseau": reseau.strip(), "projet": projet.name,
            "cree_le": time.strftime("%Y-%m-%dT%H:%M:%S%z")}


MAX_JOINDRE = 100 * 1024 * 1024


def multipart(donnees: dict) -> tuple[bytes, str]:
    """Corps multipart/form-data : un champ « fiche » (le JSON) et chaque fichier en pièce jointe (fichier_1, fichier_2…).
    C'est ce qu'attend le nœud Webhook de n8n (données binaires), comme Make et Zapier."""
    limite = "circe-" + os.urandom(12).hex()
    morceaux = [f"--{limite}\r\nContent-Disposition: form-data; name=\"fiche\"\r\nContent-Type: application/json; charset=utf-8\r\n\r\n".encode()
                + json.dumps(donnees, ensure_ascii=False).encode("utf-8") + b"\r\n"]
    for i, f in enumerate(donnees["fichiers"], 1):
        nom = f["nom"].replace('"', "")
        morceaux.append(f"--{limite}\r\nContent-Disposition: form-data; name=\"fichier_{i}\"; filename=\"{nom}\"\r\n"
                        f"Content-Type: application/octet-stream\r\n\r\n".encode() + Path(f["chemin"]).read_bytes() + b"\r\n")
    morceaux.append(f"--{limite}--\r\n".encode())
    return b"".join(morceaux), f"multipart/form-data; boundary={limite}"


def envoyer(adresse: str, donnees: dict, ouvrir=urllib.request.urlopen, joindre: bool = False) -> str:
    if joindre:
        if sum(f["octets"] for f in donnees["fichiers"]) > MAX_JOINDRE:
            return "fichiers trop lourds pour être joints (plus de 100 Mo) : utilisez un dossier partagé ; la fiche reste dans .circe/sorties/"
        corps, type_corps = multipart(donnees)
    else:
        corps, type_corps = json.dumps(donnees, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8"
    req = urllib.request.Request(adresse, data=corps, method="POST", headers={"Content-Type": type_corps, "User-Agent": "circe-sortie"})
    try:
        with ouvrir(req, timeout=DELAI_S * (6 if joindre else 1)) as r:
            return f"envoyé (réponse {getattr(r, 'status', 200)})"
    except urllib.error.HTTPError as e:
        return f"refusé par l'automatisation (réponse {e.code})"
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        return f"envoi impossible ({type(e).__name__}) : la fiche reste dans .circe/sorties/"


def livrer(a, ouvrir=urllib.request.urlopen) -> dict:
    donnees = fiche(a.type, a.titre, a.fichiers, a.texte, a.reseau, a.essai)
    joindre = bool(getattr(a, "joindre", False))
    donnees["fichiers_joints"] = joindre
    dossier = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()) / ".circe" / "sorties"
    dossier.mkdir(parents=True, exist_ok=True)
    simple = unicodedata.normalize("NFKD", a.titre).encode("ascii", "ignore").decode().lower()
    nom = time.strftime("%Y%m%d-%H%M%S") + "-" + (re.sub(r"[^a-z0-9]+", "-", simple).strip("-")[:40] or "livrable") + ".json"
    (dossier / nom).write_text(json.dumps(donnees, ensure_ascii=False, indent=1), encoding="utf-8")
    adresse = adresse_branchee()
    envoi = envoyer(adresse, donnees, ouvrir, joindre) if adresse else "aucune automatisation branchée : rien n'est parti"
    return {"fiche": str(dossier / nom), "envoi": envoi}


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="sortie.py", description="Sortie CIRCÉ vers les automatisations")
    s = p.add_subparsers(dest="commande", required=True)
    s.add_parser("brancher").add_argument("adresse")
    s.add_parser("debrancher")
    s.add_parser("etat")
    pl = s.add_parser("livrer")
    pl.add_argument("--type", choices=TYPES, required=True)
    pl.add_argument("--titre", required=True)
    pl.add_argument("--fichiers", nargs="+", required=True)
    pl.add_argument("--texte", default="")
    pl.add_argument("--reseau", default="")
    pl.add_argument("--essai", action="store_true", help="marque la fiche comme un essai (l'automatisation peut l'ignorer)")
    pl.add_argument("--joindre", action="store_true",
                    help="joint aussi le CONTENU des fichiers (100 Mo au plus), pour une automatisation qui tourne ailleurs ; seulement si l'utilisateur l'a demandé")
    a = p.parse_args(argv)
    if a.commande == "brancher":
        print(f"CIRCÉ : automatisation branchée ({brancher(a.adresse)}).")
    elif a.commande == "debrancher":
        if fichier_connexions().exists():
            fichier_connexions().unlink()
        print("CIRCÉ : plus aucune automatisation branchée.")
    elif a.commande == "etat":
        adr = adresse_branchee()
        print(f"CIRCÉ : automatisation {'branchée (' + masquer(adr) + ')' if adr else 'non branchée'}.")
    else:
        print(json.dumps(livrer(a), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
