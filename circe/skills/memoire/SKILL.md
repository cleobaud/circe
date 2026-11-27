---
name: memoire
description: Retenir ce qui compte pour la suite du projet dans la mémoire CIRCÉ (décision, préférence de l'utilisateur, erreur et sa correction, leçon, fait vérifié). À utiliser quand l'utilisateur tranche, corrige, exprime une préférence durable, ou quand une erreur a été trouvée et corrigée.
---

# Mémoire : ce qui se retient, et comment

## Quand noter
| Type | Quand | Exemple |
|---|---|---|
| `decision` | l'utilisateur tranche un choix | « on garde la police Inter, pas de serif » |
| `preference` | une préférence durable | « jamais de bouton pilule ; fond blanc » |
| `erreur` | une erreur trouvée | « le rendu sortait noir : caméra hors de la scène » |
| `lecon` | ce qu'on fera autrement | « toujours un rendu argile avant les matières » |
| `fait` | un fait vérifié utile plus tard | « l'hébergeur est Cloudflare Pages, projet x » |
| `suite` | une chose promise à faire | « ajouter le formulaire de devis après validation » |

## Comment
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/memoire.py" noter <type> "<texte court et précis>"
```
- Les mots exacts de l'utilisateur quand c'est une décision ou une préférence (entre guillemets).
- Jamais de secret, de mot de passe ni de donnée personnelle sensible dans la mémoire.
- Une note fausse se corrige par une nouvelle note qui la remplace (« remplace la note du ... : ... »).

La mémoire reste dans le dossier du projet (`.circe/`). Rien ne sort de l'ordinateur.
