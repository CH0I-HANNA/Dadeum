# Step 3: scorer

## 읽어야 할 파일

- `backend/app/pipeline/extractor.py` (SlideFeatureVector 구조 확인)
- `backend/app/models/schemas.py` (ConsistencyScore 스키마 확인)

## 작업

`backend/app/pipeline/scorer.py` 를 구현하라.

이 모듈의 역할: 전체 슬라이드의 `SlideFeatureVector` 목록을 받아 디자인 일관성 점수(`ConsistencyScore`)를 산출한다.

### 점수 산출 공식

ARCHITECTURE.md에 정의된 공식을 그대로 구현한다:

```
cohesion(group) = 1 / (1 + CV)
  where CV = std(group_features) / (mean(group_features) + ε)
  ε = 1e-8  (0 나누기 방지)

ConsistencyScore.total = 100 × (
    cohesion(typography) × 0.30 +
    cohesion(color)      × 0.30 +
    cohesion(layout)     × 0.25 +
    cohesion(content)    × 0.15
)
```

각 그룹의 `cohesion` 은 그룹에 속하는 모든 feature 차원의 CV를 평균내어 계산한다.

### feature 그룹 분류

`SlideFeatureVector.to_numpy()` 의 59차원을 아래와 같이 분류한다:

- `typography`: index 0~28 (29차원)
- `color`: index 29~43 (15차원)
- `layout`: index 44~54 (11차원)
- `content`: index 55~58 (4차원)

### 구현할 함수

```python
def compute_consistency_score(
    feature_vectors: list[SlideFeatureVector],
) -> ConsistencyScore:
    """
    슬라이드 전체의 feature vector를 받아 일관성 점수를 반환한다.
    슬라이드가 1장이면 total=100, sub_scores 모두 100을 반환한다.
    """
    ...
```

반환 타입은 `backend/app/models/schemas.py` 의 `ConsistencyScore` Pydantic 모델을 사용한다.

### 테스트

`backend/tests/test_scorer.py` 를 작성하라.

검증해야 할 것:
- 완전히 동일한 feature vector N개 입력 → total이 100에 가까운가 (≥ 95)
- 극단적으로 다른 feature vector 입력 → total이 낮은가 (≤ 50)
- 슬라이드 1장 입력 → total == 100 인가
- 반환값의 모든 점수가 0~100 범위인가

## Acceptance Criteria

```bash
cd backend && python -m pytest tests/test_scorer.py -v
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. `phases/0-mvp/index.json` 의 step 3 을 업데이트한다.

## 금지사항

- 점수를 임의로 클리핑하거나 스케일링하지 마라. 공식이 이미 0~100 범위를 보장한다.
- sub_scores 계산 시 `total` 공식과 다른 가중치를 사용하지 마라.
