"""CIRCÉ — Mémoire : le carnet automatique (hook Stop, à chaque fin de tour).

Même si personne n'écrit le relais, la session suivante sait ce qui s'est passé : pour chaque demande de l'utilisateur,
le carnet garde la demande (début), les fichiers créés ou modifiés, le nombre d'outils utilisés et le début de la réponse.
Rien ne sort de l'ordinateur : `<projet>/.circe/carnet.jsonl`. Les suites de caractères qui ressemblent à des secrets sont masquées.
Bibliothèque standard seulement.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # Python embarqué (fichier ._pth) : le dossier du script n'est pas dans le chemin d'import

GARDER = 300
SECRET = re.compile(r"(?:sk|pk|ghp|gho|xox[abp]|AKIA|eyJ)[A-Za-z0-9_\-\.]{12,}|\b(?=[A-Za-z0-9_\-]*\d)(?=[A-Za-z0-9_\-]*[A-Za-z])[A-Za-z0-9_\-]{28,}\b")
OUTILS_FICHIER = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def masquer(texte: str, n: int) -> str:
    texte = " ".join(str(texte).split())
    texte = SECRET.sub("[masqué]", texte)
    return texte if len(texte) <= n else texte[: n - 1] + "…"


def _textes(contenu) -> list[str]:
    if isinstance(contenu, str):
        return [contenu]
    if isinstance(contenu, list):
        return [b.get("text", "") for b in contenu if isinstance(b, dict) and b.get("type") == "text"]
    return []


def _systeme(texte: str) -> bool:
    """Texte injecté par Claude Code (contenu d'une compétence, rappel du système), pas tapé par l'utilisateur."""
    debut = texte.lstrip()
    return debut.startswith("<") or debut.startswith("Base directory for this skill") or debut.startswith("[Request interrupted")


def dernier_tour(chemin: Path, projet: Path) -> dict | None:
    """Le dernier tour : depuis la dernière vraie demande de l'utilisateur jusqu'à la fin du transcript."""
    try:
        lignes = chemin.read_text(encoding="utf-8-sig", errors="ignore").replace("﻿", "").splitlines()
    except OSError:
        return None
    demande, fichiers, outils, reponse = None, [], Counter(), []
    for ligne in lignes:
        try:
            entree = json.loads(ligne)
        except ValueError:
            continue
        message = entree.get("message") or {}
        role = entree.get("type") or message.get("role")
        contenu = message.get("content")
        if role == "user":
            textes = [t for t in _textes(contenu) if t.strip()]
            if textes and not entree.get("isMeta") and not _systeme(textes[0]):   # une vraie demande de l'utilisateur
                demande, fichiers, outils, reponse = " ".join(textes), [], Counter(), []
        elif role == "assistant" and demande is not None:
            reponse += _textes(contenu)
            for b in contenu if isinstance(contenu, list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    nom = str(b.get("name") or "?")
                    outils[nom] += 1
                    chemin_f = (b.get("input") or {}).get("file_path") or (b.get("input") or {}).get("notebook_path")
                    if nom in OUTILS_FICHIER and chemin_f:
                        try:
                            rel = str(Path(chemin_f).resolve().relative_to(projet.resolve()))
                        except (ValueError, OSError):
                            rel = Path(chemin_f).name
                        if rel not in fichiers:
                            fichiers.append(rel.replace("\\", "/"))
    if demande is None:
        return None
    return {"demande": masquer(demande, 240), "fichiers": fichiers[:15], "outils": dict(outils.most_common(6)),
            "reponse": masquer(" ".join(reponse), 300)}


def noter_tour(evenement: dict) -> dict | None:
    chemin = evenement.get("transcript_path")
    if not chemin:
        return None
    projet = Path(os.environ.get("CLAUDE_PROJECT_DIR") or evenement.get("cwd") or os.getcwd())
    tour = dernier_tour(Path(chemin), projet)
    if not tour:
        return None
    import time  # noqa: PLC0415
    session = str(evenement.get("session_id") or "")[:8]
    cle = hashlib.sha256(f"{session}|{tour['demande']}".encode("utf-8")).hexdigest()[:12]
    ligne = {"heure": time.strftime("%Y-%m-%d %H:%M"), "session": session, "cle": cle, **tour}
    dossier = projet / ".circe"
    dossier.mkdir(exist_ok=True)
    fichier = dossier / "carnet.jsonl"
    anciennes = fichier.read_text(encoding="utf-8", errors="ignore").splitlines() if fichier.exists() else []
    if anciennes:
        try:
            if json.loads(anciennes[-1]).get("cle") == cle:   # même demande (fin de tour relancée) : on remplace
                anciennes = anciennes[:-1]
        except ValueError:
            pass
    anciennes.append(json.dumps(ligne, ensure_ascii=False))
    fichier.write_text("\n".join(anciennes[-GARDER:]) + "\n", encoding="utf-8")
    return ligne


def lire_carnet(projet: Path, n: int) -> list[dict]:
    fichier = projet / ".circe" / "carnet.jsonl"
    if not fichier.exists():
        return []
    sortie = []
    for ligne in fichier.read_text(encoding="utf-8", errors="ignore").splitlines()[-n:]:
        try:
            sortie.append(json.loads(ligne))
        except ValueError:
            continue
    return sortie


def en_veille() -> bool:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import licence  # noqa: PLC0415 (même dossier)
        return licence.etat_rapide() == "veille"
    except Exception:
        return False


def main() -> int:
    try:
        import unique  # noqa: PLC0415 (même dossier)
        brut = unique.lire("carnet")
        if brut is None or en_veille():
            return 0
        noter_tour(json.loads(brut or "{}"))
    except Exception:
        return 0  # le carnet ne doit jamais gêner la fin d'un tour
    return 0


if __name__ == "__main__":
    sys.exit(main())
