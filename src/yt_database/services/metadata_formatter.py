# src/yt_database/services/metadata_formatter.py
"""
MetadataFormatter

Dieses Modul stellt einen Service bereit, der verschachtelte YouTube-Kanal-Metadaten rekursiv durchsucht und daraus validierte TranscriptData-Objekte erzeugt.
Einsatzgebiet: Datenextraktion aus yt-dlp-Resultaten, Vereinheitlichung der Transcript-Metadaten für die weitere Verarbeitung und Speicherung.

Features:
- Rekursive Extraktion aller Transcript-Objekte aus komplexen Metadatenstrukturen
- Umwandlung von Transcript- und Kanal-Metadaten in das zentrale Datenmodell TranscriptData
- Einfache Erweiterbarkeit durch Protokollbindung
"""

from loguru import logger

from yt_database.models.models import TranscriptData
from yt_database.services.protocols import MetadataFormatterProtocol


class MetadataFormatter(MetadataFormatterProtocol):
    """
    Service zur Extraktion und Umwandlung von YouTube-Kanal-Metadaten in TranscriptData-Objekte.
    Implementiert das MetadataFormatterProtocol.
    """

    def extract_transcript_data_objects_from_metadata(self, metadata: dict) -> list[TranscriptData]:
        """
        Extrahiert rekursiv alle Transcript-Infos aus verschachtelten Kanal-Metadaten und erstellt TranscriptData-Objekte.

        Args:
            metadata (dict): Kanal-Metadaten, typischerweise von yt-dlp.

        Returns:
            list[TranscriptData]: Liste von TranscriptData-Objekten.

        Raises:
            KeyError: Falls essentielle Felder fehlen.

        Example:
            >>> formatter = MetadataFormatter()
            >>> formatter.extract_transcript_data_objects_from_metadata(channel_metadata)
        """
        logger.debug("Starte Extraktion der TranscriptData-Objekte aus Metadaten.")
        channel_id = metadata.get("id", "")  # Extrahiere die Channel-ID
        channel_name = metadata.get("uploader", "")  # Extrahiere den Kanalnamen
        channel_url = metadata.get("webpage_url", "")  # Extrahiere die Kanal-URL
        channel_handle = metadata.get("uploader_id", "")  # Extrahiere den Kanal-Handle
        entries = metadata.get("entries", [])  # Hole die Einträge-Liste
        channel_meta = {
            "id": channel_id,
            "uploader": channel_name,
            "webpage_url": channel_url,
            "uploader_id": channel_handle,
        }

        def extract_video_objects(entries: list) -> list[TranscriptData]:
            """Rekursive Hilfsfunktion zur Extraktion aller Transcript-Objekte aus einer Eintragsliste.

            Args:
                entries (list): Liste von Einträgen (Dicts)

            Returns:
                list[TranscriptData]: Alle extrahierten Transcript-Objekte
            """
            logger.debug(f"Durchlaufe {len(entries)} Einträge für Transcript-Extraktion.")
            objects: list[TranscriptData] = []
            for entry in entries:
                # Prüfe, ob der Eintrag ein Dictionary ist
                if not isinstance(entry, dict):
                    continue  # Überspringe ungültige Einträge
                # Prüfe, ob es sich um ein Transcript handelt (yt-dlp: _type == 'url')
                if entry.get("_type") == "url" and entry.get("id") and entry.get("id") != channel_id:
                    obj = self.to_transcript_data(entry=entry, channel_meta=channel_meta)
                    objects.append(obj)  # Füge das extrahierte Transcript hinzu
                    logger.debug(f"Transcript {obj.video_id} extrahiert und hinzugefügt.")
                # Rekursion: Falls weitere Einträge verschachtelt sind
                if "entries" in entry and isinstance(entry["entries"], list):
                    logger.debug(f"Rekursiver Abstieg in verschachtelte Einträge für {entry.get('id', '')}.")
                    objects.extend(extract_video_objects(entry["entries"]))
            return objects

        result = extract_video_objects(entries)
        logger.debug(f"Extraktion abgeschlossen, {len(result)} TranscriptData-Objekte gefunden.")
        return result

    def to_transcript_data(self, entry: dict, channel_meta: dict) -> TranscriptData:
        """Erstellt ein TranscriptData-Objekt aus einem Transcript-Entry und den Kanal-Metadaten.

        Args:
            entry (dict): Transcript-Metadaten (yt-dlp-Format)
            channel_meta (dict): Kanal-Metadaten

        Returns:
            TranscriptData: Validiertes Datenmodell mit allen Feldern

        Example:
            >>> formatter = MetadataFormatter()
            >>> formatter.to_transcript_data(entry, channel_meta)
        """
        logger.debug(f"Erzeuge TranscriptData für Transcript-ID {entry.get('id', '')}.")
        # Erzeuge das TranscriptData-Objekt mit allen relevanten Feldern
        return TranscriptData(
            video_id=entry.get("id", ""),  # YouTube Transcript-ID
            video_url=entry.get("url", entry.get("original_url", "")),  # Transcript-URL
            title=entry.get("title", ""),  # Videotitel
            channel_id=channel_meta.get("id", ""),  # Kanal-ID
            channel_name=channel_meta.get("uploader", ""),  # Kanalname
            channel_url=channel_meta.get("webpage_url", ""),  # Kanal-URL
            channel_handle=channel_meta.get("uploader_id", ""),  # Kanal-Handle
            publish_date=entry.get("upload_date", ""),  # Veröffentlichungsdatum
            duration=str(entry.get("duration", "")),  # Videodauer als String
            entries=[],  # Leere Liste für Transkript-Einträge
            chapters=[],  # Leere Liste für Kapitel
            detailed_chapters=[],  # Leere Liste für detaillierte Kapitel
            error_reason="",  # Fehlerfeld initial leer
        )
