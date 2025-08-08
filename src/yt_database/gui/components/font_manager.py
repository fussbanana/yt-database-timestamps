# src/yt_database/gui/components/font_manager.py

import os
from typing import Any, Dict, Optional

from loguru import logger
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication


class FontManager:
    """
    Manager für die Inter Font-Integration in der Anwendung.

    Verwaltet das Laden, Konfigurieren und Anwenden der Inter Font
    für eine konsistente und professionelle UI-Darstellung.
    """

    def __init__(self) -> None:
        """Initialisiert den FontManager."""
        self.font_variants: Dict[str, QFont] = {}
        self.font_family: Optional[str] = None

    def setup_inter_font(self) -> bool:
        """
        Lädt und konfiguriert die Inter Font für die gesamte Anwendung.

        Returns:
            bool: True wenn Font erfolgreich geladen, False bei Fehlern
        """
        logger.debug("FontManager: Lade statische Inter Fonts für UI.")

        try:
            # Basis-Pfad zu den Font-Ressourcen
            font_base_path = os.path.join("src", "yt_database", "resources", "fonts", "Inter")
            static_path = os.path.join(font_base_path, "static")

            if not os.path.isdir(static_path):
                logger.error(f"Statisches Font-Verzeichnis nicht gefunden: {static_path}")
                return False

            font_ids = []

            for font_file in os.listdir(static_path):
                if font_file.lower().endswith(".ttf"):
                    full_path = os.path.join(static_path, font_file)
                    font_id = QFontDatabase.addApplicationFont(full_path)
                    if font_id != -1:
                        font_ids.append(font_id)
                    else:
                        logger.warning(f"FontManager: Fehler beim Laden der statischen Font: {full_path}")

            # Standard-Font für die Anwendung setzen
            if font_ids:
                logger.info(f"FontManager: {len(font_ids)} statische Inter-Fonts geladen.")

                families = QFontDatabase.applicationFontFamilies(font_ids[0])
                if families:
                    self.font_family = families[0]
                    logger.info(f"FontManager: Verwende Font-Familie '{self.font_family}'.")

                    inter_font = QFont(self.font_family)
                    inter_font.setPointSize(10)
                    inter_font.setWeight(QFont.Weight.Normal)

                    app = QApplication.instance()
                    if app and isinstance(app, QApplication):
                        app.setFont(inter_font)
                        logger.info("FontManager: Inter Font erfolgreich als Standard-Font gesetzt.")

                    self._setup_font_variants(self.font_family)
                    return True
                else:
                    logger.error("FontManager: Keine Font-Familien aus geladenen Inter Fonts gefunden.")
                    return False
            else:
                logger.error("FontManager: Keine statischen Inter Fonts konnten geladen werden.")
                return False

        except Exception as e:
            logger.error(f"FontManager: Kritischer Fehler beim Setup der Inter Font: {e}")
            return False

    def _setup_font_variants(self, font_family: str) -> None:
        """Konfiguriert verschiedene Font-Varianten für spezielle UI-Bereiche.

        Args:
            font_family: Der Name der geladenen Inter Font-Familie
        """
        logger.debug("FontManager: Konfiguriere Inter Font-Varianten für UI-Bereiche.")

        try:

            self.font_variants = {
                "ui_default": QFont(font_family, 10, QFont.Weight.Normal),
                "ui_header": QFont(font_family, 14, QFont.Weight.Medium),
                "ui_title": QFont(font_family, 12, QFont.Weight.Medium),
                "ui_label": QFont(font_family, 9, QFont.Weight.Normal),
                "ui_small": QFont(font_family, 8, QFont.Weight.Normal),
                "ui_button": QFont(font_family, 10, QFont.Weight.Medium),
                "ui_code": QFont(font_family, 9, QFont.Weight.Normal),
                "dashboard_stat": QFont(font_family, 16, QFont.Weight.Bold),
                "dashboard_label": QFont(font_family, 11, QFont.Weight.Normal),
            }

            for font_variant in self.font_variants.values():
                font_variant.setStyleHint(QFont.StyleHint.SansSerif)
                font_variant.setHintingPreference(QFont.HintingPreference.PreferDefaultHinting)

            logger.debug(f"FontManager: Font-Varianten für '{font_family}' erfolgreich konfiguriert.")

        except Exception as e:
            logger.error(f"FontManager: Fehler beim Setup der Font-Varianten: {e}")


    def get_font(self, variant: str = "ui_default") -> QFont:
        """
        Gibt eine spezifische Font-Variante zurück.
        """
        if variant in self.font_variants:
            return self.font_variants[variant]
        else:
            logger.warning(f"FontManager: Font-Variante '{variant}' nicht gefunden, verwende Fallback.")
            return QFont()

    def apply_font_to_widget(self, widget, font_variant: str = "ui_default") -> None:
        """
        Hilfsmethode zum Anwenden einer Font-Variante auf ein spezifisches Widget.
        """
        try:
            font = self.get_font(font_variant)
            widget.setFont(font)
        except Exception as e:
            logger.error(f"FontManager: Fehler beim Anwenden der Font auf Widget: {e}")

    def apply_fonts_to_widgets(self, widgets_dict: Dict[str, Any]) -> None:
        """
        Wendet die Inter Font auf verschiedene Widgets an für ein konsistentes Design.
        """
        logger.debug("FontManager: Wende Inter Font auf Widgets an.")
        try:
            widget_font_mapping = {
                "sidebar": "ui_default",
                "dashboard_widget": "ui_default",
                "explorer_widget": "ui_small",
                "database_widget": "ui_default",
                "batch_transcription_widget": "ui_default",
                "log_widget": "ui_code",
            }
            for widget_name, font_variant in widget_font_mapping.items():
                if widget_name in widgets_dict and widgets_dict[widget_name] is not None:
                    widget = widgets_dict[widget_name]
                    self.apply_font_to_widget(widget, font_variant)
                    logger.debug(f"FontManager: Inter Font '{font_variant}' auf {widget_name} angewendet.")
        except Exception as e:
            logger.error(f"FontManager: Fehler beim Anwenden der Fonts auf Widgets: {e}")

    def get_available_variants(self) -> list[str]:
        """
        Gibt eine Liste aller verfügbaren Font-Varianten zurück.
        """
        return list(self.font_variants.keys())

    def is_inter_loaded(self) -> bool:
        """
        Prüft, ob die Inter Font erfolgreich geladen wurde.
        """
        return self.font_family is not None and len(self.font_variants) > 0


font_manager = FontManager()


def setup_application_fonts() -> bool:
    """
    Convenience-Funktion zum Setup der Anwendungs-Fonts.
    """
    return bool(font_manager.setup_inter_font())


def get_ui_font(variant: str = "ui_default") -> QFont:
    """
    Convenience-Funktion zum Abrufen einer UI-Font.
    """
    return font_manager.get_font(variant)


def apply_font_to_widget(widget, variant: str = "ui_default") -> None:
    """
    Convenience-Funktion zum Anwenden einer Font auf ein Widget.
    """
    font_manager.apply_font_to_widget(widget, variant)
