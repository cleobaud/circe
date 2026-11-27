"""CIRCÉ — Système immunitaire : hook Stop « pas de « fini » sans preuve ».

Quand Claude s'apprête à rendre la main en annonçant que le travail est fini, ce hook lit son dernier message.
S'il annonce la fin sans aucune trace de preuve (commande et sortie, test, fichier, adresse, niveau de preuve),
il lui demande de continuer : donner la preuve, ou dire clairement ce qui n'est pas vérifié.
Une seule relance par fin de tour (champ « stop_hook_active ») : jamais de boucle.
Bibliothèque standard seulement ; rien n'est écrit ailleurs que dans le journal du projet (.circe/).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # Python embarqué (fichier ._pth) : le dossier du script n'est pas dans le chemin d'import

ANNONCE = re.compile(r"(?i)(?:\b(?:c'est |tout est |j'ai )?(?:fini|terminé|termine|achevé|livré)\b|\bc'est fait\b|\btout est prêt\b|\bprêt à (?:livrer|publier|l'emploi)\b"
                     r"|\b(?:done|completed|finished|all set|ready to ship)\b)")
# Marqueurs de preuve volontairement précis (relecture Codex du 24/11 : « sortie », « OK », « passed » seuls étaient trop larges).
PREUVE = re.compile(r"(?s)(?:```|\b[Pp]reuve\b|\bVÉRIFIÉ\b|\bINFÉRÉ\b|\bINCONNU\b|\bDÉCLARÉ\b|\b[Vv]érifié par\b"
                    r"|\b\d+\s*(?:tests?|essais?)\b[^\n]{0,30}\b(?:OK|ok|passés?|passent|verts?|réussis?|passed)\b|\b\d+\s*/\s*\d+\s*(?:tests?|OK)\b"
                    r"|\bcode (?:de sortie )?0\b|\bexit code 0\b|https?://\S+|[\w-]+\.(?:py|js|ts|tsx|html|css|md|json|png|jpe?g|webp|mp4|blend|glb|pdf|zip)\b"
                    r"|\b(?:[Nn]on|[Pp]as|NON|PAS)(?: encore)? (?:vérifié|VÉRIFIÉ)e?s?\b|\bLighthouse\s+\d+)")
# Ce qui n'est pas une annonce de fin (essai réel du 24/11 : « Dis-moi « fait » quand c'est terminé » relançait Claude à tort) :
# un mot cité entre guillemets, une proposition « quand / une fois / dès que … terminé », une question.
CITATION = re.compile(r"«[^»]{0,80}»|“[^”]{0,80}”|\"[^\"\n]{0,80}\"|`[^`\n]{0,80}`")
CONDITION = re.compile(r"(?i)\b(?:quand|lorsque|dès que|une fois(?: que)?|avant que|jusqu.à ce que|si|when|once|after|until|if)\b"
                       r"[^.!?\n]{0,40}?\b(?:fini|terminé|termine|achevé|livré|fait|prêt|done|finished|completed)\b")
# Ce qui est remis à plus tard n'est pas une preuve (relecture Codex du 24/11 : « C'est fini. À vérifier plus tard : `rapport.pdf`. »
# passait, le nom de fichier comptant comme preuve). La proposition qui suit ces mots est retirée avant de chercher la preuve.
# « pas vérifié » / « non vérifié » restent une déclaration honnête (c'est ce que demande la relance).
REPORT = re.compile(r"(?i)(?:\bà (?:vérifier|tester|contrôler|faire|relire|confirmer)\b|\breste à\b|\bplus tard\b|\bensuite\b\s*:|\bTODO\b"
                    r"|\bto (?:verify|check|test|do)\b|\blater\b|\bpending\b)[^.!?\n]*")


def annonce(texte: str) -> bool:
    """Vrai si le texte annonce une fin : hors citations, hors propositions conditionnelles, hors questions."""
    texte = CONDITION.sub(" ", CITATION.sub(" ", texte))
    phrases = re.split(r"(?<=[.!?])\s+|\n+", texte)
    return any(ANNONCE.search(ph) for ph in phrases if not ph.rstrip().endswith("?"))


RAISON = ("CIRCÉ, système immunitaire : tu annonces que c'est fini, mais ton message ne montre aucune preuve. "
          "Avant de rendre la main : donne la preuve (commande lancée et sa sortie, test, fichier produit, capture, adresse), "
          "ou dis clairement ce qui n'est PAS vérifié, avec un niveau : VÉRIFIÉ, DÉCLARÉ, INFÉRÉ ou INCONNU. "
          "Si la tâche n'est pas finie, dis ce qui reste.")


def _textes(contenu) -> list[str]:
    if isinstance(contenu, str):
        return [contenu]
    if isinstance(contenu, list):
        return [b.get("text", "") for b in contenu if isinstance(b, dict) and b.get("type") == "text"]
    return []


def _systeme(texte: str) -> bool:
    """Texte injecté par Claude Code (contenu d'une compétence, image lue, rappel du système), pas tapé par l'utilisateur."""
    debut = texte.lstrip()
    return debut.startswith(("<", "Base directory for this skill", "[Request interrupted", "[Image"))


def dernier_message_assistant(chemin: Path) -> str:
    """Texte des messages de l'assistant depuis la dernière vraie demande de l'utilisateur (pas un résultat d'outil)."""
    morceaux: list[str] = []
    try:
        lignes = chemin.read_text(encoding="utf-8-sig", errors="ignore").replace("﻿", "").splitlines()
    except OSError:
        return ""
    for ligne in lignes:
        try:
            entree = json.loads(ligne)
        except ValueError:
            continue
        message = entree.get("message") or {}
        role = entree.get("type") or message.get("role")
        if role == "user":
            textes = [t for t in _textes(message.get("content")) if t.strip()]
            # Relecture Codex du 24/11 + journal réel : une compétence chargée ou une image lue ajoutent une ligne « user »
            # marquée isMeta (« Base directory for this skill… », « [Image: … ] ») ; ce n'est pas une nouvelle demande.
            if textes and not entree.get("isMeta") and not _systeme(textes[0]):
                morceaux = []
        elif role == "assistant":
            morceaux.extend(_textes(message.get("content")))
    return "\n".join(morceaux)


def en_veille() -> bool:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import licence  # noqa: PLC0415 (même dossier)
        return licence.etat_rapide() == "veille"
    except Exception:
        return False


def evaluer(evenement: dict) -> dict | None:
    if evenement.get("stop_hook_active") or en_veille():
        return None
    chemin = evenement.get("transcript_path")
    if not chemin:
        return None
    texte = dernier_message_assistant(Path(chemin))
    if texte and annonce(texte) and not PREUVE.search(REPORT.sub(" ", texte)):
        return {"decision": "block", "reason": RAISON}
    return None


def main() -> int:
    try:
        import unique  # noqa: PLC0415 (même dossier)
        brut = unique.lire("preuve")
        if brut is None:
            return 0  # l'autre interprète traite déjà cet événement
        evenement = json.loads(brut or "{}")
        resultat = evaluer(evenement)
    except Exception:
        return 0  # ce contrôle ne doit jamais empêcher de rendre la main en cas de panne
    if resultat:
        try:
            dossier = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()) / ".circe"
            dossier.mkdir(exist_ok=True)
            with open(dossier / "journal-immunitaire.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({"heure": time.strftime("%Y-%m-%dT%H:%M:%S"), "outil": "Stop", "decision": "relance",
                                    "raison": "fin annoncée sans preuve"}, ensure_ascii=False) + "\n")
        except OSError:
            pass
        sys.stdout.write(json.dumps(resultat))
    return 0


if __name__ == "__main__":
    sys.exit(main())
