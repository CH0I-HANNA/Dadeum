# 프로젝트: 다듬 (Dadeum)

## 기술 스택

### Frontend
- React 18 + TypeScript (strict mode)
- Vite (빌드 도구)
- TailwindCSS v3
- React Query (서버 상태 관리)
- React Router v6

### Backend
- FastAPI (Python 3.11+)
- Pydantic v2 (스키마/검증)
- In-memory task store (서버 재시작 시 소멸 — ADR-009)
- python-pptx, pdfplumber (파싱)

### AI Pipeline
- Scikit-learn (Isolation Forest — MVP)
- PyTorch + AutoEncoder (Advanced)
- PyTorch Geometric + NetworkX (GNN — Research)
- NumPy, Pillow (Feature 추출)

## 아키텍처 규칙

- CRITICAL: 모든 AI 추론 로직은 `backend/app/pipeline/` 내 모듈에서만 처리한다. API 라우터에 추론 코드를 직접 작성하지 마라.
- CRITICAL: Feature Extraction은 `extractor.py`의 `SlideFeatureExtractor` 클래스에서만 구현한다. 다른 모듈이 python-pptx 객체를 직접 파싱하지 마라.
- CRITICAL: 프론트엔드에서 AI 모델을 직접 호출하지 마라. 반드시 FastAPI 엔드포인트를 통해서만 통신한다.
- Pydantic 스키마는 `backend/app/models/` 에만 정의한다. 동일 스키마를 여러 곳에 중복 정의하지 마라.
- TypeScript 타입은 `frontend/src/types/` 에만 정의한다. 컴포넌트 파일에 인라인 타입 정의 금지.
- API 응답 타입은 `frontend/src/types/api.ts` 에 정의하고 백엔드 Pydantic 스키마와 동기화를 유지한다.

## 개발 프로세스

- CRITICAL: 새 기능 구현 시 반드시 테스트를 먼저 작성하고, 테스트가 통과하는 구현을 작성할 것 (TDD)
- CRITICAL: Feature Extractor의 출력 스키마가 바뀌면 Outlier Detector, Explainer, Recommender 모두 영향받는다. 변경 전 downstream 의존성을 확인하라.
- 커밋 메시지는 conventional commits 형식을 따를 것 (feat:, fix:, docs:, refactor:, test:, chore:)

## 명령어

### Frontend
```
cd frontend
npm run dev      # 개발 서버 (http://localhost:5173)
npm run build    # 프로덕션 빌드
npm run lint     # ESLint
npm run test     # Vitest
```

### Backend
```
cd backend
uvicorn app.main:app --reload   # 개발 서버 (http://localhost:8000)
pytest                          # 테스트
```

### AI Pipeline (독립 실행)
```
cd backend
python -m app.pipeline.run_pipeline --file sample.pptx
```
