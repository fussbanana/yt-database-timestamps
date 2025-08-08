#!/usr/bin/env python3
"""Test-Script für Chapter-Writing-Funktionalität."""

from yt_database.services.chapter_generation_worker import ChapterGenerationWorker

def test_chapter_placeholder_determination():
    """Teste die Platzhalter-Bestimmung."""

    # Test 1: YouTube-Kommentar-Typ
    worker1 = ChapterGenerationWorker(
        video_id="test123",
        file_path="/tmp/test.md",
        file_service=None,
        pm_service=None,
        prompt_type="youtube_comment"
    )
    placeholder1 = worker1._determine_chapter_placeholder()
    print(f"YouTube-Kommentar Typ → Platzhalter: '{placeholder1}'")
    assert placeholder1 == "## Kapitel mit Zeitstempeln"

    # Test 2: Detaillierter Datenbank-Typ
    worker2 = ChapterGenerationWorker(
        video_id="test456",
        file_path="/tmp/test2.md",
        file_service=None,
        pm_service=None,
        prompt_type="detailed_database"
    )
    placeholder2 = worker2._determine_chapter_placeholder()
    print(f"Detailed Database Typ → Platzhalter: '{placeholder2}'")
    assert placeholder2 == "## Detaillierte Kapitel"

    # Test 3: Fallback ohne Typ
    worker3 = ChapterGenerationWorker(
        video_id="test789",
        file_path="/tmp/test3.md",
        file_service=None,
        pm_service=None,
        prompt_type=None
    )
    placeholder3 = worker3._determine_chapter_placeholder()
    print(f"Kein Typ (Fallback) → Platzhalter: '{placeholder3}'")
    assert placeholder3 == "## Detaillierte Kapitel"

    print("Alle Platzhalter-Tests bestanden!")

def test_chapter_type_determination():
    """Teste die Bestimmung des Datenbanktyps."""

    # Test 1: YouTube-Kommentar → summary
    worker1 = ChapterGenerationWorker(
        video_id="test123",
        file_path="/tmp/test.md",
        file_service=None,
        pm_service=None,
        prompt_type="youtube_comment"
    )
    db_type1 = worker1._determine_chapter_type_for_database()
    print(f"YouTube-Kommentar Typ → DB-Typ: '{db_type1}'")
    assert db_type1 == "summary"

    # Test 2: Detailliert → detailed
    worker2 = ChapterGenerationWorker(
        video_id="test456",
        file_path="/tmp/test2.md",
        file_service=None,
        pm_service=None,
        prompt_type="detailed_database"
    )
    db_type2 = worker2._determine_chapter_type_for_database()
    print(f"Detailed Database Typ → DB-Typ: '{db_type2}'")
    assert db_type2 == "detailed"

    print("Alle Datenbanktyp-Tests bestanden!")

if __name__ == "__main__":
    test_chapter_placeholder_determination()
    test_chapter_type_determination()
    print("\nAlle Tests für Chapter Writing erfolgreich!")
