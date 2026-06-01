# UI 디자인 가이드

## 디자인 원칙

1. **도구처럼 보여야 한다.** 마케팅 랜딩이 아니라 검수 작업을 하는 대시보드. 정보 밀도를 높이되 어수선하지 않게.
2. **결과가 주인공이다.** 슬라이드 썸네일과 점수가 화면의 중심. UI 크롬(헤더, 사이드바)은 최소화.
3. **문제는 명확하게, 설명은 간결하게.** 이상 슬라이드는 시각적으로 즉시 구분되어야 한다. 원인 설명은 1~3줄 이내.

---

## AI 슬롭 안티패턴 — 하지 마라

| 금지 사항 | 이유 |
|-----------|------|
| `backdrop-filter: blur()` | glass morphism은 AI 템플릿의 가장 흔한 징후 |
| gradient-text (배경 그라데이션 텍스트) | AI가 만든 SaaS 랜딩의 1번 특징 |
| "Powered by AI" 배지 | 기능이 아니라 장식. 사용자에게 가치 없음 |
| box-shadow 글로우 애니메이션 | 네온 글로우 = AI 슬롭 |
| 보라/인디고 브랜드 색상 | "AI = 보라색" 클리셰 |
| 모든 카드에 동일한 `rounded-2xl` | 균일한 둥근 모서리는 템플릿 느낌 |
| 배경 gradient orb (`blur-3xl` 원형) | 모든 AI 랜딩 페이지에 있는 장식 |

---

## 색상

### 배경
| 용도 | 값 |
|------|------|
| 페이지 | `#0a0a0a` |
| 카드/패널 | `#111111` |
| 호버/선택 영역 | `#1a1a1a` |

### 텍스트
| 용도 | 값 |
|------|------|
| 주 텍스트 | `text-white` (`#ffffff`) |
| 본문 | `text-neutral-300` (`#d4d4d4`) |
| 보조 | `text-neutral-400` (`#a3a3a3`) |
| 비활성/레이블 | `text-neutral-500` (`#737373`) |

### 포인트 / 시맨틱 색상
| 용도 | 값 | 사용처 |
|------|----|--------|
| 포인트 (브랜드) | `#f59e0b` (amber-400) | 점수 강조, 이상 슬라이드 테두리 |
| 정상 | `#22c55e` (green-500) | 일관성 높은 슬라이드 |
| 경고 | `#f59e0b` (amber-400) | 중간 이상 슬라이드 |
| 위험 | `#ef4444` (red-500) | 높은 이상 슬라이드 |
| 구분선/테두리 | `#262626` (neutral-800) | 카드 테두리 |

---

## 컴포넌트

### 카드
```
rounded-lg bg-[#111111] border border-neutral-800 p-4
```

### 이상 슬라이드 썸네일 (경고)
```
rounded-lg border-2 border-amber-400 ring-1 ring-amber-400/20
```

### 버튼
```
Primary : rounded-md bg-white text-black text-sm font-medium px-4 py-2 hover:bg-neutral-200
Secondary: rounded-md border border-neutral-700 text-neutral-300 text-sm px-4 py-2 hover:border-neutral-500
```

### 점수 배지 (Consistency Score)
```
큰 숫자: text-5xl font-bold text-white tabular-nums
단위:    text-sm text-neutral-500 ml-1
```

### 원인 태그 (Root Cause Label)
```
rounded-sm bg-neutral-800 text-neutral-300 text-xs px-2 py-1
```

---

## 레이아웃

- 전체 너비: `max-w-6xl mx-auto`
- 결과 페이지: 좌측 슬라이드 그리드 (2/3) + 우측 상세 패널 (1/3)
- 정렬: 좌측 정렬 기본. 숫자/점수만 우측 정렬.
- 간격: 카드 간 `gap-3`, 섹션 간 `space-y-6`

---

## 타이포그래피

| 용도 | 스타일 |
|------|--------|
| 페이지 제목 | `text-2xl font-semibold text-white` |
| 섹션 제목 | `text-sm font-medium text-neutral-400 uppercase tracking-wider` |
| 카드 제목 | `text-sm font-medium text-white` |
| 본문/설명 | `text-sm text-neutral-300 leading-relaxed` |
| 강조 수치 | `text-5xl font-bold text-white tabular-nums` |

---

## 애니메이션

- 허용: `transition-colors duration-150` (hover 색상 전환)
- 허용: 결과 로딩 후 카드 fade-in (`opacity-0 → opacity-100, duration-300`)
- 금지: 그 외 모든 애니메이션 (슬라이드, 바운스, 회전 등)

---

## 아이콘

- Lucide React 사용, `strokeWidth={1.5}`
- 아이콘 컨테이너(둥근 배경 박스)로 감싸지 않는다
- 텍스트와 함께 쓸 때는 `size={14}` 또는 `size={16}` 고정

