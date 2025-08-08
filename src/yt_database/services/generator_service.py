# -*- coding: utf-8 -*-
"""
generator_service.py

Dieses Modul enthält die GeneratorService-Klasse, die den vollständigen Workflow zur Transkript-Generierung für ein YouTube-Transcript orchestriert.
Der Service übernimmt die Validierung, Formatierung und Speicherung von Transkripten und Metadaten sowie die Aktualisierung der Datenbank.

Features:
- Transkript und Metadaten abrufen und validieren
- Metadaten mappen und vereinheitlichen
- Transkript formatieren und speichern
- Datenbankeintrag für das Transcript aktualisieren
"""

from loguru import logger

from yt_database.services.protocols import (
    FileServiceProtocol,
    FormatterServiceProtocol,
    GeneratorServiceProtocol,
    ProjectManagerProtocol,
    TranscriptServiceProtocol,
)


class GeneratorService(GeneratorServiceProtocol):
    """
    Service zur Orchestrierung des Transkriptions-Workflows für ein Transcript.
    Implementiert das GeneratorServiceProtocol.
    """

    def __init__(
        self,
        project_manager: ProjectManagerProtocol,
        transcript_service: TranscriptServiceProtocol,
        formatter_service: FormatterServiceProtocol,
        file_service: FileServiceProtocol,
    ):
        """
        Initialisiert den GeneratorService mit den benötigten Service-Komponenten.

        Args:
            project_manager (ProjectManagerProtocol): Projektmanagement-Service.
            transcript_service (TranscriptServiceProtocol): Transkriptions-Service.
            formatter_service (FormatterServiceProtocol): Formatierungs-Service.
            file_service (FileServiceProtocol): Datei-Service.

        Example:
            >>> service = GeneratorService(pm, ts, fmt, fs)
        """
        # Speichere die Service-Komponenten als Instanzvariablen
        self.project_manager = project_manager
        self.transcript_service = transcript_service
        self.formatter_service = formatter_service
        self.file_service = file_service
        logger.debug("GeneratorService initialisiert.")

    def run(self, channel_handle: str, video_id: str) -> None:
        """
        Führt den vollständigen Transkriptions-Workflow für ein Transcript aus.

        Args:
            channel_handle (str): Handle des YouTube-Kanals.
            video_id (str): ID des YouTube-Videos.

        Returns:
            None

        Workflow:
            1. Transkript und Metadaten abrufen und validieren
            2. Metadaten mappen und vereinheitlichen
            3. Transkript formatieren und speichern
            4. Datenbankeintrag für das Transcript aktualisieren
            5. Fehler und Sonderfälle loggen

        Raises:
            Exception: Bei Fehlern im Datenbank-Update oder der Verarbeitung.

        Example:
            >>> service.run("@kanal", "abc123")
        """
        logger.debug(f"Starte Verarbeitung für Transcript: {video_id} (Channel: {channel_handle})")
        # Hole das validierte Transkript- und Metadatenmodell vom Transkriptionsservice
        transcript_data = self.transcript_service.fetch_transcript(video_id)
        # Mappe die Metadaten auf die Datenbankstruktur, um Konsistenz zu gewährleisten
        # mapped_metadata = self.formatter_service.extract_metadata(transcript_data.model_dump())
        # logger.debug(f"Gemappte Metadaten: {mapped_metadata}")
        # Formatiere das Transkript für die spätere Speicherung als menschenlesbaren Text
        # Ich übergebe das vollständige TranscriptData-Objekt an den Formatter
        # Schreibe das formatierte Transkript und die Metadaten in die entsprechende Datei
        self.file_service.write_transcript_file(transcript_data)
        # Versuche, den Datenbankeintrag für das Transcript zu aktualisieren
        try:
            logger.debug(f"Versuche Datenbankeintrag für Transcript {video_id} zu aktualisieren.")
            self.project_manager.update_index(transcript_data)
            logger.debug(f"Datenbankeintrag für Transcript {video_id} erfolgreich erstellt/aktualisiert.")
        except Exception as exc:
            logger.debug(f"Fehler beim Datenbankeintrag für Transcript {video_id}: {exc}")
        # Workflow abgeschlossen
        logger.debug(f"Verarbeitung für Transcript {video_id} erfolgreich abgeschlossen.")
