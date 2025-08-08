"""
SelectorTestToolbar: Eigenständiges Toolbar-Widget zum Testen von CSS-Selektoren im WebView.
Führt die komplette Selektor-Test-Logik (JS-Ausführung, Ergebnisverarbeitung) selbstständig aus.
Kommunikation ausschließlich über Signale.
"""

import json

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QLineEdit, QPushButton, QToolBar


class SelectorTestToolbar(QToolBar):
    test_result_ready = Signal(dict)

    def __init__(self, parent=None):
        super().__init__("Test-Toolbar", parent)
        self._web_page = None
        self.selector_input = QLineEdit(self)
        self.selector_input.setPlaceholderText("CSS-Selektor hier eingeben und Enter drücken...")
        self.selector_input.setMinimumWidth(400)
        self.selector_input.returnPressed.connect(self._on_test_requested)

        self.test_button = QPushButton("Testen", self)
        self.test_button.clicked.connect(self._on_test_requested)

        self.addWidget(self.selector_input)
        self.addWidget(self.test_button)

    def set_web_page(self, web_page):
        """Setzt die QWebEnginePage, auf der getestet werden soll."""
        self._web_page = web_page

    @Slot()
    def _on_test_requested(self):
        selector = self.selector_input.text().strip()
        if not selector:
            self.test_result_ready.emit({"error": "Bitte einen Selektor zum Testen eingeben."})
            return
        if self._web_page is None:
            self.test_result_ready.emit({"error": "Webseite nicht initialisiert."})
            return
        js_selector = selector.replace('"', '"')
        script = f"""
        (function() {{
            try {{
                const elements = document.querySelectorAll(\"{js_selector}\");
                let results = [];
                elements.forEach(el => {{
                    results.push({{
                        tagName: el.tagName,
                        id: el.id,
                        className: el.className,
                        innerText: el.innerText.substring(0, 100) + '...'
                    }});
                }});
                return JSON.stringify({{ count: elements.length, found: results }});
            }} catch (e) {{
                return JSON.stringify({{ error: e.message }});
            }}
        }})();
        """
        self._web_page.runJavaScript(script, self._handle_test_result)

    def set_status(self, message: str):
        self.selector_input.setToolTip(message)

    def _handle_test_result(self, result):
        try:
            data = json.loads(result)
            self.test_result_ready.emit(data)
        except (json.JSONDecodeError, TypeError):
            self.test_result_ready.emit({"error": f"Ungültige Antwort vom Test-Skript erhalten: {result}"})
