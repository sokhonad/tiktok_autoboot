"""
tts.py — Génération audio via edge-tts (Microsoft, gratuit, aucune clé API).
Voix française de haute qualité : fr-FR-DeniseNeural (féminine) ou fr-FR-HenriNeural (masculine).
Génère un fichier MP3 par segment du script.
"""

import asyncio
import concurrent.futures
import logging
from pathlib import Path

import edge_tts

from config import OUTPUT_DIR, TTS_SPEED

logger = logging.getLogger(__name__)

# Voix française edge-tts — changer ici pour basculer M/F
# Voix disponibles FR : fr-FR-DeniseNeural, fr-FR-HenriNeural,
#                       fr-FR-EloiseNeural, fr-BE-CharlineNeural
TTS_VOICE = "fr-FR-DeniseNeural"

# Taux de parole : +10% = légèrement plus rapide
# Format edge-tts : "+10%" ou "-5%" (relatif à la vitesse normale)
_RATE_OFFSET = "+10%"


async def _generate_segment_async(text: str, output_path: Path) -> None:
    """Génère un segment audio MP3 via edge-tts (async)."""
    communicate = edge_tts.Communicate(text, TTS_VOICE, rate=_RATE_OFFSET)
    await communicate.save(str(output_path))


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
        speed: Ignoré (géré par _RATE_OFFSET)

    Returns:
        Path vers le fichier MP3 généré
    """
    audio_dir = OUTPUT_DIR / job_id / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    output_path = audio_dir / f"segment_{segment_id:02d}.mp3"

    logger.info(f"TTS segment {segment_id} : '{text[:50]}...'")
    # Lance dans un thread séparé pour éviter le conflit avec la boucle asyncio de main.py
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(asyncio.run, _generate_segment_async(text, output_path)).result()
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
