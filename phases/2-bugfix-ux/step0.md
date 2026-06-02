# Step 0: backend-bugfix

## 읽어야 할 파일

먼저 아래 파일들을 읽고 현재 구현을 파악하라:

- `/home/user/Dadeum/CLAUDE.md`
- `/home/user/Dadeum/backend/app/pipeline/explainer.py`
- `/home/user/Dadeum/backend/app/pipeline/recommender.py`
- `/home/user/Dadeum/backend/tests/` (기존 테스트 패턴 파악)

## 배경

현재 UI에서 두 가지 백엔드 문제가 확인되었다:

1. **색상 오탐 버그**: 두 슬라이드의 dominant_color가 모두 `RGB(0,0,0)` (또는 동일한 값)일 때, `_cosine_similarity`는 두 영벡터를 받아 이미 `1.0`을 반환한다. 그런데 `explain()` 메서드가 similarity=1.0인 RootCause도 필터 없이 `causes` 리스트에 그대로 추가하여 정렬 후 반환하기 때문에, 실제로는 동일한 색상임에도 color 이슈로 잘못 보고된다.

2. **수정 제안 텍스트 품질**: `recommender.py`가 생성하는 수정 제안 메시지에 `RGB(r,g,b)` 같은 기술적 내부값이 노출되어 있어 사용자에게 의미 없는 정보를 표시한다.

## 작업

### 1. `backend/app/pipeline/explainer.py` — 고유사도 RootCause 필터링

현재 `explain()` 메서드는 4개 그룹 모두에 대해 RootCause를 생성한 뒤 similarity 오름차순으로 정렬만 한다. similarity가 높더라도(이상 없는 그룹이라도) 결과에 포함된다.

수정 위치: `explain()` 메서드의 `causes.sort(...)` 이후.

```python
# 기존
causes.sort(key=lambda c: c.similarity_score)
return causes[:5]

# 수정 후
causes.sort(key=lambda c: c.similarity_score)
causes = [c for c in causes if c.similarity_score < 0.95]
return causes[:5]
```

- similarity_score가 `0.95` 이상인 그룹은 "실질적 차이 없음"으로 간주하고 RootCause 목록에서 제외한다.
- `_cosine_similarity` 함수 자체는 수정하지 않는다 (영벡터 처리 로직은 이미 올바르다).

### 2. `backend/app/pipeline/recommender.py` — 수정 제안 텍스트 개선

수정 제안 메시지에서 `RGB(r,g,b)` 형식의 원시값 노출을 제거한다:

- 색상 관련 수정 제안: RGB 값 대신 "배경색", "텍스트 색상" 등 사람이 읽을 수 있는 표현으로 교체한다.
- 폰트 관련 수정 제안: 내부 feature 이름(예: `font_0`, `layout_ratio`) 대신 "폰트 종류", "여백 비율" 등으로 교체한다.
- 수정 제안 메시지는 한국어로, 60자 이내로 간결하게 작성한다.

예시:
- 변경 전: `"배경색을 RGB(0, 0, 0)에서 RGB(255, 255, 255)로 변경하세요"`
- 변경 후: `"배경색을 다른 슬라이드와 통일하세요"`

### 3. 테스트 추가

`backend/tests/test_explainer.py` (이미 존재하는 파일에 추가 — 먼저 파일을 읽어 기존 테스트 패턴을 파악하라):

- 동일한 색상값(dominant_color 동일)을 가진 아웃라이어 슬라이드를 입력했을 때 color feature_group의 RootCause가 결과에 포함되지 않는지 검증
- 모든 feature가 베이스라인과 동일한 슬라이드는 RootCause가 0개인지 검증

## Acceptance Criteria

```bash
cd /home/user/Dadeum/backend && pytest tests/ -q
```

에러 없이 통과해야 한다.

## 검증 절차

1. AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - 추론 로직이 `backend/app/pipeline/` 내에만 있는가?
   - CLAUDE.md CRITICAL 규칙 위반 없는가?
3. `phases/2-bugfix-ux/index.json` step 0을 업데이트한다:
   - 성공 → `"status": "completed"`, `"completed_at": "<ISO 타임스탬프>"`, `"summary": "산출물 한 줄 요약"`
   - 3회 시도 후 실패 → `"status": "error"`, `"error_message": "구체적 에러"`

## 금지사항

- `explainer.py`에서 임시방편으로 해당 feature 전체를 비활성화하지 마라. 오직 동일값일 때만 제외해야 한다.
- 수정 제안 메시지에 `RGB(`, `feature_`, `numpy`, `index` 같은 기술적 키워드를 남기지 마라.
- 기존 테스트를 깨뜨리지 마라.
