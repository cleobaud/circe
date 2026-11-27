---
name: qualite
description: "Boucles universelles de qualité de CIRCÉ, à passer AVANT de montrer quoi que ce soit (aperçu, version, rendu, logo, page, vidéo) : niveau comparé à la référence côte à côte, changement de moyen si le niveau est hors d'atteinte, regard pro, corrections de l'utilisateur devenues règles. À utiliser avant chaque « voici »."
---

# CIRCÉ — qualite

1. **Avant de travailler, appelle l'outil MCP `circe_methode` avec `parcours: "qualite"`** (serveur `circe-cerveau`) et suis la méthode qu'il renvoie, du début à la fin.
2. Si l'outil répond que CIRCÉ est en veille, dis-le à l'utilisateur tel quel, sans contourner.
3. Si le serveur ne répond pas (hors ligne), dis-le, puis applique ce résumé minimal :

> Avant chaque « voici » : poser le résultat à côté de la référence (scripts/cote_a_cote.py), faire juger chaque axe par un regard neuf (sous-agent), corriger ce qui est en dessous (3 tours au plus) ; si le moyen ne peut pas atteindre le niveau, en changer ou dire l'écart avant de montrer.

La méthode détaillée est la propriété de CDOW ; elle n'est pas recopiée dans les fichiers du projet.

## L'outil de la boucle 1 (côte à côte)
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/cote_a_cote.py" "<référence>" "<résultat>"
```
Plusieurs références possibles, le résultat toujours en dernier ; `--haut 900` pour un premier écran ; `--titres "Référence,Résultat"`. Si `python` n'existe pas : `python3` ou `py -3`.
