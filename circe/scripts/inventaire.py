"""CIRCÉ — Inventaire du poste et de Claude Code, pour configurer CIRCÉ au mieux (compétence circe:configurer).

  python inventaire.py            affiche l'inventaire en JSON (lecture seule)

Ce qui est relevé : le système, Python, la version de Claude Code, les outils de création présents (ffmpeg, Node, Git,
Blender, navigateur…), une automatisation n8n locale qui répond, les NOMS des serveurs MCP, extensions et compétences déjà
installés, la présence de CLAUDE.md, les autorisations déjà données dans Claude Code (règles « allow », mode par défaut :
CIRCÉ les respecte et n'y touche jamais), l'état de CIRCÉ (licence, automatisation branchée, profil).
Ce qui n'est JAMAIS lu : les valeurs des réglages (jetons, clés, mots de passe), le contenu des fichiers du projet.
Rien n'est installé ni modifié. Rien n'est envoyé. Bibliothèque standard seulement.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # Python embarqué (fichier ._pth)

import autorisations  # noqa: E402 (même dossier)

OUTILS = {
    "ffmpeg": "montage et contrôle des vidéos", "ffprobe": "mesures des vidéos", "node": "pages animées, Remotion, scripts web",
    "npx": "outils web sans installation", "git": "historique et sauvegarde du projet", "blender": "3D et rendus",
    "gh": "GitHub", "docker": "conteneurs", "uv": "projets Python", "magick": "retouche d'images en lot",
}


def version(cmd: list[str]) -> str | None:
    exe = shutil.which(cmd[0])
    if not exe:
        return None
    try:
        r = subprocess.run([exe, *cmd[1:]], capture_output=True, timeout=15)
        sortie = (r.stdout or r.stderr).decode("utf-8", "replace").strip().splitlines()
        return sortie[0][:80] if sortie else "présent"
    except (OSError, subprocess.TimeoutExpired):
        return "présent (version illisible)"


def blender() -> str | None:
    v = version(["blender", "--version"])
    if v:
        return v
    if platform.system() == "Windows":
        for base in (os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", "")):
            dossier = Path(base) / "Blender Foundation"
            if base and dossier.exists():
                trouves = sorted(dossier.glob("Blender*/blender.exe"))
                if trouves:
                    return f"présent ({trouves[-1].parent.name})"
        steam = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Steam" / "steamapps" / "common" / "Blender" / "blender.exe"
        if steam.exists():
            return "présent (Steam)"
    # versions portables rangées dans un dossier d'outils du dossier personnel (ex. ~/Outils/blender-5.2-windows-x64/)
    for dossier in ("Outils", "Tools", "Applications", "Programmes", "Apps", "Downloads", "Téléchargements"):
        racine = Path.home() / dossier
        if racine.is_dir():
            trouves = sorted(list(racine.glob("blender*/blender.exe")) + list(racine.glob("blender*/blender")) + list(racine.glob("*/blender*/blender.exe")))
            if trouves:
                return f"présent, version portable ({trouves[-1].parent.name})"
    if Path("/Applications/Blender.app").exists():
        return "présent (Blender.app)"
    return None


def navigateur() -> str | None:
    try:
        import regarder  # noqa: PLC0415 (même dossier)
        return regarder.navigateur()
    except Exception:
        return None


def n8n_local() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:5678/healthz", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def noms_json(chemin: Path, cle: str) -> list[str]:
    """Seulement les NOMS (clés) d'une section d'un fichier JSON de réglages, jamais les valeurs."""
    try:
        d = json.loads(chemin.read_text(encoding="utf-8"))
        section = d.get(cle) or {}
        return sorted(section.keys()) if isinstance(section, dict) else []
    except (OSError, ValueError, AttributeError):
        return []


def claude_code(projet: Path) -> dict:
    maison = Path.home()
    conf = Path(os.environ.get("CLAUDE_CONFIG_DIR") or maison / ".claude")
    mcp = set(noms_json(maison / ".claude.json", "mcpServers")) | set(noms_json(projet / ".mcp.json", "mcpServers"))
    extensions = []
    try:
        installees = json.loads((conf / "plugins" / "installed_plugins.json").read_text(encoding="utf-8"))
        brut = installees.get("plugins", installees)
        extensions = sorted(brut.keys()) if isinstance(brut, dict) else []
    except (OSError, ValueError, AttributeError):
        pass
    competences = sorted(p.parent.name for p in (conf / "skills").glob("*/SKILL.md")) if (conf / "skills").exists() else []
    competences_projet = sorted(p.parent.name for p in (projet / ".claude" / "skills").glob("*/SKILL.md")) if (projet / ".claude" / "skills").exists() else []
    return {
        "version": version(["claude", "--version"]),
        "serveurs_mcp": sorted(mcp),
        "extensions": extensions,
        "competences_personnelles": competences,
        "competences_du_projet": competences_projet,
        "claude_md_personnel": (conf / "CLAUDE.md").exists(),
        "claude_md_du_projet": (projet / "CLAUDE.md").exists() or (projet / ".claude" / "CLAUDE.md").exists(),
        # Ce que l'utilisateur a déjà autorisé : CIRCÉ le respecte (pas de nouvelle demande) et n'y touche jamais.
        "autorisations_deja_donnees": autorisations.resume(projet),
    }


def projet_info(projet: Path) -> dict:
    marqueurs = {"package.json": "JavaScript/Node", "pyproject.toml": "Python", "requirements.txt": "Python", "index.html": "site statique",
                 "Cargo.toml": "Rust", "go.mod": "Go", "composer.json": "PHP"}
    return {"dossier": projet.name, "git": (projet / ".git").exists(),
            "types": sorted({v for k, v in marqueurs.items() if (projet / k).exists()}),
            "fichiers_blend": any(projet.glob("*.blend")), "videos": sum(1 for _ in projet.glob("*.mp4"))}


def circe(projet: Path) -> dict:
    etat = {"licence": "inconnu", "automatisation_branchee": False, "profil": (projet / ".circe" / "PROFIL.md").exists()}
    try:
        import licence  # noqa: PLC0415
        etat["licence"] = licence.etat_rapide()
    except Exception:
        pass
    try:
        import sortie  # noqa: PLC0415
        etat["automatisation_branchee"] = bool(sortie.adresse_branchee())
    except Exception:
        pass
    return etat


def inventaire() -> dict:
    projet = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    outils = {nom: version([nom, "-version" if nom in ("ffmpeg", "ffprobe") else "--version"]) for nom in OUTILS if nom != "blender"}
    outils["blender"] = blender()
    return {
        "systeme": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "python": platform.python_version(),
        "outils": {k: {"present": v is not None, "version": v, "sert_a": OUTILS[k]} for k, v in outils.items()},
        "navigateur": navigateur(),
        "n8n_local": n8n_local(),
        "claude_code": claude_code(projet),
        "projet": projet_info(projet),
        "circe": circe(projet),
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(inventaire(), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
