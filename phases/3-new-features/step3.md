# Step 3: backend-fix-preview

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트의 아키텍처와 설계 의도를 파악하라:

- `/Users/choehanna/Documents/Dadeum/docs/ARCHITECTURE.md`
- `/Users/choehanna/Documents/Dadeum/docs/ADR.md`
- `/Users/choehanna/Documents/Dadeum/CLAUDE.md`
- `/Users/choehanna/Documents/Dadeum/backend/app/main.py`
- `/Users/choehanna/Documents/Dadeum/backend/app/core/task_store.py`  ← task 조회 API 파악 필수
- `/Users/choehanna/Documents/Dadeum/backend/app/models/schemas.py`
- `/Users/choehanna/Documents/Dadeum/backend/app/api/thumbnail.py`  ← _render_pptx_slide 시그니처 파악 필수
- `/Users/choehanna/Documents/Dadeum/backend/app/api/report.py`  ← step 1에서 생성됨. _find_file_path 사용 패턴 참고

`task_store.py`를 읽고 task 조회 함수 이름과 반환 타입을 파악하라.

## 작업

`backend/app/api/fix.py` 를 새로 만들고 두 개의 엔드포인트를 구현한다.

---

### 엔드포인트 1: `POST /api/fix/{file_id}`

분석 결과의 수정 권장사항을 바탕으로 PPTX의 폰트와 색상을 통일하여 수정된 파일을 반환한다.

**Request Body** (`backend/app/models/schemas.py`에 추가):
```python
class FixRequest(BaseModel):
    task_id: str
```

**응답**:
- 성공: `Content-Type: application/vnd.openxmlformats-officedocument.presentationml.presentation`, `Content-Disposition: attachment; filename="dadeum-fixed-{file_id[:8]}.pptx"` 와 함께 PPTX 바이너리
- 404: file_id 없음, task status가 completed 아님, 또는 파일이 .pdf인 경우

**task 조회 패턴** (`task_store.get_task()`는 `dict | None` 반환 — 속성 접근 금지):
```python
from app.core import task_store
from app.models.schemas import FixRequest, AnalysisResult

task = task_store.get_task(task_body.task_id)  # dict | None
if task is None or task["status"] != "completed":
    raise HTTPException(status_code=404, ...)
result: AnalysisResult = task["result"]  # Pydantic 객체로 저장됨
```

**파일 경로 조회**:
```python
from app.api.thumbnail import _find_file_path
file_path = _find_file_path(file_id)
if file_path is None or file_path.suffix != ".pptx":
    raise HTTPException(status_code=404, detail="PPTX 파일만 수정 가능합니다.")
```

**수정 로직** (python-pptx 사용):

```python
import io
from pptx import Presentation
from pptx.dml.color import RGBColor
import re

prs = Presentation(str(file_path))

for outlier in result.outlier_slides:
    slide = prs.slides[outlier.slide_index]

    # 적용할 폰트명과 색상 추출
    target_font: str | None = None
    target_color: RGBColor | None = None

    for rc in outlier.root_causes:
        if rc.feature_group == "typography" and target_font is None:
            target_font = rc.expected_value  # 예: "Arial"
        if rc.feature_group == "color" and target_color is None:
            # expected_value 형식: "RGB(255, 128, 0)"
            m = re.search(r"RGB\((\d+),\s*(\d+),\s*(\d+)\)", rc.expected_value)
            if m:
                target_color = RGBColor(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # 해당 슬라이드의 모든 Run에 적용
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                if target_font:
                    run.font.name = target_font
                if target_color:
                    run.font.color.rgb = target_color

# 메모리 내 저장 후 반환 (원본 파일 절대 수정 금지)
buf = io.BytesIO()
prs.save(buf)
pptx_bytes = buf.getvalue()
```

---

### 엔드포인트 2: `GET /api/preview-fix/{file_id}/{slide_num}?task_id={task_id}`

특정 슬라이드에 수정을 적용한 후 PNG 썸네일을 반환한다.

**응답**:
- 성공: PNG 바이너리 (`Content-Type: image/png`)
- 404: 파일 없음, task 없음, 해당 슬라이드가 outlier 아님, 또는 PDF 파일인 경우

**구현**:

`task_id` 쿼리 파라미터로 task를 조회할 때도 dict 접근을 사용한다:
```python
task = task_store.get_task(task_id)
if task is None or task["status"] != "completed":
    raise HTTPException(status_code=404, ...)
result: AnalysisResult = task["result"]
```

`_render_pptx_slide(file_path, slide_num)`은 `Path`를 받아 디스크에서 다시 로드한다.
수정된 슬라이드를 렌더링하려면 수정된 Presentation을 임시 파일로 저장한 뒤 렌더링해야 한다:

```python
import tempfile, os
from pathlib import Path
from app.api.thumbnail import _render_pptx_slide

# 1. 수정 적용 (엔드포인트 1의 수정 로직을 해당 slide_num 슬라이드에만 적용)
prs = Presentation(str(file_path))
slide = prs.slides[slide_num]
# ... (위 수정 로직 동일하게 해당 슬라이드에만 적용)

# 2. 임시 파일에 저장
with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    prs.save(str(tmp_path))

try:
    png_bytes = _render_pptx_slide(tmp_path, slide_num)
finally:
    os.unlink(tmp_path)  # 임시 파일 반드시 삭제

return Response(content=png_bytes, media_type="image/png")
```

**캐싱 없음**: preview-fix 결과는 캐시하지 않는다.

---

### main.py 라우터 등록

```python
from app.api import analyze, thumbnail, upload, report, fix
app.include_router(fix.router, prefix="/api")
```

## Acceptance Criteria

```bash
cd /Users/choehanna/Documents/Dadeum/backend
pytest tests/ -q    # 기존 테스트 전부 통과
python -c "from app.api import fix; print('import OK')"   # import 에러 없음
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - `FixRequest` 스키마가 `backend/app/models/schemas.py`에만 정의되어 있는가?
   - CLAUDE.md CRITICAL 규칙을 위반하지 않았는가?
3. 결과에 따라 `phases/3-new-features/index.json`의 step 3을 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "산출물 한 줄 요약"`
   - 수정 3회 시도 후에도 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- 원본 업로드 파일(`UPLOAD_DIR` 내 파일)을 절대 수정하지 마라. 이유: 원본을 덮어쓰면 재분석 시 결과가 달라진다. `io.BytesIO` 또는 `tempfile`을 사용하여 메모리/임시 경로에서 작업하라.
- PDF 파일에 대한 fix/preview 기능을 구현하지 마라. python-pptx는 PDF를 수정할 수 없다. `file_path.suffix != ".pptx"`이면 404를 반환하라.
- 임시 파일(`tempfile.NamedTemporaryFile`)을 사용한 후 반드시 삭제하라. `try/finally`로 보장하라. 이유: 임시 파일이 누적되면 디스크가 가득 찬다.
- 프론트엔드 파일을 수정하지 마라.
- 기존 테스트를 깨뜨리지 마라.
