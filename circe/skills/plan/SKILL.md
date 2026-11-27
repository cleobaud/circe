---
name: plan
description: Écrire puis suivre un plan de projet ligne par ligne, avec une preuve pour chaque ligne cochée (`.circe/PLAN.md`). À utiliser pour tout travail de plus d'une étape, quand l'utilisateur dit « fais un plan », « on suit le plan », « quelle est la prochaine étape ? », ou quand une correction de l'utilisateur change le plan.
---

# CIRCÉ — plan

1. **Avant de travailler, appelle l'outil MCP `circe_methode` avec `parcours: "plan"`** (serveur `circe-cerveau`) et suis la méthode qu'il renvoie, du début à la fin.
2. Si l'outil répond que CIRCÉ est en veille, dis-le à l'utilisateur tel quel, sans contourner.
3. Si le serveur ne répond pas (hors ligne), dis-le, puis applique ce résumé minimal :

> Écrire .circe/PLAN.md (lignes, critères écrits d'avance) ; prochaine action = première ligne non faite ; une ligne se coche avec sa preuve ; une correction de l'utilisateur s'applique tout de suite.

La méthode détaillée est la propriété de CDOW ; elle n'est pas recopiée dans les fichiers du projet.
