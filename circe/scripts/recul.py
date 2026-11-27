"""CIRCÉ — Réflexe « point de recul » : hook UserPromptSubmit.

Retour d'usage (24/11/2026) : quand on a bien avancé, s'arrêter, relire tout ce qui a été fait, chercher les erreurs et les
oublis, puis repartir, sans attendre qu'on le demande. Ce hook ajoute un rappel au contexte de Claude (il ne bloque rien) :
  - quand l'utilisateur demande une pause ou un bilan (« pause », « on fait le point », « on n'a rien loupé ? ») ;
  - toutes les SEUIL demandes depuis le dernier point de recul (comptées dans `.circe/carnet.jsonl`), puis tous les PAS ;
  - quand la demande parle de mettre en ligne, livrer, publier ou vendre, et qu'il y a eu du travail depuis le dernier point.
Le dernier point de recul = le fichier le plus récent de `.circe/recul/` (écrit par la compétence circe:recul).
En veille (licence inactive), il se tait. Bibliothèque standard seulement.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # Python embarqué (fichier ._pth) : le dossier du script n'est pas dans le chemin d'import

SEUIL = 10
PAS = 5
# Filtres écrits SANS accents, comparés au texte sans accents (essai « nouvel utilisateur » du 24/11 : « on fait le point »
# ne déclenchait pas le point de recul ; « loupe », « oublie », « deploie » tapés sans accents non plus).
DEMANDE_RECUL = re.compile(
    r"(?i)(?:\bpause\b|\bfai(?:s|t|re|sons|tes) (?:le|un) (?:point|bilan)\b|\bpoint de recul\b|\bprend(?:s|re) du recul\b|\brelis tout\b|\brelire tout\b"
    r"|\bregarde(?:r|z)? (?:deja )?tout ce qu.on a fait\b|\bce qu.on a fait\b.{0,40}\b(?:erreur|loupe|oublie|rate)\b|\bon (?:n.)?a (?:rien |pas )?(?:loupe|oublie|rate)\b"
    r"|\bqu.est-ce qu.on a (?:loupe|oublie)\b|\btake a step back\b|\breview everything\b|\bdid we miss\b)")
PUBLICATION = re.compile(
    r"(?i)\b(?:met(?:s|tre|tez|tons)?\b.{0,40}\ben (?:ligne|prod(?:uction)?)\b|mise en (?:ligne|prod(?:uction)?)\b|en production\b|deploi\w*|deploy\w*|publi(?:e|es|er|ez|ons|cation)\b"
    r"|livre(?:r|z)? (?:au|le|la|les)\b|livraison\b|envoie(?:-le| le| la)? au client\b|on vend\b|mettre en vente\b|lancer la vente\b"
    r"|deploy\w*|publish\w*|release\b|go(?:es|ing)? live\b|ship it\b)")


def sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")
RAPPEL_DEMANDE = ("[CIRCÉ, point de recul demandé : ouvre circe:recul MAINTENANT, avant tout autre travail. Relis tout ce qui a été fait depuis "
                  "le dernier point (demandes, fichiers, plan, promesses), revérifie les preuves en les relançant, cherche erreurs et oublis, "
                  "écris .circe/recul/, corrige ce qui est sûr, puis dis le bilan en 10 lignes au plus.]")
RAPPEL_COMPTE = ("[CIRCÉ, point de recul dû : {n} demandes depuis le dernier point. Avant de continuer, ouvre circe:recul : relire ce qui a été "
                 "fait, revérifier les preuves, chercher erreurs et oublis, corriger, puis reprendre le plan. Dis-le à l'utilisateur en une ligne.]")
RAPPEL_PUBLICATION = ("[CIRCÉ, avant de mettre en ligne, livrer ou vendre : fais d'abord le point de recul (circe:recul) sur tout ce qui part "
                      "({quoi}) : preuves relancées, incohérences, oublis (légal, langues, téléphone, sécurité). "
                      "Ensuite seulement, l'accord de l'utilisateur pour publier.]")


def dernier_recul(projet: Path) -> str:
    """Heure du dernier point de recul (« AAAA-MM-JJ HH:MM »), ou « » s'il n'y en a jamais eu."""
    dossier = projet / ".circe" / "recul"
    if not dossier.is_dir():
        return ""
    fichiers = [f for f in dossier.glob("*.md") if f.is_file()]
    if not fichiers:
        return ""
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(max(f.stat().st_mtime for f in fichiers)))


def demandes_depuis(projet: Path, depuis: str) -> int:
    fichier = projet / ".circe" / "carnet.jsonl"
    if not fichier.exists():
        return 0
    n = 0
    for ligne in fichier.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            tour = json.loads(ligne)
        except ValueError:
            continue
        heure = str(tour.get("heure") or "")
        if any(str(f).replace("\\", "/").startswith(".circe/recul/") for f in tour.get("fichiers") or []):
            continue   # le tour qui a écrit le point de recul n'est pas du travail à relire
        if heure and heure > depuis:   # même format « AAAA-MM-JJ HH:MM » : l'ordre des textes est l'ordre du temps ; la minute du point compte comme relue
            n += 1
    return n


def evaluer(evenement: dict, projet: Path) -> dict | None:
    texte = sans_accents(str(evenement.get("prompt") or ""))
    if not texte:
        return None
    if DEMANDE_RECUL.search(texte):
        rappel = RAPPEL_DEMANDE
    else:
        dernier = dernier_recul(projet)
        n = demandes_depuis(projet, dernier)
        # Avant une mise en ligne : rappel s'il y a eu du travail depuis le dernier point, ou s'il n'y a jamais eu de point.
        # Seul cas sans rappel : un point vient d'être fait et rien n'a changé depuis.
        if PUBLICATION.search(texte) and (n >= 1 or not dernier):
            rappel = RAPPEL_PUBLICATION.format(quoi=f"{n} demande(s) depuis le dernier point" if dernier else "aucun point de recul encore fait dans ce projet")
        elif n >= SEUIL and (n - SEUIL) % PAS == 0:
            rappel = RAPPEL_COMPTE.format(n=n)
        else:
            return None
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": rappel}}


def en_veille() -> bool:
    try:
        import licence  # noqa: PLC0415
        return licence.etat_rapide() == "veille"
    except Exception:
        return False


def main() -> int:
    try:
        import unique  # noqa: PLC0415 (même dossier)
        brut = unique.lire("recul")
        if brut is None:
            return 0  # l'autre interprète traite déjà cet événement
        evenement = json.loads(brut or "{}")
        projet = Path(os.environ.get("CLAUDE_PROJECT_DIR") or evenement.get("cwd") or os.getcwd())
        resultat = None if en_veille() else evaluer(evenement, projet)
    except Exception:
        return 0
    if resultat:
        sys.stdout.write(json.dumps(resultat))
    return 0


if __name__ == "__main__":
    sys.exit(main())
