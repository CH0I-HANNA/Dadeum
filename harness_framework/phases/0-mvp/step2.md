# Step 2: feature-extractor

## 읽어야 할 파일

- `backend/app/pipeline/parser.py` (SlideRaw 구조체 확인)

## 작업

`backend/app/pipeline/extractor.py` 를 구현하라.

이 모듈의 역할: `SlideRaw` 목록을 받아 각 슬라이드를 수치 벡터(`SlideFeatureVector`)로 변환한다. 이후 scorer, detector, explainer 모두 이 벡터를 입력으로 받는다.

### 데이터 구조

```python
@dataclass
class SlideFeatureVector:
    slide_index: int

    # Typography (29차원)
    dominant_font_one_hot: list[float]  # 길이 20, KNOWN_FONTS(19개) + Other(1개) 원-핫
    font_size_mean: float               # pt / 72 으로 정규화
    font_size_std: float                # pt / 72 으로 정규화
    font_size_min: float                # pt / 72 으로 정규화
    font_size_max: float                # pt / 72 으로 정규화
    font_size_median: float             # pt / 72 으로 정규화
    bold_ratio: float
    italic_ratio: float
    font_variety_count: float           # 정규화 (사용 폰트 수 / 5, clip at 1.0)
    line_spacing_normalized: float      # 줄간격 평균 / 2.0, clip at 1.0. 텍스트 없으면 0.

    # Color (15차원)
    dominant_color_1: tuple[float, float, float]  # RGB 각각 0~1로 정규화
    dominant_color_2: tuple[float, float, float]
    dominant_color_3: tuple[float, float, float]
    background_color: tuple[float, float, float]
    color_variance: float
    saturation_mean: float
    brightness_mean: float

    # Layout (11차원)
    text_area_ratio: float
    image_area_ratio: float
    whitespace_ratio: float
    alignment_left_ratio: float
    alignment_center_ratio: float
    alignment_right_ratio: float
    margin_top: float
    margin_bottom: float
    margin_left: float
    margin_right: float
    element_count: float                # 정규화 (요소 수 / 20, clip at 1.0)

    # Content Density (4차원)
    word_count_normalized: float        # 단어 수 / 100, clip at 1.0
    bullet_count_normalized: float      # 불릿 수 / 20, clip at 1.0
    text_image_ratio: float             # 텍스트 면적 / (텍스트+이미지 면적), 0이면 0
    sentence_count_normalized: float    # 문장 수 / 30, clip at 1.0

    def to_numpy(self) -> np.ndarray:
        """모든 수치 feature를 1D numpy 배열로 직렬화한다."""
        ...
```

### 구현할 클래스

```python
class SlideFeatureExtractor:
    KNOWN_FONTS = [
        "Pretendard", "Noto Sans KR", "Malgun Gothic", "나눔고딕",
        "Arial", "Helvetica", "Times New Roman", "Georgia",
        "Calibri", "Cambria", "Verdana", "Tahoma",
        "Apple SD Gothic Neo", "Spoqa Han Sans", "Source Han Sans",
        "Roboto", "Open Sans", "Lato", "Montserrat",
    ]  # 길이 19 고정 (index 0~18). 이 목록에 없는 폰트는 index 19 = "Other" 슬롯에 집계.

    def extract(self, slide: SlideRaw) -> SlideFeatureVector:
        """단일 SlideRaw → SlideFeatureVector 변환."""
        ...

    def extract_all(self, slides: list[SlideRaw]) -> list[SlideFeatureVector]:
        """슬라이드 목록 전체 변환."""
        return [self.extract(s) for s in slides]
```

### 각 feature 계산 상세

**Typography**:
- `dominant_font_one_hot`: `TextElement` 전체에서 각 폰트 등장 횟수를 세어 `KNOWN_FONTS` 인덱스 기준으로 원-핫을 만든다. 텍스트가 없으면 모두 0.
- `font_size_*`: `TextElement.font_size` (pt) 의 기술통계를 계산한 뒤 `/ 72` 로 정규화한다. 텍스트가 없으면 모두 0. (pt/72 정규화는 다른 0~1 feature와 스케일을 맞추기 위함)
- `line_spacing_normalized`: `run.paragraph.line_spacing` 평균을 `/ 2.0`으로 정규화. `None`이면 1.0(기본값)으로 처리.
- `bold_ratio` / `italic_ratio`: `is_bold` / `is_italic` 인 `TextElement` 수 / 전체 `TextElement` 수.

**Color**:
- `dominant_color_1~3`: `TextElement.color_rgb` 중 가장 빈도 높은 3가지 색상. `(R,G,B)` 를 각각 `/ 255` 로 정규화. 색상이 2개 미만이면 남은 슬롯은 `(0,0,0)`.
- `background_color`: `SlideRaw.background_color_rgb` 를 `/ 255` 정규화.
- `color_variance`: 모든 `dominant_color` RGB 값의 분산.
- `saturation_mean` / `brightness_mean`: dominant_color들을 HSV로 변환하여 S, V 평균.

**Layout**:
- `text_area_ratio`: 모든 `TextElement` 의 `width × height` 합 / 1.0 (이미 정규화된 좌표이므로 합산).
- `image_area_ratio`: 모든 `ImageElement` 의 `width × height` 합.
- `whitespace_ratio`: `1 - text_area_ratio - image_area_ratio`, clip at 0.
- `alignment_*_ratio`: `TextElement.alignment` 분포.
- `margin_*`: 텍스트/이미지 요소 중 각 방향 최소 위치값 (top: min(y), left: min(x), bottom: min(1 - y - height), right: min(1 - x - width)).

**Content Density**:
- `word_count_normalized`: 모든 `TextElement.text` 를 합쳐 공백 분리 단어 수 / 100.
- `bullet_count_normalized`: `text.strip().startswith(("-", "•", "·", "*"))` 인 줄 수 / 20.
- `sentence_count_normalized`: `text` 에서 `[.!?]` 기준 문장 수 / 30.

### 테스트

`backend/tests/test_extractor.py` 를 작성하라.

검증해야 할 것:
- `to_numpy()` 출력이 항상 59차원 1D 배열인가
- 모든 값이 `NaN` 없이 유한한 float인가
- 빈 슬라이드(텍스트/이미지 없음) 입력 시 예외 없이 동작하는가

## Acceptance Criteria

```bash
cd backend && python -m pytest tests/test_extractor.py -v
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. `to_numpy()` 출력이 59차원인지 assert로 확인한다.
3. `phases/0-mvp/index.json` 의 step 2 를 업데이트한다.

## 금지사항

- `to_numpy()` 출력 차원을 임의로 바꾸지 마라. 이후 detector, scorer가 이 59차원에 의존한다.
- CLIP 등 딥러닝 임베딩을 이 step에서 추가하지 마라. Visual embedding은 MVP 이후 단계다.
- `SlideFeatureVector` 에 Pydantic을 사용하지 마라. 파이프라인 내부 구조체는 순수 dataclass다.
