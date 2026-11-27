---
name: cloture
description: Clore une tâche ou une session en écrivant le relais CIRCÉ, pour que la session suivante reprenne au bon endroit. À utiliser à la fin d'une tâche importante, avant une pause, quand l'utilisateur dit « on s'arrête », « clôture », « à demain ».
---

# Clôture : laisser la page que la prochaine session lira en premier

1. Noter au journal ce qui mérite d'être retenu (`circe:memoire`) : décisions, préférences, erreurs et leurs corrections.
2. Écrire le relais, en UNE seule ligne de commande. Elle marche telle quelle dans bash et dans PowerShell. Si `python` n'existe pas, utilise `python3` ou `py -3`.
   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/memoire.py" relais --objectif "<l'objectif du projet en une phrase>" --tache "<la tâche en cours, ou « aucune »>" --fait "<ce qui est fait, avec sa preuve>" --suite "<la prochaine action précise et son critère de réussite>" --bloque "<ce qui attend l'humain, s'il y en a>"
   ```
   Le relais est court : le détail va au journal. Toutes les valeurs viennent de la session, aucune n'est inventée. L'ancien relais est gardé automatiquement dans `.circe/historique/`.
3. Relire le relais écrit (`python "${CLAUDE_PLUGIN_ROOT}/scripts/memoire.py" lire`) et le résumer à l'utilisateur en 3 lignes.

Même sans clôture, le carnet automatique garde les dernières demandes et les fichiers touchés. Mais seul le relais dit la prochaine action avec certitude.
