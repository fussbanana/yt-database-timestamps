# Migrationsskripte für yt-database

Dieses Verzeichnis enthält Skripte zur Migration von Markdown-Dateien in eine transcript-zentrierte Wissensdatenbank.

## Verfügbare Skripte

### 1. migrate_markdown_to_database.py

Das Hauptmigrationsskript, das den gesamten `projects`-Ordner durchsucht und alle Markdown-Dateien migriert. Es verwendet das Peewee ORM für sichere und lesbare Datenbankinteraktionen.

### 2. migrate_cli.py

CLI-Tool für gezielte Migration einzelner Dateien oder Ordner.

**Verwendung:**

```bash
# Komplette Migration aller Dateien im projects-Ordner
poetry run python scripts/migrate_cli.py

# Einzelne Datei migrieren
poetry run python scripts/migrate_cli.py projects/@99ZUEINS/video_id/file.md

# Bestimmten Ordner migrieren
poetry run python scripts/migrate_cli.py projects/@99ZUEINS

# Dry-Run (zeigt nur an, was gemacht würde, ohne DB-Änderungen)
poetry run python scripts/migrate_cli.py --dry-run

# Migration erzwingen (überschreibt existierende Kapitel)
poetry run python scripts/migrate_cli.py --force
```

## Datenbankstruktur

Die Datenbank ist transcript-zentriert aufgebaut und besteht aus drei normalisierten Tabellen:

1. **Channel**: Speichert eindeutige Kanalinformationen (`channel_id`, `name`, `url`, `handle`).
2. **Transcript**: Die zentrale Tabelle. Speichert Metadaten zu einem Transkript, das durch die `video_id` seiner YouTube-Quelle eindeutig identifiziert wird.
3. **Chapter**: Speichert alle Kapitel und verweist auf einen `Transcript`-Eintrag. Ein `chapter_type`-Feld unterscheidet zwischen verschiedenen Kapitelarten (z.B. `summary`, `detailed`).

## Unterstützte Markdown-Strukturen

### YAML-Frontmatter

```yaml
---
title: Die Letzte Generation - Radikaler Aufstand des Gewissens?
video_id: Rg992slj5Cc
video_url: https://www.youtube.com/watch?v=Rg992slj5Cc
channel_id: UCTRjcYzSUGb0UwTP1gNf1uQ
channel_name: 99 ZU EINS
channel_handle: "@99ZUEINS"
publish_date: 20230702
duration: 3:03:21
online: true
error:
---
```

### Kapitel-Formate

Das Skript kann nun mehrere, unterschiedlich benannte Kapitelblöcke parsen.

**Block 1: Zusammenfassende Kapitel**

~~~markdown
## Kapitel mit Zeitstempeln

• 00:00:14: Begrüßung, Sendungsformat, Debattenkontext.
• 00:04:10: Fokus der Kritik, Hauptdifferenzen betont.

~~~

**Block 2: Detaillierte Kapitel**

~~~markdown
## Detaillierte Kapitel

• 00:01:43: Herzlich willkommen bei 99 zu 1.
• 00:01:49: Vorstellung der Diskussionsteilnehmer: Usama Taraben und Tim Wechselmann-Cassim.
~~~

### Transkript-Erkennung

Das Skript erkennt automatisch, ob ein Transkript echten Inhalt hat:

- Sucht nach der `## Transkript` Sektion.
- Prüft auf mindestens 5 Zeilen, die nicht nur Zeitstempel sind.

## Statistiken

Das Skript gibt nach der Migration detaillierte Statistiken aus, die die transcript-zentrierte Logik widerspiegeln:

- Anzahl verarbeiteter Dateien
- Anzahl erstellter/aktualisierter Transkript-Einträge
- Anzahl erstellter/übersprungener Kapitel
- Anzahl aufgetretener Fehler

## Beispiel-Output

~~~markdown
2025-08-04 10:30:00.100 | INFO | === Migrations-Statistiken ===
2025-08-04 10:30:00.100 | INFO | Verarbeitete Dateien: 15
2025-08-04 10:30:00.100 | INFO | Transkript-Einträge erstellt: 5
2025-08-04 10:30:00.100 | INFO | Transkript-Einträge aktualisiert: 10
2025-08-04 10:30:00.100 | INFO | Kapitel erstellt: 150
2025-08-04 10:30:00.100 | INFO | Kapitel übersprungen: 45
2025-08-04 10:30:00.100 | INFO | Fehler: 0
~~~~
