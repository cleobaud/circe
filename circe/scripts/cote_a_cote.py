"""CIRCÉ — Boucle du niveau : poser la référence et le résultat côte à côte, sur UNE image, à la même échelle.

  python cote_a_cote.py <référence> [<autre référence> ...] <résultat> [--haut 900] [--titres "Réf.,Le nôtre"]

Chaque élément : une image (png, jpg, webp, gif), une page (adresse https://, adresse file:///, ou fichier .html) capturée
à 1440 px par Chrome ou Edge, ou une vidéo (une image du milieu, prise par ffmpeg). Le RÉSULTAT est toujours le dernier.
--haut N : ne compare que le haut (N pixels de la largeur 1440), pour juger un premier écran.
Sortie : <projet>/.circe/cote-a-cote/<horodatage>.png, et un résumé JSON. Claude regarde l'image, puis la fait juger par
un regard neuf (sous-agent) axe par axe : compétence circe:qualite, boucle 1.
Bibliothèque standard seulement (Chrome ou Edge pour assembler, ffmpeg seulement pour une vidéo). Rien n'est envoyé.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # Python embarqué (fichier ._pth)

import regarder  # noqa: E402 (même dossier)

LARGEUR_TOTALE = 1800
HAUTEUR_MAX = 6000


def taille_image(fichier: Path) -> tuple[int, int] | None:
    """Largeur et hauteur d'un PNG, JPEG, GIF ou WebP, lues dans l'en-tête (sans bibliothèque d'images)."""
    try:
        with open(fichier, "rb") as f:
            d = f.read(65536)
    except OSError:
        return None
    if d[:8] == b"\x89PNG\r\n\x1a\n" and len(d) >= 24:
        return struct.unpack(">II", d[16:24])
    if d[:6] in (b"GIF87a", b"GIF89a"):
        return struct.unpack("<HH", d[6:10])
    if d[:4] == b"RIFF" and d[8:12] == b"WEBP":
        morceau = d[12:16]
        if morceau == b"VP8X":
            return 1 + int.from_bytes(d[24:27], "little"), 1 + int.from_bytes(d[27:30], "little")
        if morceau == b"VP8L":
            b = int.from_bytes(d[21:25], "little")
            return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
        if morceau == b"VP8 ":
            l, h = struct.unpack("<HH", d[26:30])
            return l & 0x3FFF, h & 0x3FFF
    if d[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(d):
            if d[i] != 0xFF:
                i += 1
                continue
            marque = d[i + 1]
            if marque in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, l = struct.unpack(">HH", d[i + 5:i + 9])
                return l, h
            i += 2 + struct.unpack(">H", d[i + 2:i + 4])[0]
    return None


def en_image(entree: str) -> dict:
    """Ramène un élément à une image locale : {"source", "image", "largeur", "hauteur"} ou {"source", "erreur"}."""
    e = entree.strip()
    if e.lower().endswith((".html", ".htm")) and not e.lower().startswith(("http://", "https://", "file:")):
        e = Path(e).expanduser().resolve().as_uri()
    if e.lower().startswith(("http://", "https://", "file:")):
        r = regarder.regarder(e)
        img = (r.get("captures") or {}).get("ordinateur")
        if not img:
            return {"source": entree, "erreur": r.get("erreur") or "capture impossible"}
        e = img
    p = Path(e).expanduser()
    if not p.exists():
        return {"source": entree, "erreur": "fichier introuvable"}
    if p.suffix.lower() in regarder.VIDEOS:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            return {"source": entree, "erreur": regarder.CONSEIL_FFMPEG}
        ffprobe = shutil.which("ffprobe")
        duree = regarder.sonder(ffprobe, p).get("duree_s", 0) if ffprobe else 0
        cible = regarder.dossier_exemples().parent / "cote-a-cote" / f"image-{int(time.time() * 1000)}.png"
        cible.parent.mkdir(parents=True, exist_ok=True)
        regarder.lancer([ffmpeg, "-y", "-v", "error", "-ss", str(max(0.0, float(duree or 0) / 2)), "-i", str(p), "-frames:v", "1", str(cible)], 60)
        if not cible.exists():
            return {"source": entree, "erreur": "image de la vidéo impossible à extraire"}
        p = cible
    taille = taille_image(p)
    if not taille:
        return {"source": entree, "erreur": "format d'image non reconnu (png, jpg, webp, gif)"}
    return {"source": entree, "image": str(p.resolve()), "largeur": taille[0], "hauteur": taille[1]}


def page_html(elements: list[dict], titres: list[str], haut: int | None) -> tuple[str, int, int]:
    n = len(elements)
    col = min(900, LARGEUR_TOTALE // n)
    hauteurs = []
    blocs = []
    for el, titre in zip(elements, titres):
        echelle = col / el["largeur"]
        h_aff = round(el["hauteur"] * echelle)
        h_vue = min(h_aff, round(haut * col / 1440)) if haut else h_aff
        hauteurs.append(h_vue)
        blocs.append(f'<figure><figcaption>{html.escape(titre)}</figcaption>'
                     f'<div class="cadre" style="width:{col}px;height:{h_vue}px">'
                     f'<img src="{Path(el["image"]).as_uri()}" style="width:{col}px"></div></figure>')
    largeur = n * col + (n + 1) * 24
    hauteur = min(max(hauteurs) + 90, HAUTEUR_MAX)
    page = ("<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
            "html,body{margin:0;background:#8d8d8d;font:600 20px system-ui,sans-serif;color:#111}"
            "main{display:flex;gap:24px;padding:12px 24px;align-items:flex-start}"
            "figure{margin:0}figcaption{height:40px;line-height:40px}"
            ".cadre{overflow:hidden;background:#fff}img{display:block}"
            f"</style></head><body><main>{''.join(blocs)}</main></body></html>")
    return page, largeur, hauteur


MAX_ELEMENTS = 6


def cote_a_cote(entrees: list[str], haut: int | None = None, titres: list[str] | None = None) -> dict:
    if len(entrees) < 2:
        return {"erreur": "il faut au moins une référence et le résultat (le résultat en dernier)"}
    if len(entrees) > MAX_ELEMENTS:
        return {"erreur": f"au plus {MAX_ELEMENTS} éléments sur une image (sinon tout devient trop petit pour juger) : faites plusieurs comparaisons"}
    elements = [en_image(e) for e in entrees]
    fautes = [el for el in elements if "erreur" in el]
    if fautes:
        return {"erreur": "élément illisible", "details": fautes}
    noms = titres or [f"Référence {i + 1}" for i in range(len(entrees) - 1)] + ["Résultat"]
    noms = (noms + [""] * len(entrees))[:len(entrees)]
    nav = regarder.navigateur()
    if not nav:
        return {"erreur": "ni Chrome ni Edge trouvés : posez les deux images côte à côte à la main (même largeur)."}
    dossier = regarder.dossier_exemples().parent / "cote-a-cote"
    dossier.mkdir(parents=True, exist_ok=True)
    horodatage = time.strftime("%Y-%m-%d_%H%M%S")
    page, largeur, hauteur = page_html(elements, noms, haut)
    fichier_html = dossier / f"{horodatage}.html"
    fichier_html.write_text(page, encoding="utf-8")
    cible = dossier / f"{horodatage}.png"
    profil = dossier / ".profil-temporaire"
    regarder.lancer([nav, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
                     "--allow-file-access-from-files", f"--user-data-dir={profil}", f"--window-size={largeur},{hauteur}",
                     "--virtual-time-budget=4000", f"--screenshot={cible}", fichier_html.as_uri()], 90)
    shutil.rmtree(profil, ignore_errors=True)
    fichier_html.unlink(missing_ok=True)   # relecture Codex : aucune page temporaire laissée derrière
    if not cible.exists():
        return {"erreur": "capture impossible"}
    tronque = hauteur >= HAUTEUR_MAX
    resultat = {"image": str(cible), "elements": [{"titre": t, "source": el["source"]} for t, el in zip(noms, elements)],
                "tronque": tronque,
                "suite": "Regarde l'image, puis fais juger chaque axe par un regard neuf (sous-agent) : circe:qualite, boucle 1."}
    if tronque:
        resultat["attention"] = ("image coupée en bas (page trop longue) : compare zone par zone (--haut pour le premier écran, "
                                 "puis une capture de chaque section) ; ce qui n'est pas sur l'image n'est pas jugé.")
    import hashlib  # noqa: PLC0415
    manifeste = {"cree_le": time.time(), "image": str(cible), "sha256": hashlib.sha256(cible.read_bytes()).hexdigest(),
                 "elements": resultat["elements"], "haut": haut, "tronque": tronque}
    cible.with_suffix(".json").write_text(json.dumps(manifeste, ensure_ascii=False, indent=1), encoding="utf-8")
    return resultat


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="cote_a_cote.py", description="Référence(s) et résultat côte à côte, sur une image")
    p.add_argument("entrees", nargs="+", help="références puis le résultat (le dernier)")
    p.add_argument("--haut", type=int, default=None, help="ne comparer que le haut (pixels, largeur 1440)")
    p.add_argument("--titres", default=None, help="titres séparés par des virgules")
    a = p.parse_args(argv)
    try:
        r = cote_a_cote(a.entrees, a.haut, a.titres.split(",") if a.titres else None)
    except (subprocess.TimeoutExpired, OSError, ValueError) as err:
        r = {"erreur": f"{type(err).__name__} : {err}"}
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 1 if "erreur" in r else 0


if __name__ == "__main__":
    sys.exit(main())
