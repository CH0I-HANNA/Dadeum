from __future__ import annotations

import io
import os
import re
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pptx import Presentation
from pptx.dml.color import RGBColor

from app.api.thumbnail import _find_file_path, _render_pptx_slide
from app.core import task_store
from app.models.schemas import AnalysisResult, FixRequest, OutlierSlide

router = APIRouter()


def _apply_fixes_to_slide(slide, outlier: OutlierSlide) -> None:
    target_font: str | None = None
    target_color: RGBColor | None = None

    for rc in outlier.root_causes:
        if rc.feature_group == "typography" and target_font is None:
            target_font = rc.expected_value
        if rc.feature_group == "color" and target_color is None:
            m = re.search(r"RGB\((\d+),\s*(\d+),\s*(\d+)\)", rc.expected_value)
            if m:
                target_color = RGBColor(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                if target_font:
                    run.font.name = target_font
                if target_color:
                    run.font.color.rgb = target_color


@router.post("/fix/{file_id}")
async def fix_presentation(file_id: str, task_body: FixRequest) -> Response:
    task = task_store.get_task(task_body.task_id)
    if task is None or task["status"] != "completed":
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")

    result: AnalysisResult = task["result"]

    file_path = _find_file_path(file_id)
    if file_path is None or file_path.suffix != ".pptx":
        raise HTTPException(status_code=404, detail="PPTX 파일만 수정 가능합니다.")

    prs = Presentation(str(file_path))

    for outlier in result.outlier_slides:
        prs_slide = prs.slides[outlier.slide_index]
        _apply_fixes_to_slide(prs_slide, outlier)

    buf = io.BytesIO()
    prs.save(buf)
    pptx_bytes = buf.getvalue()

    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="dadeum-fixed-{file_id[:8]}.pptx"'},
    )


@router.get("/preview-fix/{file_id}/{slide_num}")
async def preview_fix(file_id: str, slide_num: int, task_id: str = Query(...)) -> Response:
    if slide_num < 0:
        raise HTTPException(status_code=400, detail="slide_num은 0 이상이어야 합니다.")

    task = task_store.get_task(task_id)
    if task is None or task["status"] != "completed":
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")

    result: AnalysisResult = task["result"]

    file_path = _find_file_path(file_id)
    if file_path is None or file_path.suffix != ".pptx":
        raise HTTPException(status_code=404, detail="PPTX 파일만 수정 가능합니다.")

    outlier = next((o for o in result.outlier_slides if o.slide_index == slide_num), None)
    if outlier is None:
        raise HTTPException(status_code=404, detail="해당 슬라이드는 이상 슬라이드가 아닙니다.")

    prs = Presentation(str(file_path))
    prs_slide = prs.slides[slide_num]
    _apply_fixes_to_slide(prs_slide, outlier)

    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        prs.save(str(tmp_path))

    try:
        png_bytes = _render_pptx_slide(tmp_path, slide_num)
    finally:
        os.unlink(tmp_path)

    return Response(content=png_bytes, media_type="image/png")
