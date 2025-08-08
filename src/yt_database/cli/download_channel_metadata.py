import argparse

from loguru import logger


def download_channel_metadata_main() -> None:
    """Lädt Metadaten aller Videos eines YouTube-Kanals und speichert sie als JSON-Dateien.

    Diese Funktion ruft die Metadaten eines YouTube-Kanals ab und speichert sie
    inklusive der Transcript-IDs als JSON im Channel-Ordner. Optional kann die Anzahl
    der Videos begrenzt werden.

    Beispiel:
        >>> $ poetry run python run.py download-channel-metadata "https://www.youtube.com/@kanalname"
        >>> $ poetry run python run.py download-channel-metadata "https://www.youtube.com/@kanalname" --max 10

    Args:
        Keine (CLI-Argumente werden automatisch geparst).

    Raises:
        Exception: Bei Fehlern im Metadatenabruf oder beim Schreiben der Dateien.
    """
    parser = argparse.ArgumentParser(
        description="Lädt Metadaten aller Videos eines YouTube-Kanals und speichert sie als JSON-Dateien im Channel-Ordner."
    )
    parser.add_argument("channel_url", help="URL des YouTube-Kanals")
    parser.add_argument("--max", type=int, default=None, help="Maximale Anzahl Videos (optional)")
    args = parser.parse_args()

    logger.info(f"Hole Channel-Metadaten für: {args.channel_url}")
    logger.debug("Channel-Metadata-Download ist aktuell deaktiviert - verwende das GUI für diese Funktion.")
    logger.info("Starte das GUI mit: poetry run gui-prototype")

    # TODO: Implement channel metadata download through ServiceFactory
    # The functionality is available in the GUI through BatchTranscriptionWidget
