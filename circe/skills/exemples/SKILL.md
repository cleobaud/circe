---
name: exemples
description: Regarder pour de vrai les exemples donnés par l'utilisateur (vidéos, sites, images) avant de concevoir quoi que ce soit, puis écrire la fiche d'analyse. À utiliser dès que l'utilisateur fournit ou cite des exemples (« comme cette vidéo », « dans le style de ce site », un fichier .mp4, une capture, une adresse), et avant toute vidéo, tout site ou tout visuel fait « à partir de » quelque chose.
---

# Exemples : regarder avant de concevoir

On ne décrit jamais un exemple qu'on n'a pas regardé.

1. **Regarder** : une seule commande pour tous les exemples. Elle marche telle quelle dans bash et dans PowerShell ; si `python` n'existe pas, utilise `python3` ou `py -3`.
   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/regarder.py" "<fichier ou adresse 1>" "<fichier ou adresse 2>"
   ```
   - Vidéo (fichier) : planche de 12 images, durée, cadre, images par seconde, son, nombre de plans et plans par minute.
   - Site (adresse) : captures ordinateur (1440 px) et petit écran (500 px). Pour le téléphone exact, demande une capture faite sur un téléphone.
   - Image (photo, logo, visuel) : taille, cadre, poids, luminance, part sombre et claire, 5 couleurs dominantes, part transparente, et la plus grande bande unie — la zone où un texte se pose sans boîte ni voile.
   - Vidéo en ligne (TikTok, YouTube…) : pas de téléchargement. Demande le fichier, ou 6 à 12 captures.
   - S'il manque ffmpeg ou un navigateur, le résultat le dit : transmets le conseil tel quel.
2. **Ouvrir les images** (planche, captures) avec l'outil de lecture d'image et les regarder vraiment.
3. **Écrire la fiche** `.circe/exemples/<nom>/FICHE.md` pour chaque exemple, puis une synthèse :
   - **le genre** : ce qui le définit, indépendamment de la marque (méthode `references-visuelles`) ;
   - **le rythme** : plans par minute, durée, accroche des 2 premières secondes, fin ;
   - **le cadre et la composition** : où sont le sujet et le texte, les marges, la densité ;
   - **la typographie et les couleurs** : style, taille, contraste ;
   - **le son** : voix, musique, silence (d'après les mesures, et ce que l'utilisateur en dit) ;
   - **ce qu'on reprend** et **ce qu'on laisse**, en 3 lignes chacun.
4. **Montrer** la synthèse à l'utilisateur en 5 lignes au plus. Puis enchaîner sur le déroulé et les aperçus (parcours `video` ou `site`).

Les exemples restent dans le projet (`.circe/exemples/`) : rien n'est envoyé ailleurs. Jamais de copie : on garde le genre et les principes, pas le design ni les textes d'un autre.
