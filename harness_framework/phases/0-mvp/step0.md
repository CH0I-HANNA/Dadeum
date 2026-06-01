# Step 0: project-setup

## 작업

현재 작업 디렉토리(`harness_framework/`)에 `frontend/`와 `backend/`를 직접 생성한다.

### 1. 루트 구조

```
./
├── frontend/
└── backend/
```

### 2. Frontend 초기화

`frontend/` 디렉토리에서 Vite + React + TypeScript 프로젝트를 생성하라.

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install react-router-dom @tanstack/react-query axios lucide-react
```

TailwindCSS 설정은 `frontend/tailwind.config.js` 에서 `content` 경로를 `["./index.html", "./src/**/*.{ts,tsx}"]` 로 지정한다.

`frontend/src/index.css` 에 Tailwind directives를 추가하고, 기본 배경색을 `#0a0a0a` 로 설정한다.

`frontend/src/` 아래 다음 빈 디렉토리를 생성하라:
- `pages/`
- `components/`
- `types/`
- `hooks/`
- `lib/`
- `services/`

`frontend/src/types/api.ts` 를 생성하고 아래 TypeScript 타입을 정의하라:

```typescript
export interface UploadResponse {
  file_id: string;
  slide_count: number;
  filename: string;
}

export interface AnalyzeResponse {
  task_id: string;
}

export interface TaskStatus {
  task_id: string;
  status: "pending" | "processing" | "completed" | "error";
  error_message?: string;
}

export interface ResultResponse extends TaskStatus {
  result?: AnalysisResult;
}

export interface SubScore {
  typography: number;
  color: number;
  layout: number;
  content: number;
}

export interface ConsistencyScore {
  total: number;
  sub_scores: SubScore;
}

export interface RootCause {
  feature_group: "typography" | "color" | "layout" | "content";
  label: string;           // 예: "폰트 불일치"
  expected_value: string;  // 예: "Pretendard"
  actual_value: string;    // 예: "Arial"
  similarity_score: number; // 0~1
}

export interface Recommendation {
  root_cause: RootCause;
  action: string;          // 예: "Arial → Pretendard 로 변경"
  impact_score_delta: number; // 수정 후 예상 점수 상승폭
}

export interface OutlierSlide {
  slide_index: number;     // 0-based
  anomaly_score: number;   // 높을수록 이상
  root_causes: RootCause[];
  recommendations: Recommendation[];
}

export interface AnalysisResult {
  file_id: string;
  slide_count: number;
  consistency_score: ConsistencyScore;
  outlier_slides: OutlierSlide[];
  impact_score_after_fix: number; // 모든 수정안 적용 시 예상 총점
}
```

### 3. Backend 초기화

`backend/` 디렉토리에서 Python 환경을 구성하라.

`backend/requirements.txt` 를 생성하라:

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
python-pptx>=0.6.23
pdfplumber>=0.11.0
scikit-learn>=1.4.0
numpy>=1.26.0
pillow>=10.0.0
python-multipart>=0.0.9
aiofiles>=23.0.0
```

`backend/` 아래 다음 구조를 생성하라 (각 디렉토리에 빈 `__init__.py` 포함):

```
backend/
├── requirements.txt
├── tests/
│   └── __init__.py
└── app/
    ├── __init__.py
    ├── main.py
    ├── api/
    │   └── __init__.py
    ├── core/
    │   ├── __init__.py
    │   ├── config.py
    │   └── exceptions.py
    ├── models/
    │   └── __init__.py
    ├── services/
    │   └── __init__.py
    └── pipeline/
        └── __init__.py
```

`backend/app/main.py` 는 FastAPI 앱을 생성하고 CORS를 허용(`localhost:5173`)하는 최소 구성만 포함한다. 라우터는 아직 연결하지 않는다.

`backend/app/core/config.py` 에 아래 설정을 정의하라:

```python
from pathlib import Path

UPLOAD_DIR = Path("tmp/uploads")
MAX_FILE_SIZE_MB = 50
MAX_SLIDES = 50
MIN_SLIDES = 3
DISK_FREE_THRESHOLD_MB = 500
```

`backend/app/core/exceptions.py` 에 파이프라인 예외 계층을 정의하라:

```python
class PipelineError(Exception):
    """파이프라인 처리 중 발생하는 모든 예외의 기반 클래스."""
    pass

class ParseError(PipelineError):
    """파일 파싱 실패 (손상, 암호화, 지원하지 않는 형식)."""
    pass

class InsufficientSlidesError(PipelineError):
    """슬라이드 수가 분석 최소 요건(MIN_SLIDES)을 충족하지 못할 때."""
    pass
```

`backend/app/models/schemas.py` 에 `frontend/src/types/api.ts` 와 1:1 대응하는 Pydantic 모델을 정의하라. 필드명과 타입은 TypeScript 타입과 동일하게 유지한다.

## Acceptance Criteria

```bash
# Frontend 빌드 확인
cd frontend && npm run build

# Backend 기동 확인
cd backend && python -c "from app.main import app; print('OK')"

# 예외 계층 임포트 확인
cd backend && python -c "from app.core.exceptions import PipelineError, ParseError, InsufficientSlidesError; print('OK')"
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. `frontend/src/types/api.ts` 와 `backend/app/models/schemas.py` 의 필드가 일치하는지 확인한다.
3. ARCHITECTURE.md 디렉토리 구조를 따르는지 확인한다.
4. 결과에 따라 `phases/0-mvp/index.json` 의 step 0 을 업데이트한다.

## 금지사항

- 실제 파이프라인 로직(파싱, 추출, 탐지)을 이 step에서 구현하지 마라. 구조와 타입 정의만 한다.
- `frontend/src/App.tsx` 에 라우팅 외의 비즈니스 로직을 넣지 마라.
- `backend/app/main.py` 에 라우터 연결 외의 로직을 작성하지 마라.
- `backend/app/core/exceptions.py` 에 예외 처리 로직을 추가하지 마라. 클래스 정의만 한다.
