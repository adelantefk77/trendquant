# TrendQuant

Bot trendowy na spot BTC i ETH (long/flat, bez dźwigni) z panelem w przeglądarce.

## Strategia

Raz na dobę, po zamknięciu dnia UTC, bot sprawdza dla każdej monety, czy cena jest powyżej
średnich kroczących z 50, 100 i 200 dni. Każda średnia daje jeden głos: 3/3 to pełna pozycja,
0/3 to sprzedaż wszystkiego. Wielkość pozycji maleje, gdy rośnie zmienność z ostatnich 60 dni
(do 40% portfela na monetę, 80% łącznie). Reszta zostaje w gotówce. Przy spadku portfela o 15%
od szczytu panel pokazuje alarm, ale bot sam nie sprzedaje.

To narzędzie badawcze, a nie porada inwestycyjna.

## Zawartość

| Ścieżka | Co to jest |
|---|---|
| `bot/` | Bot i panel (Python, bez zależności) z plikami Dockera |
| `backtest.py`, `results.md`, `chart.html` | Backtest strategii na danych 2018–2026 i jego wyniki |
| `fetch_data.py`, `data/` | Pobieranie dziennych świec BTC i ETH z Binance |
| `project/` | Projekt graficzny panelu |

## Uruchomienie

```bash
cd bot
docker compose up -d --build
```

Panel: http://localhost:8080

Z plikiem `bot/.env` (klucze konta **demo** Bybit) bot wysyła zlecenia na konto demo.
Bez niego prowadzi portfel wirtualny. Klient Bybit działa wyłącznie ze środowiskiem demo.
