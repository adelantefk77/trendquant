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

## Railway

Repozytorium jest gotowe do wdrożenia: Railway sam znajdzie `Dockerfile` i `railway.json`
w głównym katalogu. W panelu Railway trzeba ustawić:

1. **Variables:**
   - `BYBIT_DEMO_API_KEY` i `BYBIT_DEMO_API_SECRET`: klucze demo Bybit (te same co w `bot/.env`).
     Railway nie czyta `bot/.env`. Bez tych zmiennych bot prowadzi portfel wirtualny.
   - `PANEL_PASSWORD`: hasło do panelu. Przeglądarka poprosi o login (nazwa użytkownika dowolna).
     Bez hasła panel jest publiczny i tylko do odczytu.
   - opcjonalnie parametry strategii: `TARGET_VOL`, `CAP_ASSET`, `CAP_TOTAL`, `BAND`, `DD_ALERT`.
2. **Volume:** dodaj wolumen zamontowany w `/data`, żeby stan bota przetrwał kolejne wdrożenia.
3. **Region:** wybierz region w Europie (np. Amsterdam). Binance i Bybit blokują część adresów z USA.
4. **Networking:** wygeneruj publiczną domenę, żeby otworzyć panel.

Bot musi działać w jednej kopii (`numReplicas: 1` w `railway.json`), inaczej zlecenia by się dublowały.
