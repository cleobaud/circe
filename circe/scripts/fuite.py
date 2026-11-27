"""CIRCÉ — reconnaître la méthode servie sous licence, pour qu'elle ne sorte pas du travail en cours.

La méthode et les parcours que sert le serveur sont réservés à l'abonné : ils s'appliquent pendant le travail, ils ne
s'enregistrent pas et ne se transmettent pas. C'est écrit à chaque appel ; une consigne écrite ne suffit pas.
Ce module reconnaît le texte servi à trois signes, du plus sûr au plus faible :

1. **le filigrane** : une suite de caractères invisibles déposée dans le texte servi (elle désigne l'abonné) ;
2. **l'en-tête de licence** qui ouvre chaque réponse du serveur ;
3. **la signature de fin** (« Méthode CIRCÉ 1.x, licence … », « reproduction interdite »).

Il ne lit aucun secret, n'envoie rien, et ne sert qu'à refuser une écriture ou un envoi. Bibliothèque standard seulement.
"""
from __future__ import annotations

import re

# Caractères sans largeur : espaces de jonction, marques de direction, sélecteurs de variante, espace insécable zéro.
INVISIBLES = "​‌‍‎‏⁠⁡⁢⁣⁤﻿" + "".join(chr(c) for c in range(0xFE00, 0xFE10))
FILIGRANE = re.compile(f"[{re.escape(INVISIBLES)}]{{8,}}")
ENTETE = re.compile(r"(?i)\[\s*licence circé|consigne pour claude\]\s*ce qui suit est servi sous licence")
SIGNATURE = re.compile(r"(?i)méthode circé\s*\d+\.\d+.{0,40}licence|reproduction interdite\s*\(licence circé\)")

RAISON = ("la méthode CIRCÉ servie sous licence ne s'enregistre pas et ne s'envoie pas : elle s'applique pendant le "
          "travail, c'est tout. Écris ce que TU en fais (le résultat, tes décisions, tes contrôles) — ça, c'est à "
          "l'utilisateur et ça peut sortir.")


def detecter(texte: str) -> str | None:
    """Renvoie le signe trouvé, ou None. Le texte de l'utilisateur et le travail produit passent sans rien déclencher."""
    if not texte:
        return None
    if FILIGRANE.search(texte):
        return "filigrane de la méthode servie"
    if ENTETE.search(texte):
        return "en-tête de licence de la méthode servie"
    if SIGNATURE.search(texte):
        return "signature de fin de la méthode servie"
    return None


def dans(valeur) -> str | None:
    """Même chose sur une structure quelconque (dictionnaire, liste, texte) : utile pour une fiche de sortie."""
    if isinstance(valeur, str):
        return detecter(valeur)
    if isinstance(valeur, dict):
        for v in valeur.values():
            trouve = dans(v)
            if trouve:
                return trouve
        return None
    if isinstance(valeur, (list, tuple)):
        for v in valeur:
            trouve = dans(v)
            if trouve:
                return trouve
    return None
