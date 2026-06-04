# Step 1: slide-role-badge

## 읽어야 할 파일

먼저 아래 파일들을 읽고 기존 컴포넌트 구조를 파악하라:

- `/docs/UI_GUIDE.md`
- `/frontend/src/types/api.ts` (SlideStats.slide_role 필드 확인)
- `/frontend/src/components/slides/SlideThumbnail.tsx` (수정 대상)
- `/frontend/src/components/slides/SlideGrid.tsx` (수정 대상)

## 배경

`SlideStats.slide_role`은 CNN이 예측한 슬라이드 역할 인덱스(0~4)다. 모델이 없으면 `null`이다.

역할 인덱스 매핑:
| 인덱스 | 역할 | 약칭 |
|--------|------|------|
| 0 | 표지 | 표지 |
| 1 | 섹션헤더 | 섹션 |
| 2 | 본문 | 본문 |
| 3 | 도표/시각자료 | 도표 |
| 4 | 마무리 | 마무리 |

## 작업

### 1. `SlideThumbnail.tsx` 수정

`slideRole?: number | null` prop을 추가하고, 썸네일 우상단에 역할 뱃지를 표시하라.

```tsx
interface Props {
  // 기존 props 유지
  slideRole?: number | null;  // 추가
}
```

- `slideRole`이 `null` 또는 `undefined`이면 뱃지를 렌더링하지 않는다.
- 뱃지 위치: 썸네일 우상단 (`absolute top-0.5 right-0.5`)
- 뱃지 스타일: `text-[10px] px-1 rounded bg-black/70` + 역할별 텍스트 색상
  - 표지(0): `text-purple-400`
  - 섹션헤더(1): `text-blue-400`
  - 본문(2): `text-neutral-300`
  - 도표/시각자료(3): `text-green-400`
  - 마무리(4): `text-orange-400`
- 약칭(표지/섹션/본문/도표/마무리)으로 표시한다. 공간이 좁으므로 전체 이름 사용 금지.

### 2. `SlideGrid.tsx` 수정

`slideStats?: SlideStats[]` prop을 추가하고, 각 슬라이드의 `slide_role`을 `SlideThumbnail`에 전달하라.

```tsx
interface Props {
  // 기존 props 유지
  slideStats?: SlideStats[];  // 추가
}
```

- `slideStats`가 없거나 해당 인덱스에 stats가 없으면 `slideRole`을 전달하지 않는다.
- `slideStats`는 `slide_index` 기준으로 조회한다: `slideStats.find(s => s.slide_index === i)?.slide_role`

## Acceptance Criteria

```bash
cd frontend
npm run build
npm run lint
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 기존 props 인터페이스가 그대로 유지되는지 (새 prop은 optional이어야 함) 확인한다.
3. 결과에 따라 `phases/7-hmm-frontend/index.json`의 step 1을 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "SlideThumbnail에 slideRole 뱃지 추가, SlideGrid에 slideStats prop 추가"`
   - 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- `ResultPage.tsx`를 수정하지 마라. 이 step은 SlideGrid/SlideThumbnail만 담당한다.
- 기존 `SlideThumbnail`과 `SlideGrid`의 필수 prop을 변경하지 마라. 새 prop은 모두 optional이어야 한다. 이유: ResultPage에서 기존 방식으로 사용 중이므로 시그니처를 바꾸면 빌드가 깨진다.
- 역할명을 전체 이름("섹션헤더", "도표/시각자료")으로 표시하지 마라. 약칭을 사용한다. 이유: 썸네일이 좁아 글자가 넘친다.
