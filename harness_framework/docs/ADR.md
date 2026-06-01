# Architecture Decision Records

## 철학

작동하는 최소 구현 우선. AI 파이프라인은 모듈 교체 가능하게 설계하되 MVP는 가장 단순한 모델(Isolation Forest)로 시작한다. 외부 서비스 의존성 최소화.

---

### ADR-001: FastAPI 선택 (Django/Flask 대신)

**결정**: 백엔드 프레임워크로 FastAPI 사용

**이유**: AI 파이프라인(NumPy, scikit-learn)은 CPU-bound 작업이지만, FastAPI의 `BackgroundTasks`가 스레드풀에서 실행되어 분석 중에도 다른 요청을 처리할 수 있음. Pydantic v2 내장으로 프론트엔드 TypeScript 타입과 스키마를 자동 동기화 가능. 자동 OpenAPI 문서 생성으로 프론트-백 인터페이스 협업 비용 절감.

**트레이드오프**: Django ORM, admin 패널 등 배터리 포함 기능 포기. MVP에서는 ORM이 불필요하므로 문제없음.

**구현 제약**: FastAPI `BackgroundTasks`는 등록된 함수가 `def` (sync)이면 스레드풀에서 실행하고, `async def`이면 event loop에서 실행한다. 파이프라인(scikit-learn, NumPy)은 CPU-bound sync 코드이므로 반드시 `def`로 정의해야 한다. `async def`로 정의하면 분석 실행 동안 다른 모든 요청이 블로킹된다.

---

### ADR-002: Isolation Forest로 MVP 이상치 탐지 시작

**결정**: MVP 단계에서 Isolation Forest(scikit-learn) 사용

**이유**: 레이블 데이터 없이 즉시 적용 가능한 비지도 학습 모델. 슬라이드 수가 적어도(10~50장) 동작하며, 훈련 데이터 구축 없이 바로 사용 가능.

**트레이드오프**:
- Isolation Forest는 feature importance를 직접 제공하지 않는다. 원인 분석(explainer)은 별도로 슬라이드 feature와 전체 중앙값을 비교하는 규칙 기반 로직으로 구현한다.
- 슬라이드 간 순서/시퀀스 관계를 반영하지 못한다. GNN 단계에서 해결.
- contamination=0.2 고정 시 슬라이드 수에 따라 이상치 수가 달라진다 (5장 → 1장, 50장 → 10장). 실제로 이상치가 없어도 강제로 탐지할 수 있는 한계가 있다. UI에서 "AI가 상대적으로 튀는 슬라이드를 탐지한 결과입니다"로 명시한다.

**contamination=0.2 선택 근거**: 발표자료에서 "디자인이 튀는 슬라이드"는 보통 전체의 10~30% 수준이라고 가정. 0.1이면 탐지 누락이 많고, 0.3이면 오탐이 많음. 0.2는 중간값. 향후 사용자 피드백으로 조정 예정.

---

### ADR-003: 프론트엔드 React + Vite (Next.js 대신)

**결정**: Next.js 대신 React + Vite + React Router 조합 사용

**이유**: SSR/SSG가 불필요한 SPA 구조. 백엔드가 FastAPI로 분리되어 있으므로 Next.js의 API Routes, Server Components 이점이 없음. Vite가 개발 서버 속도 측면에서 우월.

**트레이드오프**: SEO 최적화 없음. 서비스 특성상 (파일 업로드 후 분석 대시보드) SEO 불필요하므로 허용.

---

### ADR-004: 모노레포 구조 (frontend/ + backend/ 동일 레포)

**결정**: 프론트엔드와 백엔드를 단일 레포에서 관리

**이유**: 팀 규모 소규모(캡스톤 팀). 타입 스키마 변경 시 한 번에 추적 가능. 로컬 개발 환경 설정 단순화.

**트레이드오프**: 레포가 커지면 CI/CD 파이프라인 분리가 복잡해질 수 있음. MVP 단계에서는 허용.

---

### ADR-005: GNN은 Research 단계로 분리

**결정**: GNN(PyTorch Geometric) 구현을 MVP에 포함하지 않고 Research Phase로 분리

**이유**: GNN(GAE) 학습에 필요한 PPT 데이터셋을 MVP 단계에서 확보하기 어려움. 하이퍼파라미터 튜닝(엣지 임계값, 레이어 수, 임베딩 차원)에 시간이 필요. MVP는 Isolation Forest로 핵심 UX를 먼저 검증한 뒤 고도화.

**트레이드오프**: MVP에서 슬라이드 간 관계(순서, 섹션 흐름)를 반영하지 못해 이상치 탐지 정확도가 낮을 수 있음.

---

### ADR-006: 분석 작업 비동기 처리 (BackgroundTasks)

**결정**: `POST /api/analyze` 는 task_id를 즉시 반환하고, 클라이언트가 폴링으로 결과를 조회. 큐잉은 FastAPI `BackgroundTasks` 사용.

**이유**: 30슬라이드 PPT 분석에 10~30초 소요 예상. 동기 처리 시 클라이언트 타임아웃 및 사용자 경험 저하.

**트레이드오프**: 서버 재시작 시 진행 중인 작업 유실. Celery/Redis 없이 단순하게 유지하되, task 상태는 in-memory로 관리한다 (ADR-009 참조). 분석 타임아웃은 120초로 설정하고, 초과 시 error 상태로 전환.

---

### ADR-007: 파일 저장 전략 (로컬 파일시스템)

**결정**: 업로드 파일을 서버 로컬 파일시스템 (`backend/tmp/uploads/`) 에 저장

**이유**: MVP 범위에서 S3, GCS 등 외부 오브젝트 스토리지 의존성을 추가하지 않는다. 캡스톤 발표 및 로컬 개발 환경에서 즉시 동작해야 함.

**트레이드오프**:
- 서버 재시작 시 파일 소멸 (분석 결과도 함께 소멸).
- 여러 서버 인스턴스로 확장 불가 (스케일아웃 시 파일을 찾지 못함).
- 디스크 용량 관리 필요: 업로드 전 여유 공간을 확인하고, 500MB 미만이면 503을 반환한다. MVP는 자동 정리 없이 서버 재시작 시 tmp/ 폴더를 비운다.

---

### ADR-008: 썸네일 생성 방식 (Pillow 대체 렌더링)

**결정**: python-pptx로 파싱한 텍스트/레이아웃 정보를 기반으로 Pillow로 단순화된 대체 썸네일을 생성한다.

**이유**: python-pptx는 슬라이드를 이미지로 렌더링하는 기능을 제공하지 않는다. 실제 렌더링을 위한 대안은 다음과 같으나 모두 MVP 범위를 벗어난다:
- LibreOffice headless: 서버에 LibreOffice 설치 필요, 속도 느림, 외부 의존성 큼
- comtypes (Windows COM): Windows 서버 전용, 크로스플랫폼 불가
- Aspose.Slides (유료): 라이선스 비용 발생

**트레이드오프**: 생성되는 썸네일이 실제 PPTX 외관과 다르다. 배경색 + 텍스트 위치 + 이미지 영역만 표현한다. 결과 화면에 "썸네일은 레이아웃을 간략히 표현한 것입니다" 안내 문구를 표시한다.

**Pillow 썸네일 생성 규칙**:
- 크기: 최대 너비 400px, 높이는 슬라이드 원본 비율 유지 (`round(400 × slide_height_emu / slide_width_emu)`). 16:9이면 400×225, 4:3이면 400×300. 고정 크기를 사용하면 비율 왜곡이 발생하므로 반드시 원본 비율 계산 필요.
- 배경: `SlideRaw.background_color_rgb`
- 텍스트 박스: 회색(`#9ca3af`) 직사각형으로 위치/크기 표현
- 이미지 영역: 대각선 사선이 그어진 직사각형으로 표현
- 이상 슬라이드는 amber(#f59e0b) 테두리 오버레이 없이 반환. 테두리는 프론트엔드 CSS로 처리.

---

### ADR-009: Task 상태 저장소 (In-Memory)

**결정**: task 상태를 SQLite가 아닌 in-memory 딕셔너리로 관리한다.

**이유**: MVP 범위에서 SQLite 스키마 설계, 마이그레이션, 연결 관리 복잡도를 추가하지 않는다. 서버 재시작 시 task 유실은 허용된 트레이드오프(ADR-007과 동일 논리: 파일도 재시작 시 소멸).

**동시성 안전성**: `_tasks` 딕셔너리는 `threading.Lock`으로 보호한다. `BackgroundTasks`가 스레드풀에서 실행되어 동시 쓰기가 발생할 수 있기 때문.

**트레이드오프**:
- 서버 재시작 시 모든 task 상태 소멸.
- 멀티프로세스 uvicorn(`--workers > 1`) 사용 불가. MVP는 단일 워커로만 실행.
- 향후 확장 시 Redis 또는 SQLite로 교체 필요.

**구현 제약**: `task_store.py` 는 전역 `_lock = threading.Lock()` 을 선언하고, 모든 read/write 함수에서 `with _lock:` 으로 감싸야 한다.

---

### ADR-010: 분석 타임아웃 구현 전략 및 한계

**결정**: `concurrent.futures.ThreadPoolExecutor`로 파이프라인을 실행하고 `future.result(timeout=120)`으로 타임아웃을 감지한다. 타임아웃 발생 시 task 상태를 error로 전환한다.

**이유**: 세 가지 대안을 검토했다.
- `signal.alarm(120)`: Unix(macOS/Linux) 전용. Windows에서 동작하지 않으며, 멀티스레드 환경에서 signal은 main thread에서만 처리되므로 BackgroundTask 스레드에서 사용 불가.
- `multiprocessing.Process`: 실제 프로세스 종료로 타임아웃을 보장하지만, 프로세스 간 데이터 직렬화(pickle) 비용이 크고 NumPy 배열 전달이 복잡해 MVP 범위를 벗어남.
- `threading.Event + 폴링`: 폴링 오버헤드 + 파이프라인이 Event를 확인하지 않으면 실제 중단 불가.

**트레이드오프 (알려진 한계)**:
- `future.result(timeout=120)`은 TimeoutError를 발생시키지만, 백그라운드 스레드는 계속 실행된다. Python의 threading은 외부에서 스레드를 강제 종료할 수 없기 때문. 즉, 타임아웃 후에도 파이프라인이 완료될 때까지 서버 자원을 점유할 수 있다.
- 이는 MVP에서 허용된 한계. 단, `uvicorn --workers 1` (단일 워커)로 운영하면 동시 분석 작업이 1개이므로 실질적 영향이 제한됨.
- 향후: 실제 강제 종료가 필요하면 `multiprocessing` 기반으로 교체.

**구현 방법**:
```python
# analysis_service.py
from concurrent.futures import ThreadPoolExecutor, TimeoutError

def run_analysis_with_timeout(file_path, task_id):
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run_pipeline, file_path)
        try:
            result = future.result(timeout=120)
            task_store.set_completed(task_id, result)
        except TimeoutError:
            task_store.set_error(task_id, "분석 시간이 초과되었습니다.")
        except PipelineError as e:
            task_store.set_error(task_id, str(e))
        except Exception:
            task_store.set_error(task_id, "분석 중 예기치 않은 오류가 발생했습니다.")
```
