"""
Testet, ob die Logging-Konfiguration von yt_database korrekt Logdateien erzeugt und beschreibt.
"""

import time


def test_loguru_file_logger_writes_log(tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    logfile = logs_dir / "yt_database.log"
    from loguru import logger

    logger.remove()
    logger.add(
        sink=str(logfile),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss!Europe/Berlin} | {level: <8} | {name}:{function}:{line} - {message}",
        filter=lambda record: record["level"].name in ("DEBUG", "ERROR"),
    )
    logger.info("Test-Logeintrag für File-Logger")
    logger.debug("Debug-Logeintrag für File-Logger")
    logger.error("Error-Logeintrag für File-Logger")
    time.sleep(0.2)
    assert logfile.exists(), f"Logdatei {logfile} wurde nicht angelegt."
    content = logfile.read_text(encoding="utf-8")
    assert "Debug-Logeintrag" in content
    assert "Error-Logeintrag" in content
    assert "Test-Logeintrag" not in content
