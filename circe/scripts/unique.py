"""CIRCÉ — lecture de l'entrée d'un réflexe, une seule fois par événement.

Pourquoi : sous Windows sans Git Bash, Claude Code lance les réflexes par PowerShell, qui ne comprend pas
« python3 … || python … ». Les réflexes sont donc déclarés en forme exécutable (sans shell), une fois par
interprète possible (python3, python, py -3). Selon le PC, un, deux ou trois de ces lancements réussissent,
en parallèle et avec la même entrée. Le premier qui crée le jeton de cet événement fait le travail ; les
autres se taisent. En cas de doute (dossier illisible), on traite : mieux vaut deux fois que zéro.
"""
from __future__ import annotations

import hashlib
import os
import random
import sys
import time
from pathlib import Path

FENETRE_S = 10          # deux lancements d'un même événement démarrent à quelques millisecondes d'écart
VERROU_S = 5            # un verrou de renouvellement plus vieux appartient à un lancement mort : il est repris
VIE_JETON_S = 3600


def _dossier() -> Path:
    d = Path.home() / ".circe" / "tours"
    d.mkdir(parents=True, exist_ok=True)
    return d


def nettoyer(maintenant: float | None = None) -> int:
    t = maintenant if maintenant is not None else time.time()
    n = 0
    try:
        for f in _dossier().iterdir():
            try:
                if t - f.stat().st_mtime > VIE_JETON_S:
                    f.unlink()
                    n += 1
            except OSError:
                pass
    except OSError:
        pass
    return n


def _creer(chemin: Path, t: float) -> bool:
    fd = os.open(chemin, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.write(fd, repr(t).encode())
    finally:
        os.close(fd)
    return True


def _date_jeton(chemin: Path) -> float:
    try:
        return float(chemin.read_text(encoding="ascii") or 0)
    except (OSError, ValueError):
        return chemin.stat().st_mtime


def premier(brut: str, nom: str, maintenant: float | None = None) -> bool:
    """True si ce lancement est le premier pour cet événement (il doit traiter), False s'il doit se taire.
    Fenêtre GLISSANTE (relecture Codex du 24/11) : un jeton de moins de 10 s veut dire « déjà traité » ; un jeton plus
    ancien appartient à un événement identique passé (même entrée, tour suivant) : il est remplacé et l'événement traité."""
    t = maintenant if maintenant is not None else time.time()
    chemin = _dossier() / hashlib.sha256(f"{nom}|{brut}".encode("utf-8", "replace")).hexdigest()[:32]
    try:
        _creer(chemin, t)
    except FileExistsError:
        try:
            if t - _date_jeton(chemin) < FENETRE_S:
                return False
        except OSError:
            return True
        return _renouveler(chemin, t)   # jeton d'un événement passé : un seul lancement le renouvelle
    except OSError:
        return True
    if random.random() < 0.01:
        nettoyer(t)
    return True


def _renouveler(chemin: Path, t: float) -> bool:
    """Relecture Codex du 25/11 (0.5) : avant, deux lancements pouvaient lire le même jeton périmé, l'un l'effaçait et le recréait,
    l'autre effaçait ce NOUVEAU jeton et traitait aussi l'événement. Maintenant : un verrou exclusif (repris s'il a plus de 5 s,
    lancement mort), puis la date est relue SOUS le verrou ; le jeton est remplacé d'un bloc (os.replace)."""
    verrou = chemin.with_name(chemin.name + ".verrou")
    try:
        _creer(verrou, t)
    except FileExistsError:
        try:
            if t - _date_jeton(verrou) < VERROU_S:
                return False               # un autre lancement renouvelle en ce moment
            os.remove(verrou)
            _creer(verrou, t)
        except OSError:
            return False
    except OSError:
        return True
    try:
        if t - _date_jeton(chemin) < FENETRE_S:
            return False                   # déjà renouvelé par un autre lancement
        tmp = chemin.with_name(f"{chemin.name}.{os.getpid()}.{random.randrange(1 << 30)}")
        tmp.write_text(repr(t), encoding="ascii")
        os.replace(tmp, chemin)
    except OSError:
        return True
    finally:
        try:
            os.remove(verrou)
        except OSError:
            pass
    if random.random() < 0.01:
        nettoyer(t)
    return True


def lire(nom: str) -> str | None:
    """Lit l'entrée du réflexe (UTF-8, sans BOM). None = un autre lancement traite déjà cet événement."""
    tampon = getattr(sys.stdin, "buffer", None)
    if sys.stdin is None or (hasattr(sys.stdin, "isatty") and sys.stdin.isatty()):
        brut = ""
    else:
        brut = tampon.read().decode("utf-8", "replace") if tampon is not None else sys.stdin.read()
    brut = brut.replace("﻿", "").strip()
    return brut if premier(brut, nom) else None
