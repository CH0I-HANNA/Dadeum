# Step 1: backend-pdf

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트의 아키텍처와 설계 의도를 파악하라:

- `/Users/choehanna/Documents/Dadeum/docs/ARCHITECTURE.md`
- `/Users/choehanna/Documents/Dadeum/docs/ADR.md`
- `/Users/choehanna/Documents/Dadeum/CLAUDE.md`
- `/Users/choehanna/Documents/Dadeum/backend/app/main.py`
- `/Users/choehanna/Documents/Dadeum/backend/app/core/task_store.py`  ← task 조회 API 파악 필수
- `/Users/choehanna/Documents/Dadeum/backend/app/models/schemas.py`
- `/Users/choehanna/Documents/Dadeum/backend/app/api/thumbnail.py`  ← 렌더링 함수 파악 필수
- `/Users/choehanna/Documents/Dadeum/backend/requirements.txt`

`task_store.py`를 읽고 task를 조회하는 함수 이름과 반환 타입을 파악한 뒤 사용하라.
`thumbnail.py`를 읽고 `_render_pptx_slide`, `_render_pdf_slide`, `_find_file_path` 함수의 시그니처를 파악하라.

## 작업

### 1. fpdf2 의존성 추가

`backend/requirements.txt`에 `fpdf2>=2.7.0` 를 추가한다 (파일 직접 편집).

```bash
cd /Users/choehanna/Documents/Dadeum/backend
pip install "fpdf2>=2.7.0"
```

반드시 requirements.txt 파일도 수정 완료 후 확인하라. `pip install`만으로는 파일이 자동 갱신되지 않는다.

### 2. PDF 보고서 생성 API (`backend/app/api/report.py` 신규)

`GET /api/report/{task_id}` 엔드포인트를 구현한다.

**응답**:
- 성공: `Content-Type: application/pdf`, `Content-Disposition: attachment; filename="dadeum-report-{task_id[:8]}.pdf"` 와 함께 PDF 바이너리
- 404: task_id 없음, 또는 status가 `"completed"`가 아님

**task 조회 패턴** (`task_store.py`를 읽고 실제 API에 맞게 사용):
```python
from app.core import task_store

task = task_store.get_task(task_id)   # 반환 타입: dict | None
if task is None or task["status"] != "completed":
    raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
result: AnalysisResult = task["result"]  # set_completed()에서 Pydantic 객체로 저장됨
```

**슬라이드 파일 경로 조회**:
```python
from app.api.thumbnail import _find_file_path
file_path = _find_file_path(result.file_id)
if file_path is None:
    raise HTTPException(status_code=404, detail="원본 파일을 찾을 수 없습니다.")
```

**PDF 내용 구성** (A4 세로, 흰 배경):

1. **헤더**: "다듬 분석 보고서" 제목 + `슬라이드 {result.slide_count}장`
2. **일관성 점수 섹션**: 전체 점수 + 폰트/색상/레이아웃/콘텐츠 세부 점수 (숫자 + 레이블)
3. **이상 슬라이드 섹션**:
   - 이상 슬라이드가 없으면 "이상 슬라이드가 없습니다" 표시
   - 이상 슬라이드마다: 슬라이드 번호 헤더 → 썸네일 이미지 → 원인 목록 → 수정 제안 목록

**썸네일 삽입 방법** (`thumbnail.py`의 함수를 직접 import):
```python
from app.api.thumbnail import _render_pptx_slide, _render_pdf_slide
import io

# PNG bytes 획득
if file_path.suffix == ".pdf":
    png_bytes = _render_pdf_slide(file_path, outlier.slide_index)
else:
    png_bytes = _render_pptx_slide(file_path, outlier.slide_index)

# fpdf2에 이미지 삽입 (BytesIO 사용)
pdf.image(io.BytesIO(png_bytes), w=160)  # 너비 160mm
```

**한글 폰트 처리**:

fpdf2는 기본적으로 Latin 문자만 지원한다. 한글 출력을 위해 시스템 폰트를 등록한다.
macOS에서 아래 경로를 순서대로 시도하고, 하나라도 존재하면 등록한다:

```python
import os

KOREAN_FONT_CANDIDATES = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/Library/Fonts/NanumGothic.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
]

korean_font_path = next((p for p in KOREAN_FONT_CANDIDATES if os.path.exists(p)), None)

if korean_font_path:
    pdf.add_font("Korean", fname=korean_font_path)  # fpdf2 2.7+: uni=True 제거됨
    pdf.set_font("Korean", size=10)
else:
    # 한글 폰트 없으면 영문 폰트로 fallback — 한글이 '?' 로 출력될 수 있음
    pdf.set_font("Helvetica", size=10)
```

`.ttc` 파일(TrueType Collection)은 fpdf2 2.7+에서 첫 번째 폰트 face가 자동 선택된다. `uni=True`는 fpdf2 2.7에서 제거됐으므로 사용하지 마라.

**PDF 반환**:
```python
from fastapi.responses import Response

pdf_bytes = bytes(pdf.output())  # fpdf2 반환값을 bytes로 변환
return Response(
    content=pdf_bytes,
    media_type="application/pdf",
    headers={"Content-Disposition": f'attachment; filename="dadeum-report-{task_id[:8]}.pdf"'},
)
```

### 3. main.py 라우터 등록

```python
from app.api import analyze, thumbnail, upload, report
app.include_router(report.router, prefix="/api")
```

## Acceptance Criteria

```bash
cd /Users/choehanna/Documents/Dadeum/backend
pytest tests/ -q    # 기존 테스트 전부 통과
python -c "from app.api import report; print('import OK')"  # import 에러 없음
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - Pydantic 스키마가 `backend/app/models/schemas.py`에만 정의되어 있는가?
   - AI 추론 로직이 `backend/app/pipeline/`에만 있는가?
   - CLAUDE.md CRITICAL 규칙을 위반하지 않았는가?
3. 결과에 따라 `phases/3-new-features/index.json`의 step 1을 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "산출물 한 줄 요약"`
   - 수정 3회 시도 후에도 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- `_render_pptx_slide`, `_render_pdf_slide` 로직을 `report.py`에 복사하지 마라. 반드시 `thumbnail.py`에서 import하여 재사용하라. 이유: 중복 구현은 향후 렌더러 개선 시 양쪽을 모두 수정해야 하는 부채가 된다.
- 썸네일을 HTTP 내부 요청(`requests.get(...)`)으로 가져오지 마라. 함수 직접 호출을 사용하라.
- 프론트엔드 파일을 수정하지 마라.
- 기존 테스트를 깨뜨리지 마라.
