"""
Service für die Verwaltung verschiedener Analyse-Prompts für Kapitel-Generierung.

Dieses Modul bietet eine zentrale Schnittstelle zur Auswahl zwischen verschiedenen
Prompt-Typen für die Kapitel-Generierung:
- YouTube-Kommentar-Prompts (kurze, grobe Kapitel für Navigation)
- Detaillierte Datenbank-Prompts (granulare Kapitel für Suche und Analyse)
"""

from enum import Enum
from pathlib import Path

from loguru import logger

from yt_database.config.settings import Settings


class PromptType(Enum):
    """Enum für verschiedene Prompt-Typen."""

    YOUTUBE_COMMENT = "youtube_comment"
    DETAILED_DATABASE = "detailed_database"


class AnalysisPromptService:
    """
    Service für die Verwaltung und Bereitstellung verschiedener Analyse-Prompts.

    Attributes:
        settings (Settings): Globale Settings für Pfade und Konfiguration.
        prompt_files (Dict[PromptType, str]): Mapping von Prompt-Typen zu Dateinamen.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """
        Initialisiert den AnalysisPromptService.

        Args:
            settings (Settings, optional): Globale Settings. Defaults to None.
        """
        self.settings = settings or Settings()
        self.prompt_files = {
            PromptType.YOUTUBE_COMMENT: "youtube_comment",
            PromptType.DETAILED_DATABASE: "detailed_database",
        }
        logger.debug("AnalysisPromptService initialisiert.")

    def get_prompt(self, prompt_type: PromptType) -> str:
        """
        Lädt den Prompt-Text für den angegebenen Typ.

        Args:
            prompt_type (PromptType): Der gewünschte Prompt-Typ.

        Returns:
            str: Der Prompt-Text.

        Raises:
            FileNotFoundError: Wenn die Prompt-Datei nicht gefunden wird.
            ValueError: Wenn ein unbekannter Prompt-Typ angegeben wird.
        """
        if prompt_type not in self.prompt_files:
            raise ValueError(f"Unbekannter Prompt-Typ: {prompt_type}")

        filename = self.prompt_files[prompt_type]
        prompt_path = Path(__file__).parent.parent / "resources" / filename

        logger.debug(f"Lade Prompt vom Typ {prompt_type.value} aus {prompt_path}")

        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()
            logger.debug(f"Prompt erfolgreich geladen: {len(content)} Zeichen")
            return content
        except FileNotFoundError:
            logger.error(f"Prompt-Datei nicht gefunden: {prompt_path}")
            raise

    def get_available_prompt_types(self) -> list[PromptType]:
        """
        Gibt alle verfügbaren Prompt-Typen zurück.

        Returns:
            list[PromptType]: Liste aller verfügbaren Prompt-Typen.
        """
        return list(self.prompt_files.keys())

    def get_prompt_description(self, prompt_type: PromptType) -> str:
        """
        Gibt eine beschreibende Bezeichnung für den angegebenen Prompt-Typ zurück.

        Args:
            prompt_type (PromptType): Der Prompt-Typ.

        Returns:
            str: Benutzerfreundliche Beschreibung des Prompt-Typs.
        """
        descriptions = {
            PromptType.YOUTUBE_COMMENT: "Grobe Kapitel für YouTube-Kommentare (max. 4-5 Unterpunkte)",
            PromptType.DETAILED_DATABASE: "Detaillierte Kapitel für Datenbank-Suche (3-8 Unterpunkte)",
        }
        return descriptions.get(prompt_type, "Unbekannter Prompt-Typ")

    def get_target_section(self, prompt_type: PromptType) -> str:
        """
        Gibt die Ziel-Sektion zurück, in die die Kapitel geschrieben werden sollen.

        Args:
            prompt_type (PromptType): Der Prompt-Typ.

        Returns:
            str: Die Ziel-Sektion für die Kapitel-Platzierung.
        """
        sections = {
            PromptType.YOUTUBE_COMMENT: "## Kapitel mit Zeitstempeln",
            PromptType.DETAILED_DATABASE: "## Detaillierte Kapitel",
        }
        return sections.get(prompt_type, "## Detaillierte Kapitel")

    def get_chapter_database_type(self, prompt_type: PromptType) -> str:
        """
        Gibt den entsprechenden chapter_type für die Datenbank zurück.

        Args:
            prompt_type (PromptType): Der Prompt-Typ.

        Returns:
            str: Der chapter_type für die Datenbank ("summary" oder "detailed").
        """
        types = {
            PromptType.YOUTUBE_COMMENT: "summary",
            PromptType.DETAILED_DATABASE: "detailed",
        }
        return types.get(prompt_type, "detailed")
