# 다듬 (Dadeum)

> AI 기반 프레젠테이션 슬라이드 디자인 일관성 분석 서비스

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-Strict-3178C6?style=flat&logo=typescript&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3-06B6D4?style=flat&logo=tailwindcss&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-IsolationForest-F7931E?style=flat&logo=scikit-learn&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EfficientNet--B3-EE4C2C?style=flat&logo=pytorch&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-162%20passed-brightgreen?style=flat)

---

## 왜 이 서비스가 필요한가

50~100장 규모의 발표자료를 만들다 보면 어느 순간 폰트가 슬쩍 바뀌거나, 특정 슬라이드만 배경색이 다르거나, 텍스트 여백이 들쭉날쭉해진다. 여러 명이 나눠 만든 팀플 발표자료, 오래된 템플릿을 재활용한 IR Deck, 마감 직전에 급히 추가한 슬라이드들이 대표적인 사례다.

**이런 불일치를 사람 눈으로 전체 슬라이드를 훑으며 잡아내는 건 번거롭고 실수가 잦다.** 특히 "50장 중 3장만 폰트가 다른" 경우처럼 미묘한 불일치는 발표 직전까지 발견하지 못하는 경우도 많다.

다듬은 PPTX/PDF를 업로드하면 슬라이드 전체의 타이포그래피·색상·레이아웃·콘텐츠를 자동으로 분석하여 **어떤 슬라이드가 왜 튀는지**를 수치와 근거와 함께 알려준다.

### 주요 사용자

| 페르소나 | 상황 | 핵심 니즈 |
|----------|------|-----------|
| 취업 준비생 | 포트폴리오/자기소개 PPT 마감 전날 | 어떤 슬라이드가 이상한지 빠르게 파악 |
| 대학생 | 팀플 발표자료 합치기 후 검수 | 각자 만든 슬라이드의 통일감 확인 |
| 스타트업 | IR Deck 투자자 발표 전 | 브랜드 일관성 + 전문성 점검 |

---

## 기존 방법과의 차별점

### 기존 방법의 한계

| 방법 | 한계 |
|------|------|
| **직접 눈으로 검수** | 슬라이드 수가 많을수록 놓치는 불일치가 늘어남. 50장 중 3장만 다른 폰트는 거의 발견 못함 |
| **PowerPoint Designer** | 개별 슬라이드 디자인 제안에 그침. 덱 전체의 일관성을 분석하지 않음 |
| **Canva / Figma** | 처음부터 그 도구로 만든 파일에만 적용 가능. 기존 PPTX/PDF는 지원 안 함 |
| **디자이너에게 의뢰** | 비용 발생, 시간 소요. 피드백이 주관적이고 근거가 불명확한 경우 많음 |
| **AI 이미지 분석 서비스** | 슬라이드를 독립된 이미지로 분석. 덱 전체의 집합적 특성을 반영하지 못함 |

### 다듬의 차별화 포인트

**1. 덱 전체를 하나의 집합으로 분석한다**

기존 도구들은 슬라이드를 개별적으로 "이 슬라이드가 예쁜가?"를 묻지만, 다듬은 "이 슬라이드가 나머지와 얼마나 다른가?"를 묻는다. 전체 50장의 분포를 기준으로 특정 슬라이드의 이탈도를 측정하는 것이 핵심이다.

**2. 정량적 근거를 제공한다**

"이 슬라이드가 이상하다"는 말 대신 구체적인 수치를 제시한다.
- `폰트 불일치 — 기대: Pretendard (전체의 94%) / 실제: Times New Roman`
- `색상 불일치 — 기대: RGB(255,255,255) / 실제: RGB(20,20,30)`
- `레이아웃 불일치 — 기대: 텍스트 비율 51% / 실제: 텍스트 비율 15%`

디자인 감각이 없어도 왜 이상한지를 이해하고 수정할 수 있다.

**3. 레이블 없이 동작한다**

Isolation Forest 기반 비지도 학습으로, 어떤 PPTX/PDF든 별도 학습이나 사전 설정 없이 즉시 분석할 수 있다. "정상 슬라이드"가 무엇인지 모델이 미리 알 필요가 없다 — 같은 덱 안에서 상대적으로 튀는 슬라이드를 찾는다.

**4. 기존 파일 형식을 그대로 받는다**

PPTX/PDF를 업로드하면 된다. 특정 도구로 다시 만들거나 변환할 필요가 없다.

**5. 59차원 피처로 사람 눈이 놓치는 불일치를 잡는다**

폰트 크기 평균/분산/중앙값, 색상 채도·밝기, 텍스트 정렬 비율, 여백 4방향 등을 정밀하게 비교한다. "뭔가 어색한데 왜 그런지 모르겠다"는 느낌을 수치로 설명한다.

---

## 주요 기능

### 디자인 일관성 분석

**Consistency Score** — 슬라이드 전체를 4개 축으로 0~100점 채점

| 축 | 분석 내용 |
|----|----------|
| 폰트 (30%) | 폰트 종류, 크기 분포, bold/italic 비율 |
| 색상 (30%) | 지배 색상, 배경색, 채도/밝기 일관성 |
| 레이아웃 (25%) | 텍스트·이미지 면적 비율, 정렬, 여백 |
| 콘텐츠 (15%) | 단어 수, 불릿 수, 텍스트 밀도 |

**이상 슬라이드 탐지** — Isolation Forest 기반 비지도 학습. 레이블 없이 "전체에서 상대적으로 튀는 슬라이드"를 자동 검출한다.

**원인 분석** — 이상 슬라이드에 대해 "기대값 vs 실제값"을 feature 그룹별로 제시한다.
- 예: `폰트 불일치 — 기대: Pretendard / 실제: Times New Roman`
- 예: `색상 불일치 — 기대: RGB(255,255,255) / 실제: RGB(20,20,30)`

**수정 제안** — 각 원인에 대한 구체적 액션과 수정 후 예상 점수 향상치를 함께 제공한다.

### 발표 구조 분석 (실험적)

EfficientNet-B3 CNN으로 각 슬라이드를 표지·섹션헤더·본문·도표·마무리로 분류하고, 역할 흐름의 이상 여부를 규칙 기반으로 판단한다.

> ⚠️ CNN이 영어 학술 슬라이드(Zenodo10K)로 학습되어 한국어 발표자료에 대한 정확도가 낮다. 이 기능은 참고용으로만 활용하는 것을 권장한다.

### 부가 기능

- **슬라이드 비교 모드** — 두 슬라이드를 나란히 놓고 통계 비교
- **이슈 필터** — 폰트/색상/레이아웃/콘텐츠 유형별 이상 슬라이드 필터링
- **PDF 보고서** — 분석 결과 전체를 PDF 문서로 다운로드
- **수정 파일 다운로드** — 수정 제안이 반영된 PPTX/PDF 파일 생성

---

## 기술 스택

### Frontend

| 라이브러리 | 역할 |
|-----------|------|
| React 18 + TypeScript | UI, strict mode |
| Vite | 빌드 도구 |
| TailwindCSS v3 | 유틸리티 퍼스트 스타일링 |
| React Query (@tanstack/react-query) | 서버 상태 관리, 1.5초 폴링 |
| React Router v6 | 클라이언트 라우팅 |
| Axios | HTTP 클라이언트 |

### Backend

| 라이브러리 | 역할 |
|-----------|------|
| FastAPI | 비동기 REST API |
| Pydantic v2 | 스키마 검증 및 직렬화 |
| python-pptx | PPTX 파싱 및 수정 |
| pdfplumber | PDF 텍스트/레이아웃 추출 |
| pymupdf (fitz) | PDF 썸네일 렌더링 |
| fpdf2 | PDF 보고서 생성 |
| Pillow | PPTX 썸네일 렌더링 |

### AI Pipeline

| 라이브러리 | 역할 |
|-----------|------|
| scikit-learn | Isolation Forest 이상 탐지 |
| PyTorch + timm | EfficientNet-B3 역할 분류 CNN |
| NumPy | 피처 추출 수치 연산 |

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                   Browser  (React + Vite)                    │
│                                                              │
│  UploadPage                ResultPage                        │
│  ├─ 드래그 앤 드롭          ├─ ConsistencyScoreCard          │
│  └─ 파일 선택               ├─ StructureScoreCard (실험)     │
│                             ├─ SlideGrid + 역할 뱃지         │
│                             ├─ DetailPanel (원인/수정 제안)  │
│                             └─ ComparePanel                  │
└──────────────────────┬──────────────────────────────────────┘
                       │  HTTP / REST
┌──────────────────────▼──────────────────────────────────────┐
│                  FastAPI  (uvicorn --reload)                 │
│                                                              │
│  POST /api/upload              ← magic bytes 검증 포함       │
│  POST /api/analyze/{file_id}   ← task_id 즉시 반환 (202)    │
│  GET  /api/result/{task_id}    ← 클라이언트 1.5초 폴링       │
│  GET  /api/thumbnail/{id}/{n}  ← in-memory 캐싱             │
│  GET  /api/report/{task_id}    ← fpdf2 PDF 생성             │
│  POST /api/fix/{file_id}       ← 수정 파일 다운로드          │
│                                                              │
│  BackgroundTasks (ThreadPoolExecutor, timeout 180s)         │
│  In-memory task store  {task_id → status/result}            │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              AI Pipeline  (backend/app/pipeline/)            │
│                                                              │
│  parser.py          PPTX/PDF → SlideRaw                     │
│      │                                                       │
│  extractor.py       SlideRaw → SlideFeatureVector (59차원)  │
│      ├──────────────────────────────────────────────┐       │
│  scorer.py          ConsistencyScore (CV 기반)       │       │
│      └──────────────────────────────────────────────┘       │
│  detector.py        IsolationForest → OutlierResult[]       │
│  explainer.py       OutlierResult → RootCause[]             │
│  recommender.py     RootCause[] → Recommendation[]          │
│                                                              │
│  (PPTX/PDF)                                                  │
│  slide_renderer.py  PPTX/PDF → PIL Image[]                  │
│  role_classifier.py PIL Image[] → role_sequence[]  (CNN)    │
│  hmm_scorer.py      role_sequence → anomaly_score (규칙)    │
└─────────────────────────────────────────────────────────────┘
```

---

## AI 파이프라인 상세

### 1단계 — 파싱

`parser.py`가 PPTX/PDF를 읽어 슬라이드별 `SlideRaw` 구조체로 변환한다.

- **PPTX**: python-pptx로 TextElement(텍스트·폰트·색상·위치), ImageElement(위치·크기), 배경색을 추출한다.
- **PDF**: pdfplumber로 단어별 위치·폰트명·크기를 추출한다. 색상 정보는 추출 불가(흑색으로 처리).
- 슬라이드 수 상한: 50장 (초과분 무시)

### 2단계 — 피처 추출 (59차원)

`extractor.py`의 `SlideFeatureExtractor`가 `SlideRaw` → `SlideFeatureVector`로 변환한다. 모든 값은 0~1로 정규화된다.

```
Typography (index 0~28, 29차원)
  0~19  dominant_font_one_hot  — 19개 알려진 폰트 + Other 빈도 벡터
  20    font_size_mean          — pt / 72 (정규화)
  21    font_size_std
  22~24 font_size_min/max/median
  25    bold_ratio
  26    italic_ratio
  27    font_variety_count      — 사용 폰트 종류 수 / 5
  28    line_spacing_normalized

Color (index 29~43, 15차원)
  29~31 dominant_color_1 (R/255, G/255, B/255)
  32~34 dominant_color_2
  35~37 dominant_color_3
  38~40 background_color
  41    color_variance
  42    saturation_mean
  43    brightness_mean

Layout (index 44~54, 11차원)
  44    text_area_ratio
  45    image_area_ratio
  46    whitespace_ratio
  47~49 alignment_left/center/right
  50~53 margin_top/bottom/left/right
  54    element_count

Content (index 55~58, 4차원)
  55    word_count_normalized   — 단어 수 / 100
  56    bullet_count_normalized — 불릿 수 / 20
  57    text_image_ratio
  58    sentence_count_normalized
```

### 3단계 — 일관성 점수

슬라이드 집합 전체에서 각 차원의 변동계수(CV)를 계산하여 일관성(cohesion)으로 변환한다.

```python
CV(d)       = std(d) / (mean(d) + ε)
cohesion(d) = 1 / (1 + CV(d))          # 0~1, 높을수록 일관적
score       = 100 × (
    mean(cohesion for d in typography) × 0.30 +
    mean(cohesion for d in color)      × 0.30 +
    mean(cohesion for d in layout)     × 0.25 +
    mean(cohesion for d in content)    × 0.15
)
```

그룹을 flatten하여 단일 CV를 계산하면 차원 수가 많은 그룹(typography 29차원)이 단일 값인 차원(bold_ratio)을 압도하므로, **차원별 cohesion을 평균내는 방식**을 채택했다.

### 4단계 — 이상 탐지: Isolation Forest

**왜 Isolation Forest인가?**
레이블 데이터 없이 즉시 적용 가능한 비지도 학습 모델이 필요했다. 슬라이드 수가 10~50장으로 적어도 안정적으로 동작하며, 어떤 PPTX든 별도 학습 없이 바로 쓸 수 있다.

contamination은 슬라이드 수에 따라 동적으로 결정된다.

```python
def _dynamic_contamination(n: int) -> float:
    if n <= 5:  return 0.15
    if n <= 15: return 0.20
    return 0.25
```

이상 점수는 decision_function 값을 0~1로 반전 정규화한다 (높을수록 이상).

### 5단계 — 원인 분석 및 수정 제안

`explainer.py`는 이상 슬라이드의 feature 벡터와 전체 중앙값을 그룹별로 코사인 유사도로 비교하여 유사도가 낮은 그룹을 원인으로 특정한다.

`recommender.py`는 원인별로 구체적 액션 텍스트를 생성하고 점수 향상 예측치를 계산한다.

```python
impact_delta = (1 - similarity_score) × group_weight × 100 × 0.5
```

### 6단계 — 발표 구조 분석 (실험적 기능)

**역할 분류 CNN**: PPTX/PDF 슬라이드를 224×224 PIL 이미지로 렌더링한 뒤 EfficientNet-B3로 5가지 역할(표지·섹션헤더·본문·도표/시각자료·마무리)로 분류한다.

모델은 CLIP zero-shot 라벨로 생성한 약한 레이블(weak label)로 fine-tuning되었다 (val_acc = 26.2%).

**왜 HMM에서 규칙 기반으로 전환했는가?**
초기 설계는 CategoricalHMM으로 역할 시퀀스의 구조적 이상을 탐지하는 방식이었다. 그러나 CNN의 역할 분류 정확도가 26%에 그쳐 HMM 입력 시퀀스가 노이즈에 가까웠고, 정상 발표도 이상 점수가 100%에 달하는 문제가 발생했다. CNN 오류가 HMM 입력을 오염시켜 성능이 랜덤 수준으로 떨어진 cascading error였다.

이를 해결하기 위해 표지/마무리 위치 등 해석 가능한 규칙 기반 스코어러로 교체했다. 각 규칙은 CNN 예측에 독립적으로 작동하며, 단일 규칙 위반의 최대 페널티를 제한한다.

---

## 연구 배경

본 프로젝트는 다음 9개 Jupyter Notebook을 통해 연구·검증되었다 (Google Colab 기준).

| 노트북 | 내용 | 주요 산출물 |
|--------|------|------------|
| NB01 | 데이터 준비 (Zenodo10K 슬라이드 수집) | `weak_labels.csv` |
| NB02 | CNN 역할 분류기 (EfficientNet-B3) | `role_classifier_best.pt` |
| NB03 | HMM 구조 모델 (CategoricalHMM) | `hmm_model.pkl` |
| NB04 | 초기 평가 | — |
| NB05 | 평가 재설계 — 합성 구조 이상 벤치마크 | `synthetic_anomaly_benchmark.csv` |
| NB06 | CLIP zero-shot weak label → CNN 재학습 | `role_classifier_clip_best.pt` |
| NB07 | 베이스라인 비교 (B0~B4 vs 제안 방법) | `baseline_results.json` |
| NB08 | 민감도 분석 (contamination, PCA sweep) | `sensitivity_results.json` |
| NB09 | 통계적 유의성 검정 (Bootstrap CI, McNemar) | `stats_significance.json` |

### NB07 베이스라인 비교 결과 (합성 벤치마크 AUC)

합성 벤치마크는 정상 발표 시퀀스에 역할 순서 뒤섞기(shuffle_mild/severe), 표지 누락(no_cover), 마무리 누락(no_closing), 중복 섹션(dup_section) 등 5종류의 구조 이상을 주입하여 구성했다.

| 방법 | AUC | 비고 |
|------|-----|------|
| B0 Random | 0.517 | Sanity check |
| B1 Position-only | 0.493 | 덱 길이 편차만 사용 |
| B2 CLIP + IF | 0.470 | 랜덤보다 낮음 — 의미 임베딩은 역효과 |
| B3 DINOv2 + IF | 0.574 | 시각 구조 피처가 일부 유효 |
| **Proposed HMM** | **0.555** | 역할 시퀀스 모델링 |

B2가 랜덤보다 낮게 나온 이유는 CLIP이 슬라이드의 시각적 의미를 인코딩하기 때문이다. 역할 순서 이상은 내용이 아닌 구조의 문제이므로 의미 임베딩이 오히려 노이즈가 된다. DINOv2가 CLIP보다 나은 이유도 같은 맥락이다 — DINOv2는 시각 패턴을 더 직접적으로 인코딩한다.

HMM이 DINOv2+IF에 미치지 못한 원인은 CNN 역할 분류 정확도 한계(26%)에 의한 cascading error로 분석된다. CNN 품질 개선 시 유의미한 성능 향상이 예상된다.

---

## 알려진 한계

| 한계 | 설명 |
|------|------|
| PDF 색상 추출 불가 | pdfplumber는 텍스트 색상 정보를 제공하지 않아 색상 관련 이상은 PPTX에서만 탐지 |
| CNN 역할 분류 정확도 | 영어 학술 슬라이드 기반 학습으로 한국어 발표자료에 대한 정확도 낮음 (26%) |
| 발표 구조 분석 신뢰도 | CNN 정확도 한계로 역할 시퀀스 시각화는 참고용으로만 활용 권장 |
| 분석 결과 비영속성 | in-memory 저장으로 서버 재시작 시 모든 결과 소멸 |
| 최대 50장 제한 | 51장 이상인 경우 50장까지만 분석 |
| 썸네일 정확도 | Pillow 기반 근사 렌더링으로 실제 슬라이드 외관과 다를 수 있음 |
| 수정 파일 품질 | python-pptx 기반 자동 수정으로 복잡한 레이아웃에서 결과가 부정확할 수 있음 |

---

## 로컬 실행 방법

### 사전 요구사항

- Python 3.11+
- Node.js 18+
- pip

### 설치

```bash
# 1. 저장소 클론
git clone https://github.com/CH0I-HANNA/Dadeum.git
cd Dadeum

# 2. 백엔드 의존성 설치
cd backend
pip install -r requirements.txt

# 3. 프론트엔드 의존성 설치
cd ../frontend
npm install
```

### 실행

터미널 두 개를 열어서 각각 실행한다.

```bash
# 터미널 1 — 백엔드
cd backend
uvicorn app.main:app --reload
# → http://localhost:8000
# → API 문서: http://localhost:8000/docs

# 터미널 2 — 프론트엔드
cd frontend
npm run dev
# → http://localhost:5173
```

### 발표 구조 분석 활성화 (선택)

`backend/models/` 디렉토리에 아래 3개 파일을 배치하면 CNN+규칙 기반 발표 구조 분석이 활성화된다. 파일이 없으면 IF 기반 디자인 분석만 동작한다 (graceful fallback).

```
backend/models/
├── hmm_model.pkl               # NB03/05 산출물
├── hmm_thresholds.json         # NB03/05 산출물
└── role_classifier_clip_best.pt # NB06 산출물
```

### 테스트

```bash
cd backend
pytest
# → 162 passed
```

### 파일 제약

| 항목 | 제한 |
|------|------|
| 지원 형식 | `.pptx`, `.pdf` |
| 최대 파일 크기 | 50MB |
| 최대 슬라이드 수 | 50장 (초과 시 잘림) |
| 최소 슬라이드 수 | 3장 (미만 시 이상 탐지 미수행) |

---

## 프로젝트 구조

```
Dadeum/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── upload.py       # POST /api/upload
│   │   │   │                   # magic bytes 검증, 크기/확장자 제한
│   │   │   ├── analyze.py      # POST /api/analyze/{file_id}
│   │   │   │                   # GET  /api/result/{task_id}
│   │   │   ├── thumbnail.py    # GET  /api/thumbnail/{file_id}/{n}
│   │   │   │                   # PPTX: Pillow 렌더링, PDF: pymupdf 렌더링
│   │   │   ├── report.py       # GET  /api/report/{task_id} → PDF 문서
│   │   │   └── fix.py          # POST /api/fix/{file_id} → 수정 파일
│   │   │
│   │   ├── core/
│   │   │   ├── config.py       # UPLOAD_DIR, MODELS_DIR, 크기 제한 상수
│   │   │   ├── task_store.py   # in-memory {task_id → status/result}
│   │   │   │                   # threading.Lock으로 동시성 보호
│   │   │   └── exceptions.py   # PipelineError, ParseError
│   │   │
│   │   ├── models/
│   │   │   └── schemas.py      # Pydantic v2 스키마
│   │   │                       # AnalysisResult, OutlierSlide, SlideStats 등
│   │   │
│   │   ├── pipeline/           # AI 파이프라인 — 모든 추론 로직은 여기에만
│   │   │   ├── parser.py       # PPTX/PDF → SlideRaw
│   │   │   ├── extractor.py    # SlideRaw → SlideFeatureVector (59차원)
│   │   │   ├── scorer.py       # 일관성 점수 (CV 기반 cohesion)
│   │   │   ├── detector.py     # IsolationForest → OutlierResult[]
│   │   │   ├── explainer.py    # 코사인 유사도 기반 원인 분석
│   │   │   ├── recommender.py  # 수정 제안 + impact score 예측
│   │   │   ├── slide_renderer.py # PPTX/PDF → PIL Image[] (CNN 입력용)
│   │   │   ├── role_classifier.py # EfficientNet-B3 역할 분류
│   │   │   └── hmm_scorer.py   # 규칙 기반 구조 이상 점수
│   │   │
│   │   ├── services/
│   │   │   └── analysis_service.py  # 파이프라인 오케스트레이션
│   │   │                            # ThreadPoolExecutor (timeout 180s)
│   │   └── main.py
│   │
│   ├── models/                 # 학습된 모델 파일 (.gitignore)
│   │   ├── hmm_model.pkl
│   │   ├── hmm_thresholds.json
│   │   └── role_classifier_clip_best.pt
│   │
│   ├── tests/                  # pytest — 162개 테스트
│   │   ├── test_parser.py
│   │   ├── test_extractor.py
│   │   ├── test_detector.py
│   │   ├── test_scorer.py
│   │   ├── test_explainer.py
│   │   ├── test_recommender.py
│   │   ├── test_hmm_scorer.py
│   │   ├── test_role_classifier.py
│   │   ├── test_slide_renderer.py
│   │   └── test_api.py
│   │
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── UploadPage.tsx       # 드래그 앤 드롭 업로드
│       │   └── ResultPage.tsx       # 분석 결과 대시보드 (폴링 1.5s)
│       │
│       ├── components/
│       │   ├── score/
│       │   │   ├── ConsistencyScoreCard.tsx  # 일관성 점수 + 4개 축 바 차트
│       │   │   └── StructureScoreCard.tsx    # 발표 구조 점수 + 역할 흐름
│       │   ├── slides/
│       │   │   ├── SlideGrid.tsx       # 슬라이드 목록 (역할 뱃지 포함)
│       │   │   ├── SlideThumbnail.tsx  # 썸네일 + 이상/선택 표시
│       │   │   ├── SlidePreview.tsx    # 선택된 슬라이드 크게 보기
│       │   │   └── IssueFilter.tsx     # 폰트/색상/레이아웃/콘텐츠 필터
│       │   └── report/
│       │       ├── DetailPanel.tsx     # 원인 분석 + 수정 제안
│       │       ├── ComparePanel.tsx    # 두 슬라이드 통계 비교
│       │       ├── RootCauseList.tsx   # 원인 목록 (색상 스와치 포함)
│       │       └── RecommendationList.tsx # 수정 제안 목록
│       │
│       ├── hooks/
│       │   ├── useAnalysis.ts   # React Query 폴링, 타임아웃 120s, 단계별 메시지
│       │   └── useUpload.ts     # 업로드 + 분석 시작 + 리다이렉트
│       │
│       ├── services/
│       │   └── api.ts           # FastAPI 클라이언트 (axios)
│       │
│       └── types/
│           └── api.ts           # TypeScript 타입 (백엔드 스키마와 동기화)
│
├── notebooks/                   # 연구용 Jupyter Notebook (Google Colab)
│   ├── 01_data_preparation.ipynb
│   ├── 02_cnn_role_classifier.ipynb
│   ├── 03_hmm_structure.ipynb
│   ├── 04_evaluation.ipynb
│   ├── 05_eval_realign.ipynb
│   ├── 06_clip_weak_label.ipynb
│   ├── 07_baseline_suite.ipynb
│   ├── 08_sensitivity_analysis.ipynb
│   └── 09_stats_significance.ipynb
│
├── phases/                      # Harness 기반 개발 태스크 이력
│   ├── index.json               # 전체 phase 현황
│   └── {n}-{name}/              # 각 phase의 step 파일
│
└── docs/
    ├── ARCHITECTURE.md          # 시스템 아키텍처 상세
    ├── ADR.md                   # Architecture Decision Records
    ├── PRD.md                   # Product Requirements Document
    └── UI_GUIDE.md              # 디자인 시스템 가이드
```

---

## 라이선스

MIT
