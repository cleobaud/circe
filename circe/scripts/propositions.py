"""CIRCÉ — Réflexes de PROPOSITION (hook UserPromptSubmit) : les protections non activées, et le plan de projet.

La garde laisse passer les gestes dont la protection n'est pas activée et les note dans .circe/propositions.jsonl. À la demande
suivante, ce réflexe rappelle à Claude de PROPOSER la protection à l'utilisateur, une seule fois par protection et par projet
(principe de la 0.5 : proposer, jamais appliquer d'office).
Il ne bloque rien et n'active rien. Bibliothèque standard seulement.

Défaut D4 (audit du 27/11/2026) : `circe:plan` n'était jamais proposé. Constat chiffré sur un projet réel — trois jours,
neuf demandes au carnet, des dizaines de fichiers produits, et aucun `.circe/PLAN.md`. Ce réflexe le propose donc, mais
sur un FAIT et non sur les mots de la demande : quand le projet a déjà accumulé du vrai travail (plusieurs demandes dont
au moins une qui a touché des fichiers) et qu'aucun plan n'existe. Une seule fois par projet.
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


DEMANDES_AVANT_PLAN = 3          # en dessous, c'est une question ou un petit correctif : un plan serait de la paperasse


def plan_a_proposer() -> dict | None:
    """Le projet a-t-il assez de travail derrière lui pour mériter un plan, sans en avoir un ?"""
    d = dossier()
    if (d / "PLAN.md").exists():
        return None
    carnet = d / "carnet.jsonl"
    if not carnet.exists():
        return None
    try:
        if json.loads((d / "propositions-vues.json").read_text(encoding="utf-8")).get("plan"):
            return None
    except (OSError, ValueError):
        pass
    demandes, avec_fichiers = 0, 0
    try:
        for ligne in carnet.read_text(encoding="utf-8", errors="ignore").splitlines()[-200:]:
            try:
                e = json.loads(ligne)
            except ValueError:
                continue
            demandes += 1
            if e.get("fichiers"):
                avec_fichiers += 1
    except OSError:
        return None
    if demandes < DEMANDES_AVANT_PLAN or avec_fichiers < 1:
        return None
    return {"demandes": demandes, "avec_fichiers": avec_fichiers}


def marquer_plan_propose() -> None:
    f = dossier() / "propositions-vues.json"
    try:
        contenu = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        contenu = {}
    contenu["plan"] = True
    try:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(contenu, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def texte_plan(mesure: dict) -> str:
    return ("[CIRCÉ, proposition : ce projet a déjà " + str(mesure["demandes"]) + " demandes au carnet, dont "
            + str(mesure["avec_fichiers"]) + " qui ont produit ou modifié des fichiers, et il n'a toujours pas de plan "
            "(`.circe/PLAN.md`). Propose-lui UNE fois, en une phrase, d'ouvrir `circe:plan` : le travail s'y suit ligne "
            "par ligne, chaque ligne cochée avec sa preuve, et une session suivante reprend au bon endroit. "
            "S'il dit non, n'en reparle pas.]")


def evaluer() -> dict | None:
    import protections  # noqa: PLC0415
    liste = a_proposer()
    plan = plan_a_proposer()
    if not liste and plan:
        marquer_plan_propose()
        return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": texte_plan(plan)}}
    if not liste:
        return None
    morceaux = [f"« {protections.PROTECTIONS[n][0]} » ({n} : {protections.PROTECTIONS[n][1]} ; {k} geste(s) passé(s) sans blocage)"
                for n, k in liste]
    commande = f'python "{Path(__file__).resolve().parent / "protections.py"}" activer <nom>'
    texte = ("[CIRCÉ, rien d'imposé : depuis la dernière demande, des gestes que ces protections auraient couverts sont passés, car "
             "l'utilisateur ne les a pas activées : " + " ; ".join(morceaux) + ". Dans ta réponse, PROPOSE-les-lui une seule fois, en une "
             "phrase, avec leur intérêt ; ne les active JAMAIS toi-même. S'il dit oui : « configure CIRCÉ » ou " + commande + ". "
             "S'il dit non, n'en reparle pas.]")
    if plan:
        marquer_plan_propose()
        texte += "\n" + texte_plan(plan)
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
