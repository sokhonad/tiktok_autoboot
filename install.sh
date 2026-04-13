#!/usr/bin/env bash
# install.sh — Installation complète de TikTok Autobot sur Ubuntu 22.04+
# Usage : sudo bash install.sh
# Ce script installe toutes les dépendances système et Python.

set -euo pipefail

# ── Couleurs ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }
info() { echo -e "${BLUE}[→]${NC} $1"; }

# ── Vérifications préliminaires ───────────────────────────────────────────────
[[ "$(id -u)" -eq 0 ]] || err "Ce script doit être exécuté en root (sudo bash install.sh)"
[[ -f /etc/os-release ]] || err "Impossible de déterminer l'OS"
source /etc/os-release
[[ "$ID" == "ubuntu" || "$ID_LIKE" == *"debian"* ]] || warn "OS non-Ubuntu détecté, continuons..."

INSTALL_DIR="${INSTALL_DIR:-/opt/tiktok-autobot}"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║        TikTok Autobot — Installation         ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
info "Dossier d'installation : $INSTALL_DIR"
echo ""

# ── 1. Mise à jour système ────────────────────────────────────────────────────
info "1/9 — Mise à jour des paquets système..."
apt-get update -qq
apt-get upgrade -y -qq
log "Système mis à jour"

# ── 2. Dépendances système ────────────────────────────────────────────────────
info "2/9 — Installation des dépendances système..."
apt-get install -y -qq \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    ffmpeg \
    git \
    curl \
    wget \
    ca-certificates \
    gnupg \
    unzip \
    fonts-dejavu-core \
    fonts-liberation \
    fonts-noto \
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
    libxtst6

log "Dépendances système installées"

# ── 3. Node.js 20 ─────────────────────────────────────────────────────────────
info "3/9 — Installation de Node.js 20..."
if ! command -v node &>/dev/null || [[ $(node -v | cut -d. -f1 | tr -d 'v') -lt 20 ]]; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y -qq nodejs
    log "Node.js $(node -v) installé"
else
    log "Node.js $(node -v) déjà présent"
fi

# ── 4. Copie du projet ────────────────────────────────────────────────────────
info "4/9 — Copie du projet vers $INSTALL_DIR..."
if [[ ! -d "$INSTALL_DIR" ]]; then
    cp -r "$(dirname "$0")" "$INSTALL_DIR"
    log "Projet copié vers $INSTALL_DIR"
else
    warn "Dossier $INSTALL_DIR existant — mise à jour des fichiers Python uniquement"
    cp "$(dirname "$0")"/*.py "$INSTALL_DIR/" 2>/dev/null || true
fi

cd "$INSTALL_DIR"

# ── 5. Environnement Python virtuel ───────────────────────────────────────────
info "5/9 — Création de l'environnement Python virtuel..."
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel -q
log "Venv Python 3.11 créé"

# ── 6. Dépendances Python ─────────────────────────────────────────────────────
info "6/9 — Installation des dépendances Python..."
pip install -r requirements.txt -q
log "Dépendances Python installées"

# ── 7. Playwright Chromium ────────────────────────────────────────────────────
info "7/9 — Installation de Playwright Chromium..."
playwright install chromium --with-deps
log "Playwright Chromium installé"

# ── 8. Dépendances Node.js / Remotion ─────────────────────────────────────────
info "8/9 — Installation des dépendances Node.js (Remotion)..."
npm install --prefer-offline --silent
log "Dépendances Node.js installées"

# ── 9. Configuration systemd ──────────────────────────────────────────────────
info "9/9 — Configuration systemd (timer toutes les 3h)..."

# Crée l'utilisateur dédié s'il n'existe pas
if ! id "tiktokbot" &>/dev/null; then
    useradd -r -s /bin/bash -d "$INSTALL_DIR" tiktokbot
    log "Utilisateur 'tiktokbot' créé"
fi

# Permissions
chown -R tiktokbot:tiktokbot "$INSTALL_DIR"
chmod 750 "$INSTALL_DIR"
chmod 700 "$INSTALL_DIR/output" "$INSTALL_DIR/logs" 2>/dev/null || true

# Installe les fichiers systemd
cp tiktok-bot.service /etc/systemd/system/
cp tiktok-bot.timer /etc/systemd/system/

# Adapte le chemin dans le service
sed -i "s|/opt/tiktok-autobot|$INSTALL_DIR|g" /etc/systemd/system/tiktok-bot.service

systemctl daemon-reload
systemctl enable tiktok-bot.timer
log "Timer systemd activé"

# ── Fichier .env ──────────────────────────────────────────────────────────────
if [[ ! -f "$INSTALL_DIR/.env" ]]; then
    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
    warn "IMPORTANT : Édite $INSTALL_DIR/.env avec tes clés API avant de démarrer !"
fi

# ── Résumé ────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║           Installation terminée !            ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo -e "${YELLOW}Étapes suivantes :${NC}"
echo ""
echo "  1. Édite le fichier .env :"
echo -e "     ${BLUE}nano $INSTALL_DIR/.env${NC}"
echo ""
echo "  2. Exporte tes cookies TikTok dans :"
echo -e "     ${BLUE}$INSTALL_DIR/cookies.json${NC}"
echo "     (utilise l'extension 'Cookie-Editor' sur Chrome/Firefox)"
echo ""
echo "  3. Teste le bot manuellement :"
echo -e "     ${BLUE}cd $INSTALL_DIR && source venv/bin/activate && python main.py --topic 'test'${NC}"
echo ""
echo "  4. Démarre le timer systemd :"
echo -e "     ${BLUE}sudo systemctl start tiktok-bot.timer${NC}"
echo ""
echo "  5. Vérifie les prochains déclenchements :"
echo -e "     ${BLUE}sudo systemctl list-timers tiktok-bot.timer${NC}"
echo ""
echo "  6. Suivi des logs en temps réel :"
echo -e "     ${BLUE}journalctl -fu tiktok-bot.service${NC}"
echo ""
