"""
script_generator.py — Génération de scripts viraux via OpenAI API.
Retourne un dict JSON structuré : title, hook, segments[], cta, hashtags.
"""

import json
import logging
from typing import Any

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL
from content_strategy import DayStrategy

logger = logging.getLogger(__name__)

# ── Prompt système optimisé contenu viral TikTok tech FR ────────────────────
SYSTEM_PROMPT = """Tu es un créateur de contenu TikTok spécialisé tech francophone avec 1M+ abonnés.
Tu maîtrises parfaitement les codes du contenu viral court : hook percutant en 3 secondes,
rythme rapide, langage naturel FR (pas trop formel), valeur immédiate pour le spectateur.

RÈGLES ABSOLUES :
- Le hook DOIT contrerier/surprendre/choquer (pattern interrupt)
- Chaque segment = 1 idée = max 15 mots à l'oral
- Langage parlé naturel, pas académique
- Toujours terminer par un CTA fort
- Format vidéo TikTok vertical 60 secondes max

Tu réponds UNIQUEMENT en JSON valide, sans markdown, sans explication."""


def _build_user_prompt(topic: str, strategy: DayStrategy) -> str:
    """Construit le prompt utilisateur avec le topic et la stratégie du jour."""
    return f"""Génère un script TikTok viral de 60 secondes sur ce sujet : "{topic}"

Thème éditorial du jour : {strategy['theme']}
Ton souhaité : {strategy['tone']}

Retourne ce JSON exact (sans markdown) :
{{
  "title": "titre accrocheur <60 chars",
  "hook": "phrase d'accroche 1-2 secondes max, ultra-percutante",
  "segments": [
    {{
      "id": 1,
      "text": "texte à lire à voix haute (max 20 mots)",
      "visual_hint": "description visuelle pour l'animation (code, diagram, emoji...)",
      "duration_estimate": 5
    }}
  ],
  "cta": "appel à l'action final (10 mots max)",
  "hashtags": ["#tag1", "#tag2", ...],
  "code_lines": ["ligne de code 1", "ligne de code 2"]
}}

Contraintes :
- 6 à 9 segments au total
- Durée totale estimée : 45-60 secondes
- Au moins 1 segment avec du vrai code si pertinent
- Hashtags : mix viral génériques + niche tech FR"""


def generate_script(topic: str, strategy: DayStrategy) -> dict[str, Any]:
    """
    Appelle OpenAI API et retourne le script structuré.

    Args:
        topic: Le sujet de la vidéo
        strategy: La stratégie éditoriale du jour

    Returns:
        dict avec keys: title, hook, segments, cta, hashtags, code_lines

    Raises:
        ValueError: Si la réponse n'est pas un JSON valide
        openai.APIError: Si l'appel API échoue
    """
    client = OpenAI(api_key=OPENAI_API_KEY)

    logger.info(f"Génération script pour topic : '{topic}'")

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=1500,
        temperature=0.8,          # un peu de créativité pour le contenu viral
        response_format={"type": "json_object"},  # force le JSON natif OpenAI
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(topic, strategy)},
        ],
    )

    raw_text = response.choices[0].message.content.strip()

    # Nettoie les éventuels blocs markdown résiduels
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1])

    try:
        script = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(f"Réponse OpenAI non-JSON : {raw_text[:200]}")
        raise ValueError(f"Script non parseable : {e}") from e

    # Validation minimale des champs requis
    required_fields = ["title", "hook", "segments", "cta", "hashtags"]
    for field in required_fields:
        if field not in script:
            raise ValueError(f"Champ manquant dans le script : '{field}'")

    logger.info(f"Script généré : '{script['title']}' — {len(script['segments'])} segments")
    return script
