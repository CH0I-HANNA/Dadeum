# Step 2: download-thumbnail

## 읽어야 할 파일

- `/frontend/src/services/api.ts` (수정 대상 — downloadFixedFile)
- `/frontend/src/components/slides/SlideThumbnail.tsx` (수정 대상)
- `/frontend/src/pages/ResultPage.tsx` (썸네일 안내문구 수정 대상)
- `/frontend/src/components/report/ComparePanel.tsx` (비교 모드 A 뱃지 수정 대상)

## 문제

### 1. 수정 파일 다운로드 — PDF도 .pptx로 저장
`api.ts`의 `downloadFixedFile`에서 파일명이 항상 `.pptx`로 하드코딩되어 있다. PDF 파일을 업로드하고 수정 파일을 다운받으면 잘못된 확장자로 저장된다.

### 2. 썸네일 로딩 placeholder 없음
`SlideThumbnail`의 `<img>`가 로딩 중일 때 빈 공간만 보인다. 느린 네트워크에서 레이아웃이 흔들리거나 깨진 이미지 아이콘이 표시된다.

### 3. 썸네일 안내문구 오류
`ResultPage`에 `"썸네일은 실제 슬라이드를 렌더링한 것입니다."` 라고 표시되지만, 실제로는 python-pptx + Pillow 기반의 근사 렌더링이라 원본과 다를 수 있다 (ADR-008 참조).

### 4. 비교 모드 A/B 뱃지 불균형
`ComparePanel`에서 B 슬라이드에만 "B" 뱃지가 있다. A 슬라이드에 뱃지가 없어서 어느 게 기준인지 모호하다.

## 작업

### 1. `api.ts` — downloadFixedFile 파일명 수정

백엔드 응답의 `Content-Disposition` 헤더에서 파일명을 읽어라.

```ts
export async function downloadFixedFile(fileId: string, taskId: string): Promise<void> {
  const response = await client.post(
    `/api/fix/${fileId}`,
    { task_id: taskId },
    { responseType: "blob" }
  );

  // Content-Disposition 헤더에서 파일명 추출
  // 예: attachment; filename="dadeum-fixed-abc123.pptx"
  const disposition = response.headers["content-disposition"] as string | undefined;
  const match = disposition?.match(/filename="?([^";\n]+)"?/);
  const filename = match?.[1] ?? `dadeum-fixed-${fileId.slice(0, 8)}.pptx`;

  const url = URL.createObjectURL(new Blob([response.data]));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
```

### 2. `SlideThumbnail.tsx` — 로딩 placeholder 추가

`<img>` 로딩 중 회색 배경 placeholder를 표시하라.

- `useState`로 `loaded` 상태 관리
- 로딩 중: `bg-neutral-800 animate-pulse` 배경 표시 (슬라이드 비율 유지)
- 로딩 완료: 이미지 표시
- 이미지 에러: 회색 배경 유지 (에러 메시지 불필요)

슬라이드 비율: 16:9 기준으로 `aspect-video` 클래스 사용.

### 3. `ResultPage.tsx` — 썸네일 안내문구 수정

```tsx
// 현재
<p className="text-xs text-neutral-600">
  썸네일은 실제 슬라이드를 렌더링한 것입니다.
</p>

// 수정 후
<p className="text-xs text-neutral-600">
  썸네일은 실제 슬라이드와 다를 수 있습니다.
</p>
```

### 4. `ComparePanel.tsx` — A/B 뱃지 대칭 적용

비교 슬라이드 렌더링 부분에서 A, B 뱃지를 모두 표시하라.

현재 `SlideThumbnail`에 `isCompare`가 B만 표시하는 구조라면, `ComparePanel` 내부에서 직접 절대 위치 뱃지를 추가하거나 인덱스 기반으로 A/B를 구분하라.

표시 형태: 좌상단에 `"A"` / `"B"` 텍스트 뱃지 (`text-[10px] bg-black/70 text-neutral-300 px-1 rounded`)

## Acceptance Criteria

```bash
cd frontend
npm run build
npm run lint
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 결과에 따라 `phases/8-ux-polish/index.json`의 step 2를 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "downloadFixedFile Content-Disposition 파일명 읽기, 썸네일 placeholder, 안내문구 수정, ComparePanel A/B 뱃지 대칭"`
   - 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- `SlideThumbnail`에 `aspect-video`를 적용할 때 기존 `h-auto` 스타일을 제거하지 마라. 이유: 이미지가 로드된 이후에는 실제 비율로 표시되어야 한다. placeholder에만 `aspect-video`를 적용하고 이미지 로드 후 제거하라.
- Content-Disposition 파싱 실패 시 예외를 throw하지 마라. fallback 파일명(`dadeum-fixed-{fileId}.pptx`)으로 진행한다.
