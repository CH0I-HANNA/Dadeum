# Step 5: analysis-service

## 읽어야 할 파일

먼저 아래 파일들을 전부 읽고 기존 파이프라인 흐름과 이전 step 산출물을 파악하라:

- `/docs/ARCHITECTURE.md`
- `/backend/app/services/analysis_service.py` (현재 구현)
- `/backend/app/pipeline/hmm_scorer.py` (step 1)
- `/backend/app/pipeline/role_classifier.py` (step 2)
- `/backend/app/pipeline/slide_renderer.py` (step 3)
- `/backend/app/models/schemas.py` (step 4 — role_sequence, hmm_anomaly_score 추가됨)
- `/backend/tests/test_api.py` (기존 API 테스트)

## 작업

`backend/app/services/analysis_service.py`의 `run_analysis()` 함수에 HMM 파이프라인을 통합하라.

### 추가할 import

`analysis_service.py` 상단에 아래 import를 추가하라:

```python
from app.pipeline.hmm_scorer import HMMScorer
from app.pipeline.role_classifier import RoleClassifier
from app.pipeline.slide_renderer import render_pptx_slides
```

### 통합 흐름

```
[기존 유지]
parse_file → SlideFeatureExtractor → ConsistencyScore
                                   → OutlierDetector → Explainer → Recommender

[신규 추가 — PPTX 전용, 모델 없으면 skip]
RoleClassifier.load()가 None이 아니면:
    render_pptx_slides(file_path) → images
    role_classifier.predict(images) → role_sequence
    SlideStats의 slide_role 필드 채움

HMMScorer.load()가 None이 아니고 role_sequence가 있으면:
    hmm_scorer.score_sequence(role_sequence) → hmm_anomaly_score
```

### 구체적 수정 사항

`run_analysis(file_path, file_id)` 함수:

1. 기존 파이프라인 코드를 그대로 유지한다.
2. 파이프라인 끝, `AnalysisResult` 생성 직전에 아래를 추가한다:

```python
role_sequence: list[int] | None = None
hmm_anomaly_score: float | None = None

# PPTX 파일에만 CNN+HMM 파이프라인 적용
if Path(file_path).suffix.lower() == ".pptx":
    role_classifier = RoleClassifier.load()
    if role_classifier is not None:
        images = render_pptx_slides(Path(file_path))
        role_sequence = role_classifier.predict(images)

    hmm_scorer = HMMScorer.load()
    if hmm_scorer is not None and role_sequence:
        hmm_anomaly_score = hmm_scorer.score_sequence(role_sequence)
```

3. `slide_stats` 생성 루프에서 `slide_role` 필드를 채운다:
```python
slide_role = role_sequence[i] if role_sequence and i < len(role_sequence) else None
```

4. `AnalysisResult` 생성 시 `role_sequence`, `hmm_anomaly_score` 필드를 전달한다.

### Timeout 처리

기존 `_TIMEOUT_SECONDS = 120`을 `180`으로 늘려라.  
CNN 추론이 CPU에서 30~60초 소요될 수 있기 때문이다.

## Acceptance Criteria

```bash
cd backend
pytest tests/ -q
uvicorn app.main:app --reload &
sleep 3
# 샘플 PPTX 업로드 후 분석 결과에 role_sequence 또는 hmm_anomaly_score 필드 확인
# (모델 파일 없으면 null이어야 함)
```

```bash
cd backend
pytest tests/test_api.py -v
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 기존 테스트 124개 + 신규 테스트가 모두 통과하는지 확인한다.
3. 모델 파일이 있을 때와 없을 때 모두 `run_analysis()`가 정상 동작하는지 확인한다:
   - 모델 없음: `role_sequence=None`, `hmm_anomaly_score=None`
   - 모델 있음: `role_sequence=[0~4 정수 리스트]`, `hmm_anomaly_score=[0.0~1.0]`
4. 결과에 따라 `phases/6-hmm-pipeline/index.json`의 step 5를 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "run_analysis()에 CNN+HMM 파이프라인 통합. 모델 없으면 role_sequence/hmm_anomaly_score=None fallback. timeout 180초로 연장"`
   - 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- `run_analysis()` 내부에 CNN/HMM 모델 아키텍처 코드를 직접 작성하지 마라. 반드시 `RoleClassifier`, `HMMScorer` 클래스를 통해서만 호출한다.
- PDF 파일에는 CNN+HMM 파이프라인을 적용하지 마라. `slide_renderer.py`가 PPTX 전용이기 때문이다.
- `RoleClassifier.load()`, `HMMScorer.load()` 호출 결과가 `None`이어도 기존 IF 파이프라인은 반드시 실행되어야 한다. CNN+HMM은 추가적인 정보일 뿐, IF 탐지를 대체하지 않는다.
- `run_analysis_with_timeout()`의 함수 시그니처를 바꾸지 마라. `analyze.py`가 이 함수를 호출한다.
