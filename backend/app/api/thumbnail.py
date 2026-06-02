from __future__ import annotations

import io
import subprocess
import tempfile
import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from PIL import Image

from app.core.config import UPLOAD_DIR

router = APIRouter()

_cache: dict[str, bytes] = {}


def _find_file_path(file_id: str) -> Path | None:
    for ext in (".pptx", ".pdf"):
        path = UPLOAD_DIR / f"{file_id}{ext}"
        if path.exists():
            return path
    return None


def _render_with_libreoffice(file_path: Path, slide_num: int) -> bytes:
    """LibreOffice로 슬라이드를 PNG로 변환하고 해당 슬라이드 이미지를 반환한다."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--norestore",
                "--convert-to", "png",
                "--outdir", tmpdir,
                str(file_path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        tmp_path = Path(tmpdir)
        png_files = sorted(tmp_path.glob("*.png"))

        # LibreOffice가 단일 PNG 또는 슬라이드별 PNG를 생성
        if not png_files:
            raise RuntimeError(f"LibreOffice 변환 실패: {result.stderr}")

        if len(png_files) == 1 and slide_num == 0:
            # 단일 페이지 또는 첫 슬라이드
            img_path = png_files[0]
        elif slide_num < len(png_files):
            img_path = png_files[slide_num]
        else:
            # 슬라이드 수보다 적은 이미지가 생성된 경우 (LibreOffice가 첫 장만 변환)
            # 파일명에서 슬라이드 번호를 찾아봄
            numbered = sorted(tmp_path.glob(f"*{slide_num + 1}.png"))
            if numbered:
                img_path = numbered[0]
            else:
                raise RuntimeError(f"슬라이드 {slide_num}에 해당하는 이미지를 찾을 수 없습니다.")

        img = Image.open(img_path)
        # 너비 600px로 리사이즈 (원본 비율 유지)
        w, h = img.size
        new_w = 600
        new_h = round(h * new_w / w)
        img = img.resize((new_w, new_h), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()


def _render_all_slides_libreoffice(file_path: Path) -> list[bytes]:
    """LibreOffice로 전체 슬라이드를 변환하고 슬라이드별 PNG 바이트 리스트를 반환한다."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--norestore",
                "--convert-to", "png",
                "--outdir", tmpdir,
                str(file_path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        tmp_path = Path(tmpdir)
        png_files = sorted(tmp_path.glob("*.png"))

        results = []
        for png_path in png_files:
            img = Image.open(png_path)
            w, h = img.size
            new_w = 600
            new_h = round(h * new_w / w)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            results.append(buf.getvalue())

        return results


@router.get("/thumbnail/{file_id}/{slide_num}")
async def get_thumbnail(file_id: str, slide_num: int) -> Response:
    if slide_num < 0:
        raise HTTPException(status_code=400, detail="slide_num은 0 이상이어야 합니다.")

    file_path = _find_file_path(file_id)
    if file_path is None:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    cache_key = f"{file_id}:{slide_num}"
    if cache_key in _cache:
        return Response(content=_cache[cache_key], media_type="image/png")

    # 같은 파일의 전체 슬라이드가 캐시에 없으면 한 번에 전부 변환
    file_cache_key = f"{file_id}:0"
    if file_cache_key not in _cache:
        try:
            all_slides = _render_all_slides_libreoffice(file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"썸네일 생성 실패: {e}") from e

        for i, png_bytes in enumerate(all_slides):
            _cache[f"{file_id}:{i}"] = png_bytes

    if cache_key not in _cache:
        raise HTTPException(status_code=404, detail="슬라이드 번호가 범위를 벗어났습니다.")

    return Response(content=_cache[cache_key], media_type="image/png")
