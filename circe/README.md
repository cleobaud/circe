# CIRCÉ 0.3 — un système pour Claude Code, inspiré du vivant

CIRCÉ ne remplace pas Claude : il lui donne des **organes** et lui sert d'appui. Il le freine quand il se précipite, garde ce qui est bien et cherche l'optimisation. Vous gardez votre propre abonnement Claude, CIRCÉ s'y ajoute.

| Organe | Ce qu'il fait | Comment |
|---|---|---|
| **Système immunitaire** | **Rien d'imposé** : par défaut, il refuse seulement 3 gestes catastrophiques (formater un disque, effacer la racine d'un disque, effacer le dossier personnel), et Claude vous l'explique dès la première session. Les autres protections vous sont **proposées**, et vous activez celles que vous voulez (« configure CIRCÉ ») : suppression récursive, `git push`, réécriture d'historique, mise en production, publication d'un paquet, script téléchargé puis exécuté, base de données, fichiers de secrets, dossiers du système, réglages de Claude Code, envois par un outil connecté. Relance Claude s'il annonce « fini » sans preuve. | réflexes (hooks) toujours actifs ; journal dans `.circe/journal-immunitaire.jsonl` |
| **Méthode, en boucles** | Une grande boucle de la demande à la livraison, et de petites boucles dans chaque étape : exemple, aperçu, contrôle, correction. **Toujours des exemples**, regardés pour de vrai (`circe:exemples` : planches d'images, rythme, captures), **toujours un aperçu** avant de construire. **C'est CIRCÉ qui demande** : donnez seulement le sujet (« un site », « un logo », « une vidéo »), il vous demande en un message ce qu'il lui faut. Décisions de design mesurées (aucun effet par réflexe). Parcours dédiés au site, à la vidéo, à l'objet 3D, à l'identité (logo, restylisation d'un logo existant), au mouvement (transitions, animations), à l'illustration (gravure, estampe, frise, avec de vraies images libres de droits) et à la sécurité d'une petite entreprise (e-mails, site, loi, comptes). La méthode détaillée est servie à jour par le serveur de CIRCÉ. | 24 compétences (`/circe`, `/circe:configurer`, `/circe:methode`, `/circe:exemples`, `/circe:site`, `/circe:integrations`, `/circe:systeme`…) ; serveur `circe-cerveau` |
| **Mémoire** | Le relais du projet et un carnet automatique (chaque demande, avec les fichiers touchés) sont remis à Claude à chaque démarrage. Le journal garde vos décisions, vos préférences et les erreurs corrigées. | `.circe/RELAIS.md`, `.circe/carnet.jsonl` et `.circe/journal.jsonl`, dans votre projet |
| **Niveau** | Avant chaque « voici », le résultat est posé à côté de vos références sur une seule image, jugé axe par axe par un regard neuf, puis corrigé. Si le moyen choisi ne peut pas atteindre le niveau (une gravure détaillée ne se dessine pas en code, par exemple), Claude change de moyen ou vous dit l'écart avant de montrer. Le but : moins de reprises. Ce contrôle ne garantit pas le résultat ; votre avis reste le dernier mot. | `circe:qualite` ; images dans `.circe/cote-a-cote/` |
| **Point de recul** | Toutes les 10 demandes, avant une mise en ligne ou une livraison, ou quand vous dites « pause » : Claude s'arrête, relit ce qui a été fait, relance les preuves, cherche les erreurs et les oublis, corrige, puis repart. | `circe:recul` ; points écrits dans `.circe/recul/` |
| **Nos outils** | Les outils que nous avons créés, servis avec votre clé, lancés sur votre ordinateur puis effacés : le **Quai** (analyser un paquet npm, PyPI ou GitHub AVANT de l'installer : provenance, intégrité, licence, code suspect, verdict VERT, ORANGE ou ROUGE), le **vérificateur de mouvement** (une page) et le **contrôle de sécurité public** (e-mails, site, mentions). Et un **catalogue des intégrations** : pour ce que vous voulez faire, ce qu'il faut installer, depuis où, sous quelle licence ; rien ne s'installe sans votre accord. | `scripts/outil.py` ; `/circe:integrations`, `/circe:systeme` |
| **Sortie** | Un livrable validé par vous part vers vos automatisations (n8n, Make, Zapier, votre outil), qui le publient. | `circe:sortie` ; fiches dans `.circe/sorties/` |

Une fois installé, écrivez d'abord **« configure CIRCÉ »** : il fait l'inventaire de votre poste, vous demande votre but et adapte son circuit. Ensuite, donnez simplement le sujet de votre demande. `/circe` présente tous ses organes.

À chaque démarrage, CIRCÉ charge aussi ses **12 règles de conduite**, tirées de mois de travail réel avec Claude : lire la demande à la lettre, donner un avis franc avant de produire, suivre le plan ligne par ligne et cocher chaque ligne avec sa preuve, ne rien inventer, préférer moins à plus, répondre court. Elles sont dans `scripts/regles.md`.

## Prérequis
- Claude Code (en ligne de commande), avec votre propre abonnement Claude, adapté à votre usage (professionnel ou personnel).
- Python 3.9 ou plus récent, accessible par `python3`, `python` ou `py`. Sans Python, le système immunitaire et la mémoire sont **inactifs**.
- Git pour Windows n'est pas nécessaire : les réflexes de CIRCÉ se lancent sans shell.
- Une connexion Internet pour recevoir la méthode détaillée (hors ligne, un résumé s'applique).
- Pour la vidéo : ffmpeg. Pour regarder des sites en exemple : Chrome ou Edge.

## Installation
1. Décompressez l'archive reçue, par exemple dans `C:\CIRCE\` ou `~/circe/`.
2. Dans un terminal :
   ```
   claude plugin marketplace add <dossier décompressé>
   claude plugin install circe@circe-cdow
   ```
3. Ouvrez Claude Code, tapez `/plugin configure circe@circe-cdow` et collez votre clé (dans l'e-mail reçu après l'abonnement) au réglage « licence ». Claude Code la garde dans son coffre sécurisé. Redémarrez Claude Code.
4. Écrivez « configure CIRCÉ » : Claude fait l'inventaire de votre poste, vous demande votre but et adapte son circuit. Puis donnez votre premier sujet.

Gardez le dossier décompressé : Claude Code lit CIRCÉ directement depuis lui.
Mise à jour : remplacez le dossier par la nouvelle version reçue, puis lancez `claude plugin marketplace update circe-cdow`.
Essai sans installer (une session seulement) : `claude --plugin-dir <dossier>/circe`.

## Vos autorisations sont respectées
CIRCÉ s'installe sur votre Claude Code tel qu'il est : il lit les autorisations que vous avez déjà données (règles « allow » de vos réglages Claude Code, personnels et du projet, et le mode bypassPermissions) et **ne vous redemande jamais ce que vous avez déjà autorisé**. Exemple : si les réponses de Claude dans votre messagerie sont autorisées, CIRCÉ les laisse passer.
- CIRCÉ **ne touche jamais** à vos réglages : il ne les écrit pas, ne les range pas, ne retire rien. Si vous activez la protection « réglages de Claude Code », toute modification par Claude demande votre accord.
- Pour qu'un geste ne soit plus demandé : autorisez-le dans Claude Code (`/permissions`, règle « allow » avec le nom exact de l'outil, écrit dans la demande d'accord et dans `.circe/journal-immunitaire.jsonl`).
- Seuls les gestes irréversibles restent refusés quoi qu'il arrive : formatage d'un disque, suppression de la racine, du dossier personnel ou d'un lecteur entier, écriture dans un dossier du système.
- « configure CIRCÉ » vous montre les autorisations déjà en place.

## Ce qui sort de votre ordinateur
Vers nous, jamais vos fichiers ni vos exemples. Comme pour tout usage de Claude Code, ce que Claude lit pour travailler est envoyé à Anthropic, qui le traite selon ses propres conditions ; CIRCÉ n'y change rien. Côté CIRCÉ, trois envois seulement : la vérification de la licence (une fois par 24 heures au plus, la clé et l'identifiant du produit vers `api.gumroad.com`), la méthode (le serveur `circe-cerveau` reçoit la clé, le nom du parcours, la version et la langue) et nos outils (il reçoit la clé, le nom de l'outil et la version du plugin). Le Quai, lui, télécharge l'outil que vous lui demandez d'analyser depuis son registre public (npm, PyPI, GitHub), sans l'installer ni l'exécuter. La sortie vers vos automatisations n'envoie qu'à l'adresse que vous avez branchée : une fiche du livrable (titre, légende, réseau visé, nom du projet, chemins et tailles des fichiers), et le contenu des fichiers seulement si vous le demandez (option « joindre »).
Votre code, votre mémoire de projet et vos journaux restent dans le dossier du projet (`.circe/`). L'empreinte du PC est un condensé anonyme : on ne peut en retrouver ni le nom ni l'adresse matérielle.

## Abonnement et licence
- Abonnement actif : tous les organes sont actifs, avec les mises à jour et les nouveaux organes chaque mois.
- Abonnement arrêté, remboursé, ou clé activée sur plus de 3 PC : CIRCÉ passe **en veille**. La méthode et la mémoire se mettent en pause, et les protections que vous avez choisies restent actives pour vous protéger.
- Hors ligne : CIRCÉ reste actif 7 jours après la dernière vérification réussie.
- Licence d'utilisation : `LICENCE.txt`.

## Limites, dites franchement
- Le système immunitaire filtre le **texte** des commandes. Ce n'est pas un bac à sable : il arrête l'erreur et le geste évident, et ne remplace ni les permissions de Claude Code ni vos sauvegardes.
- La méthode détaillée est servie par notre serveur et marquée au nom de l'abonné ; les réflexes restent des fichiers lisibles. CIRCÉ n'est pas incopiable, et nous ne le prétendons pas.
- CIRCÉ aide Claude à mieux travailler. Il ne le rend pas infaillible : relisez ce qui compte.

## Aide
Page de CIRCÉ : https://cdow.fr/circe. Versions : `CHANGELOG.md`.
