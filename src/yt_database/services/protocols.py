"""
Protokolle und Schnittstellen für alle Service-Komponenten von yt_database.

Dieses Modul definiert alle zentralen PEP 544-Protokolle für Worker, Services, Selektoren und UI-Komponenten.
Es ermöglicht robuste Typisierung, flexible Dependency Injection und eine klare Trennung zwischen Implementierung und Vertrag.

Alle Protokolle enthalten ausschließlich Methodensignaturen und Attribute, keine Implementierungen oder Defaultwerte.
Die Typisierung erfolgt strikt nach PEP 8 und PEP 544. Die Protokolle sind die Basis für alle Service- und Worker-Komponenten im Projekt.

Example:
    class MyService(FileServiceProtocol):
        def write(self, path: str, content: Any) -> None:
            ...

        def read_metadata_file(self, path: str) -> Dict[str, Any]:
            ...
"""

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    runtime_checkable,
)

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMainWindow

from yt_database.models.models import ChapterEntry, TranscriptData
from yt_database.services.analysis_prompt_service import PromptType

# --- Zirkulären Import für Typ-Prüfung auflösen ---
if TYPE_CHECKING:
    from yt_database.services.analysis_prompt_service import PromptType
    from yt_database.services.service_factory import ServiceFactory


@runtime_checkable
class FormatterServiceProtocol(Protocol):
    """Protokoll für Formatierungsdienste.

    Methods:
        format(transcript, metadata): Formatiert Transkript.
        parse_json3_transcript(file_path): Parst JSON3-Transkriptdatei.
    """

    def format(self, transcript_data: "TranscriptData") -> str:
        """Formatiert ein Transkript.

        Args:
            transcript (Any): Rohes Transkript.
            metadata (Dict[str, Any]): Metadaten.
        Returns:
            str: Formatierter Transkripttext.
        """
        ...

    def extract_metadata(self, metadata: Any) -> Dict[str, Any]:
        """Extrahiert Metadaten.

        Args:
            metadata (Any): Eingabemetadaten.
        Returns:
            Dict[str, Any]: Extrahierte Metadaten.
        """
        ...

    def parse_json3_transcript(self, file_path: str) -> list[dict[str, Any]]:
        """Parst eine JSON3-Transkriptdatei.

        Args:
            file_path (str): Pfad zur JSON3-Datei.
        Returns:
            list[dict[str, Any]]: Liste von Transkript-Abschnitten.
        """
        ...


@runtime_checkable
class FileServiceProtocol(Protocol):
    """Protokoll für Dateiservice-Operationen.

    Methods:
        write(path: str, content: Any) -> None: Schreibt Inhalt in eine Datei.
        read(path: str) -> str: Liest Inhalt aus einer Datei.
        write_transcript_file(transcript: TranscriptData) -> None: Schreibt Transkript in eine Datei.
    """

    def write(self, path: str, content: Any) -> None:
        """Schreibt beliebigen Inhalt in eine Datei.

        Args:
            path (str): Dateipfad.
            content (Any): Zu schreibender Inhalt.
        Returns:
            None
        """
        ...

    def read(self, path: str) -> str:
        """Liest den Inhalt einer Datei als String.

        Args:
            path (str): Dateipfad.
        Returns:
            str: Inhalt der Datei.
        """
        ...

    def write_transcript_file(self, transcript: "TranscriptData") -> None: ...


@runtime_checkable
class ProjectManagerProtocol(Protocol):
    """Protokoll für Projektmanagement-Operationen.
    Methods:
        get_all_channels(): Gibt alle Kanäle zurück.
        get_videos_for_channel(channel_id): Gibt Videos für Kanal zurück.
        add_videos_to_channel(channel_id, videos_data): Fügt Videos zu Kanal hinzu.
        update_channel_index(channel_id, metadata): Aktualisiert Kanalindex.
        create_project(id, video_id): Erstellt neues Projekt.
        update_index(video_data): Aktualisiert Index.
        is_transcribed(video_id): Prüft Transkriptionsstatus.
        mark_as_chaptered(video_id): Markiert Transcript als "chaptered".
        write_transcript_with_status(video_id, formatted, metadata): Schreibt Transkript mit Status.
        get_transcript_path_for_video_id(video_id, channel_handle): Gibt Pfad zum Transkript zurück.
    """

    def is_downloaded(self, video_id: str) -> bool:
        """
        Prüft, ob ein Transcript als heruntergeladen gilt.

        Args:
            video_id (str): Die YouTube-Transcript-ID.

        Returns:
            bool: True, wenn das Transcript als heruntergeladen gilt, sonst False.
        """
        ...

    def get_all_channels(self) -> List[Any]:
        """Gibt alle Kanäle zurück.

        Returns:
            List[Any]: Liste aller Kanäle.
        """
        ...

    def get_videos_for_channel(self, channel_id: str) -> List[Any]:
        """Gibt alle Videos für einen Kanal zurück.

        Args:
            channel_id (str): Kanal-ID.
        Returns:
            List[Any]: Liste der Videos.
        """
        ...

    def add_videos_to_channel(self, channel_id: str, videos_data: List[Dict[str, str]]) -> None:
        """Fügt Videos zu einem Kanal hinzu.

        Args:
            channel_id (str): Kanal-ID.
            videos_data (List[Dict[str, str]]): Videodaten.
        Returns:
            None
        """
        ...

    def update_channel_index(self, channel_id: str, metadata: Dict[str, Any]) -> None:
        """Aktualisiert den Kanalindex.

        Args:
            channel_id (str): Kanal-ID.
            metadata (Dict[str, Any]): Metadaten.
        Returns:
            None
        """
        ...

    def create_project(self, id: str, video_id: str) -> None:
        """Erstellt ein neues Projekt.

        Args:
            id (str): Projekt-ID.
            video_id (str): Transcript-ID.
        Returns:
            None
        """
        ...

    def update_index(self, transcript_data: TranscriptData) -> None:
        """Aktualisiert den Index mit Transkriptionsdaten.

        Args:
            transcript_data (TranscriptData): Transkriptionsdaten.
        Returns:
            None
        """
        ...

    def has_transcript_lines(self, video_id: str) -> bool:
        """Prüft, ob ein Transcript transkribiert wurde.

        Args:
            video_id (str): Transcript-ID.
        Returns:
            bool: True, wenn transkribiert.
        """
        ...

    def mark_as_chaptered(self, video_id: str) -> None:
        """Markiert ein Transcript als "chaptered".

        Args:
            video_id (str): Transcript-ID.
        Returns:
            None
        """
        ...

    def get_transcript_path_for_video_id(self, video_id: str, channel_handle: Optional[str] = None) -> str:
        """Gibt den Pfad zum Transkript für eine Transcript-ID zurück.

        Args:
            video_id (str): Transcript-ID.
            channel_handle (Optional[str]): Kanal-Handle (z.B. @99ZUEINS) (optional).
        Returns:
            str: Pfad zum Transkript.
        """
        ...

    def save_chapters_to_database(
        self, video_id: str, chapters: List[ChapterEntry], chapter_type: str = "detailed"
    ) -> None:
        """Speichert Kapitelinformationen in der Datenbank.

        Args:
            video_id (str): Transcript-ID.
            chapters (List[ChapterEntry]): Liste der Kapitel.
            chapter_type (str): Der Typ der Kapitel ("summary" oder "detailed").
        Returns:
            None
        """
        ...

    def get_videos_without_transcript_or_chapters(self) -> List[Any]:
        """Gibt Videos zurück, die weder Transkript noch Kapitel haben.

        Returns:
            List[Any]: Liste der Videos ohne Transkript oder Kapitel.
        """
        ...

    def videos_to_transcript_data(self, videos: List[Any]) -> List[TranscriptData]:
        """Konvertiert Transcript-Objekte zu TranscriptData-Objekten.

        Args:
            videos (List[Any]): Liste von Transcript-Objekten.
        Returns:
            List[TranscriptData]: Liste von TranscriptData-Objekten.
        """
        ...

    def search_chapters(self, query: str) -> List[Any]:
        """Sucht in Kapiteln nach dem gegebenen Begriff.

        Args:
            query (str): Suchbegriff für die Volltextsuche.

        Returns:
            List[Any]: Liste der gefundenen Kapitel.
        """
        ...

    def create_transcript_data_for_batch(self, channel_url: str, video_ids: list[str]) -> list[TranscriptData]:
        """Erstellt eine Liste von TranscriptData-Objekten für die Stapelverarbeitung."""
        ...

    def create_transcript_data_for_single(self, video_id: str) -> TranscriptData:
        """Erstellt ein TranscriptData-Objekt für eine einzelne Video-ID."""
        ...

    def add_video_metadata(self, transcript_data: TranscriptData) -> None:
        """Fügt Metadaten für ein Video hinzu.

        Args:
            transcript_data (TranscriptData): Transkriptionsdaten.
        Returns:
            None
        """
        ...


@runtime_checkable
class TranscriptServiceProtocol(Protocol):
    """Protokoll für Transkriptionsdienste.

    Methods:
        fetch_transcript(video_id, languages, use_cookies): Holt Transkript.
        get_transcription_for_video(video_id_or_url, progress_callback): Startet Transkription.
    """

    def fetch_transcript(
        self, video_id: str, languages: Optional[List[str]] = None, use_cookies: Optional[bool] = None
    ) -> TranscriptData:
        """Ruft das Transkript und die vollständigen Metadaten für die gegebene Transcript-ID ab und gibt ein TranscriptData-Objekt zurück.

        Args:
            video_id (str): Die YouTube-Transcript-ID.
            languages (Optional[List[str]]): Bevorzugte Sprachen.
            use_cookies (Optional[bool]): Steuert explizit, ob Cookies verwendet werden sollen.
        Returns:
            TranscriptData: Validiertes Transkript- und Metadatenmodell.
        """
        raise NotImplementedError()

    def fetch_channel_metadata(self, channel_url: str) -> list[TranscriptData]:
        """Holt die Metadaten für einen Kanal.

        Args:
            channel_url (str): Die URL des YouTube-Kanals.
        Returns:
            Dict[str, Any]: Kanal-Metadaten.
        """
        raise NotImplementedError()


@runtime_checkable
class GeneratorServiceProtocol(Protocol):
    """Protokoll für den GeneratorService (Steuerung der Gesamtpipeline).

    Methods:
        run(id, video_id): Startet die Pipeline für ein Transcript.
    """

    def run(self, channel_handle: str, video_id: str) -> None:
        """Startet die Pipeline für ein Transcript.

        Args:
            channel_handle (str): Der @-Handle des Kanals.
            video_id (str): Transcript-ID.
        Returns:
            None
        """
        ...


@runtime_checkable
class BatchTranscriptionServiceProtocol(Protocol):
    """Protokoll für den BatchTranscriptionService.

    Methods:
        run_batch_transcription(channel_url, video_ids_to_process, progress_callback): Startet Stapeltranskription.
    """

    def run_batch_transcription(
        self,
        channel_url: str,
        video_ids_to_process: Optional[list[str]] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> None:
        """Startet die Stapeltranskription für einen Kanal.

        Args:
            channel_url (str): Kanal-URL.
            video_ids_to_process (Optional[list[str]]): Zu verarbeitende Transcript-IDs.
            progress_callback (Optional[Callable[[int], None]]): Callback für Fortschritt.
        Returns:
            None
        """
        ...


# --- Protokolle für Selektoren ---


class TabSelectorProtocol(Protocol):
    """Schnittstelle für Tab-Selektoren (z.B. 'Quellen', 'Chat').

    Attributes:
        TAB_SELECTOR (str): CSS-Selektor für Tab.
        TAB_LABEL_SOURCES (str): Label für Quellen-Tab.
        TAB_LABEL_CHAT (str): Label für Chat-Tab.
    """

    TAB_SELECTOR: str
    TAB_LABEL_SOURCES: str
    TAB_LABEL_CHAT: str


class InsertButtonSelectorProtocol(Protocol):
    """Schnittstelle für den 'Einfügen'-Button-Selektor.

    Attributes:
        BUTTON_SELECTOR (str): CSS-Selektor für Button.
        BUTTON_LABEL (str): Label für Button.
    """

    BUTTON_SELECTOR: str
    BUTTON_LABEL: str


class ProcessingSpinnerSelectorProtocol(Protocol):
    """Schnittstelle für den Lade-/Verarbeitungsspinne-Selektor.

    Attributes:
        SPINNER_SELECTOR (str): CSS-Selektor für Spinner.
    """

    SPINNER_SELECTOR: str


class AddSourceButtonSelectorProtocol(Protocol):
    """Schnittstelle für den 'Quelle hinzufügen'-Button-Selektor.

    Attributes:
        BUTTON (str): CSS-Selektor für Button.
    """

    BUTTON: str


class AddSourceDialogSelectorProtocol(Protocol):
    """Schnittstelle für das Icon im 'Quelle hinzufügen'-Dialog.

    Attributes:
        ICON_NAME (str): Name des Icons.
    """

    ICON_NAME: str


class PasteTextDialogSelectorProtocol(Protocol):
    """Schnittstelle für das Textfeld im 'Text einfügen'-Dialog.

    Attributes:
        TEXTAREA_SELECTOR (str): CSS-Selektor für Textfeld.
    """

    TEXTAREA_SELECTOR: str


class AllSourcesCheckboxSelectorProtocol(Protocol):
    """Schnittstelle für die 'Alle Quellen auswählen'-Checkbox.

    Attributes:
        CHECKBOX_SELECTOR (str): CSS-Selektor für Checkbox.
        CHECKED_CLASS (str): CSS-Klasse für "checked".
        UNCHECKED_CLASS (str): CSS-Klasse für "unchecked".
    """

    CHECKBOX_SELECTOR: str
    CHECKED_CLASS: str
    UNCHECKED_CLASS: str


class CopyTextChipSelectorProtocol(Protocol):
    """Schnittstelle für das 'Kopierter Text'-Chip-Element.

    Attributes:
        CHIP_SELECTOR (str): CSS-Selektor für Chip.
        CHIP_LABEL (str): Label für Chip.
    """

    CHIP_SELECTOR: str
    CHIP_LABEL: str


class QueryFieldSelectorProtocol(Protocol):
    """Schnittstelle für das Anfrage-Textfeld.

    Attributes:
        TEXTAREA_SELECTOR (str): CSS-Selektor für Textfeld.
    """

    TEXTAREA_SELECTOR: str


class SendButtonSelectorProtocol(Protocol):
    """Schnittstelle für den 'Senden'-Button-Selektor.

    Attributes:
        BUTTON_SELECTOR (str): CSS-Selektor für Button.
    """

    BUTTON_SELECTOR: str


@runtime_checkable
class SelectorServiceProtocol(Protocol):
    """Protokoll für die zentrale Selektor-Serviceklasse.

    Attributes:
        tab (TabSelectorProtocol): Tab-Selektor.
        insert_button (InsertButtonSelectorProtocol): Einfügen-Button.
        processing_spinner (ProcessingSpinnerSelectorProtocol): Spinner.
        add_source_button (AddSourceButtonSelectorProtocol): Quelle hinzufügen.
        add_source_dialog (AddSourceDialogSelectorProtocol): Dialog-Icon.
        paste_text_dialog (PasteTextDialogSelectorProtocol): Textfeld.
        all_sources_checkbox (AllSourcesCheckboxSelectorProtocol): Checkbox.
        copy_text_chip (CopyTextChipSelectorProtocol): Chip.
        query_field (QueryFieldSelectorProtocol): Anfragefeld.
        send_button (SendButtonSelectorProtocol): Senden-Button.
    """

    tab: TabSelectorProtocol
    insert_button: InsertButtonSelectorProtocol
    processing_spinner: ProcessingSpinnerSelectorProtocol
    add_source_button: AddSourceButtonSelectorProtocol
    add_source_dialog: AddSourceDialogSelectorProtocol
    paste_text_dialog: PasteTextDialogSelectorProtocol
    all_sources_checkbox: AllSourcesCheckboxSelectorProtocol
    copy_text_chip: CopyTextChipSelectorProtocol
    query_field: QueryFieldSelectorProtocol
    send_button: SendButtonSelectorProtocol


# --- UI- und Web-Protokolle ---


@runtime_checkable
class WebAutomationServiceProtocol(Protocol):
    """Protokoll für den WebAutomationService.

    Attributes:
        selectors (SelectorServiceProtocol): Selektor-Service.

    Methods:
        initialize_javascript_bridge(): Initialisiert JS-Bridge.
        extract_chapters_from_response(py_callback_slot, timeout_ms): Startet Kapitel-Extraktion.
        wait_for_spinner_to_disappear(py_callback_slot, timeout_ms): Wartet auf Spinner.
        wait_for_element_to_appear_and_click(selector, py_callback_slot, timeout_ms): Klickt auf Element.
        wait_for_element_to_appear_and_type(selector, text, py_callback_slot, timeout_ms): Tippt Text.
        wait_and_inject_text(selector, text_block, py_callback_slot): Injected Textblock.
        wait_for_element_with_text(selector, text, py_callback_slot, action_js, timeout_ms): Wartet auf Text.
        wait_for_element_with_text_and_click(selector, text, py_callback_slot, timeout_ms): Wartet und klickt.
        click_if_exists(selector, py_callback_slot): Klickt falls vorhanden.
        click_if_not_checked(base_selector, state_class, py_callback_slot): Klickt falls nicht gecheckt.
        click_if_checked(base_selector, state_class, py_callback_slot): Klickt falls gecheckt.
        wait_for_element_to_be_checked(base_selector, checked_class, py_callback_slot): Wartet auf checked.
        wait_for_element_to_be_unchecked(base_selector, checked_class, py_callback_slot): Wartet auf unchecked.
    """

    selectors: SelectorServiceProtocol

    def initialize_javascript_bridge(self) -> None:
        """Initialisiert die JavaScript-Bridge.

        Returns:
            None
        """
        ...

    def extract_chapters_from_response(self, py_callback_slot: str, timeout_ms: int) -> None:
        """Startet die Kapitel-Extraktionssequenz.

        Args:
            py_callback_slot (str): Name des Python-Slots.
            timeout_ms (int): Timeout in Millisekunden.
        Returns:
            None
        """
        ...

    def wait_for_spinner_to_disappear(self, py_callback_slot: str, timeout_ms: int) -> None:
        """Wartet, bis der Spinner verschwindet.

        Args:
            py_callback_slot (str): Name des Python-Slots.
            timeout_ms (int): Timeout in Millisekunden.
        Returns:
            None
        """
        ...

    def wait_for_element_to_appear_and_click(self, selector: str, py_callback_slot: str, timeout_ms: int) -> None:
        """Klickt auf ein Element, sobald es verfügbar ist.

        Args:
            selector (str): CSS-Selektor.
            py_callback_slot (str): Name des Python-Slots.
            timeout_ms (int): Timeout in Millisekunden.
        Returns:
            None
        """
        ...

    def wait_for_element_to_appear_and_type(
        self, selector: str, text: str, py_callback_slot: str, timeout_ms: int
    ) -> None:
        """Tippt Text in ein Element.

        Args:
            selector (str): CSS-Selektor.
            text (str): Einzutippender Text.
            py_callback_slot (str): Name des Python-Slots.
            timeout_ms (int): Timeout in Millisekunden.
        Returns:
            None
        """
        ...

    def wait_and_inject_text(self, selector: str, text_block: str, py_callback_slot: str) -> None:
        """Injects einen Textblock in ein Element.

        Args:
            selector (str): CSS-Selektor.
            text_block (str): Textblock.
            py_callback_slot (str): Name des Python-Slots.
        Returns:
            None
        """
        ...

    def wait_for_element_with_text(
        self, selector: str, text: str, py_callback_slot: str, action_js: str, timeout_ms: int
    ) -> None:
        """Wartet auf ein Element mit bestimmtem Text und führt eine JS-Aktion aus.

        Args:
            selector (str): CSS-Selektor.
            text (str): Erwarteter Text.
            py_callback_slot (str): Name des Python-Slots.
            action_js (str): JavaScript-Aktion.
            timeout_ms (int): Timeout in Millisekunden.
        Returns:
            None
        """
        ...

    def wait_for_element_with_text_and_click(
        self, selector: str, text: str, py_callback_slot: str, timeout_ms: int
    ) -> None:
        """Wartet auf ein Element mit Text und klickt darauf.

        Args:
            selector (str): CSS-Selektor.
            text (str): Erwarteter Text.
            py_callback_slot (str): Name des Python-Slots.
            timeout_ms (int): Timeout in Millisekunden.
        Returns:
            None
        """
        ...

    def click_if_exists(self, selector: str, py_callback_slot: str) -> None:
        """Klickt auf ein Element, falls es existiert.

        Args:
            selector (str): CSS-Selektor.
            py_callback_slot (str): Name des Python-Slots.
        Returns:
            None
        """
        ...

    def click_if_not_checked(self, base_selector: str, state_class: str, py_callback_slot: str) -> None:
        """Klickt auf ein Element, falls es nicht gecheckt ist.

        Args:
            base_selector (str): Basis-Selektor.
            state_class (str): Status-Klasse.
            py_callback_slot (str): Name des Python-Slots.
        Returns:
            None
        """
        ...

    def click_if_checked(self, base_selector: str, state_class: str, py_callback_slot: str) -> None:
        """Klickt auf ein Element, falls es gecheckt ist.

        Args:
            base_selector (str): Basis-Selektor.
            state_class (str): Status-Klasse.
            py_callback_slot (str): Name des Python-Slots.
        Returns:
            None
        """
        ...

    def wait_for_element_to_be_checked(self, base_selector: str, checked_class: str, py_callback_slot: str) -> None:
        """Wartet, bis ein Element gecheckt ist.

        Args:
            base_selector (str): Basis-Selektor.
            checked_class (str): Checked-Klasse.
            py_callback_slot (str): Name des Python-Slots.
        Returns:
            None
        """
        ...

    def wait_for_element_to_be_unchecked(self, base_selector: str, checked_class: str, py_callback_slot: str) -> None:
        """Wartet, bis ein Element nicht mehr gecheckt ist.

        Args:
            base_selector (str): Basis-Selektor.
            checked_class (str): Checked-Klasse.
            py_callback_slot (str): Name des Python-Slots.
        Returns:
            None
        """
        ...


@runtime_checkable
class WebEngineWindowProtocol(Protocol):
    """Protokoll für das WebEngineWindow.

    Args:
        chapters_extracted_signal (Any): Signal für extrahierte Kapitel.
        automation_sequence_failed (Any): Signal für Automationsfehler.
        service_factory (ServiceFactory): Factory für Services.
        parent (QMainWindow | None): Parent-Widget.

    Methods:
        set_url(url): Setzt die URL.
        handle_new_transcript(transcript_text): Verarbeitet neues Transkript.
        isVisible(): Gibt Sichtbarkeit zurück.
        show(): Zeigt Fenster.
        activateWindow(): Aktiviert Fenster.
        raise_(): Bringt Fenster nach vorne.
    """

    chapters_extracted_signal: Any
    automation_sequence_failed: Any

    def __init__(
        self,
        service_factory: "ServiceFactory",
        parent: QMainWindow | None = None,
    ):
        """Initialisiert das WebEngineWindow.

        Args:
            service_factory (ServiceFactory): Factory für Services.
            parent (QMainWindow | None): Parent-Widget.
        Returns:
            None
        """
        ...

    def set_url(self, url: str) -> None:
        """Setzt die URL für das WebEngineWindow.

        Args:
            url (str): Die zu setzende URL.
        Returns:
            None
        """
        ...

    def handle_new_transcript(self, transcript_text: str) -> None:
        """Verarbeitet ein neues Transkript.

        Args:
            transcript_text (str): Der Transkripttext.
        Returns:
            None
        """
        ...

    def isVisible(self) -> bool:
        """Gibt zurück, ob das Fenster sichtbar ist.

        Returns:
            bool: True, wenn sichtbar.
        """
        ...

    def show(self) -> None:
        """Zeigt das Fenster an.

        Returns:
            None
        """
        ...

    def activateWindow(self) -> None:
        """Aktiviert das Fenster.

        Returns:
            None
        """
        ...

    def raise_(self) -> None:
        """Bringt das Fenster in den Vordergrund.

        Returns:
            None
        """
        ...


@runtime_checkable
class MetadataFormatterProtocol(Protocol):
    """
    Protokoll für einen Service, der Kanal-/Transcript-Metadaten in Datenmodelle der Anwendung konvertiert.
    """

    def extract_transcript_data_objects_from_metadata(self, metadata: dict) -> list[TranscriptData]:
        """
        Extrahiert rekursiv alle Transcript-Infos aus verschachtelten Kanal-Metadaten und erstellt TranscriptData-Objekte.

        Args:
            metadata (dict): Kanal-Metadaten.

        Returns:
            list[TranscriptData]: Liste von TranscriptData-Objekten.
        """
        raise NotImplementedError

    def to_transcript_data(self, entry: dict, channel_meta: dict) -> TranscriptData:
        """
        Erstellt ein TranscriptData-Objekt aus einem Transcript-Entry und den Kanal-Metadaten.
        Args:
            entry (dict): Transcript-Metadaten.
            channel_meta (dict): Kanal-Metadaten.
        Returns:
            TranscriptData: Validiertes Datenmodell.
        """
        raise NotImplementedError


@runtime_checkable
class AnalysisPromptServiceProtocol(Protocol):
    """
    Protokoll für den AnalysisPromptService, der verschiedene Analyse-Prompts verwaltet.

    Methods:
        get_prompt(prompt_type: PromptType) -> str: Lädt den Prompt-Text für den angegebenen Typ.
        get_available_prompt_types() -> list[PromptType]: Gibt alle verfügbaren Prompt-Typen zurück.
    """

    def get_prompt(self, prompt_type: "PromptType") -> str:
        """Lädt den Prompt-Text für den angegebenen Typ.

        Args:
            prompt_type (PromptType): Der gewünschte Prompt-Typ.

        Returns:
            str: Der Prompt-Text.
        """
        ...

    def get_available_prompt_types(self) -> list["PromptType"]:
        """Gibt alle verfügbaren Prompt-Typen zurück.

        Returns:
            list[PromptType]: Liste aller verfügbaren Prompt-Typen.
        """
        ...

    def get_prompt_description(self, prompt_type: PromptType) -> str:
        """Lädt die Beschreibung für den angegebenen Prompt-Typ.

        Args:
            prompt_type (PromptType): Der gewünschte Prompt-Typ.

        Returns:
            str: Die Beschreibung des Prompts.
        """
        ...

    def get_target_section(self, prompt_type: PromptType) -> str:
        """Gibt die Ziel-Sektion für Kapitel-Platzierung zurück.

        Args:
            prompt_type (PromptType): Der gewünschte Prompt-Typ.

        Returns:
            str: Die Ziel-Sektion (z.B. "## Detaillierte Kapitel").
        """
        ...

    def get_chapter_database_type(self, prompt_type: PromptType) -> str:
        """Gibt den chapter_type für die Datenbank zurück.

        Args:
            prompt_type (PromptType): Der gewünschte Prompt-Typ.

        Returns:
            str: Der chapter_type für die Datenbank ("summary" oder "detailed").
        """
        ...


@runtime_checkable
class SingleTranscriptionServiceProtocol(Protocol):
    """Protokoll für den SingleTranscriptionService."""

    def process_video(self, transcript_data: TranscriptData) -> TranscriptData:
        """
        Führt den kompletten Workflow für ein einzelnes Video aus.

        Args:
            transcript_data (TranscriptData): Die initialen Daten des Videos.

        Returns:
            TranscriptData: Das aktualisierte Datenobjekt nach der Verarbeitung.
        """
        ...


# --- Worker-Protokolle ---


@runtime_checkable
class ChannelVideoWorkerProtocol(Protocol):
    """Protokoll für den ChannelVideoWorker."""

    finished: Any  # Signal
    error: Any  # Signal
    transcribed_videos_found: Any  # Signal

    def __init__(self, service_factory: "ServiceFactory", channel_url: str, force_download: bool):
        """Initialisiert den Worker."""
        ...

    @Slot()
    def run(self) -> None:
        """Startet die Ausführung des Workers."""
        ...


@runtime_checkable
class BatchTranscriptionWorkerProtocol(Protocol):
    """Protokoll für den BatchTranscriptionWorker."""

    progress_percent: Any  # Signal
    error: Any  # Signal
    finished: Any  # Signal

    def __init__(
        self,
        transcript_data_list: list[TranscriptData],
        batch_transcription_service: BatchTranscriptionServiceProtocol,
    ):
        """Initialisiert den Worker."""
        ...

    @Slot()
    def run(self) -> None:
        """Startet die Ausführung des Workers."""
        ...
