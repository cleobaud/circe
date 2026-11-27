---
name: sortie
description: Passer un livrable VALIDÉ par l'utilisateur à ses automatisations (n8n, Make, Zapier, son propre outil ou son cloud) pour qu'elles le publient ou le traitent, ou brancher ces automatisations. À utiliser quand l'utilisateur dit « envoie à n8n », « publie-le via mon automatisation », « branche mon webhook », « dès que c'est fini, poste-le », ou à la fin d'un parcours quand une automatisation est branchée.
---

# Sortie : CIRCÉ crée, l'automatisation de l'utilisateur publie

CIRCÉ est une partie du système de l'utilisateur : la partie création. Il passe le relais à ses autres outils. Il ne publie jamais lui-même.

## Brancher (une fois par PC)
1. Demande l'adresse du webhook de son automatisation : n8n « Webhook » en méthode POST, Make « Custom webhook », Zapier « Catch Hook ».
2. Une seule ligne, qui marche dans bash et dans PowerShell (si `python` n'existe pas : `python3` ou `py -3`) :
   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/sortie.py" brancher "<adresse https du webhook>"
   ```
   L'adresse reste sur ce PC (`~/.circe/connexions.json`). Elle n'est jamais écrite dans le projet ni répétée en entier dans un message.
3. Fais un essai, marqué comme tel :
   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/sortie.py" livrer --essai --type texte --titre "Essai CIRCÉ" --fichiers "<un petit fichier du projet>"
   ```
   Demande à l'utilisateur s'il voit l'essai arriver dans son automatisation.

## Livrer (après la validation de l'utilisateur, jamais avant)
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/sortie.py" livrer --type video --titre "<titre>" --fichiers "<fichier final>" "<miniature>" --texte "<légende validée>" --reseau "<tiktok, instagram, linkedin…>"
```
- La fiche JSON est toujours gardée dans `.circe/sorties/`, même sans automatisation branchée.
- Par défaut, seuls les chemins et les tailles des fichiers partent. Si l'automatisation tourne AILLEURS (n8n en ligne, Make, Zapier) et ne peut pas lire le PC, ajoute `--joindre` : les fichiers partent avec la fiche (100 Mo au plus). Seulement si l'utilisateur l'a demandé ou accepté : c'est son contenu qui sort.
- Redis le résultat tel quel (« envoyé », « refusé », « envoi impossible »).
- Publier au nom de l'utilisateur reste SA décision. Si la protection « actions vers l'extérieur » est activée, le système immunitaire demandera son accord ; sinon, demande-le toi-même avant de publier en son nom.

## Pour l'automatisation : ce qu'elle reçoit
`source` (« circe »), `version`, `essai`, `type`, `titre`, `fichiers` (chemin, nom, octets), `texte`, `reseau`, `projet`, `cree_le`.
