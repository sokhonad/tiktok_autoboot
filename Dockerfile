# ── Image de base Python 3.11 slim ───────────────────────────────────────────
FROM python:3.11-slim-bookworm

LABEL maintainer="tech_fr" \
      description="TikTok Autobot — pipeline vidéo automatisé"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# ── Dépendances système ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Scheduler interne au conteneur
    cron \
    # FFmpeg
    ffmpeg \
    # Polices
    fonts-dejavu-core \
    fonts-liberation \
    # Playwright Chromium
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libxcb1 libxkbcommon0 \
    libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 \
    libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 libxtst6 \
    # Node.js 20
    curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Dépendances Python ────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install "setuptools<70" wheel \
    && pip install -r requirements.txt

# ── Playwright Chromium ───────────────────────────────────────────────────────
RUN playwright install chromium --with-deps

# ── Dépendances Node.js / Remotion ───────────────────────────────────────────
COPY package.json .
RUN npm install --prefer-offline

# ── Code source ───────────────────────────────────────────────────────────────
COPY . .

# ── Dossiers de données ───────────────────────────────────────────────────────
RUN mkdir -p output logs assets/backgrounds assets/music

# ── Crontab : toutes les 3h (00h 03h 06h 09h 12h 15h 18h 21h) ───────────────
RUN echo "0 0,3,6,9,12,15,18,21 * * * root cd /app && python main.py >> /app/logs/cron.log 2>&1" \
    > /etc/cron.d/tiktok-autobot \
    && chmod 0644 /etc/cron.d/tiktok-autobot \
    && crontab /etc/cron.d/tiktok-autobot

# ── Entrypoint : démarre cron en foreground ───────────────────────────────────
CMD ["cron", "-f"]
