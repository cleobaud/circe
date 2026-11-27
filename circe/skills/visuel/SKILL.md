---
name: visuel
description: Parcours CIRCÉ pour une image fixe : publication et story de réseau social, affiche, bannière, visuel d'annonce ou de vente. Du brief au fichier aux dimensions exactes, lisible en vignette, dans la typographie de la marque. À utiliser dès qu'on produit une image (pas un logo : `circe:identite` ; pas un dessin : `circe:illustration`).
---

# CIRCÉ — visuel

1. **Avant de travailler, appelle l'outil MCP `circe_methode` avec `parcours: "visuel"`** (serveur `circe-cerveau`) et suis la méthode qu'il renvoie, du début à la fin.
2. Si l'outil répond que CIRCÉ est en veille, dis-le à l'utilisateur tel quel, sans contourner.
3. Si le serveur ne répond pas (hors ligne), dis-le, puis applique ce résumé minimal :

> Une idée et sa preuve, trois niveaux de texte au plus (20 mots en tout), accroche lisible quand l'image fait 360 px, aucune zone morte, polices de la marque réellement chargées, formats et zones sûres du réseau vérifiés — 1080 × 1080 et 1080 × 1920 sont les seuls mesurés chez nous, tout autre se demande ou se lit sur la page du réseau. MESURER chaque image reçue (`regarder.py`) : sa plus grande bande unie est la zone de texte, on la cherche avant de dessiner. Une image forte et un seul bloc de texte, marges ≥ 8 % de la largeur, une seule police, une seule couleur d'accent une seule fois ; ni boîte derrière le texte, ni voile sur la photo : si ça ne tient pas sans, c'est le cadrage qu'il faut changer. Composition en HTML capturée aux dimensions exactes par le navigateur sans fenêtre, fichier source gardé à côté de l'image. Contrôles avant de montrer : dimensions relues, vignette, contraste ≥ 4,5 : 1, zones sûres, côte à côte avec les références (`cote_a_cote.py`).

La méthode détaillée est la propriété de CDOW ; elle n'est pas recopiée dans les fichiers du projet.
