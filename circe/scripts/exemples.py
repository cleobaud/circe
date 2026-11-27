"""CIRCÉ — Réflexe « toujours des exemples » : hook UserPromptSubmit.

Quand la demande de l'utilisateur lance une création visuelle (site, page, logo, visuel, vidéo, objet 3D…) sans donner
d'exemple (ni lien, ni image, ni « comme … »), ce hook ajoute un rappel au contexte de Claude : demander des exemples,
ou en chercher 3 et les faire choisir, AVANT de concevoir. Il ne bloque rien : la demande part telle quelle.
En veille (licence inactive), il se tait. Bibliothèque standard seulement.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # Python embarqué (fichier ._pth) : le dossier du script n'est pas dans le chemin d'import

# Les filtres sont écrits SANS accents et comparés au texte sans accents (essai « nouvel utilisateur » du 24/11 :
# « cree un logo » et « genere une affiche », tapés vite, ne déclenchaient pas le rappel).
CREATION = re.compile(r"(?i)\b(?:cree[sz]?|creer|fais|faire|faites|refais|refaire|gener(?:e[sz]?|er)|dessine[rsz]?|design|concoi[st]|concevoir"
                      r"|monte[rz]?|realise[rz]?|build|create|make)\b"
                      r".{0,80}\b(?:site|page|landing|logo|visuel|affiche|banniere|interface|maquette|video|film|montage|animation|motion|objet|modele 3d|3d|scene|rendu|carrousel|post)\b")
DEJA_DES_EXEMPLES = re.compile(r"(?i)(?:https?://|\.(?:png|jpe?g|webp|gif|mp4|pdf)\b|\bcomme (?:celui|celle|ca|sur|le site|l'exemple)|\bdans le style\b|\bvoici (?:des|mes|les) (?:exemples|references)\b|\bpas d'exemple\b|\bsans exemple\b)")


def sans_accents(texte: str) -> str:
    """« Crée une vidéo » -> « Cree une video » : les filtres marchent avec ou sans accents."""
    return "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")
RAPPEL = ("[CIRCÉ, réflexe « toujours des exemples » : cette demande lance une création visuelle sans exemple. "
          "Avant de concevoir, applique circe:references-visuelles : demande à l'utilisateur 3 à 5 exemples (ce qui lui plaît, ce qui lui déplaît, "
          "ce qui existe déjà), ou cherche-en 3 de qualité et fais-le choisir. S'il dit « pas d'exemple », annonce ta direction en une phrase. "
          "Ensuite, AVANT de construire, montre un aperçu (images basse définition, maquette, storyboard) et attends son feu vert (circe:methode, étape 4). "
          "Et avant chaque « voici » : pose le résultat à côté de la référence et fais-le juger par un regard neuf (circe:qualite) ; "
          "un détail d'illustrateur ne se dessine pas en code, change de moyen plutôt que livrer une esquisse.]")


def evaluer(evenement: dict) -> dict | None:
    texte = sans_accents(str(evenement.get("prompt") or ""))
    if not texte or not CREATION.search(texte) or DEJA_DES_EXEMPLES.search(texte):
        return None
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": RAPPEL}}


def en_veille() -> bool:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import licence  # noqa: PLC0415
        return licence.etat_rapide() == "veille"
    except Exception:
        return False


def main() -> int:
    try:
        import unique  # noqa: PLC0415 (même dossier)
        brut = unique.lire("exemples")
        if brut is None:
            return 0  # l'autre interprète traite déjà cet événement
        evenement = json.loads(brut or "{}")
        resultat = None if en_veille() else evaluer(evenement)
    except Exception:
        return 0
    if resultat:
        sys.stdout.write(json.dumps(resultat))
    return 0


if __name__ == "__main__":
    sys.exit(main())
