from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile

from app.core.config import DISK_FREE_THRESHOLD_MB, MAX_FILE_SIZE_MB, UPLOAD_DIR
from app.models.schemas import UploadResponse
from app.pipeline.parser import parse_file

router = APIRouter()

_ALLOWED_EXTENSIONS = {".pptx", ".pdf"}
_MAGIC_BYTES: dict[str, bytes] = {
    ".pptx": b"PK\x03\x04",
    ".pdf": b"%PDF",
}


def _check_disk_space() -> None:
    usage = shutil.disk_usage(UPLOAD_DIR)
    free_mb = usage.free / (1024 * 1024)
    if free_mb < DISK_FREE_THRESHOLD_MB:
        raise HTTPException(status_code=503, detail="서버 디스크 공간이 부족합니다.")


def _validate_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="PPTX 또는 PDF 파일만 업로드할 수 있습니다.")
    return ext


def _validate_magic_bytes(data: bytes, ext: str) -> None:
    expected = _MAGIC_BYTES[ext]
    if not data.startswith(expected):
        raise HTTPException(
            status_code=400,
            detail="파일이 손상되었거나 잘못된 형식입니다.",
        )


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다.")

    safe_name = Path(file.filename).name
    ext = _validate_extension(safe_name)

    content = await file.read()

    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"파일 크기가 {MAX_FILE_SIZE_MB}MB를 초과합니다. 더 작은 파일을 업로드해주세요.",
        )

    _validate_magic_bytes(content, ext)

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    _check_disk_space()

    file_id = str(uuid4())
    save_path = UPLOAD_DIR / f"{file_id}{ext}"
    save_path.write_bytes(content)

    try:
        slides = parse_file(save_path)
        slide_count = len(slides)
    except Exception:
        slide_count = 0

    return UploadResponse(
        file_id=file_id,
        slide_count=slide_count,
        filename=safe_name,
    )
