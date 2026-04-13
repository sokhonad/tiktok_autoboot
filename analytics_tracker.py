"""
analytics_tracker.py — Suivi des KPIs et logs de performance des vidéos publiées.
Enregistre chaque run dans un fichier JSON pour analyse ultérieure.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from config import LOGS_DIR

logger = logging.getLogger(__name__)

ANALYTICS_FILE = LOGS_DIR / "analytics.jsonl"  # JSON Lines (1 entry par ligne)


def record_video_publish(
    job_id: str,
    topic: str,
    title: str,
    theme: str,
    hashtags: list[str],
    video_path: str,
    upload_success: bool,
    duration_seconds: float,
    pipeline_duration_seconds: float,
) -> None:
    """
    Enregistre les métadonnées d'une vidéo publiée dans le fichier analytics.

    Args:
        job_id: Identifiant unique du job
        topic: Sujet de la vidéo
        title: Titre généré
        theme: Thème éditorial du jour
        hashtags: Hashtags utilisés
        video_path: Chemin vers la vidéo publiée
        upload_success: True si l'upload a réussi
        duration_seconds: Durée de la vidéo en secondes
        pipeline_duration_seconds: Temps total du pipeline
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "job_id": job_id,
        "topic": topic,
        "title": title,
        "theme": theme,
        "hashtags": hashtags,
        "video_path": str(video_path),
        "upload_success": upload_success,
        "duration_seconds": round(duration_seconds, 2),
        "pipeline_duration_seconds": round(pipeline_duration_seconds, 2),
        "day_of_week": datetime.now().strftime("%A"),
    }

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ANALYTICS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    logger.info(
        f"Analytics enregistré : job={job_id}, upload={'OK' if upload_success else 'FAIL'}, "
        f"pipeline={pipeline_duration_seconds:.1f}s"
    )


def get_daily_stats() -> dict:
    """
    Retourne les statistiques du jour courant.

    Returns:
        Dict avec total_published, total_failed, topics_used
    """
    if not ANALYTICS_FILE.exists():
        return {"total_published": 0, "total_failed": 0, "topics_used": []}

    today = datetime.now().strftime("%Y-%m-%d")
    today_entries = []

    with open(ANALYTICS_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("timestamp", "").startswith(today):
                    today_entries.append(entry)
            except json.JSONDecodeError:
                continue

    published = [e for e in today_entries if e.get("upload_success")]
    failed = [e for e in today_entries if not e.get("upload_success")]

    return {
        "total_published": len(published),
        "total_failed": len(failed),
        "topics_used": [e["topic"] for e in today_entries],
        "themes_used": list({e.get("theme", "") for e in today_entries}),
        "avg_pipeline_duration": (
            sum(e.get("pipeline_duration_seconds", 0) for e in today_entries)
            / len(today_entries)
            if today_entries else 0
        ),
    }


def get_weekly_report() -> str:
    """
    Génère un rapport textuel de la semaine pour le log.

    Returns:
        String formatée avec les stats de la semaine
    """
    if not ANALYTICS_FILE.exists():
        return "Aucune donnée disponible."

    entries = []
    with open(ANALYTICS_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                entries.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue

    if not entries:
        return "Aucune entrée dans analytics."

    total = len(entries)
    success = sum(1 for e in entries if e.get("upload_success"))
    success_rate = success / total * 100 if total else 0

    # Thèmes les plus utilisés
    themes: dict[str, int] = {}
    for e in entries:
        t = e.get("theme", "unknown")
        themes[t] = themes.get(t, 0) + 1

    report = [
        f"=== RAPPORT ANALYTICS TIKTOK-AUTOBOT ===",
        f"Total vidéos traitées : {total}",
        f"Uploads réussis       : {success} ({success_rate:.1f}%)",
        f"Uploads échoués       : {total - success}",
        f"",
        f"Thèmes utilisés :",
    ]
    for theme, count in sorted(themes.items(), key=lambda x: -x[1]):
        report.append(f"  - {theme}: {count} vidéo(s)")

    return "\n".join(report)
