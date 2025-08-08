"""
BatchTranscriptionWorker

Qt-Worker zur Ausführung einer Batch-Transkription für eine Liste von YouTube-Videos.
Kapselt die Service-Logik und meldet Fortschritt, Fehler und Abschluss über Qt-Signale.
"""

from typing import Optional

from loguru import logger
from PySide6.QtCore import QObject, Signal, Slot

from yt_database.models.models import TranscriptData

from .protocols import BatchTranscriptionServiceProtocol


class BatchTranscriptionWorker(QObject):
    """Worker für die Batch-Transkription von YouTube-Videos mit automatischem Thread-Management.

    Args:
        channel_url (str): Die URL des YouTube-Kanals.
        video_ids (list[str]): Liste der zu transkribierenden Transcript-IDs.
        batch_transcription_service (BatchTranscriptionServiceProtocol): Service für die Transkription.

    Signals:
        progress_percent (int): Fortschritt in Prozent.
        finished (): Signal, wenn die Aufgabe abgeschlossen ist.
        error (str): Signal mit Fehlermeldung.

    Example:
        worker = BatchTranscriptionWorker(
            channel_url="https://youtube.com/@kanal",
            video_ids=["id1", "id2"],
            batch_transcription_service=batch_service
        )
        worker.start()
    """

    progress_percent = Signal(int)
    transcription_download_finished = Signal()  # Signal für Abschluss der Transkriptions-Downloads
    error = Signal(str)
    finished = Signal()

    def __init__(
        self,
        transcript_data_list: list[TranscriptData],
        batch_transcription_service: BatchTranscriptionServiceProtocol,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.transcript_data_list = transcript_data_list
        self.batch_service = batch_transcription_service
        logger.debug(f"Initialisiere BatchTranscriptionWorker mit {len(self.transcript_data_list)} Videos.")

    @Slot()
    def run(self) -> None:
        """
        Startet die Batch-Transkription und meldet Fortschritt, Fehler und Abschluss.

        Raises:
            Exception: Bei Fehlern im Transkriptionsprozess.

        Example:
            worker.run()
        """
        logger.debug("Starte Batch-Transkription im Worker.")
        try:
            total_videos = len(self.transcript_data_list)
            if total_videos == 0:
                logger.warning("Keine Videos für die Batch-Transkription übergeben.")
                self.finished.emit()
                return

            video_ids_to_process = [data.video_id for data in self.transcript_data_list]
            # Annahme: Alle Videos im Batch gehören zum selben Kanal
            channel_url = self.transcript_data_list[0].channel_url

            def progress_callback(current_step: int):
                percent = int((current_step / total_videos) * 100)
                logger.debug(f"Fortschritt: {percent}% ({current_step}/{total_videos})")
                self.progress_percent.emit(percent)

            self.batch_service.run_batch_transcription(
                channel_url,
                video_ids_to_process=video_ids_to_process,
                progress_callback=progress_callback,
            )
        except Exception as e:
            logger.error(f"Fehler im BatchTranscriptionWorker: {e}")
            self.error.emit(str(e))
        finally:
            logger.debug("BatchTranscriptionWorker hat seine Aufgabe beendet.")
            self.transcription_download_finished.emit()
            self.finished.emit()

    def stop_worker(self) -> None:
        """
        Beendet den zugehörigen Thread sauber, falls er noch läuft.
        Diese Methode sollte vor dem Schließen der Anwendung oder beim Abbruch aufgerufen werden.
        """
        thread = self.thread()
        if thread and thread.isRunning():
            logger.debug("Beende BatchTranscriptionWorker-Thread sauber.")
            thread.quit()
            thread.wait(1000)
