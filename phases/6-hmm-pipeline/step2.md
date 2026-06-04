# Step 2: role-classifier

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트 구조와 이전 step 산출물을 파악하라:

- `/docs/ARCHITECTURE.md`
- `/backend/app/core/config.py` (MODELS_DIR)
- `/backend/app/pipeline/hmm_scorer.py` (step 1 — load() 패턴 참고)
- `/backend/tests/test_hmm_scorer.py` (테스트 스타일 참고)

## 배경 지식

`role_classifier_clip_best.pt`는 EfficientNet-B3 기반 CNN으로, CLIP zero-shot 라벨로 학습됐다.  
슬라이드 이미지(224×224)를 입력받아 5개 역할(0~4) 중 하나를 예측한다.

| 인덱스 | 역할 |
|--------|------|
| 0 | 표지 |
| 1 | 섹션헤더 |
| 2 | 본문 |
| 3 | 도표/시각자료 |
| 4 | 마무리 |

체크포인트 구조: `{"epoch": int, "model_state_dict": ..., "val_acc": float}`  
로드 시 `checkpoint["model_state_dict"]`만 사용하면 된다.

모델 아키텍처:
```python
class SlideRoleClassifier(nn.Module):
    backbone = timm.create_model('efficientnet_b3', pretrained=False, num_classes=0, global_pool='avg')
    classifier = Sequential(Dropout(0.3), Linear(1536, 256), ReLU(), Dropout(0.15), Linear(256, 5))
```

## 작업

TDD 순서로 진행하라: 테스트 먼저 작성 → 구현.

### 1. `backend/tests/test_role_classifier.py` (테스트 먼저)

아래 케이스를 커버하라:

- `load()`: 체크포인트 파일 없으면 `None` 반환
- `load()`: 손상된 파일이면 `None` 반환 (예외 전파 금지)
- `predict([])`: 빈 리스트 → 빈 리스트 반환
- `predict(images)`: 반환값 길이 == 입력 이미지 수
- `predict(images)`: 각 예측값이 0 이상 4 이하의 정수
- `predict(images)`: PIL Image 리스트를 입력받아 정상 동작

`torch`/`timm` 설치 여부에 관계없이 `load()` 반환값이 `None`이거나 `RoleClassifier` 인스턴스임을 검증하라.  
실제 모델 추론 테스트는 `unittest.mock`으로 모델을 mock하라.

### 2. `backend/app/pipeline/role_classifier.py` (구현)

```python
_IMG_SIZE = 224
_ROLE_NAMES = ["표지", "섹션헤더", "본문", "도표/시각자료", "마무리"]

class RoleClassifier:
    def __init__(self, model, device) -> None: ...

    def predict(self, images: list[Image.Image]) -> list[int]:
        """PIL 이미지 리스트 → 역할 인덱스 리스트 (0~4).
        빈 리스트 입력 시 빈 리스트 반환.
        배치 크기: 32.
        전처리: Resize(224,224) → ToTensor → Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])
        """
        ...

    @classmethod
    def load(cls) -> Optional["RoleClassifier"]:
        """MODELS_DIR/role_classifier_clip_best.pt 로드.
        파일 미존재, torch/timm 미설치, 로드 실패 시 None 반환 (예외 발생 금지).
        """
        ...
```

- `torch`, `timm` import는 `load()` 내부에서 수행하라. 미설치 시 `ImportError`를 try/except로 잡아 `None` 반환한다.
- `MODELS_DIR`은 `app.core.config`에서 import한다.
- `model.eval()`과 `torch.no_grad()`를 반드시 사용하라.

## Acceptance Criteria

```bash
cd backend
pytest tests/test_role_classifier.py -v
pytest tests/ -q
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 기존 테스트가 모두 통과하는지 확인한다.
3. 결과에 따라 `phases/6-hmm-pipeline/index.json`의 step 2를 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "RoleClassifier 구현: predict(PIL_images) → list[int 0~4], load() → None or RoleClassifier"`
   - 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- `load()` 밖에서 `import torch` / `import timm`을 모듈 최상단에 두지 마라. 미설치 환경에서 서버 시작이 실패한다.
- `backend/app/api/` 모듈을 import하지 마라.
- `model.train()` 호출 금지 — 추론 전용이므로 항상 `eval()` 모드여야 한다.
