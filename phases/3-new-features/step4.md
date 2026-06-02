# Step 4: frontend-fix-preview

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트의 아키텍처와 설계 의도를 파악하라:

- `/Users/choehanna/Documents/Dadeum/docs/ARCHITECTURE.md`
- `/Users/choehanna/Documents/Dadeum/CLAUDE.md`
- `/Users/choehanna/Documents/Dadeum/frontend/src/pages/ResultPage.tsx`
- `/Users/choehanna/Documents/Dadeum/frontend/src/components/report/DetailPanel.tsx`
- `/Users/choehanna/Documents/Dadeum/frontend/src/components/slides/SlidePreview.tsx`
- `/Users/choehanna/Documents/Dadeum/frontend/src/services/api.ts`
- `/Users/choehanna/Documents/Dadeum/frontend/src/types/api.ts`

이전 step들에서 변경된 사항:
- step0: `useAnalysis`에 `stage` 반환 추가. ResultPage 헤더에 "링크 복사" 버튼 추가됨
- step2: ResultPage 헤더에 "PDF 보고서" 버튼 추가됨
- step3: 백엔드에 `POST /api/fix/{file_id}` (수정 PPTX 다운로드), `GET /api/preview-fix/{file_id}/{slide_num}?task_id={task_id}` (수정 후 썸네일) 엔드포인트 추가됨

**각 파일을 꼼꼼히 읽고 현재 Props 인터페이스, 함수 시그니처, import 구조를 파악한 뒤 작업하라.**

## 작업

### 1. API 함수 추가 (`frontend/src/services/api.ts`)

다음 두 함수를 추가한다:

```typescript
// 수정된 슬라이드 미리보기 썸네일 URL (img src에 직접 사용)
export function getPreviewFixUrl(fileId: string, slideNum: number, taskId: string): string {
  return `${BASE_URL}/api/preview-fix/${fileId}/${slideNum}?task_id=${taskId}`;
}

// 수정된 PPTX 다운로드 (blob 응답, POST 요청)
export async function downloadFixedFile(fileId: string, taskId: string): Promise<void> {
  const response = await client.post(
    `/api/fix/${fileId}`,
    { task_id: taskId },
    { responseType: "blob" }
  );
  const url = URL.createObjectURL(new Blob([response.data]));
  const a = document.createElement("a");
  a.href = url;
  a.download = `dadeum-fixed-${fileId.slice(0, 8)}.pptx`;
  a.click();
  URL.revokeObjectURL(url);
}
```

### 2. 수정된 파일 다운로드 버튼 (`frontend/src/pages/ResultPage.tsx`)

헤더 버튼 영역에 "수정 파일 다운로드" 버튼을 추가한다.

동작:
- 클릭 시 `downloadFixedFile(result.file_id, taskId ?? "")` 호출
- 다운로드 진행 중: 버튼 텍스트를 "수정 중..." 으로 변경, `disabled` 처리 (`useState<boolean>`)
- 완료 또는 에러: 원래 텍스트로 복원
- 에러 발생 시 (PDF 파일 등) `alert("PPTX 파일만 수정 가능합니다.")` 표시
- `taskId`는 `useParams<{ taskId: string }>()` 에서 가져온다 (ResultPage에 이미 있음)

### 3. DetailPanel Props 확장 + 수정 미리보기 섹션

**Props 인터페이스 변경** (`frontend/src/components/report/DetailPanel.tsx`):

`FixedPreviewImage`가 `useState`를 사용하므로 파일 상단에 import를 추가한다:
```typescript
import { useState } from "react";
```

```typescript
// 기존
interface Props {
  selectedIndex: number | null;
  outlierSlides: OutlierSlide[];
  slideStats: SlideStats[];
}

// 변경 후 (fileId, taskId 추가)
interface Props {
  selectedIndex: number | null;
  outlierSlides: OutlierSlide[];
  slideStats: SlideStats[];
  fileId: string;
  taskId: string;
}
```

**ResultPage.tsx에서 DetailPanel 호출부도 반드시 업데이트**:
```tsx
<DetailPanel
  selectedIndex={activeSlide}
  outlierSlides={result.outlier_slides}
  slideStats={result.slide_stats}
  fileId={result.file_id}          // 추가
  taskId={taskId ?? ""}            // 추가 (useParams에서 가져온 값)
/>
```

**수정 미리보기 섹션** (이상 슬라이드가 선택된 경우만, 즉 `outlier` 존재 시):

기존 "원인 분석" + "수정 제안" 아래에 추가:

```tsx
<div>
  <p className="text-xs font-medium text-neutral-400 uppercase tracking-wider mb-3">
    수정 미리보기
  </p>
  <div className="grid grid-cols-2 gap-2">
    <div>
      <p className="text-xs text-neutral-500 mb-1">현재</p>
      <img
        src={getThumbnailUrl(fileId, selectedIndex)}
        alt="현재 슬라이드"
        className="w-full rounded"
      />
    </div>
    <div>
      <p className="text-xs text-neutral-500 mb-1">수정 후</p>
      <FixedPreviewImage
        src={getPreviewFixUrl(fileId, selectedIndex, taskId)}
      />
    </div>
  </div>
</div>
```

`FixedPreviewImage`는 같은 파일 내에 정의하는 내부 컴포넌트:
```tsx
function FixedPreviewImage({ src }: { src: string }) {
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  if (error) return null;  // 에러 시 섹션 숨김 (PDF 파일 등 미지원 케이스)
  return (
    <div className="relative w-full">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-neutral-900 rounded">
          <p className="text-xs text-neutral-500">로딩 중...</p>
        </div>
      )}
      <img
        src={src}
        alt="수정 후 슬라이드"
        className="w-full rounded"
        onLoad={() => setLoading(false)}
        onError={() => { setError(true); setLoading(false); }}
      />
    </div>
  );
}
```

`getThumbnailUrl`은 `frontend/src/services/api.ts`에서 import한다.
`getPreviewFixUrl`도 동일하게 import한다.

## Acceptance Criteria

```bash
cd /Users/choehanna/Documents/Dadeum/frontend
npm run build    # 컴파일 에러 없음
npm run lint     # ESLint 에러 없음
npm run test     # 기존 테스트 통과
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - API 함수가 `frontend/src/services/api.ts`에만 정의되어 있는가?
   - TypeScript 타입이 `frontend/src/types/`에만 정의되어 있는가?
   - `FixedPreviewImage`는 `DetailPanel.tsx` 내부 컴포넌트라 별도 파일 불필요
3. 결과에 따라 `phases/3-new-features/index.json`의 step 4를 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "산출물 한 줄 요약"`
   - 수정 3회 시도 후에도 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- 백엔드 파일을 수정하지 마라. 이 step은 프론트엔드 전용이다.
- `FixedPreviewImage`에 fetch 로직을 추가하지 마라. `<img src=...>` 의 `onError`/`onLoad`로 충분하다. 브라우저가 이미지 로딩을 처리한다.
- `ComparePanel`을 수정하지 마라. 비교 모드(슬라이드 A vs B 비교)와 수정 미리보기(수정 전 vs 수정 후)는 별개 기능이다.
- `DetailPanel`의 Props에 `fileId`와 `taskId`를 추가하면 `ResultPage.tsx`의 호출부도 반드시 함께 수정해야 한다. 누락 시 TypeScript 컴파일 에러가 발생한다.
- 기존 테스트를 깨뜨리지 마라.
