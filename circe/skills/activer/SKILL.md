---
name: activer
description: Activer ou vérifier la licence d'abonnement de CIRCÉ sur ce PC. À utiliser quand l'utilisateur donne sa clé de licence, dit « active CIRCÉ », « ma licence », ou quand CIRCÉ annonce qu'il est en veille.
---

# Activer CIRCÉ

1. **La bonne façon** : la clé se règle une fois, dans Claude Code. Dis à l'utilisateur de taper `/plugin configure circe@circe-cdow`, de coller au réglage « licence » la clé reçue par e-mail après l'abonnement, puis de redémarrer Claude Code. Claude Code garde la clé dans son coffre sécurisé. CIRCÉ s'active seul au démarrage suivant, et la méthode est servie.
2. **Vérifier l'état** (sans réseau), une ligne qui marche dans bash et dans PowerShell (si `python` n'existe pas : `python3` ou `py -3`) :
   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/licence.py" etat
   ```
   Pour revérifier auprès de la plateforme : `licence.py verifier`.
3. Lire la réponse en entier et la redire à l'utilisateur :
   - `actif` : CIRCÉ est prêt. Proposer `circe:demarrage`, puis un premier travail avec `circe:methode`.
   - `veille` : donner la raison telle qu'elle est écrite (abonnement terminé, paiement refusé, clé activée sur trop de PC, aucune clé) et l'adresse d'aide de la page de CIRCÉ.
4. Pour retirer la clé de ce PC : `licence.py oublier`, puis vider le réglage avec `/plugin configure circe@circe-cdow`.

Ne jamais écrire la clé dans la mémoire, un fichier du projet ni un message. Ne jamais la demander en clair dans la conversation : elle se colle dans `/plugin configure`.
