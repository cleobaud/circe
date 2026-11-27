"""CIRCÉ — Réflexe « boucle du niveau » : hook Stop.

Demande de l'utilisateur (24/11, après un essai réel) : « poser des boucles universelles pour que Claude délivre toujours
du contenu de qualité sans jamais le reprendre ». Essai : Claude présentait un aperçu propre, mais nettement en dessous de la
référence (une gravure détaillée rendue en silhouettes), sans jamais les avoir posés côte à côte.

Quand Claude s'apprête à rendre la main en PRÉSENTANT un livrable visuel (« voici… », aperçu, rendu, pistes…), dans un projet
où des exemples ont été regardés (`.circe/exemples/`), ce réflexe vérifie qu'une image côte à côte a été faite PENDANT CE TOUR
(`.circe/cote-a-cote/`, plus récente que la dernière demande de l'utilisateur). Sinon, il relance Claude une fois : poser le
résultat à côté de la référence, faire juger chaque axe par un regard neuf, corriger ou changer de moyen (circe:qualite).
Une seule relance par fin de tour (« stop_hook_active »). En veille (licence inactive), il se tait. Bibliothèque standard seulement.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # Python embarqué (fichier ._pth)

# Relecture Codex du 24/11 : la liste de tournures était trop étroite (« le logo est fini » passait) et trop large
# (« voici les fichiers manquants » déclenchait). On cherche maintenant un LIVRABLE visuel nommé, présenté ou annoncé prêt.
LIVRABLE = (r"(?:apercus?|sites?|pages?|accueil|logos?|pistes?|videos?|rendus?|maquettes?|planches?|visuels?|affiches?|bannieres?"
            r"|illustrations?|animations?|frises?|ecussons?|montages?|storyboards?|deroules?|scenes?|modeles? 3d|objets? 3d|resultats?|livrables?)")
PRET = r"(?:prete?s?|faite?s?|rendue?s?|terminee?s?|finie?s?|livree?s?|verifiee?s?|construite?s?|refaite?s?|en place)"
PRESENTE = re.compile(rf"(?i)\b(?:voici|voila|je te montre|je vous montre|a double-cliquer|tu peux ouvrir|vous pouvez ouvrir)\b[^.!?\n]{{0,60}}?\b{LIVRABLE}\b"
                      rf"|\b{LIVRABLE}\b[^.!?\n]{{0,40}}?\b(?:est|sont|:|—|-)?\s*\b{PRET}\b")
OUTIL = Path(__file__).resolve().parent / "cote_a_cote.py"

# Essai réel du 27/11 : ce réflexe a bloqué DEUX FOIS un message où rien n'avait été produit — un état des lieux
# « /demarrage » qui citait des aperçus faits trois jours plus tôt, puis un audit qui parlait de visuels et de logo. Les
# mots ne disent pas qu'on livre. On exige donc un FAIT : un fichier visuel écrit ou modifié pendant CE tour, dans le projet.
VISUELS = {".html", ".htm", ".css", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".bmp", ".ico", ".tif",
           ".tiff", ".mp4", ".webm", ".mov", ".m4v", ".blend", ".glb", ".gltf", ".obj", ".fbx", ".stl", ".pdf"}
# « .circe/ » est la comptabilité de CIRCÉ (captures de référence, côte à côte, journal) : ce n'est pas une production.
SAUTES = {".circe", ".git", "node_modules", "__pycache__", ".venv", "venv", "build", ".next", ".cache", ".idea", ".vscode"}
PLAFOND_FICHIERS = 20000
PLAFOND_SECONDES = 2.0
FENETRE_SANS_DATE = 600.0   # demande introuvable dans la transcription : on regarde les 10 dernières minutes


def sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")


def raison() -> str:
    return ("CIRCÉ, boucle du niveau : tu présentes un livrable, mais pendant ce tour tu ne l'as pas posé à côté de la référence. "
            f"Avant de le montrer : python \"{OUTIL}\" \"<référence>\" \"<résultat>\", puis fais juger chaque axe (composition, "
            "typographie, densité de détail, couleur, finition, mouvement) par un regard neuf (sous-agent qui ne connaît pas ton travail), "
            "et corrige ce qui est en dessous (3 tours au plus). Si le niveau est hors d'atteinte avec ce moyen, change de moyen ou écris "
            "l'écart en haut de ce que tu montres. Méthode : circe:qualite.")


def _textes(contenu) -> list[str]:
    if isinstance(contenu, str):
        return [contenu]
    if isinstance(contenu, list):
        return [b.get("text", "") for b in contenu if isinstance(b, dict) and b.get("type") == "text"]
    return []


def _date(valeur) -> float | None:
    try:
        return datetime.fromisoformat(str(valeur).replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        return None


def tour(chemin: Path) -> tuple[str, float | None]:
    """(texte de l'assistant depuis la dernière vraie demande, date de cette demande)."""
    morceaux: list[str] = []
    debut = None
    try:
        lignes = chemin.read_text(encoding="utf-8-sig", errors="ignore").replace("﻿", "").splitlines()
    except OSError:
        return "", None
    for ligne in lignes:
        try:
            entree = json.loads(ligne)
        except ValueError:
            continue
        message = entree.get("message") or {}
        role = entree.get("type") or message.get("role")
        textes = [t for t in _textes(message.get("content")) if t.strip()]
        # une compétence chargée ou une image lue (lignes « user » isMeta) ne sont pas une nouvelle demande
        if role == "user" and textes and not entree.get("isMeta") and not textes[0].lstrip().startswith(
                ("<", "Base directory for this skill", "[Request interrupted", "[Image")):
            morceaux, debut = [], _date(entree.get("timestamp"))
        elif role == "assistant":
            morceaux.extend(_textes(message.get("content")))
    return "\n".join(morceaux), debut


def cote_a_cote_recent(projet: Path, depuis: float | None) -> bool:
    """Vrai si une comparaison FAITE PAR L'OUTIL existe pour ce tour : son manifeste (écrit par cote_a_cote.py) est daté
    après la demande, et l'empreinte de l'image correspond (relecture Codex du 24/11 : un PNG quelconque, ou un ancien
    fichier retouché, ne suffit plus). Ce réflexe est un rappel, pas une barrière contre un contournement délibéré."""
    import hashlib  # noqa: PLC0415
    dossier = projet / ".circe" / "cote-a-cote"
    try:
        manifestes = list(dossier.glob("*.json"))
    except OSError:
        return False
    for m in manifestes:
        try:
            d = json.loads(m.read_text(encoding="utf-8"))
            if depuis is not None and float(d.get("cree_le", 0)) < depuis:   # strictement après la demande (Codex, tour 2)
                continue
            image = Path(d["image"])
            if image.exists() and hashlib.sha256(image.read_bytes()).hexdigest() == d.get("sha256"):
                return True
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return False


def visuel_produit(projet: Path, depuis: float | None) -> bool:
    """Vrai si un fichier visuel du projet a été écrit ou modifié pendant ce tour.

    On regarde le disque, pas les noms d'outils : une page écrite par Write, une image rendue par un script Python,
    une vidéo sortie par ffmpeg comptent toutes pareil. Sans date de demande, on prend une fenêtre de 10 minutes.
    Plafonds de fichiers et de durée : ce réflexe ne doit jamais retarder la fin d'un tour.
    """
    seuil = depuis if depuis is not None else time.time() - FENETRE_SANS_DATE
    fin = time.monotonic() + PLAFOND_SECONDES
    vus = 0
    for racine, dossiers, fichiers in os.walk(projet):
        dossiers[:] = [d for d in dossiers if d not in SAUTES]
        for nom in fichiers:
            vus += 1
            if vus > PLAFOND_FICHIERS or time.monotonic() > fin:
                return True   # projet trop gros pour conclure : on ne bloque pas sur une inconnue
            if os.path.splitext(nom)[1].lower() not in VISUELS:
                continue
            try:
                if os.path.getmtime(os.path.join(racine, nom)) >= seuil:
                    return True
            except OSError:
                continue
    return False


def en_veille() -> bool:
    try:
        import licence  # noqa: PLC0415 (même dossier)
        return licence.etat_rapide() == "veille"
    except Exception:
        return False


def evaluer(evenement: dict, projet: Path) -> dict | None:
    if evenement.get("stop_hook_active") or en_veille():
        return None
    if not (projet / ".circe" / "exemples").is_dir():
        return None   # aucune référence regardée dans ce projet : pas de niveau à comparer
    chemin = evenement.get("transcript_path")
    if not chemin:
        return None
    texte, debut = tour(Path(chemin))
    if not texte or not PRESENTE.search(sans_accents(texte)):
        return None
    if not visuel_produit(projet, debut):
        return None   # rien de visuel produit pendant ce tour : parler d'un livrable n'est pas le livrer (essai du 27/11)
    if cote_a_cote_recent(projet, debut):
        return None
    return {"decision": "block", "reason": raison()}


def main() -> int:
    try:
        import unique  # noqa: PLC0415 (même dossier)
        brut = unique.lire("niveau")
        if brut is None:
            return 0  # l'autre interprète traite déjà cet événement
        evenement = json.loads(brut or "{}")
        projet = Path(os.environ.get("CLAUDE_PROJECT_DIR") or evenement.get("cwd") or os.getcwd())
        resultat = evaluer(evenement, projet)
    except Exception:
        return 0  # ce réflexe ne doit jamais empêcher de rendre la main en cas de panne
    if resultat:
        try:
            dossier = projet / ".circe"
            with open(dossier / "journal-immunitaire.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({"heure": time.strftime("%Y-%m-%dT%H:%M:%S"), "outil": "Stop", "decision": "relance",
                                    "raison": "livrable présenté sans côte à côte avec la référence"}, ensure_ascii=False) + "\n")
        except OSError:
            pass
        sys.stdout.write(json.dumps(resultat))
    return 0


if __name__ == "__main__":
    sys.exit(main())
