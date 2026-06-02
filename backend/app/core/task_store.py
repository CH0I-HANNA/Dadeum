from __future__ import annotations

import threading
from datetime import datetime
from typing import Optional

from app.models.schemas import AnalysisResult

_lock = threading.Lock()
_tasks: dict[str, dict] = {}
_file_to_task: dict[str, str] = {}


def create_task(task_id: str, file_id: str) -> None:
    with _lock:
        _tasks[task_id] = {
            "task_id": task_id,
            "file_id": file_id,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "result": None,
            "error_message": None,
        }
        _file_to_task[file_id] = task_id


def set_processing(task_id: str) -> None:
    with _lock:
        if task_id in _tasks:
            _tasks[task_id]["status"] = "processing"
            _tasks[task_id]["started_at"] = datetime.utcnow().isoformat()


def set_completed(task_id: str, result: AnalysisResult) -> None:
    with _lock:
        if task_id in _tasks:
            _tasks[task_id]["status"] = "completed"
            _tasks[task_id]["result"] = result
            _tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()


def set_error(task_id: str, message: str) -> None:
    with _lock:
        if task_id in _tasks:
            _tasks[task_id]["status"] = "error"
            _tasks[task_id]["error_message"] = message
            _tasks[task_id]["failed_at"] = datetime.utcnow().isoformat()


def get_task(task_id: str) -> Optional[dict]:
    with _lock:
        return _tasks.get(task_id)


def get_task_id_by_file_id(file_id: str) -> Optional[str]:
    with _lock:
        return _file_to_task.get(file_id)
