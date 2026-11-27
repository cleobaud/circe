---
name: mouvement
description: Parcours CIRCÉ pour les transitions et animations (site, interface, vidéo « edit », logo animé) qui forment un langage, à 60 images par seconde, avec le moins d'allers-retours possible. À utiliser dès qu'on ajoute ou refait du mouvement.
---

# CIRCÉ — mouvement

1. **Avant de travailler, appelle l'outil MCP `circe_methode` avec `parcours: "mouvement"`** (serveur `circe-cerveau`) et suis la méthode qu'il renvoie, du début à la fin.
2. Si l'outil répond que CIRCÉ est en veille, dis-le à l'utilisateur tel quel, sans contourner.
3. Si le serveur ne répond pas (hors ligne), dis-le, puis applique ce résumé minimal :

> Demander où va le mouvement et 1 à 5 exemples ; au plus 3 gestes tirés de l'identité, une seule courbe ; seulement opacity et transform, mouvement réduit respecté ; gestes filmés montrés avant d'animer tout le projet ; 60 images par seconde mesurées.

La méthode détaillée est la propriété de CDOW ; elle n'est pas recopiée dans les fichiers du projet.

## Le vérificateur de mouvement (outil de CDOW, servi avec la clé)
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/outil.py" mouvement <page.html> [autres pages]
```
Contrôles M1 à M6 (mouvement réduit, propriétés animées, apparitions partout, durées, boucles infinies, signature unique). Un « défaut » se corrige avant de montrer. Ce sont des repères : la fluidité se mesure à part.
