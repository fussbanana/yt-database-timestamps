from functools import partial
from typing import Any, Callable, Optional

from loguru import logger
from PySide6.QtCore import QThread

"""
WorkerManager-Modul
Verwaltet die Ausführung, Überwachung und das Lifecycle-Management von Hintergrund-Worker-Threads
in einer Qt-basierten Anwendung. Bietet eine Singleton-Instanz, Task-Tracking und automatisches Cleanup.
"""


class WorkerManager:
    """Verwaltet die Ausführung und das Lifecycle-Management von Worker-Threads.

    Diese Klasse bietet Methoden zum Starten, Überwachen und Aufräumen von Hintergrund-Tasks
    (Worker), die in separaten Qt-Threads laufen. Sie stellt sicher, dass Tasks eindeutig
    verwaltet werden und bietet ein Singleton-Pattern für globalen Zugriff.

    Attributes:
        main_window (Any): Referenz auf das MainWindow für UI-Interaktionen.
        running_tasks (dict[str, dict]): Tracking der aktuell laufenden Tasks.
        _instance (Optional[WorkerManager]): Singleton-Instanz.

    Example:
        manager = WorkerManager.instance(main_window)
        manager.start_worker("task1", factory, on_finish, on_error)
    """

    _instance: Optional["WorkerManager"] = None

    def __init__(self, main_window: Any) -> None:
        """Initialisiert den WorkerManager und das Task-Tracking.

        Args:
            main_window (Any): Referenz auf das MainWindow für UI-Interaktionen.
        """
        logger.debug("Initialisiere WorkerManager.")
        self.main_window = main_window
        self.running_tasks: dict[str, dict] = {}
        logger.debug("WorkerManager initialisiert.")

    def start_worker(
        self,
        task_name: str,
        worker_factory: Callable[..., Any],
        on_finish: Callable[[], None],
        on_error: Callable[[str], None],
        worker_args: Optional[tuple] = None,
        worker_kwargs: Optional[dict] = None,
        start_immediately: bool = True,
        additional_signal_connections: Optional[Callable[[Any], None]] = None,
    ) -> Optional[Any]:
        """Startet einen neuen Worker-Thread und verwaltet Cleanup und Signalverbindungen.

        Args:
            task_name (str): Eindeutiger Name des Tasks.
            worker_factory (Callable[..., Any]): Factory-Funktion zur Worker-Erzeugung.
            on_finish (Callable[[], None]): Callback bei erfolgreichem Abschluss.
            on_error (Callable[[str], None]): Callback bei Fehler.
            worker_args (Optional[tuple]): Argumente für die Factory.
            worker_kwargs (Optional[dict]): Keyword-Argumente für die Factory.
            start_immediately (bool): Ob der Thread sofort gestartet wird.
            additional_signal_connections (Optional[Callable[[Any], None]]): Zusätzliche Signalverbindungen.

        Returns:
            Optional[Any]: Die Worker-Instanz oder None, falls Task bereits läuft.

        Raises:
            ValueError: Falls Taskname bereits existiert.
        """
        logger.debug(f"Starte Worker für Task '{task_name}' mit Factory {worker_factory}.")
        # Prüfe, ob die Aufgabe bereits läuft
        # Ich prüfe, ob der Taskname schon im Dictionary ist, um doppelte Ausführung zu verhindern.
        if task_name in self.running_tasks:
            logger.warning(f"Aufgabe '{task_name}' läuft bereits.")
            return None
        # Setze Standardwerte für Argumente
        # Falls keine Argumente übergeben wurden, initialisiere mit leeren Defaults.
        if worker_args is None:
            worker_args = ()
        if worker_kwargs is None:
            worker_kwargs = {}
        # Erzeuge neuen QThread für den Worker
        # Jeder Worker läuft in einem eigenen Thread für echte Parallelität.
        thread = QThread()
        # Erzeuge Worker-Instanz über die Factory
        worker = worker_factory(*worker_args, **worker_kwargs)
        # Verschiebe Worker in den neuen Thread
        worker.moveToThread(thread)
        # Trage Task im Task-Tracking-Dictionary ein
        # Ich speichere alle relevanten Infos für spätere Verwaltung und Cleanup.
        self.running_tasks[task_name] = {
            "thread": thread,
            "worker": worker,
            "on_finish": on_finish,
            "on_error": on_error,
        }
        # Verbinde die relevanten Qt-Signale
        # Starte die Ausführung, verbinde Finish/Error mit den Callbacks.
        thread.started.connect(worker.run)
        worker.finished.connect(on_finish)
        worker.error.connect(on_error)

        # Thread-Cleanup Signale
        # Beende den Thread, wenn der Worker fertig ist oder einen Fehler wirft.
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(partial(self.on_thread_actually_finished, task_name))

        # Worker-Cleanup: Lösche Worker-Objekt wenn Thread beendet ist
        def cleanup_worker():
            logger.debug(f"Bereinige Worker-Objekt für Task '{task_name}'")
            worker.deleteLater()

        thread.finished.connect(cleanup_worker)

        # Verbinde zusätzliche Signale VOR dem Thread-Start
        # Ermöglicht flexible Erweiterung für spezielle Worker.
        if additional_signal_connections:
            additional_signal_connections(worker)

        # Starte den Thread sofort oder warte auf manuellen Start
        if start_immediately:
            thread.start()
            logger.debug(f"Thread für Task '{task_name}' wurde gestartet.")
        else:
            logger.debug(f"Worker für '{task_name}' vorbereitet, wartet auf manuellen Start.")
        # Rückgabe der Worker-Instanz
        return worker

    def on_thread_actually_finished(self, task_name: str) -> None:
        """Entfernt beendete Tasks aus der Verwaltung.

        Args:
            task_name (str): Name des beendeten Tasks.
        """
        logger.debug(f"Thread für Aufgabe '{task_name}' hat sich beendet. Entferne aus der Liste.")
        # Ich entferne den Task aus dem Dictionary, damit keine Speicherlecks entstehen.
        if task_name in self.running_tasks:
            del self.running_tasks[task_name]
        logger.debug(f"Task '{task_name}' wurde aus der Verwaltung entfernt.")

    @classmethod
    def instance(cls, main_window: Optional[Any] = None):
        """Gibt die Singleton-Instanz des WorkerManagers zurück.

        Args:
            main_window (Any, optional): Referenz auf das MainWindow (nur beim ersten Aufruf nötig).

        Returns:
            WorkerManager: Die Singleton-Instanz.

        Raises:
            ValueError: Falls main_window beim ersten Aufruf fehlt.
        """
        # Singleton-Instanz erzeugen oder zurückgeben
        if not hasattr(cls, "_instance") or cls._instance is None:
            if main_window is None:
                raise ValueError("main_window muss beim ersten Aufruf übergeben werden!")
            cls._instance = cls(main_window)
        return cls._instance
