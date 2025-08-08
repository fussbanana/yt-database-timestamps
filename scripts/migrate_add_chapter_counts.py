#!/usr/bin/env python3
"""
Migration Script: Add chapter count fields to Transcript table

Adds:
- chapter_count: IntegerField for simple chapters (YouTube comment format)
- detailed_chapter_count: IntegerField for detailed chapters (database format)

Also fixes Channel.handle unique constraint issues by allowing NULL for duplicates.
"""

import os
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from loguru import logger
from peewee import IntegerField, SQL

from yt_database.database import Channel, Transcript, db


def migrate_add_chapter_counts():
    """Add chapter count fields to Transcript table and fix Channel constraints."""
    logger.info("Starting migration: Add chapter count fields")

    try:
        with db.atomic():
            logger.info("Adding chapter_count field to Transcript table...")

            # Add chapter_count field
            try:
                db.execute_sql("ALTER TABLE transcript ADD COLUMN chapter_count INTEGER DEFAULT 0")
                logger.success("chapter_count field added")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("chapter_count field already exists")
                else:
                    logger.error(f"Error adding chapter_count: {e}")
                    raise

            # Add detailed_chapter_count field
            try:
                db.execute_sql("ALTER TABLE transcript ADD COLUMN detailed_chapter_count INTEGER DEFAULT 0")
                logger.success("detailed_chapter_count field added")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("detailed_chapter_count field already exists")
                else:
                    logger.error(f"Error adding detailed_chapter_count: {e}")
                    raise

            # Fix Channel handle unique constraint issues
            logger.info("Fixing Channel handle unique constraint issues...")

            # Find channels with duplicate handles
            duplicate_handles = (
                Channel.select(Channel.handle)
                .where(Channel.handle.is_null(False))
                .group_by(Channel.handle)
                .having(SQL("COUNT(*) > 1"))
            )

            for handle_row in duplicate_handles:
                handle = handle_row.handle
                logger.warning(f"Found duplicate handle: {handle}")

                # Keep the first channel with this handle, set others to NULL
                channels_with_handle = Channel.select().where(Channel.handle == handle).order_by(Channel.channel_id)

                channels = list(channels_with_handle)
                if len(channels) > 1:
                    # Keep the first, set others to NULL
                    for channel in channels[1:]:
                        channel.handle = None
                        channel.save()
                        logger.info(f"Set handle to NULL for channel {channel.channel_id} (was: {handle})")

            logger.success("Migration completed successfully")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


def main():
    """Run the migration."""
    logger.info("Database Migration: Add chapter count fields")

    # Ensure database connection
    if db.is_closed():
        db.connect()

    try:
        migrate_add_chapter_counts()
        logger.success("All migrations completed successfully!")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
    finally:
        if not db.is_closed():
            db.close()


if __name__ == "__main__":
    main()
