"""Minimalny klient Bybit V5 dla konta DEMO (spot, konto zunifikowane).

Adres jest ustawiony na sztywno na środowisko demo. Klient odmawia pracy
z jakimkolwiek innym hostem, więc tymi kluczami nie da się handlować na
prawdziwym rynku nawet przez pomyłkę w konfiguracji.
"""
import hashlib
import hmac
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request

DEMO_HOST = "https://api-demo.bybit.com"
RECV_WINDOW = "10000"


class BybitError(Exception):
    pass


class BybitDemo:
    def __init__(self, key, secret, host=DEMO_HOST):
        if host != DEMO_HOST:
            raise BybitError("Dozwolone jest tylko środowisko demo Bybit.")
        if not key or not secret:
            raise BybitError("Brak kluczy API Bybit demo.")
        self.key, self.secret, self.host = key, secret.encode(), host
        self._filters = {}

    def _call(self, method, path, params=None, signed=True):
        params = params or {}
        ts = str(int(time.time() * 1000))
        if method == "GET":
            payload = urllib.parse.urlencode(params)
            url = self.host + path + ("?" + payload if payload else "")
            data = None
        else:
            payload = json.dumps(params, separators=(",", ":"))
            url, data = self.host + path, payload.encode()
        headers = {"User-Agent": "paper-bot", "Content-Type": "application/json"}
        if signed:
            sign = hmac.new(self.secret, (ts + self.key + RECV_WINDOW + payload).encode(), hashlib.sha256).hexdigest()
            headers.update({"X-BAPI-API-KEY": self.key, "X-BAPI-TIMESTAMP": ts,
                            "X-BAPI-RECV-WINDOW": RECV_WINDOW, "X-BAPI-SIGN": sign})
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                body = json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 403:
                raise BybitError(
                    f"HTTP 403 z Bybit demo ({path}): Bybit blokuje adres IP serwera. "
                    "Najczęstsza przyczyna to region serwera w kraju objętym ograniczeniami Bybit "
                    "(np. USA, Singapur). Zmień region hostingu."
                ) from None
            raise BybitError(f"HTTP {e.code} z Bybit demo ({path})") from None
        if body.get("retCode") != 0:
            raise BybitError(f"Bybit demo: {body.get('retMsg')} (kod {body.get('retCode')}, {path})")
        return body["result"]

    # ---------- odczyt ----------
    def key_info(self):
        return self._call("GET", "/v5/user/query-api")

    def balances(self, coins=("USDT", "BTC", "ETH")):
        """Salda portfela konta zunifikowanego: {moneta: ilość}."""
        res = self._call("GET", "/v5/account/wallet-balance", {"accountType": "UNIFIED"})
        out = {c: 0.0 for c in coins}
        for acct in res.get("list", []):
            for c in acct.get("coin", []):
                if c["coin"] in out:
                    out[c["coin"]] = float(c.get("walletBalance") or 0)
        return out

    def filters(self, symbol):
        """Kroki i minima zlecenia dla pary spot."""
        if symbol not in self._filters:
            res = self._call("GET", "/v5/market/instruments-info", {"category": "spot", "symbol": symbol}, signed=False)
            f = res["list"][0]["lotSizeFilter"]
            self._filters[symbol] = {
                "base_step": float(f["basePrecision"]), "quote_step": float(f["quotePrecision"]),
                "min_qty": float(f["minOrderQty"]), "min_amt": float(f["minOrderAmt"]),
            }
        return self._filters[symbol]

    # ---------- zlecenia ----------
    @staticmethod
    def _floor(x, step):
        digits = max(0, -int(math.floor(math.log10(step) + 1e-9)))
        return f"{math.floor(x / step + 1e-9) * step:.{digits}f}"

    def market_buy(self, symbol, usd_value, price=None):
        """Kupno rynkowe spot na demo za podaną kwotę USDT. None, gdy poniżej minimum giełdy."""
        f = self.filters(symbol)
        if usd_value < f["min_amt"]:
            return None
        body = {"category": "spot", "symbol": symbol, "orderType": "Market", "side": "Buy",
                "marketUnit": "quoteCoin", "qty": self._floor(usd_value, max(f["quote_step"], 0.01))}
        return self.wait_fill(symbol, self._call("POST", "/v5/order/create", body)["orderId"])

    def market_sell(self, symbol, qty, price):
        """Sprzedaż rynkowa spot na demo podanej ilości monety. None, gdy poniżej minimum giełdy."""
        f = self.filters(symbol)
        if qty < f["min_qty"] or qty * price < f["min_amt"]:
            return None
        body = {"category": "spot", "symbol": symbol, "orderType": "Market", "side": "Sell",
                "marketUnit": "baseCoin", "qty": self._floor(qty, f["base_step"])}
        return self.wait_fill(symbol, self._call("POST", "/v5/order/create", body)["orderId"])

    def wait_fill(self, symbol, order_id, tries=10):
        for _ in range(tries):
            time.sleep(0.5)
            for query in ("/v5/order/realtime", "/v5/order/history"):
                lst = self._call("GET", query, {"category": "spot", "symbol": symbol, "orderId": order_id}).get("list", [])
                if lst and lst[0].get("orderStatus") in ("Filled", "PartiallyFilledCanceled", "Cancelled", "Rejected"):
                    o = lst[0]
                    qty, val = float(o.get("cumExecQty") or 0), float(o.get("cumExecValue") or 0)
                    return {"order_id": order_id, "status": o["orderStatus"], "qty": qty, "value": val,
                            "price": val / qty if qty else 0.0, "fee": float(o.get("cumExecFee") or 0)}
        return {"order_id": order_id, "status": "Unknown", "qty": 0.0, "value": 0.0, "price": 0.0, "fee": 0.0}
