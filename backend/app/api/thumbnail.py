from __future__ import annotations

import io
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from app.core.config import UPLOAD_DIR

router = APIRouter()

_THUMBNAIL_WIDTH = 800
_cache: dict[str, bytes] = {}

_FONT_PATHS = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/SFNSText.ttf",
    "/System/Library/Fonts/SFNS.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_PATHS:
        try:
            return ImageFont.truetype(path, max(6, size))
        except Exception:
            continue
    return ImageFont.load_default()


def _get_bg_color(slide) -> tuple[int, int, int]:
    try:
        fill = slide.background.fill
        rgb = fill.fore_color.rgb
        return (rgb[0], rgb[1], rgb[2])
    except Exception:
        return (255, 255, 255)


def _safe_shape_fill(shape) -> tuple[int, int, int] | None:
    try:
        fill = shape.fill
        rgb = fill.fore_color.rgb
        return (rgb[0], rgb[1], rgb[2])
    except Exception:
        return None


def _render_shape(shape, img: Image.Image, draw: ImageDraw.ImageDraw, scale: float, thumb_h: int) -> None:
    left = int((shape.left or 0) * scale)
    top = int((shape.top or 0) * scale)
    width = max(1, int((shape.width or 0) * scale))
    height = max(1, int((shape.height or 0) * scale))

    fill_color = _safe_shape_fill(shape)
    if fill_color:
        draw.rectangle([left, top, left + width, top + height], fill=fill_color)

    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
        try:
            blob = shape.image.blob
            sub = Image.open(io.BytesIO(blob)).convert("RGBA")
            sub = sub.resize((width, height), Image.LANCZOS)
            bg_sub = Image.new("RGBA", (width, height), (255, 255, 255, 255))
            bg_sub.paste(sub, mask=sub.split()[3])
            img.paste(bg_sub.convert("RGB"), (left, top))
        except Exception:
            draw.rectangle([left, top, left + width, top + height], fill=(200, 200, 200))
            draw.line([left, top, left + width, top + height], fill=(150, 150, 150), width=2)
            draw.line([left, top + height, left + width, top], fill=(150, 150, 150), width=2)

    elif shape.shape_type == MSO_SHAPE_TYPE.GROUP:
        try:
            for sub_shape in shape.shapes:
                _render_shape(sub_shape, img, draw, scale, thumb_h)
        except Exception:
            pass

    elif shape.has_text_frame:
        y_cursor = top + 2
        for para in shape.text_frame.paragraphs:
            line_text = "".join(run.text for run in para.runs)
            if not line_text.strip():
                y_cursor += 4
                continue

            fs_pt = 18.0
            color: tuple[int, int, int] = (0, 0, 0)
            for run in para.runs:
                if run.text:
                    try:
                        fs_pt = run.font.size.pt if run.font.size else 18.0
                    except Exception:
                        pass
                    try:
                        if run.font.color.type is not None:
                            rgb = run.font.color.rgb
                            color = (rgb[0], rgb[1], rgb[2])
                    except Exception:
                        pass
                    break

            fs_px = max(6, int(fs_pt * 12700 * scale))
            font = _load_font(fs_px)

            if y_cursor + fs_px > top + height:
                break

            try:
                draw.text((left + 4, y_cursor), line_text, fill=color, font=font)
                bbox = draw.textbbox((left + 4, y_cursor), line_text, font=font)
                line_h = bbox[3] - bbox[1]
            except Exception:
                draw.text((left + 4, y_cursor), line_text, fill=color)
                line_h = fs_px

            y_cursor += line_h + 2


def _render_pptx_slide(file_path: Path, slide_index: int) -> bytes:
    prs = Presentation(str(file_path))
    if slide_index >= len(prs.slides):
        raise HTTPException(status_code=404, detail="슬라이드 번호가 범위를 벗어났습니다.")

    slide_w_emu = int(prs.slide_width)
    slide_h_emu = int(prs.slide_height)
    slide = prs.slides[slide_index]

    thumb_h = round(_THUMBNAIL_WIDTH * slide_h_emu / slide_w_emu)
    scale = _THUMBNAIL_WIDTH / slide_w_emu

    bg = _get_bg_color(slide)
    img = Image.new("RGB", (_THUMBNAIL_WIDTH, thumb_h), color=bg)
    draw = ImageDraw.Draw(img)

    for shape in slide.shapes:
        try:
            _render_shape(shape, img, draw, scale, thumb_h)
        except Exception:
            pass

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _render_pdf_slide(file_path: Path, slide_index: int) -> bytes:
    from pdf2image import convert_from_path

    images = convert_from_path(
        str(file_path),
        dpi=150,
        first_page=slide_index + 1,
        last_page=slide_index + 1,
        size=(_THUMBNAIL_WIDTH, None),
    )
    if not images:
        raise ValueError("페이지 변환 실패")
    buf = io.BytesIO()
    images[0].save(buf, format="PNG")
    return buf.getvalue()


def _find_file_path(file_id: str) -> Path | None:
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
        if file_path.suffix == ".pdf":
            png_bytes = _render_pdf_slide(file_path, slide_num)
        else:
            png_bytes = _render_pptx_slide(file_path, slide_num)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"썸네일 생성 실패: {e}") from e

    _cache[cache_key] = png_bytes
    return Response(content=png_bytes, media_type="image/png")
