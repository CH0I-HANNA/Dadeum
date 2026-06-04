# Step 0: config-models-dir

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트 구조를 파악하라:

- `/docs/ARCHITECTURE.md`
- `/docs/ADR.md`
- `/backend/app/core/config.py`
- `/backend/requirements.txt`

## 작업

### 1. `backend/app/core/config.py`

기존 상수 아래에 `MODELS_DIR` 경로 상수를 추가하라.

```python
MODELS_DIR = Path("models")
```

- `MODELS_DIR`은 `backend/` 디렉토리를 기준으로 상대 경로로 정의한다.
- `UPLOAD_DIR`와 동일한 방식으로 `Path` 타입으로 선언한다.
- `MODELS_DIR.mkdir()` 호출 금지 — 디렉토리는 이미 존재하며, 없을 경우 graceful fallback이 각 모듈에서 처리한다.

### 2. `backend/requirements.txt`

아래 ML 의존성을 파일 끝에 추가하라:

```
torch>=2.0.0
timm>=0.9.0
torchvision>=0.15.0
hmmlearn>=0.3.0
```

- 이 의존성들은 `backend/models/` 파일이 없을 경우 사용되지 않으므로 선택적으로 설치 가능하다.
- 버전 하한만 지정하고 상한을 강제하지 마라.

## Acceptance Criteria

```bash
cd backend
python -c "from app.core.config import MODELS_DIR; assert MODELS_DIR.name == 'models'; print('OK')"
pytest tests/ -q
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 기존 테스트 124개가 모두 통과하는지 확인한다.
3. 결과에 따라 `phases/6-hmm-pipeline/index.json`의 step 0을 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "MODELS_DIR=Path('models') 추가, requirements.txt ML deps 추가"`
   - 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- `config.py`에서 `MODELS_DIR.mkdir()`을 호출하지 마라. 디렉토리 생성은 각 모듈의 책임이 아니며, 이미 존재한다.
- 기존 상수(`UPLOAD_DIR`, `MAX_FILE_SIZE_MB` 등)를 수정하지 마라.
