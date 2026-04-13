"""
subtitles.py — Génération de sous-titres SRT via Whisper local.
Transcrit chaque segment audio et produit un fichier .srt global avec offsets.
"""

import logging
import subprocess
import json
from pathlib import Path

import whisper

from config import WHISPER_MODEL, WHISPER_LANGUAGE, OUTPUT_DIR

logger = logging.getLogger(__name__)

# Modèle Whisper chargé une seule fois en mémoire
_whisper_model: whisper.Whisper | None = None


def _get_model() -> whisper.Whisper:
    """Charge le modèle Whisper en mémoire (singleton)."""
    global _whisper_model
    if _whisper_model is None:
        logger.info(f"Chargement modèle Whisper '{WHISPER_MODEL}'...")
        _whisper_model = whisper.load_model(WHISPER_MODEL)
    return _whisper_model


def _seconds_to_srt_timestamp(seconds: float) -> str:
    """Convertit des secondes en format SRT : HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _get_audio_duration(audio_path: Path) -> float:
    """Retourne la durée d'un fichier audio en secondes via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", str(audio_path)
        ],
        capture_output=True, text=True, check=True
    )
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def transcribe_segment(audio_path: Path, time_offset: float = 0.0) -> list[dict]:
    """
    Transcrit un fichier audio et retourne les segments avec timestamps absolus.

    Args:
        audio_path: Chemin vers le fichier MP3
        time_offset: Décalage temporel (début du segment dans la vidéo finale)

    Returns:
        Liste de dicts : {start, end, text}
    """
    model = _get_model()

    logger.info(f"Transcription : {audio_path.name} (offset={time_offset:.2f}s)")

    result = model.transcribe(
        str(audio_path),
        language=WHISPER_LANGUAGE,
        word_timestamps=True,
        verbose=False,
    )

    segments_out = []
    for seg in result["segments"]:
        segments_out.append({
            "start": seg["start"] + time_offset,
            "end": seg["end"] + time_offset,
            "text": seg["text"].strip(),
        })

    return segments_out


def generate_srt(audio_paths: list[Path], job_id: str) -> Path:
    """
    Génère le fichier SRT global en enchaînant tous les segments audio.

    Args:
        audio_paths: Liste ordonnée des fichiers MP3
        job_id: Identifiant du job

    Returns:
        Path vers le fichier .srt généré
    """
    all_segments: list[dict] = []
    time_offset = 0.0

    for audio_path in audio_paths:
        segments = transcribe_segment(audio_path, time_offset)
        all_segments.extend(segments)

        # Calcule l'offset pour le segment suivant
        try:
            time_offset += _get_audio_duration(audio_path)
        except (subprocess.CalledProcessError, KeyError) as e:
            logger.warning(f"Impossible de lire la durée de {audio_path} : {e}")
            # Fallback : utilise la fin du dernier segment transcrit
            if segments:
                time_offset = segments[-1]["end"] + 0.2

    # Génère le contenu SRT
    srt_lines: list[str] = []
    for i, seg in enumerate(all_segments, start=1):
        start_ts = _seconds_to_srt_timestamp(seg["start"])
        end_ts = _seconds_to_srt_timestamp(seg["end"])
        # Texte en majuscules pour le style TikTok
        text = seg["text"].upper()

        srt_lines.append(str(i))
        srt_lines.append(f"{start_ts} --> {end_ts}")
        srt_lines.append(text)
        srt_lines.append("")  # ligne vide entre chaque entrée SRT

    srt_dir = OUTPUT_DIR / job_id
    srt_dir.mkdir(parents=True, exist_ok=True)
    srt_path = srt_dir / "subtitles.srt"
    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")

    logger.info(f"SRT généré : {srt_path} ({len(all_segments)} segments)")
    return srt_path
