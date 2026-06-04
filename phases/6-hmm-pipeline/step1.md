# Step 1: hmm-scorer

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트 구조와 이전 step 산출물을 파악하라:

- `/docs/ARCHITECTURE.md`
- `/docs/ADR.md`
- `/backend/app/core/config.py` (step 0에서 MODELS_DIR 추가됨)
- `/backend/app/pipeline/detector.py` (기존 IsolationForest 탐지 모듈 — 참고용)
- `/backend/tests/test_detector.py` (기존 테스트 스타일 참고)

## 작업

TDD 순서로 진행하라: 테스트 먼저 작성 → 구현.

### 1. `backend/tests/test_hmm_scorer.py` (테스트 먼저)

아래 케이스를 모두 커버하는 테스트를 작성하라:

- `score_sequence([])` → `0.5` 반환
- `score_sequence([0, 1, 2, 3])` → `0.5` 반환 (시퀀스 길이 < 5)
- 반환값이 항상 `0.0 <= score <= 1.0` 범위 내
- LL이 mean과 같을 때 score ≈ 0.0 (정상)
- LL이 mean보다 훨씬 낮을 때 (z >= 3) score = 1.0 (이상)
- 이상 시퀀스 score > 정상 시퀀스 score
- std=0일 때 ZeroDivisionError 없이 동작
- `load()`: 모델 파일 없으면 `None` 반환
- `load()`: pkl만 있고 json 없으면 `None` 반환
- `load()`: 손상된 pkl이면 `None` 반환
- `load()`: 두 파일 모두 정상이면 `HMMScorer` 인스턴스 반환

테스트에서 HMM 모델은 `unittest.mock.MagicMock`으로 대체하라.  
`load()` 테스트에서 `MODELS_DIR`은 `unittest.mock.patch`로 `tmp_path`로 교체하라.

### 2. `backend/app/pipeline/hmm_scorer.py` (구현)

```python
class HMMScorer:
    def __init__(self, model, thresholds: dict) -> None: ...

    def score_sequence(self, role_sequence: list[int]) -> float:
        """역할 시퀀스 → 이상 점수 (0~1, 높을수록 이상).
        시퀀스 길이 < 5이면 0.5 반환 (NB05 기준).
        공식: seq = np.array(role_sequence).reshape(-1, 1)  # CategoricalHMM 입력 형식
              ll  = model.score(seq) / len(seq)
              z   = (mean - ll) / (std + 1e-8)
              return clip(z / 3.0, 0.0, 1.0)
        """
        ...

    @classmethod
    def load(cls) -> Optional["HMMScorer"]:
        """MODELS_DIR/hmm_model.pkl + hmm_thresholds.json 로드.
        파일 미존재 또는 로드 실패 시 None 반환 (예외 발생 금지).
        """
        ...
```

- `hmmlearn` import는 `load()` 내부에서 lazy하게 수행하지 않아도 된다. 파일 존재 여부를 먼저 확인하므로 import 실패는 `load()` 의 try/except가 처리한다.
- `MODELS_DIR`은 `app.core.config`에서 import한다.
- 실제 `hmm_thresholds.json` 구조: `{"mean": float, "std": float, "threshold_primary": float, ...}`. 코드는 `thresholds["mean"]`과 `thresholds["std"]` 두 키만 사용한다.

## Acceptance Criteria

```bash
cd backend
pytest tests/test_hmm_scorer.py -v
pytest tests/ -q
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 기존 테스트가 모두 통과하는지 확인한다.
3. 결과에 따라 `phases/6-hmm-pipeline/index.json`의 step 1을 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "HMMScorer 구현: score_sequence(role_sequence) → 0~1, load() → None(모델 없음) or HMMScorer"`
   - 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- `score_sequence()` 내부에서 예외를 raise하지 마라. 잘못된 입력(빈 시퀀스 등)은 0.5를 반환한다.
- `load()` 내부에서 예외를 밖으로 전파하지 마라. 모든 예외는 try/except로 잡고 None을 반환한다.
- `backend/app/api/` 모듈을 import하지 마라. pipeline 모듈은 api에 의존하면 안 된다.
