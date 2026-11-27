---
name: video
description: Parcours CIRCÉ pour une vidéo, un film court, un montage ou une animation (réseaux sociaux, présentation, publicité), du découpage au rendu vérifié. À utiliser dès qu'on produit ou modifie une vidéo.
---

# CIRCÉ — video

1. **Avant de travailler, appelle l'outil MCP `circe_methode` avec `parcours: "video"`** (serveur `circe-cerveau`) et suis la méthode qu'il renvoie, du début à la fin.
2. Si l'outil répond que CIRCÉ est en veille, dis-le à l'utilisateur tel quel, sans contourner.
3. Si le serveur ne répond pas (hors ligne), dis-le, puis applique ce résumé minimal :

> Intention, découpage plan par plan, aperçu de 3 à 8 images avant le long rendu, rendu, contrôles (durée, images par seconde, son, planche d'images).

**Avant de produire, lis les erreurs déjà commises** (elles coûtent un rendu chacune) :
`python "${CLAUDE_PLUGIN_ROOT}/scripts/video.py" pieges`

**Après le rendu** (code de sortie 1 s'il reste un écart) :
`python "${CLAUDE_PLUGIN_ROOT}/scripts/video.py" controler <fichier.mp4> --cadre 1080x1920 --ips 30 --duree 30-45 --son non --planche`
Pour une série, avant chaque épisode : `… registre <fichier.mp4> --schema <nom> --ignorer-debut 4 --ignorer-fin 4 --ecrire`.

La méthode détaillée est la propriété de CDOW ; elle n'est pas recopiée dans les fichiers du projet.
