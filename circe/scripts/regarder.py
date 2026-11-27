"""CIRCÉ — Regarder des exemples pour de vrai, avant de concevoir.

  python regarder.py <fichier vidéo | fichier image | adresse https://...> [...]   [--images 12]

Pour une VIDÉO (ffmpeg et ffprobe nécessaires) : durée, cadre (vertical, horizontal, carré), images par seconde, son,
nombre de plans (changements de scène) et plans par minute, 12 images à intervalles réguliers et une PLANCHE qui les assemble.
Pour un SITE : deux captures (ordinateur 1440 px, petit écran 500 px : la largeur minimale du navigateur sans fenêtre, proche d'un téléphone) par Chrome ou Edge.
Pour une IMAGE : copiée telle quelle, avec sa taille.
Tout reste sur le PC : `<projet>/.circe/exemples/<nom>/`. Le résumé s'affiche en JSON ; Claude regarde ensuite les images
(outil de lecture d'image) et écrit la fiche d'analyse (compétence circe:exemples).
Bibliothèque standard seulement. Les vidéos en ligne (TikTok, YouTube…) ne sont pas téléchargées : fournir le fichier.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import struct
import subprocess
import sys
import unicodedata
from pathlib import Path

VIDEOS = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}
IMAGES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
SEUIL_SCENE = 0.3
DUREE_MAX_ANALYSE_S = 15 * 60
CONSEIL_FFMPEG = ("ffmpeg est introuvable : installez-le (Windows : « winget install Gyan.FFmpeg » ; macOS : « brew install ffmpeg » ; "
                  "Linux : le paquet ffmpeg), puis rouvrez le terminal. En attendant, demandez des captures d'écran de la vidéo.")


def dossier_exemples() -> Path:
    d = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()) / ".circe" / "exemples"
    d.mkdir(parents=True, exist_ok=True)
    return d


def nom_sur(texte: str) -> str:
    simple = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode().lower()
    base = re.sub(r"[^a-z0-9]+", "-", simple).strip("-")[:40] or "exemple"
    d = dossier_exemples()
    nom, i = base, 2
    while (d / nom).exists():
        nom, i = f"{base}-{i}", i + 1
    return nom


def lancer(cmd: list[str], delai: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, timeout=delai)


def sonder(ffprobe: str, fichier: Path) -> dict:
    r = lancer([ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(fichier)], 60)
    info = json.loads(r.stdout.decode("utf-8", "replace") or "{}")
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    audio = any(s.get("codec_type") == "audio" for s in info.get("streams", []))
    duree = float(info.get("format", {}).get("duration") or video.get("duration") or 0)
    l, h = int(video.get("width") or 0), int(video.get("height") or 0)
    num, _, den = str(video.get("avg_frame_rate") or video.get("r_frame_rate") or "0/1").partition("/")
    ips = round(float(num) / float(den or 1), 2) if float(den or 1) else 0.0
    cadre = "vertical" if h > l * 1.1 else "horizontal" if l > h * 1.1 else "carré"
    return {"duree_s": round(duree, 2), "largeur": l, "hauteur": h, "cadre": cadre, "images_par_seconde": ips, "son": audio}


def compter_plans(ffmpeg: str, fichier: Path, duree: float) -> int | None:
    if duree <= 0 or duree > DUREE_MAX_ANALYSE_S:
        return None
    r = lancer([ffmpeg, "-hide_banner", "-nostats", "-i", str(fichier), "-an", "-vf",
                f"scale=320:-2,select='gt(scene,{SEUIL_SCENE})',showinfo", "-f", "null", "-"], 300)
    return 1 + len(re.findall(r"pts_time:", r.stderr.decode("utf-8", "replace")))


def video(fichier: Path, n_images: int) -> dict:
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        return {"type": "video", "fichier": str(fichier), "erreur": CONSEIL_FFMPEG}
    sortie = dossier_exemples() / nom_sur(fichier.stem)
    sortie.mkdir()
    mesures = sonder(ffprobe, fichier)
    duree = mesures["duree_s"]
    images = []
    for i in range(n_images):
        t = duree * (i + 0.5) / n_images if duree else 0
        cible = sortie / f"image-{i + 1:02d}.jpg"
        lancer([ffmpeg, "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(fichier), "-frames:v", "1",
                "-vf", "scale=360:-2", "-q:v", "4", "-y", str(cible)], 60)
        if cible.exists():
            images.append(cible)
    planche = sortie / "planche.jpg"
    colonnes = 4 if mesures["cadre"] == "vertical" else 3
    lignes = -(-len(images) // colonnes) if images else 1
    if images:
        lancer([ffmpeg, "-hide_banner", "-loglevel", "error", "-framerate", "1", "-i", str(sortie / "image-%02d.jpg"),
                "-vf", f"tile={colonnes}x{lignes}:padding=6:color=white", "-frames:v", "1", "-y", str(planche)], 60)
    plans = compter_plans(ffmpeg, fichier, duree)
    return {"type": "video", "fichier": str(fichier), **mesures, "plans": plans,
            "plans_par_minute": round(plans / (duree / 60), 1) if plans and duree else None,
            "planche": str(planche) if planche.exists() else None, "images": [str(x) for x in images], "dossier": str(sortie)}


def navigateur() -> str | None:
    candidats = ["chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "msedge", "microsoft-edge"]
    for c in candidats:
        if shutil.which(c):
            return shutil.which(c)
    if platform.system() == "Windows":
        for base in (os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", ""), os.environ.get("LOCALAPPDATA", "")):
            for rel in (r"Google\Chrome\Application\chrome.exe", r"Microsoft\Edge\Application\msedge.exe"):
                p = Path(base) / rel
                if base and p.exists():
                    return str(p)
    if platform.system() == "Darwin":
        for p in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"):
            if Path(p).exists():
                return p
    return None


def site(adresse: str) -> dict:
    nav = navigateur()
    if not nav:
        return {"type": "site", "adresse": adresse, "erreur": "ni Chrome ni Edge trouvés : demandez des captures d'écran du site."}
    sortie = dossier_exemples() / nom_sur(re.sub(r"^https?://(www\.)?", "", adresse))
    sortie.mkdir()
    captures = {}
    for nom, taille in (("ordinateur", "1440,2400"), ("petit-ecran", "500,2400")):   # 500 px : largeur minimale d'une fenêtre de navigateur sans écran
        cible = sortie / f"{nom}.png"
        lancer([nav, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
                f"--user-data-dir={sortie / '.profil-temporaire'}", f"--window-size={taille}", "--virtual-time-budget=8000",
                f"--screenshot={cible}", adresse], 90)
        captures[nom] = str(cible) if cible.exists() else None
    shutil.rmtree(sortie / ".profil-temporaire", ignore_errors=True)
    return {"type": "site", "adresse": adresse, "captures": captures, "dossier": str(sortie),
            "conseil": "Regardez aussi le site en vrai (défilement, animations) : une capture ne montre pas le mouvement. Pour le téléphone exact (390 px), demandez une capture faite sur un téléphone."}


# Défaut D13 (session binôme, mission M5 du 27/11/2026) : pour une vidéo, cet outil donnait durée, cadre, images par seconde
# et plans ; pour un site, des captures ; pour une IMAGE, il recopiait le fichier et s'arrêtait là. La fiche d'analyse
# demandait donc des mesures que l'outil ne donnait pas, et il a fallu les refaire à la main. Il les donne maintenant.
COTE_ANALYSE = 64          # l'image est réduite à 64 × 64 : assez pour les couleurs et les aplats, et instantané
SEUIL_APLAT = 16           # une rangée est « unie » si ses pixels s'écartent de moins de ça de sa couleur moyenne
CONSEIL_MESURE = ("Mesures de couleur indisponibles : ni ffmpeg ni Pillow. Installez l'un des deux "
                  "(« winget install Gyan.FFmpeg », ou « python -m pip install Pillow ») pour la palette et les aplats.")


def dimensions_entete(fichier: Path) -> tuple[int, int] | None:
    """Largeur et hauteur lues dans l'en-tête (PNG, GIF, WebP, JPEG) : marche sans aucun outil installé."""
    try:
        with open(fichier, "rb") as f:
            t = f.read(32)
            if t[:8] == b"\x89PNG\r\n\x1a\n":
                return struct.unpack(">II", t[16:24])
            if t[:6] in (b"GIF87a", b"GIF89a"):
                return struct.unpack("<HH", t[6:10])
            if t[:4] == b"RIFF" and t[8:12] == b"WEBP":
                forme = t[12:16]
                if forme == b"VP8X":
                    l = int.from_bytes(t[24:27], "little") + 1
                    h = int.from_bytes(t[27:30], "little") + 1
                    return l, h
                if forme == b"VP8L":
                    bits = int.from_bytes(t[21:25], "little")
                    return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
                if forme == b"VP8 ":
                    return struct.unpack("<H", t[26:28])[0] & 0x3FFF, struct.unpack("<H", t[28:30])[0] & 0x3FFF
                return None
            if t[:2] == b"\xff\xd8":                      # JPEG : on avance de marqueur en marqueur jusqu'au cadre
                f.seek(2)
                while True:
                    octet = f.read(1)
                    while octet and octet != b"\xff":
                        octet = f.read(1)
                    while octet == b"\xff":
                        octet = f.read(1)
                    if not octet:
                        return None
                    marqueur = octet[0]
                    taille = struct.unpack(">H", f.read(2))[0]
                    if marqueur in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                        f.read(1)
                        h, l = struct.unpack(">HH", f.read(4))
                        return l, h
                    f.seek(taille - 2, 1)
    except (OSError, struct.error, IndexError):
        return None
    return None


def pixels_reduits(fichier: Path) -> list[tuple[int, int, int, int]] | None:
    """64 × 64 pixels en RVB + transparence, par ffmpeg (déjà nécessaire pour les vidéos) ou par Pillow si elle est là.
    La transparence compte : sans elle, un logo sur fond transparent est mesuré comme « noir à 70 % » (essai du 27/11)."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        r = lancer([ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(fichier),
                    "-vf", f"scale={COTE_ANALYSE}:{COTE_ANALYSE}", "-frames:v", "1",
                    "-f", "rawvideo", "-pix_fmt", "rgba", "-"], 60)
        brut = r.stdout or b""
        if len(brut) >= COTE_ANALYSE * COTE_ANALYSE * 4:
            return [tuple(brut[i:i + 4]) for i in range(0, COTE_ANALYSE * COTE_ANALYSE * 4, 4)]
    try:
        from PIL import Image  # noqa: PLC0415 (facultatif : seulement si l'utilisateur l'a installée)
        petite = Image.open(fichier).convert("RGBA").resize((COTE_ANALYSE, COTE_ANALYSE))
        return list(petite.getdata())
    except Exception:
        return None


def _luminance(p: tuple[int, int, int]) -> float:
    return 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]


def bande_unie(pixels: list[tuple[int, int, int]]) -> dict | None:
    """La plus grande bande horizontale d'un seul ton : c'est là qu'un texte peut se poser sans boîte ni voile."""
    rangees = [pixels[y * COTE_ANALYSE:(y + 1) * COTE_ANALYSE] for y in range(COTE_ANALYSE)]
    unies = []
    for rangee in rangees:
        pleins = [p for p in rangee if len(p) < 4 or p[3] >= 128]
        if len(pleins) < len(rangee) // 2:        # rangée surtout transparente : pas une zone de texte
            unies.append(None)
            continue
        moy = tuple(sum(p[c] for p in pleins) / len(pleins) for c in range(3))
        ecart = max(max(abs(p[c] - moy[c]) for c in range(3)) for p in pleins)
        unies.append(moy if ecart <= SEUIL_APLAT else None)
    meilleur, debut, courant = (0, 0, 0), None, 0
    for y in range(COTE_ANALYSE + 1):
        proche = (y < COTE_ANALYSE and unies[y] is not None
                  and (debut is None or max(abs(unies[y][c] - unies[debut][c]) for c in range(3)) <= SEUIL_APLAT))
        if proche:
            debut = y if debut is None else debut
            courant += 1
        else:
            if courant > meilleur[0]:
                meilleur = (courant, debut, y - 1)
            debut, courant = None, 0
    hauteur, y1, y2 = meilleur
    if hauteur < 6:                       # moins de 10 % de la hauteur : ce n'est pas une zone de texte
        return None
    ton = [sum(unies[y][c] for y in range(y1, y2 + 1)) / hauteur for c in range(3)]
    lum = _luminance(tuple(ton))
    return {"debut_pourcent": round(100 * y1 / COTE_ANALYSE), "fin_pourcent": round(100 * (y2 + 1) / COTE_ANALYSE),
            "part_de_la_hauteur_pourcent": round(100 * hauteur / COTE_ANALYSE),
            "couleur": "#%02x%02x%02x" % tuple(round(c) for c in ton),
            "texte_lisible": "clair" if lum < 90 else ("sombre" if lum > 165 else "aucun sans retouche")}


def mesurer_image(fichier: Path) -> dict:
    mesures: dict = {}
    taille = dimensions_entete(fichier)
    pixels = pixels_reduits(fichier)
    if pixels and not taille:
        try:
            from PIL import Image  # noqa: PLC0415
            taille = Image.open(fichier).size
        except Exception:
            taille = None
    if taille:
        l, h = taille
        mesures.update({"largeur": l, "hauteur": h, "rapport": round(l / h, 3) if h else None,
                        "cadre": "carre" if abs(l - h) <= 2 else ("vertical" if h > l else "horizontal")})
    mesures["poids_ko"] = round(fichier.stat().st_size / 1024)
    if not pixels:
        mesures["conseil"] = CONSEIL_MESURE
        return mesures
    # Les pixels transparents ne sont pas une couleur : un logo sur fond transparent était mesuré « noir à 70 % ».
    opaques = [p for p in pixels if len(p) < 4 or p[3] >= 128]
    transparence = round(100 * (len(pixels) - len(opaques)) / len(pixels))
    if transparence >= 5:
        mesures["part_transparente_pourcent"] = transparence
    if not opaques:
        mesures["conseil"] = "image entièrement transparente : rien à mesurer."
        return mesures
    n = len(opaques)
    mesures["luminance_moyenne"] = round(sum(_luminance(p) for p in opaques) / n)
    mesures["part_sombre_pourcent"] = round(100 * sum(1 for p in opaques if _luminance(p) < 40) / n)
    mesures["part_claire_pourcent"] = round(100 * sum(1 for p in opaques if _luminance(p) > 215) / n)
    comptes: dict[tuple[int, int, int], int] = {}
    for p in opaques:                      # couleurs arrondies par pas de 16 : on cherche des familles, pas des nuances
        cle = (p[0] // 16 * 16, p[1] // 16 * 16, p[2] // 16 * 16)
        comptes[cle] = comptes.get(cle, 0) + 1
    dominantes = sorted(comptes.items(), key=lambda x: -x[1])[:5]
    mesures["couleurs_dominantes"] = [{"couleur": "#%02x%02x%02x" % c, "part_pourcent": round(100 * k / n)}
                                      for c, k in dominantes]
    bande = bande_unie(pixels)
    mesures["zone_de_texte"] = bande or "aucune bande unie d'au moins 10 % de la hauteur"
    return mesures


def image(fichier: Path) -> dict:
    sortie = dossier_exemples() / nom_sur(fichier.stem)
    sortie.mkdir()
    cible = sortie / fichier.name
    shutil.copy2(fichier, cible)
    resultat = {"type": "image", "fichier": str(cible), "dossier": str(sortie)}
    resultat.update(mesurer_image(fichier))
    resultat["suite"] = ("Ouvre l'image et regarde-la vraiment, puis écris la fiche (circe:exemples). "
                         "La « zone_de_texte » est une bande unie : c'est là qu'un texte se pose sans boîte ni voile.")
    return resultat


def regarder(entree: str, n_images: int = 12) -> dict:
    # Essai « nouvel utilisateur » du 24/11 : une page locale (file:///…%20…) donnait « fichier introuvable », et Claude
    # lançait un serveur local pour la capturer. Une adresse file:// de page se capture directement ; sinon, c'est un fichier.
    if re.match(r"^file:", entree, re.I):
        from urllib.parse import unquote, urlparse  # noqa: PLC0415
        chemin = unquote(urlparse(entree).path)
        if re.match(r"^/[A-Za-z]:", chemin):
            chemin = chemin[1:]
        if Path(chemin).suffix.lower() in (".html", ".htm"):
            return site(entree) if Path(chemin).exists() else {"entree": entree, "erreur": "fichier introuvable"}
        entree = chemin
    if re.match(r"^https?://", entree, re.I):
        if re.search(r"(?i)tiktok\.com|youtube\.com|youtu\.be|instagram\.com|facebook\.com|vimeo\.com", entree):
            return {"type": "video", "adresse": entree, "erreur": "vidéo en ligne : CIRCÉ ne la télécharge pas. Demandez le fichier vidéo, "
                                                                   "ou 6 à 12 captures d'écran à des moments différents."}
        return site(entree)
    fichier = Path(entree).expanduser()
    if not fichier.exists():
        return {"entree": entree, "erreur": "fichier introuvable"}
    ext = fichier.suffix.lower()
    if ext in VIDEOS:
        return video(fichier, n_images)
    if ext in IMAGES:
        return image(fichier)
    return {"entree": entree, "erreur": f"type non pris en charge ({ext}) : vidéo, image ou adresse de site"}


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="regarder.py", description="Regarder des exemples (vidéos, sites, images) avant de concevoir")
    p.add_argument("entrees", nargs="+")
    p.add_argument("--images", type=int, default=12)
    a = p.parse_args(argv)
    resultats = []
    for e in a.entrees:
        try:
            resultats.append(regarder(e, max(4, min(a.images, 24))))
        except (subprocess.TimeoutExpired, OSError, ValueError) as err:
            resultats.append({"entree": e, "erreur": f"{type(err).__name__} : {err}"})
    print(json.dumps(resultats, ensure_ascii=False, indent=1))
    return 1 if all("erreur" in r for r in resultats) else 0


if __name__ == "__main__":
    sys.exit(main())
