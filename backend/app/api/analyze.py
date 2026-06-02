from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.core import task_store
from app.core.config import UPLOAD_DIR
from app.models.schemas import AnalyzeResponse, ResultResponse
from app.services.analysis_service import run_analysis_with_timeout

router = APIRouter()


def _find_file(file_id: str) -> Path:
    for ext in (".pptx", ".pdf"):
        path = UPLOAD_DIR / f"{file_id}{ext}"
        if path.exists():
            return path
    raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")


@router.post("/analyze/{file_id}", response_model=AnalyzeResponse, status_code=202)
async def start_analysis(file_id: str, background_tasks: BackgroundTasks) -> AnalyzeResponse:
    file_path = _find_file(file_id)

    existing_task_id = task_store.get_task_id_by_file_id(file_id)
    if existing_task_id is not None:
        task = task_store.get_task(existing_task_id)
        if task and task["status"] in ("pending", "processing"):
            raise HTTPException(status_code=409, detail="이미 분석이 진행 중입니다.")

    task_id = str(uuid4())
    task_store.create_task(task_id, file_id)
    background_tasks.add_task(run_analysis_with_timeout, file_path, file_id, task_id)

    return AnalyzeResponse(task_id=task_id)


@router.get("/result/{task_id}", response_model=ResultResponse)
async def get_result(task_id: str) -> ResultResponse:
    task = task_store.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")

    status = task["status"]
    if status in ("pending", "processing"):
        return ResultResponse(task_id=task_id, status=status)
    if status == "completed":
        return ResultResponse(task_id=task_id, status="completed", result=task["result"])
    return ResultResponse(
        task_id=task_id,
        status="error",
        error_message=task.get("error_message"),
    )
