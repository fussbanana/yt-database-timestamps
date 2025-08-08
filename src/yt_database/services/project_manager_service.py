"""
Service zur Verwaltung und Synchronisation von YouTube-Projekten und Metadaten über eine SQLite-Datenbank.

Dieser Service kapselt alle Operationen rund um Kanäle, Videos und Transkripte:
- Hinzufügen, Aktualisieren und Status-Tracking von Kanälen und Videos
- Synchronisation mit der Datenbank
- Verwaltung der Projektstruktur und Dateipfade
- Schreiben von Transkripten mit Status in Markdown

Die Datei ist vollständig nach Google-Style dokumentiert und enthält strategische Debug-Logs sowie Inline-Kommentare für alle nicht-trivialen Zeilen.
"""

import os
from typing import List, Optional

import yaml
from loguru import logger

from yt_database.config.settings import Settings
from yt_database.database import Channel, Chapter, Transcript, db
from yt_database.models.models import ChapterEntry, TranscriptData
from yt_database.models.search_models import SearchResult
from yt_database.services.protocols import ProjectManagerProtocol
from yt_database.utils.transcript_for_video_id_util import get_transcript_path_for_video_id
from yt_database.utils.utils import (
    get_or_set_frontmatter_value,
    has_content_after_marker,
    to_snake_case,
)


class ProjectManagerService(ProjectManagerProtocol):
    """
    Service zur Verwaltung, Synchronisation und Statuspflege von YouTube-Kanälen, Videos und Transkripten.

    Kapselt alle datenbankbezogenen und dateibezogenen Operationen für Projekte, Kanäle, Videos und Transkripte.
    Bietet Methoden zur Erstellung, Aktualisierung, Statusabfrage und Suche.

    Attributes:
        file_service (FileService): Service für Dateioperationen (z.B. Schreiben von Transkripten).
        settings (Settings): Globale Konfiguration für Projektpfade und weitere Einstellungen.
    """

    def __init__(self, settings: Settings, file_service) -> None:
        """
        Initialisiert den ProjectManagerService mit Settings und FileService.

        Args:
            settings (Settings): Globale Konfiguration für Projektpfade und weitere Einstellungen.
            file_service: Service für Dateioperationen.
        """
        self.settings = settings
        self.file_service = file_service
        logger.debug("ProjectManagerService (SQLite-Backend, Pydantic Settings) initialisiert.")

    def get_all_channels(self) -> List[Channel]:
        """
        Gibt alle Kanäle aus der Datenbank zurück.

        Returns:
            List[Channel]: Liste aller Channel-Objekte.
        """
        logger.debug("Hole alle Kanäle aus der Datenbank.")
        return list(Channel.select())

    def create_project(self, id: str, video_id: str) -> None:
        """
        Erstellt ein Projektverzeichnis für einen Kanal und ein Video.

        Args:
            id (str): Kanal-ID.
            video_id (str): Video-ID.
        """
        projects_dir = self.settings.project_path
        project_dir = os.path.join(projects_dir, id, video_id)
        os.makedirs(project_dir, exist_ok=True)
        logger.debug(f"Projektverzeichnis erstellt: {project_dir}")

    def update_index(self, transcript_data: TranscriptData) -> None:
        """
        Erstellt oder aktualisiert einen Transcript-Eintrag in der Datenbank und markiert ihn als transkribiert.

        Args:
            transcript_data (TranscriptData): Pydantic-Modell mit Transcript- und Transkript-Daten.
        """
        logger.debug(f"Aktualisiere Transcript-Index für {transcript_data.video_id}")
        with db.atomic():
            channel, _ = Channel.get_or_create(
                channel_id=transcript_data.channel_id,
                defaults={
                    "name": transcript_data.channel_name,
                    "url": transcript_data.channel_url,
                    "handle": transcript_data.channel_handle,
                },
            )
            # Transcript.replace sorgt für Upsert (insert or update)
            Transcript.replace(
                video_id=transcript_data.video_id,
                channel=channel,
                video_url=transcript_data.video_url,
                title=transcript_data.title,
                publish_date=transcript_data.publish_date,
                duration=transcript_data.duration,
                transcript_lines=len(transcript_data.entries),
                is_transcribed=True,
                has_chapters=bool(transcript_data.chapters),
            ).execute()
        logger.debug(f"Index für Transcript {transcript_data.video_id} aktualisiert und als transkribiert markiert.")

    def add_video_metadata(self, transcript_data: TranscriptData) -> None:
        """
        Erstellt oder aktualisiert nur die Metadaten eines Videos in der Datenbank,
        ohne den is_transcribed-Status zu verändern.

        Args:
            transcript_data (TranscriptData): Pydantic-Modell mit Transcript-Metadaten.
        """
        logger.debug(f"Speichere Transcript-Metadaten für {transcript_data.video_id}")
        with db.atomic():
            channel, _ = Channel.get_or_create(
                channel_id=transcript_data.channel_id,
                defaults={
                    "name": transcript_data.channel_name,
                    "url": transcript_data.channel_url,
                    "handle": transcript_data.channel_handle,
                },
            )
            existing_video = Transcript.get_or_none(video_id=transcript_data.video_id)
            current_transcribed_status = existing_video.is_transcribed if existing_video else False
            Transcript.replace(
                video_id=transcript_data.video_id,
                channel=channel,
                video_url=transcript_data.video_url,
                title=transcript_data.title,
                publish_date=transcript_data.publish_date,
                duration=transcript_data.duration,
                is_transcribed=current_transcribed_status,
                has_chapters=bool(transcript_data.chapters),
            ).execute()
        logger.debug(
            f"Transcript-Metadaten für {transcript_data.video_id} gespeichert (is_transcribed={current_transcribed_status})."
        )

    def has_transcript_lines(self, video_id: str) -> bool:
        """
        Prüft, ob für ein Video ein Transkript inhaltlich vorhanden ist.

        Args:
            video_id (str): Die Video-ID.

        Returns:
            bool: True, wenn Transkriptzeilen vorhanden sind, sonst False.
        """
        video = Transcript.get_or_none(video_id=video_id)
        if not video:
            return False
        has_transcript_lines = video.transcript_lines > 0
        logger.debug(
            f"Transcript-Status für {video_id}: transcript_lines={video.transcript_lines}, "
            f"is_transcribed_flag={video.is_transcribed}, result={has_transcript_lines}"
        )
        return has_transcript_lines

    def mark_as_chaptered(self, video_id: str) -> None:
        """
        Markiert ein Transcript als 'mit Kapiteln versehen' und als transkribiert in der Datenbank.

        Args:
            video_id (str): Die Video-ID.
        """
        logger.debug(
            f"Markiere Transcript {video_id} als 'mit Kapiteln versehen' und als transkribiert in der Datenbank."
        )
        try:
            updated_rows = (
                Transcript.update(has_chapters=True, is_transcribed=True)
                .where(Transcript.video_id == video_id)
                .execute()
            )
            if updated_rows > 0:
                logger.debug(f"Transcript {video_id} erfolgreich als 'mit Kapiteln' und 'transkribiert' markiert.")
            else:
                logger.warning(f"Transcript {video_id} nicht in der Datenbank gefunden.")
        except Exception as e:
            logger.error(f"Fehler beim Markieren von Transcript {video_id}: {e}")

    def get_chapters_for_video(self, video_id: str) -> list:
        """
        Holt alle Kapitel für ein Transcript aus der Datenbank.

        Args:
            video_id (str): Die Video-ID.

        Returns:
            list: Liste von ChapterEntry-Objekten.
        """
        try:
            chapters = []
            chapter_records = Chapter.select().where(Chapter.transcript == video_id).order_by(Chapter.chapter_id)
            for record in chapter_records:
                start_hms = getattr(record, "start", "00:00:00")
                end_hms = getattr(record, "end", "00:00:00")
                chapter = ChapterEntry(
                    title=record.title,
                    start=self._parse_timestamp(start_hms),
                    end=self._parse_timestamp(end_hms),
                    start_hms=start_hms,
                    end_hms=end_hms,
                )
                chapters.append(chapter)
            return chapters
        except Exception as e:
            logger.error(f"Fehler beim Laden der Kapitel für Transcript {video_id}: {e}")
            return []

    def _parse_timestamp(self, timestamp: str) -> float:
        """
        Konvertiert einen Zeitstempel-String ("HH:MM:SS" oder "MM:SS") in Sekunden.

        Args:
            timestamp (str): Zeitstempel als String.

        Returns:
            float: Zeit in Sekunden.
        """
        try:
            parts = timestamp.split(":")
            if len(parts) == 2:  # MM:SS
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:  # HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except (ValueError, IndexError):
            logger.warning(f"Konnte Timestamp nicht parsen: {timestamp}")
        return 0.0

    def write_transcript_with_status(self, video_id: str, formatted: str, metadata: dict) -> None:
        """
        Schreibt das Transkript inkl. YAML-Frontmatter und Status-Feldern (transcript, chapters) in die Markdown-Datei.

        Args:
            video_id (str): Video-ID.
            formatted (str): Formatierter Transkript-Text (ohne YAML-Frontmatter).
            metadata (dict): Basis-Metadaten (z.B. von YoutubeMetadataService).
        """
        logger.debug(f"Schreibe Transkript mit Status für Transcript {video_id}.")
        transcript = has_content_after_marker(formatted, "## Transkript")
        chapters = has_content_after_marker(formatted, "## Kapitel mit Zeitstempeln")
        online = get_or_set_frontmatter_value(formatted, "Online", default=False)
        yaml_metadata = {
            "Transcript-Titel": metadata.get("video_titel", ""),
            "Transcript-ID": metadata.get("video_id", video_id),
            "YouTube-URL": metadata.get("youtube_url", ""),
            "Veröffentlichungsdatum": metadata.get("veroeffentlichungsdatum", ""),
            "Dauer": metadata.get("dauer", ""),
            "Kanalname": metadata.get("kanalname", ""),
            "Transkript": transcript,
            "Kapitel": chapters,
            "Online": online,
        }
        yaml_frontmatter = (
            "---\n" + yaml.safe_dump(yaml_metadata, default_flow_style=False, allow_unicode=True) + "---\n\n"
        )
        full_content = yaml_frontmatter + formatted
        channel_folder = metadata["id"]
        safe_title = to_snake_case(metadata.get("video_titel", "unbekannt"))
        projects_dir = self.settings.project_path
        filename = f"{projects_dir}/{channel_folder}/{video_id}/{safe_title}_transcript.md"
        self.file_service.write(filename, full_content)
        logger.debug(f"Transkript mit Status geschrieben: {filename}")

    def get_transcript_path_for_video_id(self, video_id: str, channel_handle: Optional[str] = None) -> str:
        """
        Gibt den Pfad zur Transkriptdatei für ein Video zurück.

        Args:
            video_id (str): Video-ID.
            channel_handle (Optional[str]): Optionaler Kanal-Handle. Falls nicht angegeben, wird er aus der DB ermittelt.

        Returns:
            str: Pfad zur Transkriptdatei oder leerer String, falls nicht gefunden.
        """
        logger.debug(f"Hole Transkript-Pfad für Transcript {video_id}.")
        projects_dir = self.settings.project_path
        handle = channel_handle
        if handle is None:
            video = Transcript.get_or_none(video_id=video_id)
            if video and hasattr(video, "channel") and video.channel:
                handle = video.channel.handle
        if not handle:
            logger.trace(f"Kanal-Handle für Transcript {video_id} nicht gefunden.")
            return ""
        path = get_transcript_path_for_video_id(projects_dir, handle, video_id)
        return path or ""

    def get_videos_for_channel(self, channel_id: str) -> List[Transcript]:
        """
        Gibt alle Videos für einen bestimmten Kanal aus der Datenbank zurück.

        Args:
            channel_id (str): Die Kanal-ID.

        Returns:
            List[Transcript]: Liste der Transcript-Objekte für den Kanal.
        """
        logger.debug(f"Hole alle Videos für Kanal {channel_id} aus der Datenbank.")
        return list(Transcript.select().join(Channel).where(Channel.channel_id == channel_id))

    def get_all_videos(self) -> List[Transcript]:
        """
        Gibt alle Videos aus der Datenbank zurück.

        Returns:
            List[Transcript]: Liste aller Transcript-Objekte in der Datenbank.
        """
        logger.debug("Hole alle Videos aus der Datenbank.")
        return list(Transcript.select())

    def get_videos_without_transcript_or_chapters(self) -> List[Transcript]:
        """
        Gibt alle Videos zurück, die noch kein Transkript oder keine Kapitel haben.
        (Vereinfachte Version: Prüft nur auf Kapitel in der Datenbank.)

        Returns:
            List[Transcript]: Liste der Transcript-Objekte ohne Transkript oder Kapitel.
        """
        logger.debug("Hole Videos ohne Transkript oder Kapitel aus der Datenbank.")
        videos = []
        for video in Transcript.select():
            db_chapters = self.get_chapters_for_video(str(video.video_id))
            has_chapters = bool(db_chapters)
            if not has_chapters:
                videos.append(video)
        return videos

    def videos_to_transcript_data(self, videos: List[Transcript]) -> List[TranscriptData]:
        """
        Konvertiert eine Liste von Transcript-Objekten zu TranscriptData-Objekten.

        Args:
            videos (List[Transcript]): Liste der Transcript-Objekte aus der Datenbank.

        Returns:
            List[TranscriptData]: Liste der TranscriptData-Objekte.
        """
        transcript_data_list = []
        for video in videos:
            channel = video.channel
            transcript_data = TranscriptData(
                video_id=str(video.video_id),
                channel_id=str(channel.channel_id),
                channel_name=str(channel.name),
                channel_url=str(channel.url),
                channel_handle=getattr(channel, "channel_handle", ""),
                video_url=f"https://www.youtube.com/watch?v={video.video_id}",
                title=str(video.title),
                publish_date=str(video.publish_date),
                duration=str(video.duration),
                entries=[],
                chapters=[],
                error_reason="",
            )
            transcript_data_list.append(transcript_data)
        return transcript_data_list

    def save_chapters_to_database(
        self, video_id: str, chapters: List[ChapterEntry], chapter_type: str = "detailed"
    ) -> None:
        """
        Speichert eine Liste von ChapterEntry-Objekten für ein Transcript in der Datenbank.

        Args:
            video_id (str): Die Video-ID.
            chapters (List[ChapterEntry]): Liste der Kapitelobjekte.
            chapter_type (str): Der Typ der Kapitel ("summary" oder "detailed").
        """
        logger.debug(
            f"Speichere {len(chapters)} Kapitel vom Typ '{chapter_type}' für Transcript {video_id} in der Datenbank."
        )
        try:
            with db.atomic():
                transcript_obj = Transcript.get(Transcript.video_id == video_id)
                # Lösche existierende Kapitel des gleichen Typs
                Chapter.delete().where(
                    (Chapter.transcript == transcript_obj) & (Chapter.chapter_type == chapter_type)
                ).execute()
                for chapter in chapters:
                    Chapter.create(
                        transcript=transcript_obj,
                        title=chapter.title,
                        start_seconds=int(chapter.start),
                        chapter_type=chapter_type,
                    )
                # Aktualisiere Kapitelzähler im Transcript
                if chapter_type == "summary":
                    Transcript.update(has_chapters=True, chapter_count=len(chapters)).where(
                        Transcript.video_id == video_id
                    ).execute()
                else:
                    Transcript.update(has_chapters=True, detailed_chapter_count=len(chapters)).where(
                        Transcript.video_id == video_id
                    ).execute()
            logger.debug(f"Kapitel für Transcript {video_id} erfolgreich gespeichert.")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Kapitel für Transcript {video_id}: {e}")
            raise

    def create_transcript_data_for_batch(self, channel_url: str, video_ids: list[str]) -> list[TranscriptData]:
        """
        Erstellt eine Liste von initialen TranscriptData-Objekten für einen Batch-Lauf.

        Args:
            channel_url (str): Die URL des Kanals.
            video_ids (list[str]): Eine Liste von Video-IDs.

        Returns:
            list[TranscriptData]: Eine Liste von vorbereiteten TranscriptData-Objekten.
        """
        logger.debug(f"Erstelle TranscriptData-Objekte für Batch-Lauf für Kanal: {channel_url}")
        try:
            channel = Channel.get(Channel.url == channel_url)
        except Exception:
            logger.error(f"Kanal mit URL {channel_url} nicht in der Datenbank gefunden.")
            channel_id_from_url = channel_url.split("/")[-1]
            channel, _ = Channel.get_or_create(
                url=channel_url,
                defaults={
                    "channel_id": channel_id_from_url,
                    "name": "Unbekannter Kanal",
                    "handle": channel_id_from_url,
                },
            )
            logger.warning(f"Platzhalter-Kanal '{channel.name}' für URL {channel_url} erstellt.")
        prepared_data = []
        for video_id in video_ids:
            data = TranscriptData(
                video_id=video_id,
                channel_id=channel.channel_id,
                channel_name=channel.name,
                channel_url=channel.url,
                channel_handle=getattr(channel, "handle", ""),
                video_url=f"https://www.youtube.com/watch?v={video_id}",
            )
            prepared_data.append(data)
        logger.info(f"{len(prepared_data)} TranscriptData-Objekte für den Batch-Lauf vorbereitet.")
        return prepared_data

    def create_transcript_data_for_single(self, video_id: str) -> TranscriptData:
        """
        Erstellt ein TranscriptData-Objekt für eine einzelne Video-ID.

        Args:
            video_id (str): Die Video-ID.

        Returns:
            TranscriptData: Ein vorbereitetes TranscriptData-Objekt.
        """
        logger.debug(f"Erstelle TranscriptData-Objekt für Video: {video_id}")
        try:
            video = Transcript.get(Transcript.video_id == video_id)
            channel = video.channel
            data = TranscriptData(
                video_id=video_id,
                channel_id=channel.channel_id,
                channel_name=channel.name,
                channel_url=channel.url,
                channel_handle=getattr(channel, "handle", ""),
                video_url=f"https://www.youtube.com/watch?v={video_id}",
                title=video.title or "",
                publish_date=str(video.publish_date) if video.publish_date else "",
                duration=str(video.duration) if video.duration else "",
            )
            logger.debug(f"TranscriptData-Objekt für Video {video_id} erstellt.")
            return data
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des TranscriptData-Objekts für Video {video_id}: {e}")
            return TranscriptData(
                video_id=video_id,
                channel_id="unknown",
                channel_name="Unbekannter Kanal",
                channel_url="",
                channel_handle="",
                video_url=f"https://www.youtube.com/watch?v={video_id}",
                error_reason=f"Video nicht in Datenbank gefunden: {e}",
            )

    def search_chapters(self, query: str, limit: int = 50) -> List[SearchResult]:
        """
        Durchsucht Kapitel-Titel mit FTS5 und gibt strukturierte Ergebnisse zurück.

        Args:
            query (str): Das zu suchende Stichwort. FTS5-Syntax wird unterstützt.
            limit (int): Maximale Anzahl der Ergebnisse.

        Returns:
            List[SearchResult]: Eine Liste von typsicheren Suchergebnis-Objekten.
        """
        logger.info(f"Suche nach Kapiteln mit Stichwort: '{query}'")
        try:
            # FTS5-Suche durchführen und mit Chapter- und Transcript-Daten verknüpfen
            sql = """
                SELECT
                    c.title as chapter_title,
                    c.start_seconds,
                    t.title as video_title,
                    t.video_url,
                    ch.name as channel_name,
                    ch.handle as channel_handle,
                    c.chapter_id
                FROM chapter_fts cf
                JOIN chapter c ON cf.chapter_id = c.chapter_id
                JOIN transcript t ON c.transcript_id = t.video_id
                JOIN channel ch ON t.channel_id = ch.channel_id
                WHERE chapter_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """
            cursor = db.execute_sql(sql, (query, limit))
            results = []
            for row in cursor.fetchall():
                chapter_title, start_seconds, video_title, video_url, channel_name, channel_handle, chapter_id = row
                timestamp_url = f"{video_url}&t={start_seconds}s"
                start_time_str = self._seconds_to_hms(start_seconds)
                results.append(
                    SearchResult(
                        video_title=video_title,
                        channel_name=channel_name,
                        channel_handle=channel_handle,
                        chapter_title=chapter_title,
                        timestamp_url=timestamp_url,
                        start_time_str=start_time_str,
                    )
                )
            logger.info(f"{len(results)} Ergebnisse für '{query}' gefunden.")
            return results
        except Exception as e:
            logger.error(f"Fehler bei der Kapitel-Suche: {e}")
            return []

    def _seconds_to_hms(self, seconds: int) -> str:
        """
        Hilfsmethode zur Konvertierung von Sekunden in HH:MM:SS.

        Args:
            seconds (int): Zeit in Sekunden.

        Returns:
            str: Zeit als HH:MM:SS-String.
        """
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def delete_video_safe(self, video_id: str) -> dict:
        """
        Löscht ein Video und alle zugehörigen Kapitel sicher mit Statistiken.

        Args:
            video_id (str): Die Video-ID.

        Returns:
            dict: Statistiken über die Löschung oder Fehlerinformation.
        """
        try:
            video = Transcript.get_or_none(video_id=video_id)
            if not video:
                return {"success": False, "error": f"Video {video_id} nicht gefunden."}

            # Statistiken sammeln
            chapter_count = Chapter.select().where(Chapter.transcript == video).count()
            video_title = video.title
            channel_name = video.channel.name if video.channel else "Unbekannt"

            # Löschung durchführen (CASCADE löscht automatisch die Kapitel)
            video.delete_instance(recursive=True)

            logger.info(f"Video '{video_title}' ({video_id}) mit {chapter_count} Kapiteln gelöscht.")

            return {
                "success": True,
                "video_title": video_title,
                "channel_name": channel_name,
                "chapters_deleted": chapter_count,
                "message": f"Video '{video_title}' und {chapter_count} Kapitel erfolgreich gelöscht.",
            }

        except Exception as e:
            logger.error(f"Fehler beim Löschen von Video {video_id}: {e}")
            return {"success": False, "error": f"Fehler beim Löschen: {e}"}

    def delete_channel_safe(self, channel_id: str) -> dict:
        """
        Löscht einen Kanal und alle zugehörigen Videos/Kapitel sicher mit Statistiken.

        Args:
            channel_id (str): Die Kanal-ID.

        Returns:
            dict: Statistiken über die Löschung oder Fehlerinformation.
        """
        try:
            channel = Channel.get_or_none(channel_id=channel_id)
            if not channel:
                return {"success": False, "error": f"Kanal {channel_id} nicht gefunden."}

            # Statistiken sammeln
            video_count = Transcript.select().where(Transcript.channel == channel).count()
            chapter_count = Chapter.select().join(Transcript).where(Transcript.channel == channel).count()
            channel_name = channel.name

            # Löschung durchführen (CASCADE löscht automatisch Videos und Kapitel)
            channel.delete_instance(recursive=True)

            logger.info(
                f"Kanal '{channel_name}' ({channel_id}) mit {video_count} Videos und {chapter_count} Kapiteln gelöscht."
            )

            return {
                "success": True,
                "channel_name": channel_name,
                "videos_deleted": video_count,
                "chapters_deleted": chapter_count,
                "message": f"Kanal '{channel_name}' mit {video_count} Videos und {chapter_count} Kapiteln erfolgreich gelöscht.",
            }

        except Exception as e:
            logger.error(f"Fehler beim Löschen von Kanal {channel_id}: {e}")
            return {"success": False, "error": f"Fehler beim Löschen: {e}"}

    def delete_chapters_safe(self, video_id: str, chapter_type: Optional[str] = None) -> dict:
        """
        Löscht Kapitel eines Videos sicher mit Statistiken.

        Args:
            video_id (str): Die Video-ID.
            chapter_type (str, optional): Typ der zu löschenden Kapitel.

        Returns:
            dict: Statistiken über die Löschung oder Fehlerinformation.
        """
        try:
            video = Transcript.get_or_none(video_id=video_id)
            if not video:
                return {"success": False, "error": f"Video {video_id} nicht gefunden."}

            # Kapitel-Query erstellen
            query = Chapter.select().where(Chapter.transcript == video)
            if chapter_type:
                query = query.where(Chapter.chapter_type == chapter_type)

            # Statistiken sammeln
            chapter_count = query.count()
            if chapter_count == 0:
                return {"success": False, "error": "Keine Kapitel zum Löschen gefunden."}

            # Löschung durchführen
            delete_query = Chapter.delete().where(Chapter.transcript == video)
            if chapter_type:
                delete_query = delete_query.where(Chapter.chapter_type == chapter_type)
            delete_query.execute()

            # Transcript-Status aktualisieren
            remaining_chapters = Chapter.select().where(Chapter.transcript == video).count()
            Transcript.update(
                has_chapters=(remaining_chapters > 0),
                chapter_count=remaining_chapters if not chapter_type else video.chapter_count,
                detailed_chapter_count=(
                    remaining_chapters if chapter_type == "detailed" else video.detailed_chapter_count
                ),
            ).where(Transcript.video_id == video_id).execute()

            logger.info(f"{chapter_count} Kapitel von Video '{video.title}' ({video_id}) gelöscht.")

            return {
                "success": True,
                "video_title": video.title,
                "chapters_deleted": chapter_count,
                "remaining_chapters": remaining_chapters,
                "message": f"{chapter_count} Kapitel erfolgreich gelöscht. {remaining_chapters} verbleibend.",
            }

        except Exception as e:
            logger.error(f"Fehler beim Löschen von Kapiteln für Video {video_id}: {e}")
            return {"success": False, "error": f"Fehler beim Löschen: {e}"}

    def get_deletion_preview(self, item_type: str, item_id: str) -> dict:
        """
        Gibt eine Vorschau der Löschungsauswirkungen zurück ohne zu löschen.

        Args:
            item_type (str): "video" oder "channel"
            item_id (str): ID des Items

        Returns:
            dict: Vorschau-Statistiken
        """
        try:
            if item_type == "video":
                video = Transcript.get_or_none(video_id=item_id)
                if not video:
                    return {"success": False, "error": f"Video {item_id} nicht gefunden."}

                chapter_count = Chapter.select().where(Chapter.transcript == video).count()
                return {
                    "success": True,
                    "type": "video",
                    "title": video.title,
                    "channel_name": video.channel.name if video.channel else "Unbekannt",
                    "videos_affected": 1,
                    "chapters_affected": chapter_count,
                }

            elif item_type == "channel":
                channel = Channel.get_or_none(channel_id=item_id)
                if not channel:
                    return {"success": False, "error": f"Kanal {item_id} nicht gefunden."}

                video_count = Transcript.select().where(Transcript.channel == channel).count()
                chapter_count = Chapter.select().join(Transcript).where(Transcript.channel == channel).count()

                return {
                    "success": True,
                    "type": "channel",
                    "title": channel.name,
                    "videos_affected": video_count,
                    "chapters_affected": chapter_count,
                }
            else:
                return {"success": False, "error": f"Unbekannter Item-Typ: {item_type}"}

        except Exception as e:
            logger.error(f"Fehler bei Löschungsvorschau für {item_type} {item_id}: {e}")
            return {"success": False, "error": f"Fehler bei Vorschau: {e}"}
