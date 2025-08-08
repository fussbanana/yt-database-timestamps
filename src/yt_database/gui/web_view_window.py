"""
web_view_window.py
=================

Dateikopf-Kommentar:
--------------------
Dieses Modul implementiert das WebEngineWindow für die Anzeige und Automatisierung von Webinhalten im YouTube-Datenbankprojekt. Es bietet eine persistente WebView mit Automatisierungsfunktionen, eine JavaScript-Bridge für die Kommunikation mit der Webseite und einen Workflow zur automatisierten Verarbeitung von Transkripten und Prompts.
"""

import os
from typing import Any, Callable, Literal, Optional

from loguru import logger
from PySide6.QtCore import QByteArray, QObject, QStandardPaths, QUrl, Signal, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from yt_database.config.settings import settings
from yt_database.gui.widgets.selector_test_toolbar import SelectorTestToolbar
from yt_database.services.service_factory import ServiceFactory


class JsBridge(QObject):
    """
    Bridge-Klasse für die Kommunikation zwischen Python und JavaScript.
    """

    generic_response_received = Signal(dict)
    bridge_is_ready = Signal()

    @Slot(dict)
    def on_generic_response(self, response: dict) -> None:
        self.generic_response_received.emit(response)

    @Slot()
    def confirm_bridge_readiness(self) -> None:
        logger.success("JavaScript-Bridge-Verbindung von JS nach Python bestätigt!")
        self.bridge_is_ready.emit()


class WebEngineWindow(QMainWindow):
    """
    Fenster zur Anzeige von Webinhalten mit Automatisierungs- und Kommunikationsfunktionen.
    """

    chapters_extracted_signal = Signal(str)
    automation_sequence_finished = Signal(str)
    automation_sequence_failed = Signal(str)

    def __init__(self, service_factory: "ServiceFactory", parent: Optional[QWidget] = None) -> None:
        """
        Initialisiert das WebEngineWindow mit allen Services und der UI.
        """
        super().__init__(parent)

        self._setup_state()
        self._setup_services(service_factory)
        self._setup_ui()

        # Logik nach dem UI-Setup
        self._load_settings()
        self._load_analysis_prompt()
        self.set_url(settings.webview_url)

    def _setup_ui(self) -> None:
        """Ruft die UI-Setup-Methoden in der richtigen Reihenfolge auf."""
        logger.debug("Initialisiere UI-Komponenten.")
        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()
        # Der AutomationService ist eng mit der UI (page) verknüpft und wird hier initialisiert.
        self.automation_service = self._service_factory.get_web_automation_service(page=self.web_view.page())

    def _setup_widgets(self) -> None:
        """Initialisiert alle UI-Komponenten und konfiguriert ihre statischen Eigenschaften."""
        self.setWindowTitle("AI Assistant - NotebookLM")
        self.statusBar().showMessage("Bereit.")

        self._create_web_view_with_profile()
        self.web_view.setObjectName("web_engine_web_view")

        self.js_bridge = JsBridge()
        self.channel = QWebChannel(self.web_view.page())

        self.test_toolbar = SelectorTestToolbar(self)
        self.test_toolbar.setObjectName("web_engine_test_toolbar")

    def _setup_layouts(self) -> None:
        """Ordnet die initialisierten Widgets in Layouts an."""
        self.test_toolbar.set_web_page(self.web_view.page())
        self.addToolBar(self.test_toolbar)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web_view)

        central_widget = QWidget()
        central_widget.setObjectName("web_engine_central_widget")
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def _setup_signals(self) -> None:
        """Verbindet die Signale der permanenten Widgets mit ihren Slots."""
        logger.debug("Verbinde Signale und Slots.")
        self.web_view.page().setWebChannel(self.channel)
        self.channel.registerObject("py_bridge", self.js_bridge)
        self.web_view.page().loadFinished.connect(self._on_page_load_finished)
        self.js_bridge.generic_response_received.connect(self.on_automation_step_finished)
        self.js_bridge.bridge_is_ready.connect(self._on_bridge_ready)
        self.test_toolbar.test_result_ready.connect(self._handle_selector_test_result)

    def _setup_state(self) -> None:
        """Initialisiert alle internen Zustandsvariablen."""
        logger.debug("Initialisiere internen Zustand des WebEngineWindow.")
        self._analysis_prompt: Optional[str] = None
        self._pending_prompt: str = ""
        self._pending_transcript: str = ""
        self._current_sequence: list[Callable[..., Any]] = []
        self._current_sequence_name: str = ""
        self._automation_ready: bool = False
        self._pending_sequence: Optional[tuple[list, str]] = None

    def _setup_services(self, service_factory: "ServiceFactory") -> None:
        """Initialisiert abhängige Dienste mithilfe der ServiceFactory."""
        logger.debug("Initialisiere abhängige Services.")
        self._service_factory = service_factory
        self._file_service = service_factory.get_file_service()
        self._analysis_prompt_service = service_factory.get_analysis_prompt_service()

    def _create_web_view_with_profile(self) -> None:
        """Erstellt ein persistentes Web-Profil und die zugehörige QWebEngineView."""
        data_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
        if not data_path:
            data_path = os.path.join(os.path.expanduser("~"), ".YTDatabaseMissionControl")
        profile_path = os.path.join(data_path, "web_profiles", "notebooklm")
        os.makedirs(profile_path, exist_ok=True)
        logger.debug(f"Web-Engine-Profil wird gespeichert unter: {profile_path}")
        self.web_profile = QWebEngineProfile("notebooklm_profile", self)
        self.web_profile.setPersistentStoragePath(profile_path)
        self.web_profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.web_view = QWebEngineView(self.web_profile)

    def _load_analysis_prompt(self) -> None:
        """Lädt den Analyse-Prompt über den Analysis-Prompt-Service."""
        try:
            from yt_database.services.analysis_prompt_service import PromptType

            current_prompt_type_str = getattr(settings, "prompt_type", "youtube_comment")
            prompt_type = (
                PromptType.DETAILED_DATABASE
                if current_prompt_type_str == "detailed_database"
                else PromptType.YOUTUBE_COMMENT
            )
            self._analysis_prompt = self._analysis_prompt_service.get_prompt(prompt_type)
            logger.debug(f"Analyse-Prompt erfolgreich über Service geladen (Typ: {current_prompt_type_str}).")
        except Exception as e:
            logger.error(f"Fehler beim Laden des Analyse-Prompts über Service: {e}")
            self._analysis_prompt = ""

    def update_analysis_prompt(self, prompt_text: str) -> None:
        """Aktualisiert den Analyse-Prompt zur Laufzeit."""
        logger.debug(f"Aktualisiere Analyse-Prompt: {prompt_text[:100]}...")
        self._analysis_prompt = prompt_text

    def set_url(self, url: str) -> None:
        """Setzt die URL im WebView."""
        self.web_view.setUrl(QUrl(url))

    @Slot(str)
    def handle_new_transcript(self, transcript_text: str) -> None:
        """Startet den Workflow: Transkript hochladen, warten, Prompt senden."""
        logger.debug("handle_new_transcript: Starte Upload- und Warte-Sequenz.")
        self._pending_prompt = self._get_analysis_prompt()
        self._pending_transcript = transcript_text
        self._start_upload_sequence()

    def _start_upload_sequence(self) -> None:
        """Erstellt und startet die Sequenz zum Hochladen des Transkripts."""
        selectors = self.automation_service.selectors
        upload_sequence = [
            self._create_wait_for_element_with_text_and_click_step(
                selectors.tab.TAB_SELECTOR, selectors.tab.TAB_LABEL_SOURCES, "tab.QUELLEN_TAB", timeout_ms=10000
            ),
            self._create_wait_and_click_step(
                selectors.add_source_button.BUTTON, "add_source_button.BUTTON", timeout_ms=10000
            ),
            self._create_wait_for_element_with_text_and_click_step(
                selectors.copy_text_chip.CHIP_SELECTOR,
                selectors.copy_text_chip.CHIP_LABEL,
                "copy_text_chip.CHIP_SELECTOR",
                timeout_ms=10000,
            ),
            self._create_wait_and_type_step(
                selectors.paste_text_dialog.TEXTAREA_SELECTOR,
                self._pending_transcript,
                "paste_text_dialog.TEXTAREA_SELECTOR",
                timeout_ms=10000,
            ),
            self._create_wait_for_element_with_text_and_click_step(
                selectors.insert_button.BUTTON_SELECTOR,
                selectors.insert_button.BUTTON_LABEL,
                "insert_button.BUTTON_SELECTOR",
                timeout_ms=10000,
            ),
            self._create_click_on_state_step(
                base_selector=selectors.all_sources_checkbox.CHECKBOX_SELECTOR,
                state_class=selectors.all_sources_checkbox.CHECKED_CLASS,
                label="Aktiviere 'Alle Quellen'",
                click_if="unchecked",
            ),
            self._create_click_on_state_step(
                base_selector=selectors.all_sources_checkbox.CHECKBOX_SELECTOR,
                state_class=selectors.all_sources_checkbox.CHECKED_CLASS,
                label="Deaktiviere 'Alle Quellen'",
                click_if="checked",
            ),
            self._create_wait_for_spinner_to_disapear_step("Warten auf Spinner nach Einfügen", timeout_ms=120000),
        ]
        self._execute_sequence(upload_sequence, "upload_transcript")

    def _start_prompt_sequence(self) -> None:
        """Erstellt und startet die Sequenz zum Einfügen des Analyse-Prompts."""
        logger.debug("Starte Prompt-Einfüge-Sequenz.")
        self._pending_prompt = self._get_analysis_prompt()
        selectors = self.automation_service.selectors
        prompt_sequence = [
            self._create_wait_for_element_with_text_and_click_step(
                selectors.tab.TAB_SELECTOR, selectors.tab.TAB_LABEL_CHAT, "Klick auf den Chat-Tab", timeout_ms=10000
            ),
            self._create_wait_and_type_step(
                selectors.query_field.TEXTAREA_SELECTOR,
                self._pending_prompt,
                "Schreibe Prompt in das Eingabefeld",
                timeout_ms=10000,
            ),
            self._create_wait_and_click_step(
                selectors.send_button.BUTTON_SELECTOR, "Klick auf den Senden-Button", timeout_ms=10000
            ),
        ]
        self._execute_sequence(prompt_sequence, "prompt_insertion")

    def _execute_sequence(self, sequence: list[Callable[..., Any]], sequence_name: str) -> None:
        """Führt eine Liste von Automatisierungsfunktionen nacheinander aus."""
        if not self._automation_ready:
            logger.warning(
                f"Automatisierung für '{sequence_name}' angefordert, aber Seite nicht bereit. Sequenz wird aufgeschoben."
            )
            self._pending_sequence = (sequence, sequence_name)
            return
        logger.debug(f"Starte Automatisierungssequenz: {sequence_name} ({len(sequence)} Schritte)")
        self._current_sequence = list(sequence)
        self._current_sequence_name = sequence_name
        self._execute_next_step()

    def _execute_next_step(self) -> None:
        """Führt den nächsten Schritt in der aktuellen Sequenz aus."""
        if not self._current_sequence:
            logger.debug(f"Sequenz '{self._current_sequence_name}' erfolgreich abgeschlossen.")
            self.automation_sequence_finished.emit(self._current_sequence_name)
            if self._current_sequence_name == "upload_transcript":
                self._start_prompt_sequence()
            elif self._current_sequence_name == "prompt_insertion":
                self.automation_service.extract_chapters_from_response("on_generic_response", timeout_ms=12000000)
            return

        logger.debug(f"Führe Schritt aus: {self._current_sequence_name} (Rest: {len(self._current_sequence)})")
        next_step = self._current_sequence.pop(0)

        if next_step is None or not callable(next_step):
            error_msg = f"Ungültiger Schritt in Sequenz '{self._current_sequence_name}': {type(next_step)}"
            logger.error(f"[Automation] {error_msg}")
            self.automation_sequence_failed.emit(error_msg)
            return

        try:
            next_step()
        except Exception as e:
            error_msg = f"Fehler beim Ausführen des Schritts in '{self._current_sequence_name}': {e}"
            logger.error(f"[Automation] {error_msg}")
            self.automation_sequence_failed.emit(error_msg)

    def _create_wait_for_element_with_text_and_click_step(
        self, selector: str, text: str, py_callback: str, timeout_ms: int
    ) -> Callable:
        """Erstellt einen Schritt, der auf ein Element mit bestimmtem Text klickt."""
        if not all(isinstance(arg, str) and arg for arg in [selector, text]):
            error_msg = f"Ungültiger Selektor/Text für '{py_callback}'"
            logger.error(f"[Automation] {error_msg}. Breche Sequenz ab.")
            return lambda: self.on_automation_step_finished({"status": "error", "message": error_msg})
        return lambda: self.automation_service.wait_for_element_with_text_and_click(
            selector, text, "on_generic_response", timeout_ms=timeout_ms
        )

    def _create_wait_and_click_step(self, selector: str, py_callback: str, timeout_ms: int) -> Callable:
        """Erstellt einen Schritt, der auf ein Element klickt."""
        if not isinstance(selector, str) or not selector:
            error_msg = f"Ungültiger Selektor für '{py_callback}'"
            logger.error(f"[Automation] {error_msg}. Breche Sequenz ab.")
            return lambda: self.on_automation_step_finished({"status": "error", "message": error_msg})
        return lambda: self.automation_service.wait_for_element_to_appear_and_click(
            selector, "on_generic_response", timeout_ms=timeout_ms
        )

    def _create_wait_and_type_step(self, selector: str, text: str, py_callback: str, timeout_ms: int) -> Callable:
        """Erstellt einen Schritt, der Text in ein Element tippt."""
        if not isinstance(selector, str) or not selector:
            error_msg = f"Ungültiger Selektor für '{py_callback}'"
            logger.error(f"[Automation] {error_msg}. Breche Sequenz ab.")
            return lambda: self.on_automation_step_finished({"status": "error", "message": error_msg})
        return lambda: self.automation_service.wait_for_element_to_appear_and_type(
            selector, text, "on_generic_response", timeout_ms=10000
        )

    def _create_click_on_state_step(
        self, base_selector: str, state_class: str, label: str, click_if: Literal["checked", "unchecked"]
    ) -> Callable:
        """Erstellt einen Schritt, der ein Element basierend auf einer Zustandsklasse anklickt."""
        if not all(isinstance(arg, str) and arg for arg in [base_selector, state_class]):
            error_msg = f"Ungültiger Selektor/Klasse für '{label}'"
            logger.error(f"[Automation] {error_msg}")
            return lambda: self.on_automation_step_finished({"status": "error", "message": error_msg})
        if click_if not in ("checked", "unchecked"):
            error_msg = f"Ungültiger Zustand '{click_if}' für '{label}'."
            logger.error(f"[Automation] {error_msg}")
            return lambda: self.on_automation_step_finished({"status": "error", "message": error_msg})

        if click_if == "checked":
            return lambda: self.automation_service.click_if_checked(
                base_selector=base_selector, state_class=state_class, py_callback_slot="on_generic_response"
            )
        else:
            return lambda: self.automation_service.click_if_not_checked(
                base_selector=base_selector, state_class=state_class, py_callback_slot="on_generic_response"
            )

    def _create_wait_for_spinner_to_disapear_step(self, py_callback: str, timeout_ms: int = 10000) -> Callable:
        """Erstellt einen Schritt, der wartet, bis der Lade-Spinner verschwindet."""
        logger.debug(f"[Automation] Erstelle Schritt für '{py_callback}': Warte auf Spinner.")
        return lambda: self.automation_service.wait_for_spinner_to_disappear(
            "on_generic_response", timeout_ms=timeout_ms
        )

    @Slot(dict)
    def on_automation_step_finished(self, response: dict) -> None:
        """Zentraler Handler für alle Rückmeldungen vom WebAutomationService."""
        status = response.get("status")
        message = response.get("message")
        logger.debug(f"Automatisierungsschritt beendet: Status='{status}', Nachricht='{message}'")
        if status == "success" and "result" in response:
            logger.debug(f"Kapitel erfolgreich extrahiert ({len(response['result'])} Zeichen).")
            self.chapters_extracted_signal.emit(response["result"])
            return
        if status == "success":
            self._execute_next_step()
        else:
            error_message = f"Fehler in Sequenz '{self._current_sequence_name}': {message}"
            logger.error(error_message)
            self._current_sequence = []
            self.automation_sequence_failed.emit(error_message)

    def _on_page_load_finished(self, ok: bool) -> None:
        """Wird aufgerufen, wenn die Seite vollständig geladen ist."""
        logger.debug(f"Seite geladen: ok={ok}. Initialisiere JavaScript-Brücke...")
        self.automation_service.initialize_javascript_bridge()

    @Slot()
    def _on_bridge_ready(self) -> None:
        """Wird aufgerufen, nachdem JS die Verbindung bestätigt hat."""
        self._automation_ready = True
        logger.debug("Automatisierung ist jetzt bereit. Führe ggf. wartende Sequenz aus.")
        if self._pending_sequence:
            logger.debug("Starte aufgeschobene Automatisierungssequenz.")
            sequence, name = self._pending_sequence
            self._pending_sequence = None
            self._execute_sequence(sequence, name)

    @Slot(dict)
    def _handle_selector_test_result(self, data: dict) -> None:
        """Zeigt das Ergebnis des Selektor-Tests in der Statusleiste an."""
        if "error" in data:
            message = f"JS-Fehler: {data['error']}"
            logger.error(f"[Selector Test] {message}")
        else:
            count = data.get("count", 0)
            message = f"{count} Element(e) für Selektor gefunden."
            logger.debug(f"[Selector Test] {message}")
        self.statusBar().showMessage(message)

    def _load_settings(self) -> None:
        """Lädt die gespeicherte Fenstergeometrie."""
        geometry_hex = settings.web_window_geometry
        if geometry_hex:
            try:
                self.restoreGeometry(QByteArray.fromHex(geometry_hex.encode("utf-8")))
            except Exception as e:
                logger.warning(f"Fehler beim Wiederherstellen der Geometrie: {e}")
                self.setGeometry(150, 150, 1024, 768)
        else:
            self.setGeometry(150, 150, 1024, 768)

    def _save_settings(self) -> None:
        """Speichert die aktuelle Fenstergeometrie."""
        geometry_hex = bytes(self.saveGeometry().toHex().data()).decode("utf-8")
        settings.web_window_geometry = geometry_hex

    def _get_analysis_prompt(self) -> str:
        """Gibt den aktuellen Analyse-Prompt über den Service zurück."""
        try:
            from yt_database.services.analysis_prompt_service import PromptType

            current_prompt_type_str = getattr(settings, "prompt_type", "youtube_comment")
            prompt_type = (
                PromptType.DETAILED_DATABASE
                if current_prompt_type_str == "detailed_database"
                else PromptType.YOUTUBE_COMMENT
            )
            prompt_text = self._analysis_prompt_service.get_prompt(prompt_type)
            logger.debug(
                f"Aktueller Analyse-Prompt dynamisch geladen (Typ: {current_prompt_type_str}, {len(prompt_text)} Zeichen)."
            )
            return prompt_text
        except Exception as e:
            logger.error(f"Fehler beim dynamischen Laden des Analyse-Prompts: {e}")
            return self._analysis_prompt or ""

    def closeEvent(self, event) -> None:
        """Überschreibt das Schließen-Event, um das Fenster nur auszublenden."""
        self._save_settings()
        self.hide()
        event.ignore()
