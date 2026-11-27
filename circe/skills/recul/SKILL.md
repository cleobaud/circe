---
name: recul
description: Point de recul de CIRCÉ. S'arrêter et relire tout ce qui a été fait depuis le dernier point (demandes, fichiers, plan, promesses). Relancer les preuves, chercher les erreurs et les oublis, corriger, puis repartir. À utiliser quand l'utilisateur dit « pause », « on fait le point », « regarde tout ce qu'on a fait », « on n'a rien loupé ? ». Aussi quand le réflexe de CIRCÉ le rappelle (toutes les 10 demandes), avant une mise en ligne, une livraison ou une vente, et à la fin d'une grosse étape.
---

# Point de recul : relire avant de continuer

Quand on avance vite, les erreurs se cachent dans ce qui « a marché ». Le point de recul les cherche exprès, sur des preuves et pas de mémoire. Il fait partie de la grande boucle de la méthode. Un réflexe de CIRCÉ le rappelle tout seul : toutes les 10 demandes, puis toutes les 5, et avant toute mise en ligne ou livraison.

## 1. Rassembler (sans rien modifier)
- Les demandes depuis le dernier point : `.circe/carnet.jsonl` (les lignes plus récentes que le dernier fichier de `.circe/recul/`) et la conversation. Pour chacune, les mots exacts de l'utilisateur.
- Le plan `.circe/PLAN.md` : les lignes cochées et leurs preuves.
- Les fichiers créés ou modifiés (listés dans le carnet).
- Ce qui a été promis à l'utilisateur dans les réponses (« je vais… », « c'est en ligne », « c'est corrigé »).

## 2. Contrôler, demande par demande (une ligne chacune)
- **À la lettre** : ce qui a été fait est-il ce qui était demandé ? Relis ses mots, pas ton résumé.
- **Preuve encore vraie** : relance la commande, le test, la capture ou l'adresse. Un résultat d'il y a une heure ne prouve pas l'état actuel.
- **Promesses** : chaque « je vais » a-t-il été fait ? Sinon, il va au plan ou se dit.
- **Cohérence** : même prix, même nom, même version, même texte partout (site, boutique, documents, langues).
- **Chiffres et heures** : chacun a-t-il sa source (fichier, commande, horloge) ?
- **Oublis** : le légal (mentions, conditions, données personnelles), les autres langues, le téléphone, la sauvegarde, la sécurité. Et ce que l'utilisateur risque d'ignorer : impôts, contrats, échéances.
- **Ce qui a demandé plusieurs essais** : la cause est-elle comprise et retenue (`circe:memoire`) ?

## 3. Écrire le point
`.circe/recul/AAAA-MM-JJ_HHMM.md`, avec l'heure de l'horloge du système. Quatre parties :
- **SÛR** : ce qui a été vérifié, avec la preuve relancée.
- **À CORRIGER** : les erreurs trouvées.
- **OUBLIS** : ce qui manquait.
- **LEÇONS** : ce qu'il faut retenir.

## 4. Corriger, puis repartir
- Corrige tout de suite ce qui est sûr et petit, et vérifie la correction.
- Le reste va au plan, à sa place. On ne réordonne pas le plan pour autant.
- Dis à l'utilisateur, en 10 lignes au plus : ce qui est sûr, ce qui a été corrigé, ce qui reste, ce qu'il doit savoir ou faire.
- Puis reprends la première ligne non cochée du plan.

## Règles
- Rien ne se coche de mémoire.
- Un point de recul qui ne trouve rien doit dire ce qu'il a vérifié. Sinon, il n'a pas été fait.
- Une erreur trouvée se dit, même si elle est gênante. On ne réécrit pas l'histoire.
