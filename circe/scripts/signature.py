"""Vérifie la signature de CDOW sur un outil servi (RSA PKCS#1 v1.5 + SHA-256), en bibliothèque standard seulement.

Ce qui est signé : « CIRCE-OUTIL-1 », le nom, la version et l'empreinte sha256 du code, une ligne chacun. La clé publique est
dans cle_outils.py ; la clé privée reste sur le PC de CDOW (ni dans le plugin, ni au serveur).
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac

import cle_outils

# en-tête DER de DigestInfo pour SHA-256 (RFC 8017, section 9.2, note 1)
_SHA256_DIGESTINFO = bytes.fromhex("3031300d060960864801650304020105000420")


def message(nom: str, version: str, empreinte: str) -> bytes:
    return f"{cle_outils.ENTETE}\n{nom}\n{version}\n{empreinte}".encode("utf-8")


def valide(nom: str, version: str, empreinte: str, signature_b64: str, n: int | None = None, e: int | None = None) -> bool:
    n = cle_outils.N if n is None else n
    e = cle_outils.E if e is None else e
    k = (n.bit_length() + 7) // 8
    try:
        s = base64.b64decode(signature_b64 or "", validate=True)
    except (binascii.Error, ValueError):
        return False
    if len(s) != k:
        return False
    entier = int.from_bytes(s, "big")
    if entier >= n:
        return False
    em = pow(entier, e, n).to_bytes(k, "big")
    t = _SHA256_DIGESTINFO + hashlib.sha256(message(nom, version, empreinte)).digest()
    if k < len(t) + 11:
        return False
    attendu = b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t
    return hmac.compare_digest(em, attendu)
