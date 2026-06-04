# Step 1: result-states

## 읽어야 할 파일

- `/frontend/src/pages/ResultPage.tsx` (수정 대상 — 전체 읽기)
- `/frontend/src/types/api.ts` (impact_score_after_fix 필드 확인)

## 문제

### 1. "분석 결과 v2" 태그
헤더의 `<span className="text-xs text-amber-400">v2</span>`는 개발 중 남긴 흔적이다. 서비스에 노출되면 안 된다.

### 2. 이상 슬라이드 0개일 때 빈 화면
`outlier_slides.length === 0`이면 점수 카드 아래에 아무것도 표시되지 않는다. 사용자는 분석이 끝난 건지, 결과가 없는 건지 알 수 없다.

### 3. 결과 완료 후 새 파일 분석 버튼 없음
에러 상태에서만 "다시 시도" 버튼이 있다. 정상 완료 후 새 파일을 분석하려면 직접 URL을 바꿔야 한다.

### 4. impact_score_after_fix 미표시
`result.impact_score_after_fix`는 백엔드가 계산해서 내려주지만 UI에서 사용하지 않는다.

## 작업

### 1. "v2" 태그 제거

```tsx
// 현재
<h1 className="text-2xl font-semibold text-white">분석 결과 <span className="text-xs text-amber-400">v2</span></h1>

// 수정 후
<h1 className="text-2xl font-semibold text-white">분석 결과</h1>
```

### 2. 이상 슬라이드 0개 상태 처리

`outlier_slides.length === 0`이고 `consistency_score.total >= 70`일 때, 슬라이드 목록과 상세 패널 대신 긍정적인 메시지를 표시하라.

```tsx
{result.outlier_slides.length === 0 ? (
  <div className="rounded-lg bg-[#111111] border border-neutral-800 p-8 text-center">
    <p className="text-lg text-white mb-2">디자인이 일관성 있게 구성되어 있습니다</p>
    <p className="text-sm text-neutral-400">이상 슬라이드가 감지되지 않았습니다.</p>
  </div>
) : (
  /* 기존 3패널 레이아웃 */
)}
```

### 3. 헤더에 "새 파일 분석" 버튼 추가

헤더 우측 버튼 그룹에 추가하라:

```tsx
<button
  type="button"
  onClick={() => navigate("/")}
  className="shrink-0 rounded-md border border-neutral-700 text-neutral-300 text-sm px-4 py-2 hover:border-neutral-500 transition-colors duration-150"
>
  새 파일 분석
</button>
```

### 4. impact_score_after_fix 표시

이상 슬라이드가 있을 때, 이상 슬라이드 알림 텍스트 옆에 예상 점수를 추가하라.

현재:
```tsx
<p className="text-sm text-amber-400">
  슬라이드 {result.slide_count}장 중{" "}
  <span className="font-medium">{result.outlier_slides.length}장</span>에서 디자인 이상 감지
</p>
```

수정 후:
```tsx
<p className="text-sm text-amber-400">
  슬라이드 {result.slide_count}장 중{" "}
  <span className="font-medium">{result.outlier_slides.length}장</span>에서 디자인 이상 감지
  {result.impact_score_after_fix > result.consistency_score.total && (
    <span className="ml-2 text-neutral-400">
      · 수정 시 <span className="text-white">{Math.round(result.impact_score_after_fix)}점</span> 예상
    </span>
  )}
</p>
```

## Acceptance Criteria

```bash
cd frontend
npm run build
npm run lint
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 결과에 따라 `phases/8-ux-polish/index.json`의 step 1을 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "v2 태그 제거, 0 outliers 긍정 피드백, 새 파일 분석 버튼, impact_score 표시"`
   - 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- 0 outliers 상태에서 SlideGrid, DetailPanel 등을 렌더링하지 마라. 이유: 선택할 슬라이드가 없어서 빈 상태 처리가 복잡해진다.
- `impact_score_after_fix`가 `consistency_score.total`보다 낮거나 같을 때 표시하지 마라. 이유: 수정해도 나빠지거나 변화 없는 경우 혼란을 준다.
