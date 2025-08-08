"""
Dieser Service stellt eine robuste und wiederverwendbare API für Web-Automationsabläufe bereit, die über QWebChannel und JavaScript ausgeführt werden. Er ermöglicht flexible Interaktionen mit Webseiten für KI-Workflows und UI-Automatisierung. Die Klasse kapselt alle relevanten Automationsrezepte und bietet eine konsistente Schnittstelle für komplexe und einfache Aktionen. Debug-Logging und Inline-Kommentare sind strategisch platziert, um die Nachvollziehbarkeit und Wartbarkeit zu maximieren.

Hauptfunktionen:
- Initialisierung und Setup der WebEnginePage und Selektoren
- JavaScript-Bridge-Initialisierung
- Warten und Interagieren mit DOM-Elementen (Klick, Typing, etc.)
- Komplexe Automationsrezepte (z.B. Kapitel-Extraktion)
- Private Hilfsmethoden für JavaScript-Ausführung und DOM-Interaktion

Alle Methoden sind mit Google-Style-Docstrings, Typ-Hints und deutschen Entwickler-Kommentaren versehen.
"""

from typing import Callable, Optional

from loguru import logger
from PySide6.QtCore import QFile, QIODevice, QObject
from PySide6.QtWebEngineCore import QWebEnginePage

from yt_database.config.settings import settings
from yt_database.services.protocols import SelectorServiceProtocol


class WebAutomationService(QObject):
    """
    Service für Web-Automationsabläufe via QWebChannel und JavaScript.

    Args:
        page (QWebEnginePage): Die zu automatisierende WebEngine-Seite.
        selectors (SelectorServiceProtocol): Service für Selektoren und UI-Elemente.

    Attributes:
        _page (QWebEnginePage): Die aktuelle WebEngine-Seite.
        selectors (SelectorServiceProtocol): Selektor-Service für UI-Elemente.

    Raises:
        ValueError: Falls page oder selectors nicht gesetzt sind.
    """

    def __init__(self, page: QWebEnginePage, selectors: SelectorServiceProtocol) -> None:
        """
        Initialisiert den WebAutomationService mit Seite und Selektoren.

        Args:
            page (QWebEnginePage): Die zu automatisierende Seite.
            selectors (SelectorServiceProtocol): Selektor-Service.

        Raises:
            ValueError: Falls page oder selectors nicht gesetzt sind.
        """
        super().__init__()
        if not page or not selectors:
            raise ValueError("WebAutomationService benötigt eine 'page' und 'selectors'.")
        self._page = page
        self.selectors = selectors
        logger.debug("WebAutomationService initialisiert.")

    def set_page(self, page: QWebEnginePage) -> None:
        """
        Setzt die QWebEnginePage für die Automatisierung.

        Args:
            page (QWebEnginePage): Die neue Seite.

        Raises:
            ValueError: Falls page None ist.
        """
        # Validierung der Eingabe
        if not page:
            raise ValueError("Die übergebene Seite darf nicht None sein.")
        self._page = page
        logger.debug("WebEnginePage wurde im WebAutomationService erfolgreich gesetzt.")

    def initialize_javascript_bridge(self) -> None:
        """
        Injiziert das QWebChannel-Skript und startet den Handshake zur Verbindungsbestätigung.

        Raises:
            RuntimeError: Falls die Seite nicht gesetzt ist oder das Skript nicht geladen werden kann.
        """
        logger.debug("Initialisiere JavaScript-Bridge.")
        if self._page is None:
            logger.error("Kann JS-Brücke nicht initialisieren: Seite wurde nicht gesetzt.")
            return
        # Lade das qwebchannel.js-Skript
        script_path = ":/qtwebchannel/qwebchannel.js"
        file = QFile(script_path)
        if not file.open(QIODevice.OpenModeFlag.ReadOnly):
            logger.error("Konnte qwebchannel.js nicht laden!")
            return
        content = bytes(file.readAll().data()).decode("utf-8")
        self._run_js(content)
        logger.debug("qwebchannel.js erfolgreich in die Seite injiziert.")
        # Handshake-Skript für die Bridge
        handshake_script = """
            (function() {
                setTimeout(function() {
                    if (typeof qt === 'undefined' || typeof qt.webChannelTransport === 'undefined') {
                        console.error('[JS] qt.webChannelTransport ist nach kurzer Wartezeit immer noch nicht verfügbar.');
                        return;
                    }
                    new QWebChannel(qt.webChannelTransport, function(channel) {
                        window.py_bridge = channel.objects.py_bridge;
                        if (window.py_bridge && typeof window.py_bridge.confirm_bridge_readiness === 'function') {
                            window.py_bridge.confirm_bridge_readiness();
                        } else {
                            console.error('[JS] Konnte py_bridge-Objekt oder confirm_bridge_readiness nicht im Channel finden!');
                        }
                    });
                }, 100);
            })();
        """
        self._run_js(handshake_script)
        logger.debug("Handshake zur Bestätigung der JS-Bridge wurde angestoßen.")

    # ---------------------------------------------
    # Öffentliche Methoden für die Automatisierung
    # ---------------------------------------------

    def wait_for_element_to_appear_and_click(
        self, selector: str, py_callback_slot: str, timeout_ms: int = 10000
    ) -> None:
        """
        Wartet auf ein Element und klickt es.

        Args:
            selector (str): CSS-Selektor des Elements.
            py_callback_slot (str): Name des Python-Callback-Slots.
            timeout_ms (int): Timeout in Millisekunden.
        """
        logger.debug(f"Aktion: Warte auf '{selector}' und klicke.")
        action_js = "el.click();"
        self._js_wait_for_element_to_appear(
            selector=selector, py_callback_slot=py_callback_slot, action_js=action_js, timeout_ms=timeout_ms
        )

    def wait_for_element_to_appear_and_type(
        self, selector: str, text: str, py_callback_slot: str, timeout_ms: int = 10000
    ) -> None:
        """
        Wartet auf ein Eingabefeld und tippt Text ein.

        Args:
            selector (str): CSS-Selektor des Eingabefelds.
            text (str): Einzutippender Text.
            py_callback_slot (str): Name des Python-Callback-Slots.
            timeout_ms (int): Timeout in Millisekunden.
        """
        logger.debug(f"Aktion: Warte auf '{selector}' und tippe Text.")
        # Escape für Sonderzeichen im Text
        escaped_text = text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        action_js = f"el.value = `{escaped_text}`; el.dispatchEvent(new Event('input', {{ bubbles: true }}));"
        self._js_wait_for_element_to_appear(
            selector=selector, py_callback_slot=py_callback_slot, action_js=action_js, timeout_ms=timeout_ms
        )

    def wait_for_element_with_text_and_click(
        self, selector: str, text: str, py_callback_slot: str, timeout_ms: int = 10000
    ) -> None:
        """
        Sucht nach Elementen, filtert nach Text und klickt.

        Args:
            selector (str): CSS-Selektor der Elemente.
            text (str): Text, nach dem gefiltert wird.
            py_callback_slot (str): Name des Python-Callback-Slots.
            timeout_ms (int): Timeout in Millisekunden.
        """
        logger.debug(f"Aktion: Warte auf '{selector}' mit Text '{text}' und klicke.")
        self._js_wait_for_element_with_text(
            selector=selector,
            text_to_find=text,
            py_callback_slot=py_callback_slot,
            action_js="el.click();",
            timeout_ms=timeout_ms,
        )

    def click_if_not_checked(self, base_selector: str, state_class: str, py_callback_slot: str) -> None:
        """
        Klickt ein Element nur, wenn es die 'checked_class' NICHT hat.

        Args:
            base_selector (str): Basis-Selektor.
            state_class (str): CSS-Klasse für den Zustand.
            py_callback_slot (str): Name des Python-Callback-Slots.
        """
        logger.debug(f"Bedingte Aktion: Klicke '{base_selector}', falls nicht '{state_class}'.")
        conditional_selector = f"{base_selector}:not(.{state_class})"
        self._js_execute_action_if_element_exists(conditional_selector, "el.click();", py_callback_slot)

    def click_if_checked(self, base_selector: str, state_class: str, py_callback_slot: str) -> None:
        """
        Klickt ein Element nur, wenn es die 'checked_class' BEREITS HAT.

        Args:
            base_selector (str): Basis-Selektor.
            state_class (str): CSS-Klasse für den Zustand.
            py_callback_slot (str): Name des Python-Callback-Slots.
        """
        logger.debug(f"Bedingte Aktion: Klicke '{base_selector}', falls bereits '{state_class}'.")
        conditional_selector = f"{base_selector}.{state_class}"
        self._js_execute_action_if_element_exists(conditional_selector, "el.click();", py_callback_slot)

    def wait_for_element_to_appear(self, selector: str, py_callback_slot: str, timeout_ms: int = 10000) -> None:
        """
        Wartet darauf, dass ein Element erscheint.

        Args:
            selector (str): CSS-Selektor des Elements.
            py_callback_slot (str): Name des Python-Callback-Slots.
            timeout_ms (int): Timeout in Millisekunden.
        """
        logger.debug(f"Aktion: Warte auf Erscheinen von '{selector}' (Timeout: {timeout_ms}ms).")
        self._js_wait_for_element_to_appear(selector=selector, py_callback_slot=py_callback_slot, timeout_ms=timeout_ms)

    def extract_chapters_from_response(self, py_callback_slot: str, timeout_ms: int = 30000) -> None:
        """
        Startet die Extraktion von Kapiteln aus der letzten KI-Antwort.

        Args:
            py_callback_slot (str): Name des Python-Callback-Slots.
            timeout_ms (int): Timeout in Millisekunden.
        """
        logger.debug("Rezept: 'extract_chapters_from_response'")
        selector = "div.chat-message-pair:last-of-type .to-user-message-card-content pre code"
        self._js_wait_for_response_and_extract(selector, py_callback_slot, timeout_ms=timeout_ms)

    def wait_for_spinner_to_disappear(self, py_callback_slot: str, timeout_ms: int = 10000) -> None:
        """
        Wartet, bis der Lade-Spinner von der Seite verschwindet.

        Args:
            py_callback_slot (str): Name des Python-Callback-Slots.
            timeout_ms (int): Timeout in Millisekunden.
        """
        logger.debug("Rezept: 'wait_for_spinner_to_disappear'")
        spinner_selector = self.selectors.processing_spinner.SPINNER_SELECTOR
        self._js_wait_for_element_to_disappear(spinner_selector, py_callback_slot, timeout_ms=timeout_ms)

    # ---------------------------------------------
    # Private Hilfsmethoden für JavaScript-Ausführung
    # ---------------------------------------------

    def _run_js(self, script: str, callback: Optional[Callable] = None) -> None:
        """
        Führt JavaScript sicher im Kontext der aktuellen Seite aus.

        Args:
            script (str): JavaScript-Code.
            callback (Optional[Callable]): Optionaler Callback nach Ausführung.
        """
        logger.debug("Führe JavaScript im Seitenkontext aus.")
        if self._page is None:
            logger.error("Fehler: Versuch, JavaScript auszuführen, bevor die Seite gesetzt wurde.")
            return
        if callback:
            self._page.runJavaScript(script, 0, callback)
        else:
            self._page.runJavaScript(script)

    def _js_wait_for_element_to_appear(
        self, selector: str, py_callback_slot: str, action_js: Optional[str] = None, timeout_ms: int = 10000
    ) -> None:
        """
        JS-Handler: Wartet auf das Erscheinen eines Elements und führt optional eine Aktion aus.

        Args:
            selector (str): CSS-Selektor.
            py_callback_slot (str): Name des Python-Callback-Slots.
            action_js (Optional[str]): Optionaler JavaScript-Code für die Aktion.
            timeout_ms (int): Timeout in Millisekunden.
        """
        logger.debug(f"Starte JS-Warte-Handler für '{selector}' mit Timeout {timeout_ms}ms.")
        debug_js = "true" if settings.debug else "false"
        js_helpers = self._JS_FIND_ELEMENT_HELPER.format(debug_js=debug_js)
        action_definition = f"const action = (el) => {{ {action_js} }};" if action_js else "const action = null;"
        action_call = "if (action) action(el);" if action_js else ""
        action_call_found = "if (action) action(foundEl);" if action_js else ""
        js_logic = f"""
            (function() {{
                {js_helpers}
                {action_definition}
                const selector = `{selector}`;
                const timeout = {timeout_ms};
                const pyCallbackSlot = `{py_callback_slot}`;
                let observer;
                let timeoutId;
                const report_back = (status, message) => {{
                    if (observer) observer.disconnect();
                    clearTimeout(timeoutId);
                    window.py_bridge[pyCallbackSlot]({{ status, selector, message }});
                }};
                timeoutId = setTimeout(() => report_back('timeout', `Timeout von ${{timeout}}ms erreicht beim Warten auf: ${{selector}}`), timeout);
                const el = findElementInAnyContext(selector);
                if (el) {{
                    {action_call}
                    report_back('success', 'Element war sofort vorhanden.');
                    return;
                }}
                observer = new MutationObserver(() => {{
                    const foundEl = findElementInAnyContext(selector);
                    if (foundEl) {{
                        {action_call_found}
                        report_back('success', 'Element ist erschienen.');
                    }}
                }});
                observer.observe(document.body, {{ childList: true, subtree: true }});
            }})();
        """
        self._run_js(js_logic)

    def _js_wait_for_element_to_disappear(
        self, selector: str, py_callback_slot: str, timeout_ms: int = 10000, action_js: Optional[str] = None
    ) -> None:
        """
        JS-Handler: Wartet darauf, dass ein Element verschwindet und führt optional eine Aktion aus.

        Args:
            selector (str): CSS-Selektor.
            py_callback_slot (str): Name des Python-Callback-Slots.
            timeout_ms (int): Timeout in Millisekunden.
            action_js (Optional[str]): Optionaler JavaScript-Code für die Aktion.
        """
        logger.debug(f"Starte JS-Disappear-Handler für '{selector}' mit Timeout {timeout_ms}ms.")
        debug_js = "true" if settings.debug else "false"
        js_helpers = self._JS_FIND_ELEMENT_HELPER.format(debug_js=debug_js)
        action_definition = f"const action = () => {{ {action_js} }};" if action_js else "const action = null;"
        action_call = "if (action) action();" if action_js else ""
        js_logic = f"""
            (function() {{
                {js_helpers}
                {action_definition}
                const selector = `{selector}`;
                const timeout = {timeout_ms};
                const pyCallbackSlot = `{py_callback_slot}`;
                let observer;
                let timeoutId;
                const report_back = (status, message) => {{
                    if (observer) observer.disconnect();
                    clearTimeout(timeoutId);
                    window.py_bridge[pyCallbackSlot]({{ status, selector, message }});
                }};
                timeoutId = setTimeout(() => report_back('timeout', `Timeout...`), timeout);
                if (!findElementInAnyContext(selector)) {{
                    {action_call}
                    report_back('success', 'Element war bereits weg.');
                    return;
                }}
                observer = new MutationObserver(() => {{
                    if (!findElementInAnyContext(selector)) {{
                        {action_call}
                        report_back('success', 'Element ist verschwunden.');
                    }}
                }});
                observer.observe(document.body, {{ childList: true, subtree: true }});
            }})();
        """
        self._run_js(js_logic)

    def _js_wait_for_element_with_text(
        self,
        selector: str,
        text_to_find: str,
        py_callback_slot: str,
        action_js: Optional[str] = None,
        timeout_ms: int = 10000,
    ) -> None:
        """
        JS-Handler: Wartet auf ein Element mit bestimmtem Text und führt optional eine Aktion aus.

        Args:
            selector (str): CSS-Selektor.
            text_to_find (str): Text, nach dem gesucht wird.
            py_callback_slot (str): Name des Python-Callback-Slots.
            action_js (Optional[str]): Optionaler JavaScript-Code für die Aktion.
            timeout_ms (int): Timeout in Millisekunden.
        """
        logger.debug(f"Starte JS-Text-Handler für '{selector}' mit Text '{text_to_find}' und Timeout {timeout_ms}ms.")
        debug_js = "true" if settings.debug else "false"
        js_helpers = self._JS_FIND_ELEMENTS_HELPER.format(debug_js=debug_js)
        action_definition = f"const action = (el) => {{ {action_js} }};" if action_js else "const action = null;"
        action_call = "if (action) action(el);" if action_js else ""
        js_logic = f"""
            (function() {{
                {js_helpers}
                {action_definition}
                const selector = `{selector}`;
                const textToFind = `{text_to_find}`;
                const timeout = {timeout_ms};
                const pyCallbackSlot = `{py_callback_slot}`;
                let observer;
                let timeoutId;
                const report_back = (status, message) => {{
                    if (observer) observer.disconnect();
                    clearTimeout(timeoutId);
                    window.py_bridge[pyCallbackSlot]({{ status, selector, message }});
                }};
                const findAndExecute = () => {{
                    const elements = findElementsInAnyContext(selector);
                    if (!elements || elements.length == 0) return false;
                    for (const el of elements) {{
                        if (el.innerText && el.innerText.trim().includes(textToFind)) {{
                            {action_call}
                            report_back('success', `Element mit Text "${{textToFind}}" gefunden.`);
                            return true;
                        }}
                    }}
                    return false;
                }};
                timeoutId = setTimeout(() => report_back('timeout', `Timeout von ${{timeout}}ms erreicht. Element mit Text "${{textToFind}}" nicht gefunden.`), timeout);
                if (findAndExecute()) return;
                observer = new MutationObserver(() => {{ if (findAndExecute()) {{}} }});
                observer.observe(document.body, {{ childList: true, subtree: true, characterData: true }});
            }})();
        """
        self._run_js(js_logic)

    def _js_execute_action_if_element_exists(self, selector: str, action_js: str, py_callback_slot: str) -> None:
        """
        JS-Handler: Prüft, ob ein Element existiert und führt dann eine Aktion aus.

        Args:
            selector (str): CSS-Selektor.
            action_js (str): JavaScript-Code für die Aktion.
            py_callback_slot (str): Name des Python-Callback-Slots.
        """
        logger.debug(f"Prüfe Existenz von Element '{selector}' und führe Aktion aus.")
        debug_js = "true" if settings.debug else "false"
        js_helpers = self._JS_FIND_ELEMENT_HELPER.format(debug_js=debug_js)
        js_logic = f"""
            (function() {{
                {js_helpers}
                const selector = `{selector}`;
                const action = (el) => {{ {action_js} }};
                const pyCallbackSlot = `{py_callback_slot}`;
                const report_back = (status, message) => {{
                    if (window.py_bridge && typeof window.py_bridge[pyCallbackSlot] === 'function') {{
                        window.py_bridge[pyCallbackSlot]({{ status, selector, message }});
                    }}
                }};
                const el = findElementInAnyContext(selector);
                if (el) {{
                    action(el);
                    report_back('success', `Bedingung erfüllt (Element gefunden), Aktion ausgeführt für: ${{selector}}`);
                }} else {{
                    report_back('success', `Bedingung nicht erfüllt (Element nicht gefunden), keine Aktion nötig für: ${{selector}}`);
                }}
            }})();
        """
        self._run_js(js_logic)

    def _js_wait_for_response_and_extract(self, selector: str, py_callback_slot: str, timeout_ms: int = 30000) -> None:
        """
        JS-Handler: Wartet auf eine stabile Text-Antwort im DOM und extrahiert sie.

        Args:
            selector (str): CSS-Selektor.
            py_callback_slot (str): Name des Python-Callback-Slots.
            timeout_ms (int): Timeout in Millisekunden.
        """
        logger.debug(f"Starte JS-Extraktions-Handler für '{selector}' mit Timeout {timeout_ms}ms.")
        debug_js = "true" if settings.debug else "false"
        js_helpers = self._JS_FIND_ELEMENT_HELPER.format(debug_js=debug_js)
        stability_delay = 4000
        js_logic = f"""
            (function() {{
                {js_helpers}
                const selector = `{selector}`;
                const masterTimeout = {timeout_ms};
                const stabilityDelay = {stability_delay};
                const pyCallbackSlot = `{py_callback_slot}`;
                let lastText = '';
                let stabilityTimer = null;
                let checkInterval = null;
                let masterTimeoutId = null;
                const cleanUpAndResolve = (resultText, status, message) => {{
                    clearInterval(checkInterval);
                    clearTimeout(stabilityTimer);
                    clearTimeout(masterTimeoutId);
                    if (window.py_bridge && typeof window.py_bridge[pyCallbackSlot] === 'function') {{
                        window.py_bridge[pyCallbackSlot]({{ status, selector, message, result: resultText }});
                    }}
                }};
                masterTimeoutId = setTimeout(() => cleanUpAndResolve(lastText, 'timeout', 'Master-Timeout für Extraktion erreicht.'), masterTimeout);
                checkInterval = setInterval(() => {{
                    const el = findElementInAnyContext(selector);
                    if (el) {{
                        const currentText = el.innerText;
                        if (currentText.length > lastText.length) {{
                            lastText = currentText;
                            clearTimeout(stabilityTimer);
                            stabilityTimer = setTimeout(() => cleanUpAndResolve(currentText, 'success', 'Antwort hat sich stabilisiert.'), stabilityDelay);
                        }}
                    }}
                }}, 500);
            }})();
        """
        self._run_js(js_logic)

    # ---------------------------------------------
    # JS-Hilfsfunktionen als String-Templates
    # ---------------------------------------------

    _JS_FIND_ELEMENT_HELPER = """
        function findElementInAnyContext(selector) {{
            const DEBUG_JS = {debug_js};
            let element = document.querySelector(selector);
            if (element) return element;
            const frames = document.querySelectorAll('iframe');
            for (let i = 0; i < frames.length; i++) {{
                try {{
                    const frameDocument = frames[i].contentDocument || frames[i].contentWindow.document;
                    if (frameDocument) {{
                        element = frameDocument.querySelector(selector);
                        if (element) return element;
                    }}
                }} catch (e) {{
                    if (DEBUG_JS) console.log(`[JS] Konnte nicht auf iFrame zugreifen: ${{e.message}}`);
                }}
            }}
            return null;
        }}
    """

    _JS_FIND_ELEMENTS_HELPER = """
        function findElementsInAnyContext(selector) {{
            const DEBUG_JS = {debug_js};
            let elements = Array.from(document.querySelectorAll(selector));
            const frames = document.querySelectorAll('iframe');
            for (let i = 0; i < frames.length; i++) {{
                try {{
                    const frameDocument = frames[i].contentDocument || frames[i].contentWindow.document;
                    if (frameDocument) {{
                        elements = elements.concat(Array.from(frameDocument.querySelectorAll(selector)));
                    }}
                }} catch (e) {{
                    if (DEBUG_JS) console.log(`[JS] Konnte nicht auf iFrame zugreifen: ${{e.message}}`);
                }}
            }}
            return elements;
        }}
    """
