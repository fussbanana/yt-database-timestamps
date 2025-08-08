# src/yt_database/services/generator_worker.py

from loguru import logger
from PySide6.QtCore import QObject, Signal


class GeneratorWorker(QObject):
    """
    Worker für die Transkriptions-Generierung eines Videos.

    Args:
        generator_service: Instanz von GeneratorService.
        channel_handle (str): Handle des YouTube-Kanals.
        video_id (str): ID des YouTube-Videos.

    Signals:
        finished: Wird gesendet, wenn die Verarbeitung abgeschlossen ist.
        error: Wird gesendet, wenn ein Fehler auftritt.
        status_update: Status- oder Fortschrittsmeldungen.
    """

    finished = Signal(str)
    error = Signal(str)
    status_update = Signal(str)

    def __init__(self, transcript_service, generator_service, channel_handle: str, video_id: str) -> None:
        super().__init__()
        self.transcript_service = transcript_service
        self.generator_service = generator_service
        self.channel_handle = channel_handle
        self.video_id = video_id

    def run(self) -> None:
        """
        Führt den Transkriptions-Workflow für ein Transcript aus und sendet Status/Fehler über Signale.
        """
        try:
            self.status_update.emit(
                f"Starte Verarbeitung für Transcript: {self.video_id} (Channel: {self.channel_handle})"
            )
            transcript_data = self.generator_service.transcript_service.fetch_transcript(self.video_id)
            if (
                transcript_data.entries
                and isinstance(transcript_data.entries, list)
                and len(transcript_data.entries) > 0
            ):
                self.status_update.emit(
                    f"Gültiges Transkript mit {len(transcript_data.entries)} Zeilen für {self.video_id} gefunden."
                )
                self.generator_service.file_service.write_transcript_file(transcript_data)
                self.generator_service.project_manager.update_index(transcript_data)
                self.status_update.emit(f"Verarbeitung für Transcript {self.video_id} erfolgreich abgeschlossen.")
                self.finished.emit(self.video_id)
            else:
                error_reason = transcript_data.error_reason or "Transkript war leer oder nicht vorhanden."
                msg = f"Verarbeitung für Transcript {self.video_id} abgebrochen. Grund: {error_reason}"
                logger.warning(msg)
                self.error.emit(msg)
                self.finished.emit(self.video_id)
        except Exception as exc:
            msg = f"Unerwarteter Fehler bei der Verarbeitung von {self.video_id}: {exc}"
            logger.error(msg)
            self.error.emit(msg)
            self.finished.emit(self.video_id)
