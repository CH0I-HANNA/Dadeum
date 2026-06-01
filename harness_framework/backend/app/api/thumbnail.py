from __future__ import annotations

import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from PIL import Image, ImageDraw

from app.core.config import UPLOAD_DIR
from app.pipeline.parser import SlideRaw, parse_file

router = APIRouter()

_THUMBNAIL_WIDTH = 400
_cache: dict[str, bytes] = {}

_TEXT_BOX_COLOR = (156, 163, 175)  # #9ca3af
_DIAGONAL_COLOR = (100, 100, 100)


def _render_thumbnail(slide: SlideRaw) -> bytes:
    w_emu = slide.slide_width_emu
    h_emu = slide.slide_height_emu

    if w_emu > 0 and h_emu > 0:
        thumb_h = round(_THUMBNAIL_WIDTH * h_emu / w_emu)
    else:
        thumb_h = round(_THUMBNAIL_WIDTH * 9 / 16)

    bg = slide.background_color_rgb
    img = Image.new("RGB", (_THUMBNAIL_WIDTH, thumb_h), color=bg)
    draw = ImageDraw.Draw(img)

    for elem in slide.text_elements:
        x0 = round(elem.x * _THUMBNAIL_WIDTH)
        y0 = round(elem.y * thumb_h)
        x1 = round((elem.x + elem.width) * _THUMBNAIL_WIDTH)
        y1 = round((elem.y + elem.height) * thumb_h)
        if x1 > x0 and y1 > y0:
            draw.rectangle([x0, y0, x1, y1], fill=_TEXT_BOX_COLOR)

    for elem in slide.image_elements:
        x0 = round(elem.x * _THUMBNAIL_WIDTH)
        y0 = round(elem.y * thumb_h)
        x1 = round((elem.x + elem.width) * _THUMBNAIL_WIDTH)
        y1 = round((elem.y + elem.height) * thumb_h)
        if x1 > x0 and y1 > y0:
            draw.rectangle([x0, y0, x1, y1], outline=_DIAGONAL_COLOR)
            draw.line([x0, y0, x1, y1], fill=_DIAGONAL_COLOR)
            draw.line([x0, y1, x1, y0], fill=_DIAGONAL_COLOR)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _find_file_path(file_id: str):
    for ext in (".pptx", ".pdf"):
        path = UPLOAD_DIR / f"{file_id}{ext}"
        if path.exists():
            return path
    return None


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

    try:
        slides = parse_file(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"썸네일 생성 실패: {e}") from e

    if slide_num >= len(slides):
        raise HTTPException(status_code=404, detail="슬라이드 번호가 범위를 벗어났습니다.")

    png_bytes = _render_thumbnail(slides[slide_num])
    _cache[cache_key] = png_bytes

    return Response(content=png_bytes, media_type="image/png")
