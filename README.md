# 다듬 (Dadeum)

> AI 기반 프레젠테이션 슬라이드 디자인 일관성 분석 서비스
> **AI 기반 프레젠테이션 슬라이드 디자인 일관성 분석 서비스**
>
> PPTX / PDF를 업로드하면 30초 내에 어떤 슬라이드가 왜 튀는지를 수치와 근거로 알려준다.

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
## 목차

| | 섹션 | 대상 독자 |
|--|------|---------|
| 1 | [데모 & 스크린샷](#1-데모--스크린샷) | 모두 |
| 2 | [왜 다듬인가](#2-왜-다듬인가) | 모두 |
| 3 | [주요 기능](#3-주요-기능) | 모두 |
| 4 | [기술 스택 & 아키텍처](#4-기술-스택--아키텍처) | 개발자 |
| 5 | [기술적 도전 과제](#5-기술적-도전-과제) | 개발자 / 면접관 |
| 6 | [AI 파이프라인 상세](#6-ai-파이프라인-상세) | 개발자 / 연구자 |
| 7 | [연구 배경](#7-연구-배경) | 연구자 |
| 8 | [한계와 향후 연구 과제](#8-한계와-향후-연구-과제) | 모두 |
| 9 | [로컬 실행 방법](#9-로컬-실행-방법) | 개발자 |
| 10 | [프로젝트 구조](#10-프로젝트-구조) | 개발자 |

50~100장 규모의 발표자료를 만들다 보면 어느 순간 폰트가 슬쩍 바뀌거나, 특정 슬라이드만 배경색이 다르거나, 텍스트 여백이 들쭉날쭉해진다. 여러 명이 나눠 만든 팀플 발표자료, 오래된 템플릿을 재활용한 IR Deck, 마감 직전에 급히 추가한 슬라이드들이 대표적인 사례다.
---

## 1. 데모 & 스크린샷

> 🎬 **[데모 영상 보기](데모_영상_링크)** — 파일 업로드부터 분석 결과 확인까지 전체 흐름 (약 2분)

<br>

**업로드 화면** — PPTX 또는 PDF를 드래그 앤 드롭하거나 클릭하여 선택

![업로드 화면](docs/screenshots/01_upload.png)

<br>

**분석 결과 — 일관성 점수 & 발표 구조** — 전체 점수와 4개 축 세부 점수, 발표 역할 흐름

![분석 결과](docs/screenshots/02_score_cards.png)

<br>

**이상 슬라이드 탐지 & 원인 분석** — 이상 슬라이드 강조(주황 테두리) + 원인 및 수정 제안

![이상 슬라이드](docs/screenshots/03_outlier_detail.png)

<br>

**슬라이드 비교 모드** — 두 슬라이드를 나란히 놓고 통계 차이 비교

![슬라이드 비교](docs/screenshots/04_compare.png)

> 📁 스크린샷 파일 위치: `docs/screenshots/`

---

## 2. 왜 다듬인가

### 문제: 사람 눈으로는 못 잡는 불일치

50장짜리 발표자료에서 3장만 폰트가 다르다고 해보자. 슬라이드를 한 장씩 넘기며 이걸 발견하는 사람은 거의 없다. **사람은 바로 앞 슬라이드와 비교하지, 전체 50장을 동시에 비교하지 않는다.**

불일치가 쌓이는 전형적인 상황:
- 팀원이 각자 만든 슬라이드를 하나로 합칠 때
- 오래된 템플릿 위에 새 슬라이드를 덧붙일 때
- 마감 직전 다른 소스에서 복사·붙여넣기 할 때

그 결과는 작지 않다.

| 상황 | 청중이 받는 인상 |
|------|----------------|
| 자기소개 PPT의 폰트가 슬라이드마다 다름 | 세심하지 못하다 |
| IR Deck 3장만 색상 톤이 다름 | 브랜드 일관성 없다, 전문성 부족 |
| 학위 발표 중 레이아웃이 흐트러짐 | 내용보다 형식이 눈에 띈다 |

### 해결: 덱 전체를 하나의 집합으로 분석

다듬은 슬라이드를 개별적으로 평가하지 않는다. **덱 전체의 분포를 먼저 파악하고, 그 분포에서 벗어나는 슬라이드를 찾는다.**

각 슬라이드를 59차원 피처 벡터(폰트·색상·레이아웃·콘텐츠)로 변환한 뒤 Isolation Forest로 이탈 점수를 계산한다. 이상이 탐지되면 어느 피처 그룹에서 가장 크게 벗어났는지를 분석하여 구체적인 근거와 수정 제안을 함께 제시한다.

```
슬라이드 8번  이상 점수 0.97

  원인:  색상 불일치
         기대값: RGB(255, 255, 255)  ← 나머지 47장의 주 색상
         실제값: RGB(20, 20, 30)     ← 이 슬라이드만 어두운 계열

  제안:  주 색상을 다른 슬라이드와 통일하세요  (+10.6점 예상)
```

**이런 불일치를 사람 눈으로 전체 슬라이드를 훑으며 잡아내는 건 번거롭고 실수가 잦다.** 특히 "50장 중 3장만 폰트가 다른" 경우처럼 미묘한 불일치는 발표 직전까지 발견하지 못하는 경우도 많다.
### 기존 방법과의 비교

다듬은 PPTX/PDF를 업로드하면 슬라이드 전체의 타이포그래피·색상·레이아웃·콘텐츠를 자동으로 분석하여 **어떤 슬라이드가 왜 튀는지**를 수치와 근거와 함께 알려준다.
| 방법 | 덱 전체 비교 | 근거 제시 | 기존 파일 지원 |
|------|:-----------:|:--------:|:------------:|
| 직접 눈으로 검수 | ❌ | ❌ | ✅ |
| PowerPoint Designer | ❌ (슬라이드 단위) | △ | ✅ |
| Canva / Figma | ❌ | ❌ | ❌ |
| 디자이너 의뢰 | △ | △ (주관적) | ✅ |
| **다듬** | **✅** | **✅ (수치)** | **✅** |

### 주요 사용자

| 페르소나 | 상황 | 핵심 니즈 |
|----------|------|-----------|
| 취업 준비생 | 포트폴리오/자기소개 PPT 마감 전날 | 어떤 슬라이드가 이상한지 빠르게 파악 |
| 대학생 | 팀플 발표자료 합치기 후 검수 | 각자 만든 슬라이드의 통일감 확인 |
| 스타트업 | IR Deck 투자자 발표 전 | 브랜드 일관성 + 전문성 점검 |
| 페르소나 | 상황 | 다듬으로 얻는 것 |
|----------|------|----------------|
| 취업 준비생 | 포트폴리오 PPT 마감 전날 | 이상한 슬라이드 + 이유를 30초 안에 파악 |
| 대학생 | 팀플 슬라이드 합치기 후 검수 | 통일감 깨는 슬라이드를 수치로 특정 |
| 스타트업 | IR Deck 투자자 발표 전 | 브랜드 일관성 + 발표 흐름 구조 점검 |

---

## 기존 방법과의 차별점
## 3. 주요 기능

### 기존 방법의 한계
### 🎯 일관성 점수 (Consistency Score)

| 방법 | 한계 |
|------|------|
| **직접 눈으로 검수** | 슬라이드 수가 많을수록 놓치는 불일치가 늘어남. 50장 중 3장만 다른 폰트는 거의 발견 못함 |
| **PowerPoint Designer** | 개별 슬라이드 디자인 제안에 그침. 덱 전체의 일관성을 분석하지 않음 |
| **Canva / Figma** | 처음부터 그 도구로 만든 파일에만 적용 가능. 기존 PPTX/PDF는 지원 안 함 |
| **디자이너에게 의뢰** | 비용 발생, 시간 소요. 피드백이 주관적이고 근거가 불명확한 경우 많음 |
| **AI 이미지 분석 서비스** | 슬라이드를 독립된 이미지로 분석. 덱 전체의 집합적 특성을 반영하지 못함 |
발표 전체를 4개 축으로 **0~100점** 채점한다. 점수가 낮을수록 특정 슬라이드가 전체 경향에서 크게 벗어나 있다.

| 축 | 가중치 | 측정 내용 |
|----|:------:|----------|
| 폰트 (Typography) | 30% | 폰트 종류 분포, 크기 통계, Bold/Italic 비율 |
| 색상 (Color) | 30% | 지배 색상 RGB, 배경색, 채도·밝기 |
| 레이아웃 (Layout) | 25% | 텍스트·이미지 면적, 정렬 비율, 4방향 여백 |
| 콘텐츠 (Content) | 15% | 단어 수, 불릿 수, 텍스트 밀도 |

"색상 55점 / 폰트 89점" → 수정 우선순위가 색상임을 바로 알 수 있다.

---

### 🔍 이상 슬라이드 탐지

**Isolation Forest** 비지도 학습으로 전체 덱에서 상대적으로 튀는 슬라이드를 자동 검출한다. 사전 레이블이 전혀 필요 없다 — 같은 덱 안에서 상대적 이탈을 측정한다.

탐지 민감도는 슬라이드 수에 따라 자동 조정된다.

### 다듬의 차별화 포인트
```
 5장 이하  →  contamination 0.15
15장 이하  →  contamination 0.20
15장 초과  →  contamination 0.25
```

---

**1. 덱 전체를 하나의 집합으로 분석한다**
### 🧠 원인 분석 & 수정 제안

기존 도구들은 슬라이드를 개별적으로 "이 슬라이드가 예쁜가?"를 묻지만, 다듬은 "이 슬라이드가 나머지와 얼마나 다른가?"를 묻는다. 전체 50장의 분포를 기준으로 특정 슬라이드의 이탈도를 측정하는 것이 핵심이다.
이상 슬라이드를 찾은 뒤, 어떤 피처 그룹에서 가장 크게 벗어났는지를 코사인 유사도로 분석한다. 결과는 "기대값 vs 실제값" 형태로 제시된다.

수정 제안과 함께 점수 향상 예측치도 계산한다.

```
제안: 폰트 크기 36pt → 24pt로 조정 권장     (+3.2점 예상)
제안: 주 색상을 다른 슬라이드와 통일하세요  (+10.6점 예상)
──────────────────────────────────────────
모두 적용 시  77점 → 최대 92점 향상 가능
```

**2. 정량적 근거를 제공한다**
수정 제안이 반영된 **PPTX/PDF 파일 다운로드**도 지원한다.

"이 슬라이드가 이상하다"는 말 대신 구체적인 수치를 제시한다.
- `폰트 불일치 — 기대: Pretendard (전체의 94%) / 실제: Times New Roman`
- `색상 불일치 — 기대: RGB(255,255,255) / 실제: RGB(20,20,30)`
- `레이아웃 불일치 — 기대: 텍스트 비율 51% / 실제: 텍스트 비율 15%`
---

디자인 감각이 없어도 왜 이상한지를 이해하고 수정할 수 있다.
### 📐 슬라이드 비교 모드

**3. 레이블 없이 동작한다**
두 슬라이드를 나란히 놓고 폰트·크기·텍스트 영역·단어 수·역할을 수치로 비교한다. 차이가 있는 항목은 자동 강조 표시된다. 팀원이 서로 다른 스타일로 만든 슬라이드를 맞출 때 유용하다.

Isolation Forest 기반 비지도 학습으로, 어떤 PPTX/PDF든 별도 학습이나 사전 설정 없이 즉시 분석할 수 있다. "정상 슬라이드"가 무엇인지 모델이 미리 알 필요가 없다 — 같은 덱 안에서 상대적으로 튀는 슬라이드를 찾는다.
---

**4. 기존 파일 형식을 그대로 받는다**
### 📊 발표 구조 분석 *(실험적 기능)*

PPTX/PDF를 업로드하면 된다. 특정 도구로 다시 만들거나 변환할 필요가 없다.
> ⚠️ **현재 참고용 기능이다.** CNN 역할 분류 정확도(26%) 한계로 신뢰도가 낮다. 자세한 내용은 [한계와 향후 연구 과제](#8-한계와-향후-연구-과제)를 참고.

**5. 59차원 피처로 사람 눈이 놓치는 불일치를 잡는다**
CNN으로 각 슬라이드의 역할(표지·섹션·본문·도표·마무리)을 분류하고, 역할 흐름의 이상 여부를 규칙 기반으로 판단한다.

폰트 크기 평균/분산/중앙값, 색상 채도·밝기, 텍스트 정렬 비율, 여백 4방향 등을 정밀하게 비교한다. "뭔가 어색한데 왜 그런지 모르겠다"는 느낌을 수치로 설명한다.
```
정상:  표지 → 섹션 → 본문 → 본문 → 마무리
이상:  본문 → 마무리 → 표지 → 섹션 → 본문
              ↑ 마무리가 중간에 등장
```

---

## 주요 기능
### 📄 PDF 보고서

### 디자인 일관성 분석
분석 결과 전체(일관성 점수, 이상 슬라이드 목록, 원인·수정 제안)를 PDF로 다운로드한다. 팀 공유, 디자이너 의뢰, 포트폴리오 기록용으로 활용할 수 있다.

**Consistency Score** — 슬라이드 전체를 4개 축으로 0~100점 채점
---

## 4. 기술 스택 & 아키텍처

| 축 | 분석 내용 |
|----|----------|
| 폰트 (30%) | 폰트 종류, 크기 분포, bold/italic 비율 |
| 색상 (30%) | 지배 색상, 배경색, 채도/밝기 일관성 |
| 레이아웃 (25%) | 텍스트·이미지 면적 비율, 정렬, 여백 |
| 콘텐츠 (15%) | 단어 수, 불릿 수, 텍스트 밀도 |
### 기술 스택

**이상 슬라이드 탐지** — Isolation Forest 기반 비지도 학습. 레이블 없이 "전체에서 상대적으로 튀는 슬라이드"를 자동 검출한다.
**Frontend**

**원인 분석** — 이상 슬라이드에 대해 "기대값 vs 실제값"을 feature 그룹별로 제시한다.
- 예: `폰트 불일치 — 기대: Pretendard / 실제: Times New Roman`
- 예: `색상 불일치 — 기대: RGB(255,255,255) / 실제: RGB(20,20,30)`
| | 라이브러리 | 역할 |
|--|-----------|------|
| UI | React 18 + TypeScript (strict) | 컴포넌트 |
| 빌드 | Vite | 개발 서버 & 번들링 |
| 스타일 | TailwindCSS v3 | 유틸리티 CSS |
| 상태 | React Query | 서버 상태 + 1.5초 폴링 |
| 라우팅 | React Router v6 | SPA 라우팅 |
| HTTP | Axios | API 클라이언트 |

**수정 제안** — 각 원인에 대한 구체적 액션과 수정 후 예상 점수 향상치를 함께 제공한다.
**Backend**

### 발표 구조 분석 (실험적)
| | 라이브러리 | 역할 |
|--|-----------|------|
| API | FastAPI + Pydantic v2 | REST API + 스키마 검증 |
| PPTX | python-pptx | 파싱 & 수정 |
| PDF | pdfplumber + pymupdf | 텍스트 추출 & 렌더링 |
| 보고서 | fpdf2 | PDF 생성 |

EfficientNet-B3 CNN으로 각 슬라이드를 표지·섹션헤더·본문·도표·마무리로 분류하고, 역할 흐름의 이상 여부를 규칙 기반으로 판단한다.
**AI Pipeline**

> ⚠️ CNN이 영어 학술 슬라이드(Zenodo10K)로 학습되어 한국어 발표자료에 대한 정확도가 낮다. 이 기능은 참고용으로만 활용하는 것을 권장한다.
| | 라이브러리 | 역할 |
|--|-----------|------|
| 이상 탐지 | scikit-learn | Isolation Forest |
| CNN | PyTorch + timm | EfficientNet-B3 역할 분류 |
| 이미지 | Pillow + NumPy | 피처 추출 & 렌더링 |

---

### 부가 기능
### 아키텍처

- **슬라이드 비교 모드** — 두 슬라이드를 나란히 놓고 통계 비교
- **이슈 필터** — 폰트/색상/레이아웃/콘텐츠 유형별 이상 슬라이드 필터링
- **PDF 보고서** — 분석 결과 전체를 PDF 문서로 다운로드
- **수정 파일 다운로드** — 수정 제안이 반영된 PPTX/PDF 파일 생성
```
┌──────────────────────────────────────────────────────────────┐
│                  Browser  (React + Vite)                      │
│                                                               │
│  UploadPage                  ResultPage                       │
│  └─ 드래그 앤 드롭            ├─ ConsistencyScoreCard         │
│                               ├─ StructureScoreCard (실험)    │
│                               ├─ SlideGrid + 역할 뱃지        │
│                               ├─ DetailPanel (원인/수정 제안) │
│                               └─ ComparePanel                 │
└─────────────────────┬────────────────────────────────────────┘
                      │  HTTP / REST
┌─────────────────────▼────────────────────────────────────────┐
│                  FastAPI  (uvicorn)                           │
│                                                               │
│  POST /api/upload              ← magic bytes 검증             │
│  POST /api/analyze/{file_id}   ← 202 즉시 반환 + 백그라운드   │
│  GET  /api/result/{task_id}    ← 클라이언트 1.5초 폴링        │
│  GET  /api/thumbnail/{id}/{n}  ← in-memory 캐싱              │
│  GET  /api/report/{task_id}    ← fpdf2 PDF 생성              │
│  POST /api/fix/{file_id}       ← 수정 파일 다운로드           │
│                                                               │
│  BackgroundTasks → ThreadPoolExecutor (timeout 180s)         │
│  In-memory task store  {task_id → status/result}             │
└─────────────────────┬────────────────────────────────────────┘
                      │
┌─────────────────────▼────────────────────────────────────────┐
│                  AI Pipeline                                  │
│                                                               │
│  parser.py       PPTX/PDF → SlideRaw                         │
│  extractor.py    SlideRaw → FeatureVector (59차원)            │
│  scorer.py       FeatureVector[] → ConsistencyScore          │
│  detector.py     FeatureVector[] → OutlierResult[]           │
│  explainer.py    OutlierResult → RootCause[]                 │
│  recommender.py  RootCause[] → Recommendation[]              │
│                                                               │
│  slide_renderer.py  PPTX/PDF → PIL Image[]   (CNN용)         │
│  role_classifier.py PIL Image[] → role_sequence              │
│  hmm_scorer.py      role_sequence → anomaly_score            │
└──────────────────────────────────────────────────────────────┘
```

---

## 기술 스택
## 5. 기술적 도전 과제

> 단순 API 연결이나 라이브러리 사용을 넘어, 실제로 고민하고 설계 결정을 내린 문제들이다.

---

### Frontend
### Challenge 1. "일관성"을 어떻게 수치로 만드는가

| 라이브러리 | 역할 |
|-----------|------|
| React 18 + TypeScript | UI, strict mode |
| Vite | 빌드 도구 |
| TailwindCSS v3 | 유틸리티 퍼스트 스타일링 |
| React Query (@tanstack/react-query) | 서버 상태 관리, 1.5초 폴링 |
| React Router v6 | 클라이언트 라우팅 |
| Axios | HTTP 클라이언트 |
**문제**: "이 발표가 일관적이다"는 말은 직관적이지만, 0~100점으로 표현하려면 구체적인 정의가 필요하다.

### Backend
**접근**: 각 피처의 **변동계수(CV)** 를 일관성 지표로 사용했다. 슬라이드 간 변동이 작을수록 일관적이다.

| 라이브러리 | 역할 |
|-----------|------|
| FastAPI | 비동기 REST API |
| Pydantic v2 | 스키마 검증 및 직렬화 |
| python-pptx | PPTX 파싱 및 수정 |
| pdfplumber | PDF 텍스트/레이아웃 추출 |
| pymupdf (fitz) | PDF 썸네일 렌더링 |
| fpdf2 | PDF 보고서 생성 |
| Pillow | PPTX 썸네일 렌더링 |
```
CV(d)       = std(d) / (mean(d) + ε)
cohesion(d) = 1 / (1 + CV(d))     →  0~1, 높을수록 일관적
score       = 100 × Σ (cohesion_group × weight_group)
```

### AI Pipeline
**설계 과정의 함정**: 처음엔 그룹 전체를 flatten하여 단일 CV를 계산했다. Typography(29차원)가 Content(4차원)를 7배 압도해서 Typography 점수가 전체를 결정해버렸다. 차원별로 cohesion을 계산하고 평균을 내는 방식으로 수정해 각 피처가 동등하게 기여하도록 했다.

| 라이브러리 | 역할 |
|-----------|------|
| scikit-learn | Isolation Forest 이상 탐지 |
| PyTorch + timm | EfficientNet-B3 역할 분류 CNN |
| NumPy | 피처 추출 수치 연산 |
**스케일 문제**: 폰트 크기를 pt 단위 그대로 쓰면 `font_size_mean ≈ 24`가 되어 0~1 범위의 다른 피처보다 24배 크다. 모든 폰트 크기 피처를 `pt / 72`로 정규화했다.

---

## 아키텍처
### Challenge 2. 레이블 없이 이상 슬라이드를 어떻게 탐지하는가

**문제**: "이상한 슬라이드"의 정의가 발표마다 다르다. 사전 레이블 데이터 구축이 불가능하다.

**왜 지도학습이 불가능한가**: 빨간 배경이 어떤 발표에서는 이상치지만, 다른 발표에서는 의도된 디자인이다. 이상은 절대적 기준이 아니라 같은 덱 안에서의 상대적 이탈이다.

**Isolation Forest 선택 이유**: "이상치는 정상 데이터보다 고립시키기 쉽다"는 직관에 기반한다. 레이블이 전혀 필요 없고, 슬라이드 수가 10~50장처럼 적어도 동작한다.

---

### Challenge 3. Isolation Forest는 "왜 이상한지"를 알려주지 않는다

**문제**: IF는 이상 점수를 반환하지만 어떤 피처 때문인지는 알려주지 않는다. 사용자는 "슬라이드 3번이 이상합니다"만으로는 수정을 할 수 없다.

**해결**: 별도의 Explainer 모듈을 설계했다. 이상 슬라이드의 피처 벡터와 전체 중앙값을 그룹별 **코사인 유사도**로 비교하여 가장 이탈된 그룹을 원인으로 특정한다. 그룹이 특정되면 그 안에서 어떤 값이 다른지를 사람이 읽을 수 있는 텍스트로 변환한다.

---

### Challenge 4. 발표 흐름을 어떻게 모델링하는가 — HMM과 Cascading Error

**설계 의도**: 발표는 역할 시퀀스 데이터다. 표지 다음에는 섹션이 올 가능성이 높은 마르코프 성질을 활용하여 **CategoricalHMM**으로 발표 역할 전이 패턴을 학습했다.

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
관측값:  [0, 1, 2, 2, 4]   ← CNN이 예측한 역할 시퀀스
anomaly_score = clip((mean - ll/len) / std / 3.0, 0, 1)
```

합성 벤치마크(NB07)에서 AUC 0.555를 달성했다.

**발견한 문제 — Cascading Error**: HMM 자체는 정상 동작했으나 CNN 정확도가 26%여서 입력 시퀀스가 노이즈였다. 정상 발표도 마무리(4)가 중간에 여러 번 예측되면 HMM이 로그 우도를 낮게 계산해 이상 점수 1.0이 나왔다. HMM 코드의 버그가 아니라 **입력 데이터의 품질 문제**였다는 걸 발견하기까지 시간이 걸렸다.

**대응**: HMM 모델은 보존하되 서비스에서는 규칙 기반 스코어러로 임시 교체. CNN 정확도 개선 시 재활성화할 수 있도록 `HMMScorer.load()` 인터페이스를 유지했다.

---

### Challenge 5. 학습 데이터가 없다 — Weak Supervision

**문제**: CNN 학습을 위한 "이 슬라이드는 표지다" 같은 레이블이 없다. 수천 장을 직접 레이블링하는 건 불가능했다.

**접근**: CLIP의 zero-shot 능력을 활용했다. "a title slide", "a closing slide" 같은 텍스트 프롬프트와 슬라이드 이미지의 유사도를 계산하여 약한 레이블(weak label)을 자동 생성했다.

**한계**: 두 단계의 약한 신호(CLIP 레이블 → CNN)가 누적되어 최종 정확도가 26%에 그쳤다. **Weak Supervision의 한계는 레이블 생성 단계에서 이미 결정된다.**

---

## AI 파이프라인 상세
### Challenge 6. 30초 걸리는 분석을 어떻게 비동기로 처리하는가

**FastAPI의 함정**: `BackgroundTasks`에 `async def`를 등록하면 event loop에서 실행된다. CPU-bound 코드(scikit-learn, NumPy)를 `async def`로 실행하면 다른 모든 요청이 블로킹된다. 반드시 `def`(sync)로 정의해 ThreadPoolExecutor에서 실행해야 한다.

### 1단계 — 파싱
**Timeout 구현**: `signal.alarm`은 Unix 전용이고 멀티스레드에서 main thread에서만 처리된다. `ThreadPoolExecutor` + `future.result(timeout=180)`으로 타임아웃을 감지했다.

```python
with ThreadPoolExecutor(max_workers=1) as executor:
    future = executor.submit(run_analysis, file_path, file_id)
    result = future.result(timeout=180)  # TimeoutError → task error 처리
```

`parser.py`가 PPTX/PDF를 읽어 슬라이드별 `SlideRaw` 구조체로 변환한다.
---

- **PPTX**: python-pptx로 TextElement(텍스트·폰트·색상·위치), ImageElement(위치·크기), 배경색을 추출한다.
- **PDF**: pdfplumber로 단어별 위치·폰트명·크기를 추출한다. 색상 정보는 추출 불가(흑색으로 처리).
- 슬라이드 수 상한: 50장 (초과분 무시)
## 6. AI 파이프라인 상세

### 2단계 — 피처 추출 (59차원)
### 피처 추출 (59차원)

`extractor.py`의 `SlideFeatureExtractor`가 `SlideRaw` → `SlideFeatureVector`로 변환한다. 모든 값은 0~1로 정규화된다.
`SlideFeatureExtractor`가 각 슬라이드를 59차원 벡터로 변환한다. 모든 값은 0~1 정규화.

```
Typography (index 0~28, 29차원)
  0~19  dominant_font_one_hot  — 19개 알려진 폰트 + Other 빈도 벡터
  20    font_size_mean          — pt / 72 (정규화)
  0~19  폰트 빈도 one-hot  — 19개 알려진 폰트 + Other
  20    font_size_mean      — pt / 72
 21    font_size_std
  22~24 font_size_min/max/median
  22~24 font_size_min / max / median
 25    bold_ratio
 26    italic_ratio
  27    font_variety_count      — 사용 폰트 종류 수 / 5
  27    font_variety_count  — 폰트 종류 수 / 5
 28    line_spacing_normalized

Color (index 29~43, 15차원)
@@ -231,24 +386,22 @@ Layout (index 44~54, 11차원)
 44    text_area_ratio
 45    image_area_ratio
 46    whitespace_ratio
  47~49 alignment_left/center/right
  50~53 margin_top/bottom/left/right
  47~49 alignment_left / center / right
  50~53 margin_top / bottom / left / right
 54    element_count

Content (index 55~58, 4차원)
  55    word_count_normalized   — 단어 수 / 100
  56    bullet_count_normalized — 불릿 수 / 20
  55    word_count_normalized    — 단어 수 / 100
  56    bullet_count_normalized  — 불릿 수 / 20
 57    text_image_ratio
 58    sentence_count_normalized
```

### 3단계 — 일관성 점수

슬라이드 집합 전체에서 각 차원의 변동계수(CV)를 계산하여 일관성(cohesion)으로 변환한다.
### 일관성 점수 계산

```python
CV(d)       = std(d) / (mean(d) + ε)
cohesion(d) = 1 / (1 + CV(d))          # 0~1, 높을수록 일관적
cohesion(d) = 1 / (1 + CV(d))
score       = 100 × (
mean(cohesion for d in typography) × 0.30 +
mean(cohesion for d in color)      × 0.30 +
@@ -257,153 +410,144 @@ score       = 100 × (
)
```

그룹을 flatten하여 단일 CV를 계산하면 차원 수가 많은 그룹(typography 29차원)이 단일 값인 차원(bold_ratio)을 압도하므로, **차원별 cohesion을 평균내는 방식**을 채택했다.

### 4단계 — 이상 탐지: Isolation Forest

**왜 Isolation Forest인가?**
레이블 데이터 없이 즉시 적용 가능한 비지도 학습 모델이 필요했다. 슬라이드 수가 10~50장으로 적어도 안정적으로 동작하며, 어떤 PPTX든 별도 학습 없이 바로 쓸 수 있다.

contamination은 슬라이드 수에 따라 동적으로 결정된다.
### Isolation Forest contamination 동적 조정

```python
def _dynamic_contamination(n: int) -> float:
    if n <= 5:  return 0.15
    if n <= 15: return 0.20
    if n <= 5:   return 0.15
    if n <= 15:  return 0.20
return 0.25
```

이상 점수는 decision_function 값을 0~1로 반전 정규화한다 (높을수록 이상).

### 5단계 — 원인 분석 및 수정 제안

`explainer.py`는 이상 슬라이드의 feature 벡터와 전체 중앙값을 그룹별로 코사인 유사도로 비교하여 유사도가 낮은 그룹을 원인으로 특정한다.

`recommender.py`는 원인별로 구체적 액션 텍스트를 생성하고 점수 향상 예측치를 계산한다.
### HMM 구조 이상 탐지

```python
impact_delta = (1 - similarity_score) × group_weight × 100 × 0.5
ll            = hmm_model.score(seq) / len(seq)   # per-observation 로그 우도
z             = (thresholds['mean'] - ll) / (thresholds['std'] + ε)
anomaly_score = clip(z / 3.0, 0.0, 1.0)
```

### 6단계 — 발표 구조 분석 (실험적 기능)

**역할 분류 CNN**: PPTX/PDF 슬라이드를 224×224 PIL 이미지로 렌더링한 뒤 EfficientNet-B3로 5가지 역할(표지·섹션헤더·본문·도표/시각자료·마무리)로 분류한다.

모델은 CLIP zero-shot 라벨로 생성한 약한 레이블(weak label)로 fine-tuning되었다 (val_acc = 26.2%).

**왜 HMM에서 규칙 기반으로 전환했는가?**
초기 설계는 CategoricalHMM으로 역할 시퀀스의 구조적 이상을 탐지하는 방식이었다. 그러나 CNN의 역할 분류 정확도가 26%에 그쳐 HMM 입력 시퀀스가 노이즈에 가까웠고, 정상 발표도 이상 점수가 100%에 달하는 문제가 발생했다. CNN 오류가 HMM 입력을 오염시켜 성능이 랜덤 수준으로 떨어진 cascading error였다.

이를 해결하기 위해 표지/마무리 위치 등 해석 가능한 규칙 기반 스코어러로 교체했다. 각 규칙은 CNN 예측에 독립적으로 작동하며, 단일 규칙 위반의 최대 페널티를 제한한다.
학습된 모델: `backend/models/hmm_model.pkl` (NB03/05 산출물)

---

## 연구 배경
## 7. 연구 배경

본 프로젝트는 다음 9개 Jupyter Notebook을 통해 연구·검증되었다 (Google Colab 기준).
총 9개의 Jupyter Notebook으로 연구·검증했다 (Google Colab 기준).

| 노트북 | 내용 | 주요 산출물 |
|--------|------|------------|
| NB01 | 데이터 준비 (Zenodo10K 슬라이드 수집) | `weak_labels.csv` |
| NB01 | 데이터 준비 (Zenodo10K) | `weak_labels.csv` |
| NB02 | CNN 역할 분류기 (EfficientNet-B3) | `role_classifier_best.pt` |
| NB03 | HMM 구조 모델 (CategoricalHMM) | `hmm_model.pkl` |
| NB04 | 초기 평가 | — |
| NB05 | 평가 재설계 — 합성 구조 이상 벤치마크 | `synthetic_anomaly_benchmark.csv` |
| NB06 | CLIP zero-shot weak label → CNN 재학습 | `role_classifier_clip_best.pt` |
| NB07 | 베이스라인 비교 (B0~B4 vs 제안 방법) | `baseline_results.json` |
| NB05 | 평가 재설계 + 합성 벤치마크 구축 | `synthetic_anomaly_benchmark.csv` |
| NB06 | CLIP weak label → CNN 재학습 | `role_classifier_clip_best.pt` |
| NB07 | 베이스라인 비교 (B0~B4 vs HMM) | `baseline_results.json` |
| NB08 | 민감도 분석 (contamination, PCA sweep) | `sensitivity_results.json` |
| NB09 | 통계적 유의성 검정 (Bootstrap CI, McNemar) | `stats_significance.json` |

### NB07 베이스라인 비교 결과 (합성 벤치마크 AUC)
### NB07 베이스라인 비교 (합성 벤치마크 AUC)

합성 벤치마크는 정상 발표 시퀀스에 역할 순서 뒤섞기(shuffle_mild/severe), 표지 누락(no_cover), 마무리 누락(no_closing), 중복 섹션(dup_section) 등 5종류의 구조 이상을 주입하여 구성했다.
합성 벤치마크는 정상 시퀀스에 역할 순서 뒤섞기, 표지 누락, 마무리 누락, 중복 섹션 등 5종류 이상을 주입하여 구성했다.

| 방법 | AUC | 비고 |
|------|-----|------|
|------|:---:|------|
| B0 Random | 0.517 | Sanity check |
| B1 Position-only | 0.493 | 덱 길이 편차만 사용 |
| B2 CLIP + IF | 0.470 | 랜덤보다 낮음 — 의미 임베딩은 역효과 |
| B2 CLIP + IF | 0.470 | **랜덤보다 낮음** — 의미 임베딩은 역효과 |
| B3 DINOv2 + IF | 0.574 | 시각 구조 피처가 일부 유효 |
| **Proposed HMM** | **0.555** | 역할 시퀀스 모델링 |

B2가 랜덤보다 낮게 나온 이유는 CLIP이 슬라이드의 시각적 의미를 인코딩하기 때문이다. 역할 순서 이상은 내용이 아닌 구조의 문제이므로 의미 임베딩이 오히려 노이즈가 된다. DINOv2가 CLIP보다 나은 이유도 같은 맥락이다 — DINOv2는 시각 패턴을 더 직접적으로 인코딩한다.
> B2(CLIP)가 랜덤보다 낮은 이유: CLIP은 슬라이드의 의미 내용을 인코딩한다. 구조 이상은 내용이 아니라 순서의 문제이므로 의미 임베딩이 오히려 노이즈가 된다. HMM이 DINOv2에 미치지 못한 이유는 CNN cascading error(Challenge 4 참고).

---

## 8. 한계와 향후 연구 과제

HMM이 DINOv2+IF에 미치지 못한 원인은 CNN 역할 분류 정확도 한계(26%)에 의한 cascading error로 분석된다. CNN 품질 개선 시 유의미한 성능 향상이 예상된다.
### 미완성 기능: 발표 구조 분석

발표 구조 분석은 **설계는 완성됐지만 서비스 품질 기준에 도달하지 못한 미완성 기능**이다.

**원래 설계**: CNN으로 역할을 분류 → CategoricalHMM으로 시퀀스 이상 탐지. 합성 벤치마크 AUC 0.555 달성.

**현재 한계**: CNN 정확도 26% → HMM 입력 시퀀스가 노이즈 → 정상 발표도 이상 점수 1.0 → cascading error.

**현재 대응**: 규칙 기반 스코어러로 임시 교체. HMM 모델과 인터페이스는 보존.

**해결 조건 및 향후 방향**:

| 접근 | 필요한 것 | 예상 효과 |
|------|----------|----------|
| 한국어 발표자료 수동 레이블링 | 500~1000장 직접 annotation | CNN 60%+ → HMM 재활성화 가능 |
| VLM 자동 레이블링 | GPT-4V 등으로 역할 자동 분류 | 데이터 수집 비용 절감 |
| CLIP 한국어 프롬프트 개선 | 도메인 특화 프롬프트 설계 | Weak label 품질 향상 |

---

## 알려진 한계
### 기타 알려진 한계

| 한계 | 설명 |
|------|------|
| PDF 색상 추출 불가 | pdfplumber는 텍스트 색상 정보를 제공하지 않아 색상 관련 이상은 PPTX에서만 탐지 |
| CNN 역할 분류 정확도 | 영어 학술 슬라이드 기반 학습으로 한국어 발표자료에 대한 정확도 낮음 (26%) |
| 발표 구조 분석 신뢰도 | CNN 정확도 한계로 역할 시퀀스 시각화는 참고용으로만 활용 권장 |
| 분석 결과 비영속성 | in-memory 저장으로 서버 재시작 시 모든 결과 소멸 |
| 최대 50장 제한 | 51장 이상인 경우 50장까지만 분석 |
| 썸네일 정확도 | Pillow 기반 근사 렌더링으로 실제 슬라이드 외관과 다를 수 있음 |
| 수정 파일 품질 | python-pptx 기반 자동 수정으로 복잡한 레이아웃에서 결과가 부정확할 수 있음 |
| 한계 | 원인 | 영향 |
|------|------|------|
| PDF 색상 추출 불가 | pdfplumber가 색상 미제공 | PDF 업로드 시 색상 이상 탐지 불가 |
| 분석 결과 비영속성 | in-memory 저장 | 서버 재시작 시 결과 소멸 |
| 썸네일 근사 렌더링 | python-pptx 이미지 렌더링 미지원 | 실제 슬라이드와 외관이 다를 수 있음 |
| 수정 파일 품질 | 폰트명·색상 교체만 지원 | 복잡한 레이아웃·애니메이션 처리 불가 |
| 최대 50장 제한 | 성능 상한 | 51장 이상은 잘려서 분석 |

---

## 로컬 실행 방법
## 9. 로컬 실행 방법

### 사전 요구사항

- Python 3.11+
- Node.js 18+
- pip

### 설치

```bash
# 1. 저장소 클론
# 저장소 클론
git clone https://github.com/CH0I-HANNA/Dadeum.git
cd Dadeum

# 2. 백엔드 의존성 설치
cd backend
pip install -r requirements.txt
# 백엔드
cd backend && pip install -r requirements.txt

# 3. 프론트엔드 의존성 설치
cd ../frontend
npm install
# 프론트엔드
cd ../frontend && npm install
```

### 실행

터미널 두 개를 열어서 각각 실행한다.

```bash
# 터미널 1 — 백엔드
cd backend
uvicorn app.main:app --reload
# → http://localhost:8000
# → API 문서: http://localhost:8000/docs
# → http://localhost:8000  |  API 문서: http://localhost:8000/docs

# 터미널 2 — 프론트엔드
cd frontend
npm run dev
# → http://localhost:5173
```

### 테스트

```bash
cd backend
pytest        # 162 passed
```

### 발표 구조 분석 활성화 (선택)

`backend/models/` 디렉토리에 아래 3개 파일을 배치하면 CNN+규칙 기반 발표 구조 분석이 활성화된다. 파일이 없으면 IF 기반 디자인 분석만 동작한다 (graceful fallback).
`backend/models/`에 아래 파일을 배치하면 CNN + 규칙 기반 구조 분석이 활성화된다. 없으면 IF 파이프라인만 동작한다.

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
├── hmm_model.pkl                 ← NB03/05 산출물
├── hmm_thresholds.json           ← NB03/05 산출물
└── role_classifier_clip_best.pt  ← NB06 산출물
```

### 파일 제약
@@ -417,118 +561,61 @@ pytest

---

## 프로젝트 구조
## 10. 프로젝트 구조

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
│   │   ├── api/                  # FastAPI 라우터
│   │   │   ├── upload.py         # POST /api/upload
│   │   │   ├── analyze.py        # POST /api/analyze, GET /api/result
│   │   │   ├── thumbnail.py      # GET /api/thumbnail (fitz 렌더링)
│   │   │   ├── report.py         # GET /api/report → PDF
│   │   │   └── fix.py            # POST /api/fix → 수정 파일
│   │   ├── core/
│   │   │   ├── config.py       # UPLOAD_DIR, MODELS_DIR, 크기 제한 상수
│   │   │   ├── task_store.py   # in-memory {task_id → status/result}
│   │   │   │                   # threading.Lock으로 동시성 보호
│   │   │   └── exceptions.py   # PipelineError, ParseError
│   │   │
│   │   │   ├── config.py         # 상수 (UPLOAD_DIR, MODELS_DIR 등)
│   │   │   ├── task_store.py     # in-memory {task_id → status/result}
│   │   │   └── exceptions.py
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
│   │   │   └── schemas.py        # Pydantic v2 스키마
│   │   ├── pipeline/             # 모든 AI 추론 로직은 여기에만
│   │   │   ├── parser.py         # PPTX/PDF → SlideRaw
│   │   │   ├── extractor.py      # SlideRaw → FeatureVector (59차원)
│   │   │   ├── scorer.py         # ConsistencyScore (CV 기반)
│   │   │   ├── detector.py       # IsolationForest → OutlierResult[]
│   │   │   ├── explainer.py      # 코사인 유사도 기반 원인 분석
│   │   │   ├── recommender.py    # 수정 제안 + impact score
│   │   │   ├── slide_renderer.py # PPTX/PDF → PIL Image[] (CNN용)
│   │   │   ├── role_classifier.py # EfficientNet-B3 역할 분류
│   │   │   └── hmm_scorer.py   # 규칙 기반 구조 이상 점수
│   │   │
│   │   │   └── hmm_scorer.py     # 규칙 기반 구조 이상 점수
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
│   ├── models/                   # 학습된 모델 파일 (.gitignore)
│   ├── tests/                    # pytest (162개)
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── UploadPage.tsx       # 드래그 앤 드롭 업로드
│       │   └── ResultPage.tsx       # 분석 결과 대시보드 (폴링 1.5s)
│       │
│       │   ├── UploadPage.tsx
│       │   └── ResultPage.tsx
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
│       │   ├── score/            # ConsistencyScoreCard, StructureScoreCard
│       │   ├── slides/           # SlideGrid, SlideThumbnail, SlidePreview
│       │   └── report/           # DetailPanel, ComparePanel, RootCauseList
│       ├── hooks/                # useAnalysis (폴링), useUpload
│       ├── services/api.ts       # FastAPI 클라이언트
│       └── types/api.ts          # TypeScript 타입 (백엔드 스키마 동기화)
│
├── notebooks/                    # 연구용 Jupyter Notebook (NB01~NB09)
├── phases/                       # Harness 개발 태스크 이력
└── docs/
    ├── ARCHITECTURE.md          # 시스템 아키텍처 상세
    ├── ADR.md                   # Architecture Decision Records
    ├── PRD.md                   # Product Requirements Document
    └── UI_GUIDE.md              # 디자인 시스템 가이드
    ├── ARCHITECTURE.md
    ├── ADR.md
    ├── PRD.md
    └── screenshots/
```

---
<br>

**업로드 화면** — PPTX 또는 PDF를 드래그 앤 드롭하거나 클릭하여 선택

![업로드 화면](docs/screenshots/01_upload.png)

<br>

**분석 결과 — 일관성 점수 & 발표 구조** — 전체 점수와 4개 축 세부 점수, 발표 역할 흐름

![분석 결과](docs/screenshots/02_score_cards.png)

<br>

**이상 슬라이드 탐지 & 원인 분석** — 이상 슬라이드 강조(주황 테두리) + 원인 및 수정 제안

![이상 슬라이드](docs/screenshots/03_outlier_detail.png)

<br>

**슬라이드 비교 모드** — 두 슬라이드를 나란히 놓고 통계 차이 비교

![슬라이드 비교](docs/screenshots/04_compare.png)

> 📁 스크린샷 파일 위치: `docs/screenshots/`

---

## 2. 왜 다듬인가

### 문제: 사람 눈으로는 못 잡는 불일치

50장짜리 발표자료에서 3장만 폰트가 다르다고 해보자. 슬라이드를 한 장씩 넘기며 이걸 발견하는 사람은 거의 없다. **사람은 바로 앞 슬라이드와 비교하지, 전체 50장을 동시에 비교하지 않는다.**

불일치가 쌓이는 전형적인 상황:
- 팀원이 각자 만든 슬라이드를 하나로 합칠 때
- 오래된 템플릿 위에 새 슬라이드를 덧붙일 때
- 마감 직전 다른 소스에서 복사·붙여넣기 할 때

그 결과는 작지 않다.

| 상황 | 청중이 받는 인상 |
|------|----------------|
| 자기소개 PPT의 폰트가 슬라이드마다 다름 | 세심하지 못하다 |
| IR Deck 3장만 색상 톤이 다름 | 브랜드 일관성 없다, 전문성 부족 |
| 학위 발표 중 레이아웃이 흐트러짐 | 내용보다 형식이 눈에 띈다 |

### 해결: 덱 전체를 하나의 집합으로 분석

다듬은 슬라이드를 개별적으로 평가하지 않는다. **덱 전체의 분포를 먼저 파악하고, 그 분포에서 벗어나는 슬라이드를 찾는다.**

각 슬라이드를 59차원 피처 벡터(폰트·색상·레이아웃·콘텐츠)로 변환한 뒤 Isolation Forest로 이탈 점수를 계산한다. 이상이 탐지되면 어느 피처 그룹에서 가장 크게 벗어났는지를 분석하여 구체적인 근거와 수정 제안을 함께 제시한다.

```
슬라이드 8번  이상 점수 0.97

  원인:  색상 불일치
         기대값: RGB(255, 255, 255)  ← 나머지 47장의 주 색상
         실제값: RGB(20, 20, 30)     ← 이 슬라이드만 어두운 계열

  제안:  주 색상을 다른 슬라이드와 통일하세요  (+10.6점 예상)
```

### 기존 방법과의 비교

| 방법 | 덱 전체 비교 | 근거 제시 | 기존 파일 지원 |
|------|:-----------:|:--------:|:------------:|
| 직접 눈으로 검수 | ❌ | ❌ | ✅ |
| PowerPoint Designer | ❌ (슬라이드 단위) | △ | ✅ |
| Canva / Figma | ❌ | ❌ | ❌ |
| 디자이너 의뢰 | △ | △ (주관적) | ✅ |
| **다듬** | **✅** | **✅ (수치)** | **✅** |

### 주요 사용자

| 페르소나 | 상황 | 다듬으로 얻는 것 |
|----------|------|----------------|
| 취업 준비생 | 포트폴리오 PPT 마감 전날 | 이상한 슬라이드 + 이유를 30초 안에 파악 |
| 대학생 | 팀플 슬라이드 합치기 후 검수 | 통일감 깨는 슬라이드를 수치로 특정 |
| 스타트업 | IR Deck 투자자 발표 전 | 브랜드 일관성 + 발표 흐름 구조 점검 |

---

## 3. 주요 기능

### 🎯 일관성 점수 (Consistency Score)

발표 전체를 4개 축으로 **0~100점** 채점한다. 점수가 낮을수록 특정 슬라이드가 전체 경향에서 크게 벗어나 있다.

| 축 | 가중치 | 측정 내용 |
|----|:------:|----------|
| 폰트 (Typography) | 30% | 폰트 종류 분포, 크기 통계, Bold/Italic 비율 |
| 색상 (Color) | 30% | 지배 색상 RGB, 배경색, 채도·밝기 |
| 레이아웃 (Layout) | 25% | 텍스트·이미지 면적, 정렬 비율, 4방향 여백 |
| 콘텐츠 (Content) | 15% | 단어 수, 불릿 수, 텍스트 밀도 |

"색상 55점 / 폰트 89점" → 수정 우선순위가 색상임을 바로 알 수 있다.

---

### 🔍 이상 슬라이드 탐지

**Isolation Forest** 비지도 학습으로 전체 덱에서 상대적으로 튀는 슬라이드를 자동 검출한다. 사전 레이블이 전혀 필요 없다 — 같은 덱 안에서 상대적 이탈을 측정한다.

탐지 민감도는 슬라이드 수에 따라 자동 조정된다.

```
 5장 이하  →  contamination 0.15
15장 이하  →  contamination 0.20
15장 초과  →  contamination 0.25
```

---

### 🧠 원인 분석 & 수정 제안

이상 슬라이드를 찾은 뒤, 어떤 피처 그룹에서 가장 크게 벗어났는지를 코사인 유사도로 분석한다. 결과는 "기대값 vs 실제값" 형태로 제시된다.

수정 제안과 함께 점수 향상 예측치도 계산한다.

```
제안: 폰트 크기 36pt → 24pt로 조정 권장     (+3.2점 예상)
제안: 주 색상을 다른 슬라이드와 통일하세요  (+10.6점 예상)
──────────────────────────────────────────
모두 적용 시  77점 → 최대 92점 향상 가능
```

수정 제안이 반영된 **PPTX/PDF 파일 다운로드**도 지원한다.

---

### 📐 슬라이드 비교 모드

두 슬라이드를 나란히 놓고 폰트·크기·텍스트 영역·단어 수·역할을 수치로 비교한다. 차이가 있는 항목은 자동 강조 표시된다. 팀원이 서로 다른 스타일로 만든 슬라이드를 맞출 때 유용하다.

---

### 📊 발표 구조 분석 *(실험적 기능)*

> ⚠️ **현재 참고용 기능이다.** CNN 역할 분류 정확도(26%) 한계로 신뢰도가 낮다. 자세한 내용은 [한계와 향후 연구 과제](#8-한계와-향후-연구-과제)를 참고.

CNN으로 각 슬라이드의 역할(표지·섹션·본문·도표·마무리)을 분류하고, 역할 흐름의 이상 여부를 규칙 기반으로 판단한다.

```
정상:  표지 → 섹션 → 본문 → 본문 → 마무리
이상:  본문 → 마무리 → 표지 → 섹션 → 본문
              ↑ 마무리가 중간에 등장
```

---

### 📄 PDF 보고서

분석 결과 전체(일관성 점수, 이상 슬라이드 목록, 원인·수정 제안)를 PDF로 다운로드한다. 팀 공유, 디자이너 의뢰, 포트폴리오 기록용으로 활용할 수 있다.

---

## 4. 기술 스택 & 아키텍처

### 기술 스택

**Frontend**

| | 라이브러리 | 역할 |
|--|-----------|------|
| UI | React 18 + TypeScript (strict) | 컴포넌트 |
| 빌드 | Vite | 개발 서버 & 번들링 |
| 스타일 | TailwindCSS v3 | 유틸리티 CSS |
| 상태 | React Query | 서버 상태 + 1.5초 폴링 |
| 라우팅 | React Router v6 | SPA 라우팅 |
| HTTP | Axios | API 클라이언트 |

**Backend**

| | 라이브러리 | 역할 |
|--|-----------|------|
| API | FastAPI + Pydantic v2 | REST API + 스키마 검증 |
| PPTX | python-pptx | 파싱 & 수정 |
| PDF | pdfplumber + pymupdf | 텍스트 추출 & 렌더링 |
| 보고서 | fpdf2 | PDF 생성 |

**AI Pipeline**

| | 라이브러리 | 역할 |
|--|-----------|------|
| 이상 탐지 | scikit-learn | Isolation Forest |
| CNN | PyTorch + timm | EfficientNet-B3 역할 분류 |
| 이미지 | Pillow + NumPy | 피처 추출 & 렌더링 |

---

### 아키텍처

```
┌──────────────────────────────────────────────────────────────┐
│                  Browser  (React + Vite)                      │
│                                                               │
│  UploadPage                  ResultPage                       │
│  └─ 드래그 앤 드롭            ├─ ConsistencyScoreCard         │
│                               ├─ StructureScoreCard (실험)    │
│                               ├─ SlideGrid + 역할 뱃지        │
│                               ├─ DetailPanel (원인/수정 제안) │
│                               └─ ComparePanel                 │
└─────────────────────┬────────────────────────────────────────┘
                      │  HTTP / REST
┌─────────────────────▼────────────────────────────────────────┐
│                  FastAPI  (uvicorn)                           │
│                                                               │
│  POST /api/upload              ← magic bytes 검증             │
│  POST /api/analyze/{file_id}   ← 202 즉시 반환 + 백그라운드   │
│  GET  /api/result/{task_id}    ← 클라이언트 1.5초 폴링        │
│  GET  /api/thumbnail/{id}/{n}  ← in-memory 캐싱              │
│  GET  /api/report/{task_id}    ← fpdf2 PDF 생성              │
│  POST /api/fix/{file_id}       ← 수정 파일 다운로드           │
│                                                               │
│  BackgroundTasks → ThreadPoolExecutor (timeout 180s)         │
│  In-memory task store  {task_id → status/result}             │
└─────────────────────┬────────────────────────────────────────┘
                      │
┌─────────────────────▼────────────────────────────────────────┐
│                  AI Pipeline                                  │
│                                                               │
│  parser.py       PPTX/PDF → SlideRaw                         │
│  extractor.py    SlideRaw → FeatureVector (59차원)            │
│  scorer.py       FeatureVector[] → ConsistencyScore          │
│  detector.py     FeatureVector[] → OutlierResult[]           │
│  explainer.py    OutlierResult → RootCause[]                 │
│  recommender.py  RootCause[] → Recommendation[]              │
│                                                               │
│  slide_renderer.py  PPTX/PDF → PIL Image[]   (CNN용)         │
│  role_classifier.py PIL Image[] → role_sequence              │
│  hmm_scorer.py      role_sequence → anomaly_score            │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. 기술적 도전 과제

> 단순 API 연결이나 라이브러리 사용을 넘어, 실제로 고민하고 설계 결정을 내린 문제들이다.

---

### Challenge 1. "일관성"을 어떻게 수치로 만드는가

**문제**: "이 발표가 일관적이다"는 말은 직관적이지만, 0~100점으로 표현하려면 구체적인 정의가 필요하다.

**접근**: 각 피처의 **변동계수(CV)** 를 일관성 지표로 사용했다. 슬라이드 간 변동이 작을수록 일관적이다.

```
CV(d)       = std(d) / (mean(d) + ε)
cohesion(d) = 1 / (1 + CV(d))     →  0~1, 높을수록 일관적
score       = 100 × Σ (cohesion_group × weight_group)
```

**설계 과정의 함정**: 처음엔 그룹 전체를 flatten하여 단일 CV를 계산했다. Typography(29차원)가 Content(4차원)를 7배 압도해서 Typography 점수가 전체를 결정해버렸다. 차원별로 cohesion을 계산하고 평균을 내는 방식으로 수정해 각 피처가 동등하게 기여하도록 했다.

**스케일 문제**: 폰트 크기를 pt 단위 그대로 쓰면 `font_size_mean ≈ 24`가 되어 0~1 범위의 다른 피처보다 24배 크다. 모든 폰트 크기 피처를 `pt / 72`로 정규화했다.

---

### Challenge 2. 레이블 없이 이상 슬라이드를 어떻게 탐지하는가

**문제**: "이상한 슬라이드"의 정의가 발표마다 다르다. 사전 레이블 데이터 구축이 불가능하다.

**왜 지도학습이 불가능한가**: 빨간 배경이 어떤 발표에서는 이상치지만, 다른 발표에서는 의도된 디자인이다. 이상은 절대적 기준이 아니라 같은 덱 안에서의 상대적 이탈이다.

**Isolation Forest 선택 이유**: "이상치는 정상 데이터보다 고립시키기 쉽다"는 직관에 기반한다. 레이블이 전혀 필요 없고, 슬라이드 수가 10~50장처럼 적어도 동작한다.

---

### Challenge 3. Isolation Forest는 "왜 이상한지"를 알려주지 않는다

**문제**: IF는 이상 점수를 반환하지만 어떤 피처 때문인지는 알려주지 않는다. 사용자는 "슬라이드 3번이 이상합니다"만으로는 수정을 할 수 없다.

**해결**: 별도의 Explainer 모듈을 설계했다. 이상 슬라이드의 피처 벡터와 전체 중앙값을 그룹별 **코사인 유사도**로 비교하여 가장 이탈된 그룹을 원인으로 특정한다. 그룹이 특정되면 그 안에서 어떤 값이 다른지를 사람이 읽을 수 있는 텍스트로 변환한다.

---

### Challenge 4. 발표 흐름을 어떻게 모델링하는가 — HMM과 Cascading Error

**설계 의도**: 발표는 역할 시퀀스 데이터다. 표지 다음에는 섹션이 올 가능성이 높은 마르코프 성질을 활용하여 **CategoricalHMM**으로 발표 역할 전이 패턴을 학습했다.

```
관측값:  [0, 1, 2, 2, 4]   ← CNN이 예측한 역할 시퀀스
anomaly_score = clip((mean - ll/len) / std / 3.0, 0, 1)
```

합성 벤치마크(NB07)에서 AUC 0.555를 달성했다.

**발견한 문제 — Cascading Error**: HMM 자체는 정상 동작했으나 CNN 정확도가 26%여서 입력 시퀀스가 노이즈였다. 정상 발표도 마무리(4)가 중간에 여러 번 예측되면 HMM이 로그 우도를 낮게 계산해 이상 점수 1.0이 나왔다. HMM 코드의 버그가 아니라 **입력 데이터의 품질 문제**였다는 걸 발견하기까지 시간이 걸렸다.

**대응**: HMM 모델은 보존하되 서비스에서는 규칙 기반 스코어러로 임시 교체. CNN 정확도 개선 시 재활성화할 수 있도록 `HMMScorer.load()` 인터페이스를 유지했다.

---

### Challenge 5. 학습 데이터가 없다 — Weak Supervision

**문제**: CNN 학습을 위한 "이 슬라이드는 표지다" 같은 레이블이 없다. 수천 장을 직접 레이블링하는 건 불가능했다.

**접근**: CLIP의 zero-shot 능력을 활용했다. "a title slide", "a closing slide" 같은 텍스트 프롬프트와 슬라이드 이미지의 유사도를 계산하여 약한 레이블(weak label)을 자동 생성했다.

**한계**: 두 단계의 약한 신호(CLIP 레이블 → CNN)가 누적되어 최종 정확도가 26%에 그쳤다. **Weak Supervision의 한계는 레이블 생성 단계에서 이미 결정된다.**

---

### Challenge 6. 30초 걸리는 분석을 어떻게 비동기로 처리하는가

**FastAPI의 함정**: `BackgroundTasks`에 `async def`를 등록하면 event loop에서 실행된다. CPU-bound 코드(scikit-learn, NumPy)를 `async def`로 실행하면 다른 모든 요청이 블로킹된다. 반드시 `def`(sync)로 정의해 ThreadPoolExecutor에서 실행해야 한다.

**Timeout 구현**: `signal.alarm`은 Unix 전용이고 멀티스레드에서 main thread에서만 처리된다. `ThreadPoolExecutor` + `future.result(timeout=180)`으로 타임아웃을 감지했다.

```python
with ThreadPoolExecutor(max_workers=1) as executor:
    future = executor.submit(run_analysis, file_path, file_id)
    result = future.result(timeout=180)  # TimeoutError → task error 처리
```

---

## 6. AI 파이프라인 상세

### 피처 추출 (59차원)

`SlideFeatureExtractor`가 각 슬라이드를 59차원 벡터로 변환한다. 모든 값은 0~1 정규화.

```
Typography (index 0~28, 29차원)
  0~19  폰트 빈도 one-hot  — 19개 알려진 폰트 + Other
  20    font_size_mean      — pt / 72
  21    font_size_std
  22~24 font_size_min / max / median
  25    bold_ratio
  26    italic_ratio
  27    font_variety_count  — 폰트 종류 수 / 5
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
  47~49 alignment_left / center / right
  50~53 margin_top / bottom / left / right
  54    element_count

Content (index 55~58, 4차원)
  55    word_count_normalized    — 단어 수 / 100
  56    bullet_count_normalized  — 불릿 수 / 20
  57    text_image_ratio
  58    sentence_count_normalized
```

### 일관성 점수 계산

```python
CV(d)       = std(d) / (mean(d) + ε)
cohesion(d) = 1 / (1 + CV(d))
score       = 100 × (
    mean(cohesion for d in typography) × 0.30 +
    mean(cohesion for d in color)      × 0.30 +
    mean(cohesion for d in layout)     × 0.25 +
    mean(cohesion for d in content)    × 0.15
)
```

### Isolation Forest contamination 동적 조정

```python
def _dynamic_contamination(n: int) -> float:
    if n <= 5:   return 0.15
    if n <= 15:  return 0.20
    return 0.25
```

### HMM 구조 이상 탐지

```python
ll            = hmm_model.score(seq) / len(seq)   # per-observation 로그 우도
z             = (thresholds['mean'] - ll) / (thresholds['std'] + ε)
anomaly_score = clip(z / 3.0, 0.0, 1.0)
```

학습된 모델: `backend/models/hmm_model.pkl` (NB03/05 산출물)

---

## 7. 연구 배경

총 9개의 Jupyter Notebook으로 연구·검증했다 (Google Colab 기준).

| 노트북 | 내용 | 주요 산출물 |
|--------|------|------------|
| NB01 | 데이터 준비 (Zenodo10K) | `weak_labels.csv` |
| NB02 | CNN 역할 분류기 (EfficientNet-B3) | `role_classifier_best.pt` |
| NB03 | HMM 구조 모델 (CategoricalHMM) | `hmm_model.pkl` |
| NB04 | 초기 평가 | — |
| NB05 | 평가 재설계 + 합성 벤치마크 구축 | `synthetic_anomaly_benchmark.csv` |
| NB06 | CLIP weak label → CNN 재학습 | `role_classifier_clip_best.pt` |
| NB07 | 베이스라인 비교 (B0~B4 vs HMM) | `baseline_results.json` |
| NB08 | 민감도 분석 (contamination, PCA sweep) | `sensitivity_results.json` |
| NB09 | 통계적 유의성 검정 (Bootstrap CI, McNemar) | `stats_significance.json` |

### NB07 베이스라인 비교 (합성 벤치마크 AUC)

합성 벤치마크는 정상 시퀀스에 역할 순서 뒤섞기, 표지 누락, 마무리 누락, 중복 섹션 등 5종류 이상을 주입하여 구성했다.

| 방법 | AUC | 비고 |
|------|:---:|------|
| B0 Random | 0.517 | Sanity check |
| B1 Position-only | 0.493 | 덱 길이 편차만 사용 |
| B2 CLIP + IF | 0.470 | **랜덤보다 낮음** — 의미 임베딩은 역효과 |
| B3 DINOv2 + IF | 0.574 | 시각 구조 피처가 일부 유효 |
| **Proposed HMM** | **0.555** | 역할 시퀀스 모델링 |

> B2(CLIP)가 랜덤보다 낮은 이유: CLIP은 슬라이드의 의미 내용을 인코딩한다. 구조 이상은 내용이 아니라 순서의 문제이므로 의미 임베딩이 오히려 노이즈가 된다. HMM이 DINOv2에 미치지 못한 이유는 CNN cascading error(Challenge 4 참고).

---

## 8. 한계와 향후 연구 과제

### 미완성 기능: 발표 구조 분석

발표 구조 분석은 **설계는 완성됐지만 서비스 품질 기준에 도달하지 못한 미완성 기능**이다.

**원래 설계**: CNN으로 역할을 분류 → CategoricalHMM으로 시퀀스 이상 탐지. 합성 벤치마크 AUC 0.555 달성.

**현재 한계**: CNN 정확도 26% → HMM 입력 시퀀스가 노이즈 → 정상 발표도 이상 점수 1.0 → cascading error.

**현재 대응**: 규칙 기반 스코어러로 임시 교체. HMM 모델과 인터페이스는 보존.

**해결 조건 및 향후 방향**:

| 접근 | 필요한 것 | 예상 효과 |
|------|----------|----------|
| 한국어 발표자료 수동 레이블링 | 500~1000장 직접 annotation | CNN 60%+ → HMM 재활성화 가능 |
| VLM 자동 레이블링 | GPT-4V 등으로 역할 자동 분류 | 데이터 수집 비용 절감 |
| CLIP 한국어 프롬프트 개선 | 도메인 특화 프롬프트 설계 | Weak label 품질 향상 |

---

### 기타 알려진 한계

| 한계 | 원인 | 영향 |
|------|------|------|
| PDF 색상 추출 불가 | pdfplumber가 색상 미제공 | PDF 업로드 시 색상 이상 탐지 불가 |
| 분석 결과 비영속성 | in-memory 저장 | 서버 재시작 시 결과 소멸 |
| 썸네일 근사 렌더링 | python-pptx 이미지 렌더링 미지원 | 실제 슬라이드와 외관이 다를 수 있음 |
| 수정 파일 품질 | 폰트명·색상 교체만 지원 | 복잡한 레이아웃·애니메이션 처리 불가 |
| 최대 50장 제한 | 성능 상한 | 51장 이상은 잘려서 분석 |

---

## 9. 로컬 실행 방법

### 사전 요구사항

- Python 3.11+
- Node.js 18+

### 설치

```bash
# 저장소 클론
git clone https://github.com/CH0I-HANNA/Dadeum.git
cd Dadeum

# 백엔드
cd backend && pip install -r requirements.txt

# 프론트엔드
cd ../frontend && npm install
```

### 실행

```bash
# 터미널 1 — 백엔드
cd backend
uvicorn app.main:app --reload
# → http://localhost:8000  |  API 문서: http://localhost:8000/docs

# 터미널 2 — 프론트엔드
cd frontend
npm run dev
# → http://localhost:5173
```

### 테스트

```bash
cd backend
pytest        # 162 passed
```

### 발표 구조 분석 활성화 (선택)

`backend/models/`에 아래 파일을 배치하면 CNN + 규칙 기반 구조 분석이 활성화된다. 없으면 IF 파이프라인만 동작한다.

```
backend/models/
├── hmm_model.pkl                 ← NB03/05 산출물
├── hmm_thresholds.json           ← NB03/05 산출물
└── role_classifier_clip_best.pt  ← NB06 산출물
```

### 파일 제약

| 항목 | 제한 |
|------|------|
| 지원 형식 | `.pptx`, `.pdf` |
| 최대 파일 크기 | 50MB |
| 최대 슬라이드 수 | 50장 (초과 시 잘림) |
| 최소 슬라이드 수 | 3장 (미만 시 이상 탐지 미수행) |

---

## 10. 프로젝트 구조

```
Dadeum/
├── backend/
│   ├── app/
│   │   ├── api/                  # FastAPI 라우터
│   │   │   ├── upload.py         # POST /api/upload
│   │   │   ├── analyze.py        # POST /api/analyze, GET /api/result
│   │   │   ├── thumbnail.py      # GET /api/thumbnail (fitz 렌더링)
│   │   │   ├── report.py         # GET /api/report → PDF
│   │   │   └── fix.py            # POST /api/fix → 수정 파일
│   │   ├── core/
│   │   │   ├── config.py         # 상수 (UPLOAD_DIR, MODELS_DIR 등)
│   │   │   ├── task_store.py     # in-memory {task_id → status/result}
│   │   │   └── exceptions.py
│   │   ├── models/
│   │   │   └── schemas.py        # Pydantic v2 스키마
│   │   ├── pipeline/             # 모든 AI 추론 로직은 여기에만
│   │   │   ├── parser.py         # PPTX/PDF → SlideRaw
│   │   │   ├── extractor.py      # SlideRaw → FeatureVector (59차원)
│   │   │   ├── scorer.py         # ConsistencyScore (CV 기반)
│   │   │   ├── detector.py       # IsolationForest → OutlierResult[]
│   │   │   ├── explainer.py      # 코사인 유사도 기반 원인 분석
│   │   │   ├── recommender.py    # 수정 제안 + impact score
│   │   │   ├── slide_renderer.py # PPTX/PDF → PIL Image[] (CNN용)
│   │   │   ├── role_classifier.py # EfficientNet-B3 역할 분류
│   │   │   └── hmm_scorer.py     # 규칙 기반 구조 이상 점수
│   │   ├── services/
│   │   │   └── analysis_service.py  # 파이프라인 오케스트레이션
│   │   └── main.py
│   ├── models/                   # 학습된 모델 파일 (.gitignore)
│   ├── tests/                    # pytest (162개)
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── UploadPage.tsx
│       │   └── ResultPage.tsx
│       ├── components/
│       │   ├── score/            # ConsistencyScoreCard, StructureScoreCard
│       │   ├── slides/           # SlideGrid, SlideThumbnail, SlidePreview
│       │   └── report/           # DetailPanel, ComparePanel, RootCauseList
│       ├── hooks/                # useAnalysis (폴링), useUpload
│       ├── services/api.ts       # FastAPI 클라이언트
│       └── types/api.ts          # TypeScript 타입 (백엔드 스키마 동기화)
│
├── notebooks/                    # 연구용 Jupyter Notebook (NB01~NB09)
├── phases/                       # Harness 개발 태스크 이력
└── docs/
    ├── ARCHITECTURE.md
    ├── ADR.md
    ├── PRD.md
    └── screenshots/
```

---

## 라이선스

MIT
