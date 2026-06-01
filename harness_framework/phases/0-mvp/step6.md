# Step 6: recommender

## 읽어야 할 파일

- `backend/app/pipeline/explainer.py` (RootCause 생성 방식 확인)
- `backend/app/pipeline/scorer.py` (ConsistencyScore 공식 확인)
- `backend/app/models/schemas.py` (Recommendation 스키마 확인)

## 작업

`backend/app/pipeline/recommender.py` 를 구현하라.

이 모듈의 역할: `RootCause` 를 받아 구체적인 수정안(`Recommendation`)과 수정 후 예상 점수 상승폭(`impact_score_delta`)을 반환한다.

### 구현할 클래스

```python
class Recommender:
    def recommend(
        self,
        root_cause: RootCause,
        slide_index: int,
        all_vectors: list[SlideFeatureVector],
    ) -> Recommendation:
        """단일 RootCause에 대한 수정안을 반환한다."""
        ...

    def recommend_all(
        self,
        root_causes_by_slide: dict[int, list[RootCause]],
        all_vectors: list[SlideFeatureVector],
    ) -> dict[int, list[Recommendation]]:
        """slide_index → Recommendation 목록 매핑을 반환한다."""
        ...

    def estimate_impact_score(
        self,
        all_vectors: list[SlideFeatureVector],
        recommendations_by_slide: dict[int, list[Recommendation]],
    ) -> float:
        """
        모든 수정안이 적용된다고 가정했을 때 예상 ConsistencyScore.total을 반환한다.
        실제로 벡터를 수정하는 것이 아니라 점수 상승폭의 합산 추정치를 현재 점수에 더한다.
        결과는 100을 초과하지 않도록 clip한다.
        """
        ...
```

### action 문구 생성 규칙

`Recommendation.action` 은 `RootCause.label` 에 따라 아래 템플릿으로 생성한다:

- `"폰트 불일치"` → `f"{actual_value} → {expected_value} 로 변경 권장"`
- `"폰트 크기 불일치"` → `f"폰트 크기 {actual_value} → {expected_value} 로 조정 권장"`
- `"색상 불일치"` → `f"주 색상을 전체 기준 색상 {expected_value} 에 맞게 조정 권장"`
- `"레이아웃 불일치"` → `f"텍스트 영역 비율을 {expected_value} 에 맞게 조정 권장"`
- `"과도한 텍스트 밀도"` → `"텍스트 양을 줄이거나 슬라이드를 분리 권장"`
- 그 외 → `f"{label} 수정 권장"`

### impact_score_delta 계산

`RootCause.similarity_score` 를 기반으로 추정한다:

```python
# 유사도가 낮을수록 개선 여지가 크다
improvement_potential = 1 - root_cause.similarity_score
group_weight = {"typography": 0.30, "color": 0.30, "layout": 0.25, "content": 0.15}
impact_score_delta = improvement_potential * group_weight[root_cause.feature_group] * 100 * 0.5
# × 0.5: 수정이 완벽하게 적용된다고 가정해도 절반 효과를 보수적으로 추정
```

### 테스트

`backend/tests/test_recommender.py` 를 작성하라.

검증해야 할 것:
- `action` 문구가 비어있지 않은가
- `impact_score_delta` 가 0 이상인가
- `estimate_impact_score` 반환값이 0~100 범위인가

## Acceptance Criteria

```bash
cd backend && python -m pytest tests/test_recommender.py -v
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. `phases/0-mvp/index.json` 의 step 6 을 업데이트한다.

## 금지사항

- 실제로 PPTX 파일을 수정하거나 새 파일을 생성하지 마라. 이 단계는 텍스트 수정안 생성까지만 담당한다.
- `estimate_impact_score` 에서 feature vector를 직접 수정하지 마라. 점수 상승폭 추정은 수식 기반으로만 한다.
