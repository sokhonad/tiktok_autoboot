# ── Stage 1 : Image de base Python 3.11 + dépendances système ───────────────
FROM python:3.11-slim-bookworm AS base

# Métadonnées
LABEL maintainer="tech_fr" \
      description="TikTok Autobot — pipeline vidéo automatisé"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# ── Dépendances système ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    # FFmpeg pour le montage vidéo
    ffmpeg \
    # Polices pour les overlays texte
    fonts-dejavu-core \
    fonts-liberation \
    # Dépendances Playwright Chromium
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libxtst6 \
    # Node.js 20 pour Remotion
    curl \
    ca-certificates \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Répertoire de travail ─────────────────────────────────────────────────────
WORKDIR /app

# ── Dépendances Python ────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# ── Installation Playwright Chromium ─────────────────────────────────────────
RUN playwright install chromium --with-deps

# ── Dépendances Node.js / Remotion ───────────────────────────────────────────
COPY package.json .
RUN npm install --prefer-offline

# ── Copie du code source ──────────────────────────────────────────────────────
COPY . .

# ── Création des dossiers de données ─────────────────────────────────────────
RUN mkdir -p output logs assets/backgrounds assets/music

# ── Utilisateur non-root pour la sécurité ────────────────────────────────────
RUN useradd -m -u 1000 botuser \
    && chown -R botuser:botuser /app
USER botuser

# ── Point d'entrée par défaut ─────────────────────────────────────────────────
CMD ["python", "main.py"]
