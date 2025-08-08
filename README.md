# yt-database-timestamps

## Übersicht

`yt-database-timestamps` ist eine modulare Python-Anwendung zur automatisierten Verarbeitung, Analyse und Verwaltung von YouTube-Transkripten und Metadaten. Das Projekt bietet eine moderne GUI (PySide6), eine CLI, sowie eine flexible Service-Architektur für verschiedene Workflows (Transkription, Prompt-Generierung, Datenbankverwaltung).

## Features

- Automatisierte Transkript- und Kapitelgenerierung für YouTube-Videos
- Batch- und Einzel-Transkription
- Moderne GUI mit Live-Reload, Font- und Style-Management
- CLI-Tools für schnelle Verarbeitung und Integration
- Flexible Service- und Worker-Architektur (GeneratorService, WorkerManager, ServiceFactory)
- Persistente SQLite-Datenbank mit FTS5-Suche
- Konfigurierbare Prompts und Analyse-Workflows
- Umfangreiche Test- und Mock-Services


## Installation

```bash
# Voraussetzungen: Python >= 3.12, poetry
poetry install
```

## Starten der Anwendung

```bash
# GUI starten
poetry run gui

# CLI-Transkription
poetry run python src/yt_database/cli/get_video_transcription.py --help
```

## Architektur

- **src/yt_database/database.py**: Datenbankmodelle und Initialisierung
- **src/yt_database/services/**: Zentrale Services (Transkription, Generator, File, Prompt, Formatter, etc.)
- **src/yt_database/gui/**: GUI-Komponenten, Widgets, MainWindow, WebView
- **src/yt_database/cli/**: Kommandozeilentools für Transkription und Metadaten
- **src/yt_database/config/**: Settings und Logging-Konfiguration
- **src/yt_database/models/**: Datenmodelle für Suche und Transkripte
- **src/yt_database/resources/**: Fonts, Styles, Icons, Prompts

## Hauptmodule & Klassen

- **MainWindow**: Einstiegspunkt der GUI
- **WorkerManager**: Verwaltung von Hintergrund-Workern
- **GeneratorService**: Orchestriert die Transkriptions- und Prompt-Workflows
- **ServiceFactory**: Erzeugt und konfiguriert alle Services
- **BatchTranscriptionService / SingleTranscriptionService**: Verarbeitung von Transkripten
- **AnalysisPromptService**: Verwaltung und Generierung von Prompts
- **FontManager / StyleManager / UiManager**: GUI-Design und Live-Reload
- **FileService / ProjectManagerService**: Dateiverwaltung und Projektmanagement

## Datenbank

- SQLite mit FTS5 für schnelle Volltextsuche
- Modelle: Channel, Transcript, Chapter
- Initialisierung: `src/yt_database/database.py`

## Konfiguration

- Settings: `src/yt_database/config/settings.py`
- Logging: `src/yt_database/config/logging_config.py`
- Prompts: `src/yt_database/resources/youtube_comment`, `detailed_database`

## Tests & Entwicklung

- Test- und Mock-Services unter `src/yt_database/services/mocks/`
- Coverage-Reports unter `htmlcov/`
- Diagramme und Architekturübersichten unter `diagram.md`, `yt-database _ sequencechart.svg`

## Beispiel-Workflow

1. Video-URL oder ID eingeben
2. Transkript generieren (GUI oder CLI)
3. Kapitel extrahieren und speichern
4. Analyse-Prompt anwenden
5. Ergebnisse in Datenbank und GUI anzeigen

## Lizenz

MIT

---

Für weitere Informationen siehe die Modul-Dokumentationen im Ordner `Modul Dokumentation`.
