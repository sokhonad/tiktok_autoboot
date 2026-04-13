"""
config.py — Clés API, constantes globales et configuration du projet.
Charge les variables depuis .env via python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Charge le fichier .env depuis la racine du projet
load_dotenv(Path(__file__).parent / ".env")

# ── API Keys ────────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")  # Sarah FR par défaut

# ── Chemins fichiers ─────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
MUSIC_DIR = ASSETS_DIR / "music"
COOKIES_PATH = Path(os.getenv("TIKTOK_COOKIES_PATH", BASE_DIR / "cookies.json"))
REMOTION_DIR = BASE_DIR / "tiktok-visuals"

# ── Modèles ──────────────────────────────────────────────────────────────────
OPENAI_MODEL = "gpt-4o"                  # gpt-4o = meilleur rapport qualité/coût
WHISPER_MODEL = "base"                   # base = bon compromis vitesse/qualité
WHISPER_LANGUAGE = "fr"

# ── Vidéo ────────────────────────────────────────────────────────────────────
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
VIDEO_DURATION_MAX = 60                  # secondes, limite TikTok

# ── TTS ──────────────────────────────────────────────────────────────────────
TTS_SPEED = 1.1                          # légèrement accéléré, naturel FR
TTS_MODEL = "eleven_multilingual_v2"

# ── Pipeline ─────────────────────────────────────────────────────────────────
VIDEOS_PER_DAY = 8
RETRY_MAX = 3
RETRY_DELAY_SECONDS = 10

# ── TikTok ───────────────────────────────────────────────────────────────────
TIKTOK_UPLOAD_URL = "https://www.tiktok.com/upload"
CHANNEL_HANDLE = "@tech_fr"

# Crée les dossiers si absents au démarrage
for _d in [OUTPUT_DIR, LOGS_DIR, BACKGROUNDS_DIR, MUSIC_DIR]:
    _d.mkdir(parents=True, exist_ok=True)
