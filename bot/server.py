"""Uruchamia silnik bota w tle i serwuje panel (http://localhost:8080).

Zmienne:
  PORT            port panelu (Railway ustawia go sam)
  PANEL_PASSWORD  hasło do panelu (logowanie HTTP Basic, nazwa użytkownika dowolna).
                  Bez hasła panel jest otwarty; na Railway jest wtedy tylko do odczytu.
"""
import base64
import hmac
import json
import os
import pwd
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
PASSWORD = os.environ.get("PANEL_PASSWORD", "")
ON_RAILWAY = bool(os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("RAILWAY_ENVIRONMENT_NAME"))
# Na publicznym hostingu przyciski sterujące działają tylko za hasłem.
CONTROLS = bool(PASSWORD) or not ON_RAILWAY
bot = None


def drop_privileges():
    """Kontener startuje jako root tylko po to, żeby oddać wolumen /data użytkownikowi bot.

    Wolumeny Railway są montowane jako root; bez tego bot nie zapisałby stanu.
    """
    if os.getuid() != 0:
        return
    user = pwd.getpwnam("bot")
    data_dir = os.path.dirname(os.environ.get("STATE_PATH", "/data/state.json"))
    os.makedirs(data_dir, exist_ok=True)
    os.chown(data_dir, user.pw_uid, user.pw_gid)
    for root, dirs, files in os.walk(data_dir):
        for name in dirs + files:
            os.chown(os.path.join(root, name), user.pw_uid, user.pw_gid)
    os.setgroups([])
    os.setgid(user.pw_gid)
    os.setuid(user.pw_uid)
    os.environ["HOME"] = user.pw_dir


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj).encode(), "application/json; charset=utf-8")

    def _authorized(self):
        if not PASSWORD:
            return True
        header = self.headers.get("Authorization", "")
        if header.startswith("Basic "):
            try:
                given = base64.b64decode(header[6:]).decode("utf-8").split(":", 1)[1]
            except (ValueError, IndexError, UnicodeDecodeError):
                return False
            return hmac.compare_digest(given.encode(), PASSWORD.encode())
        return False

    def _challenge(self):
        self._send(401, b'{"error": "unauthorized"}', "application/json; charset=utf-8",
                   {"WWW-Authenticate": 'Basic realm="TrendQuant", charset="UTF-8"'})

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/healthz":  # sprawdzanie stanu przez Railway działa bez hasła
            return self._json({"ok": True})
        if not self._authorized():
            return self._challenge()
        if path in ("/", "/index.html"):
            with open(os.path.join(STATIC, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif path == "/api/state":
            snap = bot.snapshot()
            snap["controls_enabled"] = CONTROLS
            self._json(snap)
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        if not self._authorized():
            return self._challenge()
        if not CONTROLS:
            return self._json({"error": "Panel tylko do odczytu. Ustaw PANEL_PASSWORD."}, 403)
        if self.path == "/api/pause":
            bot.set_paused(True)
        elif self.path == "/api/resume":
            bot.set_paused(False)
        elif self.path == "/api/rebase":
            return self._json({"ok": bot.rebase()})
        else:
            return self._json({"error": "not found"}, 404)
        self._json({"paused": bot.state["paused"]})

    def log_message(self, *args):  # bez logu każdego odpytania panelu
        pass


if __name__ == "__main__":
    drop_privileges()
    from engine import Bot  # import po oddaniu uprawnień: silnik od razu czyta stan z /data

    bot = Bot()
    threading.Thread(target=bot.run_forever, daemon=True).start()
    port = int(os.environ.get("PORT", "8080"))
    from engine import VENUE
    mode = f"konto demo {VENUE}, wirtualne środki" if bot.broker else "portfel wirtualny, bez zleceń"
    access = "z hasłem" if PASSWORD else ("tylko do odczytu, brak PANEL_PASSWORD" if not CONTROLS else "bez hasła")
    print(f"Panel na porcie {port} ({mode}; panel {access})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
