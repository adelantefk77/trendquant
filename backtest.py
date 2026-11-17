"""Backtest: podążanie za trendem long/flat na spocie BTC i ETH.

Reguły (ustalone z góry, bez strojenia):
  - sygnał: głosy trzech średnich kroczących (50/100/200 dni); głos = close > SMA
  - wielkość: głosy/3 * min(limit_na_aktywo, docelowa_zmienność / zmienność_60d)
  - sygnał liczony na zamknięciu dnia t, zlecenie wykonane po cenie otwarcia dnia t+1
  - zmiana głosów -> handel następnego dnia; korekta wielkości tylko w poniedziałki
    i tylko gdy odchylenie od celu przekracza pasmo
  - koszt: prowizja + poślizg na stronę, liczony od obrotu
Gotówka nie zarabia odsetek. Brak dźwigni.

Uruchom: python3 backtest.py   (najpierw python3 fetch_data.py)
"""
import json
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

ASSETS = ["BTCUSDT", "ETHUSDT"]
ANN = 365
HOLDOUT_START = "2025-05-16"  # ostatnie 18 miesięcy jako okres kontrolny


@dataclass(frozen=True)
class Params:
    mas: tuple = (50, 100, 200)
    vol_win: int = 60
    target_vol: float = 0.10      # docelowa zmienność roczna na aktywo
    cap_asset: float = 0.40       # maks. udział jednego aktywa
    cap_total: float = 0.80       # maks. łączna ekspozycja
    band: float = 0.05            # pasmo korekty wielkości (pp udziału)
    cost: float = 0.0015          # koszt na stronę: 0,10% prowizji + 0,05% poślizgu


def load():
    frames = {}
    for a in ASSETS:
        d = pd.read_csv(f"data/{a}.csv", parse_dates=["date"]).set_index("date")
        frames[a] = d[["open", "close"]]
    px = pd.concat(frames, axis=1).dropna()
    return px


def targets(px, p):
    """Docelowe udziały wyliczone na zamknięciu każdego dnia (bez podglądania przyszłości)."""
    close = px.xs("close", axis=1, level=1)
    votes = sum((close > close.rolling(m).mean()).astype(float) for m in p.mas) / len(p.mas)
    # dopóki najdłuższa średnia nie ma pełnej historii, sygnał nie istnieje
    votes[close.rolling(max(p.mas)).mean().isna()] = np.nan
    vol = np.log(close).diff().rolling(p.vol_win).std() * np.sqrt(ANN)
    w = votes * np.minimum(p.cap_asset, p.target_vol / vol)
    tot = w.sum(axis=1)
    scale = np.where(tot > p.cap_total, p.cap_total / tot, 1.0)
    return w.mul(scale, axis=0), votes


def simulate(px, p, start=None):
    w_tgt, votes = targets(px, p)
    opens = px.xs("open", axis=1, level=1).values
    closes = px.xs("close", axis=1, level=1).values
    wt, vt = w_tgt.values, votes.values
    n, k = closes.shape
    first = int(np.argmax(~np.isnan(wt).any(axis=1))) + 1  # pierwszy dzień handlu
    if start is not None:
        first = max(first, int(px.index.searchsorted(pd.Timestamp(start))))
    cash, units = 1.0, np.zeros(k)
    last_votes = np.zeros(k)
    equity = np.full(n, np.nan)
    expo = np.full(n, np.nan)
    trades, turnover, costs = 0, 0.0, 0.0
    for t in range(first, n):
        o = opens[t]
        eq_open = cash + units @ o
        w_cur = units * o / eq_open
        tgt, v = wt[t - 1], vt[t - 1]          # sygnał z wczorajszego zamknięcia
        monday = px.index[t].weekday() == 0
        for i in range(k):
            vote_change = v[i] != last_votes[i]
            resize = monday and abs(tgt[i] - w_cur[i]) > p.band
            if not (vote_change or resize):
                continue
            delta = tgt[i] * eq_open - units[i] * o[i]   # wartość do kupna (+) / sprzedaży (-)
            if abs(delta) < 1e-9:
                last_votes[i] = v[i]
                continue
            fee = abs(delta) * p.cost
            units[i] += delta / o[i]
            cash -= delta + fee
            trades += 1
            turnover += abs(delta) / eq_open
            costs += fee
            last_votes[i] = v[i]
        equity[t] = cash + units @ closes[t]
        expo[t] = (units @ closes[t]) / equity[t]
    eq = pd.Series(equity, index=px.index).dropna()
    return eq, pd.Series(expo, index=px.index).dropna(), dict(trades=trades, turnover=turnover, costs=costs)


def buy_and_hold(px, start, cost):
    """50/50 BTC/ETH kupione na otwarciu pierwszego dnia, bez rebalansowania."""
    opens = px.xs("open", axis=1, level=1).loc[start:]
    closes = px.xs("close", axis=1, level=1).loc[start:]
    units = (0.5 * (1 - cost)) / opens.iloc[0]
    return (closes * units).sum(axis=1)


def dca(px, start, cost):
    """Równe miesięczne zakupy 50/50 przez cały okres; niewykorzystana gotówka czeka."""
    opens = px.xs("open", axis=1, level=1).loc[start:]
    closes = px.xs("close", axis=1, level=1).loc[start:]
    months = opens.index.to_period("M")
    buy_days = ~pd.Series(months, index=opens.index).duplicated()
    n_buys = int(buy_days.sum())
    cash, units, out = 1.0, np.zeros(len(ASSETS)), []
    chunk = 1.0 / n_buys
    for d in opens.index:
        if buy_days[d]:
            units += (chunk / 2) * (1 - cost) / opens.loc[d].values
            cash -= chunk
        out.append(cash + units @ closes.loc[d].values)
    return pd.Series(out, index=opens.index)


def metrics(eq):
    r = eq.pct_change().dropna()
    years = len(r) / ANN
    cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1
    vol = r.std() * np.sqrt(ANN)
    dd = eq / eq.cummax() - 1
    return dict(
        cagr=cagr, vol=vol, sharpe=(r.mean() * ANN / vol) if vol > 0 else float("nan"),
        maxdd=dd.min(), dd15_days=float((dd < -0.15).mean()), total=eq.iloc[-1] / eq.iloc[0] - 1,
    )


def fmt_row(name, m, extra=""):
    return (f"| {name} | {m['cagr']*100:6.1f}% | {m['vol']*100:5.1f}% | {m['sharpe']:5.2f} | "
            f"{m['maxdd']*100:6.1f}% | {m['dd15_days']*100:4.0f}% |{extra}")


VARIANTS = {
    "Trend ostrożny (10% zmienności)": Params(),
    "Trend agresywny (40% zmienności)": Params(target_vol=0.40, cap_asset=0.35, cap_total=0.70),
    "Trend bez skalowania (50/50)": Params(target_vol=9.9, cap_asset=0.50, cap_total=1.00),
    "Sama SMA200 bez skalowania (50/50)": Params(mas=(200,), target_vol=9.9, cap_asset=0.50, cap_total=1.00),
}


def main():
    px = load()
    out = []
    P = out.append
    curves = {}

    runs = {name: simulate(px, p) for name, p in VARIANTS.items()}
    start = next(iter(runs.values()))[0].index[0]
    end = px.index[-1]
    bh = buy_and_hold(px, start, Params().cost)
    dc = dca(px, start, Params().cost)

    P(f"# Wyniki backtestu: trend long/flat na BTC i ETH (spot)\n")
    P(f"Okres: {start.date()} – {end.date()} ({(end - start).days / 365:.1f} roku). "
      f"Koszt: 0,15% na stronę. Dane: dzienne świece Binance, UTC. Gotówka bez odsetek.\n")

    P("## Cały okres\n")
    P("| Wariant | CAGR | Zmienność | Sharpe | Maks. obsunięcie | Dni z obsunięciem >15% | Śr. ekspozycja | Transakcje | Koszty łącznie |")
    P("|---|---|---|---|---|---|---|---|---|")
    for name, (eq, expo, st) in runs.items():
        P(fmt_row(name, metrics(eq), f" {expo.mean()*100:4.0f}% | {st['trades']} | {st['costs']*100:.1f}% kapitału pocz. |"))
        curves[name] = eq
    P(fmt_row("Kup i trzymaj 50/50", metrics(bh), " 100% | 2 | – |"))
    P(fmt_row("Miesięczne DCA 50/50", metrics(dc), " rośnie do 100% | – | – |"))
    curves["Kup i trzymaj 50/50"] = bh
    P("")

    P("## Zwroty roczne\n")
    names = list(curves)
    P("| Rok | " + " | ".join(names) + " |")
    P("|---|" + "---|" * len(names))
    yearly = {n: c.groupby(c.index.year).agg(["first", "last"]) for n, c in curves.items()}
    for y in sorted(set(bh.index.year)):
        cells = []
        for n in names:
            c = curves[n]
            prev = c[c.index.year < y]
            base = prev.iloc[-1] if len(prev) else c.iloc[0]
            cells.append(f"{(yearly[n].loc[y, 'last'] / base - 1) * 100:6.1f}%")
        P(f"| {y} | " + " | ".join(cells) + " |")
    P("")

    P(f"## Okres kontrolny (ostatnie 18 miesięcy, od {HOLDOUT_START})\n")
    P("Reguły nie były strojone na żadnym okresie, więc to tylko wycinek tej samej symulacji.\n")
    P("| Wariant | CAGR | Zmienność | Sharpe | Maks. obsunięcie | Dni z obsunięciem >15% |")
    P("|---|---|---|---|---|---|")
    for n, c in curves.items():
        P(fmt_row(n, metrics(c.loc[HOLDOUT_START:])))
    P("")

    P("## Wrażliwość na koszty (trend ostrożny i bez skalowania)\n")
    P("| Koszt na stronę | Ostrożny: CAGR | Ostrożny: Sharpe | Bez skalowania: CAGR | Bez skalowania: Sharpe |")
    P("|---|---|---|---|---|")
    for c in (0.0, 0.0015, 0.0030, 0.0045, 0.0100):
        a = metrics(simulate(px, replace(VARIANTS["Trend ostrożny (10% zmienności)"], cost=c))[0])
        b = metrics(simulate(px, replace(VARIANTS["Trend bez skalowania (50/50)"], cost=c))[0])
        P(f"| {c*100:.2f}% | {a['cagr']*100:.1f}% | {a['sharpe']:.2f} | {b['cagr']*100:.1f}% | {b['sharpe']:.2f} |")
    P("")

    P("## Stabilność parametrów (trend bez skalowania, koszt 0,15%)\n")
    P("Jeśli wynik zależy od dokładnych długości średnich, to jest dopasowany do historii.\n")
    P("| Średnie | Okno zmienności | CAGR | Sharpe | Maks. obsunięcie |")
    P("|---|---|---|---|---|")
    base = VARIANTS["Trend bez skalowania (50/50)"]
    grid = []
    for mas in ((30, 60, 120), (40, 80, 160), (50, 100, 200), (60, 120, 240), (75, 150, 300), (20, 50, 100, 200)):
        m = metrics(simulate(px, replace(base, mas=mas), start=start)[0])
        grid.append(m["sharpe"])
        P(f"| {'/'.join(map(str, mas))} | – | {m['cagr']*100:.1f}% | {m['sharpe']:.2f} | {m['maxdd']*100:.1f}% |")
    cons = VARIANTS["Trend ostrożny (10% zmienności)"]
    for vw in (30, 60, 90):
        m = metrics(simulate(px, replace(cons, vol_win=vw), start=start)[0])
        P(f"| 50/100/200 (ostrożny) | {vw} dni | {m['cagr']*100:.1f}% | {m['sharpe']:.2f} | {m['maxdd']*100:.1f}% |")
    P("")

    P("## Opóźnione wykonanie (trend bez skalowania)\n")
    P("Sygnał wykonany dzień później niż w regułach, żeby sprawdzić zależność od dokładnej chwili zlecenia.\n")
    lag = px.copy()
    lag.loc[:, (slice(None), "open")] = px.xs("open", axis=1, level=1).shift(-1).values
    m0 = metrics(simulate(px, base)[0])
    m1 = metrics(simulate(lag.dropna(), base)[0])
    P("| Wykonanie | CAGR | Sharpe | Maks. obsunięcie |")
    P("|---|---|---|---|")
    P(f"| Otwarcie następnego dnia | {m0['cagr']*100:.1f}% | {m0['sharpe']:.2f} | {m0['maxdd']*100:.1f}% |")
    P(f"| Otwarcie dzień później | {m1['cagr']*100:.1f}% | {m1['sharpe']:.2f} | {m1['maxdd']*100:.1f}% |")
    P("")

    text = "\n".join(out)
    with open("results.md", "w") as f:
        f.write(text + "\n")
    print(text)

    chart = {"dates": [d.strftime("%Y-%m-%d") for d in bh.index],
             "series": {n: [round(float(v), 5) for v in (c / c.iloc[0]).reindex(bh.index).values] for n, c in curves.items()}}
    with open("results.json", "w") as f:
        json.dump(chart, f)


if __name__ == "__main__":
    main()
