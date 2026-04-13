#!/usr/bin/env bash
# install.sh — Installation complète de TikTok Autobot
# Compatible : Ubuntu 20.04, 22.04, 24.04 / Debian 11+
# Usage : sudo bash install.sh

set -euo pipefail

# ── Couleurs ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }
info() { echo -e "${BLUE}[→]${NC} $1"; }

# ── Vérifications préliminaires ───────────────────────────────────────────────
[[ "$(id -u)" -eq 0 ]] || err "Ce script doit être exécuté en root (sudo bash install.sh)"
[[ -f /etc/os-release ]] || err "Impossible de déterminer l'OS"
source /etc/os-release

INSTALL_DIR="${INSTALL_DIR:-/opt/tiktok-autobot}"
UBUNTU_VERSION="${VERSION_ID:-0}"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║        TikTok Autobot — Installation         ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
info "OS détecté     : ${PRETTY_NAME:-unknown}"
info "Version Ubuntu : $UBUNTU_VERSION"
info "Dossier        : $INSTALL_DIR"
echo ""

# ── 1. Mise à jour système ────────────────────────────────────────────────────
info "1/9 — Mise à jour des paquets système..."
apt-get update -qq
apt-get upgrade -y -qq
log "Système mis à jour"

# ── 2. Dépendances de base ────────────────────────────────────────────────────
info "2/9 — Installation des dépendances de base..."
apt-get install -y -qq \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    curl \
    wget \
    gnupg \
    git \
    unzip \
    ffmpeg \
    fonts-dejavu-core \
    fonts-liberation \
    python3-pip
log "Dépendances de base installées"

# ── 3. Python 3.11 (via deadsnakes si nécessaire) ─────────────────────────────
info "3/9 — Installation de Python 3.11..."

# Tente l'installation directe d'abord
if apt-get install -y -qq python3.11 python3.11-venv python3.11-dev 2>/dev/null; then
    log "Python 3.11 installé depuis les dépôts officiels"
else
    # Fallback : PPA deadsnakes (Ubuntu 20.04 et autres)
    warn "Python 3.11 absent des dépôts — ajout du PPA deadsnakes..."
    add-apt-repository -y ppa:deadsnakes/ppa
    apt-get update -qq
    apt-get install -y -qq python3.11 python3.11-venv python3.11-dev python3.11-distutils
    log "Python 3.11 installé via PPA deadsnakes"
fi

python3.11 --version

# ── 4. Dépendances Playwright Chromium ───────────────────────────────────────
info "4/9 — Dépendances Playwright Chromium..."

# libasound2 a été renommé libasound2t64 sur Ubuntu 24.04+
LIBASOUND="libasound2"
if [[ "$(echo "$UBUNTU_VERSION >= 24.04" | bc -l 2>/dev/null || echo 0)" == "1" ]] || \
   apt-cache show libasound2t64 &>/dev/null 2>&1; then
    LIBASOUND="libasound2t64"
    warn "Ubuntu 24.04+ détecté — utilisation de libasound2t64"
fi

apt-get install -y -qq \
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
    "$LIBASOUND" \
    libxtst6 \
    fonts-noto 2>/dev/null || warn "Certains paquets Chromium déjà présents, on continue..."

log "Dépendances Playwright installées"

# ── 5. Node.js 20 ─────────────────────────────────────────────────────────────
info "5/9 — Installation de Node.js 20..."
if ! command -v node &>/dev/null || [[ $(node -v | cut -d. -f1 | tr -d 'v') -lt 20 ]]; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y -qq nodejs
    log "Node.js $(node -v) installé"
else
    log "Node.js $(node -v) déjà présent"
fi

# ── 6. Copie / positionnement du projet ──────────────────────────────────────
info "6/9 — Positionnement du projet dans $INSTALL_DIR..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$SCRIPT_DIR" != "$INSTALL_DIR" ]]; then
    if [[ ! -d "$INSTALL_DIR" ]]; then
        cp -r "$SCRIPT_DIR" "$INSTALL_DIR"
        log "Projet copié vers $INSTALL_DIR"
    else
        warn "Dossier $INSTALL_DIR existant — mise à jour des fichiers Python uniquement"
        cp "$SCRIPT_DIR"/*.py "$INSTALL_DIR/" 2>/dev/null || true
        cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/" 2>/dev/null || true
    fi
else
    log "Projet déjà dans $INSTALL_DIR"
fi

cd "$INSTALL_DIR"
mkdir -p output logs assets/backgrounds assets/music

# ── 7. Environnement Python virtuel + dépendances ────────────────────────────
info "7/9 — Création venv Python 3.11 + installation des paquets..."
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel -q
pip install -r requirements.txt -q
log "Venv Python 3.11 et dépendances installés"

# ── Playwright Chromium ───────────────────────────────────────────────────────
info "    Installation Playwright Chromium..."
playwright install chromium --with-deps
log "Playwright Chromium installé"

# ── 8. Dépendances Node.js / Remotion ─────────────────────────────────────────
info "8/9 — Dépendances Node.js (Remotion)..."
npm install --silent
log "Dépendances Node.js installées"

# ── 9. Systemd ────────────────────────────────────────────────────────────────
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

# Installe et active les units systemd
cp tiktok-bot.service /etc/systemd/system/
cp tiktok-bot.timer   /etc/systemd/system/
sed -i "s|/opt/tiktok-autobot|$INSTALL_DIR|g" /etc/systemd/system/tiktok-bot.service
systemctl daemon-reload
systemctl enable tiktok-bot.timer
log "Timer systemd activé (00h/03h/06h/09h/12h/15h/18h/21h)"

# ── Fichier .env ──────────────────────────────────────────────────────────────
if [[ ! -f "$INSTALL_DIR/.env" ]]; then
    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
    warn "IMPORTANT : Édite $INSTALL_DIR/.env avec tes clés API !"
fi

# ── Résumé ────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║           Installation terminée !            ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
python3.11 --version
node -v
ffmpeg -version 2>&1 | head -1
echo ""
echo -e "${YELLOW}Étapes suivantes :${NC}"
echo ""
echo "  1. Remplis tes clés API :"
echo -e "     ${BLUE}nano $INSTALL_DIR/.env${NC}"
echo ""
echo "  2. Exporte tes cookies TikTok :"
echo -e "     ${BLUE}# Sur ton PC : extension Cookie-Editor → Export JSON"
echo -e "     scp cookies.json user@VPS:$INSTALL_DIR/cookies.json${NC}"
echo ""
echo "  3. Teste manuellement :"
echo -e "     ${BLUE}cd $INSTALL_DIR && source venv/bin/activate"
echo -e "     python main.py --topic 'Docker en 60 secondes'${NC}"
echo ""
echo "  4. Lance le timer automatique :"
echo -e "     ${BLUE}sudo systemctl start tiktok-bot.timer"
echo -e "     systemctl list-timers tiktok-bot.timer${NC}"
echo ""
echo "  5. Logs en temps réel :"
echo -e "     ${BLUE}journalctl -fu tiktok-bot.service${NC}"
echo ""
