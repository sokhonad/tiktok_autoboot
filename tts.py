"""
tts.py — Génération audio via ElevenLabs (multilingual v2).
Génère un fichier MP3 par segment du script.
"""

import logging
from pathlib import Path

import requests

from config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
    TTS_MODEL,
    TTS_SPEED,
    OUTPUT_DIR,
)

logger = logging.getLogger(__name__)

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"


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
        job_id: Identifiant unique du job (ex: timestamp)
        speed: Vitesse de lecture (1.0 = normal, 1.1 = légèrement rapide)

    Returns:
        Path vers le fichier MP3 généré

    Raises:
        requests.HTTPError: Si l'appel API ElevenLabs échoue
    """
    url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{ELEVENLABS_VOICE_ID}"

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    payload = {
        "text": text,
        "model_id": TTS_MODEL,
        "voice_settings": {
            "stability": 0.5,           # équilibre stabilité/expressivité
            "similarity_boost": 0.75,   # fidélité à la voix originale
            "style": 0.4,               # un peu de style pour TikTok
            "use_speaker_boost": True,
        },
        # speed est un paramètre de génération, pas de voice_settings
    }

    logger.info(f"TTS segment {segment_id} : '{text[:50]}...'")

    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()

    # Sauvegarde dans output/<job_id>/audio_segment_<id>.mp3
    audio_dir = OUTPUT_DIR / job_id / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    output_path = audio_dir / f"segment_{segment_id:02d}.mp3"
    output_path.write_bytes(response.content)

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
        except requests.HTTPError as e:
            logger.error(f"Erreur TTS segment {seg_id} : {e}")
            raise

    logger.info(f"TTS complet : {len(audio_paths)} fichiers audio générés")
    return audio_paths
