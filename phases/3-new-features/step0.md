# Step 0: frontend-share-progress

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트의 아키텍처와 설계 의도를 파악하라:

- `/Users/choehanna/Documents/Dadeum/docs/ARCHITECTURE.md`
- `/Users/choehanna/Documents/Dadeum/CLAUDE.md`
- `/Users/choehanna/Documents/Dadeum/frontend/src/pages/ResultPage.tsx`
- `/Users/choehanna/Documents/Dadeum/frontend/src/hooks/useAnalysis.ts`

## 작업

### 1. URL 공유 버튼 (ResultPage.tsx)

`frontend/src/pages/ResultPage.tsx`의 헤더 영역 "결과 내보내기" 버튼 옆에 "링크 복사" 버튼을 추가한다.

동작:
- 클릭 시 `navigator.clipboard.writeText(window.location.href)` 로 현재 URL을 클립보드에 복사
- 복사 성공 후 버튼 텍스트가 "복사됨 ✓" 로 2초간 바뀌었다가 원래대로 돌아옴 (`useState<boolean>` + `setTimeout` 사용)
- 클립보드 API 실패 시(구형 브라우저) 아무 동작 없이 실패를 무시함 (`catch` 블록 비워둠)
- 스타일: "결과 내보내기" 버튼과 동일한 스타일

### 2. 분석 진행 단계 표시 (`frontend/src/hooks/useAnalysis.ts`)

`useAnalysis.ts`를 수정하여 반환값에 `stage: string` 필드를 추가한다.

**구현 방법**:

```typescript
// useRef를 사용하는 이유: 시작 시각은 한 번만 기록하면 되고,
// 이 값이 바뀔 때 re-render가 불필요하기 때문이다.
// import { useState, useEffect, useRef } from "react";  ← useRef 반드시 추가
const startTimeRef = useRef<number>(Date.now());

// stage는 React Query 폴링(1.5초마다)으로 re-render가 발생할 때마다
// 현재 시각과 startTimeRef.current의 차이로 계산한다.
const elapsed = (Date.now() - startTimeRef.current) / 1000; // 초 단위

function getStage(elapsed: number, status: string): string {
  if (status === "completed" || status === "error") return "";
  if (elapsed < 5)  return "파일 파싱 중...";
  if (elapsed < 15) return "특징 추출 중...";
  if (elapsed < 30) return "이상 슬라이드 탐지 중...";
  return "결과 생성 중...";
}
```

`UseAnalysisReturn` 인터페이스에 `stage: string`을 추가하고 반환한다.

### 3. 진행 단계 표시 (ResultPage.tsx)

`useAnalysis`에서 `stage`를 받아 분석 중 화면에 표시한다:

```tsx
// status === "pending" || status === "processing" 분기에서
<div className="w-6 h-6 border-2 border-neutral-600 border-t-amber-400 rounded-full animate-spin" />
<p className="text-sm text-neutral-400">분석 중...</p>
{stage && <p className="text-xs text-neutral-500">{stage}</p>}
```

## Acceptance Criteria

```bash
cd /Users/choehanna/Documents/Dadeum/frontend
npm run build    # 컴파일 에러 없음
npm run lint     # ESLint 에러 없음
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - `frontend/src/types/` 에만 타입 정의되어 있는가?
   - 컴포넌트 파일에 인라인 타입 정의가 없는가?
   - CLAUDE.md CRITICAL 규칙을 위반하지 않았는가?
3. 결과에 따라 `phases/3-new-features/index.json`의 step 0을 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "산출물 한 줄 요약"`
   - 수정 3회 시도 후에도 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- 백엔드를 수정하지 마라. 이 step은 프론트엔드 전용이다.
- `useAnalysis.ts`의 기존 반환 필드(`result`, `status`, `error`)를 제거하지 마라. `stage`만 추가한다.
- `setInterval`을 사용하지 마라. React Query 폴링이 1.5초마다 re-render를 발생시키므로, 그 시점에 `Date.now() - startTimeRef.current`로 계산하면 충분하다.
- `timedOut` 상태일 때 `stage`는 반드시 `""` 를 반환해야 한다. 타임아웃 에러 화면에 진행 단계가 표시되면 안 된다.
