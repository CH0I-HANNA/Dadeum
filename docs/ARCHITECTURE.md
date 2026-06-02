# 아키텍처

## 디렉토리 구조

```
./
├── frontend/
│   └── src/
│       ├── pages/          # 라우트 단위 컴포넌트 (UploadPage, ResultPage)
│       ├── components/     # 재사용 UI 컴포넌트
│       │   ├── upload/     # 파일 업로드 관련
│       │   ├── score/      # Consistency Score 카드
│       │   ├── slides/     # 슬라이드 그리드 + 이상 슬라이드 하이라이트
│       │   └── report/     # Root Cause + Recommendation 패널
│       ├── types/          # TypeScript 타입 정의 (api.ts 포함)
│       ├── hooks/          # Custom React hooks (useAnalysis, useUpload)
│       ├── lib/            # 유틸리티 함수
│       └── services/       # FastAPI 클라이언트 (axios 래퍼)
│
└── backend/
    ├── app/
    │   ├── api/            # FastAPI 라우터 (upload.py, analyze.py, thumbnail.py)
    │   ├── core/           # 설정(config.py), task 저장소(task_store.py), 예외(exceptions.py)
    │   ├── models/         # Pydantic 스키마 (schemas.py)
    │   ├── services/       # 비즈니스 로직 (analysis_service.py)
    │   └── pipeline/       # AI 파이프라인 모듈
    │       ├── parser.py        # PPTX/PDF → SlideRaw 구조체
    │       ├── extractor.py     # SlideRaw → SlideFeatureVector
    │       ├── detector.py      # SlideFeatureVector[] → OutlierResult[]
    │       ├── explainer.py     # OutlierResult → RootCause[]
    │       ├── recommender.py   # RootCause[] → Recommendation[]
    │       └── scorer.py        # SlideFeatureVector[] → ConsistencyScore
    └── tests/              # pytest 테스트 (test_parser.py, test_extractor.py, ...)
```

**`backend/app/core/exceptions.py`**: 파이프라인 전용 예외 클래스를 정의한다.

```python
class PipelineError(Exception):
    """파이프라인 실행 중 발생하는 모든 예외의 기반 클래스."""
    pass

class ParseError(PipelineError):
    """파싱 단계 실패 (손상 파일, 암호화, 지원하지 않는 형식)."""
    pass

class InsufficientSlidesError(PipelineError):
    """슬라이드 수 부족으로 특정 분석 불가."""
    pass
```

`analysis_service.py`는 `PipelineError` 및 하위 예외를 catch하여 task 상태를 `error`로 전환하고, `error_message`에 사용자 친화적 메시지를 저장한다. 예상치 못한 `Exception`도 catch하여 `error`로 처리한다.

---

## 파이프라인 데이터 흐름 (정상 경로)

```
PPTX/PDF 파일
    │
    ▼
[파일 유효성 검사] ── 실패 ──▶ task status = "error"
    │ 통과
    ▼
parser.py — SlideRaw (텍스트박스, 폰트, 색상, 위치, 이미지 원본 정보)
    │  예외 발생 시 → PipelineError("파싱 실패") → task error
    ▼
extractor.py — SlideFeatureVector[] (수치화된 feature 벡터, 슬라이드당 59차원)
    │  슬라이드 수 < 3 → outlier_slides=[] 로 진행 (scorer만 실행)
    │
    ├──▶ scorer.py ───────────────────▶ ConsistencyScore
    │
    └──▶ detector.py ── OutlierResult[]
              │  슬라이드 수 < 3 → 빈 리스트 반환
              ▼
         explainer.py — dict[slide_index, RootCause[]]
              │
              ▼
         recommender.py — dict[slide_index, Recommendation[]] + impact_score
              │
              ▼
         AnalysisResult → task status = "completed"
```

---

## 파일 유효성 검사 파이프라인

업로드 시점과 파싱 시점 두 단계로 검사한다.

### 업로드 시점 (api/upload.py)

1. **Content-Type 확인**: `multipart/form-data` 가 아니면 400
2. **확장자 확인**: `.pptx`, `.pdf` 외 → 400 "지원하지 않는 파일 형식"
3. **파일 크기 확인**: 50MB 초과 → 413
4. **Magic bytes 확인**: 확장자와 실제 파일 시그니처 일치 여부 확인
   - PPTX: `PK\x03\x04` (ZIP 기반)
   - PDF: `%PDF`
   - 불일치 시 → 400 "파일이 손상되었거나 잘못된 형식입니다"
5. **파일명 sanitize**: `pathlib.Path(filename).name` 으로 경로 traversal 방지

### 파싱 시점 (pipeline/parser.py)

6. **PPTX 열기 시도**: `python-pptx` 예외 → `PipelineError("파일을 열 수 없습니다")`
7. **슬라이드 수 확인**: 0장이면 `PipelineError("슬라이드가 없습니다")`
8. **슬라이드 수 상한 적용**: 50장 초과 시 50장까지만 처리, 나머지 무시
9. **암호화 감지**: PPTX 열기 시 `PackageNotFoundError` → `PipelineError("암호로 보호된 파일")`

---

## Task 상태 머신

```
[생성]
  │
  ▼
pending ──▶ processing ──▶ completed
                │
                ▼
              error
```

| 전이 | 조건 | 기록 필드 |
|------|------|----------|
| pending → processing | BackgroundTask 시작 시 | `started_at` |
| processing → completed | `run_analysis` 정상 완료 | `completed_at`, `result` |
| processing → error | 파이프라인 예외 발생 | `failed_at`, `error_message` |
| processing → error | 분석 120초 초과 (timeout) | `failed_at`, `error_message = "분석 시간 초과"` |

**타임아웃**: `analysis_service.py` 는 `concurrent.futures.ThreadPoolExecutor` 로 파이프라인을 실행하고 `future.result(timeout=120)` 으로 타임아웃을 감지한다. 타임아웃 발생 시 task 상태를 error로 전환한다. `signal.alarm` 은 스레드에서 사용 불가(Unix 전용, main thread 제약)이므로 사용하지 않는다. (ADR-010 참조)

**stuck task 감지**: task가 `processing` 상태로 180초 이상 유지되면 클라이언트가 타임아웃 처리한다 (서버 측 정리 메커니즘은 MVP 제외).

---

## API 엔드포인트 명세

### POST /api/upload

| 항목 | 내용 |
|------|------|
| Request | `multipart/form-data`, field name: `file` |
| 성공 응답 | 200 + `UploadResponse { file_id, slide_count, filename }` |
| 400 | 지원하지 않는 형식, magic bytes 불일치, 파일명 없음 |
| 413 | 파일 크기 50MB 초과 |
| 500 | 파일 저장 실패 (디스크 오류 등) |

### POST /api/analyze/{file_id}

| 항목 | 내용 |
|------|------|
| Request | Path param: `file_id` |
| 성공 응답 | 202 + `AnalyzeResponse { task_id }` |
| 404 | `file_id` 에 해당하는 파일 없음 |
| 409 | 동일 `file_id` 에 대해 이미 분석 진행 중 (중복 방지) |

**409 감지 구현**: `task_store` 는 `task_id → task` 매핑 외에 `file_id → task_id` 역방향 매핑도 유지한다. `POST /api/analyze` 호출 시 `file_id`로 역방향 조회하여 기존 task가 `pending` 또는 `processing` 상태이면 409 반환. `completed` 또는 `error` 상태이면 새 task 생성 허용.

### GET /api/result/{task_id}

| 항목 | 내용 |
|------|------|
| Request | Path param: `task_id` |
| 성공 응답 (진행 중) | 200 + `{ status: "pending" \| "processing" }` |
| 성공 응답 (완료) | 200 + `{ status: "completed", result: AnalysisResult }` |
| 성공 응답 (에러) | 200 + `{ status: "error", error_message: string }` |
| 404 | `task_id` 없음 |

### GET /api/thumbnail/{file_id}/{slide_num}

| 항목 | 내용 |
|------|------|
| Request | Path params: `file_id`, `slide_num` (0-based) |
| 성공 응답 | 200 + PNG 바이너리, `Content-Type: image/png` |
| 400 | `slide_num` 이 음수이거나 정수가 아닌 경우 |
| 404 | `file_id` 없음, 또는 `slide_num` 이 슬라이드 수 초과 |
| 500 | 썸네일 생성 실패 |

**썸네일 생성 방식**: python-pptx는 슬라이드를 이미지로 렌더링하는 기능을 제공하지 않는다. MVP에서는 Pillow로 슬라이드 원본 비율을 유지한 대체 썸네일을 생성한다. 크기: 최대 너비 400px, 높이는 `slide_height_emu / slide_width_emu × 400` 으로 계산 (16:9이면 400×225, 4:3이면 400×300). 실제 PPTX 외관과 다를 수 있으며, 결과 화면에 이 사실을 표시한다. (ADR-008 참조)

**썸네일 캐싱**: 동일 `file_id + slide_num` 조합의 썸네일은 메모리에 캐시(`dict[str, bytes]`)하여 반복 요청 시 재생성하지 않는다. 서버 재시작 시 캐시 소멸.

---

## Feature Vector 설계

`SlideFeatureVector`는 슬라이드당 아래 feature 그룹으로 구성된다. **차원 순서는 scorer의 인덱스 매핑과 반드시 일치해야 한다.**

### Typography (index 0~28, 29차원)

| index | Feature | 설명 |
|-------|---------|------|
| 0~18 | font_frequency | KNOWN_FONTS 19개 각각의 사용 빈도 (TextElement 수 기준, 합산 정규화). 빈도 벡터. |
| 19 | font_frequency_other | KNOWN_FONTS 목록에 없는 폰트의 합산 빈도. index 0~19의 합 = 1.0. |
| 20 | font_size_mean | 슬라이드 내 모든 TextElement font_size 평균. **정규화: pt / 72** (72pt = 1인치 기준). |
| 21 | font_size_std | 표준편차. **정규화: pt / 72** |
| 22 | font_size_min | 최솟값. **정규화: pt / 72** |
| 23 | font_size_max | 최댓값. **정규화: pt / 72** |
| 24 | font_size_median | 중앙값. **정규화: pt / 72** |
| 25 | bold_ratio | Bold TextElement 수 / 전체 TextElement 수 |
| 26 | italic_ratio | Italic TextElement 수 / 전체 TextElement 수 |
| 27 | font_variety_count | 사용 폰트 종류 수 / 5 (clip 1.0) |
| 28 | line_spacing_normalized | 평균 줄간격 / 2.0 (기본값 1.0 기준, clip 1.0). 데이터 없으면 0.5. |

**정규화 근거**: font_size_* 를 pt 그대로 두면 (예: mean=24pt) 다른 0~1 feature보다 스케일이 24배 커진다. Consistency Score의 CV 계산에서 typography 그룹이 다른 그룹을 압도하게 되므로 반드시 / 72 정규화가 필요하다.

**KNOWN_FONTS (index 0~18, 총 19개)**:
```
0: Pretendard       1: Noto Sans KR     2: Malgun Gothic
3: 나눔고딕          4: Apple SD Gothic  5: Spoqa Han Sans
6: Source Han Sans  7: Arial            8: Helvetica
9: Times New Roman  10: Georgia         11: Calibri
12: Cambria         13: Verdana         14: Tahoma
15: Roboto          16: Open Sans       17: Lato
18: Montserrat
index 19: Other (KNOWN_FONTS에 없는 모든 폰트)
```

**엣지케이스**: 텍스트 요소가 없으면 index 0~28 전부 0.0. 분모가 0인 경우 0으로 처리.

**총 Typography 차원: 29차원 (기존 28차원에서 1 증가)**

### Color (index 29~43, 15차원)

| index | Feature | 설명 |
|-------|---------|------|
| 29~31 | dominant_color_1 | 가장 빈도 높은 텍스트 색상 [R/255, G/255, B/255] |
| 32~34 | dominant_color_2 | 두 번째 색상 (없으면 0,0,0) |
| 35~37 | dominant_color_3 | 세 번째 색상 (없으면 0,0,0) |
| 38~40 | background_color | SlideRaw.background_color_rgb / 255 |
| 41 | color_variance | dominant_color 3개 RGB값 전체의 분산 |
| 42 | saturation_mean | dominant_color 3개를 HSV 변환 후 S 평균 |
| 43 | brightness_mean | dominant_color 3개를 HSV 변환 후 V 평균 |

**엣지케이스**: 텍스트 색상이 없으면 dominant_color 전부 0.0.

### Layout (index 44~54, 11차원)

| index | Feature | 설명 |
|-------|---------|------|
| 44 | text_area_ratio | Σ(width×height) of TextElements, clip 1.0 |
| 45 | image_area_ratio | Σ(width×height) of ImageElements, clip 1.0 |
| 46 | whitespace_ratio | max(0, 1 - text_area_ratio - image_area_ratio) |
| 47 | alignment_left | TextElement 중 left 비율 |
| 48 | alignment_center | center 비율 |
| 49 | alignment_right | right 비율 |
| 50 | margin_top | min(y) of all elements. 요소 없으면 0.5 |
| 51 | margin_bottom | min(1 - y - height). 요소 없으면 0.5 |
| 52 | margin_left | min(x). 요소 없으면 0.5 |
| 53 | margin_right | min(1 - x - width). 요소 없으면 0.5 |
| 54 | element_count | (텍스트+이미지 요소 수) / 20, clip 1.0 |

### Content Density (index 55~58, 4차원)

| index | Feature | 설명 |
|-------|---------|------|
| 55 | word_count_normalized | 전체 텍스트 단어 수 / 100, clip 1.0 |
| 56 | bullet_count_normalized | 불릿으로 시작하는 줄 수 / 20, clip 1.0 |
| 57 | text_image_ratio | text_area / (text_area + image_area + ε) |
| 58 | sentence_count_normalized | 문장 수 / 30, clip 1.0 |

**총 59차원** (Typography 29 + Color 15 + Layout 11 + Content 4). 이후 Visual Embedding (128차원, CLIP) 추가 시 index 59~186으로 확장.

---

## Consistency Score 산출 공식

각 feature 그룹 내 각 차원 d에 대해 CV를 계산하고, 그룹의 cohesion은 차원별 cohesion의 평균이다.

```
# 슬라이드가 N장, 그룹 내 차원이 D개일 때
for each dimension d in group:
    values_d = [slide[d] for slide in all_slides]   # 길이 N의 벡터
    CV_d = std(values_d) / (mean(values_d) + ε)     # ε = 1e-8
    cohesion_d = 1 / (1 + CV_d)                     # 0~1

cohesion(group) = mean(cohesion_d for d in group)   # 차원별 평균

ConsistencyScore.total = 100 × (
    cohesion(typography) × 0.30 +   # index 0~28  (29차원)
    cohesion(color)      × 0.30 +   # index 29~43 (15차원)
    cohesion(layout)     × 0.25 +   # index 44~54 (11차원)
    cohesion(content)    × 0.15     # index 55~58 (4차원)
)
```

**차원별로 계산하는 이유**: group을 flatten하여 단일 CV를 계산하면 차원 수가 많은 그룹(typography 29차원)이 단일 값인 차원(bold_ratio 1차원)보다 CV를 지배하게 된다. 차원별 cohesion을 평균내면 각 feature의 기여가 균등해진다.

**엣지케이스**:
- 슬라이드 1장: std = 0 → CV_d = 0 → cohesion_d = 1.0 → total = 100
- 모든 슬라이드가 동일: std = 0 → total = 100
- 특정 차원 d가 전체 슬라이드에서 모두 0.0: std = 0, mean = 0 → CV = 0/(ε) ≈ 0 → cohesion_d = 1.0. "데이터 없음"이므로 해당 그룹 세부 점수 UI에서 "분석 불가" 표시 (단, 점수 계산에는 포함).

---

## Outlier Detection 모델 전략

| 단계 | 모델 | 조건 |
|------|------|------|
| MVP | Isolation Forest (scikit-learn) | 학습 데이터 없이 즉시 적용 가능 |
| Advanced | AutoEncoder (PyTorch) | 충분한 PPT 샘플 축적 후 적용 |
| Research | GNN (PyTorch Geometric) | 슬라이드 간 Style Similarity를 Edge로 구성, 그래프 이상치 탐지 |

GNN 상세: 슬라이드를 노드로, feature 유사도(코사인 유사도 > 임계값)를 엣지로 구성한 그래프에서 Graph Autoencoder(GAE)로 재구성 오류가 높은 노드를 이상치로 탐지.

**Isolation Forest 엣지케이스**:
- 슬라이드 3장 미만: 탐지 불가 → `OutlierResult[]` 빈 리스트 반환
- contamination=0.2 기준으로 최소 1장이 이상치로 탐지될 수 있음 (슬라이드 5장 × 0.2 = 1장). 이상치가 없어야 할 상황에서도 강제로 탐지할 수 있는 한계를 사용자에게 안내.

---

## 파일 저장 및 정리

- 업로드 파일 저장 경로: `backend/tmp/uploads/{uuid4}{ext}` (예: `backend/tmp/uploads/a3f9...b2.pptx`). `file_id = uuid4` 이고 `ext` 는 업로드 시 검증된 확장자(`.pptx` 또는 `.pdf`). `parse_file` 이 확장자로 파일 타입을 판별하므로 확장자 유지 필수.
- 분석 완료 후 파일 정리: MVP는 자동 삭제 없음. 서버 재시작 시 tmp/ 디렉토리 비워짐.
- 디스크 부족 시: `shutil.disk_usage()` 로 업로드 전 여유 공간 확인. 500MB 미만이면 503 반환.

---

## 동시성 안전성

- `task_store.py` 의 `_tasks` 딕셔너리는 여러 BackgroundTask 스레드에서 동시 접근 가능.
- `threading.Lock` 으로 read/write 보호 필수. (ADR-009 참조)
- FastAPI의 `BackgroundTasks` 는 응답 반환 후 같은 프로세스 내 스레드풀에서 실행됨.

---

## 상태 관리 (Frontend)

- 서버 상태 (분석 결과, 파일 메타): React Query (`useQuery`, `useMutation`)
- 클라이언트 상태 (선택된 슬라이드, UI 토글): `useState` / `useReducer`
- 전역 공유 상태 없음 — 페이지 단위로 데이터 격리
- 폴링 간격: 1.5초. `status === "completed" | "error"` 시 폴링 중단.
- 클라이언트 타임아웃: 폴링 시작 후 120초 경과 시 강제 중단 + 에러 메시지 표시.
