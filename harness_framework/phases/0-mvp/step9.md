# Step 9: frontend-result

## 읽어야 할 파일

- `frontend/src/types/api.ts`
- `frontend/src/services/api.ts`
- `frontend/src/pages/UploadPage.tsx` (스타일 일관성 확인)

## 작업

분석 결과 페이지를 구현하라. 이 페이지가 MVP의 핵심 화면이다.

### 1. useAnalysis hook

`frontend/src/hooks/useAnalysis.ts` 를 구현하라.

```typescript
interface UseAnalysisReturn {
  result: AnalysisResult | null;
  status: TaskStatus["status"];
  error: string | null;
}

export function useAnalysis(taskId: string): UseAnalysisReturn
```

`getResult` API를 1.5초 간격으로 폴링한다. `status === "completed"` 또는 `"error"` 가 되면 폴링을 중단한다. React Query의 `refetchInterval` 을 활용한다.

### 2. 컴포넌트 구조

```
ResultPage
├── ResultHeader          # 파일명, 슬라이드 수, 분석 완료 시각
├── ConsistencyScoreCard  # 총점 + 4개 세부 점수 바
├── SlideGrid             # 전체 슬라이드 썸네일 그리드
│   └── SlideThumbnail    # 개별 썸네일 (이상치면 amber 테두리)
└── DetailPanel           # 선택된 슬라이드의 원인 + 수정안
    ├── RootCauseList     # 원인 태그 목록
    └── RecommendationList # 수정안 + impact_score_delta
```

### 3. 각 컴포넌트 상세

**ConsistencyScoreCard**:
- 총점을 `text-5xl font-bold` 로 크게 표시
- 4개 세부 점수(폰트, 색상, 레이아웃, 콘텐츠)를 가로 바(bar) 형태로 표시
- 점수 70 이상: `#22c55e`, 40~70: `#f59e0b`, 40 미만: `#ef4444`

**SlideGrid**:
- `grid grid-cols-4 gap-3` 레이아웃
- 각 썸네일은 `GET /api/thumbnail/{file_id}/{slide_num}` 으로 이미지를 불러온다
- 이상 슬라이드: `border-2 border-amber-400` 테두리
- 슬라이드 클릭 시 DetailPanel에 해당 슬라이드 정보 표시

**DetailPanel**:
- 선택된 슬라이드가 없으면 "슬라이드를 선택하면 상세 분석 결과가 표시됩니다" 안내문
- 이상 슬라이드 선택 시: RootCause 태그 + Recommendation 목록
- 정상 슬라이드 선택 시: "이 슬라이드는 전체 디자인과 일관성이 높습니다" 표시
- Recommendation 항목마다 `+{delta}점` 예상 개선 효과 표시 (amber 색상)

**로딩/에러 상태**:
- `status === "pending" | "processing"` 일 때: 로딩 스피너 + "분석 중..." 텍스트
- `status === "error"` 일 때: 에러 메시지 + "다시 시도" 버튼 (UploadPage로 이동)

### 4. 레이아웃

UI_GUIDE.md의 레이아웃 규칙을 따른다:
- 결과 페이지: `max-w-6xl mx-auto`
- 좌측 슬라이드 그리드 (`w-2/3`) + 우측 상세 패널 (`w-1/3`)
- `gap-6` 간격

## Acceptance Criteria

```bash
cd frontend && npm run build   # 빌드 에러 없음
cd frontend && npm run lint    # lint 에러 없음
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 백엔드 서버를 실행하고 실제 PPTX 파일을 업로드하여 결과 페이지가 정상 렌더링되는지 확인한다.
3. 이상 슬라이드 썸네일에 amber 테두리가 표시되는지 확인한다.
4. 이상 슬라이드 클릭 시 DetailPanel에 원인과 수정안이 표시되는지 확인한다.
5. `phases/0-mvp/index.json` 의 step 9 를 업데이트한다.

## 금지사항

- UI_GUIDE.md의 AI 슬롭 안티패턴(glass morphism, gradient-text, 보라색 계열, 글로우 등)을 사용하지 마라.
- 폴링 interval을 1초 미만으로 설정하지 마라. 백엔드에 과부하를 줄 수 있다.
- `AnalysisResult` 를 컴포넌트 내부에서 직접 fetch하지 마라. 반드시 `useAnalysis` 훅을 통해서만 데이터를 가져온다.
