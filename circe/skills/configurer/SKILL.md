---
name: configurer
description: "Configurer CIRCÉ pour CET utilisateur et CE poste : inventaire de ce que Claude Code a déjà (outils, connexions, extensions), but de l'utilisateur, puis la configuration et le circuit de travail adaptés (par exemple vidéos produites puis publiées par son automatisation). À utiliser au premier lancement de CIRCÉ dans un projet, quand l'utilisateur dit « configure CIRCÉ », « optimise mon installation », « qu'est-ce que je peux faire avec CIRCÉ ? », ou quand son but change."
---

# Configurer : CIRCÉ s'adapte à l'utilisateur, pas l'inverse

But : que Claude utilise TOUT ce qu'il a déjà sur ce poste, au service du but réel de l'utilisateur, avec les réflexes et la méthode de CIRCÉ.

## 1. Inventaire (lecture seule, 5 secondes)
Une ligne, qui marche dans bash et dans PowerShell (si `python` n'existe pas : `python3` ou `py -3`) :
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/inventaire.py"
```
Il relève : le système, les outils de création (ffmpeg, Node, Blender, Git, navigateur…), une automatisation n8n locale, les NOMS des serveurs MCP, extensions et compétences déjà installés, les CLAUDE.md, les autorisations déjà données dans Claude Code (`autorisations_deja_donnees`), l'état de CIRCÉ. Il ne lit jamais une valeur secrète.

## 2. Le but, en UNE question
Résume l'inventaire en 3 lignes : ce qui est prêt, ce qui manque. Ajoute une ligne sur ses autorisations : « Vos autorisations Claude Code : <nombre> règles déjà données (par exemple <2 ou 3 noms>). CIRCÉ les respecte : il ne vous redemandera rien de ce que vous avez déjà autorisé, et il n'y touche pas. » Puis demande, en une seule fois :
« Qu'est-ce que vous voulez produire le plus souvent ? Sites, vidéos pour les réseaux, objets ou scènes 3D, contenus écrits, autre chose. Et que doit-il se passer quand c'est validé ? Rien, l'envoyer à un outil (n8n, Make, Zapier), le publier. »

## 3. Le circuit proposé (sortie : un tableau)
| Étape | Qui | Avec quoi (présent sur ce poste) | Ce qui manque |
|---|---|---|---|
Construis-le à partir du but et de l'inventaire, jamais d'un modèle tout fait. Exemples de circuits :
- **Vidéos pour les réseaux** : exemples de l'utilisateur (`circe:exemples`) → déroulé et aperçus (`circe:video`) → montage (ffmpeg ; Node/Remotion ou page animée s'ils sont présents) → contrôles → validation → `circe:sortie` vers son automatisation, qui publie.
- **Sites** : exemples → genre → aperçu → construction → contrôles (navigateur) → mise en ligne sur son accord.
- **3D** : références → silhouette → rendu d'essai dans Blender (si présent, ou par son serveur MCP) → rendu final.
- Utilise ce qui existe déjà : un serveur MCP déjà installé (Blender, navigateur, base de données…), une compétence ou une extension déjà présente. Ne propose pas d'installer ce qui fait doublon.

## 4. Ce qui manque : proposer, jamais imposer
Pour chaque outil manquant : à quoi il servirait dans SON circuit, la commande d'installation officielle, et son coût (gratuit ou non). Rien ne s'installe sans son accord, une installation à la fois, en vérifiant la source officielle.

## 5. Les protections : proposer, jamais imposer
CIRCÉ n'impose rien : par défaut, seuls 3 gestes catastrophiques sont refusés (formater un disque, effacer la racine d'un disque, effacer le dossier personnel). Montre la liste :
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/protections.py" etat
```
Présente-les UNE par une, avec leur intérêt pour SON circuit (ex. « envoi git » s'il publie du code, « mise en production » s'il déploie). Il active seulement ce qu'il veut :
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/protections.py" activer <nom> [<nom>…]
```
N'active jamais rien sans son oui explicite pour CETTE protection. Désactiver se fait sur sa demande (son accord est alors demandé). Note ses choix dans le profil.

## 6. Le profil (sortie : `.circe/PROFIL.md`)
Écris, en 15 lignes au plus : le but, le circuit retenu, les protections choisies, les outils présents et ceux qu'il a refusés, l'automatisation branchée ou non, la date. Note aussi la décision au journal :
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/memoire.py" noter decision "<but et circuit retenus, en une phrase>"
```
Le profil est relu à chaque démarrage. Quand le but change, refais cette compétence.

## Règles
- On adapte CIRCÉ à l'existant de l'utilisateur : ses outils, ses habitudes, ses automatisations. On ne refait pas son système.
- Une proposition à la fois, en commençant par ce qui sert le plus son but.
- Aucun réglage de Claude Code (permissions, réglages globaux) n'est modifié sans son accord explicite. Ses autorisations existantes restent telles quelles : CIRCÉ ne les retire pas, ne les réécrit pas, ne les « range » pas.
