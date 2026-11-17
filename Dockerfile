# TrendQuant: bot trendowy (portfel wirtualny albo konto demo Bybit) z panelem.
# Sama biblioteka standardowa Pythona, bez zależności. Kontekst budowania: główny katalog repozytorium.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STATE_PATH=/data/state.json \
    PORT=8080

RUN useradd --create-home --uid 10001 bot && mkdir /data && chown bot:bot /data
WORKDIR /app
COPY bot/engine.py bot/bybit.py bot/okx.py bot/server.py ./
COPY bot/static ./static

# Start jako root tylko po to, żeby oddać wolumen /data użytkownikowi bot;
# server.py od razu potem przełącza się na tego użytkownika.
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import os,urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:%s/healthz' % os.environ.get('PORT','8080'), timeout=3).status == 200 else 1)"

CMD ["python", "server.py"]
