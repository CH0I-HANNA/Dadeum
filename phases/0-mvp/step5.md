# Step 5: explainer

## 읽어야 할 파일

- `backend/app/pipeline/extractor.py` (SlideFeatureVector, KNOWN_FONTS 확인)
- `backend/app/pipeline/detector.py` (OutlierResult 구조 확인)
- `backend/app/models/schemas.py` (RootCause 스키마 확인)

## 작업

`backend/app/pipeline/explainer.py` 를 구현하라.

이 모듈의 역할: 이상치로 탐지된 슬라이드가 **왜** 이상한지 설명한다. 전체 슬라이드의 기준값(중앙값)과 해당 슬라이드의 값을 비교하여 가장 차이가 큰 feature 그룹과 구체적인 원인을 반환한다.

### 구현할 클래스

```python
class Explainer:
    def explain(
        self,
        outlier: OutlierResult,
        all_vectors: list[SlideFeatureVector],
    ) -> list[RootCause]:
        """
        이상 슬라이드 1개에 대해 원인 RootCause 목록을 반환한다.
        최대 3개까지 반환하며, similarity_score가 낮은 순으로 정렬한다.
        """
        ...

    def explain_all(
        self,
        outliers: list[OutlierResult],
        all_vectors: list[SlideFeatureVector],
    ) -> dict[int, list[RootCause]]:
        """slide_index → RootCause 목록 매핑을 반환한다."""
        ...
```

### 원인 분석 로직

각 feature 그룹(typography, color, layout, content)별로 아래를 수행한다:

1. **기준값 계산**: 전체 슬라이드 feature vector에서 해당 그룹 차원의 중앙값(median)을 구한다.
2. **유사도 계산**: 이상 슬라이드의 해당 그룹 벡터와 기준값 벡터 간 코사인 유사도를 계산한다.
3. `similarity_score` 가 낮은 그룹(= 전체와 다른 그룹)을 원인으로 판단한다.

### RootCause 레이블 생성 규칙

`RootCause.label`, `expected_value`, `actual_value` 는 아래 규칙으로 생성한다:

**Typography 그룹이 원인인 경우**:
- 가장 차이가 큰 feature를 찾는다 (font_size_mean vs 기준, dominant_font_one_hot 차이 등).
- `dominant_font_one_hot` 차이가 가장 크면: `label="폰트 불일치"`, `expected_value=가장_많이_쓰인_폰트명`, `actual_value=이_슬라이드에서_가장_많이_쓰인_폰트명`
- `font_size_mean` 차이가 가장 크면: `label="폰트 크기 불일치"`, `expected_value=f"{기준_크기:.0f}pt"`, `actual_value=f"{실제_크기:.0f}pt"`

**Color 그룹이 원인인 경우**:
- `label="색상 불일치"`, `expected_value=f"RGB{기준_dominant_color_1}"`, `actual_value=f"RGB{실제_dominant_color_1}"`

**Layout 그룹이 원인인 경우**:
- `label="레이아웃 불일치"`, `expected_value=f"텍스트 비율 {기준:.0%}"`, `actual_value=f"텍스트 비율 {실제:.0%}"`

**Content 그룹이 원인인 경우**:
- `word_count_normalized` 가 기준의 2배 이상이면: `label="과도한 텍스트 밀도"`
- 그 외: `label="콘텐츠 밀도 불일치"`

### 테스트

`backend/tests/test_explainer.py` 를 작성하라.

검증해야 할 것:
- 폰트만 다른 슬라이드가 입력되면 typography 그룹이 첫 번째 원인으로 반환되는가
- `RootCause` 목록이 최대 3개인가
- `similarity_score` 가 0~1 범위인가

## Acceptance Criteria

```bash
cd backend && python -m pytest tests/test_explainer.py -v
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. `phases/0-mvp/index.json` 의 step 5 를 업데이트한다.

## 금지사항

- LLM API를 호출하지 마라. 모든 설명은 규칙 기반으로 생성한다.
- `is_outlier == False` 인 슬라이드에 대해 `explain` 을 호출해도 빈 리스트를 반환하라. 예외를 발생시키지 마라.
