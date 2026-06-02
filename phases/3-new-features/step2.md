# Step 2: frontend-pdf

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트의 아키텍처와 설계 의도를 파악하라:

- `/Users/choehanna/Documents/Dadeum/docs/ARCHITECTURE.md`
- `/Users/choehanna/Documents/Dadeum/CLAUDE.md`
- `/Users/choehanna/Documents/Dadeum/frontend/src/pages/ResultPage.tsx`
- `/Users/choehanna/Documents/Dadeum/frontend/src/services/api.ts`
- `/Users/choehanna/Documents/Dadeum/frontend/src/types/api.ts`

이전 step(step0)에서 ResultPage.tsx에 "링크 복사" 버튼이 추가되어 있다. 헤더 버튼 영역을 꼼꼼히 읽고 동일한 패턴으로 PDF 버튼을 추가하라.

## 작업

### 1. API 함수 추가 (`frontend/src/services/api.ts`)

다음 함수를 추가한다:

```typescript
export function getReportUrl(taskId: string): string {
  return `${BASE_URL}/api/report/${taskId}`;
}
```

### 2. PDF 다운로드 버튼 추가 (`frontend/src/pages/ResultPage.tsx`)

헤더의 버튼 영역("링크 복사", "결과 내보내기" 옆)에 "PDF 보고서" 버튼을 추가한다.

동작:
- 클릭 시 `window.open(getReportUrl(taskId), '_blank')` 로 새 탭에서 PDF를 열어 브라우저 기본 다운로드 동작을 트리거한다
- `taskId`는 `useParams`에서 가져온다 (이미 ResultPage에서 사용 중)

스타일: "결과 내보내기" 버튼과 동일한 스타일 (`border border-neutral-700 text-neutral-300 text-sm px-4 py-2 ...`)

## Acceptance Criteria

```bash
cd /Users/choehanna/Documents/Dadeum/frontend
npm run build    # 컴파일 에러 없음
npm run lint     # ESLint 에러 없음
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - API 함수가 `frontend/src/services/api.ts`에만 정의되어 있는가?
   - TypeScript 타입이 `frontend/src/types/`에만 정의되어 있는가?
3. 결과에 따라 `phases/3-new-features/index.json`의 step 2를 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "산출물 한 줄 요약"`
   - 수정 3회 시도 후에도 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- 백엔드를 수정하지 마라. 이 step은 프론트엔드 전용이다.
- PDF를 프론트엔드에서 직접 생성하지 마라 (jsPDF, html2canvas 등 사용 금지). 반드시 step 1에서 만든 백엔드 API를 호출하라.
- 기존 "결과 내보내기"(JSON) 버튼을 제거하거나 수정하지 마라.
