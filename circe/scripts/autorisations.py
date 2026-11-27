"""CIRCÉ — Les autorisations déjà données dans Claude Code (lecture seule).

Demande de l'utilisateur (24/11) : « quand il arrive sur un système qui est déjà fait, il check les autorisations et il les
touche pas ». La garde ne redemande jamais ce que l'utilisateur a déjà autorisé dans Claude Code, et CIRCÉ ne modifie jamais
ces réglages (une écriture de ces fichiers par Claude demande l'accord : voir garde.py).

Fichiers lus (seulement la liste « permissions.allow », jamais d'autre valeur) :
  - réglages personnels : <dossier de configuration de Claude Code>/settings.json et settings.local.json ;
  - réglages du projet : <projet>/.claude/settings.json et <projet>/.claude/settings.local.json.
Règles comprises (syntaxe de Claude Code) :
  - « Outil » seul ou « Outil(*) » : tout l'outil (Bash, PowerShell, Edit, Write, Read...) ;
  - « mcp__serveur », « mcp__serveur__* » : tous les outils d'un serveur ; « mcp__serveur__outil » : cet outil ;
  - « Bash(préfixe:*) », « Bash(git push *) » (étoile = n'importe quoi), « Bash(commande exacte) » ; idem PowerShell.
  Une règle de chemin (« Edit(./src/**) ») n'est pas interprétée : CIRCÉ demande alors comme avant (prudence).
Bibliothèque standard seulement.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

SEPARATEURS = re.compile(r"\s*(?:&&|\|\||;|\||(?<![<>])&(?![>&])|\r?\n)\s*")
# Une commande imbriquée ($(...), `...`, <(...), >(...)) cache un autre geste : une règle sur le début de la ligne ne la couvre pas.
IMBRIQUE = re.compile(r"\$\(|`|<\(|>\(")
REGLE = re.compile(r"([^()\s]+)(?:\((.*)\))?", re.S)
# Claude Code : une règle « Edit » couvre tous les outils d'écriture de fichiers ; une règle « Read » couvre la lecture et la recherche.
FAMILLE = {"Write": "Edit", "MultiEdit": "Edit", "NotebookEdit": "Edit", "Edit": "Edit", "Read": "Read", "Grep": "Read", "Glob": "Read"}


def dossier_config() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def fichiers_reglages(projet: Path | None) -> list[Path]:
    conf = dossier_config()
    candidats = [conf / "settings.json", conf / "settings.local.json"]
    if projet:
        candidats += [projet / ".claude" / "settings.json", projet / ".claude" / "settings.local.json"]
    vus: set[str] = set()
    fichiers = []
    for f in candidats:
        cle = os.path.normcase(os.path.abspath(f))
        if cle not in vus:
            vus.add(cle)
            fichiers.append(f)
    return fichiers


def lire(projet: Path | None) -> dict:
    """{"allow": [règles], "mode": defaultMode ou None, "fichiers": [fichiers lus]} ; un fichier illisible est ignoré."""
    regles: list[str] = []
    mode = None
    lus = []
    for f in fichiers_reglages(projet):
        try:
            d = json.loads(f.read_text(encoding="utf-8-sig"))
            perm = d.get("permissions") or {}
            allow = perm.get("allow") or []
        except (OSError, ValueError, AttributeError, TypeError):
            continue
        lus.append(str(f))
        regles += [r.strip() for r in allow if isinstance(r, str) and r.strip()]
        if isinstance(perm.get("defaultMode"), str):
            mode = perm["defaultMode"]
    return {"allow": regles, "mode": mode, "fichiers": lus}


def decouper(regle: str) -> tuple[str | None, str | None]:
    m = REGLE.fullmatch(regle.strip())
    return (m.group(1), m.group(2)) if m else (None, None)


def _tout(contenu: str | None) -> bool:
    return contenu is None or contenu.strip() in ("", "*")


def outil_entier(outil: str, regles: list[str]) -> bool:
    """Vrai si une règle autorise TOUT l'outil (ou sa famille, ex. « Edit » pour Write)."""
    noms = {outil, FAMILLE.get(outil, outil)}
    return any(nom in noms and _tout(contenu) for nom, contenu in map(decouper, regles))


def couvre_commande(contenu: str, commande: str) -> bool:
    contenu, commande = contenu.strip(), commande.strip()
    if contenu.endswith(":*"):
        prefixe = contenu[:-2].rstrip()
        return commande == prefixe or commande.startswith(prefixe + " ")
    if "*" in contenu:
        return re.fullmatch(".*".join(re.escape(p) for p in contenu.split("*")), commande, re.S) is not None
    return commande == contenu


def shell_autorise(outil: str, commande: str, motif: re.Pattern, regles: list[str]) -> bool:
    """Vrai si l'utilisateur a déjà autorisé, dans Claude Code, chaque morceau de la commande qui déclenche ce motif."""
    if outil_entier(outil, regles):
        return True
    contenus = [c for nom, c in map(decouper, regles) if nom == outil and not _tout(c)]
    if not contenus:
        return False
    concernes = [s for s in SEPARATEURS.split(commande.strip()) if s and motif.search(s)]
    if not concernes:  # le motif enjambe plusieurs morceaux (ex. « curl ... | sh ») : seule une autorisation de tout l'outil le couvre
        return False
    if any(IMBRIQUE.search(s) for s in concernes):
        return False
    return all(any(couvre_commande(c, s) for c in contenus) for s in concernes)


def mcp_autorise(outil: str, regles: list[str]) -> bool:
    """Vrai si l'outil MCP est déjà autorisé : par son nom exact, ou par son serveur entier."""
    for nom, contenu in map(decouper, regles):
        if not nom or not nom.startswith("mcp__") or not _tout(contenu):
            continue
        if nom == outil:
            return True
        if nom.endswith("__*") and outil.startswith(nom[:-1]):
            return True
        if nom.count("__") == 1 and outil.startswith(nom + "__"):
            return True
    return False


def resume(projet: Path | None) -> dict:
    """Pour l'inventaire de « configure CIRCÉ » : ce qui est déjà autorisé, que CIRCÉ respecte et ne touche pas."""
    d = lire(projet)
    return {"mode_par_defaut": d["mode"], "regles_allow": d["allow"][:60], "nombre_de_regles_allow": len(d["allow"]),
            "outils_mcp_autorises": sorted(r for r in d["allow"] if r.startswith("mcp__")), "fichiers_lus": d["fichiers"]}
