"""
main.py — Orchestrateur principal du pipeline TikTok Autobot.
Génère et publie une vidéo complète : script → TTS → sous-titres → vidéo → upload.
Gestion d'erreurs avec retry (3 tentatives), logs horodatés, nettoyage auto.
"""

import asyncio
import logging
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

from config import (
    LOGS_DIR,
    OUTPUT_DIR,
    RETRY_MAX,
    RETRY_DELAY_SECONDS,
    VIDEOS_PER_DAY,
)
from content_strategy import get_today_strategy, get_today_topic, inject_cta
from script_generator import generate_script
from tts import generate_all_segments
from subtitles import generate_srt
from video_builder import concatenate_audio, build_final_video
from remotion_renderer import render_remotion_video
from metadata_randomizer import randomize_video_metadata
from stealth_uploader import upload_to_tiktok
from analytics_tracker import record_video_publish, get_daily_stats

# ── Configuration du logging ─────────────────────────────────────────────────
LOGS_DIR.mkdir(parents=True, exist_ok=True)

log_filename = LOGS_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_filename, encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")


def _make_job_id() -> str:
    """Génère un identifiant unique pour ce job basé sur le timestamp."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _cleanup_job(job_id: str) -> None:
    """
    Supprime les fichiers temporaires du job (audio, srt, remotion bg).
    Conserve uniquement la vidéo finale dans output/<job_id>/.
    """
    job_dir = OUTPUT_DIR / job_id
    if not job_dir.exists():
        return

    # Supprime les sous-dossiers temporaires
    for subdir in ["audio"]:
        target = job_dir / subdir
        if target.exists():
            shutil.rmtree(target)
            logger.debug(f"Nettoyé : {target}")

    # Supprime les fichiers intermédiaires
    for pattern in ["audio_full.wav", "remotion_bg.mp4", "subtitles.srt", "final_video.mp4"]:
        p = job_dir / pattern
        if p.exists():
            p.unlink()
            logger.debug(f"Supprimé : {p}")

    logger.info(f"Nettoyage terminé pour job {job_id}")


async def run_pipeline(topic: str | None = None) -> bool:
    """
    Exécute le pipeline complet pour générer et publier une vidéo.

    Étapes :
    1. Récupère la stratégie du jour et un topic
    2. Génère le script via Claude API
    3. Génère l'audio via ElevenLabs (TTS)
    4. Génère les sous-titres via Whisper
    5. Assemble la vidéo via FFmpeg
    6. (Optionnel) Rendu Remotion
    7. Randomise les métadonnées
    8. Upload sur TikTok
    9. Log analytics + nettoyage

    Args:
        topic: Topic spécifique (si None, sélection aléatoire du jour)

    Returns:
        True si l'upload a réussi
    """
    pipeline_start = time.time()
    job_id = _make_job_id()
    strategy = get_today_strategy()

    if topic is None:
        topic = get_today_topic()

    logger.info(f"{'='*60}")
    logger.info(f"NOUVEAU JOB : {job_id}")
    logger.info(f"Topic       : {topic}")
    logger.info(f"Thème       : {strategy['theme']}")
    logger.info(f"{'='*60}")

    # ── Étape 1 : Génération du script ───────────────────────────────────────
    logger.info("ÉTAPE 1/7 — Génération du script (Claude API)...")
    script = generate_script(topic, strategy)
    script = inject_cta(script, strategy)

    logger.info(f"Script : '{script['title']}' — {len(script['segments'])} segments")

    # ── Étape 2 : Synthèse vocale ────────────────────────────────────────────
    logger.info("ÉTAPE 2/7 — Synthèse vocale (ElevenLabs)...")
    audio_paths = generate_all_segments(script["segments"], job_id)
    logger.info(f"{len(audio_paths)} fichiers audio générés")

    # ── Étape 3 : Sous-titres ────────────────────────────────────────────────
    logger.info("ÉTAPE 3/7 — Génération sous-titres (Whisper)...")
    srt_path = generate_srt(audio_paths, job_id)

    # ── Étape 4 : Concaténation audio ────────────────────────────────────────
    logger.info("ÉTAPE 4/7 — Concaténation audio...")
    full_audio = concatenate_audio(audio_paths, job_id)

    # ── Étape 5 : Assemblage vidéo ───────────────────────────────────────────
    logger.info("ÉTAPE 5/7 — Assemblage vidéo (FFmpeg)...")
    video_path = build_final_video(
        audio_path=full_audio,
        srt_path=srt_path,
        job_id=job_id,
        title=script["title"],
        cta=script["cta"],
        script=script,
    )

    # ── Étape 6 : Randomisation métadonnées ──────────────────────────────────
    logger.info("ÉTAPE 6/7 — Randomisation métadonnées...")
    final_video = randomize_video_metadata(video_path, job_id)

    # ── Étape 7 : Upload TikTok ──────────────────────────────────────────────
    logger.info("ÉTAPE 7/7 — Upload TikTok (Playwright)...")
    upload_success = await upload_to_tiktok(
        video_path=final_video,
        title=script["title"],
        hashtags=script.get("hashtags", []),
    )

    pipeline_duration = time.time() - pipeline_start

    # ── Enregistrement analytics ─────────────────────────────────────────────
    # Durée vidéo (approximée depuis les segments)
    total_duration = sum(
        s.get("duration_estimate", 5) for s in script["segments"]
    )

    record_video_publish(
        job_id=job_id,
        topic=topic,
        title=script["title"],
        theme=strategy["theme"],
        hashtags=script.get("hashtags", []),
        video_path=str(final_video),
        upload_success=upload_success,
        duration_seconds=float(total_duration),
        pipeline_duration_seconds=pipeline_duration,
    )

    status = "SUCCÈS" if upload_success else "ÉCHEC"
    logger.info(f"Pipeline terminé [{status}] en {pipeline_duration:.1f}s — Job: {job_id}")

    # Nettoyage des fichiers temporaires
    _cleanup_job(job_id)

    return upload_success


async def run_with_retry(topic: str | None = None) -> bool:
    """
    Lance le pipeline avec retry automatique (max RETRY_MAX tentatives).

    Args:
        topic: Topic optionnel à forcer

    Returns:
        True si au moins une tentative a réussi
    """
    for attempt in range(1, RETRY_MAX + 1):
        try:
            logger.info(f"Tentative {attempt}/{RETRY_MAX}")
            result = await run_pipeline(topic)
            if result:
                return True
            logger.warning(f"Tentative {attempt} : upload échoué (sans exception)")
        except Exception as e:
            logger.error(f"Tentative {attempt} échouée avec exception : {e}", exc_info=True)

        if attempt < RETRY_MAX:
            logger.info(f"Attente {RETRY_DELAY_SECONDS}s avant retry...")
            await asyncio.sleep(RETRY_DELAY_SECONDS)

    logger.error(f"Toutes les tentatives ont échoué pour ce job")
    return False


async def main() -> None:
    """
    Point d'entrée principal.
    Lance une seule vidéo (appelé par le cron toutes les 3h).
    """
    import argparse

    parser = argparse.ArgumentParser(description="TikTok Autobot — Pipeline de génération vidéo")
    parser.add_argument("--topic", type=str, help="Topic spécifique à générer", default=None)
    parser.add_argument("--stats", action="store_true", help="Affiche les stats du jour et quitte")
    args = parser.parse_args()

    if args.stats:
        stats = get_daily_stats()
        logger.info(f"Stats du jour : {stats}")
        return

    logger.info(f"TikTok Autobot démarré — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    success = await run_with_retry(topic=args.topic)

    if not success:
        sys.exit(1)  # Code retour 1 pour indiquer l'échec (utile pour systemd)


if __name__ == "__main__":
    asyncio.run(main())
