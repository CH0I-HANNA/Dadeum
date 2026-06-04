# Step 3: result-page-update

## 읽어야 할 파일

- `/frontend/src/pages/ResultPage.tsx` (수정 대상 — 전체 읽기)
- `/frontend/src/hooks/useAnalysis.ts` (수정 대상)
- `/frontend/src/components/score/StructureScoreCard.tsx` (step 0 산출물)
- `/frontend/src/components/slides/SlideGrid.tsx` (step 1 산출물 — slideStats prop 추가됨)

## 작업

### 1. `useAnalysis.ts` — stage 메시지 업데이트

현재 `getStage` 함수는 30초 이후 모두 "결과 생성 중..."을 반환한다.  
CNN 추론이 CPU에서 30~90초 소요될 수 있으므로 메시지를 확장하라.

```ts
// 현재
function getStage(elapsed: number, status: string): string {
  if (elapsed < 5)  return "파일 파싱 중...";
  if (elapsed < 15) return "특징 추출 중...";
  if (elapsed < 30) return "이상 슬라이드 탐지 중...";
  return "결과 생성 중...";
}

// 수정 후
function getStage(elapsed: number, status: string): string {
  if (elapsed < 5)  return "파일 파싱 중...";
  if (elapsed < 15) return "특징 추출 중...";
  if (elapsed < 30) return "이상 슬라이드 탐지 중...";
  if (elapsed < 90) return "발표 구조 분석 중...";  // CNN + HMM 단계
  return "결과 생성 중...";
}
```

### 2. `ResultPage.tsx` — StructureScoreCard 삽입

`ConsistencyScoreCard` 바로 아래에 추가하라:

```tsx
import StructureScoreCard from "../components/score/StructureScoreCard";

// ConsistencyScoreCard 아래
<StructureScoreCard
  roleSequence={result.role_sequence}
  hmmAnomalyScore={result.hmm_anomaly_score}
/>
```

### 3. `ResultPage.tsx` — SlideGrid에 slideStats 전달

기존 `SlideGrid` 호출에 `slideStats` prop 추가:

```tsx
<SlideGrid
  fileId={result.file_id}
  slideCount={result.slide_count}
  outlierSlides={filteredOutlierSlides}
  selectedSlide={activeSlide}
  compareSlide={compareMode ? compareSlide : null}
  onSelectSlide={handleSelectSlide}
  slideStats={result.slide_stats}
/>
```

## Acceptance Criteria

```bash
cd frontend
npm run build
npm run lint
npm test
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 빌드/lint/테스트 모두 통과하는지 확인한다.
3. 레이아웃 순서 확인: `ConsistencyScoreCard` → `StructureScoreCard` → 이상 슬라이드 알림 → 3패널
4. 결과에 따라 `phases/7-hmm-frontend/index.json`의 step 3을 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "ResultPage에 StructureScoreCard 삽입 + SlideGrid slideStats 연결, useAnalysis stage 90초까지 확장"`
   - 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- `StructureScoreCard` 로직을 `ResultPage`에 인라인으로 작성하지 마라. 이유: 컴포넌트 분리 원칙 위반.
- `result.role_sequence`나 `result.hmm_anomaly_score`에 대한 별도 null 체크를 `ResultPage`에 추가하지 마라. 이유: `StructureScoreCard` 내부에서 처리한다.
- `useAnalysis.ts`에서 `CLIENT_TIMEOUT`(120_000ms)을 수정하지 마라. 타임아웃은 클라이언트 기준이고, 백엔드 타임아웃(180초)과 별도다.
