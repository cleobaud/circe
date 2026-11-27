"""CIRCÉ — où en est CIRCÉ sur ce poste, et que puis-je faire s'il est hors ligne ?

  python etat.py              l'état en clair : version, licence, serveur, ce qui marche, ce qui attend
  python etat.py --json       le même état en JSON
  python etat.py --hors-ligne la réponse courte à donner quand le serveur ne répond pas

Deux défauts d'un coup (relevés par la session binôme le 27/11/2026) :
- **D5** : quand le serveur ne répond pas, les compétences disaient « dis-le, puis applique ce résumé minimal » — sans
  dire ce qui marche quand même, ni quand réessayer. Un utilisateur conclut que le logiciel est cassé.
- **D6, moitié locale** : aucune commande ne disait la version installée ni ce que le produit contient. Les chiffres
  d'un visuel ou d'une page de vente se recopiaient d'un site, et vieillissaient (constaté en M4 et M6).

La version la plus récente disponible, elle, viendra du serveur : tant qu'il ne la donne pas, cette commande ne
l'invente pas. Aucun secret n'est lu, aucune clé n'est affichée. Bibliothèque standard seulement.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(ICI))

DELAI_SERVEUR_S = 4

MARCHE_HORS_LIGNE = [
    "la mémoire du projet (relais, carnet, journal) et la reprise au bon endroit",
    "le système immunitaire : les gestes catastrophiques refusés, « pas de fini sans preuve », les rappels",
    "les compétences installées et leur résumé de secours",
    "les outils du plugin : regarder (mesures et planches), côte à côte, contrôles vidéo, intégrité, plan, mémoire",
]
ATTEND_LE_SERVEUR = [
    "la méthode détaillée de chaque parcours (elle est servie, pas livrée)",
    "les outils servis par CDOW (le Quai, par exemple)",
    "la dernière version publiée du logiciel",
]


def version_installee() -> str | None:
    try:
        return str(json.loads((RACINE / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"])
    except (OSError, ValueError, KeyError):
        return None


def adresse_serveur() -> str | None:
    try:
        d = json.loads((RACINE / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        return str(d["mcpServers"]["circe-cerveau"]["url"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def competences() -> list[str]:
    dossier = RACINE / "skills"
    if not dossier.is_dir():
        return []
    return sorted(d.name for d in dossier.iterdir() if (d / "SKILL.md").exists())


def licence_etat() -> str:
    try:
        import licence  # noqa: PLC0415 (même dossier)
        return licence.etat_rapide()
    except Exception:                       # noqa: BLE001 — une panne du contrôle ne doit pas casser l'état
        return "inconnu"


def serveur_joignable(ouvrir=urllib.request.urlopen) -> tuple[bool, str]:
    """Une requête sans clé, juste pour savoir si la machine répond. Rien du projet n'est envoyé."""
    adresse = adresse_serveur()
    if not adresse:
        return False, "adresse du serveur introuvable dans le manifeste"
    try:
        requete = urllib.request.Request(adresse, method="HEAD", headers={"User-Agent": "circe-etat"})
        with ouvrir(requete, timeout=DELAI_SERVEUR_S) as r:
            return True, f"réponse {getattr(r, 'status', '?')}"
    except urllib.error.HTTPError as e:     # une réponse d'erreur reste une réponse : la machine est là
        return True, f"réponse {e.code}"
    except Exception as e:                  # noqa: BLE001 — réseau coupé, DNS, pare-feu, délai dépassé
        return False, type(e).__name__


def etat(ouvrir=urllib.request.urlopen) -> dict:
    joignable, detail = serveur_joignable(ouvrir)
    noms = competences()
    return {"version_installee": version_installee(), "licence": licence_etat(),
            "serveur_joignable": joignable, "serveur_detail": detail,
            "competences": len(noms), "liste_competences": noms,
            "marche_hors_ligne": MARCHE_HORS_LIGNE, "attend_le_serveur": ATTEND_LE_SERVEUR}


def texte_hors_ligne(e: dict) -> str:
    return ("CIRCÉ ne joint pas son serveur ({}). Le logiciel n'est pas cassé : {} compétences restent là, "
            "la mémoire du projet, le système immunitaire et les outils de contrôle marchent. Ce qui attend : la "
            "méthode détaillée des parcours et les outils servis. Réessaie dans quelques minutes, ou à la prochaine "
            "demande : chaque appel retente. Si ça dure, regarde ta connexion, puis l'état de cdow.fr."
            .format(e["serveur_detail"], e["competences"]))


def en_clair(e: dict) -> str:
    lignes = [f"CIRCÉ {e['version_installee'] or '?'} — licence : {e['licence']} — "
              f"serveur : {'joignable' if e['serveur_joignable'] else 'INJOIGNABLE'} ({e['serveur_detail']})",
              f"{e['competences']} compétences installées : " + ", ".join(e["liste_competences"]),
              "",
              "Marche sans le serveur :"] + [f"  - {x}" for x in e["marche_hors_ligne"]] + [
              "", "Attend le serveur :"] + [f"  - {x}" for x in e["attend_le_serveur"]]
    if not e["serveur_joignable"]:
        lignes += ["", texte_hors_ligne(e)]
    return "\n".join(lignes)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="etat.py", description="Où en est CIRCÉ sur ce poste")
    p.add_argument("--json", action="store_true")
    p.add_argument("--hors-ligne", action="store_true", help="la réponse courte quand le serveur ne répond pas")
    a = p.parse_args(argv)
    e = etat()
    if a.json:
        print(json.dumps(e, ensure_ascii=False, indent=1))
    elif a.hors_ligne:
        # Essai du 27/11 : la commande donnait la phrase « hors ligne » même quand le serveur répondait.
        print(texte_hors_ligne(e) if not e["serveur_joignable"]
              else f"Le serveur répond ({e['serveur_detail']}) : rien à signaler, la méthode est servie normalement.")
    else:
        print(en_clair(e))
    return 0 if e["serveur_joignable"] else 1


if __name__ == "__main__":
    sys.exit(main())
