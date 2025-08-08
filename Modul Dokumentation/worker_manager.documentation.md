# Modul-Dokumentation: `worker_manager.py`

## Übersicht

Das Modul `worker_manager.py` verwaltet die Lebenszyklen und die Steuerung von Worker-Threads innerhalb der GUI-Anwendung. Es stellt sicher, dass Aufgaben (Tasks) parallel und kontrolliert ausgeführt werden können, und bietet Mechanismen zur Überwachung, zum Starten, Stoppen und zur Fehlerbehandlung von Worker-Instanzen.

## Hauptklasse: `WorkerManager`

### Zweck

Die Klasse `WorkerManager` ist als Singleton implementiert und übernimmt die zentrale Verwaltung aller Worker-Threads. Sie sorgt für die Initialisierung, das Starten, Stoppen und die Statusabfrage der Worker und stellt sicher, dass keine doppelten Aufgaben gestartet werden.

### Wichtige Methoden

- **`__init__(self, main_window: MainWindow)`**: Initialisiert den Manager mit Referenz auf das Hauptfenster.
- **`start_worker(self, task_name: str, worker_class: Type[QThread], *args, **kwargs) -> Optional[QThread]`**: Startet einen neuen Worker-Thread für die angegebene Aufgabe, sofern diese nicht bereits läuft.
- **`prepare_worker(self, task_name: str, worker_class: Type[QThread], *args, **kwargs) -> QThread`**: Bereitet einen Worker vor, ohne ihn direkt zu starten.
- **`stop_worker(self, task_name: str) -> None`**: Stoppt einen spezifischen Worker-Thread.
- **`stop_all_workers(self) -> None`**: Beendet alle laufenden Worker-Threads.
- **`get_running_tasks_info(self) -> List[Dict[str, Any]]`**: Gibt eine Liste mit Informationen zu allen laufenden Tasks zurück.
- **`on_thread_actually_finished(self, task_name: str) -> None`**: Callback, wenn ein Thread tatsächlich beendet wurde.
- **`instance(cls, main_window: MainWindow = None) -> WorkerManager`**: Singleton-Instanzzugriff.

### Datenstrukturen

- **`self.running_tasks: Dict[str, QThread]`**: Hält alle aktuell laufenden Worker-Threads, indiziert nach Task-Namen.
- **`self.main_window: MainWindow`**: Referenz auf das Hauptfenster zur Interaktion mit der GUI.

## Abhängigkeiten

- **PySide6.QtCore.QThread**: Für die Thread-Verwaltung.
- **loguru.logger**: Für Logging und Fehlerausgaben.
- **QIcon, Icons**: Für die visuelle Darstellung und Statusanzeigen in der GUI.
- **MainWindow**: Hauptfenster der Anwendung, wird für Statusanzeigen und Interaktionen benötigt.

## Typische Workflows

1. **Starten eines Workers**: Über `start_worker` wird ein neuer Thread für eine Aufgabe gestartet, sofern diese nicht bereits läuft.
2. **Stoppen eines Workers**: Mit `stop_worker` kann ein spezifischer Thread beendet werden; `stop_all_workers` beendet alle.
3. **Statusabfrage**: Mit `get_running_tasks_info` werden alle laufenden Tasks und deren Status zurückgegeben.
4. **Fehlerbehandlung**: Fehler und doppelte Starts werden über Logging und Rückgabewerte behandelt.

## Beispiel: Starten eines Workers

```python
from yt_database.gui.components.worker_manager import WorkerManager

worker_manager = WorkerManager.instance(main_window)
worker = worker_manager.start_worker(
    task_name="Transkription",
    worker_class=TranscriptWorker,
    video_id="abc123"
)
```

## Hinweise

- Die Klasse ist als Singleton ausgelegt; Zugriff erfolgt über `WorkerManager.instance()`.
- Die Methoden sind strikt typisiert und mit Google-Style-Docstrings versehen.
- Die Verwaltung der Worker erfolgt thread-sicher und GUI-konform.

## Autoren & Wartung

- Hauptautor: Sascha (Projektinhaber)
- Wartung: Siehe Projekt-README

---

