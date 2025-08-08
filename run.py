# run.py
"""
Zentrale Runner-Datei für das yt-database-Projekt.

Dieses Modul stellt den Einstiegspunkt für alle wichtigen Workflows und CLI-Kommandos bereit.
Es übernimmt die Argument- und Subkommando-Verarbeitung und leitet die Ausführung an die jeweiligen CLI-Module weiter.

Beispiel:
    python run.py batch-transcribe --channel-url <url>
    python run.py transcribe-video --video-id <id>
    python run.py download-channel-metadata --channel-url <url>

Alle Argumente und Subkommandos werden an die jeweiligen CLI-Module weitergereicht.

Architektur-Entscheidung:
    - Die zentrale Steuerung erfolgt über argparse und Subparser.
    - Logging wird über loguru bereitgestellt und dokumentiert alle Schritte.
    - Die CLI-Module sind lose gekoppelt und können unabhängig getestet werden.

:author: Sascha
"""

import argparse
import sys
from yt_database.config import logging_config
from loguru import logger
from yt_database.cli.batch_transcribe import batch_transcribe_main
from yt_database.cli.download_channel_metadata import download_channel_metadata_main
from yt_database.cli.get_video_transcription import get_video_transcription_main
from yt_database.gui.main_window import main as main_window_main


def main() -> None:
    """
    Einstiegspunkt für das yt-database-Projekt.

    Initialisiert den Argumentparser, verarbeitet Subkommandos und leitet die Ausführung
    an die jeweiligen CLI-Module weiter.

    Ablauf:
        1. Initialisiert argparse mit Subparsern für alle unterstützten Kommandos.
        2. Übergibt alle weiteren Argumente an die jeweiligen CLI-Module.
        3. Loggt alle relevanten Schritte und Argumente.
        4. Führt das gewählte Subkommando aus.

    Raises:
        SystemExit: Bei Fehlern in der Argumentverarbeitung oder Ausführung.
    """
    logger.info("Starte yt-database Runner.")
    parser = argparse.ArgumentParser(description="Zentrale Runner-Datei für yt-database. Wähle ein Subkommando.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_transcribe = subparsers.add_parser("transcribe-video", help="Transkribiert ein einzelnes Transcript.")
    parser_transcribe.set_defaults(func=lambda: get_video_transcription_main())

    parser_batch = subparsers.add_parser("batch-transcribe", help="Batch-Transkription für einen Kanal.")
    parser_batch.set_defaults(func=lambda: batch_transcribe_main())

    parser_meta = subparsers.add_parser("download-channel-metadata", help="Lädt und speichert Channel-Metadaten.")
    parser_meta.set_defaults(func=lambda: download_channel_metadata_main())

    parser_gui = subparsers.add_parser("gui", help="Startet das GUI-Hauptfenster.")
    parser_gui.set_defaults(func=lambda: main_window_main())

    parser_prototype = subparsers.add_parser("gui-prototype", help="Startet das neue Prototyp-GUI (Testversion).")
    parser_prototype.set_defaults(func=lambda: prototype_main())

    args, unknown = parser.parse_known_args()
    logger.debug(f"Argumente: {sys.argv}")
    logger.info(f"Gewähltes Subkommando: {args.command}")
    sys.argv = [sys.argv[0]] + unknown
    logger.info(f"Starte Subkommando: {args.command}")
    args.func()
    logger.info(f"Subkommando {args.command} abgeschlossen.")


if __name__ == "__main__":
    main()
