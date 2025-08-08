import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Anwendungskonfiguration für yt_database.
    Attributes:
        debug (bool): Debug-Modus aktivieren.
        database_url (str): Datenbank-URL.
        api_key (str): API-Key für externe Dienste.
        test_video_id (str): Beispiel-Transcript-ID für Tests.
        use_real_services (bool): Wenn True, werden echte Services verwendet, sonst Mocks.
        webview_url (str): Standard-URL, die im WebView geladen wird.
    Beispiel:
        >>> from yt_database.config.settings import settings
        >>> print(settings.debug)
        False
    """

    debug: bool = Field(default=False, description="Debug-Modus aktivieren")
    database_url: str = Field(default="", description="Datenbank-URL")
    api_key: str = Field(default="", description="API-Key für externe Dienste")
    test_video_id: str = Field(default="", description="Beispiel-Transcript-ID für Tests")
    prompt_type: Literal["youtube_comment", "detailed_database"] = Field(
        default="youtube_comment",
        description="Der zu verwendende Prompt-Typ ('youtube_comment' oder 'detailed_database').",
    )
    transcription_provider: Literal["api", "yt_dlp"] = Field(
        default="yt_dlp",
        description="Der zu verwendende Transkript-Service ('api' oder 'yt_dlp').",
    )
    yt_dlp_cookies_path: str = Field(default="./cookies.txt", description="Pfad zu den yt-dlp-Cookies")
    use_yt_dlp_cookies: bool = Field(
        default=True,
        description="Steuert, ob yt-dlp-Cookies verwendet werden (empfohlen: True für private/regionale Videos, False für öffentlich zugängliche Videos ohne Login)",
    )
    use_real_services: bool = Field(
        default=True,
        description="Wenn True, werden echte Services verwendet, sonst Mocks",
    )
    default_interval: int = Field(default=60, description="Standard-Intervall für Abfragen")
    default_max_videos: int = Field(default=10, description="Maximale Anzahl Videos")
    project_path: str = Field(default="./projects", description="Pfad zum Projektverzeichnis")
    last_channel_url: str = Field(default="", description="Zuletzt geöffnete Kanal-URL")
    main_window_geometry: str = Field(
        default="100,100,900,650",
        description="Persistente Geometrie des Hauptfensters (serialisiert)",
    )
    web_window_geometry: str = Field(
        default="500,100,800,600",
        description="Persistente Geometrie des WebView-Fensters (serialisiert)",
    )
    webview_url: str = Field(
        default="https://www.example.com/",
        description="Standard-URL, die im WebView geladen wird.",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @classmethod
    def load_from_yaml(cls, path: str = "yt_database.yaml") -> "Settings":
        """
        Lädt die Settings aus einer YAML-Datei. Fehlt die Datei, werden Defaults verwendet.
        """
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        return cls()

    def save_to_yaml(self, path: str = "yt_database.yaml") -> None:
        """
        Speichert die aktuellen Settings in eine YAML-Datei.
        """
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.model_dump(), f, allow_unicode=True, sort_keys=False)


# --- NEUER CODE START ---

# Die settings.py liegt in src/yt_database/config/
# Wir gehen drei Ebenen hoch, um zum Projekt-Root zu gelangen (wo sich 'src' befindet)
# src/yt_database/config -> src/yt_database -> src -> PROJECT_ROOT
# Wenn Ihr Projekt-Root das 'src'-Verzeichnis selbst ist, ändern Sie es zu .parent.parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Definieren Sie die Pfade für die Styles
# Diese werden nicht in der YAML gespeichert, sondern sind statische Pfade
STYLES_PATH = PROJECT_ROOT / "yt_database" / "resources" / "styles"
STYLESHEET_FILE = STYLES_PATH / "main.qss"
# --- NEUER CODE ENDE ---


settings = Settings.load_from_yaml()
