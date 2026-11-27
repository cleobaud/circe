# Versions de CIRCÉ

## 0.6.0 — 27/11/2026

Cette version réunit tout ce qui a été corrigé depuis la 0.5.0, la dernière que vous avez pu installer : les 0.5.1 à
0.5.3 n'ont jamais été publiées (annonce de la version au démarrage, mise à jour automatique, et son correctif Windows ;
leurs sections détaillées sont plus bas).

- **CIRCÉ vous dit où il en est, et ne vous laisse plus croire qu'il est cassé.** Nouvelle commande
  `python scripts/etat.py` : version installée, état de la licence, serveur joignable ou non, nombre de compétences
  compté dans le produit, puis ce qui marche **sans** le serveur (mémoire du projet, système immunitaire, compétences
  et leurs résumés, outils de contrôle) et ce qui l'attend (la méthode détaillée, les outils servis). `--hors-ligne`
  donne la phrase courte à lire quand la connexion manque.
- **Vous voyez si un outil de CIRCÉ a été modifié sur votre poste.** Le paquet porte le relevé signé de ses fichiers ;
  au démarrage, CIRCÉ dit en une ligne ce qui a changé, et la commande pour revenir à l'origine
  (`claude plugin update circe@circe-cdow`). Il ne bloque jamais : c'est votre ordinateur. Un relevé non signé ou
  réécrit est signalé comme tel.
- **La mise à jour automatique ne s'installe plus que depuis la place de marché officielle de CDOW.** Toute autre
  source (dossier local, autre dépôt) est annoncée au démarrage, et rien ne s'installe tout seul.
- **CIRCÉ mesure une image au lieu de la deviner.** `scripts/regarder.py` donne, pour une image,
  sa taille, sa luminance, ses cinq couleurs dominantes, sa part transparente et sa plus grande bande unie — la zone où
  un texte se pose sans boîte ni voile. Nouvelle compétence `circe:visuel` (publication, story, affiche, bannière),
  nouvelle compétence `circe:schema-video` (une série de vidéos : un format fixe, un contenu neuf à chaque épisode).
- **Les contrôles d'une vidéo sont outillés** : `scripts/video.py controler` vérifie le cadre, les images par seconde,
  la durée, la présence ou l'absence de son, les images noires, et sort une planche de 12 images ;
  `video.py registre` refuse un épisode qui reprend un plan déjà montré ; `video.py polices` vérifie qu'une police
  couvre bien tout le texte **avant** le rendu ; `video.py pieges` liste les erreurs déjà commises, à lire avant de produire.
- **Les réflexes voient enfin les cas les plus courants.** Le rappel « toujours des exemples » se déclenche aussi quand
  le brief est lu dans un fichier (et non tapé dans la conversation), et sur les demandes d'image qu'il ratait
  (« fais-moi une image pour Instagram », « il me faudrait une vignette »). Le rappel « pas de fini sans preuve »
  entend maintenant les formules que CIRCÉ lui-même emploie (« FAIT : … », « ça marche »).
- **CIRCÉ propose un plan quand le travail le mérite** : quand un projet a déjà plusieurs demandes derrière lui, dont au
  moins une qui a produit des fichiers, et toujours pas de `.circe/PLAN.md`. Une seule fois, jamais imposé.
- **La méthode servie reste chez vous, et chez nous.** Elle ne peut plus être écrite dans un fichier de projet ni
  envoyée à une automatisation : ce refus n'est pas une protection que vous activez, c'est le contrat de licence, et il
  protège aussi vos fichiers d'une copie qui ne vous appartient pas. Ce que CIRCÉ produit pour vous, lui, reste à vous
  et sort librement.
- **Une mise à jour garde votre clé et la mémoire de vos projets** ; c'est une désinstallation qui efface la clé. C'est
  maintenant écrit à l'écran la première fois qu'un projet voit une nouvelle version.
- Essais : 249 tests automatiques passent sur cette version (109 avant la journée du 27/11). Chaque correction a les
  siens, et plusieurs ont été écrits à partir d'erreurs réelles rejouées telles quelles.

## 0.5.3 — 27/11/2026
- **Correction : sous Windows, la mise à jour automatique de la 0.5.2 ne démarrait pas.** La commande `claude` y est un fichier `.CMD` ; lancée par son nom seul, elle était introuvable. CIRCÉ résout maintenant son chemin complet avant de la lancer, et ne tente rien si Claude Code n'est pas dans le PATH. Trouvé par un essai de bout en bout, pas par relecture.

## 0.5.2 — 27/11/2026
- **CIRCÉ se met à jour lui-même.** Au démarrage, il regarde si une version plus récente existe et l'installe seul, sans rien demander. Elle prend la main au prochain lancement de Claude Code : les plugins se chargent au démarrage, c'est une limite de Claude Code et non un choix de CIRCÉ. Tout est dit en une ligne, jamais en silence.
- Pour reprendre la main : `python scripts/maj.py proposer` (CIRCÉ demandera avant d'installer) ou `python scripts/maj.py jamais`. `python scripts/maj.py etat` dit ce qui est installé, ce qui est disponible et le réglage.
- Aucun appel réseau dans le plugin : ce sont `claude plugin marketplace update` et `claude plugin update`, lancés détachés, qui vont voir. Une commande absente, un catalogue illisible ou une panne n'empêchent jamais une session de démarrer, et une tentative ratée ne se répète pas en boucle.
- Essais : 15 tests pour la mise à jour (les trois réglages, la comparaison des versions, les pannes), 133 au total.

## 0.5.1 — 27/11/2026
- **Au démarrage, CIRCÉ dit quelle version est installée et comment en chercher une plus récente.** La première fois qu'un projet voit une version, il résume aussi ce qu'elle apporte (nouvelles compétences, nouveaux réflexes). Tout est lu dans le paquet : aucun appel réseau, rien à configurer.
- **Le réflexe du niveau ne relance plus à tort.** Il vérifie qu'un fichier visuel a vraiment été écrit ou modifié pendant le tour, au lieu de chercher des mots (« aperçu », « logo », « visuels ») dans la réponse de Claude. Essai réel du 27/11 : deux relances injustifiées de suite, sur un état des lieux puis sur un audit, alors que rien n'avait été produit.
- Essais : 109 tests automatiques avant ces deux corrections, et de nouveaux tests pour chacune (dont les deux relances injustifiées, rejouées telles quelles).

## 0.5.0 — en préparation : rien d'imposé
- **À l'installation, CIRCÉ n'impose rien.** Par défaut, il refuse seulement 3 gestes catastrophiques : formater un disque, effacer la racine d'un disque, effacer le dossier personnel. Claude vous l'explique dès la première session, puis le rappelle quand il le faut.
- **Les autres protections sont proposées, jamais appliquées d'office** : suppression récursive, `git push`, réécriture d'historique git, mise en production, publication d'un paquet, script téléchargé puis exécuté, base de données, fichiers de secrets, dossiers du système, réglages de Claude Code, envois par un outil connecté. Quand un geste qu'une protection aurait couvert passe, Claude vous la propose une fois, en une phrase ; il ne l'active jamais lui-même.
- Vous activez ce que vous voulez avec « configure CIRCÉ » (`scripts/protections.py`). Une protection activée refuse ou demande votre accord, comme avant. Désactiver une protection demande toujours votre accord.
- Nouveau réflexe `propositions.py` (à chaque demande, rien de bloqué) ; le journal des propositions ne contient jamais la commande.
- Correction (relecture de Codex) : un réflexe ne répond plus deux fois au même événement quand deux interprètes Python renouvellent en même temps un ancien jeton (verrou exclusif).

## 0.4.0 — 24/11/2026 (niveau CDOW)
- **Nos outils, avec la clé** : le plugin ne contient pas leur code ; `scripts/outil.py` le demande au serveur avec votre clé, vérifie son empreinte et la **signature de CDOW** (clé publique dans le plugin ; la clé privée n'est ni dans le plugin ni au serveur : un serveur détourné ne pourrait pas faire passer un faux outil), le lance sur votre ordinateur, puis l'efface. Trois outils pour commencer : le **Quai** (analyser un paquet npm, PyPI ou GitHub AVANT de l'installer, sans l'exécuter : provenance, intégrité, licence, fouille du code, verdict VERT / ORANGE / ROUGE), le **vérificateur de mouvement** (contrôles M1 à M6 d'une page) et le **contrôle de sécurité public** (e-mails, site, mentions, traceurs : seulement ce que tout visiteur voit).
- Nouveau parcours `integrations` : ce que Claude Code sait déjà faire, puis, par besoin (animation, site, vidéo, 3D, image), les outils que nous utilisons vraiment, avec source officielle, licence, installation, vérification et verdict du Quai ; rien ne s'installe sans votre accord, un outil à la fois.
- Nouveau parcours `systeme` : monter une base de travail comme la nôtre (mémoire et rituels, coffre de notes, téléphone, tâches planifiées, second avis, orchestre), une étape à la fois, chacune vérifiée, coût dit à l'avance.
- La méthode servie est sous licence : Claude l'applique pendant le travail sans la recopier ni l'enregistrer ; vos fichiers, vos idées et vos résultats restent à vous.
- Mouvement : plus d'effets tout faits à copier ; les repères techniques (durées, courbes) et les contrôles restent.
- Nouveau parcours `illustration` : une gravure, une estampe ou une frise se fait avec de vraies images anciennes libres de droits (provenance et mention de droits gardées), recolorées et composées dans la page, jamais en silhouettes dessinées en code.
- Nouveau parcours `design` : le concept écrit avant le code, le registre du client mesuré (sobre ou riche), chaque effet (intro, transitions, défilement, 3D, son, mascotte) utilisé, adapté ou écarté avec sa raison, et des contrôles chiffrés.
- Nouveau parcours `securite` : protéger une petite entreprise pas à pas, avec l'accord du gérant à chaque modification (e-mails SPF, DKIM et DMARC ; site ; mentions légales, confidentialité, cookies ; comptes ; rapport). On ne lit que ce qui est public ; jamais de mot de passe.
- Méthode servie en version 1.4.

## 0.3.0 — 24/11/2026
- Nouvelle compétence `recul` : le point de recul. Claude s'arrête, relit tout ce qui a été fait depuis le dernier point (demandes, fichiers, plan, promesses), relance les preuves, cherche les erreurs et les oublis, corrige, puis repart. Un réflexe le rappelle toutes les 10 demandes (puis toutes les 5), avant une mise en ligne ou une livraison, et quand vous dites « pause » ; la garde le rappelle aussi avant une mise en production.
- C'est CIRCÉ qui demande : chaque parcours commence par son kit de départ (exemples, matière, message, public), demandé en un seul message, seulement ce qui manque.
- Nouveau parcours `identite` : logo et identité visuelle, dont la restylisation d'un logo existant (on garde ses invariants, on l'améliore dans un style, contrôle de reconnaissance), 3 pistes sur une planche, grammaire, déclinaison d'un bloc.
- Nouveau parcours `mouvement` : transitions et animations qui forment un langage (3 gestes au plus), aperçu filmé avant d'animer, 60 images par seconde mesurées.
- Site : un site en plusieurs langues s'adapte au public de chaque langue (prix et taxes du pays, exemples, mentions).
- Vos autorisations sont respectées : CIRCÉ lit celles que vous avez déjà données dans Claude Code (règles « allow », mode bypassPermissions) et ne redemande jamais ce qui est déjà autorisé (par exemple les réponses dans votre propre messagerie). Il n'y touche jamais ; une modification de ces réglages par Claude demande votre accord. « configure CIRCÉ » les recense. Les gestes irréversibles restent refusés quoi qu'il arrive.
- Le réflexe de preuve ne prend plus une citation (« dites-moi « fait » quand c'est terminé »), une condition ou une question pour une annonce de fin, et ne compte plus comme preuve ce qui est remis à plus tard (« à vérifier plus tard : rapport.pdf »).
- Les réflexes « toujours des exemples » et « point de recul » comprennent aussi les mots tapés sans accents (« cree un logo », « genere une affiche », « on a rien loupe ») et « on fait le point ».
- Jamais en dessous du niveau : nouvelle compétence `qualite` et nouvel outil `cote_a_cote.py`. Avant chaque « voici », le résultat est posé à côté des références sur une seule image, jugé par un regard neuf, corrigé (3 tours au plus) ; si le moyen choisi ne peut pas atteindre le niveau, Claude change de moyen ou dit l'écart avant de montrer. Un réflexe le rappelle quand un livrable est présenté sans cette comparaison.
- `regarder.py` capture aussi une page locale (adresse `file:///`), sans serveur à lancer.
- Méthode servie en version 1.3.
- Essais : 78 tests automatiques, Windows vierge, et un test « nouvel utilisateur » sur un Claude Code vierge.

## 0.2.0 — 24/11/2026 (offre de lancement et de test)
- Méthode en boucles : une grande boucle de la demande à la livraison, de petites boucles (exemple, aperçu, contrôle, correction) dans chaque étape ; comprendre le GENRE d'un exemple avant son design.
- Méthode servie à jour par le serveur de CIRCÉ, seulement aux abonnés actifs, marquée au nom de l'abonné ; résumé de secours hors ligne.
- Nouvelle compétence `exemples` : vidéos (planche de 12 images, durée, cadre, images par seconde, son, plans par minute), sites (captures), images.
- Nouvelle compétence `configurer` : inventaire du poste et de Claude Code (outils, connexions, extensions, sans jamais lire un secret), but de l'utilisateur, circuit adapté, profil relu à chaque démarrage.
- Nouvelle compétence `sortie` : un livrable validé part vers n8n, Make, Zapier ou votre outil (fiche JSON, jamais le contenu des fichiers).
- Mémoire : carnet automatique de chaque demande et des fichiers touchés, remis au démarrage.
- Clé saisie une fois à l'installation, gardée dans le coffre sécurisé de Claude Code.
- Réflexes lancés sans shell (python3, python ou py) : plus besoin de Git pour Windows.
- Essais : 54 tests automatiques, plus de vraies sessions de Claude Code (méthode servie, mémoire redite par une nouvelle session).

## 0.1.0 — 24/11/2026 (préversion)
- Système immunitaire :
  - garde avant chaque action : refus de l'irréversible, accord demandé pour le sensible, y compris les outils MCP d'envoi et de publication ;
  - pas de « fini » sans preuve (une relance au plus par fin de tour) ;
  - journal sans aucun argument de commande.
- Méthode : 12 compétences, dont le parcours général, le site, la vidéo, l'objet 3D, les références visuelles et la preuve. Réflexe « toujours des exemples, toujours un aperçu » à chaque demande de création.
- Mémoire : relais du projet remis au démarrage, copie avant le résumé de la conversation, journal des décisions, préférences, erreurs et leçons.
- Règles de conduite (12) chargées à chaque démarrage : lire à la lettre, avis franc avant de produire, plan suivi ligne par ligne (compétence `plan`), rien d'inventé, preuve, réponses courtes.
- Licence : clé d'abonnement vérifiée au plus une fois par 24 h, grâce hors ligne de 7 jours, veille si l'abonnement s'arrête, 3 PC par clé.
- Hooks lancés par `python3`, sinon `python` : fonctionnent par sh (Git Bash, macOS, Linux) et par cmd.exe.
- Essais : 33 tests automatiques (dont les commandes des hooks par cmd.exe et par bash), plus trois essais dans de vraies sessions de Claude Code.
