# src/yt_database/utils/extract_youtube_id_util.py
import re

from loguru import logger


def extract_video_id(url_or_id: str) -> str | None:
    """
    Extrahiert die YouTube-Transcript-ID aus einer URL oder gibt sie direkt zurück.
    Ist jetzt robust gegen variable Lookbehind-Fehler.

    Args:
        url_or_id (str): YouTube-URL oder Transcript-ID.

    Returns:
        str | None: Die extrahierte Transcript-ID oder None, falls keine gefunden wurde.
    """
    if not url_or_id or not isinstance(url_or_id, str):
        return None

    # Prüfen, ob es sich bereits um eine gültige ID handelt (11 Zeichen, keine Sonderzeichen außer -_)
    if re.fullmatch(r"[a-zA-Z0-9_-]{11}", url_or_id.strip()):
        return url_or_id.strip()

    # Präfixe und einer erfassenden Gruppe für die ID.
    # (?:...) -> Finde, aber erfasse nicht (non-capturing group)
    #    (...)   -> Finde UND erfasse (capturing group)
    video_id_pattern = re.compile(r"(?:v=|v/|vi=|vi/|youtu\.be/|embed/|shorts/|watch\?v=)" r"([a-zA-Z0-9_-]{11})")

    match = video_id_pattern.search(url_or_id)
    if match:
        return match.group(1)

    logger.warning(f"Konnte keine gültige YouTube-Transcript-ID aus '{url_or_id}' extrahieren.")
    return None
