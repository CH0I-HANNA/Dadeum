# Step 8: frontend-upload

## 읽어야 할 파일

- `frontend/src/types/api.ts`

## 작업

파일 업로드 페이지와 API 클라이언트를 구현하라.

### 1. API 클라이언트

`frontend/src/services/api.ts` 를 구현하라.

```typescript
const BASE_URL = "http://localhost:8000";

export async function uploadFile(file: File): Promise<UploadResponse>
export async function startAnalysis(fileId: string): Promise<AnalyzeResponse>
export async function getResult(taskId: string): Promise<TaskStatus & { result?: AnalysisResult }>
export async function getThumbnailUrl(fileId: string, slideNum: number): string
// getThumbnailUrl은 비동기 아님 — URL 문자열만 조립하여 반환
```

### 2. useUpload hook

`frontend/src/hooks/useUpload.ts` 를 구현하라.

```typescript
interface UseUploadReturn {
  upload: (file: File) => Promise<void>;
  isUploading: boolean;
  error: string | null;
  uploadResponse: UploadResponse | null;
}

export function useUpload(): UseUploadReturn
```

`upload` 함수는 `uploadFile` → `startAnalysis` 를 순서대로 호출하고, `task_id` 를 반환하면 `/result/{task_id}` 로 React Router navigate한다.

### 3. UploadPage

`frontend/src/pages/UploadPage.tsx` 를 구현하라.

레이아웃:
- 중앙 수직 배치 (화면 전체 높이)
- 서비스명 "다듬" + 부제 "발표자료 디자인 일관성 분석"
- 드래그 앤 드롭 영역 (점선 테두리, `.pptx .pdf` 수락)
- 파일 선택 버튼 (Primary 버튼 스타일)
- 업로드 중 로딩 상태 표시

UI_GUIDE.md 색상/컴포넌트 스타일을 따른다:
- 배경: `#0a0a0a`
- 드롭존: `border border-dashed border-neutral-700 rounded-lg`
- 드래그 오버 시: `border-amber-400`

### 4. App.tsx 라우팅

`frontend/src/App.tsx` 에 React Router 라우팅을 설정하라:
- `/` → `UploadPage`
- `/result/:taskId` → `ResultPage` (이 step에서는 placeholder 컴포넌트로 대체)

### 테스트 없음

이 step은 UI 컴포넌트이므로 자동화 테스트 대신 아래 수동 검증으로 대체한다.

## Acceptance Criteria

```bash
cd frontend && npm run build   # 빌드 에러 없음
cd frontend && npm run lint    # lint 에러 없음
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. `npm run dev` 로 개발 서버 실행 후 `http://localhost:5173` 에서 업로드 페이지가 렌더링되는지 확인한다.
3. `.pptx` 파일을 드래그하면 드롭존 테두리가 `amber-400` 으로 바뀌는지 확인한다.
4. `phases/0-mvp/index.json` 의 step 8 을 업데이트한다.

## 금지사항

- UI_GUIDE.md의 AI 슬롭 안티패턴(glass morphism, gradient-text, 글로우 등)을 사용하지 마라.
- `useUpload` 훅 내부에서 직접 `axios` 를 호출하지 마라. 반드시 `services/api.ts` 를 통해서만 호출한다.
- `ResultPage` 를 이 step에서 구현하지 마라. placeholder(`<div>결과 페이지</div>`)로만 둔다.
