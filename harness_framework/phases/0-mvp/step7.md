# Step 7: api-layer

## 읽어야 할 파일

- `backend/app/models/schemas.py`
- `backend/app/core/exceptions.py`
- `backend/app/pipeline/` 디렉토리 전체 (parser, extractor, scorer, detector, explainer, recommender)

## 작업

FastAPI 라우터와 분석 서비스 레이어를 구현하라.

### 1. analysis_service.py

`backend/app/services/analysis_service.py` 를 구현하라. 파이프라인 모듈을 조합하여 전체 분석을 실행한다.

```python
def run_analysis(file_path: str | Path) -> AnalysisResult:
    """
    파이프라인 전체를 순서대로 실행하고 AnalysisResult를 반환한다.
    1. parse_file
    2. SlideFeatureExtractor.extract_all
    3. compute_consistency_score
    4. OutlierDetector.fit_predict
    5. Explainer.explain_all
    6. Recommender.recommend_all + estimate_impact_score
    """
    ...
```

### 2. task 상태 관리

`backend/app/core/task_store.py` 를 구현하라. SQLite 없이 인메모리 딕셔너리로 task 상태를 관리한다 (MVP 한정, ADR-009 참조).

```python
import threading

# BackgroundTasks는 스레드풀에서 실행되므로 동시 쓰기 방지를 위해 Lock 필수.
_lock = threading.Lock()
_tasks: dict[str, dict] = {}
_file_to_task: dict[str, str] = {}  # file_id → task_id (409 중복 탐지용)

def create_task(task_id: str, file_id: str) -> None: ...
def set_processing(task_id: str) -> None: ...
def set_completed(task_id: str, result: AnalysisResult) -> None: ...
def set_error(task_id: str, message: str) -> None: ...
def get_task(task_id: str) -> dict | None: ...
def get_task_id_by_file_id(file_id: str) -> str | None: ...
```

모든 함수는 `with _lock:` 블록 안에서 딕셔너리를 읽고 쓴다.

### 3. API 라우터

`backend/app/api/` 에 아래 라우터를 구현하고 `main.py` 에 연결하라.

**upload.py**:
```
POST /api/upload
  - 파일 수신 (multipart/form-data)
  - 확장자 검증: .pptx, .pdf 만 허용. 불일치 시 400
  - 파일 크기 검증: MAX_FILE_SIZE_MB 초과 시 413 (HTTP 413 Content Too Large)
  - 디스크 여유 공간 < DISK_FREE_THRESHOLD_MB 이면 503
  - `config.UPLOAD_DIR / f"{uuid4}{ext}"` 로 저장 (ext = `.pptx` 또는 `.pdf`). 확장자를 유지해야 parse_file이 타입을 판별할 수 있다. file_id = uuid4 (확장자 미포함 문자열).
  - 응답: UploadResponse { file_id, slide_count, filename }
  - slide_count는 파일 저장 후 parse_file을 호출하여 확인
```

**analyze.py**:
```
POST /api/analyze/{file_id}
  - UPLOAD_DIR에서 file_id 파일 존재 여부 확인, 없으면 404
  - task_store.get_task_id_by_file_id(file_id) 가 이미 존재하면 409 반환
  - task_id(uuid4) 생성, task_store.create_task(task_id, file_id) 로 등록
  - BackgroundTasks로 run_analysis_with_timeout 비동기 실행 (ADR-010 패턴)
  - 즉시 응답: AnalyzeResponse { task_id }

GET /api/result/{task_id}
  - task_store에서 상태 조회
  - status == "pending" | "processing" → TaskStatus만 반환 (result 없음)
  - status == "completed" → TaskStatus + AnalysisResult 반환
  - status == "error" → TaskStatus + error_message 반환
  - task_id 없으면 404
```

**thumbnail.py**:
```
GET /api/thumbnail/{file_id}/{slide_num}
  - PPTX는 python-pptx로 슬라이드를 렌더링하지 않는다 (ADR-008 참조).
  - file_id에 해당하는 파일을 parse_file로 파싱하고, slide_num 슬라이드의
    배경색·텍스트 박스·이미지 영역을 Pillow로 대체 렌더링하여 PNG로 반환한다.
  - 이미지 너비: 400px, 높이: round(400 × slide_height_emu / slide_width_emu)
    (원본 슬라이드 비율 유지. 16:9이면 400×225, 4:3이면 400×300)
  - 텍스트 박스: #9ca3af 직사각형. 이미지 영역: 대각선 사선 직사각형.
  - 결과는 메모리 캐시에 저장 (동일 file_id+slide_num 재요청 시 재파싱 생략).
  - Content-Type: image/png
```

### 테스트

`backend/tests/test_api.py` 를 작성하라. `TestClient` 를 사용한다.

검증해야 할 것:
- `.pptx` 파일 업로드 성공 시 200 + `file_id` 반환
- 잘못된 확장자 업로드 시 400 반환
- `analyze` 호출 후 `result` 폴링 시 completed 상태가 되는가 (동기 처리 테스트)

## Acceptance Criteria

```bash
cd backend && python -m pytest tests/test_api.py -v
cd backend && uvicorn app.main:app --reload &
sleep 3 && curl http://localhost:8000/docs | grep -q "openapi"
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. `http://localhost:8000/docs` 에서 3개 엔드포인트가 보이는지 확인한다.
3. `phases/0-mvp/index.json` 의 step 7 을 업데이트한다.

## 금지사항

- Celery, Redis 등 외부 큐를 도입하지 마라. FastAPI `BackgroundTasks` 만 사용한다 (ADR-006).
- 업로드된 파일을 응답에 포함하지 마라. `file_id` 만 반환한다.
- `run_analysis` 를 라우터에 직접 호출하지 마라. 반드시 `analysis_service.py` 를 통해서만 호출한다.
