import uuid
from typing import Dict, List, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from core.downloader import DownloadTask

class QueueManager(QObject):
    task_added = pyqtSignal(dict)
    task_updated = pyqtSignal(str, dict)
    task_completed = pyqtSignal(str, str)
    task_failed = pyqtSignal(str, str)
    queue_changed = pyqtSignal()

    def __init__(self, max_concurrent: int = 3):
        super().__init__()
        self.max_concurrent = max_concurrent
        self.tasks: Dict[str, dict] = {}           # task_id -> task_meta
        self.workers: Dict[str, DownloadTask] = {}  # task_id -> active QThread
        self.waiting_queue: List[str] = []         # list of task_ids

    def set_max_concurrent(self, val: int):
        self.max_concurrent = max(1, min(val, 10))
        self._process_queue()

    def add_download(self, options: dict) -> str:
        task_id = str(uuid.uuid4())[:8]
        task_info = {
            "id": task_id,
            "title": options.get("title", "Untitled Download"),
            "uploader": options.get("uploader", "Unknown"),
            "thumbnail": options.get("thumbnail", ""),
            "duration": options.get("duration", ""),
            "format_desc": options.get("format_desc", ""),
            "options": options,
            "status": "queued",
            "percent": 0.0,
            "speed": "",
            "eta": "",
            "downloaded_bytes": 0,
            "total_bytes": 0,
            "filepath": "",
            "error": ""
        }
        self.tasks[task_id] = task_info
        self.waiting_queue.append(task_id)
        self.task_added.emit(task_info)
        self.queue_changed.emit()
        self._process_queue()
        return task_id

    def _process_queue(self):
        # Count currently active running workers
        active_count = len(self.workers)
        while active_count < self.max_concurrent and self.waiting_queue:
            task_id = self.waiting_queue.pop(0)
            if task_id not in self.tasks:
                continue
            
            task_info = self.tasks[task_id]
            task_info["status"] = "starting"
            self.task_updated.emit(task_id, {"status": "starting", "status_text": "Starting download..."})

            worker = DownloadTask(task_id, task_info["options"])
            worker.progress_signal.connect(self._on_progress)
            worker.finished_signal.connect(self._on_finished)
            worker.error_signal.connect(self._on_error)
            
            self.workers[task_id] = worker
            worker.start()
            active_count += 1

    def _on_progress(self, task_id: str, p: dict):
        if task_id in self.tasks:
            self.tasks[task_id].update(p)
            self.task_updated.emit(task_id, p)

    def _on_finished(self, task_id: str, filepath: str):
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["percent"] = 100.0
            self.tasks[task_id]["filepath"] = filepath
        if task_id in self.workers:
            del self.workers[task_id]
        
        self.task_completed.emit(task_id, filepath)
        self.queue_changed.emit()
        self._process_queue()

    def _on_error(self, task_id: str, err: str):
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "cancelled" if err == "Cancelled" else "error"
            self.tasks[task_id]["error"] = err
        if task_id in self.workers:
            del self.workers[task_id]

        self.task_failed.emit(task_id, err)
        self.queue_changed.emit()
        self._process_queue()

    def cancel_task(self, task_id: str):
        if task_id in self.waiting_queue:
            self.waiting_queue.remove(task_id)
            if task_id in self.tasks:
                self.tasks[task_id]["status"] = "cancelled"
                self.task_failed.emit(task_id, "Cancelled")
                self.queue_changed.emit()
        elif task_id in self.workers:
            self.workers[task_id].cancel()

    def remove_task(self, task_id: str):
        self.cancel_task(task_id)
        if task_id in self.tasks:
            del self.tasks[task_id]
        self.queue_changed.emit()

    def clear_completed(self):
        to_del = [tid for tid, t in self.tasks.items() if t["status"] in ("completed", "cancelled", "error")]
        for tid in to_del:
            if tid in self.tasks:
                del self.tasks[tid]
        self.queue_changed.emit()

    def get_all_tasks(self) -> List[dict]:
        return list(self.tasks.values())
