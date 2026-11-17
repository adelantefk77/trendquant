"""Silnik handlu na papierze: trend long/flat na spocie BTC i ETH.

Te same reguły co w backtest.py:
  - sygnał z zamkniętej świecy dziennej (UTC): głosy SMA 50/100/200
  - wielkość: głosy/3 * min(limit_na_aktywo, docelowa_zmienność / zmienność_60d)
  - wykonanie po cenie otwarcia następnej świecy, z kosztem na stronę
  - zmiana głosów -> handel; korekta wielkości tylko w poniedziałki poza pasmem

Bot NIE składa prawdziwych zleceń i nie używa kluczy API. Korzysta tylko
z publicznych danych rynkowych i prowadzi wirtualny portfel w pliku stanu.
"""
import json
import math
import os
import statistics
import threading
import time
import urllib.request
from datetime import datetime, timezone

from bybit import BybitDemo, BybitError
from okx import OKXDemo, OKXError

BrokerError = (BybitError, OKXError)

API = os.environ.get("MARKET_API", "https://data-api.binance.vision/api/v3/klines")
ASSETS = ["BTCUSDT", "ETHUSDT"]
MAS = (50, 100, 200)
VOL_WIN = 60
ANN = 365
DAY_MS = 86_400_000


def env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return float(default)


CFG = {
    "initial_cash": env_float("INITIAL_CASH", 10000),
    "target_vol": env_float("TARGET_VOL", 0.10),
    "cap_asset": env_float("CAP_ASSET", 0.40),
    "cap_total": env_float("CAP_TOTAL", 0.80),
    "band": env_float("BAND", 0.05),
    "cost": env_float("COST", 0.0015),
    "dd_alert": env_float("DD_ALERT", 0.15),
    "poll_seconds": env_float("POLL_SECONDS", 60),
    "start_date": os.environ.get("START_DATE", "").strip(),  # RRRR-MM-DD: odtwórz historię od tej daty
    "mas": list(MAS),
    "vol_win": VOL_WIN,
}
BYBIT_KEY = os.environ.get("BYBIT_DEMO_API_KEY", "").strip()
BYBIT_SECRET = os.environ.get("BYBIT_DEMO_API_SECRET", "").strip()
OKX_KEY = os.environ.get("OKX_DEMO_API_KEY", "").strip()
OKX_SECRET = os.environ.get("OKX_DEMO_API_SECRET", "").strip()
OKX_PASSPHRASE = os.environ.get("OKX_DEMO_PASSPHRASE", "").strip()
OKX_HOST = os.environ.get("OKX_HOST", "").strip() or None
OKX_QUOTE = os.environ.get("OKX_QUOTE", "").strip() or None  # USDT albo USDC; puste = automatycznie
# Z kluczami demo bot wysyła zlecenia na konto demo Bybit; bez nich prowadzi portfel wirtualny.
# Wybór giełdy: zmienna BROKER (okx_demo, bybit_demo, paper) albo automatycznie według podanych kluczy.
_auto = ("okx_demo" if OKX_KEY and OKX_SECRET and OKX_PASSPHRASE
         else "bybit_demo" if BYBIT_KEY and BYBIT_SECRET else "paper")
CFG["broker"] = os.environ.get("BROKER", "").strip() or _auto
VENUE = {"okx_demo": "OKX", "bybit_demo": "Bybit"}.get(CFG["broker"])
COIN = {"BTCUSDT": "BTC", "ETHUSDT": "ETH"}
STATE_PATH = os.environ.get("STATE_PATH", "/data/state.json")


def day(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def iso_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_klines(symbol, limit=1000):
    url = f"{API}?symbol={symbol}&interval=1d&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "paper-bot"})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = json.load(r)
    return [{"t": k[0], "date": day(k[0]), "open": float(k[1]), "close": float(k[4]), "close_t": k[6]} for k in raw]


def indicators(closes, j):
    """Wskaźniki na zamknięciu świecy j (bez danych z przyszłości)."""
    if j + 1 < max(MAS) or j < VOL_WIN:
        return None
    smas = {m: sum(closes[j - m + 1:j + 1]) / m for m in MAS}
    votes = sum(1 for m in MAS if closes[j] > smas[m])
    rets = [math.log(closes[i] / closes[i - 1]) for i in range(j - VOL_WIN + 1, j + 1)]
    vol = statistics.stdev(rets) * math.sqrt(ANN)
    return {"smas": smas, "votes": votes, "vol": vol}


def target_weights(inds):
    w = {a: (i["votes"] / len(MAS)) * min(CFG["cap_asset"], CFG["target_vol"] / i["vol"]) for a, i in inds.items()}
    tot = sum(w.values())
    if tot > CFG["cap_total"]:
        w = {a: x * CFG["cap_total"] / tot for a, x in w.items()}
    return w


class Bot:
    def __init__(self):
        self.lock = threading.RLock()
        self.market = None          # ostatnie pobrane dane rynkowe
        self.status = {"data_ok": False, "message": "Uruchamianie", "updated_at": None, "last_error": None}
        if CFG["broker"] == "okx_demo":
            self.broker = OKXDemo(OKX_KEY, OKX_SECRET, OKX_PASSPHRASE, host=OKX_HOST, quote=OKX_QUOTE)
        elif CFG["broker"] == "bybit_demo":
            self.broker = BybitDemo(BYBIT_KEY, BYBIT_SECRET)
        else:
            self.broker = None
        self.state = self._load()

    # ---------- stan ----------
    def _fresh(self):
        return {
            "version": 1,
            "broker": CFG["broker"],
            "initial_equity": None if CFG["broker"] != "paper" else CFG["initial_cash"],
            "created_at": iso_now(),
            "cash": CFG["initial_cash"],
            "units": {a: 0.0 for a in ASSETS},
            "last_votes": {a: 0 for a in ASSETS},
            "last_signal_date": None,   # data ostatniej przetworzonej świecy sygnałowej
            "peak_equity": CFG["initial_cash"],
            "alert_active": False,
            "paused": False,
            "trades": [],
            "equity_history": [],
            "events": [],
            "fees_paid": 0.0,
        }

    def _load(self):
        try:
            with open(STATE_PATH) as f:
                st = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self._fresh()
        if st.get("broker", "paper") != CFG["broker"]:
            # zmiana trybu (portfel wirtualny <-> konto demo): stary stan zostaje jako kopia
            os.replace(STATE_PATH, f"{STATE_PATH}.{st.get('broker', 'paper')}.bak")
            return self._fresh()
        st.setdefault("initial_equity", CFG["initial_cash"])
        return st

    def _quote(self):
        return getattr(self.broker, "quote", None) or "USDT"

    @staticmethod
    def _amt(x, sign=False):
        """Kwota z odstępem tysięcy, np. 566 475.83."""
        return (f"{x:+,.2f}" if sign else f"{x:,.2f}").replace(",", " ")

    def _sync_account(self, prices, own_trade=False):
        """Tryb konta demo: gotówka i pozycje pochodzą z prawdziwych sald konta demo giełdy.

        Zmiana sald, której nie wywołało zlecenie bota (wpłata, wypłata, ręczna transakcja,
        reset konta demo), przesuwa punkt startowy i szczyt o swoją wartość. Dzięki temu
        wynik i obsunięcie pokazują tylko efekt strategii.
        """
        s = self.state
        old_cash, old_units = s["cash"], dict(s["units"])
        bal = self.broker.balances()
        s["cash"] = bal["USDT"]
        for a in ASSETS:
            s["units"][a] = bal[COIN[a]]
        eq = s["cash"] + sum(s["units"][a] * prices[a] for a in ASSETS)
        if s["initial_equity"] is None:
            s["initial_equity"] = s["peak_equity"] = eq
            self._event("info", f"Połączono z kontem demo {VENUE}. Kapitał na starcie: {self._amt(eq)} {self._quote()}.")
            return
        if own_trade:
            return
        flow = (s["cash"] - old_cash) + sum((s["units"][a] - old_units.get(a, 0.0)) * prices[a] for a in ASSETS)
        if abs(flow) > max(1.0, 1e-5 * eq):  # pomija zaokrąglenia giełdy
            s["initial_equity"] += flow
            s["peak_equity"] = max(s["peak_equity"] + flow, eq)
            s["flows_total"] = s.get("flows_total", 0.0) + flow
            kind = "Wpłata lub zakup spoza bota" if flow > 0 else "Wypłata, sprzedaż spoza bota albo reset konta demo"
            self._event("info", f"{kind}: {self._amt(flow, sign=True)} {self._quote()}. Punkt startowy przesunięty "
                                f"o tę kwotę, więc nie wpływa na wynik strategii.")

    def rebase(self):
        """Ustawia obecny kapitał jako nowy punkt startowy i szczyt (przycisk w panelu)."""
        with self.lock:
            s, kl = self.state, self.market
            if not kl:
                return False
            prices = {a: kl[a][-1]["close"] for a in ASSETS}
            eq = s["cash"] + sum(s["units"][a] * prices[a] for a in ASSETS)
            s["initial_equity"] = s["peak_equity"] = eq
            s["alert_active"] = False
            s["flows_total"] = 0.0
            self._event("info", f"Operator ustawił nowy punkt startowy: {self._amt(eq)} {self._quote()}.")
            self._save()
            return True

    def _fill(self, a, delta, price, sell_all):
        """Wykonuje zmianę pozycji. Zwraca (ilość, cena, wartość, koszt w USDT) albo None."""
        s = self.state
        if self.broker is None:
            fee = abs(delta) * CFG["cost"]
            s["units"][a] += delta / price
            if abs(s["units"][a]) < 1e-12:
                s["units"][a] = 0.0
            s["cash"] -= delta + fee
            return abs(delta) / price, price, abs(delta), fee
        if delta > 0:
            f = self.broker.market_buy(a, delta, price)
        else:
            f = self.broker.market_sell(a, s["units"][a] if sell_all else abs(delta) / price, price)
        if f is None:
            return None
        if f["qty"] <= 0:
            raise BrokerError[0](f"Zlecenie {a} nie zostało wypełnione (status {f['status']}).")
        # prowizja spot: przy kupnie w monecie, przy sprzedaży w USDT
        fee = f["fee"] * f["price"] if delta > 0 else f["fee"]
        return f["qty"], f["price"], f["value"], fee

    def _save(self):
        os.makedirs(os.path.dirname(STATE_PATH) or ".", exist_ok=True)
        tmp = STATE_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.state, f)
        os.replace(tmp, STATE_PATH)

    def _event(self, kind, text):
        self.state["events"].append({"ts": iso_now(), "kind": kind, "text": text})
        self.state["events"] = self.state["events"][-200:]

    # ---------- logika ----------
    def _process(self, kl, j, replay):
        """Sygnał ze świecy j, wykonanie po otwarciu świecy j+1."""
        s = self.state
        inds = {a: indicators([k["close"] for k in kl[a]], j) for a in ASSETS}
        if any(v is None for v in inds.values()):
            return
        tgt = target_weights(inds)
        opens = {a: kl[a][j + 1]["open"] for a in ASSETS}
        # Bieżąca świeca: jeśli bot rusza długo po północy UTC, cena otwarcia jest już
        # nieosiągalna, więc wirtualne zlecenie wypełnia się po cenie bieżącej.
        live = self.broker is not None
        late = live or (not replay and time.time() * 1000 - kl[ASSETS[0]][j + 1]["t"] > 10 * 60_000)
        if late:
            opens = {a: kl[a][j + 1]["close"] for a in ASSETS}
        exec_date = kl[ASSETS[0]][j + 1]["date"]
        eq_open = s["cash"] + sum(s["units"][a] * opens[a] for a in ASSETS)
        monday = datetime.strptime(exec_date, "%Y-%m-%d").weekday() == 0
        plan = []
        for a in ASSETS:
            w_cur = s["units"][a] * opens[a] / eq_open
            votes = inds[a]["votes"]
            vote_change = votes != s["last_votes"][a]
            resize = monday and abs(tgt[a] - w_cur) > CFG["band"]
            if vote_change or resize:
                plan.append((a, tgt[a] * eq_open - s["units"][a] * opens[a], w_cur, votes, vote_change))
        plan.sort(key=lambda x: x[1])  # najpierw sprzedaże, żeby zwolnić gotówkę
        for a, delta, w_cur, votes, vote_change in plan:
            prev_votes = s["last_votes"][a]
            if abs(delta) < 1e-6 * eq_open:
                s["last_votes"][a] = votes
                continue
            try:
                fill = self._fill(a, delta, opens[a], sell_all=(tgt[a] == 0))
            except BrokerError as e:
                self._event("alert", f"Zlecenie {a} na {VENUE} demo nie powiodło się: {e}")
                if live:
                    # zlecenie mogło się częściowo wypełnić: zapisz salda jako efekt bota, nie wpłatę
                    try:
                        self._sync_account(opens, own_trade=True)
                    except BrokerError:
                        pass
                raise
            s["last_votes"][a] = votes
            if fill is None:
                self._event("info", f"Pominięto zlecenie {a}: poniżej minimum giełdy.")
                continue
            qty, price, notional, fee = fill
            s["fees_paid"] += fee
            if vote_change:
                reason = f"Zmiana głosów {prev_votes}/3 → {votes}/3"
            else:
                reason = f"Tygodniowa korekta wielkości (odchylenie {abs(tgt[a] - w_cur) * 100:.1f} pp)"
            s["trades"].append({
                "date": exec_date, "signal_date": kl[a][j]["date"], "symbol": a,
                "side": "KUPNO" if delta > 0 else "SPRZEDAŻ",
                "qty": qty, "price": price, "notional": notional, "fee": fee,
                "w_from": w_cur, "w_to": tgt[a], "votes_from": prev_votes, "votes_to": votes,
                "reason": reason, "replay": replay, "late": late and not live, "venue": CFG["broker"],
            })
            if live:
                self._sync_account(opens, own_trade=True)
        s["trades"] = s["trades"][-500:]
        s["last_signal_date"] = kl[ASSETS[0]][j]["date"]
        eq = s["cash"] + sum(s["units"][a] * opens[a] for a in ASSETS)
        s["equity_history"].append({"date": exec_date, "equity": eq, "replay": replay})
        s["equity_history"] = s["equity_history"][-2000:]
        self._track_drawdown(eq)

    def _track_drawdown(self, eq):
        s = self.state
        s["peak_equity"] = max(s["peak_equity"], eq)
        dd = eq / s["peak_equity"] - 1
        breached = dd <= -CFG["dd_alert"]
        if breached and not s["alert_active"]:
            self._event("alert", f"Obsunięcie {dd * 100:.1f}% przekroczyło próg alarmu {CFG['dd_alert'] * 100:.0f}%. Wymagany przegląd.")
        if not breached and s["alert_active"]:
            self._event("info", "Obsunięcie wróciło powyżej progu alarmu.")
        s["alert_active"] = breached

    def tick(self):
        """Jedno przejście: pobierz dane, przetwórz nowe zamknięte świece, wyceń portfel."""
        try:
            kl = {a: fetch_klines(a) for a in ASSETS}
        except Exception as e:  # sieć lub API
            with self.lock:
                self.status.update(data_ok=False, message="Brak danych rynkowych. Handel wstrzymany.", last_error=str(e)[:200])
            return
        now_ms = int(time.time() * 1000)
        with self.lock:
            s = self.state
            dates = [k["date"] for k in kl[ASSETS[0]]]
            aligned = all([k["date"] for k in kl[a]] == dates for a in ASSETS)
            n_closed = sum(1 for k in kl[ASSETS[0]] if k["close_t"] < now_ms)
            last_closed = n_closed - 1
            fresh = n_closed > 0 and now_ms - kl[ASSETS[0]][last_closed]["close_t"] < DAY_MS + 15 * 60_000
            has_forming = len(dates) > n_closed
            data_ok = aligned and fresh and has_forming
            self.market = kl
            if not data_ok:
                self.status.update(data_ok=False, updated_at=iso_now(), last_error=None,
                                   message="Dane nieaktualne lub niespójne. Handel wstrzymany.")
                return
            # od której świecy zacząć
            if s["last_signal_date"] is None:
                if CFG["start_date"] and CFG["start_date"] in dates:
                    first = max(dates.index(CFG["start_date"]) - 1, max(MAS) - 1)
                    self._event("info", f"Odtwarzanie historii od {dates[first + 1]} (tryb symulacji wstecznej).")
                else:
                    first = last_closed
                    self._event("info", f"Start bota na koncie demo {VENUE}." if self.broker else "Start portfela papierowego.")
            elif s["last_signal_date"] in dates:
                first = dates.index(s["last_signal_date"]) + 1
            else:
                first = last_closed
            prices = {a: kl[a][-1]["close"] for a in ASSETS}
            try:
                if self.broker is not None:
                    self._sync_account(prices)
                    first = max(first, last_closed)  # na koncie demo nie da się handlować wstecz
                if s["paused"]:
                    # wstrzymany bot pomija sygnały; po wznowieniu rusza od bieżącej świecy
                    if last_closed >= first:
                        s["last_signal_date"] = dates[last_closed]
                else:
                    for j in range(first, last_closed + 1):
                        self._process(kl, j, replay=(j < last_closed))
            except BrokerError as e:
                self._save()
                self.status.update(data_ok=False, updated_at=iso_now(), last_error=str(e)[:200],
                                   message=f"Problem z kontem demo {VENUE}. Bot ponowi próbę.")
                return
            eq = s["cash"] + sum(s["units"][a] * prices[a] for a in ASSETS)
            self._track_drawdown(eq)
            self._save()
            self.status.update(data_ok=True, updated_at=iso_now(), last_error=None,
                               message="Wstrzymany przez operatora" if s["paused"] else "Monitorowanie dziennego zamknięcia UTC")

    def run_forever(self):
        while True:
            try:
                self.tick()
            except Exception as e:  # nie pozwól, żeby błąd zatrzymał pętlę
                with self.lock:
                    self.status.update(data_ok=False, message="Błąd silnika. Handel wstrzymany.", last_error=str(e)[:200])
            time.sleep(CFG["poll_seconds"])

    def set_paused(self, paused):
        with self.lock:
            if self.state["paused"] != paused:
                self.state["paused"] = paused
                self._event("info", "Bot wstrzymany przez operatora." if paused else "Bot wznowiony przez operatora.")
                self._save()

    # ---------- widok dla panelu ----------
    def snapshot(self):
        with self.lock:
            s, kl = self.state, self.market
            out = {"config": CFG, "status": dict(self.status), "paused": s["paused"], "mode": CFG["broker"], "quote": getattr(self.broker, "quote", None) or "USDT",
                   "alert_active": s["alert_active"], "created_at": s["created_at"],
                   "last_signal_date": s["last_signal_date"], "server_time": iso_now(),
                   "trades": list(reversed(s["trades"][-60:])), "events": list(reversed(s["events"][-20:])),
                   "equity_history": s["equity_history"][-800:], "assets": [], "portfolio": None}
            if not kl:
                return out
            now_ms = int(time.time() * 1000)
            n_closed = sum(1 for k in kl[ASSETS[0]] if k["close_t"] < now_ms)
            j = n_closed - 1
            prices = {a: kl[a][-1]["close"] for a in ASSETS}
            eq = s["cash"] + sum(s["units"][a] * prices[a] for a in ASSETS)
            inds = {a: indicators([k["close"] for k in kl[a]], j) for a in ASSETS}
            tgt = target_weights(inds) if all(inds.values()) else {a: 0.0 for a in ASSETS}
            for a in ASSETS:
                closes = [k["close"] for k in kl[a]]
                span = range(max(j - 119, max(MAS) - 1), j + 1)
                hist = [{"date": kl[a][i]["date"], "close": closes[i],
                         **{f"sma{m}": sum(closes[i - m + 1:i + 1]) / m for m in MAS}} for i in span]
                ind = inds[a]
                out["assets"].append({
                    "symbol": a, "price": prices[a], "prev_close": closes[j],
                    "change_24h": prices[a] / closes[j] - 1 if closes[j] else 0.0,
                    "signal_close": closes[j], "signal_date": kl[a][j]["date"],
                    "smas": ind["smas"] if ind else None, "votes": ind["votes"] if ind else None,
                    "vol": ind["vol"] if ind else None, "target_w": tgt[a],
                    "current_w": s["units"][a] * prices[a] / eq if eq else 0.0,
                    "units": s["units"][a], "value": s["units"][a] * prices[a], "history": hist,
                })
            invested = sum(s["units"][a] * prices[a] for a in ASSETS)
            initial = s.get("initial_equity") or eq
            next_close = kl[ASSETS[0]][-1]["close_t"] + 1
            out["portfolio"] = {
                "equity": eq, "cash": s["cash"], "invested": invested, "exposure": invested / eq if eq else 0.0,
                "initial": initial, "pnl": eq - initial, "pnl_pct": eq / initial - 1,
                "peak": s["peak_equity"], "drawdown": eq / s["peak_equity"] - 1, "fees_paid": s["fees_paid"],
                "flows_total": s.get("flows_total", 0.0),
                "trade_count": len(s["trades"]), "next_eval_ms": next_close,
            }
            return out
