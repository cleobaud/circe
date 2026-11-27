---
name: securite
description: "Sécurité d'une petite entreprise française, pas à pas et avec son accord : e-mails (SPF, DKIM, DMARC), site (sauvegarde, HTTPS, protections, mises à jour), loi (mentions légales, confidentialité, cookies), comptes (double vérification, nom de domaine, règle du RIB), rapport. À utiliser quand l'utilisateur veut protéger son entreprise ou celle d'un client qui l'a mandaté, ou dit « sécurité », « DMARC », « mentions légales »."
---

# CIRCÉ — securite

1. **Avant de travailler, appelle l'outil MCP `circe_methode` avec `parcours: "securite"`** (serveur `circe-cerveau`) et suis la méthode qu'il renvoie, du début à la fin.
2. Si l'outil répond que CIRCÉ est en veille, dis-le à l'utilisateur tel quel, sans contourner.
3. Si le serveur ne répond pas (hors ligne), dis-le, puis applique ce résumé minimal :

> Protéger une petite entreprise pas à pas, avec l'accord du gérant à chaque modification : contrôles et bilan public d'abord (rien n'est sondé ni forcé), puis e-mails, site, loi, comptes, rapport ; jamais de mot de passe lu ni tapé ; s'arrêter dès que ce n'est plus à toi.

La méthode détaillée est la propriété de CDOW ; elle n'est pas recopiée dans les fichiers du projet.

## Le contrôle public de niveau 1 (outil de CDOW, servi avec la clé)
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/outil.py" securite <domaine> [autres domaines]
```
Seulement ce que tout visiteur voit : DNS public (SPF, DMARC, DKIM), réponse du site, en-têtes, certificat, mentions légales, traceurs. Rien n'est sondé ni forcé ; aller plus loin (niveau 2) demande l'accord écrit du gérant.
