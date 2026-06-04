# Step 3: slide-renderer

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트 구조와 이전 step 산출물을 파악하라:

- `/docs/ARCHITECTURE.md`
- `/docs/ADR.md` (ADR-008: 썸네일 생성 방식)
- `/backend/app/api/thumbnail.py` (기존 PIL 렌더링 로직 — 참고만 하고 import 금지)
- `/backend/app/pipeline/parser.py` (SlideRaw 구조 파악)

## 배경 지식

`role_classifier.py`의 `predict(images)`는 `PIL.Image` 리스트를 입력받는다.  
`slide_renderer.py`는 PPTX 파일에서 슬라이드별 PIL Image를 생성해 CNN 추론에 공급한다.

렌더링 품질: python-pptx + Pillow 기반의 간략한 렌더링. LibreOffice 수준의 완벽한 재현은 불필요하다. CNN이 역할을 분류할 수 있을 정도의 시각 정보(텍스트 밀도, 이미지 유무, 레이아웃 구조)면 충분하다.

## 작업

TDD 순서로 진행하라: 테스트 먼저 작성 → 구현.

### 1. `backend/tests/test_slide_renderer.py` (테스트 먼저)

아래 케이스를 커버하라:

- 유효한 PPTX → 반환 리스트 길이 == 슬라이드 수
- 각 반환값이 `PIL.Image.Image` 인스턴스
- 각 이미지 크기가 `(224, 224)`
- 개별 슬라이드 렌더링 실패 시 흰색 224×224 이미지로 대체 (예외 전파 금지)
- 빈 슬라이드(텍스트/이미지 없음)도 정상 처리

테스트용 PPTX는 `python-pptx`로 인메모리 생성 후 `tmp_path`에 저장해 사용하라.

### 2. `backend/app/pipeline/slide_renderer.py` (구현)

```python
_CNN_SIZE = 224

def render_pptx_slides(file_path: Path, size: int = _CNN_SIZE) -> list[Image.Image]:
    """PPTX 파일의 각 슬라이드를 PIL Image (size×size RGB)로 렌더링한다.
    렌더링 실패한 슬라이드는 흰색 이미지로 대체한다.
    """
    ...
```

구현 가이드:
- `python-pptx`로 슬라이드를 파싱하고, Pillow로 각 슬라이드를 RGB 이미지로 그린다.
- 배경색, 도형 fill, 텍스트, 이미지 블롭을 순서대로 렌더링한다.
- 렌더링 후 `img.resize((size, size), Image.LANCZOS)`로 크기를 통일한다.
- `api/thumbnail.py`와 유사한 로직이지만 해당 파일을 import하지 않는다. 독립 구현한다.
- `parser.py`의 `parse_pptx()`를 사용해도 되지만, 이미지 블롭 접근을 위해 `Presentation` 객체를 직접 열어도 된다.

## Acceptance Criteria

```bash
cd backend
pytest tests/test_slide_renderer.py -v
pytest tests/ -q
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 기존 테스트가 모두 통과하는지 확인한다.
3. 결과에 따라 `phases/6-hmm-pipeline/index.json`의 step 3을 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "render_pptx_slides(file_path) → list[PIL.Image 224×224] 구현"`
   - 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`

## 금지사항

- `from app.api.thumbnail import ...` 금지. pipeline은 api에 의존하면 안 된다 (단방향 의존성: api → pipeline).
- PDF 렌더링은 구현하지 마라. PPTX 전용으로만 구현한다. PDF는 analysis_service에서 건너뛴다.
- 렌더링 실패 시 예외를 밖으로 전파하지 마라. 슬라이드별로 try/except 처리한다.
