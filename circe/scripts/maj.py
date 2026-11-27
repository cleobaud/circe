"""CIRCÉ — mise à jour au démarrage, sans rien demander à l'utilisateur.

Demande de l'utilisateur du 27/11 : « il faut trouver une solution pour qu'il se mette lui-même à jour au démarrage ».

Deux limites de Claude Code, qui décident de la forme :
- les plugins sont chargés AU DÉMARRAGE : une version installée pendant la session ne peut pas s'y charger elle-même
  (`claude plugin update` le dit : « restart required to apply »). Donc CIRCÉ s'installe tout seul, et la nouvelle
  version prend la main au prochain lancement. C'est le maximum atteignable, et c'est annoncé en une ligne.
- un réflexe doit rendre la main en quelques secondes : rien n'est attendu ici. Le catalogue se lit sur le disque
  (instantané), et les commandes `claude` sont lancées DÉTACHÉES. Leur résultat est vu au démarrage suivant.

Réglage de l'utilisateur (`~/.circe/maj.json`, ou le fichier de la variable CIRCE_MAJ pour les essais) :
  {"choix": "auto"}       installe tout seul (par défaut : c'est le même produit, déjà accepté à l'installation)
  {"choix": "proposer"}   dit qu'une version existe et attend la demande de l'utilisateur
  {"choix": "jamais"}     se taît

  python maj.py etat        ce qui est installé, ce qui est disponible, le réglage
  python maj.py auto|proposer|jamais     change le réglage
  python maj.py maintenant  lance la mise à jour tout de suite (détachée)

Bibliothèque standard seulement, aucun appel réseau dans ce fichier : c'est `claude` qui parle au réseau.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

PLUGIN = "circe"
PLACE = "circe-cdow"
IDENTIFIANT = f"{PLUGIN}@{PLACE}"
# Un essai raté ne se répète pas en boucle ; le catalogue ne se rafraîchit pas à chaque ouverture de terminal.
DELAI_TENTATIVE = 3600.0
DELAI_RAFRAICHISSEMENT = 86400.0
CHOIX_VALIDES = ("auto", "proposer", "jamais")


def fichier() -> Path:
    autre = os.environ.get("CIRCE_MAJ")
    return Path(autre) if autre else Path.home() / ".circe" / "maj.json"


def lire_etat() -> dict:
    try:
        etat = json.loads(fichier().read_text(encoding="utf-8"))
        return etat if isinstance(etat, dict) else {}
    except (OSError, ValueError):
        return {}


def ecrire_etat(etat: dict) -> None:
    try:
        f = fichier()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(etat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass


def choix() -> str:
    valeur = str(lire_etat().get("choix", "auto"))
    return valeur if valeur in CHOIX_VALIDES else "auto"


def dossier_config() -> Path:
    """Le dossier de réglages de Claude Code réellement utilisé (il n'est pas toujours ~/.claude)."""
    autre = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(autre) if autre else Path.home() / ".claude"


def version_installee() -> str | None:
    try:
        config = json.loads((Path(__file__).resolve().parent / "config.json").read_text(encoding="utf-8"))
        return str(config["version"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


DEPOT_OFFICIEL = "cleobaud/circe"        # la place de marché publique de CDOW (décision du 27/11/2026)


def source_declaree() -> dict | None:
    """Ce que le registre de Claude Code dit de la place de marché « circe-cdow » sur CE poste."""
    try:
        places = json.loads((dossier_config() / "plugins" / "known_marketplaces.json").read_text(encoding="utf-8"))
        source = places[PLACE].get("source")
        return source if isinstance(source, dict) else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def source_officielle(source: dict | None = None) -> bool:
    """Vrai si la mise à jour viendrait bien du dépôt de CDOW.

    Pourquoi ce contrôle : le nom « circe-cdow » n'appartient à personne dans le registre local. Qui peut écrire dans
    ce fichier peut faire pointer ce nom ailleurs, et la mise à jour automatique installerait alors du code étranger
    chez l'utilisateur, sans que rien ne le dise. On n'installe donc tout seul QUE depuis le dépôt officiel ; tout le
    reste (dossier local, autre dépôt) est annoncé à l'utilisateur, jamais installé en silence.
    """
    s = source_declaree() if source is None else source
    if not s:
        return False
    if s.get("source") == "github":
        return str(s.get("repo", "")).strip().lower().removesuffix(".git") == DEPOT_OFFICIEL
    if s.get("source") in ("git", "url"):
        adresse = str(s.get("url") or s.get("repo") or "").strip().lower().removesuffix(".git")
        return adresse.endswith("github.com/" + DEPOT_OFFICIEL) or adresse.endswith(DEPOT_OFFICIEL)
    return False


def dit_la_source(s: dict | None) -> str:
    if not s:
        return "inconnue"
    if s.get("source") == "github":
        return "dépôt " + str(s.get("repo", "?"))
    if s.get("source") == "directory":
        return "dossier local " + str(s.get("path", "?"))
    return str(s.get("source", "?"))


def version_disponible() -> str | None:
    """La version annoncée par le catalogue de la place de marché, lu sur le disque (aucun réseau).

    `claude plugin marketplace update` est ce qui rafraîchit ce catalogue ; on le lance détaché par ailleurs.
    """
    try:
        places = json.loads((dossier_config() / "plugins" / "known_marketplaces.json").read_text(encoding="utf-8"))
        ici = Path(places[PLACE]["installLocation"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    try:
        catalogue = json.loads((ici / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        for p in catalogue.get("plugins", []):
            if p.get("name") == PLUGIN and p.get("version"):
                return str(p["version"])
    except (OSError, ValueError, TypeError):
        return None
    return None


def rang(version: str) -> tuple:
    return tuple(int(m) for m in re.findall(r"\d+", version or "")[:4])


def plus_recente(disponible: str | None, installee: str | None) -> bool:
    if not disponible or not installee:
        return False
    a, b = rang(disponible), rang(installee)
    return bool(a) and bool(b) and a > b


def executable() -> str | None:
    """Le chemin complet de la commande `claude`.

    Essai réel du 27/11 : sous Windows, `claude` est un fichier `.CMD`. Lancé par son nom nu, Popen échoue
    (« le fichier spécifié est introuvable ») parce que CreateProcess n'applique pas PATHEXT. Il faut le résoudre.
    """
    for nom in ("claude", "claude.cmd", "claude.exe"):
        chemin = shutil.which(nom)
        if chemin:
            return chemin
    return None


def lancer(args: list[str]) -> bool:
    """Lance une commande `claude` DÉTACHÉE : le réflexe rend la main tout de suite, le résultat se voit après."""
    exe = executable()
    if not exe:
        return False
    if os.name == "nt":
        sans_fenetre = {"creationflags": 0x00000008 | 0x08000000}   # DETACHED_PROCESS | CREATE_NO_WINDOW
    else:
        sans_fenetre = {"start_new_session": True}
    try:
        subprocess.Popen([exe, *args], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, **sans_fenetre)
        return True
    except (OSError, ValueError):
        return False


def rafraichir_catalogue(etat: dict) -> None:
    """Demande à Claude Code d'aller voir s'il existe une version plus récente ; au plus une fois par jour."""
    if time.time() - float(etat.get("dernier_rafraichissement", 0) or 0) < DELAI_RAFRAICHISSEMENT:
        return
    if lancer(["plugin", "marketplace", "update", PLACE]):
        etat["dernier_rafraichissement"] = time.time()
        ecrire_etat(etat)


def installer(etat: dict) -> bool:
    if time.time() - float(etat.get("derniere_tentative", 0) or 0) < DELAI_TENTATIVE:
        return False
    if not source_officielle():
        return False          # source non officielle : on annonce, on n'installe pas (voir au_demarrage)
    if not lancer(["plugin", "update", IDENTIFIANT, "-y"]):
        return False
    etat["derniere_tentative"] = time.time()
    ecrire_etat(etat)
    return True


def au_demarrage() -> str:
    """La ligne à montrer au démarrage. Vide quand il n'y a rien à dire."""
    reglage = choix()
    if reglage == "jamais":
        return ""
    etat = lire_etat()
    installee, disponible = version_installee(), version_disponible()
    if not plus_recente(disponible, installee):
        rafraichir_catalogue(etat)
        return ""
    if not source_officielle():
        # Le nom « circe-cdow » n'appartient à personne dans le registre local : s'il pointe ailleurs que le dépôt de
        # CDOW, on n'installe rien tout seul. On le dit, et l'utilisateur décide.
        return (f"[CIRCÉ {disponible} est annoncée (vous avez {installee}), mais la source de mise à jour n'est PAS "
                f"celle de CDOW : {dit_la_source(source_declaree())}. Rien ne sera installé automatiquement. "
                f"Dis-le à l'utilisateur en une ligne : pour la source officielle, "
                f"`claude plugin marketplace add {DEPOT_OFFICIEL}` ; s'il sait ce qu'il fait (installation locale, "
                f"essai), il peut installer lui-même avec `claude plugin update {IDENTIFIANT}`.]")
    if reglage == "proposer":
        return (f"[CIRCÉ {disponible} existe (vous avez {installee}). Dis-le à l'utilisateur en une ligne et demande-lui "
                f"s'il veut l'installer : `claude plugin update {IDENTIFIANT}`, puis redémarrer Claude Code. "
                f"Pour que CIRCÉ s'en occupe seul à l'avenir : `python \"{Path(__file__).resolve()}\" auto`.]")
    if installer(etat):
        return (f"[CIRCÉ s'installe tout seul : {installee} → {disponible}. Dis à l'utilisateur, en une ligne, que la "
                f"mise à jour est en cours et qu'elle prendra la main au prochain démarrage de Claude Code (les plugins "
                f"se chargent au lancement, cette session continue en {installee}). Pour ne plus le faire : "
                f"`python \"{Path(__file__).resolve()}\" proposer`.]")
    return (f"[CIRCÉ {disponible} a déjà été installée ou la tentative est trop récente ; cette session tourne en "
            f"{installee}. Dis à l'utilisateur, en une ligne, qu'un redémarrage de Claude Code la mettra en service.]")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    action = args[0] if args else "etat"
    if action in CHOIX_VALIDES:
        etat = lire_etat()
        etat["choix"] = action
        ecrire_etat(etat)
        print(f"CIRCÉ, mise à jour : réglage « {action} » enregistré dans {fichier()}")
        return 0
    if action == "maintenant":
        etat = lire_etat()
        etat.pop("derniere_tentative", None)
        print("mise à jour lancée (détachée)" if installer(etat) else "la commande claude n'a pas pu être lancée")
        return 0
    if action == "etat":
        installee, disponible = version_installee(), version_disponible()
        print(f"installée    : {installee}")
        print(f"disponible   : {disponible or '(catalogue illisible ou place de marché absente)'}")
        print(f"réglage      : {choix()}  (auto | proposer | jamais)")
        print(f"fichier      : {fichier()}")
        print(f"plus récente : {'oui' if plus_recente(disponible, installee) else 'non'}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
