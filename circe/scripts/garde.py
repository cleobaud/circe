"""CIRCÉ — Système immunitaire : garde PreToolUse de Claude Code.

Lit le JSON du hook sur l'entrée standard ({tool_name, tool_input, permission_mode, ...}) et rend une décision :
  - « deny »  : geste irréversible ou dangereux (formatage, suppression de la racine ou du dossier personnel, écriture dans un
               dossier système) : toujours refusé, même si Claude Code l'autorise ;
  - « ask »   : geste sensible qui demande l'accord de l'humain (suppression récursive, git push, réécriture d'historique,
               mise en production, publication d'un paquet, script distant exécuté, lecture d'un secret, envoi ou publication
               par un outil MCP, modification des réglages de Claude Code) ;
  - rien      : le reste passe.
RIEN D'IMPOSÉ (0.5) : chaque règle appartient à une PROTECTION (scripts/protections.py). Par défaut, seule
« catastrophique » est en service (formater un disque, effacer la racine d'un disque ou le dossier personnel) ; une règle dont la
protection n'est pas activée ne bloque rien : le geste passe et une PROPOSITION est notée (.circe/propositions.jsonl), que le réflexe
propositions.py présente une fois. Désactiver une protection ou écrire ses réglages demande toujours l'accord de l'utilisateur.
Les autorisations déjà données dans Claude Code sont respectées (demande de l'utilisateur, 24/11 : « il check les autorisations
et il les touche pas ») : un geste « ask » déjà autorisé par une règle « allow » des réglages, ou en mode bypassPermissions,
passe sans nouvelle demande (scripts/autorisations.py). CIRCÉ ne modifie jamais ces réglages, et une écriture de ces réglages
par Claude demande toujours l'accord, quel que soit le mode (y compris bypassPermissions).
Bibliothèque standard seulement. Aucun argument de commande n'est écrit au journal : seulement l'outil, la décision et la raison.
LIMITE ASSUMÉE : c'est un filtre sur le TEXTE de la commande, pas un bac à sable. Il arrête l'erreur et le geste évident,
il ne remplace ni les permissions de Claude Code ni vos sauvegardes.
En cas de panne interne : refus pour un texte qui ressemble à un geste critique, passage pour le reste (jamais de plantage nu).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # Python embarqué (fichier ._pth) : le dossier du script n'est pas dans le chemin d'import

import autorisations  # noqa: E402 (même dossier)

OUTILS_SHELL = {"Bash", "PowerShell"}
OUTILS_ECRITURE = {"Write", "Edit", "NotebookEdit", "MultiEdit"}

SECRETS = (r"(?:(?<![A-Za-z0-9_.])\.env(?!\.(?:example|sample|template)\b)(?![A-Za-z0-9_])"
           r"|\bid_(?:rsa|ed25519|ecdsa)\b|\.pem\b|\.p12\b|\.pfx\b|\.git-credentials\b|\bcredentials\.json\b|\bauth\.json\b|\.npmrc\b|\.pypirc\b)")
LECTURE = (r"(?:\bcat\b|\btype\b|\bGet-Content\b|\bgc\b|\bhead\b|\btail\b|\bless\b|\bmore\b|\bsed\b|\bawk\b|\bgrep\b|\brg\b"
           r"|\bselect-string\b|\bsls\b|\bcopy\b|\bcp\b|\bCopy-Item\b|\bbase64\b|\bcertutil\b|\bcurl\b[^|;&\n]*(?:-d|--data|-F|-T)\b)")
RACINES = r"""(?:/|~/?|\$HOME/?|%USERPROFILE%\\?|[A-Za-z]:\\?|\*|\.\.?/?|/\*)(?=\s|$|["';&|])"""

REFUS_SHELL = [
    ("formatage d'un disque", re.compile(r"(?i)(?:\bformat(?:-volume)?\s+[a-z]:|\bFormat-Volume\b|\bdiskpart\b|\bmkfs(?:\.\w+)?\b|\bdd\s+[^|;&\n]*of=/dev/)")),
    ("suppression de la racine, du dossier personnel ou d'un lecteur entier",
     re.compile(rf"""(?i)(?:\brm\s+(?:-[a-z]*\s+)*-[a-z]*r[a-z]*\s+(?:-[a-z]+\s+)*["']?{RACINES}|\bRemove-Item\b[^|;&\n]*-Recurse\b[^|;&\n]*\s["']?{RACINES}|\brmdir\s+/s\s+(?:/q\s+)?["']?{RACINES})""")),
]
DEMANDE_SHELL = [
    ("secrets", "lecture d'un fichier de secrets (son contenu partirait dans la conversation)", re.compile(rf"(?is)(?:{LECTURE}.*{SECRETS}|{SECRETS}.*{LECTURE})")),
    ("suppression", "suppression récursive", re.compile(r"(?i)(?:\brm\s+(?:-[a-z]*\s+)*-[a-z]*r[a-z]*\b|\brm\s+--recursive\b|\bRemove-Item\b[^|;&\n]*-Recurse\b|\bri\b[^|;&\n]*-Recurse\b|\brmdir\s+/s\b|\brd\s+/s\b|\bdel\s+[^|;&\n]*/s\b|\bshutil\s*\.\s*rmtree\b|\brimraf\b|\bfs\s*\.\s*rm(?:Sync)?\s*\([^)]*recursive)")),
    ("historique_git", "réécriture ou perte d'historique git", re.compile(r"(?i)\bgit\b[^|;&\n]*(?:\breset\s+--hard\b|\bclean\s+-[a-z]*f|\bpush\b[^|;&\n]*(?:--force\b|--force-with-lease\b|\s-f\b)|\bbranch\s+-D\b|\bcheckout\s+--\s|\brestore\s+--source\b)")),
    ("git_push", "envoi vers un dépôt distant (git push)", re.compile(r"(?i)\bgit(?:\.exe)?\b(?:\s+-[Cc]\s+\S+|\s+--?[a-z][\w-]*(?:=\S+)?)*\s+push\b")),
    ("production", "mise en production", re.compile(r"(?i)(?:\bnetlify\b[^|;&\n]*\bdeploy\b[^|;&\n]*(?:--prod\b|\s-p\b)|\bvercel\b[^|;&\n]*(?:--prod\b|\bdeploy\b[^|;&\n]*--prod)|\bwrangler\b[^|;&\n]*\b(?:deploy|publish|pages\s+deploy)\b|\bfirebase\b[^|;&\n]*\bdeploy\b|\bflyctl?\b[^|;&\n]*\bdeploy\b|\bkubectl\b[^|;&\n]*\b(?:apply|delete)\b|\bterraform\b[^|;&\n]*\b(?:apply|destroy)\b)")),
    ("publication", "publication d'un paquet ou d'une image", re.compile(r"(?i)(?:\bnpm\s+publish\b|\bpnpm\s+publish\b|\byarn\s+publish\b|\btwine\s+upload\b|\bcargo\s+publish\b|\bdocker\s+push\b|\bgh\s+release\s+create\b)")),
    ("script_distant", "script téléchargé puis exécuté", re.compile(r"(?i)(?:\b(?:curl|wget)\b[^|;&\n]*\|\s*(?:sudo\s+)?(?:ba|z)?sh\b|\b(?:iwr|Invoke-WebRequest|irm|Invoke-RestMethod)\b[^|;&\n]*\|\s*(?:iex|Invoke-Expression)\b)")),
    ("base_de_donnees", "base de données vidée ou supprimée", re.compile(r"(?i)\b(?:DROP\s+(?:TABLE|DATABASE|SCHEMA)|TRUNCATE\s+TABLE)\b|\bDELETE\s+FROM\s+\w+\s*(?:;|$)")),
]
ECRITURE_INTERDITE = re.compile(r"(?i)^(?:[a-z]:)?[/\\]+(?:windows|program files(?: \(x86\))?|programdata|system|etc|usr|bin|sbin|boot)(?:[/\\]|$)")
ECRITURE_SECRET = re.compile(SECRETS)
MCP_SENSIBLE = re.compile(r"(?i)^(?:send|reply|forward|publish|post|tweet|upload|delete|remove|trash|transfer|pay|charge|refund|deploy|invite|share|create_(?:post|invoice|payment|charge|refund))")
OUTILS_LECTURE = {"Read", "Grep"}
# Réglages de Claude Code (là où vivent les autorisations de l'utilisateur) : CIRCÉ n'y touche jamais sans lui.
_REGLAGES_BASE = r"\.claude[/\\]+(?:[^\s\"'|;&<>]*[/\\]+)?settings(?:\.local)?\.json\b|\bclaude(?:\.exe)?\s+config\s+(?:add|set|remove)\b"
DEMANDE_REGLAGES = ("modification possible des réglages de Claude Code (là où sont vos autorisations) : CIRCÉ n'y touche jamais "
                    "sans vous, votre accord est demandé.")
AIDE_AUTORISER = (" Pour qu'il ne demande plus : autorisez cet outil dans Claude Code (/permissions, règle « allow » avec son nom "
                  "exact) ; CIRCÉ respecte les autorisations que vous avez déjà données.")
# Les choix de protection appartiennent à l'utilisateur : les désactiver, ou écrire leur fichier, demande toujours son accord.
CHOIX_PROTECTIONS = re.compile(r"(?i)(?:protections\.py[\"']?\s+(?:desactiver|désactiver)\b|\.circe[/\\]+protections\.json\b|CIRCE_PROTECTIONS\s*=)")
DEMANDE_CHOIX = "modification de vos choix de protection CIRCÉ : seule votre décision compte, votre accord est demandé."
CRITIQUE_GROSSIER = re.compile(r"(?i)(?:rm\s+-[a-z]*r|Remove-Item|rmdir\s+/s|format|diskpart|git\s+push|--force|deploy|publish|\.env\b|id_rsa"
                               r"|settings(?:\.local)?\.json)")


def motif_reglages() -> re.Pattern:
    """Les chemins des réglages : « .claude/settings*.json » partout, et le dossier de configuration réel (CLAUDE_CONFIG_DIR)."""
    morceaux = [m for m in re.split(r"[/\\]+", str(autorisations.dossier_config())) if m]
    conf = r"[/\\]+".join(re.escape(m) for m in morceaux) + r"[/\\]+settings(?:\.local)?\.json\b"
    return re.compile(rf"(?i)(?:{_REGLAGES_BASE}|{conf})")


def est_reglage(chemin: str) -> bool:
    if not chemin:
        return False
    p = Path(chemin)
    if p.name.lower() not in ("settings.json", "settings.local.json"):
        return False
    if p.parent.name.lower() == ".claude":
        return True
    try:
        return os.path.normcase(os.path.abspath(p.parent)) == os.path.normcase(os.path.abspath(autorisations.dossier_config()))
    except (OSError, ValueError):
        return False


def _decision(decision: str, raison: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                   "permissionDecisionReason": f"CIRCÉ, système immunitaire : {raison}"}}


def evaluer(evenement: dict, propositions: list | None = None) -> dict | None:
    """Rend la décision (dict au format des hooks) ou None si l'action passe. Une règle dont la protection n'est pas activée ne
    décide rien : (protection, raison) est ajouté à `propositions` (si une liste est donnée) et le contrôle continue."""
    import protections  # noqa: PLC0415 (même dossier)

    def en_service(nom: str, raison: str) -> bool:
        if protections.active(nom):
            return True
        if propositions is not None and (nom, raison) not in propositions:
            propositions.append((nom, raison))
        return False

    outil = evenement.get("tool_name") or ""
    entree = evenement.get("tool_input") or {}
    bypass = evenement.get("permission_mode") == "bypassPermissions"
    projet = Path(os.environ.get("CLAUDE_PROJECT_DIR") or evenement.get("cwd") or os.getcwd())
    _cache: dict = {}

    def regles() -> list[str]:
        if "allow" not in _cache:
            _cache["allow"] = autorisations.lire(projet)["allow"]
        return _cache["allow"]

    if outil in OUTILS_SHELL:
        cmd = str(entree.get("command") or "")
        for raison, motif in REFUS_SHELL:
            if motif.search(cmd) and en_service("catastrophique", raison):
                return _decision("deny", raison + " : geste refusé ; si c'est voulu, faites-le vous-même hors de Claude.")
        if CHOIX_PROTECTIONS.search(cmd):
            return _decision("ask", DEMANDE_CHOIX)
        if motif_reglages().search(cmd) and en_service("reglages", "modification des réglages de Claude Code"):
            return _decision("ask", DEMANDE_REGLAGES)  # même en mode bypass (relecture Codex, tour 2), une fois la protection activée
        for nom, raison, motif in DEMANDE_SHELL:
            if motif.search(cmd) and en_service(nom, raison):
                if bypass or autorisations.shell_autorise(outil, cmd, motif, regles()):
                    continue  # déjà autorisé par l'utilisateur dans Claude Code : pas de nouvelle demande
                rappel = " Avant d'accepter : le point de recul (circe:recul) a-t-il été fait sur ce qui part ?" if raison.startswith(("mise en production", "publication")) else ""
                return _decision("ask", raison + " : votre accord est demandé." + rappel)
        return None
    if outil in OUTILS_ECRITURE:
        chemin = str(entree.get("file_path") or entree.get("notebook_path") or "")
        if CHOIX_PROTECTIONS.search(chemin):
            return _decision("ask", DEMANDE_CHOIX)
        if ECRITURE_INTERDITE.match(chemin) and en_service("systeme", "écriture dans un dossier du système"):
            return _decision("deny", "écriture dans un dossier du système : refusée.")
        if est_reglage(chemin) and en_service("reglages", "modification des réglages de Claude Code"):
            return _decision("ask", DEMANDE_REGLAGES)
        if ECRITURE_SECRET.search(chemin) and en_service("secrets", "écriture dans un fichier de secrets"):
            if bypass or evenement.get("permission_mode") == "acceptEdits" or autorisations.outil_entier(outil, regles()):
                return None
            return _decision("ask", "écriture dans un fichier de secrets : votre accord est demandé.")
        return None
    if outil in OUTILS_LECTURE:
        chemin = str(entree.get("file_path") or entree.get("path") or "")
        if ECRITURE_SECRET.search(chemin) and not (bypass or autorisations.outil_entier(outil, regles())) \
                and en_service("secrets", "lecture d'un fichier de secrets"):
            return _decision("ask", "lecture d'un fichier de secrets (son contenu partirait dans la conversation) : votre accord est demandé.")
        return None
    if outil.startswith("mcp__"):
        texte = json.dumps(entree, ensure_ascii=False)
        if CHOIX_PROTECTIONS.search(texte):
            return _decision("ask", DEMANDE_CHOIX)
        if motif_reglages().search(texte) and en_service("reglages", "modification des réglages de Claude Code"):
            return _decision("ask", DEMANDE_REGLAGES)  # un outil de fichiers MCP vers les réglages (relecture Codex du 24/11)
        nom_action = outil.split("__")[-1]
        if MCP_SENSIBLE.search(nom_action) and not (bypass or autorisations.mcp_autorise(outil, regles())) \
                and en_service("exterieur", f"action vers l'extérieur ({nom_action})"):
            return _decision("ask", f"action vers l'extérieur ({nom_action}) : votre accord est demandé avant l'envoi." + AIDE_AUTORISER)
    return None


def _journal(outil: str, decision: str, raison: str) -> None:
    racine = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    try:
        dossier = racine / ".circe"
        dossier.mkdir(exist_ok=True)
        ligne = {"heure": time.strftime("%Y-%m-%dT%H:%M:%S"), "outil": outil, "decision": decision, "raison": raison}
        with open(dossier / "journal-immunitaire.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _protections_choisies() -> bool:
    """L'utilisateur a activé au moins une protection de plus que celles par défaut : en cas de panne, on reste prudent pour lui."""
    try:
        import protections  # noqa: PLC0415
        return bool(protections.actives() - set(protections.DEFAUT))
    except Exception:
        return False


def _noter_propositions(outil: str, props: list) -> None:
    """Gestes qu'une protection non activée aurait couverts : notés pour être PROPOSÉS (jamais la commande elle-même)."""
    racine = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    try:
        dossier = racine / ".circe"
        dossier.mkdir(exist_ok=True)
        with open(dossier / "propositions.jsonl", "a", encoding="utf-8") as f:
            for nom, raison in props:
                f.write(json.dumps({"heure": time.strftime("%Y-%m-%dT%H:%M:%S"), "outil": outil, "protection": nom, "raison": raison},
                                   ensure_ascii=False) + "\n")
    except OSError:
        pass


def lire_entree() -> str:
    """Le JSON des hooks arrive en UTF-8 ; sous Windows, Python lirait sinon dans l'encodage local (accents cassés)."""
    tampon = getattr(sys.stdin, "buffer", None)
    brut = tampon.read().decode("utf-8", "replace") if tampon is not None else sys.stdin.read()
    return brut.replace("﻿", "").strip()  # marque d'ordre des octets (BOM) ajoutée par certains hôtes Windows : ignorée


def main() -> int:
    import unique  # noqa: PLC0415 (même dossier)
    brut = unique.lire("garde")
    if brut is None:
        return 0  # l'autre interprète traite déjà cet événement
    props: list = []
    try:
        evenement = json.loads(brut or "{}")
        resultat = evaluer(evenement, props)
        if props and not resultat:
            _noter_propositions(str(evenement.get("tool_name") or "?"), props)
    except Exception:  # panne interne : refus seulement d'un geste catastrophique (rien d'imposé), sinon passage
        if any(m.search(brut or "") for _, m in REFUS_SHELL) or (CRITIQUE_GROSSIER.search(brut or "") and _protections_choisies()):
            resultat = _decision("deny", "contrôle impossible (panne du garde) sur un geste qui ressemble à un geste critique : refusé par prudence.")
            evenement = {}
        else:
            return 0
    if resultat:
        sortie = resultat["hookSpecificOutput"]
        _journal(str(evenement.get("tool_name") or "?"), sortie["permissionDecision"], sortie["permissionDecisionReason"])
        sys.stdout.write(json.dumps(resultat))  # ASCII échappé : lisible quel que soit l'encodage de la console
    return 0


if __name__ == "__main__":
    sys.exit(main())
