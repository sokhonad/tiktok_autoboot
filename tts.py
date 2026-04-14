"""
tts.py — Génération audio via gTTS (Google Translate TTS, gratuit, aucune clé API).
Fonctionne depuis les VPS/serveurs sans restriction IP.
Génère un fichier MP3 par segment du script.
"""

import logging
from pathlib import Path

from gtts import gTTS

from config import OUTPUT_DIR, TTS_SPEED

logger = logging.getLogger(__name__)

# Langue et domaine TLD pour la voix FR
# tld="fr" = accent français (France), tld="ca" = accent québécois
_LANG = "fr"
_TLD = "fr"


def generate_segment_audio(
    text: str,
    segment_id: int,
    job_id: str,
    speed: float = TTS_SPEED,
) -> Path:
    """
    Génère le fichier audio MP3 pour un segment de texte.

    Args:
        text: Texte à synthétiser
        segment_id: Numéro du segment (pour nommer le fichier)
        job_id: Identifiant unique du job
        speed: Ignoré (gTTS ne supporte pas la vitesse variable)

    Returns:
        Path vers le fichier MP3 généré
    """
    audio_dir = OUTPUT_DIR / job_id / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    output_path = audio_dir / f"segment_{segment_id:02d}.mp3"

    logger.info(f"TTS segment {segment_id} : '{text[:50]}...'")
    tts = gTTS(text=text, lang=_LANG, tld=_TLD, slow=False)
    tts.save(str(output_path))
    logger.info(f"Audio segment {segment_id} sauvegardé : {output_path}")
    return output_path


def generate_all_segments(segments: list[dict], job_id: str) -> list[Path]:
    """
    Génère les fichiers audio pour tous les segments du script.

    Args:
        segments: Liste de dicts avec au moins la clé 'text'
        job_id: Identifiant unique du job

    Returns:
        Liste ordonnée des Path vers les MP3 générés
    """
    audio_paths: list[Path] = []

    for segment in segments:
        seg_id = segment.get("id", len(audio_paths) + 1)
        text = segment["text"]
        try:
            path = generate_segment_audio(text, seg_id, job_id)
            audio_paths.append(path)
        except Exception as e:
            logger.error(f"Erreur TTS segment {seg_id} : {e}")
            raise

    logger.info(f"TTS complet : {len(audio_paths)} fichiers audio générés")
    return audio_paths
