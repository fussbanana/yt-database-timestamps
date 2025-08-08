from functools import partial
from typing import Any, Callable, Optional, List, Dict

from loguru import logger
from PySide6.QtCore import QThread


class WorkerManager:

    _instance: Optional["WorkerManager"] = None

    def __init__(self, main_window: Any) -> None:

        logger.debug("Initialisiere WorkerManager.")
        self.main_window = main_window
        self.running_tasks: dict[str, dict] = {}
        self._workers: Dict[str, Dict[str, Any]] = {}
        logger.info("WorkerManager initialisiert.")

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

    def get_running_tasks_info(self) -> List[Dict[str, Any]]:
        """Get information about all running tasks.
        Returns:
            List of dictionaries containing task information with keys:
            - 'name': Task name
            - 'is_running': Boolean indicating if task is currently running
            - 'progress': Current progress (if available)
        """
        tasks_info = []
        for task_name, worker_info in self._workers.items():
            worker = worker_info.get("worker")
            thread = worker_info.get("thread")
            is_running = worker is not None and thread is not None and thread.isRunning()
            task_info = {
                "name": task_name,
                "is_running": is_running,
                "progress": getattr(worker, "progress", 0) if worker else 0,
            }
            tasks_info.append(task_info)
        return tasks_info

    def stop_all_workers(self) -> int:
        """Stop all running workers and their threads.

        Returns:
            int: Number of workers that were stopped
        """
        stopped_count = 0

        for task_name, worker_info in self._workers.items():
            worker = worker_info.get("worker")
            thread = worker_info.get("thread")

            if thread is not None and thread.isRunning():
                logger.debug(f"Stoppe Worker: {task_name}")

                # Stoppe den Worker falls er eine stop-Methode hat
                if worker and hasattr(worker, "stop"):
                    worker.stop()

                # Stoppe den Thread
                thread.quit()
                thread.wait(3000)  # Warte max. 3 Sekunden

                if thread.isRunning():
                    logger.warning(f"Thread für {task_name} konnte nicht ordnungsgemäß gestoppt werden")
                    thread.terminate()
                else:
                    logger.debug(f"Worker {task_name} erfolgreich gestoppt")
                    stopped_count += 1

        # Aufräumen: Gestoppte Worker aus dem Dictionary entfernen
        self._cleanup_finished_workers()

        logger.info(f"Insgesamt {stopped_count} Worker gestoppt")
        return stopped_count

    def _cleanup_finished_workers(self) -> None:
        """Remove finished workers from the workers dictionary."""
        finished_tasks = []

        for task_name, worker_info in self._workers.items():
            thread = worker_info.get("thread")
            if thread is None or not thread.isRunning():
                finished_tasks.append(task_name)

        for task_name in finished_tasks:
            logger.debug(f"Entferne beendeten Worker: {task_name}")
            del self._workers[task_name]
