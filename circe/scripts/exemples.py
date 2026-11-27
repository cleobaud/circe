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
                      r"|monte[rz]?|realise[rz]?|build|create|make"
                      # « il me faudrait une vignette », « j'ai besoin d'une image » : deux façons de demander aussi
                      # courantes que « fais-moi », et qui ne déclenchaient rien (trou trouvé le 27/11).
                      r"|fau[dt](?:rait|ra)?|besoin d'une?|il nous faut)\b"
                      # Mots d'image fixe ajoutés le 27/11 après la mission M5 : « fais-moi une image pour Instagram » ne
                      # déclenchait rien, alors que c'est la demande la plus courante. « image » exclut les images
                      # d'informatique (docker, disque, ISO…), qui ne sont pas des créations visuelles.
                      r".{0,80}\b(?:site|page|landing|logo|visuel|affiche|banniere|interface|maquette|video|film|montage|animation|motion|objet|modele 3d|3d|scene|rendu|carrousel|post"
                      r"|image(?!\s+(?:docker|disque|iso|systeme|conteneur|machine))s?|illustration|dessin|story|stories|vignette|miniature|flyer|couverture|icone|pictogramme)\b")
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
RAPPEL_BRIEF = ("[CIRCÉ, réflexe « toujours des exemples » : le fichier que tu viens de lire est un brief de création, et il "
                "ne donne aucun exemple. " + RAPPEL[len("[CIRCÉ, réflexe « toujours des exemples » : cette demande lance une création visuelle sans exemple. "):])


# Défaut D2 (relevé par la session binôme le 27/11/2026) : un vrai client n'écrit pas toujours sa demande dans le fil de la
# conversation — il envoie un brief, et l'utilisateur le dépose dans un fichier que Claude ouvre. Le réflexe ne voyait que la
# phrase tapée : le brief lu passait sans aucun rappel. Il regarde maintenant aussi le contenu d'un fichier LU pendant le tour.
# Garde-fous, pour ne pas crier sur n'importe quel fichier : seulement un fichier de texte (pas du code), court (un brief est
# court), hors des dossiers de service, et le même filtre « création sans exemple » que pour la phrase tapée.
TEXTE_LISIBLE = (".md", ".markdown", ".txt", ".rst", ".eml", ".brief", "")
DOSSIERS_DE_SERVICE = (".circe", ".git", "node_modules", "__pycache__", "site-packages", ".claude")
BRIEF_MAXIMUM = 20_000   # au-delà, ce n'est plus un brief : document, journal, code


def _contenu_lu(evenement: dict) -> str:
    """Le texte renvoyé par l'outil Read, quelle que soit la forme (chaîne, ou objet avec « content »/« text »/« file »)."""
    r = evenement.get("tool_response")
    for _ in range(3):
        if isinstance(r, str):
            return r
        if isinstance(r, list):
            return "\n".join(x for x in r if isinstance(x, str))
        if isinstance(r, dict):
            for cle in ("content", "text", "file"):
                if cle in r:
                    r = r[cle]
                    break
            else:
                return ""
        else:
            return ""
    return r if isinstance(r, str) else ""


def brief_lu(evenement: dict) -> bool:
    """Vrai si l'outil qui vient de tourner a lu un brief de création, sans exemple."""
    if evenement.get("tool_name") != "Read":
        return False
    chemin = str((evenement.get("tool_input") or {}).get("file_path") or "")
    if not chemin:
        return False
    p = Path(chemin)
    if p.suffix.lower() not in TEXTE_LISIBLE:
        return False
    parties = {x.lower() for x in p.parts}
    if parties & set(DOSSIERS_DE_SERVICE):
        return False
    contenu = _contenu_lu(evenement)
    if not contenu or len(contenu) > BRIEF_MAXIMUM:
        return False
    contenu = sans_accents(contenu)
    return bool(CREATION.search(contenu)) and not DEJA_DES_EXEMPLES.search(contenu)


def evaluer_lecture(evenement: dict) -> dict | None:
    """Réflexe sur un brief LU dans un fichier (hook PostToolUse)."""
    if not brief_lu(evenement):
        return None
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": RAPPEL_BRIEF}}


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
        # Un seul script pour les deux réflexes : la phrase tapée (UserPromptSubmit) et le brief lu (PostToolUse, D2).
        lecture = evenement.get("hook_event_name") == "PostToolUse" or "tool_response" in evenement
        resultat = None if en_veille() else (evaluer_lecture(evenement) if lecture else evaluer(evenement))
    except Exception:
        return 0
    if resultat:
        sys.stdout.write(json.dumps(resultat))
    return 0


if __name__ == "__main__":
    sys.exit(main())
