#!/usr/bin/env python3
"""
Einfaches CLI-Tool für gezielte Markdown-Migration.

Dieses Skript kann einzelne Dateien oder Ordner migrieren.
"""

import argparse
import sys
from pathlib import Path

from loguru import logger

# Füge das src-Verzeichnis zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from migrate_markdown_to_database import MarkdownMigrator


def main():
    """Hauptfunktion für das CLI-Tool."""
    parser = argparse.ArgumentParser(description="Migriert Markdown-Dateien in die Datenbank")
    parser.add_argument(
        "target", nargs="?", help="Pfad zur spezifischen Datei oder zum Ordner (Standard: kompletter projects-Ordner)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Zeigt nur an, was gemacht würde, ohne Änderungen zu machen"
    )
    parser.add_argument("--force", action="store_true", help="Überschreibt existierende Kapitel")

    args = parser.parse_args()

    # Basis-Verzeichnisse
    base_dir = Path(__file__).parent.parent
    projects_dir = base_dir / "projects"
    database_path = base_dir / "yt_database.db"

    if not database_path.exists():
        logger.error(f"Datenbank nicht gefunden: {database_path}")
        return 1

    # Ziel-Pfad bestimmen
    if args.target:
        target_path = Path(args.target)
        if not target_path.is_absolute():
            target_path = base_dir / target_path
    else:
        target_path = projects_dir

    if not target_path.exists():
        logger.error(f"Ziel-Pfad nicht gefunden: {target_path}")
        return 1

    logger.info(f"Ziel: {target_path}")
    logger.info(f"Datenbank: {database_path}")

    if args.dry_run:
        logger.info("DRY-RUN Modus - keine Änderungen werden gemacht")

    # Migration ausführen
    migrator = MarkdownMigrator(target_path, database_path)

    if target_path.is_file() and target_path.suffix == ".md":
        # Einzelne Datei migrieren
        if args.dry_run:
            logger.info(f"Würde migrieren: {target_path}")
        else:
            migrator._migrate_file(target_path)
    else:
        # Ordner oder komplette Migration
        if args.dry_run:
            markdown_files = list(target_path.rglob("*.md"))
            logger.info(f"Würde {len(markdown_files)} Dateien migrieren:")
            for md_file in markdown_files:
                logger.info(f"  - {md_file}")
        else:
            migrator.migrate_all()

    return 0


if __name__ == "__main__":
    sys.exit(main())
