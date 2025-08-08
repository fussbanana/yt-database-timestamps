#!/usr/bin/env python3
"""
Dieses Modul definiert die Datenbankstruktur für das YouTube-Datenbankprojekt mittels Peewee ORM.

Die Struktur ist transcript-zentriert. Die Haupttabelle `Transcript` speichert die Metadaten
zu einem Transkript, das durch die `video_id` seiner YouTube-Quelle eindeutig identifiziert wird.
"""

import os
import uuid

from loguru import logger
from peewee import (
    BooleanField,
    CharField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
    TextField,
    UUIDField,
)

# Pfad zur Datenbank-Datei im Hauptverzeichnis des Projekts
DATABASE_PATH = os.path.join(os.getcwd(), "yt_database.db")
db = SqliteDatabase(DATABASE_PATH)


class BaseModel(Model):
    """Basisklasse für alle Datenbankmodelle."""

    class Meta:
        database = db


class Channel(BaseModel):
    """Tabelle zur Speicherung von Kanal-Informationen."""

    channel_id = CharField(primary_key=True, help_text="Eindeutige YouTube-Kanal-ID")
    name = CharField(help_text="Name des Kanals")
    url = CharField(unique=True, help_text="URL des Kanals")
    handle = CharField(null=True, help_text="Handle des Kanals (z.B. @handle)")


class Transcript(BaseModel):
    """
    Zentrale Tabelle zur Speicherung von Transkript-Metadaten.
    Jeder Eintrag repräsentiert ein Transkript von einem bestimmten YouTube-Video.
    """

    title = TextField(help_text="Titel des Quell-Videos")
    video_id = CharField(primary_key=True, help_text="Eindeutige YouTube-Video-ID, die als ID für das Transkript dient")
    video_url = CharField(unique=True, help_text="URL des Quell-Videos")
    duration = IntegerField(default=0, help_text="Dauer in Sekunden")
    chapter_count = IntegerField(default=0, help_text="Anzahl der einfachen Kapitel (YouTube-Kommentar-Format)")
    detailed_chapter_count = IntegerField(default=0, help_text="Anzahl der detaillierten Kapitel (Datenbank-Format)")
    has_chapters = BooleanField(default=False, index=True, help_text="Status, ob Kapitel vorhanden sind")
    is_transcribed = BooleanField(default=False, index=True, help_text="Status, ob der Transkript-Text vorhanden ist")
    transcript_lines = IntegerField(default=0, help_text="Anzahl der Transkriptzeilen")
    channel = ForeignKeyField(Channel, backref="transcripts", on_delete="CASCADE", help_text="Referenz zum Kanal")
    publish_date = CharField(null=True, help_text="Veröffentlichungsdatum (YYYYMMDD)")
    online = BooleanField(default=False, help_text="Status, ob das Quell-Video online verfügbar ist")
    error_reason = TextField(null=True, help_text="Fehlermeldung bei der Verarbeitung")


class Chapter(BaseModel):
    """Tabelle zur Speicherung von Kapiteln, die zu einem Transkript gehören."""

    chapter_id = UUIDField(primary_key=True, default=uuid.uuid4)
    transcript = ForeignKeyField(
        Transcript, backref="chapters", on_delete="CASCADE", help_text="Referenz zum Transkript"
    )
    title = TextField(help_text="Titel des Kapitels")
    start_seconds = IntegerField(help_text="Startzeit des Kapitels in Sekunden")
    chapter_type = CharField(help_text="Typ des Kapitels (z.B. 'summary' oder 'detailed')")


def initialize_database() -> None:
    """Erstellt die Datenbanktabellen, falls sie nicht existieren."""
    logger.info("Initialisiere Datenbank und erstelle Tabellen falls nötig.")
    if not os.path.exists(DATABASE_PATH):
        logger.info(f"Erstelle neue Datenbankdatei unter: {DATABASE_PATH}")
    else:
        logger.info(f"Verwende existierende Datenbankdatei unter: {DATABASE_PATH}")

    with db:
        db.create_tables([Channel, Transcript, Chapter], safe=True)
        _setup_fts5_search()
    logger.debug("Datenbank initialisiert und Tabellen erstellt.")


def _setup_fts5_search() -> None:
    """Erstellt die FTS5-Tabelle und korrekte Trigger für die Kapitel-Suche."""
    try:
        # Prüfe, ob die FTS5-Tabelle bereits existiert
        cursor = db.execute_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='chapter_fts';")
        fts_exists = cursor.fetchone() is not None

        if fts_exists:
            logger.debug("FTS5-Tabelle chapter_fts existiert bereits - überspringe Erstellung.")
            return

        # Lösche existierende Trigger für einen sauberen Neustart (falls welche existieren)
        db.execute_sql("DROP TRIGGER IF EXISTS chapter_ai;")
        db.execute_sql("DROP TRIGGER IF EXISTS chapter_ad;")
        db.execute_sql("DROP TRIGGER IF EXISTS chapter_au;")

        # Erstelle FTS5-Tabelle für Kapitel-Suche (ohne content/content_rowid für UUID-Kompatibilität)
        db.execute_sql(
            """
            CREATE VIRTUAL TABLE chapter_fts USING fts5(
                chapter_id UNINDEXED,
                title
            );
        """
        )

        # Erstelle Trigger mit chapter_id als Referenz
        db.execute_sql(
            """
            CREATE TRIGGER chapter_ai AFTER INSERT ON chapter BEGIN
                INSERT INTO chapter_fts(chapter_id, title) VALUES (new.chapter_id, new.title);
            END;
        """
        )

        db.execute_sql(
            """
            CREATE TRIGGER chapter_ad AFTER DELETE ON chapter BEGIN
                DELETE FROM chapter_fts WHERE chapter_id = old.chapter_id;
            END;
        """
        )

        db.execute_sql(
            """
            CREATE TRIGGER chapter_au AFTER UPDATE ON chapter BEGIN
                DELETE FROM chapter_fts WHERE chapter_id = old.chapter_id;
                INSERT INTO chapter_fts(chapter_id, title) VALUES (new.chapter_id, new.title);
            END;
        """
        )

        logger.debug("FTS5-Tabelle und Trigger für Kapitel-Suche erfolgreich erstellt.")

    except Exception as e:
        logger.warning(f"Fehler beim Erstellen der FTS5-Suche: {e}")
        # Nicht kritisch, da die Suche optional ist


# Automatische Initialisierung beim Import
initialize_database()

if __name__ == "__main__":
    print("Datenbank initialisiert.")
