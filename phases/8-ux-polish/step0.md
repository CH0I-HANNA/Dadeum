# Step 0: upload-errors

## 읽어야 할 파일

- `/frontend/src/pages/UploadPage.tsx` (수정 대상)
- `/frontend/src/hooks/useUpload.ts` (수정 대상)
- `/frontend/src/services/api.ts` (HTTP 상태 코드 참고)

## 문제

### 1. 잘못된 파일 드래그 시 무반응

`UploadPage.tsx`의 `handleFile`은 `isAccepted`가 false이면 그냥 `return`한다. 사용자는 왜 업로드가 안 되는지 알 수 없다.

### 2. 에러 메시지 날것 노출

`useUpload.ts`의 catch 블록에서 `err.message`를 그대로 쓴다. axios 에러는 "Request failed with status code 413"처럼 기술적인 메시지가 그대로 사용자에게 노출된다.

## 작업

### 1. `UploadPage.tsx` — 파일 타입 거부 에러 표시

`handleFile`에서 `isAccepted`가 false일 때 에러 상태를 설정하도록 수정하라.

현재:
```ts
const handleFile = (file: File) => {
  if (!isAccepted(file)) return;  // 무반응
  upload(file);
};
```

수정 후: `isAccepted`가 false이면 `useUpload`에 에러를 설정하거나, `UploadPage` 내부 상태로 에러를 관리하라.

에러 메시지: `"PPTX 또는 PDF 파일만 업로드할 수 있습니다."`

### 2. `useUpload.ts` — HTTP 상태 코드별 메시지 매핑

catch 블록에서 axios 에러의 상태 코드를 확인하고 사용자 친화적 메시지로 변환하라.

```ts
// 상태 코드별 메시지
400 → "파일 형식이 올바르지 않거나 손상된 파일입니다."
413 → "파일 크기가 50MB를 초과합니다. 더 작은 파일을 사용해주세요."
503 → "서버 저장 공간이 부족합니다. 잠시 후 다시 시도해주세요."
그 외 → "업로드 중 오류가 발생했습니다. 다시 시도해주세요."
```

axios 에러 응답의 `detail` 필드도 확인하라: `err?.response?.data?.detail`  
백엔드가 `detail`을 내려주면 그 메시지를 우선 사용하고, 없으면 위 상태 코드별 기본 메시지를 사용한다.

## Acceptance Criteria

```bash
cd frontend
npm run build
npm run lint
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 결과에 따라 `phases/8-ux-polish/index.json`의 step 0을 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "UploadPage 파일 타입 에러 메시지 추가, useUpload HTTP 상태 코드별 메시지 매핑"`
   - 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- `isAccepted` 로직을 변경하지 마라. 허용 파일 목록은 그대로다.
- `useUpload`의 `upload` 함수 시그니처를 변경하지 마라. `UploadPage`가 이 함수를 호출한다.
- 기술적 메시지(상태 코드, stack trace)를 사용자에게 노출하지 마라.
