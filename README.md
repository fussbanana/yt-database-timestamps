# yt-database

## Update

### Implementierte Features - Übersicht

### (Basis)

- 5 Suchstrategien: AUTO, EXACT, ALL, ANY, FUZZY
- BM25-Relevanz-Ranking statt Standard-FTS5
- Query-Parser für komplexe Syntax: "exakte Phrasen", +required, -excluded
- Snippet-Highlighting in Suchergebnissen

### (Erweiterte Suche)

- Synonym-Expansion mit 15 semantischen Kategorien
- SearchSuggestionProvider mit Datenbank-basiertem Ranking
- Live-Suchvorschläge in GUI
- Intelligente Auto-Strategie mit Fallback-Logik

### (AI-Semantische Suche)

- Semantische Suche mit AI-Embeddings (384-dimensionale Vektoren)
- Bedeutungsbasierte Suche ohne exakte Keywords
- Hybrid-Suche: 60% Semantic + 40% Keywords, gewichtet
- Vector Database mit SQLite BLOB-Speicherung
- CPU-optimierte sentence-transformers Integration

### GUI-Integration

- 7 Suchstrategien in ComboBox verfügbar
- SearchWidgetTree mit Live-Suggestions
- SignalHandler verbindet Backend mit Frontend
- Vollständige Protokoll-basierte Typisierung

### Technische Details

- Cosine-Similarity für Vektor-Ähnlichkeitsberechnung
- Batch-Embedding für bestehende Kapitel
- Lazy-Loading für AI-Model (150MB)
- Performance-Monitoring und Caching-bereit

### Aktuelle Suchstrategien (7 total)

1. AUTO - Intelligente automatische Auswahl
2. EXACT - Exakte Phrasen-Suche
3. ALL - Alle Wörter müssen vorkommen (AND)
4. ANY - Mindestens ein Wort (OR)
5. FUZZY - Wildcards und Prefix-Matching
6. SEMANTIC - Reine AI-basierte Bedeutungssuche
7. HYBRID - Kombiniert AI + Keywords optimal

## Übersicht

`yt-database` ist eine modulare Python-Anwendung zur automatisierten Verarbeitung, Analyse und Verwaltung von YouTube-Transkripten und Metadaten. Das Projekt bietet eine moderne GUI (PySide6), eine CLI, sowie eine flexible Service-Architektur für verschiedene Workflows (Transkription, Prompt-Generierung, Datenbankverwaltung).

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

Voraussetzungen:

- Python ≥ 3.12
- Poetry
- SQLite3 (CLI) empfohlen, Datenbank-Engine ist SQLite mit FTS5
- Node.js und npm (für SASS-Live-Kompilierung)

Beispiele zur Installation unter Linux:

```bash
# Debian/Ubuntu
sudo apt update
sudo apt install -y sqlite3 nodejs npm

# Fedora
sudo dnf install -y sqlite nodejs npm
```

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

## SASS-Live-Kompilierung (SCSS ➜ QSS)

Die GUI verwendet ein Stylesheet in QSS-Form (`main.qss`). Zur komfortablen Entwicklung wird `main.qss` aus der SASS/SCSS-Quelle `main.scss` erzeugt und per Watch-Task laufend neu kompiliert. Der `StyleManager` lädt Änderungen an `main.qss` automatisch live in die laufende Anwendung.

Voraussetzungen:

- Node.js und npm installiert

Installation der Abhängigkeiten (Dart Sass als Dev-Dependency):

```bash
npm install --save-dev sass
```

Einmalige Kompilierung (ohne Watch):

```bash
npx sass src/yt_database/resources/styles/main.scss src/yt_database/resources/styles/main.qss
```

Watch-Mode (empfohlen für die Entwicklung):

```bash
npx sass --watch \

## Beispiel-Workflow
```

Hinweise:

- Stelle sicher, dass die GUI läuft (z. B. per `poetry run gui`). Der `StyleManager` beobachtet `main.qss` und lädt Änderungen automatisch.
- QSS ist ein Subset von CSS. Verwende nur Eigenschaften, die von Qt Stylesheets unterstützt werden.
- Falls Ressourcen (Icons) geändert werden, kompiliere die Qt-Resource-Datei optional neu:

 ```bash
 poetry run python scripts/compile_resources.py
 ```

1. Video-URL oder ID eingeben
2. Transkript generieren (GUI oder CLI)
3. Kapitel extrahieren und speichern
4. Analyse-Prompt anwenden
5. Ergebnisse in Datenbank und GUI anzeigen

## Lizenz

MIT

---

Für weitere Informationen siehe die Modul-Dokumentationen im Ordner `Modul Dokumentation`.
