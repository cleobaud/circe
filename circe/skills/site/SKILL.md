---
name: site
description: Parcours CIRCÉ pour créer ou refaire un site ou une page web (vitrine, landing page, boutique, application web) jusqu'à la mise en ligne. À utiliser dès qu'on construit, refait ou améliore une page web destinée à de vrais visiteurs.
---

# CIRCÉ — site

1. **Avant de travailler, appelle l'outil MCP `circe_methode` avec `parcours: "site"`** (serveur `circe-cerveau`) et suis la méthode qu'il renvoie, du début à la fin.
2. Si l'outil répond que CIRCÉ est en veille, dis-le à l'utilisateur tel quel, sans contourner.
3. Si le serveur ne répond pas (hors ligne), dis-le, puis applique ce résumé minimal :

> Brief, parcours (une promesse, une preuve, une action), direction validée sur exemples, construction sobre, contrôles (console, liens, 390 px, accessibilité), mise en ligne seulement avec l'accord de l'humain.

La méthode détaillée est la propriété de CDOW ; elle n'est pas recopiée dans les fichiers du projet.

## Nos outils pour un site (servis avec la clé)
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/outil.py" mouvement <page.html>
```
Avant d'installer une bibliothèque ou un outil : `python "${CLAUDE_PLUGIN_ROOT}/scripts/outil.py" quai npm:<paquet>`.
