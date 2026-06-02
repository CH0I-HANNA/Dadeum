# Step 1: backend-algorithm

## 읽어야 할 파일

먼저 아래 파일들을 읽고 설계 의도를 파악하라:

- `/docs/ARCHITECTURE.md` (Outlier Detection 모델 전략, contamination 선택 근거)
- `/docs/ADR.md` (ADR-002: contamination=0.2 근거)
- `/backend/app/pipeline/detector.py`
- `/backend/app/pipeline/explainer.py`
- `/backend/tests/test_detector.py`
- `/backend/tests/test_explainer.py`
- `phases/1-ux-improvements/index.json` (이전 step summary 확인)

이전 step에서 생성/수정된 파일:
- `/backend/app/models/schemas.py` (SlideStats 추가됨)
- `/backend/app/services/analysis_service.py` (slide_stats 포함됨)

## 작업

### 1. `backend/app/pipeline/detector.py` — 동적 contamination

현재 `OutlierDetector.__init__`는 `contamination=0.2`로 고정되어 있다. 슬라이드 수가 적을 때 오탐을 줄이고 많을 때 적절히 탐지하기 위해 슬라이드 수 기반 동적 조정을 도입한다.

`fit_predict()` 메서드에서 `feature_vectors`의 길이를 보고 contamination을 결정한다:
- 3~5장: 0.15
- 6~15장: 0.20 (기존 기본값)
- 16장 이상: 0.25

`OutlierDetector.__init__`의 `contamination` 파라미터는 `None`을 기본값으로 변경하고, `None`이면 동적 계산, 값이 있으면 그 값을 사용한다 (테스트 주입용).

시그니처:
```python
class OutlierDetector:
    def __init__(self, contamination: float | None = None) -> None: ...
    def fit_predict(self, feature_vectors: list[SlideFeatureVector]) -> list[OutlierResult]: ...
```

### 2. `backend/app/pipeline/explainer.py` — 최대 근거 수 5개로 확장

현재 `explain()` 메서드는 최대 3개의 `RootCause`를 반환한다. 5개로 늘린다.

`explain()` 내부에서 `return sorted_causes[:3]`를 `return sorted_causes[:5]`로 변경한다.

### 3. 테스트 업데이트

`tests/test_detector.py`:
- 3장 슬라이드로 contamination=0.15가 적용되는지 확인 (IsolationForest에 0.15가 전달되는지 mock 또는 슬라이드 수를 통해 간접 확인)
- 16장 이상에서 contamination=0.25가 사용되는지 확인

`tests/test_explainer.py`:
- 근거가 5개까지 반환될 수 있는지 확인 (충분한 그룹 수로 테스트)

## Acceptance Criteria

```bash
cd backend && pytest tests/ -q
```

에러 없이 통과해야 한다.

## 검증 절차

1. AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - `OutlierDetector` 인터페이스가 변경되어도 `analysis_service.py`가 `OutlierDetector()`로 기본 호출하면 동적 contamination이 적용되는가?
   - CLAUDE.md CRITICAL 규칙 위반 없는가?
3. `phases/1-ux-improvements/index.json` step 1을 업데이트한다.

## 금지사항

- `analysis_service.py`를 수정하지 마라. 이유: `OutlierDetector()`를 인자 없이 호출하는 기존 코드가 자동으로 동적 contamination을 사용해야 한다.
- contamination 동적 계산 로직을 `analysis_service.py`에 넣지 마라. 이유: 모델 내부 로직은 pipeline 모듈에서만 처리한다.
- 기존 테스트를 깨뜨리지 마라.
