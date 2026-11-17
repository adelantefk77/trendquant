# Bot trendowy (portfel wirtualny albo konto demo Bybit): sama biblioteka standardowa Pythona.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STATE_PATH=/data/state.json \
    PORT=8080

RUN useradd --create-home --uid 10001 bot && mkdir /data && chown bot:bot /data
WORKDIR /app
COPY --chown=bot:bot engine.py bybit.py server.py ./
COPY --chown=bot:bot static ./static

USER bot
VOLUME /data
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=3).status == 200 else 1)"

CMD ["python", "server.py"]
