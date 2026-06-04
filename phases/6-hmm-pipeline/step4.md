# Step 4: schema-update

## 읽어야 할 파일

먼저 아래 파일들을 읽고 기존 스키마 구조를 파악하라:

- `/docs/ARCHITECTURE.md`
- `/backend/app/models/schemas.py` (현재 스키마)
- `/backend/tests/test_api.py` (API 테스트 — 스키마 변경 영향 파악)
- `/frontend/src/types/api.ts` (프론트엔드 타입 — 동기화 필요)

## 작업

### 1. `backend/app/models/schemas.py`

`SlideStats`와 `AnalysisResult`에 HMM 파이프라인 결과 필드를 추가하라.

**`SlideStats`에 추가:**
```python
slide_role: Optional[int] = None
# CNN이 예측한 역할 인덱스 (0=표지, 1=섹션헤더, 2=본문, 3=도표/시각자료, 4=마무리)
# RoleClassifier 없으면 None
```

**`AnalysisResult`에 추가:**
```python
role_sequence: Optional[list[int]] = None
# CNN 역할 예측 시퀀스 (슬라이드 순서대로)
# RoleClassifier 없으면 None

hmm_anomaly_score: Optional[float] = None
# HMM 기반 덱 전체 이상 점수 (0~1, 높을수록 이상)
# HMMScorer 없으면 None
```

- 기존 필드를 수정하거나 삭제하지 마라.
- 모든 새 필드는 `Optional`이고 기본값 `None`이어야 한다 (기존 클라이언트 호환성 유지).

### 2. `frontend/src/types/api.ts`

백엔드 스키마 변경과 동기화하라. `SlideStats`와 `AnalysisResult` 타입에 동일한 필드를 추가하라:

```typescript
// SlideStats에 추가
slide_role?: number | null;

// AnalysisResult에 추가
role_sequence?: number[] | null;
hmm_anomaly_score?: number | null;
```

- 이 프로젝트의 프론트엔드 타입은 **snake_case**를 사용한다 (`slide_index`, `impact_score_after_fix` 등 기존 필드 참고). camelCase로 변환하지 마라.
- 기존 타입을 수정하지 않도록 추가만 한다.

## Acceptance Criteria

```bash
cd backend
pytest tests/ -q

cd frontend
npm run build
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 기존 테스트가 모두 통과하는지 확인한다.
3. 프론트엔드 빌드 에러 없는지 확인한다.
4. 결과에 따라 `phases/6-hmm-pipeline/index.json`의 step 4를 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "SlideStats.slide_role, AnalysisResult.role_sequence/hmm_anomaly_score 추가 (Optional, 기본값 None), frontend api.ts 동기화"`
   - 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- 기존 필드(`consistency_score`, `outlier_slides` 등)를 수정하거나 타입을 바꾸지 마라. Optional 추가만 허용.
- `Required` 필드로 추가하지 마라. 기존 클라이언트가 이 필드 없이도 동작해야 한다.
