"""
video_builder.py — Assemblage final de la vidéo via FFmpeg.
Concatène les audios, fond dark animé 1080x1920, sous-titres style TikTok,
header @tech_fr et CTA animé pour les 3 dernières secondes.
"""

import logging
import subprocess
import tempfile
from pathlib import Path

from config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    VIDEO_FPS,
    OUTPUT_DIR,
    BACKGROUNDS_DIR,
    CHANNEL_HANDLE,
)

logger = logging.getLogger(__name__)


def _run_ffmpeg(args: list[str], description: str) -> None:
    """Execute une commande FFmpeg et lève une exception si elle échoue."""
    cmd = ["ffmpeg", "-y"] + args
    logger.debug(f"FFmpeg [{description}]: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"FFmpeg error [{description}]:\n{result.stderr}")
        raise RuntimeError(f"FFmpeg failed: {description}\n{result.stderr[-500:]}")


def concatenate_audio(audio_paths: list[Path], job_id: str) -> Path:
    """
    Concatène tous les segments MP3 en un seul fichier WAV.

    Args:
        audio_paths: Liste ordonnée des fichiers audio
        job_id: Identifiant du job

    Returns:
        Path vers le fichier audio concaténé
    """
    out_dir = OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    concat_path = out_dir / "audio_full.wav"

    # Crée un fichier de liste pour FFmpeg concat demuxer
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for p in audio_paths:
            f.write(f"file '{p.resolve()}'\n")
        list_file = f.name

    _run_ffmpeg(
        ["-f", "concat", "-safe", "0", "-i", list_file, "-ar", "44100", str(concat_path)],
        "concatenate_audio",
    )

    Path(list_file).unlink(missing_ok=True)
    logger.info(f"Audio concaténé : {concat_path}")
    return concat_path


def _build_background_filter(duration: float) -> str:
    """
    Construit le filtre FFmpeg pour le fond dark animé avec gradient.
    Fond noir avec légère animation de particules simulée via noise.
    """
    w, h = VIDEO_WIDTH, VIDEO_HEIGHT
    return (
        f"color=c=0x0a0a0f:size={w}x{h}:rate={VIDEO_FPS}:duration={duration}[bg];"
        # Bande colorée en haut (dégradé violet-bleu)
        f"[bg]drawbox=x=0:y=0:w={w}:h=8:color=0x6c63ff@0.8:t=fill[bg];"
        # Header channel
        f"[bg]drawtext=text='{CHANNEL_HANDLE}':fontcolor=white:fontsize=36:"
        f"x=(w-text_w)/2:y=30:font=Montserrat:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf[bg]"
    )


def build_final_video(
    audio_path: Path,
    srt_path: Path,
    job_id: str,
    title: str,
    cta: str,
    script: dict,
) -> Path:
    """
    Assemble la vidéo finale : fond animé + audio + sous-titres + header + CTA.

    Args:
        audio_path: Fichier audio concaténé
        srt_path: Fichier de sous-titres SRT
        job_id: Identifiant du job
        title: Titre de la vidéo (pour overlay)
        cta: Texte du CTA affiché en fin de vidéo
        script: Script complet (pour accéder aux metadata)

    Returns:
        Path vers la vidéo MP4 finale
    """
    out_dir = OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / "final_video.mp4"

    # Récupère la durée de l'audio
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(audio_path)],
        capture_output=True, text=True, check=True
    )
    duration = float(probe.stdout.strip())
    cta_start = max(0, duration - 3)  # CTA les 3 dernières secondes

    w, h = VIDEO_WIDTH, VIDEO_HEIGHT
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    # Échappe le chemin SRT pour FFmpeg (antislash Windows + virgules)
    srt_escaped = str(srt_path).replace("\\", "/").replace(":", "\\:")

    # Texte CTA nettoyé : supprime émojis, newlines et caractères non-ASCII
    cta_clean = "".join(
        c for c in cta.replace("\n", " ").replace("\r", "")[:50]
        if ord(c) < 128
    ).strip()

    # Filtre vidéo simple — PAS de label [bg], source déjà passée en -i
    vf_filter = ",".join([
        # Barre violette en haut
        f"drawbox=x=0:y=0:w={w}:h=6:color=0x6c63ff@1:t=fill",
        # Header @tech_fr
        f"drawtext=text='{CHANNEL_HANDLE}':fontfile={font_path}"
        f":fontcolor=white:fontsize=38:x=(w-text_w)/2:y=18",
        # Sous-titres style TikTok
        f"subtitles='{srt_escaped}':force_style="
        f"'FontName=DejaVuSans-Bold,FontSize=22,"
        f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        f"Outline=3,Shadow=1,Alignment=2,MarginV=320'",
        # CTA doré les 3 dernières secondes
        f"drawtext=text='{cta_clean}':fontfile={font_path}"
        f":fontcolor=0xFFD700:fontsize=26"
        f":x=(w-text_w)/2:y=h-160"
        f":enable='between(t,{cta_start:.1f},{duration:.1f})'"
        f":box=1:boxcolor=0x000000@0.6:boxborderw=8",
    ])

    _run_ffmpeg(
        [
            "-f", "lavfi", "-i", f"color=c=0x0d0d1a:size={w}x{h}:rate={VIDEO_FPS}",
            "-i", str(audio_path),
            "-vf", vf_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            "-movflags", "+faststart",
            str(output_path),
        ],
        "build_final_video",
    )

    logger.info(f"Vidéo finale : {output_path} ({duration:.1f}s)")
    return output_path
