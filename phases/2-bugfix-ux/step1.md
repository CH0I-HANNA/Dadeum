# Step 1: frontend-ux

## 읽어야 할 파일

먼저 아래 파일들을 읽고 현재 구현을 파악하라:

- `/home/user/Dadeum/CLAUDE.md`
- `/home/user/Dadeum/frontend/src/pages/ResultPage.tsx`
- `/home/user/Dadeum/frontend/src/components/slides/SlideGrid.tsx`
- `/home/user/Dadeum/frontend/src/components/slides/SlidePreview.tsx`
- `/home/user/Dadeum/frontend/src/components/report/DetailPanel.tsx`
- `/home/user/Dadeum/frontend/src/components/report/RootCauseList.tsx`
- `/home/user/Dadeum/frontend/src/components/report/RecommendationList.tsx`
- `/home/user/Dadeum/frontend/src/types/api.ts`

## 배경

현재 UI에서 다음 문제들이 확인되었다:

1. **색상값 표시**: RootCause에서 `RGB(r,g,b)` 텍스트가 그대로 노출되어 사용자가 의미를 알 수 없다.
2. **+0.0점 수정 제안 노출**: `impact_score_delta`가 0.0인 수정 제안이 목록에 표시되어 노이즈를 발생시킨다.
3. **슬라이드 목록 너비**: `w-48`(192px)이 너무 좁아 2열 썸네일이 작게 표시된다.
4. **필터 버튼 위치**: 현재 가운데 패널 상단에 위치한 IssueFilter가 슬라이드 목록과 분리되어 있어 맥락이 끊긴다.
5. **슬라이드 번호 뱃지**: 현재 `text-[10px]`로 너무 작아 읽기 어렵다.

## 작업

### 1. `frontend/src/components/report/RootCauseList.tsx` — 색상값 컬러 스와치 표시

현재 `RootCauseList.tsx`는 `cause.expected_value`와 `cause.actual_value`를 텍스트로 그대로 렌더링한다:

```tsx
<p className="text-xs text-neutral-500 leading-relaxed">
  기대: {cause.expected_value} → 실제: {cause.actual_value}
</p>
```

백엔드 `explainer.py`의 `_color_label`이 `"RGB(0, 0, 0)"` 형식 문자열을 반환하므로 이 텍스트가 UI에 그대로 노출된다.

수정: `expected_value` / `actual_value`에 `RGB(` 패턴이 포함되어 있으면 텍스트 대신 인라인 컬러 스와치를 렌더링한다.

`frontend/src/utils/color.ts` (신규 파일)에 헬퍼 함수를 작성하라:

```ts
// "RGB(0, 0, 0)" → { css: "rgb(0,0,0)", hex: "#000000" } | null
export function parseRgbString(val: string): { css: string; hex: string } | null { ... }
```

HEX 변환 포함. 패턴 불일치 시 `null` 반환.

`RootCauseList.tsx`에서 값마다 `parseRgbString`을 호출해 non-null이면 스와치로, null이면 기존 텍스트로 렌더링:

- 스와치: `<span style={{ background: css }} className="w-4 h-4 rounded-full inline-block border border-neutral-600 align-middle" />` + HEX 문자열 텍스트
- 스와치와 HEX를 `flex items-center gap-1.5` 래퍼로 감싼다.

TypeScript 규칙: 유틸 함수는 `frontend/src/utils/color.ts`로 분리. 컴포넌트 내 인라인 타입 정의 금지.

### 2. `frontend/src/components/report/RecommendationList.tsx` — 효과 없는 제안 숨김

`impact_score_delta`가 `0.05` 미만인 항목을 필터링하여 목록에서 제외한다:

```tsx
const visibleRecs = recommendations.filter(r => r.impact_score_delta >= 0.05);
```

`visibleRecs`가 빈 배열이면 `"개선 제안이 없습니다"` 텍스트를 표시한다.

### 3. `frontend/src/pages/ResultPage.tsx` — 슬라이드 목록 너비 및 필터 위치 변경

**너비 조정**: 왼쪽 패널 `w-48` → `w-56` (224px). 2열 썸네일이 좀 더 넓게 표시된다.

**필터 위치 이동**: `IssueFilter`를 가운데 패널에서 왼쪽 슬라이드 목록 패널 상단으로 이동한다.

변경 전 레이아웃 (가운데 패널):
```tsx
<div className="flex items-center justify-between">
  {result.outlier_slides.length > 0 ? (
    <IssueFilter ... />
  ) : (
    <div />
  )}
  <button ...>비교</button>
</div>
```

변경 후:
- 왼쪽 패널 상단에 `IssueFilter` 배치 (슬라이드 목록 레이블 아래).
- 가운데 패널 상단에는 비교 버튼만 남기고 오른쪽 정렬.

### 4. `frontend/src/components/slides/SlideThumbnail.tsx` — 슬라이드 번호 뱃지 크기

슬라이드 번호 스팬의 폰트 크기 `text-[10px]` → `text-xs` (12px), padding 소폭 증가.

변경 전:
```tsx
<span className="absolute bottom-0.5 left-1 text-[10px] text-white/70 bg-black/50 px-1 rounded">
```

변경 후:
```tsx
<span className="absolute bottom-1 left-1 text-xs text-white/80 bg-black/60 px-1.5 py-0.5 rounded">
```

## Acceptance Criteria

```bash
cd /home/user/Dadeum/frontend && npm run lint && npm run build
```

에러 없이 통과해야 한다.

## 검증 절차

1. AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - TypeScript 타입이 `frontend/src/types/` 또는 컴포넌트 상단 헬퍼에만 정의되어 있는가? (컴포넌트 내 인라인 타입 정의 금지)
   - color 헬퍼 함수(`parseRgbString`)가 `frontend/src/utils/color.ts`에 분리되어 있는가?
   - CLAUDE.md CRITICAL 규칙 위반 없는가?
3. `phases/2-bugfix-ux/index.json` step 1을 업데이트한다:
   - 성공 → `"status": "completed"`, `"completed_at": "<ISO 타임스탬프>"`, `"summary": "산출물 한 줄 요약"`
   - 3회 시도 후 실패 → `"status": "error"`, `"error_message": "구체적 에러"`

## 금지사항

- 컴포넌트 파일 내에 TypeScript `interface` 또는 `type`을 인라인으로 새로 정의하지 마라. 이유: CLAUDE.md — TypeScript 타입은 `frontend/src/types/`에만 정의.
- RGB 파싱 로직을 각 컴포넌트에 중복 구현하지 마라. 헬퍼 함수 하나로 분리하라.
- 기존 3패널 레이아웃 구조를 깨뜨리지 마라.
- 비교 버튼을 제거하거나 위치를 완전히 바꾸지 마라.
