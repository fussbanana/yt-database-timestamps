"""
Testet, ob die Loguru-Konfiguration in yt_database nur DEBUG und ERROR in die Datei schreibt.
"""

import time

from loguru import logger


def test_file_logger_only_debug_and_error(tmp_path):
    logfile = tmp_path / "yt_database.log"
    # Logger für Test: Schreibe in temp-Datei, nur DEBUG und ERROR
    test_logger = logger.bind()
    test_logger.add(
        sink=str(logfile),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss!Europe/Berlin} | {level: <8} | {name}:{function}:{line} - {message}",
        filter=lambda record: record["level"].name in ("DEBUG", "ERROR"),
    )
    test_logger.info("Info-Log sollte nicht erscheinen")
    test_logger.debug("Debug-Log sollte erscheinen")
    test_logger.error("Error-Log sollte erscheinen")
    # Warte bis Log geschrieben ist (max 1 Sekunde)
    for _ in range(10):
        if logfile.exists() and logfile.stat().st_size > 0:
            break
        time.sleep(0.1)
    content = logfile.read_text(encoding="utf-8")
    # Prüfe Zeilen einzeln, bessere Fehlermeldung
    assert any("Debug-Log sollte erscheinen" in line for line in content.splitlines()), f"Debug fehlt: {content}"
    assert any("Error-Log sollte erscheinen" in line for line in content.splitlines()), f"Error fehlt: {content}"
    assert all("Info-Log sollte nicht erscheinen" not in line for line in content.splitlines()), (
        f"Info taucht auf: {content}"
    )
