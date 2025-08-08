import os
from typing import List, Optional

import yt_dlp
from loguru import logger

from yt_database.config.settings import Settings, settings
from yt_database.models.models import TranscriptData, TranscriptEntry
from yt_database.services.protocols import TranscriptServiceProtocol
from yt_database.services.service_factory import ServiceFactory

# Die Klasse TranscriptService erbt von TranscriptServiceProtocol und implementiert yt-dlp-Transkription.


class TranscriptService(TranscriptServiceProtocol):
    def __init__(self, settings: Settings = settings) -> None:
        """Initialisiert den Service.

        Args:
            settings (Settings): Das zentrale Settings-Modell.
        """
        self.settings = settings  # Speichert die Settings-Instanz für spätere Verwendung.
        # Factory wird später injiziert, wenn verfügbar
        self.factory: Optional["ServiceFactory"] = None
        logger.debug("TranscriptService (yt-dlp-Variante) initialisiert.")

    # Holt das Transkript für eine Transcript-ID mit yt-dlp.
    def fetch_transcript(
        self, video_id: str, languages: Optional[List[str]] = None, use_cookies: Optional[bool] = None
    ) -> TranscriptData:
        """
        Ruft das Transkript und die vollständigen Metadaten für die gegebene Transcript-ID mit yt-dlp ab und gibt ein TranscriptData-Objekt zurück.
        """
        if languages is None:
            languages = ["de"]
        logger.debug(f"Hole Transkript und Metadaten für Transcript {video_id} mit yt-dlp...")
        output_template = f"{video_id}"
        cookie_path = self.settings.yt_dlp_cookies_path
        use_cookies_effective = (
            use_cookies if use_cookies is not None else getattr(self.settings, "use_yt_dlp_cookies", True)
        )
        cookies_value = None
        if use_cookies_effective and cookie_path and os.path.exists(cookie_path):
            cookies_value = cookie_path
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "writeautomaticsub": True,
            "subtitleslangs": languages,
            "subtitlesformat": "json3",
            "outtmpl": {"default": output_template},
            "ignoreerrors": True,
        }
        if cookies_value:
            ydl_opts["cookies"] = cookies_value
        transcript_entries = []
        chapters: list = []
        error_reason = ""
        transcript_file_path = f"{output_template}.{languages[0]}.json3"
        metadata = None
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                metadata = info_dict
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
                if os.path.exists(transcript_file_path):
                    try:
                        if self.factory is None:
                            raise RuntimeError("Factory wurde nicht korrekt injiziert")
                        formatter = self.factory.get_formatter_service()
                        parsed = formatter.parse_json3_transcript(transcript_file_path)
                        for entry in parsed:
                            # Sichere Extraktion nur der erwarteten Felder
                            safe_entry = {
                                "text": entry.get("text", ""),
                                "start": entry.get("start", 0.0),
                                "duration": entry.get("duration", 0.0),
                                "start_hms": entry.get("start_hms", ""),
                                "end_hms": entry.get("end_hms", ""),
                                "duration_hms": entry.get("duration_hms", ""),
                                "speaker": entry.get("speaker", ""),
                            }
                            transcript_entries.append(
                                TranscriptEntry(
                                    text=safe_entry["text"],
                                    start=safe_entry["start"],
                                    end=safe_entry["start"] + safe_entry["duration"],
                                    duration=safe_entry["duration"],
                                    start_hms=safe_entry["start_hms"],
                                    end_hms=safe_entry["end_hms"],
                                    duration_hms=safe_entry["duration_hms"],
                                    speaker=safe_entry["speaker"],
                                )
                            )
                    except Exception as e:
                        error_reason = f"Fehler beim Parsen des Transkript-JSON: {e}"
                else:
                    error_reason = f"Kein deutsches Transkript für Transcript {video_id} gefunden."
        except Exception as e:
            error_reason = f"Fehler in TranscriptService: {e}"
            logger.debug(f"Unerwarteter Fehler für {video_id}: {e}")
        finally:
            if os.path.exists(transcript_file_path):
                try:
                    os.remove(transcript_file_path)
                    logger.debug(f"Temporäre Transkript-Datei gelöscht: {transcript_file_path}")
                except OSError as e:
                    logger.debug(f"Konnte temporäre Datei nicht löschen: {e}")
        # Metadaten extrahieren
        video_id_val = metadata.get("id", str(video_id)) if metadata else video_id
        channel_id = metadata.get("channel_id", "") if metadata else ""
        channel_name = metadata.get("uploader", "") if metadata else ""
        channel_handle = metadata.get("uploader_id", "") if metadata else ""
        channel_url = metadata.get("channel_url", "") if metadata else ""
        video_url = metadata.get("webpage_url", "") if metadata else ""
        title = metadata.get("title", "") if metadata else ""
        publish_date = metadata.get("upload_date", "") if metadata else ""
        duration = metadata.get("duration_string", "") if metadata else ""
        return TranscriptData(
            title=str(title),
            video_id=str(video_id_val),
            video_url=str(video_url),
            channel_id=str(channel_id),
            channel_name=str(channel_name),
            channel_url=str(channel_url),
            channel_handle=str(channel_handle),
            publish_date=str(publish_date),
            duration=str(duration),
            entries=transcript_entries,
            chapters=chapters,
            error_reason=str(error_reason),
        )

    def fetch_channel_metadata(self, channel_url: str) -> list[TranscriptData]:
        """Lädt die Metadaten eines YouTube-Kanals über yt-dlp und schreibt neue Videos in die Datenbank.

        Args:
            channel_url (str): Die URL des YouTube-Kanals.

        Returns:
            list[TranscriptData]: Liste der geladenen TranscriptData-Objekte.
        """
        logger.debug(f"Starte fetch_channel_metadata für {channel_url}")
        cookie_file_path = self.settings.yt_dlp_cookies_path
        use_cookies = getattr(self.settings, "use_yt_dlp_cookies", True)
        if use_cookies and cookie_file_path and os.path.exists(cookie_file_path):
            cookies_value = cookie_file_path
        else:
            cookies_value = None
        ydl_opts = {
            "quiet": True,
            "extract_flat": True,
            "skip_download": True,
            "force_generic_extractor": False,
            "ignoreerrors": True,
            "extractor_args": {"youtube": {"player_client": ["tv_embedded"]}},
        }
        if cookies_value:
            ydl_opts["cookies"] = cookies_value
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            channel_metadata = ydl.extract_info(channel_url, download=False)
            if not isinstance(channel_metadata, dict):
                logger.error(f"Konnte keine Channel-Metadaten extrahieren für {channel_url}.")
                return []
        # Extrahiere TranscriptData-Objekte aus den Channel-Metadaten
        if self.factory is None:
            raise RuntimeError("Factory wurde nicht korrekt injiziert")
        channel_transcript_data = self.factory.get_metadata_formatter().extract_transcript_data_objects_from_metadata(
            channel_metadata
        )
        if not channel_transcript_data:
            logger.error(f"Konnte keine Videos für {channel_url} extrahieren.")
            return []
        logger.debug(f"fetch_channel_metadata: {len(channel_transcript_data)} gefunden.")

        # Schreibe neue Videos in die Datenbank
        pm_service = self.factory.get_project_manager_service()
        for td in channel_transcript_data:
            # Prüfe, ob das Transcript schon existiert
            from yt_database.database import Transcript

            if not Transcript.select().where(Transcript.video_id == td.video_id).exists():
                try:
                    # Verwende add_video_metadata für Channel-Metadaten (ohne Transcript-Inhalt)
                    pm_service.add_video_metadata(td)
                    logger.debug(f"Transcript-Metadaten für {td.video_id} in die Datenbank geschrieben.")
                except Exception as e:
                    logger.error(f"Fehler beim Schreiben von Transcript-Metadaten {td.video_id} in die DB: {e}")
            else:
                logger.debug(f"Transcript {td.video_id} existiert bereits in der Datenbank.")
        return channel_transcript_data
