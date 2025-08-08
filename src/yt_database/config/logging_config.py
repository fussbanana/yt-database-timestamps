"""
Konfiguriert das Logging für yt_database mit loguru.

Fügt einen farbigen Konsolen-Logger (INFO) und einen Datei-Logger (DEBUG, Rotation, Retention) hinzu.
Logdateien werden im Verzeichnis logs/ abgelegt.

Beispiel:
    >>> from yt_database.config import logging_config
    >>> from loguru import logger
    >>> logger.info("Test")
    2025-07-21 12:00:00 | INFO     | ... - Test
"""

import sys

from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(
    sink="logs/yt_database.log",
    level="DEBUG",
    rotation="1 day",
    retention="7 days",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    filter=lambda record: record["level"].name in ("DEBUG", "WARNING", "ERROR", "CRITICAL", "INFO"),
)
