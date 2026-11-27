"""CIRCÉ — Réflexe « rien d'imposé » (0.5) : hook UserPromptSubmit.

La garde laisse passer les gestes dont la protection n'est pas activée et les note dans .circe/propositions.jsonl. À la demande
suivante, ce réflexe rappelle à Claude de PROPOSER la protection à l'utilisateur, une seule fois par protection et par projet
(principe de la 0.5 : proposer, jamais appliquer d'office).
Il ne bloque rien et n'active rien. Bibliothèque standard seulement.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def dossier() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()) / ".circe"


def a_proposer() -> list:
    """Protections non activées, vues dans ce projet et jamais encore proposées ; marquées « proposées » une fois rendues."""
    import protections  # noqa: PLC0415
    d = dossier()
    f, vues_f = d / "propositions.jsonl", d / "propositions-vues.json"
    if not f.exists():
        return []
    try:
        vues = set(json.loads(vues_f.read_text(encoding="utf-8")).get("proposees", []))
    except (OSError, ValueError):
        vues = set()
    act = protections.actives()
    nouvelles, comptes = [], {}
    for ligne in f.read_text(encoding="utf-8", errors="ignore").splitlines()[-500:]:
        try:
            nom = json.loads(ligne).get("protection")
        except ValueError:
            continue
        if nom in protections.PROTECTIONS and nom not in act and nom not in vues:
            comptes[nom] = comptes.get(nom, 0) + 1
            if nom not in nouvelles:
                nouvelles.append(nom)
    if nouvelles:
        try:
            vues_f.write_text(json.dumps({"proposees": sorted(vues | set(nouvelles))}, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    return [(n, comptes[n]) for n in nouvelles]


def evaluer() -> dict | None:
    import protections  # noqa: PLC0415
    liste = a_proposer()
    if not liste:
        return None
    morceaux = [f"« {protections.PROTECTIONS[n][0]} » ({n} : {protections.PROTECTIONS[n][1]} ; {k} geste(s) passé(s) sans blocage)"
                for n, k in liste]
    commande = f'python "{Path(__file__).resolve().parent / "protections.py"}" activer <nom>'
    texte = ("[CIRCÉ, rien d'imposé : depuis la dernière demande, des gestes que ces protections auraient couverts sont passés, car "
             "l'utilisateur ne les a pas activées : " + " ; ".join(morceaux) + ". Dans ta réponse, PROPOSE-les-lui une seule fois, en une "
             "phrase, avec leur intérêt ; ne les active JAMAIS toi-même. S'il dit oui : « configure CIRCÉ » ou " + commande + ". "
             "S'il dit non, n'en reparle pas.]")
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": texte}}


def main() -> int:
    try:
        import unique  # noqa: PLC0415 (même dossier)
        if unique.lire("propositions") is None:
            return 0  # l'autre interprète traite déjà cet événement
        resultat = evaluer()
    except Exception:
        return 0
    if resultat:
        sys.stdout.write(json.dumps(resultat))
    return 0


if __name__ == "__main__":
    sys.exit(main())
