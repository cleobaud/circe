"""CIRCÉ — « Rien d'imposé » (0.5). Principe : à l'installation, CIRCÉ ne bloque rien et ne
demande rien ; il PROPOSE, et l'utilisateur active ce qu'il veut. Seuls 3 gestes catastrophiques restent refusés par défaut
(formater un disque, effacer la racine d'un disque, effacer le dossier personnel), et c'est expliqué dès la première session,
puis rappelé ensuite.

État : ~/.circe/protections.json  {"actives": [...], "desactivees": [...], "explique": true}
  (CIRCE_PROTECTIONS = un autre fichier, pour les essais). Fichier absent ou illisible : les réglages par défaut.

  python protections.py etat                     liste des protections, actives ou proposées
  python protections.py activer <nom> [<nom>…]   active (le choix de l'utilisateur, dit par lui)
  python protections.py desactiver <nom> […]     désactive (la garde demande toujours l'accord de l'utilisateur pour ça)
  python protections.py toutes                   active tout
Bibliothèque standard seulement.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# nom -> (libellé pour l'utilisateur, ce qu'elle fait une fois activée)
PROTECTIONS = {
    "catastrophique": ("3 gestes catastrophiques", "refuse de formater un disque, d'effacer la racine d'un disque ou le dossier personnel"),
    "suppression": ("suppression récursive", "demande votre accord avant de supprimer un dossier et son contenu"),
    "historique_git": ("historique git", "demande votre accord avant de réécrire ou perdre l'historique git (reset --hard, push --force…)"),
    "git_push": ("envoi git", "demande votre accord avant un git push"),
    "production": ("mise en production", "demande votre accord avant un déploiement en production"),
    "publication": ("publication de paquet", "demande votre accord avant de publier un paquet ou une image"),
    "script_distant": ("script distant", "demande votre accord avant d'exécuter un script téléchargé"),
    "base_de_donnees": ("base de données", "demande votre accord avant de vider ou supprimer une base"),
    "secrets": ("fichiers de secrets", "demande votre accord avant de lire ou d'écrire un fichier de secrets (.env, clés)"),
    "systeme": ("dossiers du système", "refuse l'écriture dans un dossier du système (Windows, /etc…)"),
    "reglages": ("réglages de Claude Code", "demande votre accord avant que Claude modifie vos réglages (vos autorisations)"),
    "exterieur": ("actions vers l'extérieur", "demande votre accord avant un envoi, une publication ou une suppression par un connecteur"),
}
DEFAUT = frozenset({"catastrophique"})       # les 3 refus par défaut, expliqués dès la première session


def fichier() -> Path:
    autre = os.environ.get("CIRCE_PROTECTIONS")
    return Path(autre) if autre else Path.home() / ".circe" / "protections.json"


def lire_etat() -> dict:
    try:
        d = json.loads(fichier().read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def actives() -> set:
    """Les protections en service : les réglages par défaut, plus les choix de l'utilisateur."""
    e = lire_etat()
    ajout = {x for x in e.get("actives", []) if x in PROTECTIONS}
    retrait = {x for x in e.get("desactivees", []) if x in PROTECTIONS}
    return (set(DEFAUT) | ajout) - retrait


def active(nom: str) -> bool:
    try:
        return nom in actives()
    except Exception:
        return nom in DEFAUT


def _ecrire(e: dict) -> None:
    f = fichier()
    f.parent.mkdir(parents=True, exist_ok=True)
    e["modifie_le"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, f)


def changer(noms: list, activer: bool) -> list:
    inconnus = [n for n in noms if n not in PROTECTIONS]
    if inconnus:
        raise ValueError("protection inconnue : " + ", ".join(inconnus) + " (voir : python protections.py etat)")
    e = lire_etat()
    on, off = set(e.get("actives", [])), set(e.get("desactivees", []))
    for n in noms:
        (on.add if activer else on.discard)(n)
        (off.discard if activer else off.add)(n)
    e["actives"], e["desactivees"] = sorted(on), sorted(off)
    _ecrire(e)
    return sorted(actives())


def texte_session() -> str:
    """Pour le début de chaque session (SessionStart) : la première fois, Claude l'explique à l'utilisateur ; ensuite, un rappel."""
    act = actives()
    proposees = [PROTECTIONS[n][0] for n in PROTECTIONS if n not in act]
    commande = f'python "{Path(__file__).resolve()}"'
    base = ("CIRCÉ, rien d'imposé : seules les protections choisies par l'utilisateur sont en service ("
            + ", ".join(PROTECTIONS[n][0] for n in PROTECTIONS if n in act) + "). Rien d'autre n'est bloqué ni demandé par CIRCÉ. "
            "Quand un geste qu'une protection aurait couvert passe, CIRCÉ te le signale : propose-la UNE fois à l'utilisateur, "
            "en une phrase, sans jamais l'activer toi-même. Il l'active avec « configure CIRCÉ » ou " + commande + " activer <nom>.")
    e = lire_etat()
    if e.get("explique"):
        return "[" + base + "]"
    try:
        e["explique"] = True
        _ecrire(e)
    except OSError:
        pass
    return ("[" + base + " PREMIÈRE SESSION AVEC CIRCÉ : dans ta première réponse, explique-le à l'utilisateur en 3 phrases simples. "
            "1) CIRCÉ n'impose rien : il ne bloque que 3 gestes catastrophiques (formater un disque, effacer la racine d'un disque, "
            "effacer le dossier personnel). 2) Les autres protections sont proposées, à activer quand il veut : "
            + ", ".join(proposees) + ". 3) « configure CIRCÉ » les présente une par une.]")


def main(argv: list) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    cmd = argv[1] if len(argv) > 1 else "etat"
    try:
        if cmd in ("activer", "desactiver"):
            changer(argv[2:], cmd == "activer")
        elif cmd == "toutes":
            changer(list(PROTECTIONS), True)
        elif cmd != "etat":
            print(__doc__)
            return 2
    except ValueError as e:
        print(e)
        return 2
    act = actives()
    for n, (lib, quoi) in PROTECTIONS.items():
        print(f"[{'active ' if n in act else 'proposée'}] {n:16s} {lib} : {quoi}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
