"""
remotion_renderer.py — Rendu headless via CLI Remotion.
Passe topic + code_lines en props JSON, retourne un MP4 1080x1920 30fps.
"""

import json
import logging
import subprocess
from pathlib import Path

from config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    VIDEO_FPS,
    OUTPUT_DIR,
    REMOTION_DIR,
)

logger = logging.getLogger(__name__)

# Composition Remotion à utiliser (doit correspondre à Root.tsx)
REMOTION_COMPOSITION_ID = "TechFRVideo"


def render_remotion_video(
    job_id: str,
    topic: str,
    code_lines: list[str],
    duration_in_frames: int = 1800,  # 60s × 30fps
) -> Path:
    """
    Rend une vidéo MP4 via Remotion CLI en mode headless.

    Args:
        job_id: Identifiant unique du job
        topic: Sujet de la vidéo (affiché en titre)
        code_lines: Lignes de code à animer dans CodeTyping
        duration_in_frames: Durée en frames (default: 60s × 30fps)

    Returns:
        Path vers le fichier MP4 rendu

    Raises:
        RuntimeError: Si Remotion échoue
    """
    out_dir = OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / "remotion_bg.mp4"

    # Props passées à la composition Remotion en JSON
    props = {
        "topic": topic,
        "codeLines": code_lines,
        "channelHandle": "@tech_fr",
    }
    props_json = json.dumps(props)

    # Commande npx remotion render
    cmd = [
        "npx", "remotion", "render",
        str(REMOTION_DIR),                  # dossier racine Remotion
        REMOTION_COMPOSITION_ID,            # ID de la composition
        str(output_path),                   # chemin de sortie
        "--props", props_json,
        "--width", str(VIDEO_WIDTH),
        "--height", str(VIDEO_HEIGHT),
        "--fps", str(VIDEO_FPS),
        "--frames", f"0-{duration_in_frames - 1}",
        "--codec", "h264",
        "--crf", "23",
        "--concurrency", "4",               # parallélisme render
        "--log", "warn",
    ]

    logger.info(f"Rendu Remotion : topic='{topic}', frames={duration_in_frames}")
    logger.debug(f"CMD: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        cwd=str(REMOTION_DIR),
        capture_output=True,
        text=True,
        timeout=300,  # 5 minutes max
    )

    if result.returncode != 0:
        logger.error(f"Remotion stderr:\n{result.stderr}")
        raise RuntimeError(f"Remotion render failed:\n{result.stderr[-500:]}")

    logger.info(f"Remotion render OK : {output_path}")
    return output_path


def overlay_remotion_on_video(
    base_video: Path,
    remotion_video: Path,
    job_id: str,
) -> Path:
    """
    Superpose le rendu Remotion (fond animé) sous la vidéo principale.
    Utilisé si on veut mixer l'animation React avec l'audio+sous-titres.

    Args:
        base_video: Vidéo principale (avec audio et sous-titres)
        remotion_video: Vidéo de fond Remotion
        job_id: Identifiant du job

    Returns:
        Path vers la vidéo fusionnée
    """
    out_dir = OUTPUT_DIR / job_id
    output_path = out_dir / "merged_video.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(remotion_video),   # fond animé
        "-i", str(base_video),       # vidéo principale (avec texte/sous-titres)
        "-filter_complex",
        "[0:v][1:v]overlay=0:0[v]",  # superpose la vidéo principale sur le fond
        "-map", "[v]",
        "-map", "1:a",               # audio de la vidéo principale
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Overlay FFmpeg failed:\n{result.stderr[-500:]}")

    logger.info(f"Vidéo fusionnée : {output_path}")
    return output_path
