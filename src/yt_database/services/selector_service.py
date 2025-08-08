"""
SelectorService: Zentrale Verwaltung und Bereitstellung aller CSS-Selektoren für die Web-Automatisierung.

Dieses Modul stellt typsichere, strukturierte und leicht wartbare Selektor-Konfigurationen für alle UI-Komponenten bereit.
Jede Selektor-Dataclass implementiert ein Protokoll aus protocols.py und ist als frozen dataclass deklariert.
Die zentrale Serviceklasse aggregiert alle Selektoren und stellt sie als Attribute zur Verfügung.

Example:
    selectors = SelectorService()
    print(selectors.tab.TAB_LABEL_SOURCES)  # 'Quellen'
"""

from dataclasses import dataclass

from loguru import logger

from .protocols import (
    AddSourceButtonSelectorProtocol,
    AddSourceDialogSelectorProtocol,
    AllSourcesCheckboxSelectorProtocol,
    CopyTextChipSelectorProtocol,
    InsertButtonSelectorProtocol,
    PasteTextDialogSelectorProtocol,
    ProcessingSpinnerSelectorProtocol,
    QueryFieldSelectorProtocol,
    SendButtonSelectorProtocol,
    TabSelectorProtocol,
)


@dataclass(frozen=True)
class TabSelector(TabSelectorProtocol):
    """Selektoren für die Haupt-Tabs der Web-App (z.B. 'Quellen', 'Chat').

    Attributes:
        TAB_SELECTOR (str): CSS-Selektor für Tab-Elemente.
        TAB_LABEL_SOURCES (str): Label für den Quellen-Tab.
        TAB_LABEL_CHAT (str): Label für den Chat-Tab.
    """

    # CSS-Selektor für Tab-Elemente
    TAB_SELECTOR: str = 'div[role="tab"]'
    # Label für den Quellen-Tab
    TAB_LABEL_SOURCES: str = "Quellen"
    # Label für den Chat-Tab
    TAB_LABEL_CHAT: str = "Chat"


@dataclass(frozen=True)
class AllSourcesCheckboxSelector(AllSourcesCheckboxSelectorProtocol):
    """Selektor für das 'Alle Quellen auswählen'-Checkbox-Element.

    Attributes:
        CHECKBOX_SELECTOR (str): CSS-Selektor für die Checkbox.
        CHECKED_CLASS (str): CSS-Klasse für ausgewählt.
        UNCHECKED_CLASS (str): CSS-Klasse für nicht ausgewählt.
    """

    # CSS-Selektor für die Checkbox
    CHECKBOX_SELECTOR: str = 'input[aria-label="Alle Quellen auswählen"]'
    # Klasse, wenn die Checkbox ausgewählt ist
    CHECKED_CLASS: str = "mdc-checkbox--selected"
    # Klasse, wenn die Checkbox nicht ausgewählt ist
    UNCHECKED_CLASS: str = "mdc-checkbox--unselected"


@dataclass(frozen=True)
class AddSourceButtonSelector(AddSourceButtonSelectorProtocol):
    """Selektor für den 'Quelle hinzufügen'-Button.

    Attributes:
        BUTTON (str): CSS-Selektor für den Button.
    """

    # CSS-Selektor für den Button
    BUTTON: str = 'button[aria-label="Quelle hinzufügen"]'


@dataclass(frozen=True)
class AddSourceDialogSelector(AddSourceDialogSelectorProtocol):
    """Selektor für das Icon im 'Quelle hinzufügen'-Dialog.

    Attributes:
        ICON_NAME (str): Name des Icons.
    """

    # Name des Icons im Dialog
    ICON_NAME: str = "content_paste"


@dataclass(frozen=True)
class PasteTextDialogSelector(PasteTextDialogSelectorProtocol):
    """Selektor für das Textfeld im 'Text einfügen'-Dialog.

    Attributes:
        TEXTAREA_SELECTOR (str): CSS-Selektor für das Textfeld.
    """

    # CSS-Selektor für das Textfeld
    TEXTAREA_SELECTOR: str = 'textarea[matinput][formcontrolname="text"]'


@dataclass(frozen=True)
class InsertButtonSelector(InsertButtonSelectorProtocol):
    """Selektor für den 'Einfügen'-Button im Dialog.

    Attributes:
        BUTTON_SELECTOR (str): CSS-Selektor für den Button.
        BUTTON_LABEL (str): Label des Buttons.
    """

    # Allgemeiner Selektor für alle Buttons
    BUTTON_SELECTOR: str = "button"
    # Exakter Text, der den Button identifiziert
    BUTTON_LABEL: str = "Einfügen"


@dataclass(frozen=True)
class CopyTextChipSelector(CopyTextChipSelectorProtocol):
    """Selektor für das 'Kopierter Text'-Chip-Element.

    Attributes:
        CHIP_SELECTOR (str): CSS-Selektor für das Chip-Element.
        CHIP_LABEL (str): Label des Chips.
    """

    # Stabile Selektor für Chips dieser Art
    CHIP_SELECTOR: str = "mat-chip.chip-group__chip"
    # Text, der den Chip identifiziert
    CHIP_LABEL: str = "Kopierter Text"


@dataclass(frozen=True)
class QueryFieldSelector(QueryFieldSelectorProtocol):
    """Selektor für das Anfrage-Textfeld.

    Attributes:
        TEXTAREA_SELECTOR (str): CSS-Selektor für das Textfeld.
    """

    # CSS-Selektor für das Anfragefeld
    TEXTAREA_SELECTOR: str = 'textarea[aria-label="Feld für Anfragen"]'


@dataclass(frozen=True)
class SendButtonSelector(SendButtonSelectorProtocol):
    """Selektor für den 'Senden'-Button.

    Attributes:
        BUTTON_SELECTOR (str): CSS-Selektor für den Button.
    """

    # CSS-Selektor für den Senden-Button
    BUTTON_SELECTOR: str = 'button.submit-button[aria-label="Senden"]:not([disabled])'


@dataclass(frozen=True)
class ProcessingSpinnerSelector(ProcessingSpinnerSelectorProtocol):
    """Selektor für den Lade-/Verarbeitungsspinne.

    Attributes:
        SPINNER_SELECTOR (str): CSS-Selektor für den Spinner.
    """

    # CSS-Selektor für den Spinner
    SPINNER_SELECTOR: str = '[role="progressbar"].mat-mdc-progress-spinner[mode="indeterminate"]'


class SelectorService:
    """Zentrale Serviceklasse für alle UI-Selektoren der Web-Automatisierung.

    Stellt typsichere, strukturierte Selektoren als Attribute bereit, um die Wartbarkeit und Testbarkeit der Automatisierung zu erhöhen.

    Example:
        selectors = SelectorService()
        selectors.tab.TAB_LABEL_SOURCES  # 'Quellen'
    """

    def __init__(self) -> None:
        """Initialisiert alle Selektor-Dataclasses als Attribute.

        Example:
            selectors = SelectorService()
            selectors.add_source_button.BUTTON_SELECTOR  # 'button[aria-label="Quelle hinzufügen"]'
        """
        logger.debug("Initialisiere SelectorService und alle Selektor-Dataclasses.")
        # Initialisiere Tab-Selektoren
        self.tab = TabSelector()
        # Initialisiere Einfügen-Button-Selektor
        self.insert_button = InsertButtonSelector()
        # Initialisiere Spinner-Selektor
        self.processing_spinner = ProcessingSpinnerSelector()
        # Initialisiere Quelle-hinzufügen-Button-Selektor
        self.add_source_button = AddSourceButtonSelector()
        # Initialisiere Dialog-Icon-Selektor
        self.add_source_dialog = AddSourceDialogSelector()
        # Initialisiere Textfeld-Selektor im Dialog
        self.paste_text_dialog = PasteTextDialogSelector()
        # Initialisiere Checkbox-Selektor für alle Quellen
        self.all_sources_checkbox = AllSourcesCheckboxSelector()
        # Initialisiere Chip-Selektor für kopierten Text
        self.copy_text_chip = CopyTextChipSelector()
        # Initialisiere Anfragefeld-Selektor
        self.query_field = QueryFieldSelector()
        # Initialisiere Senden-Button-Selektor
        self.send_button = SendButtonSelector()
