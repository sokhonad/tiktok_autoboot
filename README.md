# TikTok Autobot — Pipeline vidéo tech_fr automatisé

> Pipeline complet qui génère et publie **8 vidéos TikTok/jour** sur la niche tech FR.  
> Stack : Python 3.11 · FFmpeg · Playwright · Remotion · Whisper · Claude API · ElevenLabs

---

## Sommaire

1. [Architecture](#architecture)
2. [Prérequis](#prérequis)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Cookies TikTok](#cookies-tiktok)
6. [Lancement](#lancement)
7. [Planning éditorial](#planning-éditorial)
8. [Pipeline détaillé](#pipeline-détaillé)
9. [Remotion (animations)](#remotion-animations)
10. [Docker](#docker)
11. [Systemd timer](#systemd-timer)
12. [Commandes utiles](#commandes-utiles)
13. [Structure des sorties](#structure-des-sorties)
14. [Anti-détection](#anti-détection)
15. [Dépannage](#dépannage)

---

## Architecture

```
Cron systemd (toutes les 3h)
        │
        ▼
    main.py  ──────────────────────────────────────────────────────────────────
        │
        ├─ 1. content_strategy.py ──→  topic du jour (pool de 70+ sujets)
        │
        ├─ 2. script_generator.py ──→  Claude claude-sonnet-4-20250514
        │                              └─→ JSON { title, hook, segments[], cta, hashtags }
        │
        ├─ 3. tts.py ───────────────→  ElevenLabs multilingual v2
        │                              └─→ MP3 par segment
        │
        ├─ 4. subtitles.py ─────────→  Whisper "base" FR
        │                              └─→ subtitles.srt (timestamps précis)
        │
        ├─ 5. video_builder.py ─────→  FFmpeg
        │                              └─→ MP4 1080×1920 · fond dark · header · sous-titres
        │
        ├─ 6. metadata_randomizer.py→  FFmpeg
        │                              └─→ vitesse ±1%, brightness, EXIF aléatoires
        │
        ├─ 7. stealth_uploader.py ──→  Playwright Chromium
        │                              └─→ upload TikTok + comportement humain
        │
        └─ 8. analytics_tracker.py ─→  logs/analytics.jsonl (KPIs)
```

---

## Prérequis

| Dépendance | Version minimale | Rôle |
|---|---|---|
| Ubuntu | 22.04 LTS | OS cible (VPS/dédié) |
| Python | 3.11 | Runtime principal |
| Node.js | 20 LTS | Remotion (rendu React) |
| FFmpeg | 5.0+ | Montage vidéo |
| RAM | 4 Go | Whisper + Chromium headless |
| Disque | 10 Go | Modèles + sorties vidéo |
| Clé Anthropic | — | Génération script (Claude) |
| Clé ElevenLabs | — | Synthèse vocale FR |

---

## Installation

### Option A — Script automatique (recommandé)

```bash
# Copie le projet sur ton VPS
scp -r tiktok-autobot/ user@ton-vps:/opt/

# Connecte-toi et lance l'installation (root requis)
ssh user@ton-vps
sudo bash /opt/tiktok-autobot/install.sh
```

Le script `install.sh` effectue dans l'ordre :
1. Mise à jour `apt`
2. Installation FFmpeg, polices, dépendances Chromium
3. Installation Node.js 20 via NodeSource
4. Création du virtualenv Python 3.11
5. `pip install -r requirements.txt`
6. `playwright install chromium --with-deps`
7. `npm install` (Remotion)
8. Création utilisateur système `tiktokbot`
9. Installation + activation des units systemd

### Option B — Installation manuelle

```bash
cd /opt/tiktok-autobot

# Dépendances système
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv ffmpeg nodejs npm \
  fonts-dejavu-core libnss3 libgbm1 libasound2

# Playwright Chromium
sudo apt-get install -y libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
  libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libpango-1.0-0 libcairo2

# Virtualenv Python
python3.11 -m venv venv
source venv/bin/activate

# Dépendances Python
pip install -r requirements.txt

# Playwright (navigateur)
playwright install chromium --with-deps

# Dépendances Node.js (Remotion)
npm install
```

---

## Configuration

### Fichier `.env`

```bash
cp .env.example .env
nano .env
```

```env
# ── Claude API (Anthropic) ────────────────────────────────────────────
# Obtenir sur : console.anthropic.com
ANTHROPIC_API_KEY=sk-ant-api03-...

# ── ElevenLabs TTS ────────────────────────────────────────────────────
# Obtenir sur : elevenlabs.io/api
ELEVENLABS_API_KEY=...

# Voice ID FR recommandés :
#   EXAVITQu4vr4xnSDxMaL  →  Sarah (naturelle, recommandée)
#   21m00Tcm4TlvDq8ikWAM  →  Rachel
#   MF3mGyEYCl7XYWbV9V6O  →  Elli
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL

# ── Cookies TikTok ────────────────────────────────────────────────────
TIKTOK_COOKIES_PATH=cookies.json
```

### Variables avancées dans `config.py`

| Variable | Défaut | Description |
|---|---|---|
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Modèle Claude utilisé |
| `WHISPER_MODEL` | `base` | Taille modèle Whisper (`tiny`/`base`/`small`) |
| `TTS_SPEED` | `1.1` | Vitesse voix ElevenLabs (1.0 = normal) |
| `VIDEO_FPS` | `30` | Images par seconde |
| `RETRY_MAX` | `3` | Tentatives max avant abandon |
| `VIDEOS_PER_DAY` | `8` | Référence (géré par le timer) |

---

## Cookies TikTok

Les cookies permettent au bot d'uploader sur **ton compte TikTok existant** sans avoir à se reconnecter.

### Exporter les cookies

1. Ouvre **Chrome** ou **Firefox**
2. Va sur [tiktok.com](https://www.tiktok.com) et **connecte-toi**
3. Installe l'extension **[Cookie-Editor](https://cookie-editor.cgagnier.ca/)**
4. Clique l'icône → **Export** → **Export as JSON**
5. Copie le contenu dans `/opt/tiktok-autobot/cookies.json`

### Format attendu

```json
[
  {
    "name": "sessionid",
    "value": "abc123...",
    "domain": ".tiktok.com",
    "path": "/",
    "httpOnly": true,
    "secure": true
  },
  ...
]
```

> Les cookies expirent en général après **30 à 90 jours**. Renouvelle-les si les uploads échouent.

---

## Lancement

### Premier test manuel

```bash
cd /opt/tiktok-autobot
source venv/bin/activate

# Génère et uploade une vidéo sur un topic spécifique
python main.py --topic "5 f-strings Python que tu n'utilises pas encore"

# Sans topic → sélection aléatoire selon le thème du jour
python main.py
```

### Activer l'automatisation (8 vidéos/jour)

```bash
# Démarre le timer systemd
sudo systemctl start tiktok-bot.timer

# Vérifie qu'il tourne
sudo systemctl status tiktok-bot.timer

# Voir les prochains déclenchements
systemctl list-timers tiktok-bot.timer
```

---

## Planning éditorial

Le thème change chaque jour automatiquement. Chaque thème dispose d'un pool de **10 topics** et d'un lien d'affiliation dédié.

| Jour | Thème | Topics | Affiliation |
|---|---|---|---|
| Lundi | Python Tips | f-strings, decorators, asyncio… | Python Bootcamp |
| Mardi | IA & LLM | Prompt engineering, RAG, agents… | Cursor AI |
| Mercredi | DevOps & Cloud | Docker, GitHub Actions, Terraform… | AWS Certs |
| Jeudi | Outils & Productivité | VSCode, git aliases, Neovim… | Notion |
| Vendredi | Cybersécurité | SQL injection, JWT, OWASP… | HackTheBox |
| Samedi | Carrière & Salaires | Salaires FR, freelance, négociation… | OpenClassrooms |
| Dimanche | Web & Frontend | Next.js 15, RSC, Tailwind, tRPC… | Vercel |

Pour ajouter des topics ou modifier les affiliations : édite `content_strategy.py` → `WEEKLY_PLAN`.

---

## Pipeline détaillé

### 1 — Génération script (`script_generator.py`)

Appel Claude API avec un prompt optimisé pour le contenu viral TikTok FR.

**Sortie JSON :**
```json
{
  "title": "5 f-strings Python que tu n'utilises pas",
  "hook": "Tu utilises Python depuis des années... et tu rates ça.",
  "segments": [
    {
      "id": 1,
      "text": "Les f-strings, tu connais. Mais le debug mode avec = ?",
      "visual_hint": "code: x = 42; print(f'{x=}')",
      "duration_estimate": 6
    }
  ],
  "cta": "Lien en bio pour aller plus loin !",
  "hashtags": ["#python", "#programmation", "#devfr"],
  "code_lines": ["x = 42", "print(f'{x=}')"]
}
```

### 2 — Synthèse vocale (`tts.py`)

- Modèle : `eleven_multilingual_v2`
- Paramètres voix : stability 0.5, similarity 0.75, style 0.4
- 1 fichier MP3 par segment → `output/<job_id>/audio/segment_01.mp3`

### 3 — Sous-titres (`subtitles.py`)

- Whisper transcrit chaque MP3 séparément
- Calcule les offsets temporels cumulatifs
- Texte converti en **MAJUSCULES** (style TikTok)
- Sortie : `output/<job_id>/subtitles.srt`

### 4 — Assemblage vidéo (`video_builder.py`)

Filtre FFmpeg complexe en une seule passe :
- Fond `#0d0d1a` (dark navy)
- Barre violette `#6c63ff` en haut
- Header `@tech_fr` centré
- Sous-titres : DejaVuSans-Bold, taille 22, blanc, centré, outline noir
- CTA doré dernières 3 secondes
- Codec : H.264 CRF 23, AAC 192k

### 5 — Randomisation (`metadata_randomizer.py`)

| Variation | Plage | But |
|---|---|---|
| Vitesse vidéo | 0.99× – 1.01× | Éviter hash matching |
| Brightness | −0.02 – +0.02 | Imperceptible à l'œil |
| Contrast | 0.97 – 1.03 | Fingerprint unique |
| `encoder` metadata | 6 valeurs aléatoires | Masquer l'origine |
| `creation_time` | J−7 à J | Date EXIF variable |

### 6 — Upload (`stealth_uploader.py`)

Séquence simulée :
1. Ouvre TikTok **home** (comportement naturel)
2. Scrolls aléatoires
3. Navigue vers `/upload`
4. Dépose le fichier vidéo
5. Remplit la description + hashtags (frappe humaine)
6. Micro-mouvements pendant l'attente
7. Clic sur "Publier"

---

## Remotion (animations)

Remotion génère un fond animé React/TypeScript en MP4, superposable sur la vidéo FFmpeg.

### Compositions disponibles

| ID | Fichier | Description |
|---|---|---|
| `TechFRVideo` | `TechFRVideo.tsx` | Fond animé + CodeTyping + CTA spring |

### Lancer le studio de preview

```bash
npm run start
# Ouvre http://localhost:3000
```

### Render en CLI

```bash
npx remotion render tiktok-visuals/src/index.ts TechFRVideo output/test.mp4 \
  --width 1080 --height 1920 --fps 30 \
  --props '{"topic":"Python tips","codeLines":["print(f\"{x=}\")"],"channelHandle":"@tech_fr"}'
```

### Activer le rendu Remotion dans le pipeline

Dans `main.py`, décommente la section `render_remotion_video` et l'appel à `overlay_remotion_on_video`.

---

## Docker

### Build & test

```bash
cp .env.example .env && nano .env

docker compose build

# Test manuel
docker compose run --rm tiktok-bot python main.py --topic "Docker test"
```

### Avec cron système (hors Docker Compose restart)

```bash
# Ajoute la tâche cron
echo "0 0,3,6,9,12,15,18,21 * * * root \
  docker compose -f /opt/tiktok-autobot/docker-compose.yml run --rm \
  tiktok-bot python main.py >> /var/log/tiktok-autobot-cron.log 2>&1" \
  | sudo tee /etc/cron.d/tiktok-autobot
```

---

## Systemd timer

Le timer déclenche le service **8 fois par jour** : 00h, 03h, 06h, 09h, 12h, 15h, 18h, 21h.

```bash
# Voir les fichiers
cat tiktok-bot.service
cat tiktok-bot.timer

# Installer (fait par install.sh, ou manuellement)
sudo cp tiktok-bot.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tiktok-bot.timer

# Statut
sudo systemctl status tiktok-bot.timer
systemctl list-timers tiktok-bot.timer

# Déclencher manuellement (hors timer)
sudo systemctl start tiktok-bot.service

# Logs du dernier run
journalctl -u tiktok-bot.service -n 50

# Logs en temps réel
journalctl -fu tiktok-bot.service
```

---

## Commandes utiles

```bash
# ── Générer une vidéo ─────────────────────────────────────────────────
source venv/bin/activate

python main.py                                        # topic aléatoire du jour
python main.py --topic "Docker en 60 secondes"       # topic forcé
python main.py --stats                                # stats du jour

# ── Analytics ─────────────────────────────────────────────────────────
python -c "from analytics_tracker import get_daily_stats; \
           import json; print(json.dumps(get_daily_stats(), indent=2, ensure_ascii=False))"

python -c "from analytics_tracker import get_weekly_report; print(get_weekly_report())"

# ── Logs ──────────────────────────────────────────────────────────────
ls -lt logs/                               # logs récents
tail -f logs/run_*.log                     # suivi dernier log fichier
journalctl -fu tiktok-bot.service          # suivi logs systemd

# ── Remotion ──────────────────────────────────────────────────────────
npm run start                              # studio preview (port 3000)

# ── Vérifications système ─────────────────────────────────────────────
python -c "import whisper; m = whisper.load_model('base'); print('Whisper OK')"
python -c "import anthropic; print('Anthropic OK')"
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
ffmpeg -version | head -1
node -v && npx remotion --version
```

---

## Structure des sorties

```
tiktok-autobot/
├── output/
│   └── 20250408_120000/          ← job_id (timestamp)
│       ├── audio/
│       │   ├── segment_01.mp3
│       │   ├── segment_02.mp3
│       │   └── ...
│       ├── audio_full.wav         ← segments concaténés
│       ├── subtitles.srt          ← sous-titres horodatés
│       ├── final_video.mp4        ← vidéo FFmpeg brute
│       └── final_randomized.mp4  ← vidéo uploadée (métadonnées variées)
│
└── logs/
    ├── run_20250408_120000.log    ← log détaillé de chaque run
    └── analytics.jsonl            ← historique JSON Lines (1 ligne/vidéo)
```

### Format d'une entrée `analytics.jsonl`

```json
{
  "timestamp": "2025-04-08T12:00:00Z",
  "job_id": "20250408_120000",
  "topic": "5 f-strings Python que tu n'utilises pas encore",
  "title": "Tu rates ces f-strings Python depuis des années",
  "theme": "python_tips",
  "hashtags": ["#python", "#programmation", "#devfr"],
  "video_path": "output/20250408_120000/final_randomized.mp4",
  "upload_success": true,
  "duration_seconds": 52.4,
  "pipeline_duration_seconds": 187.3,
  "day_of_week": "Tuesday"
}
```

---

## Anti-détection

Le bot intègre 5 couches de protection contre la détection automatisée :

### 1. Patches JavaScript Playwright

| Patch | Cible | Méthode |
|---|---|---|
| `navigator.webdriver` | Supprime le flag bot | `Object.defineProperty` → `undefined` |
| `navigator.plugins` | Simule les plugins Chrome | 3 plugins réalistes injectés |
| Canvas fingerprint | Bruite les pixels | Noise ±0.2 sur `getImageData` |
| WebGL vendor | Simule Intel GPU | Override `getParameter` |
| `screen.width/height` | Dimensions réalistes | 1920×1080 |
| Timezone | Europe/Paris cohérent | `Date.getTimezoneOffset` → −60 |

### 2. Comportement humain (`human_behavior.py`)

- **Souris** : courbe de Bézier cubique avec easing ease-in-out
- **Frappe** : délais gaussiens 50–180ms, pauses occasionnelles 300–800ms
- **Scroll** : progression sinusoïdale (accélération/décélération)
- **Micro-mouvements** : déplacements aléatoires ±30px pendant les attentes

### 3. Métadonnées vidéo (`metadata_randomizer.py`)

Chaque vidéo est légèrement différente au niveau binaire, évitant la détection par hash ou fingerprint de contenu.

### 4. Session réelle via cookies

Utilise une vraie session TikTok exportée depuis ton navigateur — pas de simulation de login.

### 5. User-agent et contexte réaliste

```
Mozilla/5.0 (Windows NT 10.0; Win64; x64)
AppleWebKit/537.36 (KHTML, like Gecko)
Chrome/124.0.0.0 Safari/537.36
```
Locale `fr-FR`, timezone `Europe/Paris`, géolocalisation Paris.

---

## Dépannage

### Whisper — `No module named 'whisper'` ou erreur torch

```bash
# CPU uniquement (VPS sans GPU)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install openai-whisper
```

### Playwright — Chromium introuvable

```bash
playwright install chromium --with-deps
# ou en root
sudo $(which playwright) install chromium --with-deps
```

### FFmpeg — `subtitles` filter erreur

Vérifie que FFmpeg est compilé avec `--enable-libass` :
```bash
ffmpeg -filters | grep subtitles
# Si absent :
sudo apt-get install ffmpeg libass-dev
```

### Upload TikTok — sélecteur CSS introuvable

TikTok met à jour son UI régulièrement. Pour déboguer :
```bash
# Lance en mode visible (non-headless) pour inspecter manuellement
# Dans stealth_uploader.py, remplace headless=True par headless=False
python -c "
import asyncio
from stealth_uploader import upload_to_tiktok
from pathlib import Path
asyncio.run(upload_to_tiktok(Path('output/test.mp4'), 'Test', ['#test']))
"
```

### Cookies expirés

Symptôme : redirection vers la page de login lors de l'upload.

```bash
# Ré-exporte les cookies TikTok depuis Chrome (voir section Cookies TikTok)
# Remplace le fichier existant
cp ~/Downloads/cookies_export.json /opt/tiktok-autobot/cookies.json
```

### Mémoire insuffisante (Whisper + Chromium)

```bash
# Utilise le modèle Whisper plus léger
# Dans config.py : WHISPER_MODEL = "tiny"

# Ou augmente le swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Vérifier que tout fonctionne avant le premier run

```bash
source venv/bin/activate

# Test individuel de chaque module
python -c "
from config import ANTHROPIC_API_KEY, ELEVENLABS_API_KEY
assert ANTHROPIC_API_KEY, 'ANTHROPIC_API_KEY manquante'
assert ELEVENLABS_API_KEY, 'ELEVENLABS_API_KEY manquante'
print('Config OK')
"

python -c "import whisper; whisper.load_model('base'); print('Whisper OK')"
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
ffmpeg -version | head -1 && echo "FFmpeg OK"
node -v && echo "Node OK"
```
