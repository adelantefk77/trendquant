"""Uruchamia silnik bota w tle i serwuje panel (http://localhost:8080)."""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from engine import Bot

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
bot = Bot()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj).encode(), "application/json; charset=utf-8")

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            with open(os.path.join(STATIC, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif path == "/api/state":
            self._json(bot.snapshot())
        elif path == "/healthz":
            self._json({"ok": True})
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/api/pause":
            bot.set_paused(True)
        elif self.path == "/api/resume":
            bot.set_paused(False)
        else:
            return self._json({"error": "not found"}, 404)
        self._json({"paused": bot.state["paused"]})

    def log_message(self, *args):  # bez logu każdego odpytania panelu
        pass


if __name__ == "__main__":
    threading.Thread(target=bot.run_forever, daemon=True).start()
    port = int(os.environ.get("PORT", "8080"))
    mode = "konto demo Bybit, wirtualne środki" if bot.broker else "portfel wirtualny, bez zleceń"
    print(f"Panel: http://localhost:{port}  ({mode})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
