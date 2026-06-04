# Step 0: structure-score-card

## 읽어야 할 파일

- `/docs/UI_GUIDE.md`
- `/frontend/src/types/api.ts` (role_sequence, hmm_anomaly_score 필드 확인)
- `/frontend/src/components/score/ConsistencyScoreCard.tsx` (카드 디자인 패턴 참고)

## 배경

백엔드 HMM 파이프라인은 두 값을 반환한다:
- `hmm_anomaly_score: number | null` — 발표 구조 이상 점수 (0~1, **높을수록 이상**, ConsistencyScore와 반대)
- `role_sequence: number[] | null` — CNN이 예측한 슬라이드별 역할 인덱스 배열

역할 인덱스:
| 인덱스 | 역할 | 표시 약칭 |
|--------|------|----------|
| 0 | 표지 | 표지 |
| 1 | 섹션헤더 | 섹션 |
| 2 | 본문 | 본문 |
| 3 | 도표/시각자료 | 도표 |
| 4 | 마무리 | 마무리 |

**주의: 두 값은 독립적으로 null일 수 있다.** 모델 미사용 시 둘 다 null, 오류 시 한 쪽만 null 가능.

## 작업

`frontend/src/components/score/StructureScoreCard.tsx`를 새로 생성하라.

```tsx
interface Props {
  roleSequence: number[] | null | undefined;
  hmmAnomalyScore: number | null | undefined;
}

export default function StructureScoreCard({ roleSequence, hmmAnomalyScore }: Props)
```

### null 처리 규칙

- `roleSequence`와 `hmmAnomalyScore` **둘 다** null/undefined이면 `null` 반환 (컴포넌트 미렌더링)
- 한 쪽만 있으면 있는 것만 표시한다

### 1. 이상 점수 섹션 (hmmAnomalyScore가 있을 때)

- 점수를 0~100으로 환산: `Math.round(hmmAnomalyScore * 100)`
- 점수 색상 (ConsistencyScore와 **반대** — 낮을수록 좋음):
  - 0~30: `#22c55e` (green, 양호)
  - 31~60: `#f59e0b` (amber, 주의)
  - 61~100: `#ef4444` (red, 위험)
- 레이블: "발표 구조 이상 점수"
- 설명 텍스트: "발표 흐름이 자연스러울수록 낮게 나타납니다" (text-xs text-neutral-500)
- **중요**: `hmmAnomalyScore === 0`일 때도 정상 표시해야 한다. `if (!hmmAnomalyScore)` 대신 `if (hmmAnomalyScore == null)` 로 체크하라.

### 2. 역할 시퀀스 섹션 (roleSequence가 있을 때)

- 각 역할을 칩(pill) 형태로 가로 나열하고 `→` 화살표로 연결
- 역할별 텍스트 색상: 표지=`text-purple-400`, 섹션=`text-blue-400`, 본문=`text-neutral-300`, 도표=`text-green-400`, 마무리=`text-orange-400`
- **슬라이드가 많을 때 처리**: 12개 초과 시 처음 6개 + `···` + 마지막 3개만 표시
  - 예: `[표지, 섹션, 본문, 본문, 본문, 본문] ··· [본문, 본문, 마무리]`
  - `···` 위에 hover 시 전체 개수 표시: `title={전체 ${roleSequence.length}장}`
- 가로 스크롤 금지. 잘라서 표시하라.

### 디자인

- 카드 스타일: `rounded-lg bg-[#111111] border border-neutral-800 p-4`
- `ConsistencyScoreCard`와 같은 시각 언어 사용

## Acceptance Criteria

```bash
cd frontend
npm run build
npm run lint
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 결과에 따라 `phases/7-hmm-frontend/index.json`의 step 0을 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "StructureScoreCard 생성: hmm_anomaly_score 게이지 + role_sequence 흐름(12개 초과 시 truncate), 각각 null 독립 처리"`
   - 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- `ResultPage.tsx` 수정 금지. 이 step은 컴포넌트 생성만 담당한다.
- 인라인 타입 정의 금지. 타입은 `frontend/src/types/api.ts`에서 import한다.
- `overflow-x-auto` + 긴 시퀀스 그대로 나열 금지. 12개 초과 시 반드시 잘라서 표시한다. 이유: 슬라이드 30장짜리 발표에서 가로 스크롤이 매우 길어져 UI가 깨진다.
