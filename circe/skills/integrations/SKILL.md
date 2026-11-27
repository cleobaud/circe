---
name: integrations
description: "Catalogue des intégrations de CIRCÉ (servi par le serveur) : ce que Claude Code sait faire, et pour chaque besoin (animation, site, 3D, vidéo, image et logo…) les outils, connecteurs, plugins et compétences à proposer, avec leur source officielle, leur licence et leur installation. À utiliser dès qu'un projet demande une capacité qui n'est pas encore installée, ou qu'un exemple de l'utilisateur montre un rendu à reproduire."
---

# CIRCÉ — integrations

1. **Avant de travailler, appelle l'outil MCP `circe_methode` avec `parcours: "integrations"`** (serveur `circe-cerveau`) et suis la méthode qu'il renvoie, du début à la fin.
2. Si l'outil répond que CIRCÉ est en veille, dis-le à l'utilisateur tel quel, sans contourner.
3. Si le serveur ne répond pas (hors ligne), dis-le, puis applique ce résumé minimal :

> Tirer le besoin de l'exemple de l'utilisateur, faire l'inventaire de ce qui est déjà installé, proposer seulement ce que la tâche demande (rôle, taille, licence, payant ou non), passer chaque outil au Quai, installer un par un depuis la source officielle avec l'accord de l'utilisateur, vérifier chaque installation.

La méthode détaillée est la propriété de CDOW ; elle n'est pas recopiée dans les fichiers du projet.

## Le Quai : passer chaque outil AVANT de l'installer (outil de CDOW, servi avec la clé)
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/outil.py" quai npm:<paquet> | pypi:<paquet> | github:<propriétaire>/<dépôt> | url:<adresse d'une archive>
```
VERT : installable depuis la source officielle. ORANGE : lis les points avec l'utilisateur avant d'installer. ROUGE : ne pas installer en l'état. Le Quai ne tourne qu'avec une clé valide et une connexion : sinon, dis-le, et ne remplace pas son verdict par une impression. Un installeur officiel signé (Python, Node.js, Blender, Claude Code) se vérifie par sa source : le domaine officiel, jamais un miroir.
