#!/usr/bin/env python3
"""
FTS5-Migration für Kapitel-Suche.

Dieses Skript erstellt eine virtuelle FTS5-Tabelle für die schnelle Volltextsuche
in Kapitel-Titeln und richtet automatische Trigger zur Synchronisation ein.
"""

from yt_database.database import db, Chapter
from loguru import logger


def migrate():
    """
    Führt die FTS5-Migration durch.
    Erstellt eine virtuelle FTS-Tabelle und die zugehörigen Trigger.
    """
    logger.info("Starte FTS5-Migration für Kapitel...")

    try:
        # 1. Virtuelle FTS-Tabelle erstellen (ohne ROWID-Verknüpfung)
        logger.info("Erstelle FTS5-Tabelle für Kapitel...")
        db.execute_sql("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chapter_fts USING fts5(
                chapter_id UNINDEXED,
                title
            );
        """)
        logger.debug("FTS5-Tabelle 'chapter_fts' erstellt.")

        # 2. Trigger für INSERT erstellen
        logger.info("Erstelle Trigger zur Synchronisation der FTS-Tabelle...")
        db.execute_sql("""
            CREATE TRIGGER IF NOT EXISTS chapter_ai AFTER INSERT ON chapter BEGIN
                INSERT INTO chapter_fts(chapter_id, title) VALUES (new.chapter_id, new.title);
            END;
        """)
        logger.debug("INSERT-Trigger erstellt.")

        # 3. Trigger für DELETE erstellen
        db.execute_sql("""
            CREATE TRIGGER IF NOT EXISTS chapter_ad AFTER DELETE ON chapter BEGIN
                DELETE FROM chapter_fts WHERE chapter_id = old.chapter_id;
            END;
        """)
        logger.debug("DELETE-Trigger erstellt.")

        # 4. Trigger für UPDATE erstellen
        db.execute_sql("""
            CREATE TRIGGER IF NOT EXISTS chapter_au AFTER UPDATE ON chapter BEGIN
                UPDATE chapter_fts SET title = new.title WHERE chapter_id = old.chapter_id;
            END;
        """)
        logger.debug("UPDATE-Trigger erstellt.")

        # 5. Existierende Daten laden
        logger.info("Fülle die FTS-Tabelle mit existierenden Daten...")
        db.execute_sql("""
            INSERT INTO chapter_fts(chapter_id, title)
            SELECT chapter_id, title FROM chapter;
        """)

        # Prüfe, wie viele Kapitel indexiert wurden
        result = db.execute_sql("SELECT COUNT(*) FROM chapter_fts").fetchone()
        chapter_count = result[0] if result else 0

        logger.success(f"FTS-Migration abgeschlossen! {chapter_count} Kapitel indexiert.")

    except Exception as e:
        logger.error(f"Fehler bei der FTS-Migration: {e}")
        raise


def verify_fts_setup():
    """
    Verifiziert, dass die FTS-Einrichtung korrekt funktioniert.
    """
    logger.info("Verifiziere FTS-Setup...")

    try:
        # Teste eine einfache Suche
        test_result = db.execute_sql(
            "SELECT COUNT(*) FROM chapter_fts WHERE chapter_fts MATCH 'test'"
        ).fetchone()

        # Prüfe die Anzahl der indexierten Kapitel
        total_chapters = db.execute_sql("SELECT COUNT(*) FROM chapter").fetchone()[0]
        indexed_chapters = db.execute_sql("SELECT COUNT(*) FROM chapter_fts").fetchone()[0]

        logger.info(f"Gesamt-Kapitel: {total_chapters}")
        logger.info(f"Indexierte Kapitel: {indexed_chapters}")

        if total_chapters == indexed_chapters:
            logger.success("FTS-Setup erfolgreich verifiziert!")
        else:
            logger.warning(f"Diskrepanz: {total_chapters - indexed_chapters} Kapitel nicht indexiert.")

    except Exception as e:
        logger.error(f"Fehler bei der Verifikation: {e}")


if __name__ == "__main__":
    try:
        migrate()
        verify_fts_setup()
    except Exception as e:
        logger.error(f"Migration fehlgeschlagen: {e}")
        exit(1)
