"""CIRCÉ — Licence d'abonnement (clé Gumroad), vérifiée au démarrage, avec un cache et une grâce hors ligne.

  python licence.py activer <CLÉ>     active CIRCÉ sur ce PC (compte une activation chez Gumroad)
  python licence.py etat               affiche l'état (actif, veille, non configuré) sans appeler le réseau
  python licence.py verifier           revérifie si la dernière vérification date de plus de 24 h (aucune activation comptée)
  python licence.py oublier            retire la clé de ce PC

État local : `~/.circe/licence.json` (la clé, une empreinte anonyme du PC, la date de la dernière vérification réussie).
La clé n'est jamais écrite dans un journal ni affichée en entier.
Hors ligne : CIRCÉ reste actif 7 jours après la dernière vérification réussie, puis passe en veille jusqu'à la prochaine connexion.
Veille : le système immunitaire reste actif (il protège l'utilisateur) ; la mémoire et la méthode se mettent en pause.
LIMITE ASSUMÉE : ce contrôle se contourne en modifiant les fichiers locaux. Il empêche l'usage ordinaire d'une clé arrêtée
ou partagée, il ne rend pas CIRCÉ incopiable. Bibliothèque standard seulement.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

ICI = Path(__file__).resolve().parent
URL_VERIFICATION = "https://api.gumroad.com/v2/licenses/verify"
INTERVALLE_S = 24 * 3600
GRACE_S = 7 * 24 * 3600
MAX_ACTIVATIONS = 3
DELAI_RESEAU_S = 5


def config() -> dict:
    try:
        return json.loads((ICI / "config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def fichier_etat() -> Path:
    d = Path.home() / ".circe"
    d.mkdir(exist_ok=True)
    return d / "licence.json"


def lire_etat() -> dict:
    try:
        return json.loads(fichier_etat().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def ecrire_etat(etat: dict) -> None:
    fichier_etat().write_text(json.dumps(etat, ensure_ascii=False, indent=1), encoding="utf-8")


def empreinte() -> str:
    """Condensé anonyme du PC : on ne peut pas en retrouver le nom ni l'adresse matérielle."""
    brut = f"circe|{platform.node()}|{uuid.getnode()}|{platform.machine()}|{platform.system()}"
    return hashlib.sha256(brut.encode("utf-8")).hexdigest()[:16]


def masquer(cle: str) -> str:
    return (cle[:4] + "…" + cle[-4:]) if len(cle) > 10 else "…"


def appeler_gumroad(produit: str, cle: str, compter: bool, ouvrir=urllib.request.urlopen) -> dict:
    donnees = urllib.parse.urlencode({"product_id": produit, "license_key": cle,
                                      "increment_uses_count": "true" if compter else "false"}).encode()
    requete = urllib.request.Request(URL_VERIFICATION, data=donnees, method="POST",
                                     headers={"User-Agent": "circe-licence/0.3"})
    try:
        with ouvrir(requete, timeout=DELAI_RESEAU_S) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:  # Gumroad répond 404 avec success=false pour une clé inconnue
        try:
            return json.loads(e.read().decode("utf-8"))
        except ValueError:
            return {"success": False, "message": f"HTTP {e.code}"}


def juger(reponse: dict) -> tuple[str, str]:
    """(etat, raison) d'après la réponse de Gumroad. Noms de champs du « purchase » : INFÉRÉ, à confirmer sur une vraie vente."""
    if not reponse.get("success"):
        return "invalide", str(reponse.get("message") or "clé refusée par Gumroad")
    achat = reponse.get("purchase") or {}
    for champ, raison in (("refunded", "achat remboursé"), ("chargebacked", "paiement contesté"), ("disputed", "paiement contesté")):
        if achat.get(champ):
            return "veille", raison
    for champ, raison in (("subscription_ended_at", "abonnement terminé"), ("subscription_failed_at", "paiement de l'abonnement refusé")):
        if achat.get(champ):
            return "veille", raison
    if int(reponse.get("uses") or 0) > MAX_ACTIVATIONS:
        return "veille", f"clé activée sur plus de {MAX_ACTIVATIONS} PC : écrivez-nous pour la remettre à zéro"
    return "actif", "abonnement actif"


def activer(cle: str, ouvrir=urllib.request.urlopen, maintenant: float | None = None) -> dict:
    produit = config().get("gumroad_product_id")
    if not produit:
        raise SystemExit("licence non configurée dans ce paquet (config.json) : rien à activer")
    cle = cle.strip()
    etat_local = lire_etat()
    deja_ici = etat_local.get("cle") == cle and etat_local.get("empreinte") == empreinte()
    reponse = appeler_gumroad(produit, cle, compter=not deja_ici, ouvrir=ouvrir)
    etat, raison = juger(reponse)
    if etat == "invalide":
        raise SystemExit(f"activation refusée : {raison}")
    t = maintenant if maintenant is not None else time.time()
    nouvel = {"cle": cle, "empreinte": empreinte(), "etat": etat, "raison": raison, "verifie_le": t, "derniere_reussite": t}
    ecrire_etat(nouvel)
    return nouvel


def cle_option() -> str:
    """Clé saisie à l'installation du plugin (réglage « licence », gardé par Claude Code dans son coffre sécurisé)."""
    return os.environ.get("CLAUDE_PLUGIN_OPTION_LICENCE", "").strip()


def verifier(ouvrir=urllib.request.urlopen, maintenant: float | None = None, forcer: bool = False) -> dict:
    """État courant ; appelle Gumroad au plus une fois par 24 h ; ne compte jamais d'activation,
    sauf la première fois qu'une clé saisie à l'installation est vue sur ce PC (activation automatique)."""
    t = maintenant if maintenant is not None else time.time()
    produit = config().get("gumroad_product_id")
    if not produit:
        return {"etat": "non_configure", "raison": "licence non configurée (version de démonstration ou de développement)"}
    etat = lire_etat()
    option = cle_option()
    if option and (etat.get("cle") != option or etat.get("empreinte") != empreinte()):
        try:
            return activer(option, ouvrir=ouvrir, maintenant=t)
        except SystemExit as refus:
            return {"etat": "veille", "raison": str(refus)}
        except (urllib.error.URLError, OSError, ValueError, TimeoutError):
            return {"etat": "veille", "raison": "activation impossible pour le moment (hors ligne) : elle se refera au prochain démarrage"}
    if not etat.get("cle"):
        return {"etat": "veille", "raison": "aucune clé : tapez /plugin configure circe@circe-cdow dans Claude Code, collez la clé, puis redémarrez Claude Code"}
    if etat.get("empreinte") != empreinte():
        return {"etat": "veille", "raison": "clé activée sur un autre PC : relancez l'activation sur celui-ci"}
    if not forcer and t - float(etat.get("verifie_le") or 0) < INTERVALLE_S:
        return etat
    try:
        reponse = appeler_gumroad(produit, etat["cle"], compter=False, ouvrir=ouvrir)
        nouvel_etat, raison = juger(reponse)
        etat.update({"etat": "veille" if nouvel_etat == "invalide" else nouvel_etat, "raison": raison, "verifie_le": t})
        if nouvel_etat == "actif":
            etat["derniere_reussite"] = t
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        etat["verifie_le"] = t
        if t - float(etat.get("derniere_reussite") or 0) > GRACE_S:
            etat.update({"etat": "veille", "raison": "pas de vérification réussie depuis 7 jours (hors ligne)"})
        else:
            etat["raison"] = "hors ligne : grâce de 7 jours en cours"
    ecrire_etat(etat)
    return etat


def etat_rapide(maintenant: float | None = None) -> str:
    """État SANS réseau, pour les réflexes appelés à chaque message (exemples, preuve) : « actif », « veille » ou « non_configure ».
    Même règle que verifier() : sans clé, sur un autre PC, ou sans vérification réussie depuis la grâce, c'est la veille."""
    if not config().get("gumroad_product_id"):
        return "non_configure"
    etat = lire_etat()
    if not etat.get("cle") or etat.get("empreinte") != empreinte():
        return "veille"
    t = maintenant if maintenant is not None else time.time()
    if t - float(etat.get("derniere_reussite") or 0) > GRACE_S:
        return "veille"
    return "actif" if etat.get("etat") == "actif" else "veille"


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not argv:
        print(__doc__)
        return 0
    commande = argv[0]
    if commande == "activer" and len(argv) == 2:
        etat = activer(argv[1])
        print(f"CIRCÉ : {etat['etat']} ({etat['raison']}) ; clé {masquer(etat['cle'])} sur ce PC.")
    elif commande == "etat":
        etat = lire_etat()
        cfg = "configurée" if config().get("gumroad_product_id") else "non configurée"
        print(f"CIRCÉ : licence {cfg} ; état {etat.get('etat', 'aucun')} ({etat.get('raison', '-')}) ; clé {masquer(etat.get('cle', ''))}")
    elif commande == "verifier":
        etat = verifier(forcer=True)
        print(f"CIRCÉ : {etat.get('etat')} ({etat.get('raison')})")
    elif commande == "oublier":
        if fichier_etat().exists():
            fichier_etat().unlink()
        print("CIRCÉ : clé retirée de ce PC.")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
