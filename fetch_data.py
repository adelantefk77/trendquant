"""Pobiera dzienne świece spot (UTC) z publicznego API Binance do data/<SYMBOL>.csv.

Nie wymaga klucza API. Bieżąca, niezamknięta świeca jest pomijana.
"""
import csv
import json
import os
import time
import urllib.request

BASE = "https://data-api.binance.vision/api/v3/klines"
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
START_MS = 1502928000000  # 2017-08-17, początek notowań BTCUSDT
DAY_MS = 86_400_000


def fetch(symbol):
    rows, start = [], START_MS
    now_ms = int(time.time() * 1000)
    while True:
        url = f"{BASE}?symbol={symbol}&interval=1d&startTime={start}&limit=1000"
        with urllib.request.urlopen(url, timeout=30) as r:
            batch = json.load(r)
        if not batch:
            break
        rows.extend(batch)
        start = batch[-1][0] + DAY_MS
        if len(batch) < 1000:
            break
        time.sleep(0.2)
    # tylko zamknięte świece
    return [k for k in rows if k[6] < now_ms]


def main():
    os.makedirs("data", exist_ok=True)
    for sym in SYMBOLS:
        rows = fetch(sym)
        path = os.path.join("data", f"{sym}.csv")
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["date", "open", "high", "low", "close", "volume"])
            for k in rows:
                d = time.strftime("%Y-%m-%d", time.gmtime(k[0] / 1000))
                w.writerow([d, k[1], k[2], k[3], k[4], k[5]])
        print(f"{sym}: {len(rows)} świec, {path}")


if __name__ == "__main__":
    main()
