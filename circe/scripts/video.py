"""CIRCÉ — contrôles d'une vidéo produite, et registre de nouveauté d'une série.

  python video.py controler <fichier.mp4> [--cadre 1080x1920] [--ips 30] [--duree 30-45] [--son non] [--planche]
  python video.py registre  <fichier.mp4> --schema <nom> [--episode <titre>] [--ecrire]
  python video.py polices   <police.ttf|.otf|.woff> --texte "<le texte qui sera affiché>"
  python video.py pieges                                   (les erreurs mesurées, à lire AVANT de produire)

Pourquoi cet outil existe : les erreurs qu'il attrape ont toutes été commises pour de vrai, le 27/11/2026, en produisant
une vidéo verticale de 36 s. Elles ne se voient pas en relisant le code — seulement sur le fichier rendu, trop tard.
  - l'image rendue n'était plus au format demandé (fenêtre de cadrage mal calculée) : image écrasée, invisible à la relecture ;
  - une piste audio oubliée alors que le client monte le son lui-même ;
  - une durée hors de la plage du réseau ;
  - des images entièrement noires au montage ;
  - un sous-ensemble de police sans les accents : le rendu est perdu, et on ne le voit qu'à la fin ;
  - un plan déjà montré dans un épisode précédent (une série se juge sur sa nouveauté).

ffprobe et ffmpeg sont nécessaires pour « controler » et « registre » ; le reste est en bibliothèque standard.
Rien n'est envoyé ailleurs : tout reste dans le projet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path

CONSEIL_FFMPEG = ("ffmpeg et ffprobe sont nécessaires : installez-les (Windows : « winget install Gyan.FFmpeg » ; "
                  "macOS : « brew install ffmpeg » ; Linux : le paquet ffmpeg), puis rouvrez le terminal.")
COTE = 16               # côté de l'empreinte : 16 × 16 = 256 bits, assez pour qu'une ressemblance ne soit pas un hasard
CONTRASTE_MINIMUM = 12  # écart maximum-minimum en dessous duquel une image est unie : aucune empreinte utile
NOIR_MAXIMUM = 3        # luminance moyenne sous ce seuil = image VRAIMENT noire.
# La reduction se fait en MOYENNANT les pixels (flags=area). Sans ca (essai du 27/11 sur une vraie video sombre),
# ffmpeg echantillonne et rate les elements fins : une image de maquette sombre mesurait 2 au lieu de 14, et
# 8 images sur 12 etaient declarees noires a tort. Les empreintes sont concernees aussi : elles perdaient le detail.
# Essai du 27/11 sur une vraie vidéo : à 8, un plan sombre voulu (un terminal noir) était signalé à tort.


PIEGES = [
    "La fenêtre de cadrage garde le format de sortie : sinon l'image est écrasée, et la relecture du code ne le voit pas.",
    "La caméra se POSE sur ce dont la voix parle : arrivée en ~1,4 s, plan tenu ~5 s. En mouvement, rien n'est lisible.",
    "Aucune boîte derrière les sous-titres : on réserve du vide pour l'accroche au lieu de poser un voile sur l'image.",
    "Une police en sous-ensemble peut ne pas avoir les accents : « video.py polices » AVANT le rendu, pas après.",
    "Un chiffre affiché se compte dans le produit, il ne se recopie pas d'un site : il vieillit.",
    "Au-delà de 100 images : Pillow pour composer, ffmpeg pour assembler. Un navigateur sans fenêtre est trop lent.",
    "Rien ne se rend avant le feu vert de l'utilisateur sur les images clés : un rendu raté coûte le temps du rendu.",
    "Une série ne rejuge pas ses secondes fixes (accroche, carte de fin) : « --ignorer-debut » et « --ignorer-fin ».",
]


def lancer(cmd: list[str], delai: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, timeout=delai)


def sonde(fichier: Path) -> dict:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return {"erreur": CONSEIL_FFMPEG}
    r = lancer([ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(fichier)], 90)
    try:
        d = json.loads(r.stdout.decode("utf-8", "replace") or "{}")
    except ValueError:
        return {"erreur": "ffprobe n'a rien renvoyé de lisible pour ce fichier."}
    flux = [s for s in d.get("streams", []) if s.get("codec_type") == "video"]
    if not flux:
        return {"erreur": "aucune piste vidéo dans ce fichier."}
    v = flux[0]
    num, _, den = (v.get("avg_frame_rate") or "0/1").partition("/")
    ips = round(float(num) / float(den), 2) if den and float(den) else 0.0
    return {"largeur": int(v.get("width") or 0), "hauteur": int(v.get("height") or 0), "images_par_seconde": ips,
            "duree_s": round(float(d.get("format", {}).get("duration") or 0), 2),
            "son": any(s.get("codec_type") == "audio" for s in d.get("streams", [])),
            "codec": v.get("codec_name"), "poids_ko": round(fichier.stat().st_size / 1024)}


def empreintes(fichier: Path, duree: float, combien: int = 12,
               ignorer_debut: float = 0.0, ignorer_fin: float = 0.0) -> list[str]:
    """Une empreinte par image clé : 16 × 16 en gris, comparée à sa moyenne. Deux plans identiques donnent la même.
    16 × 16 et non 8 × 8 (essai du 27/11) : en 8 × 8, deux vidéos sans rapport se ressemblaient par hasard."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or duree <= 0:
        return []
    # Les parties FIXES du schéma (accroche, carte de fin) se répètent exprès d'un épisode à l'autre :
    # les mesurer ferait refuser chaque épisode. Essai du 27/11 : les deux vidéos de référence, de deux auteurs
    # différents, partageaient leur dernière image — la même carte de fin TikTok. Le registre ne juge que le milieu.
    debut = max(0.0, ignorer_debut)
    fin = max(debut + 0.1, duree - max(0.0, ignorer_fin))
    sorties = []
    for i in range(combien):
        t = debut + (fin - debut) * (i + 0.5) / combien
        r = lancer([ffmpeg, "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(fichier),
                    "-frames:v", "1", "-vf", f"scale={COTE}:{COTE}:flags=area", "-pix_fmt", "gray", "-f", "rawvideo", "-"], 90)
        brut = r.stdout or b""
        if len(brut) < COTE * COTE:
            continue
        octets = brut[:COTE * COTE]
        # Essai du 27/11 : deux vidéos SANS rapport étaient déclarées identiques, parce que leurs images unies
        # (un écran blanc, un écran noir) donnent toutes la même empreinte. Une image sans contraste ne dit rien :
        # elle n'est pas comptée.
        if max(octets) - min(octets) < CONTRASTE_MINIMUM:
            continue
        moyenne = sum(octets) / len(octets)
        bits = "".join("1" if o > moyenne else "0" for o in octets)
        sorties.append(f"{int(bits, 2):0{COTE * COTE // 4}x}")
    return sorties


def images_noires(fichier: Path, duree: float, combien: int = 12) -> list[float]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or duree <= 0:
        return []
    noires = []
    for i in range(combien):
        t = duree * (i + 0.5) / combien
        r = lancer([ffmpeg, "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(fichier),
                    "-frames:v", "1", "-vf", "scale=8:8:flags=area", "-pix_fmt", "gray", "-f", "rawvideo", "-"], 90)
        brut = r.stdout or b""
        if len(brut) >= 64 and sum(brut[:64]) / 64 < NOIR_MAXIMUM:
            noires.append(round(t, 2))
    return noires


def planche(fichier: Path, duree: float, sortie: Path, combien: int = 12) -> Path | None:
    """La planche de 12 images que la méthode demande de regarder avant de livrer."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or duree <= 0:
        return None
    sortie.parent.mkdir(parents=True, exist_ok=True)
    colonnes = 4
    lignes = math.ceil(combien / colonnes)
    r = lancer([ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(fichier),
                "-vf", f"fps={combien / duree:.6f},scale=270:-1,tile={colonnes}x{lignes}",
                "-frames:v", "1", "-y", str(sortie)], 180)
    return sortie if sortie.exists() and r.returncode == 0 else None


def controler(fichier: Path, cadre: str | None, ips: float | None, duree: str | None,
              son: str | None, faire_planche: bool) -> dict:
    mesures = sonde(fichier)
    if "erreur" in mesures:
        return {"conforme": False, "ecarts": [mesures["erreur"]]}
    ecarts = []
    if cadre:
        l, _, h = cadre.lower().partition("x")
        if (mesures["largeur"], mesures["hauteur"]) != (int(l), int(h)):
            ecarts.append(f"cadre {mesures['largeur']}x{mesures['hauteur']} au lieu de {cadre} "
                          f"(une fenêtre de cadrage au mauvais rapport écrase l'image sans qu'on le voie)")
    if ips and abs(mesures["images_par_seconde"] - ips) > 0.5:
        ecarts.append(f"{mesures['images_par_seconde']} images/s au lieu de {ips}")
    if duree:
        bas, _, haut = duree.partition("-")
        bas, haut = float(bas), float(haut or bas)
        if not (bas <= mesures["duree_s"] <= haut):
            ecarts.append(f"durée {mesures['duree_s']} s hors de la plage {bas}-{haut} s")
    if son == "non" and mesures["son"]:
        ecarts.append("une piste audio est présente alors qu'elle ne devait pas l'être")
    if son == "oui" and not mesures["son"]:
        ecarts.append("aucune piste audio alors qu'il en fallait une")
    noires = images_noires(fichier, mesures["duree_s"])
    if noires:
        ecarts.append(f"images noires à {noires} s")
    resultat = {"conforme": not ecarts, "ecarts": ecarts, **mesures}
    if faire_planche:
        p = planche(fichier, mesures["duree_s"], fichier.with_name(fichier.stem + "-planche.jpg"))
        resultat["planche"] = str(p) if p else None
        resultat["suite"] = "Regarde la planche : rien de coupé au bord, aucun texte illisible, aucune image noire."
    return resultat


def registre(fichier: Path, schema: str, episode: str, chemin: Path, ecrire: bool,
             ignorer_debut: float = 0.0, ignorer_fin: float = 0.0) -> dict:
    """Une série ne refait jamais un plan déjà montré. Contrôle AVANT publication."""
    mesures = sonde(fichier)
    if "erreur" in mesures:
        return {"nouveau": False, "ecarts": [mesures["erreur"]]}
    actuelles = empreintes(fichier, mesures["duree_s"], 12, ignorer_debut, ignorer_fin)
    if not actuelles:
        return {"nouveau": False, "ecarts": ["impossible de lire les images de cette vidéo (ffmpeg)."]}
    try:
        connu = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        connu = {"schema": schema, "episodes": []}
    reprises = []
    for ancien in connu.get("episodes", []):
        communes = set(ancien.get("empreintes", [])) & set(actuelles)
        if communes:
            reprises.append({"episode": ancien.get("episode"), "plans_repris": sorted(communes)})
    resultat = {"nouveau": not reprises, "reprises": reprises, "empreintes": actuelles,
                "registre": str(chemin), "episodes_connus": len(connu.get("episodes", []))}
    if reprises:
        resultat["ecarts"] = [f"{len(reprises)} épisode(s) déjà publié(s) partagent un plan avec celui-ci : "
                              "refais le plan repris, ou change de thème."]
        return resultat
    if ecrire:
        connu.setdefault("episodes", []).append({"episode": episode or fichier.stem,
                                                 "date": time.strftime("%Y-%m-%d"), "fichier": fichier.name,
                                                 "empreintes": actuelles})
        connu["schema"] = schema
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(json.dumps(connu, ensure_ascii=False, indent=1), encoding="utf-8")
        resultat["ecrit"] = True
    return resultat


def polices(police: Path, texte: str) -> dict:
    """Un sous-ensemble de police peut ne pas avoir les accents : on le voit sinon APRÈS le rendu, trop tard."""
    try:
        from fontTools.ttLib import TTFont  # noqa: PLC0415 (facultatif)
    except ImportError:
        return {"erreur": "fontTools n'est pas installé : « python -m pip install fonttools »."}
    try:
        f = TTFont(police)
        couverts = set()
        for table in f["cmap"].tables:
            couverts |= set(table.cmap)
    except Exception as e:                      # noqa: BLE001 (une police illisible ne doit pas tout arrêter)
        return {"erreur": f"police illisible : {e}"}
    manquants = sorted({c for c in texte if c.strip() and ord(c) not in couverts})
    return {"police": police.name, "caracteres_couverts": len(couverts),
            "manquants": "".join(manquants), "complete": not manquants}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="video.py", description="Contrôles d'une vidéo produite (CIRCÉ)")
    sous = p.add_subparsers(dest="quoi", required=True)

    c = sous.add_parser("controler", help="cadre, images par seconde, durée, son, images noires, planche")
    c.add_argument("fichier")
    c.add_argument("--cadre", default=None, help="par exemple 1080x1920")
    c.add_argument("--ips", type=float, default=None)
    c.add_argument("--duree", default=None, help="plage en secondes, par exemple 30-45")
    c.add_argument("--son", choices=["oui", "non"], default=None)
    c.add_argument("--planche", action="store_true")

    r = sous.add_parser("registre", help="registre de nouveauté d'une série : aucun plan déjà montré")
    r.add_argument("fichier")
    r.add_argument("--schema", required=True)
    r.add_argument("--episode", default="")
    r.add_argument("--registre", default="schemas/registre-nouveaute.json")
    r.add_argument("--ecrire", action="store_true", help="inscrire l'épisode s'il est nouveau")
    r.add_argument("--ignorer-debut", type=float, default=0.0, help="secondes d'accroche fixe à ne pas juger")
    r.add_argument("--ignorer-fin", type=float, default=0.0, help="secondes de fin fixe à ne pas juger")

    sous.add_parser("pieges", help="les erreurs mesurées, à lire avant de produire")

    f = sous.add_parser("polices", help="le texte à afficher est-il couvert par la police ?")
    f.add_argument("police")
    f.add_argument("--texte", required=True)

    a = p.parse_args(argv)
    if a.quoi == "pieges":
        for i, piege in enumerate(PIEGES, 1):
            print(f"{i}. {piege}")
        return 0
    if a.quoi == "controler":
        sortie = controler(Path(a.fichier), a.cadre, a.ips, a.duree, a.son, a.planche)
    elif a.quoi == "registre":
        sortie = registre(Path(a.fichier), a.schema, a.episode, Path(a.registre), a.ecrire,
                          a.ignorer_debut, a.ignorer_fin)
    else:
        sortie = polices(Path(a.police), a.texte)
    print(json.dumps(sortie, ensure_ascii=False, indent=1))
    return 0 if sortie.get("conforme", sortie.get("nouveau", sortie.get("complete", True))) else 1


if __name__ == "__main__":
    sys.exit(main())
