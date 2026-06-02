# Step 2: frontend-ux

## 읽어야 할 파일

먼저 아래 파일들을 읽고 설계 의도를 파악하라:

- `/docs/UI_GUIDE.md` (색상, 컴포넌트 스타일, 안티패턴)
- `/docs/PRD.md` (핵심 기능 요구사항)
- `/frontend/src/types/api.ts`
- `/frontend/src/pages/ResultPage.tsx`
- `/frontend/src/components/score/ConsistencyScoreCard.tsx`
- `/frontend/src/components/report/DetailPanel.tsx`
- `/frontend/src/components/report/RecommendationList.tsx`
- `/frontend/src/components/report/RootCauseList.tsx`

이전 step에서 생성/수정된 파일:
- `/backend/app/models/schemas.py` (SlideStats 추가됨 — `AnalysisResult.slide_stats: list[SlideStats]`)

## 작업

### 1. `frontend/src/types/api.ts` — SlideStats 타입 추가

백엔드 `SlideStats` Pydantic 모델과 동기화한다:

```typescript
export interface SlideStats {
  slide_index: number;
  word_count: number;
  font_size_mean: number;   // pt 단위
  text_area_ratio: number;  // 0~1
  element_count: number;
  dominant_font: string;
}
```

`AnalysisResult` 인터페이스에 필드 추가:
```typescript
slide_stats: SlideStats[];
```

### 2. `frontend/src/pages/ResultPage.tsx` — 첫 번째 아웃라이어 자동 선택

현재: `useState<number | null>(null)`로 초기값이 없어 디테일 패널이 비어있다.

변경: 분석 결과가 로드되면 첫 번째 아웃라이어 슬라이드를 자동 선택한다.

`useEffect`를 사용해 `result`가 변경될 때 아래 로직을 실행한다:
- `result.outlier_slides`가 비어있지 않으면 `result.outlier_slides[0].slide_index`로 `setSelectedSlide` 호출
- 이미 `selectedSlide`가 설정된 경우 덮어쓰지 않는다 (사용자가 다른 슬라이드를 선택했을 수 있음)

### 3. `frontend/src/pages/ResultPage.tsx` — 아웃라이어 요약 배너

`ConsistencyScoreCard` 바로 아래, 썸네일 안내 문구 위에 아웃라이어 요약 배너를 추가한다.

배너 조건:
- `result.outlier_slides.length > 0`일 때만 렌더링
- 텍스트: `"슬라이드 {slide_count}장 중 {outlier_count}장에서 디자인 이상 감지"`
- 스타일: `text-sm text-amber-400` (별도 카드나 박스 없이 텍스트만, UI_GUIDE의 AI 슬롭 안티패턴 주의)

### 4. `frontend/src/components/report/DetailPanel.tsx` — 비아웃라이어 슬라이드 정보 표시

현재: 비아웃라이어 슬라이드 선택 시 "이 슬라이드는 전체 디자인과 일관성이 높습니다"만 표시.

변경: 해당 슬라이드의 `SlideStats`를 함께 표시한다.

Props 변경:
```typescript
interface Props {
  selectedIndex: number | null;
  outlierSlides: OutlierSlide[];
  slideStats: SlideStats[];   // 추가
}
```

비아웃라이어 슬라이드 선택 시 렌더링:
```
[이 슬라이드는 전체 디자인과 일관성이 높습니다]

슬라이드 통계
주요 폰트    {dominant_font}
평균 폰트 크기  {font_size_mean}pt
텍스트 영역   {(text_area_ratio * 100).toFixed(0)}%
단어 수     {word_count}개
요소 수     {element_count}개
```

스타일: 레이블은 `text-xs text-neutral-500`, 값은 `text-sm text-neutral-300`. 테이블 형태(`grid grid-cols-2`) 레이아웃.

`ResultPage.tsx`에서 `DetailPanel`에 `slideStats={result.slide_stats}` prop 전달.

### 5. `frontend/src/components/report/RecommendationList.tsx` — 개선

현재: 수정 제안을 단순 목록으로 표시.

변경:
- `impact_score_delta` 내림차순으로 정렬 (가장 효과적인 수정이 상단)
- 첫 번째 항목에 "가장 효과적" 텍스트 레이블 추가 (스타일: `text-xs text-neutral-500`)
- 목록 아래에 합산 기대 점수 향상을 표시: `"모두 적용 시 최대 +{합계}점 향상 가능"`  
  (스타일: `text-xs text-neutral-500 mt-3 pt-3 border-t border-neutral-800`)
- 합산 값이 0이면 해당 줄을 숨긴다

## Acceptance Criteria

```bash
cd frontend && npm run build && npm run lint
```

컴파일/린트 에러 없음.

## 검증 절차

1. AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - TypeScript 타입이 `frontend/src/types/api.ts`에만 정의되어 있는가?
   - 컴포넌트 파일에 인라인 타입 정의가 없는가?
   - UI_GUIDE.md 안티패턴(backdrop-filter, gradient-text, box-shadow 글로우 등)을 사용하지 않았는가?
   - CLAUDE.md CRITICAL 규칙 위반 없는가?
3. `phases/1-ux-improvements/index.json` step 2를 업데이트한다.

## 금지사항

- `SlideStats` 타입을 컴포넌트 파일에 인라인으로 정의하지 마라. 이유: TypeScript 타입은 `frontend/src/types/`에만 정의한다.
- `backdrop-filter: blur()`, gradient-text, box-shadow 글로우 등 UI_GUIDE 금지 스타일을 사용하지 마라.
- AI 직접 호출 로직을 프론트엔드에 추가하지 마라. 이유: CRITICAL — 프론트엔드는 FastAPI 엔드포인트를 통해서만 통신한다.
- 기존 컴포넌트의 Props 타입을 컴포넌트 파일 내부에 중복 정의하지 마라.
