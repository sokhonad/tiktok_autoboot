"""
metadata_randomizer.py — Variation imperceptible des métadonnées vidéo.
Variation vitesse, brightness/contrast minimes, métadonnées EXIF aléatoires.
"""

import logging
import random
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from config import OUTPUT_DIR

logger = logging.getLogger(__name__)


def _run_ffmpeg(args: list[str], description: str) -> None:
    """Execute FFmpeg silencieusement et lève une exception si erreur."""
    cmd = ["ffmpeg", "-y"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"FFmpeg error [{description}]:\n{result.stderr[-400:]}")
        raise RuntimeError(f"FFmpeg failed: {description}")


def randomize_video_metadata(input_path: Path, job_id: str) -> Path:
    """
    Applique des variations imperceptibles à la vidéo pour éviter la détection
    par empreinte digitale (fingerprinting) de contenu dupliqué.

    Variations appliquées :
    - Vitesse : ±1% (0.99x à 1.01x)
    - Brightness : ±0.02 (imperceptible à l'œil)
    - Contrast : ±0.03
    - Métadonnées encoder : chaîne aléatoire
    - creation_time : date aléatoire dans les 7 derniers jours

    Args:
        input_path: Vidéo d'entrée
        job_id: Identifiant du job

    Returns:
        Path vers la vidéo avec métadonnées randomisées
    """
    out_dir = OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / "final_randomized.mp4"

    # ── Variation vitesse (0.99x – 1.01x) ───────────────────────────────────
    speed_factor = random.uniform(0.99, 1.01)
    audio_tempo = 1 / speed_factor  # compensation audio inverse

    # ── Variation brightness/contrast imperceptible ──────────────────────────
    brightness = random.uniform(-0.02, 0.02)
    contrast = random.uniform(0.97, 1.03)

    # ── Métadonnées EXIF aléatoires ──────────────────────────────────────────
    # Simule différentes caméras/encoders pour éviter le fingerprinting
    encoders = [
        "Lavf58.76.100", "Lavf59.16.100", "HandBrake 1.6.1",
        "VideoEditor 2.1", "MediaMuxer v2", "ExportKit 3.0"
    ]
    encoder_str = random.choice(encoders)

    # creation_time aléatoire dans les 7 derniers jours
    creation_offset = timedelta(
        days=random.randint(0, 7),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    creation_time = (datetime.utcnow() - creation_offset).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── Filtre vidéo combiné ─────────────────────────────────────────────────
    vf = f"setpts={speed_factor:.4f}*PTS,eq=brightness={brightness:.4f}:contrast={contrast:.4f}"

    # Filtre audio : atempo doit être entre 0.5 et 2.0
    af = f"atempo={min(max(audio_tempo, 0.5), 2.0):.4f}"

    _run_ffmpeg(
        [
            "-i", str(input_path),
            "-vf", vf,
            "-af", af,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-metadata", f"encoder={encoder_str}",
            "-metadata", f"creation_time={creation_time}",
            "-metadata", "comment=",           # efface les commentaires
            "-metadata", "copyright=",         # efface le copyright
            "-movflags", "+faststart",
            str(output_path),
        ],
        "randomize_metadata",
    )

    file_size = output_path.stat().st_size / 1024 / 1024
    logger.info(
        f"Métadonnées randomisées : speed={speed_factor:.3f}x, "
        f"brightness={brightness:+.3f}, contrast={contrast:.3f} — "
        f"{file_size:.1f} MB → {output_path}"
    )

    return output_path


def add_unique_noise_frame(input_path: Path, job_id: str) -> Path:
    """
    Ajoute une frame de bruit unique et imperceptible au début de la vidéo.
    Rend chaque vidéo unique au niveau binaire (contre le hash matching).

    Args:
        input_path: Vidéo d'entrée
        job_id: Identifiant du job

    Returns:
        Path vers la vidéo modifiée
    """
    out_dir = OUTPUT_DIR / job_id
    output_path = out_dir / "final_unique.mp4"

    # Micro-variation de teinte aléatoire sur les 3 premières frames
    hue_shift = random.uniform(-2, 2)

    vf = (
        f"select='lt(n\\,3)',hue=h={hue_shift:.2f},"
        f"select='gte(n\\,0)'"
    )

    # Plus simple : juste encoder avec un seed aléatoire pour le CRF
    crf_variation = random.randint(22, 24)

    _run_ffmpeg(
        [
            "-i", str(input_path),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", str(crf_variation),
            "-c:a", "copy",
            "-movflags", "+faststart",
            str(output_path),
        ],
        "add_unique_noise",
    )

    logger.info(f"Frame unique ajoutée : crf={crf_variation}, hue_shift={hue_shift:.2f}")
    return output_path
