"""
MockBatchTranscriptionWorker
---------------------------

Mock für BatchTranscriptionWorker. Simuliert die Signal-Logik ohne echte Transkription.

:author: fussbanana
"""

from PySide6.QtCore import QObject, Signal, Slot


class MockBatchTranscriptionWorker(QObject):
    """
    Mock-Worker für Tests. Sendet die gleichen Signale wie das Original,
    ruft aber keine echten Services auf.

    :param channel_url: Die YouTube-Kanal-URL
    :param interval: Intervall zwischen den Transkriptionen (Sekunden)
    :param max_videos: Maximale Anzahl der zu verarbeitenden Videos (None = alle)
    """

    progress = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.channel_url = kwargs.get("channel_url", None)
        self.interval = kwargs.get("interval", None)
        self.max_videos = kwargs.get("max_videos", None)
        self.provider = kwargs.get("provider", None)
        self.video_ids = kwargs.get("video_ids", None)
        self.is_running = True

    @Slot()
    def run(self) -> None:
        """
        Simuliert den Transkriptionsprozess.
        """
        self.progress.emit(f"[MOCK] Starte Worker für: {self.channel_url}")
        # Simuliere einen erfolgreichen Durchlauf
        self.progress.emit("[MOCK] Worker-Aufgabe beendet.")
        self.finished.emit()

    @Slot()
    def run_with_error(self) -> None:
        """
        Simuliert einen Fehlerfall.
        """
        self.progress.emit(f"[MOCK] Starte Worker für: {self.channel_url}")
        self.error.emit("[MOCK] Fehler im Worker")
        self.finished.emit()
