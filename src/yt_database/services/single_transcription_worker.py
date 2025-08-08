"""
SingleTranscriptionWorker

Qt-Worker für die Einzeltranskription eines YouTube-Videos mit automatischem Thread-Management.
Kapselt den Transkriptions-Workflow und kommuniziert über Qt-Signale mit der GUI.
"""

from typing import Optional

from loguru import logger
from PySide6.QtCore import QObject, Signal, Slot

from yt_database.models.models import TranscriptData
from yt_database.services.protocols import SingleTranscriptionServiceProtocol


class SingleTranscriptionWorker(QObject):
    """Worker für die Einzeltranskription eines YouTube-Videos mit automatischem Thread-Management.

    Args:
        transcript_data (TranscriptData): Die Daten des zu transkribierenden Videos.
        single_transcription_service (SingleTranscriptionServiceProtocol): Service für die Einzeltranskription.

    Signals:
        finished (TranscriptData): Signal, wenn die Aufgabe abgeschlossen ist. Enthält das Ergebnis.
        error (str): Signal mit Fehlermeldung.
        status_update (str): Status-Updates für die GUI.
    """

    finished = Signal(TranscriptData)
    error = Signal(str)
    status_update = Signal(str)

    def __init__(
        self,
        transcript_data: TranscriptData,
        single_transcription_service: SingleTranscriptionServiceProtocol,
        parent: Optional[QObject] = None,
    ) -> None:
        """
        Initialisiert den Worker für die Einzeltranskription.
        """
        super().__init__(parent)
        self.transcript_data = transcript_data
        self.single_transcript_service = single_transcription_service
        logger.debug(f"Initialisiere SingleTranscriptionWorker für Video {self.transcript_data.video_id}.")

    @Slot()
    def run(self) -> None:
        """
        Startet die Einzeltranskription und meldet den Abschluss oder Fehler.
        """
        logger.debug(f"Starte Einzeltranskription im Worker für {self.transcript_data.video_id}.")
        try:
            self.status_update.emit(f"Starte Verarbeitung für Video: {self.transcript_data.video_id}")

            transcription_result = self.single_transcript_service.process_video(self.transcript_data)

            if transcription_result.error_reason:
                self.error.emit(transcription_result.error_reason)
            else:
                self.status_update.emit(f"Verarbeitung für Video {transcription_result.video_id} erfolgreich.")

            self.finished.emit(transcription_result)

        except Exception as exc:
            msg = f"Unerwarteter Fehler bei der Verarbeitung von {self.transcript_data.video_id}: {exc}"
            logger.error(msg)
            self.error.emit(msg)
            # Sende das ursprüngliche Objekt mit Fehlerinformationen zurück
            self.transcript_data.error_reason = msg
            self.finished.emit(self.transcript_data)

    def stop_worker(self) -> None:
        """
        Beendet den zugehörigen Thread sauber, falls er noch läuft.
        Diese Methode sollte vor dem Schließen der Anwendung oder beim Abbruch aufgerufen werden.
        """
        thread = self.thread()
        if thread and thread.isRunning():
            logger.debug("Beende SingleTranscriptionWorker-Thread sauber.")
            thread.quit()
            thread.wait(1000)
