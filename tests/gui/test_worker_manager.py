"""
Test für WorkerManager

Testet die grundlegende Instanziierung und das Starten eines Dummy-Workers.
"""

import pytest
from PySide6.QtWidgets import QApplication
from yt_database.gui.components.worker_manager import WorkerManager
from PySide6.QtCore import QObject, Signal

class DummyWorker(QObject):
    finished = Signal()
    error = Signal(str)

    def run(self):
        self.finished.emit()

def test_worker_manager_instantiation_and_run(qtbot):
    app = QApplication.instance() or QApplication([])
    main_window = object()  # Dummy-Objekt als MainWindow-Ersatz
    manager = WorkerManager.instance(main_window)
    results = {"finished": False, "error": None}

    def on_finish():
        results["finished"] = True

    def on_error(msg):
        results["error"] = msg

    worker = manager.start_worker(
        task_name="dummy_task",
        worker_factory=DummyWorker,
        on_finish=on_finish,
        on_error=on_error
    )
    qtbot.waitSignal(worker.finished, timeout=1000)
    assert results["finished"] is True
    assert results["error"] is None
