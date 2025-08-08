#!/usr/bin/env python3
"""
Kapitel-Statistiken Skript

Dieses Skript zeigt umfassende Statistiken über die in der Datenbank
gespeicherten Kapitel an, einschließlich:
- Gesamtanzahl der Transkripte und Kapitel
- Kapitel-Typen Aufschlüsselung
- Top-Videos mit den meisten Kapiteln
- Durchschnittswerte und Extremwerte

Usage:
    poetry run python scripts/chapter_statistics.py [--top N]
"""

import argparse
import sys
from pathlib import Path

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger
from yt_database.database import Chapter, Transcript


def analyze_chapter_statistics(top_count: int = 5) -> None:
    """
    Analysiert und zeigt Kapitel-Statistiken an.

    Args:
        top_count: Anzahl der Top-Videos, die angezeigt werden sollen
    """
    logger.info("Beginne Analyse der Kapitel-Statistiken...")

    # Grundlegende Statistiken
    total_transcripts = Transcript.select().count()
    total_chapters = Chapter.select().count()
    transcripts_with_chapters = Chapter.select(Chapter.transcript).distinct().count()

    print("DATENBANK-STATUS")
    print("=" * 50)
    print(f"Transkripte in DB: {total_transcripts}")
    print(f"Kapitel insgesamt: {total_chapters}")
    print(f"Transkripte mit Kapiteln: {transcripts_with_chapters}")
    print("=" * 50)

    # Kapitel-Typen aufschlüsseln
    youtube_chapters = Chapter.select().where(Chapter.chapter_type == 'youtube').count()
    detailed_chapters = Chapter.select().where(Chapter.chapter_type == 'detailed').count()

    print(f"YouTube-Kapitel: {youtube_chapters}")
    print(f"Detaillierte Kapitel: {detailed_chapters}")
    print("=" * 50)

    # Top-Videos mit den meisten Kapiteln
    print(f"TOP {top_count} TRANSKRIPTE MIT DEN MEISTEN KAPITELN:")

    # Alle Kapitel gruppiert nach video_id
    video_chapter_counts = {}
    for chapter in Chapter.select():
        video_id = chapter.transcript.video_id
        if video_id in video_chapter_counts:
            video_chapter_counts[video_id] += 1
        else:
            video_chapter_counts[video_id] = 1

    # Sortiert nach Anzahl der Kapitel
    sorted_videos = sorted(video_chapter_counts.items(), key=lambda x: x[1], reverse=True)

    for i, (video_id, count) in enumerate(sorted_videos[:top_count]):
        print(f"  {i+1}. {video_id}: {count} Kapitel")

    # Zusätzliche Statistiken
    if video_chapter_counts:
        avg_chapters = sum(video_chapter_counts.values()) / len(video_chapter_counts)
        max_chapters = max(video_chapter_counts.values())
        min_chapters = min(video_chapter_counts.values())

        print(f"\nZUSÄTZLICHE DETAILS:")
        print(f"Durchschnittliche Kapitel pro Video: {avg_chapters:.1f}")
        print(f"Videos mit den meisten Kapiteln haben: {max_chapters} Kapitel")
        print(f"Videos mit den wenigsten Kapiteln haben: {min_chapters} Kapitel")

        # Verteilungsstatistiken
        sorted_counts = sorted(video_chapter_counts.values(), reverse=True)
        median_chapters = sorted_counts[len(sorted_counts) // 2]

        print(f"Median-Kapitelanzahl: {median_chapters}")
        print(f"Videos mit über 100 Kapiteln: {sum(1 for count in video_chapter_counts.values() if count > 100)}")
        print(f"Videos mit unter 10 Kapiteln: {sum(1 for count in video_chapter_counts.values() if count < 10)}")

    logger.success("Kapitel-Statistiken erfolgreich generiert!")


def main() -> None:
    """Hauptfunktion des Skripts."""
    parser = argparse.ArgumentParser(
        description="Zeigt umfassende Statistiken über Kapitel in der Datenbank an"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Anzahl der Top-Videos, die angezeigt werden sollen (Standard: 5)"
    )

    args = parser.parse_args()

    # Loguru-Konfiguration
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )

    try:
        analyze_chapter_statistics(args.top)
    except Exception as e:
        logger.error(f"Fehler bei der Statistik-Generierung: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
