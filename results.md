# Wyniki backtestu: trend long/flat na BTC i ETH (spot)

Okres: 2018-03-05 – 2026-11-15 (8.7 roku). Koszt: 0,15% na stronę. Dane: dzienne świece Binance, UTC. Gotówka bez odsetek.

## Cały okres

| Wariant | CAGR | Zmienność | Sharpe | Maks. obsunięcie | Dni z obsunięciem >15% | Śr. ekspozycja | Transakcje | Koszty łącznie |
|---|---|---|---|---|---|---|---|---|
| Trend ostrożny (10% zmienności) |   16.4% |  14.2% |  1.14 |  -16.8% |    3% |   18% | 674 | 15.0% kapitału pocz. |
| Trend agresywny (40% zmienności) |   30.2% |  30.6% |  1.02 |  -37.2% |   63% |   37% | 660 | 59.4% kapitału pocz. |
| Trend bez skalowania (50/50) |   40.3% |  43.2% |  1.00 |  -48.2% |   74% |   52% | 661 | 143.4% kapitału pocz. |
| Sama SMA200 bez skalowania (50/50) |   30.1% |  46.4% |  0.80 |  -61.8% |   81% |   52% | 152 | 50.4% kapitału pocz. |
| Kup i trzymaj 50/50 |   17.1% |  66.4% |  0.58 |  -81.0% |   82% | 100% | 2 | – |
| Miesięczne DCA 50/50 |   16.0% |  47.8% |  0.55 |  -70.3% |   53% | rośnie do 100% | – | – |

## Zwroty roczne

| Rok | Trend ostrożny (10% zmienności) | Trend agresywny (40% zmienności) | Trend bez skalowania (50/50) | Sama SMA200 bez skalowania (50/50) | Kup i trzymaj 50/50 |
|---|---|---|---|---|---|
| 2018 |   -6.8% |  -20.2% |  -30.0% |  -39.1% |  -76.0% |
| 2019 |   22.2% |   39.8% |   54.5% |   32.4% |   63.5% |
| 2020 |   53.7% |  126.3% |  204.3% |  155.9% |  334.4% |
| 2021 |   30.4% |  101.3% |  140.0% |  100.7% |  145.6% |
| 2022 |   -8.8% |  -20.6% |  -28.5% |   -8.2% |  -65.9% |
| 2023 |   35.0% |   52.6% |   78.7% |   73.1% |  123.8% |
| 2024 |   25.0% |   37.4% |   52.1% |   64.9% |   90.0% |
| 2025 |    3.0% |   14.0% |   18.8% |   -7.2% |   -7.8% |
| 2026 |    3.4% |    3.4% |    4.5% |   -1.5% |  -29.4% |

## Okres kontrolny (ostatnie 18 miesięcy, od 2025-05-16)

Reguły nie były strojone na żadnym okresie, więc to tylko wycinek tej samej symulacji.

| Wariant | CAGR | Zmienność | Sharpe | Maks. obsunięcie | Dni z obsunięciem >15% |
|---|---|---|---|---|---|
| Trend ostrożny (10% zmienności) |    4.9% |  11.9% |  0.46 |  -12.6% |    0% |
| Trend agresywny (40% zmienności) |   10.5% |  20.0% |  0.60 |  -19.2% |   49% |
| Trend bez skalowania (50/50) |   14.0% |  28.2% |  0.60 |  -26.5% |   59% |
| Sama SMA200 bez skalowania (50/50) |    4.4% |  29.5% |  0.29 |  -28.8% |   68% |
| Kup i trzymaj 50/50 |  -24.6% |  46.2% | -0.38 |  -57.5% |   69% |

## Wrażliwość na koszty (trend ostrożny i bez skalowania)

| Koszt na stronę | Ostrożny: CAGR | Ostrożny: Sharpe | Bez skalowania: CAGR | Bez skalowania: Sharpe |
|---|---|---|---|---|
| 0.00% | 17.2% | 1.19 | 43.0% | 1.05 |
| 0.15% | 16.4% | 1.14 | 40.3% | 1.00 |
| 0.30% | 15.6% | 1.09 | 37.6% | 0.96 |
| 0.45% | 14.8% | 1.04 | 35.2% | 0.92 |
| 1.00% | 12.0% | 0.87 | 26.0% | 0.75 |

## Stabilność parametrów (trend bez skalowania, koszt 0,15%)

Jeśli wynik zależy od dokładnych długości średnich, to jest dopasowany do historii.

| Średnie | Okno zmienności | CAGR | Sharpe | Maks. obsunięcie |
|---|---|---|---|---|
| 30/60/120 | – | 45.4% | 1.10 | -48.1% |
| 40/80/160 | – | 42.1% | 1.03 | -49.9% |
| 50/100/200 | – | 40.3% | 1.00 | -48.2% |
| 60/120/240 | – | 42.7% | 1.03 | -51.5% |
| 75/150/300 | – | 41.1% | 1.00 | -50.3% |
| 20/50/100/200 | – | 40.3% | 1.02 | -49.0% |
| 50/100/200 (ostrożny) | 30 dni | 17.2% | 1.16 | -17.9% |
| 50/100/200 (ostrożny) | 60 dni | 16.4% | 1.14 | -16.8% |
| 50/100/200 (ostrożny) | 90 dni | 15.4% | 1.10 | -16.5% |

## Opóźnione wykonanie (trend bez skalowania)

Sygnał wykonany dzień później niż w regułach, żeby sprawdzić zależność od dokładnej chwili zlecenia.

| Wykonanie | CAGR | Sharpe | Maks. obsunięcie |
|---|---|---|---|
| Otwarcie następnego dnia | 40.3% | 1.00 | -48.2% |
| Otwarcie dzień później | 37.8% | 0.96 | -50.7% |

