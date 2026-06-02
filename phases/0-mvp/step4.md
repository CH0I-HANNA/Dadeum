# Step 4: outlier-detector

## 읽어야 할 파일

- `backend/app/pipeline/extractor.py` (SlideFeatureVector 구조 확인)
- `backend/app/models/schemas.py` (OutlierSlide 스키마 확인)

## 작업

`backend/app/pipeline/detector.py` 를 구현하라.

이 모듈의 역할: 전체 슬라이드의 feature vector를 받아 이상 슬라이드를 탐지하고 각 슬라이드의 anomaly score를 반환한다.

### 구현할 클래스

```python
class OutlierDetector:
    def __init__(self, contamination: float = 0.2):
        """
        contamination: 전체 슬라이드 중 이상치로 볼 비율.
        기본값 0.2 (20%). 슬라이드가 10장이면 최대 2장을 이상치로 탐지.
        """
        ...

    def fit_predict(
        self,
        feature_vectors: list[SlideFeatureVector],
    ) -> list[OutlierResult]:
        """
        Isolation Forest를 fit하고 각 슬라이드의 이상 여부와 anomaly score를 반환한다.
        슬라이드가 3장 미만이면 빈 리스트를 반환한다 (탐지 불가).
        """
        ...
```

### OutlierResult 내부 데이터 구조

```python
@dataclass
class OutlierResult:
    slide_index: int
    is_outlier: bool
    anomaly_score: float   # 0~1, 높을수록 이상. IsolationForest의 decision_function을 0~1로 정규화.
    feature_vector: SlideFeatureVector  # explainer에서 사용
```

`anomaly_score` 정규화: `sklearn` 의 `decision_function` 은 음수일수록 이상치다. 이를 `(score - min) / (max - min + ε)` 로 0~1 변환 후 반전(`1 - normalized`)하여 높을수록 이상치가 되도록 한다.

### Isolation Forest 설정

```python
IsolationForest(
    n_estimators=100,
    contamination=self.contamination,
    random_state=42,
)
```

### 테스트

`backend/tests/test_detector.py` 를 작성하라.

검증해야 할 것:
- 10개의 유사한 벡터 중 1개의 극단적으로 다른 벡터를 넣으면 그 슬라이드가 이상치로 탐지되는가
- `anomaly_score` 가 모두 0~1 범위인가
- 슬라이드 3장 미만 입력 시 빈 리스트를 반환하는가

## Acceptance Criteria

```bash
cd backend && python -m pytest tests/test_detector.py -v
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. `phases/0-mvp/index.json` 의 step 4 를 업데이트한다.

## 금지사항

- 이 step에서 AutoEncoder나 GNN을 구현하지 마라. Isolation Forest만 구현한다.
- `fit` 과 `predict` 를 분리하지 마라. `fit_predict` 를 단일 메서드로 유지한다 (매 요청마다 새로 fit하는 구조).
