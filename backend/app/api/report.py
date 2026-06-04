from __future__ import annotations

import io
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from fpdf import FPDF

from app.api.thumbnail import _find_file_path, _render_pdf_slide, _render_pptx_slide
from app.core import task_store
from app.models.schemas import AnalysisResult

router = APIRouter()

_KOREAN_FONT_CANDIDATES = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/Library/Fonts/NanumGothic.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
]


def _build_pdf(result: AnalysisResult, task_id: str) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    korean_font_path = next((p for p in _KOREAN_FONT_CANDIDATES if os.path.exists(p)), None)

    def set_font(size: int, style: str = "") -> None:
        if korean_font_path:
            pdf.set_font("Korean", style=style, size=size)
        else:
            pdf.set_font("Helvetica", style=style, size=size)

    if korean_font_path:
        pdf.add_font("Korean", fname=korean_font_path)
        pdf.add_font("Korean", style="B", fname=korean_font_path)

    # ── 헤더 ──────────────────────────────────────────────
    set_font(18, "B")
    pdf.cell(0, 10, "다듬 분석 보고서", new_x="LMARGIN", new_y="NEXT", align="L")

    set_font(10)
    pdf.cell(0, 8, f"슬라이드 {result.slide_count}장", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(4)

    # ── 일관성 점수 섹션 ──────────────────────────────────
    set_font(12, "B")
    pdf.cell(0, 8, "일관성 점수", new_x="LMARGIN", new_y="NEXT", align="L")

    set_font(10)
    score = result.consistency_score
    pdf.cell(0, 7, f"  전체 점수: {score.total:.1f} / 100", new_x="LMARGIN", new_y="NEXT")

    sub = score.sub_scores
    pdf.cell(0, 6, f"  - 폰트:    {sub.typography:.1f}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"  - 색상:    {sub.color:.1f}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"  - 레이아웃: {sub.layout:.1f}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"  - 콘텐츠:  {sub.content:.1f}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── 이상 슬라이드 섹션 ────────────────────────────────
    set_font(12, "B")
    pdf.cell(0, 8, "이상 슬라이드", new_x="LMARGIN", new_y="NEXT", align="L")

    if not result.outlier_slides:
        set_font(10)
        pdf.cell(0, 7, "  이상 슬라이드가 없습니다.", new_x="LMARGIN", new_y="NEXT")
    else:
        file_path = _find_file_path(result.file_id)

        for outlier in result.outlier_slides:
            slide_num = outlier.slide_index + 1

            set_font(11, "B")
            pdf.cell(0, 9, f"슬라이드 {slide_num}  (이상 점수: {outlier.anomaly_score:.3f})",
                     new_x="LMARGIN", new_y="NEXT")

            # 썸네일 삽입
            if file_path is not None:
                try:
                    if file_path.suffix == ".pdf":
                        png_bytes = _render_pdf_slide(file_path, outlier.slide_index)
                    else:
                        png_bytes = _render_pptx_slide(file_path, outlier.slide_index)
                    pdf.image(io.BytesIO(png_bytes), w=160)
                    pdf.ln(2)
                except Exception:
                    pass

            # 원인 목록
            if outlier.root_causes:
                set_font(10, "B")
                pdf.cell(0, 6, "  원인:", new_x="LMARGIN", new_y="NEXT")
                set_font(10)
                for cause in outlier.root_causes:
                    pdf.cell(0, 6, f"    - {cause.label}  (기대값: {cause.expected_value} / 실제값: {cause.actual_value})",
                             new_x="LMARGIN", new_y="NEXT")

            # 수정 제안 목록
            if outlier.recommendations:
                set_font(10, "B")
                pdf.cell(0, 6, "  수정 제안:", new_x="LMARGIN", new_y="NEXT")
                set_font(10)
                for rec in outlier.recommendations:
                    pdf.cell(0, 6, f"    - {rec.action}  (+{rec.impact_score_delta:.1f}점 예상)",
                             new_x="LMARGIN", new_y="NEXT")

            pdf.ln(4)

    return bytes(pdf.output())


@router.get("/report/{task_id}")
async def get_report(task_id: str) -> Response:
    task = task_store.get_task(task_id)
    if task is None or task["status"] != "completed":
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")

    result: AnalysisResult = task["result"]
    pdf_bytes = _build_pdf(result, task_id)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="dadeum-report-{task_id[:8]}.pdf"'},
    )
