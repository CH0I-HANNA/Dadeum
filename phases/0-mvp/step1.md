# Step 1: pptx-parser

## 읽어야 할 파일

- `backend/app/models/schemas.py`

## 작업

`backend/app/pipeline/parser.py` 를 구현하라.

이 모듈의 역할: PPTX 또는 PDF 파일을 받아 슬라이드별 원본 정보를 구조화된 데이터(`SlideRaw`)로 추출한다. 이후 모든 파이프라인 모듈은 이 구조체를 입력으로 받는다.

### 데이터 구조

`parser.py` 상단에 아래 dataclass를 정의하라 (Pydantic이 아닌 순수 dataclass — 파이프라인 내부 전용):

```python
@dataclass
class TextElement:
    text: str
    font_family: str        # 폰트명, 불명확하면 "Unknown"
    font_size: float        # pt 단위
    is_bold: bool
    is_italic: bool
    color_rgb: tuple[int, int, int]  # (R, G, B)
    x: float                # EMU → 비율 (0~1), 슬라이드 너비 기준
    y: float
    width: float
    height: float
    alignment: str          # "left" | "center" | "right" | "unknown"

@dataclass
class ImageElement:
    x: float
    y: float
    width: float
    height: float

@dataclass
class SlideRaw:
    slide_index: int         # 0-based
    text_elements: list[TextElement]
    image_elements: list[ImageElement]
    background_color_rgb: tuple[int, int, int]  # 추출 불가 시 (255, 255, 255)
    slide_width_emu: int
    slide_height_emu: int
```

### 구현할 함수

```python
def parse_pptx(file_path: str | Path) -> list[SlideRaw]:
    """PPTX 파일을 파싱하여 슬라이드별 SlideRaw 목록을 반환한다."""
    ...

def parse_pdf(file_path: str | Path) -> list[SlideRaw]:
    """PDF 파일을 파싱하여 슬라이드별 SlideRaw 목록을 반환한다.
    PDF는 텍스트 위치/폰트 정보만 추출 가능하며, 이미지 위치는 bbox로 추정한다."""
    ...

def parse_file(file_path: str | Path) -> list[SlideRaw]:
    """확장자를 보고 parse_pptx 또는 parse_pdf를 호출한다."""
    ...
```

### PPTX 파싱 상세 규칙

- `python-pptx` 의 `Presentation` 객체를 사용한다.
- 각 슬라이드의 `shapes` 를 순회하며 `TEXT_BOX`, `PLACEHOLDER` 타입에서 `TextElement` 를 추출한다.
- `PICTURE` 타입은 `ImageElement` 로 추출한다.
- 폰트는 `run.font.name` → `paragraph.font.name` → `"Unknown"` 순으로 fallback한다.
- 폰트 크기는 `run.font.size` (EMU) → `paragraph.font.size` → `18.0` (기본값) 순으로 fallback한다. `Pt` 단위로 변환한다.
- 색상은 `run.font.color.rgb` 가 없으면 `(0, 0, 0)` 으로 처리한다.
- 배경색은 `slide.background.fill` 에서 추출한다. `solid` fill이 아니면 `(255, 255, 255)` 로 처리한다.
- 위치(x, y, width, height)는 EMU 값을 슬라이드 크기로 나눠 0~1 비율로 정규화한다.

### 테스트

`backend/tests/test_parser.py` 를 작성하라. 테스트용 PPTX 파일을 `python-pptx` 로 직접 생성하여 fixture로 사용한다 (실제 파일 의존성 없음).

검증해야 할 것:
- `parse_pptx` 가 슬라이드 수만큼 `SlideRaw` 를 반환하는가
- `TextElement` 의 font_family, font_size, color_rgb 가 올바르게 추출되는가
- 위치값이 0~1 사이로 정규화되는가

## Acceptance Criteria

```bash
cd backend && python -m pytest tests/test_parser.py -v
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 모든 테스트가 통과하는지 확인한다.
3. `phases/0-mvp/index.json` 의 step 1 을 업데이트한다.

## 금지사항

- `SlideRaw` 에 Pydantic을 사용하지 마라. 파이프라인 내부 구조체는 순수 dataclass다.
- PDF 파싱에서 이미지를 렌더링하거나 변환하지 마라. 텍스트와 이미지 bbox 좌표만 추출한다.
- 이 step에서 feature 추출 로직을 구현하지 마라. `SlideRaw` 는 원본 정보 보존이 목적이다.
