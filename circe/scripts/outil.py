"""Lance un outil de CDOW servi par le serveur CIRCÉ (porte /outil), avec la clé de l'abonné.

Le code de nos outils n'est PAS dans le plugin : il est demandé au serveur au moment voulu, vérifié (empreinte sha256
et signature de CDOW, clé publique dans cle_outils.py),
écrit dans un dossier temporaire HORS du projet, lancé avec le Python de l'utilisateur, puis effacé. Sans clé valide,
rien ne tourne. Ce code est sous licence : ne pas le recopier ni le conserver (licence CIRCÉ).

  python outil.py <nom> [arguments de l'outil...]
  python outil.py quai npm:nom-du-paquet          (analyser un outil AVANT de l'installer)
Envoie au serveur EXACTEMENT : la clé (en-tête) et {nom, version_plugin}. Rien du projet.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import licence  # noqa: E402
import signature  # noqa: E402

PORTE = os.environ.get("CIRCE_PORTE_OUTIL", "https://cerveau.cdow.fr/outil")


def version_plugin() -> str:
    try:
        return json.loads((ICI.parent / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")).get("version", "")
    except (OSError, ValueError):
        return ""


def cle() -> str:
    return licence.cle_option() or str(licence.lire_etat().get("cle") or "").strip()


def demander(nom: str, ouvrir=urllib.request.urlopen) -> dict:
    corps = json.dumps({"nom": nom, "version_plugin": version_plugin()}).encode("utf-8")
    req = urllib.request.Request(PORTE, data=corps, method="POST",
                                 headers={"Content-Type": "application/json", "X-Circe-Licence": cle(),
                                          "User-Agent": "CIRCE-outil/1.0"})
    try:
        with ouvrir(req, timeout=60) as r:
            donnees = r.read(10 * 1024 * 1024 + 1)          # plafond de la réponse (relecture Codex du 24/11)
            if len(donnees) > 10 * 1024 * 1024:
                return {"erreur": "réponse du serveur trop grosse : refusée"}
            return json.loads(donnees.decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return {"erreur": json.loads(e.read(65536).decode("utf-8")).get("erreur", f"refus du serveur ({e.code})")}
        except ValueError:
            return {"erreur": f"refus du serveur ({e.code})"}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"erreur": f"serveur CIRCÉ injoignable ({e}). Nos outils demandent une connexion Internet."}


def lancer(nom: str, args: list[str], ouvrir=urllib.request.urlopen) -> int:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,39}", nom or ""):   # le nom devient un nom de fichier : rien d'autre
        print(f"CIRCÉ : nom d'outil invalide : {nom!r}")
        return 2
    if not cle():
        print("CIRCÉ : aucune clé de licence. Tapez /plugin configure circe@circe-cdow dans Claude Code, collez la clé reçue par "
              "e-mail, puis redémarrez Claude Code.")
        return 4
    rep = demander(nom, ouvrir)
    if rep.get("erreur"):
        print(f"CIRCÉ : {rep['erreur']}")
        return 4
    code = rep.get("code", "")
    corps = code[code.find("\n") + 1:]
    empreinte = hashlib.sha256(corps.encode("utf-8")).hexdigest()
    if empreinte != rep.get("sha256"):
        print("CIRCÉ : l'outil reçu ne correspond pas à son empreinte ; il n'est pas lancé.")
        return 5
    # signé par CDOW sur son PC (la clé privée n'est pas au serveur) : un serveur détourné ne peut pas faire passer un faux outil
    if rep.get("nom") != nom or not signature.valide(nom, str(rep.get("version", "")), empreinte, str(rep.get("signature", ""))):
        print("CIRCÉ : l'outil reçu n'est pas signé par CDOW ; il n'est pas lancé. Prévenez-nous : contact@cdow.fr")
        return 5
    dossier = Path(tempfile.mkdtemp(prefix="circe-outil-"))
    try:
        fichier = dossier / f"{nom}.py"
        fichier.write_text(code, encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        return subprocess.run([sys.executable, "-I", str(fichier), *args], env=env).returncode
    finally:
        shutil.rmtree(dossier, ignore_errors=True)   # rien ne reste sur le disque (licence)


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not argv or argv[0] in ("-h", "--aide"):
        print(__doc__)
        return 2
    return lancer(argv[0], argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
