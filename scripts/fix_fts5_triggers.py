#!/usr/bin/env python3
"""
Reparatur-Skript für FTS5-Trigger in bestehenden Datenbanken.

Dieses Skript behebt das Problem mit fehlerhaften SQL-Triggern, die auf
nicht existierende Spalten 'old.id' und 'new.id' verweisen, anstatt
'old.chapter_id' und 'new.chapter_id' zu verwenden.
"""

import os
import sys

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from loguru import logger
from yt_database.database import db


def fix_fts5_triggers():
    """Repariert die FTS5-Trigger für die Kapitel-Suche."""
    logger.info("Starte Reparatur der FTS5-Trigger...")

    try:
        with db:
            # Lösche existierende FTS5-Strukturen komplett
            logger.info("Lösche existierende FTS5-Strukturen...")
            db.execute_sql("DROP TABLE IF EXISTS chapter_fts;")
            db.execute_sql("DROP TRIGGER IF EXISTS chapter_ai;")
            db.execute_sql("DROP TRIGGER IF EXISTS chapter_ad;")
            db.execute_sql("DROP TRIGGER IF EXISTS chapter_au;")

            # Erstelle neue FTS5-Tabelle (UUID-kompatibel)
            logger.info("Erstelle neue FTS5-Tabelle...")
            db.execute_sql("""
                CREATE VIRTUAL TABLE chapter_fts USING fts5(
                    chapter_id UNINDEXED,
                    title
                );
            """)

            # Erstelle korrekte Trigger
            logger.info("Erstelle korrekte Trigger...")
            db.execute_sql("""
                CREATE TRIGGER chapter_ai AFTER INSERT ON chapter BEGIN
                    INSERT INTO chapter_fts(chapter_id, title) VALUES (new.chapter_id, new.title);
                END;
            """)

            db.execute_sql("""
                CREATE TRIGGER chapter_ad AFTER DELETE ON chapter BEGIN
                    DELETE FROM chapter_fts WHERE chapter_id = old.chapter_id;
                END;
            """)

            db.execute_sql("""
                CREATE TRIGGER chapter_au AFTER UPDATE ON chapter BEGIN
                    DELETE FROM chapter_fts WHERE chapter_id = old.chapter_id;
                    INSERT INTO chapter_fts(chapter_id, title) VALUES (new.chapter_id, new.title);
                END;
            """)

            # Fülle FTS5-Tabelle mit existierenden Kapiteln
            logger.info("Fülle FTS5-Index mit existierenden Kapiteln...")
            cursor = db.execute_sql("SELECT chapter_id, title FROM chapter;")
            chapters = cursor.fetchall()

            # Verwende Batch-Insert für bessere Performance
            insert_data = []
            for chapter_id, title in chapters:
                insert_data.append((chapter_id, title))

            # Batch-Insert ausführen
            with db.atomic():
                for chapter_id, title in insert_data:
                    db.execute_sql(
                        "INSERT INTO chapter_fts(chapter_id, title) VALUES (?, ?);",
                        (chapter_id, title)
                    )

            # Commit sicherstellen
            db.commit()

            # Prüfe Ergebnis
            verify_cursor = db.execute_sql("SELECT COUNT(*) FROM chapter_fts;")
            actual_count = verify_cursor.fetchone()[0]

            logger.info(f"{len(chapters)} Kapitel verarbeitet, {actual_count} in FTS5-Index vorhanden.")

        logger.success("FTS5-Trigger erfolgreich repariert!")

    except Exception as e:
        logger.error(f"Fehler beim Reparieren der FTS5-Trigger: {e}")
        return False

    return True


def main():
    """Hauptfunktion des Reparatur-Skripts."""
    logger.info("=== FTS5-Trigger Reparatur-Skript ===")

    if fix_fts5_triggers():
        logger.success("Reparatur erfolgreich abgeschlossen!")
        return 0
    else:
        logger.error("Reparatur fehlgeschlagen!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
