"""Minimalny klient OKX V5 dla konta DEMO (Demo Trading, spot).

Każde zapytanie ma nagłówek `x-simulated-trading: 1`, ustawiony na sztywno.
OKX kieruje je wtedy na konto demo; klucz z prawdziwego konta zostałby odrzucony,
więc tymi kluczami nie da się handlować prawdziwymi środkami.

OKX ma osobne domeny dla regionów, a klucz działa tylko na domenie swojego konta.
Klient sam wybiera pierwszą domenę, która rozpoznaje klucz (albo tę z OKX_HOST).

Waluta rozliczeniowa: konta europejskie (MiCA) nie mają USDT, tylko USDC. Bez podanej
waluty klient wybiera USDT, a gdy na koncie go nie ma, a jest USDC, przechodzi na USDC.
Silnik nadal widzi ją pod nazwą "USDT" (ceny USDT i USDC są praktycznie równe).
"""
import base64
import hashlib
import hmac
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

HOSTS = ["https://www.okx.com", "https://my.okx.com", "https://eea.okx.com", "https://app.okx.com"]
WRONG_DOMAIN = {"50119", "50120"}  # klucz nie istnieje na tej domenie


class OKXError(Exception):
    pass


class OKXDemo:
    def __init__(self, key, secret, passphrase, host=None, quote=None):
        if not (key and secret and passphrase):
            raise OKXError("Brak kluczy API OKX demo (klucz, sekret i hasło).")
        if host and host not in HOSTS:
            raise OKXError(f"Nieznana domena OKX: {host}")
        self.key, self.secret, self.passphrase = key, secret.encode(), passphrase
        self.host = host
        self.quote = quote.upper() if quote else None
        self._filters = {}

    def inst(self, symbol):
        """BTCUSDT -> BTC-USDT albo BTC-USDC, zależnie od waluty rozliczeniowej konta."""
        if self.quote is None:
            self.balances()
        return symbol[:-4] + "-" + self.quote

    # ---------- zapytania ----------
    def _raw(self, host, method, path, params=None, signed=True):
        params = params or {}
        if method == "GET":
            query = urllib.parse.urlencode(params)
            path = path + ("?" + query if query else "")
            body, data = "", None
        else:
            body = json.dumps(params, separators=(",", ":"))
            data = body.encode()
        headers = {"User-Agent": "paper-bot", "Content-Type": "application/json", "x-simulated-trading": "1"}
        if signed:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"
            sign = base64.b64encode(hmac.new(self.secret, (ts + method + path + body).encode(), hashlib.sha256).digest()).decode()
            headers.update({"OK-ACCESS-KEY": self.key, "OK-ACCESS-SIGN": sign,
                            "OK-ACCESS-TIMESTAMP": ts, "OK-ACCESS-PASSPHRASE": self.passphrase})
        req = urllib.request.Request(host + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            try:
                return json.load(e)  # OKX zwraca kod błędu w treści także przy 4xx
            except Exception:
                if e.code == 403:
                    raise OKXError(f"HTTP 403 z OKX ({path.split('?')[0]}): OKX blokuje adres IP serwera. "
                                   "Najczęstsza przyczyna to region serwera w kraju objętym ograniczeniami (np. USA). "
                                   "Zmień region hostingu.") from None
                raise OKXError(f"HTTP {e.code} z OKX ({path.split('?')[0]})") from None

    def _call(self, method, path, params=None, signed=True):
        if self.host is None:
            self.host = self.detect_host()
        res = self._raw(self.host, method, path, params, signed)
        if res.get("code") != "0":
            detail = ""
            if res.get("data") and isinstance(res["data"], list) and isinstance(res["data"][0], dict):
                detail = res["data"][0].get("sMsg", "")
            raise OKXError(f"OKX demo: {res.get('msg') or detail or 'błąd'} (kod {res.get('code')}, {path})"
                           + (f": {detail}" if detail and res.get("msg") else ""))
        return res["data"]

    def detect_host(self):
        """Pierwsza domena, na której klucz istnieje."""
        last = None
        for h in HOSTS:
            res = self._raw(h, "GET", "/api/v5/account/balance", {"ccy": "USDT"})
            if res.get("code") == "0":
                return h
            last = res
            if res.get("code") not in WRONG_DOMAIN:
                raise OKXError(f"OKX demo: {res.get('msg')} (kod {res.get('code')}, {h})")
        raise OKXError(f"Klucz OKX demo nie działa na żadnej domenie OKX ({last.get('msg') if last else 'brak odpowiedzi'}).")

    # ---------- odczyt ----------
    def balances(self, coins=("BTC", "ETH")):
        """Salda konta demo: {"USDT": waluta rozliczeniowa, "BTC": ..., "ETH": ...}."""
        data = self._call("GET", "/api/v5/account/balance")
        all_bal = {d["ccy"]: float(d.get("cashBal") or 0) for d in (data[0].get("details", []) if data else [])}
        if self.quote is None:
            self.quote = "USDC" if all_bal.get("USDT", 0) <= 0 and all_bal.get("USDC", 0) > 0 else "USDT"
        out = {"USDT": all_bal.get(self.quote, 0.0)}
        out.update({c: all_bal.get(c, 0.0) for c in coins})
        return out

    def filters(self, symbol):
        if symbol not in self._filters:
            d = self._call("GET", "/api/v5/public/instruments", {"instType": "SPOT", "instId": self.inst(symbol)}, signed=False)[0]
            self._filters[symbol] = {"lot": float(d["lotSz"]), "min_qty": float(d["minSz"])}
        return self._filters[symbol]

    # ---------- zlecenia ----------
    @staticmethod
    def _floor(x, step):
        digits = max(0, -int(math.floor(math.log10(step) + 1e-9)))
        return f"{math.floor(x / step + 1e-9) * step:.{digits}f}"

    def market_buy(self, symbol, usd_value, price):
        """Kupno rynkowe za podaną kwotę USDT. None, gdy poniżej minimum giełdy."""
        f = self.filters(symbol)
        if usd_value < 1 or usd_value / price < f["min_qty"]:
            return None
        body = {"instId": self.inst(symbol), "tdMode": "cash", "side": "buy", "ordType": "market",
                "tgtCcy": "quote_ccy", "sz": self._floor(usd_value, 0.01)}
        return self._place(symbol, body)

    def market_sell(self, symbol, qty, price):
        """Sprzedaż rynkowa podanej ilości monety. None, gdy poniżej minimum giełdy."""
        f = self.filters(symbol)
        sz = math.floor(qty / f["lot"] + 1e-9) * f["lot"]
        if sz < f["min_qty"]:
            return None
        body = {"instId": self.inst(symbol), "tdMode": "cash", "side": "sell", "ordType": "market",
                "tgtCcy": "base_ccy", "sz": self._floor(qty, f["lot"])}
        return self._place(symbol, body)

    def _place(self, symbol, body):
        order_id = self._call("POST", "/api/v5/trade/order", body)[0]["ordId"]
        for _ in range(10):
            time.sleep(0.5)
            o = self._call("GET", "/api/v5/trade/order", {"instId": self.inst(symbol), "ordId": order_id})[0]
            if o.get("state") in ("filled", "canceled", "mmp_canceled"):
                qty, px = float(o.get("accFillSz") or 0), float(o.get("avgPx") or 0)
                # Prowizja: przy kupnie w monecie bazowej, przy sprzedaży w USDT (OKX podaje ją ze znakiem minus).
                return {"order_id": order_id, "status": o["state"], "qty": qty, "price": px,
                        "value": qty * px, "fee": abs(float(o.get("fee") or 0))}
        return {"order_id": order_id, "status": "unknown", "qty": 0.0, "price": 0.0, "value": 0.0, "fee": 0.0}
