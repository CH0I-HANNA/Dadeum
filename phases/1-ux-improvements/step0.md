# Step 0: backend-slide-stats

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트의 아키텍처와 설계 의도를 파악하라:

- `/docs/ARCHITECTURE.md`
- `/docs/ADR.md`
- `/backend/app/models/schemas.py`
- `/backend/app/pipeline/extractor.py` (SlideFeatureVector 구조, to_numpy() 인덱스 매핑)
- `/backend/app/services/analysis_service.py`
- `/backend/tests/` (기존 테스트 패턴 파악)

## 작업

비아웃라이어 슬라이드를 선택했을 때 프론트엔드에서 해당 슬라이드의 실제 분석 수치를 보여주려면, 백엔드가 모든 슬라이드의 핵심 지표를 `AnalysisResult`에 포함해야 한다.

### 1. `backend/app/models/schemas.py` — `SlideStats` 모델 추가

`AnalysisResult` 위에 아래 모델을 추가한다:

```python
class SlideStats(BaseModel):
    slide_index: int          # 0-based
    word_count: int           # 슬라이드 내 단어 수 (반올림한 정수)
    font_size_mean: float     # 평균 폰트 크기 (pt 단위, 정규화 전 원본값)
    text_area_ratio: float    # 텍스트 영역 비율 0~1
    element_count: int        # 텍스트+이미지 요소 수
    dominant_font: str        # 가장 빈도 높은 폰트 이름 ("없음"이면 "-")
```

`AnalysisResult`에 필드 추가:
```python
class AnalysisResult(BaseModel):
    ...
    slide_stats: list[SlideStats] = []   # 모든 슬라이드 (outlier 포함)
```

### 2. `backend/app/services/analysis_service.py` — `slide_stats` 생성

`run_analysis()` 함수 내에서 `feature_vectors`와 `slides`(parser 결과)를 이용해 `SlideStats` 목록을 생성한 후 `AnalysisResult`에 포함한다.

핵심 규칙:
- `word_count`: `SlideRaw.text_elements`에서 모든 `text` 필드의 단어 수 합산 (`len(text.split())`)
- `font_size_mean`: `feature_vectors[i]`의 index 20 (font_size_mean)을 역정규화 — `round(fv.to_numpy()[20] * 72, 1)`. 텍스트 없으면 0.0
- `text_area_ratio`: `feature_vectors[i]`의 index 44 (text_area_ratio)
- `element_count`: `len(slides[i].text_elements) + len(slides[i].image_elements)`
- `dominant_font`: feature vector index 0~19 중 가장 값이 큰 index에 해당하는 폰트 이름. 모두 0이면 "-"

### 3. `backend/tests/test_analysis_service.py` (신규 또는 기존 테스트 파일에 추가)

아래 시나리오를 검증하는 테스트를 작성한다:
- `slide_stats`의 길이가 `slide_count`와 같은지
- `slide_stats[i].slide_index == i` 인지
- `font_size_mean`이 음수가 아닌지
- `element_count >= 0` 인지

## Acceptance Criteria

```bash
cd backend && pytest tests/ -q
```

에러 없이 통과해야 한다.

## 검증 절차

1. AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - `SlideStats`는 `backend/app/models/schemas.py`에만 정의되어 있는가?
   - `analysis_service.py`가 pipeline 모듈을 통해서만 데이터를 읽는가? (python-pptx 직접 임포트 금지)
   - CLAUDE.md CRITICAL 규칙 위반 없는가?
3. `phases/1-ux-improvements/index.json` step 0을 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "산출물 한 줄 요약"`
   - 3회 시도 후 실패 → `"status": "error"`, `"error_message": "구체적 에러"`

## 금지사항

- `analysis_service.py`에서 `python-pptx`를 직접 임포트하지 마라. 이유: CRITICAL 규칙 — Feature Extraction은 `extractor.py`의 `SlideFeatureExtractor`에서만 처리한다.
- `SlideStats`를 `analysis_service.py`나 다른 모듈에 중복 정의하지 마라. 이유: Pydantic 스키마는 `backend/app/models/`에만 정의한다.
- 기존 테스트를 깨뜨리지 마라.
