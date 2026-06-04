# Step 2: detail-compare-role

## 읽어야 할 파일

- `/frontend/src/types/api.ts` (SlideStats.slide_role 필드 확인)
- `/frontend/src/components/report/DetailPanel.tsx` (수정 대상 — 전체 읽기)
- `/frontend/src/components/report/ComparePanel.tsx` (수정 대상 — 전체 읽기)

## 배경

`SlideStats.slide_role`은 CNN이 예측한 슬라이드 역할(0~4, null 가능)이다.  
현재 DetailPanel과 ComparePanel 모두 슬라이드 통계를 표시하지만 역할 정보는 누락되어 있다.

역할 인덱스 → 한글 이름:
```
0=표지, 1=섹션헤더, 2=본문, 3=도표/시각자료, 4=마무리
```

## 작업

### 1. `DetailPanel.tsx` 수정

슬라이드 통계 그리드에 **역할** 행을 추가하라. 정상 슬라이드 패널과 이상 슬라이드 패널 **둘 다** 수정한다.

```
기존 통계 순서:
주요 폰트 / 평균 폰트 크기 / 텍스트 영역 / 단어 수 / 요소 수

수정 후:
역할 / 주요 폰트 / 평균 폰트 크기 / 텍스트 영역 / 단어 수 / 요소 수
```

- `slide_role`이 `null`이면 역할 행 자체를 렌더링하지 않는다
- 역할 이름 표시: `["표지", "섹션헤더", "본문", "도표/시각자료", "마무리"][stats.slide_role]`

### 2. `ComparePanel.tsx` 수정

비교 테이블에 **역할** 행을 추가하라.

```
기존 행 순서:
주요 폰트 / 폰트 크기 / 텍스트 영역 / 단어 수 / 요소 수

수정 후:
역할 / 주요 폰트 / 폰트 크기 / 텍스트 영역 / 단어 수 / 요소 수
```

- `statsA.slide_role`이나 `statsB.slide_role` 중 하나라도 `null`이면 역할 행을 렌더링하지 않는다
- highlight 조건: 두 슬라이드의 역할이 다를 때 (`statsA.slide_role !== statsB.slide_role`)
- 역할 이름은 전체 이름 사용 ("섹션헤더", "도표/시각자료")

## Acceptance Criteria

```bash
cd frontend
npm run build
npm run lint
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 빌드/lint 에러 없는지 확인한다.
3. 결과에 따라 `phases/7-hmm-frontend/index.json`의 step 2를 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "DetailPanel + ComparePanel에 slide_role 행 추가, null이면 미렌더링"`
   - 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- `ResultPage.tsx`, `SlideGrid.tsx`, `SlideThumbnail.tsx` 수정 금지. 이 step은 DetailPanel과 ComparePanel만 담당한다.
- `slide_role`이 `null`일 때 "알 수 없음" 같은 fallback 텍스트를 표시하지 마라. 이유: 모델 미사용이 정상 상태이므로 빈 칸보다 행 자체를 숨기는 게 더 깔끔하다.
