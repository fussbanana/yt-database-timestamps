import io
import os
import re
from typing import Iterable, Optional, TextIO, Tuple, Union

from loguru import logger


def to_snake_case(name: str) -> str:
    """
    Konvertiert einen String in snake_case.

    Erkennt CamelCase, ersetzt Sonderzeichen und Leerzeichen durch '_',
    fasst mehrere Unterstriche zusammen und gibt bei leerem Ergebnis 'unbekannt' zurück.

    Args:
        name (str): Der zu konvertierende String.

    Returns:
        str: Der konvertierte String im snake_case-Format.

    Beispiel:
        >>> to_snake_case("Mein Transcript-Titel!")
        'mein_video_titel'
        >>> to_snake_case("CamelCaseTest")
        'camel_case_test'
        >>> to_snake_case("")
        'unbekannt'
    """
    s = name.strip()
    # CamelCase/PascalCase zu snake_case
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    s = s.lower()
    # Sonderzeichen und Leerzeichen ersetzen, Umlaute bleiben erhalten
    s = re.sub(r"[^a-z0-9äöüÄÖÜ]+", "_", s)
    s = re.sub(r"_+", "_", s)
    s = s.strip("_")
    return s or "unbekannt"


def get_or_set_frontmatter_value(md_source: str, key: str, default: str | bool) -> Tuple[str, Optional[str]]:
    """
    Liest den Wert eines Schlüssels aus dem Frontmatter einer Markdown-Datei oder einem String.
    Falls nicht vorhanden, wird der Schlüssel mit dem Defaultwert ergänzt und der neue Inhalt zurückgegeben.

    Args:
        md_source (str): Pfad zur Markdown-Datei oder Inhalt als String.
        key (str): Der zu suchende Schlüssel im Frontmatter.
        default (str | bool): Der Standardwert, der gesetzt wird, falls der Schlüssel fehlt.

    Returns:
        Tuple[str, Optional[str]]: Der Wert des Schlüssels und ggf. der neue Inhalt (wenn ergänzt), sonst None.
    """
    # logger.debug(f"get_or_set_frontmatter_value: key={key}, default={default}")
    # Prüfen, ob md_source ein existierender Pfad ist
    if os.path.isfile(md_source):
        with open(md_source, "r", encoding="utf-8") as f:
            lines = f.readlines()
        source_type = "file"
    else:
        lines = md_source.splitlines(keepends=True)
        source_type = "string"
    frontmatter_end = None
    value = None
    key_prefix = f"{key}:"
    for i, line in enumerate(lines):
        if line.strip() == "---" and i != 0:
            frontmatter_end = i
            break
        if line.startswith(key_prefix):
            value = line.split(":", 1)[1].strip()
    if value is not None:
        # logger.debug(f"Frontmatter-Wert gefunden: {key}={value} (Quelle: {source_type})")
        return value, None
    insert_idx = frontmatter_end if frontmatter_end is not None else len(lines)
    new_value = str(default).lower()
    lines.insert(insert_idx, f"{key}: {new_value}\n")
    # logger.debug(f"Frontmatter-Wert ergänzt: {key}={new_value} (Quelle: {source_type})")
    if source_type == "file":
        with open(md_source, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return new_value, None
    else:
        new_content = "".join(lines)
        return new_value, new_content


def has_content_after_marker(
    source: Union[str, TextIO, Iterable[str]], marker: str, default: bool = False, lines_to_check: int = 3
) -> bool:
    """Prüft, ob nach einer Markierungszeile nicht-leerer Inhalt folgt.

    Diese Funktion kann verschiedene Quelltypen verarbeiten:
    1.  Ein Dateipfad (str).
    2.  Ein mehrzeiliger String (str).
    3.  Ein Text-Stream (z.B. ein geöffnetes Dateiobjekt, io.StringIO, sys.stdin).

    Args:
        source: Der Dateipfad, String-Inhalt oder Stream, der durchsucht werden soll.
        marker: Die exakte Zeile (ohne führende/nachfolgende Leerzeichen), nach der gesucht wird.
        default: Der Rückgabewert, falls der Marker nicht gefunden wird oder ein Fehler auftritt.
        lines_to_check: Die Anzahl der Zeilen, die nach dem Marker auf Inhalt geprüft werden sollen.

    Returns:
        True, wenn innerhalb von `lines_to_check` Zeilen nach dem Marker Inhalt gefunden wird.
        False, wenn der Marker gefunden wird, aber die folgenden Zeilen leer sind oder die Quelle endet.
        `default`, wenn der Marker nicht gefunden wird.
    """
    try:
        # Fall 1 & 2: Quelle ist ein String (kann Pfad oder Inhalt sein)
        if isinstance(source, str):
            if os.path.isfile(source):
                # Es ist ein Dateipfad -> Öffne die Datei und rufe die Funktion rekursiv mit dem Stream auf
                with open(source, "r", encoding="utf-8") as f:
                    return has_content_after_marker(f, marker, default, lines_to_check)
            else:
                # Es ist ein String-Inhalt -> Wandle ihn in einen Stream um
                string_stream = io.StringIO(source)
                return has_content_after_marker(string_stream, marker, default, lines_to_check)

        # Fall 3: Quelle ist bereits ein Stream/Iterator (wie eine geöffnete Datei)
        # Wir iterieren Zeile für Zeile, um den Speicher zu schonen.
        lines_iterator = iter(source)
        for line in lines_iterator:
            if line.strip() == marker:
                # Marker gefunden! Jetzt die nächsten Zeilen prüfen.
                for _ in range(lines_to_check):
                    try:
                        next_line = next(lines_iterator)
                        if next_line.strip():
                            # Inhalt gefunden, wir sind fertig.
                            return True
                    except StopIteration:
                        # Das Ende des Streams wurde erreicht, bevor wir Inhalt fanden.
                        return False
                # Die `lines_to_check` Zeilen nach dem Marker waren alle leer.
                return False

        # Der Marker wurde in der gesamten Quelle nicht gefunden.
        return default

    except Exception as e:
        logger.warning(f"Fehler beim Lesen der Quelle: {e}")
        return default


def find_transcript_markdown_for_video_id(video_id: str, projects_dir: str = "projects") -> Optional[str]:
    """
    Deprecated: Diese Funktion wurde durch
    `yt_database.utils.transcript_for_video_id_util.get_transcript_path_for_video_id` ersetzt.
    Sie wird nicht mehr verwendet und wurde im Rahmen einer Konsolidierung entfernt.

    Args:
        video_id (str): Die Transcript-ID.
        projects_dir (str): Pfad zum Projekteordner.

    Returns:
        Optional[str]: Immer None. Bitte die neue Utility-Funktion verwenden.
    """
    logger.debug(
        "find_transcript_markdown_for_video_id ist deprecated. Verwende get_transcript_path_for_video_id aus transcript_for_video_id_util."
    )
    return None
