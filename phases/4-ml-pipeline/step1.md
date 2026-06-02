# Step 1: data-prep

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트 구조와 설계 의도를 파악하라:

- `/Users/choehanna/Documents/Dadeum/CLAUDE.md`
- `/Users/choehanna/Documents/Dadeum/docs/ARCHITECTURE.md`
- `/Users/choehanna/Documents/Dadeum/notebooks/01_data_preparation.ipynb` — step0 완료 후 상태
- `/Users/choehanna/Documents/Dadeum/phases/4-ml-pipeline/step0.md` — step0에서 변경된 내용 파악

이전 step(data-source)에서 NB01이 stanford_slide 기반 이미지 파이프라인으로 교체됐다.

**이 step의 전제 조건**: PPTX 파일이 실제로 제공되는 데이터셋을 사용할 때만 적용한다.
stanford_slide(이미지 전용)로 실행한 경우 이 step은 skip한다.
NB01 첫 셀에서 아래를 확인하고 결정한다:

```python
# PPTX 데이터 여부 확인
has_pptx = len(list(Path(PPTX_DIR).glob('*.pptx'))) > 0
print(f'PPTX 데이터 존재: {has_pptx}')
# has_pptx == False 이면 이 step은 skip
```

PPTX가 없으면 `phases/4-ml-pipeline/index.json`의 step 1을 즉시
`"status": "completed"`, `"summary": "PPTX 데이터 없음 — stanford_slide 이미지 파이프라인에서 skip"` 으로 업데이트하고 종료한다.

---

## 작업

`notebooks/01_data_preparation.ipynb`에 아래 개선 사항을 추가한다.

### 1. `get_slide_features` — shape_type 분기 추가

현재 코드는 `shape_type == 13` (그림)만 이미지로 인식한다.
차트(3), 테이블(19), SmartArt(24)를 시각 영역으로 함께 집계하도록 수정한다.

```python
from pptx.enum.shapes import MSO_SHAPE_TYPE

VISUAL_SHAPE_TYPES = {3, 13, 19, 24}  # Chart, Picture, Table, SmartArt

def get_slide_features(slide, slide_width, slide_height):
    total_area = slide_width * slide_height
    word_count = 0
    visual_area = 0
    has_table = False
    has_chart = False

    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    word_count += len(run.text.split())
        if shape.shape_type in VISUAL_SHAPE_TYPES:
            visual_area += shape.width * shape.height
            if shape.shape_type == 3:
                has_chart = True
            if shape.shape_type == 19:
                has_table = True

    visual_ratio = min(visual_area / (total_area + 1e-8), 1.0)
    return word_count, visual_ratio, has_table, has_chart
```

`assign_weak_label`도 시그니처를 변경하고 테이블/차트가 있으면 `ROLE_VISUAL`로 즉시 분류한다:

```python
def assign_weak_label(
    slide_idx: int, total_slides: int,
    word_count: int, visual_ratio: float,
    has_table: bool, has_chart: bool,
) -> int:
    position_ratio = slide_idx / max(total_slides - 1, 1)
    if slide_idx == 0:
        return ROLE_COVER
    if slide_idx == total_slides - 1:
        return ROLE_CLOSING
    if has_table or has_chart or visual_ratio > 0.40:
        return ROLE_VISUAL
    if word_count < 15 and 0.05 < position_ratio < 0.85:
        return ROLE_SECTION
    return ROLE_BODY
```

`records.append(...)` 호출부를 새 반환값에 맞게 수정한다. `image_ratio` 키를 `visual_ratio`로 변경한다:

```python
word_count, visual_ratio, has_table, has_chart = get_slide_features(slide, W, H)
label = assign_weak_label(i, n, word_count, visual_ratio, has_table, has_chart)

records.append({
    'deck_id':        deck_id,
    'slide_idx':      i,
    'total_slides':   n,
    'position_ratio': round(i / max(n - 1, 1), 4),
    'word_count':     word_count,
    'visual_ratio':   round(visual_ratio, 4),   # image_ratio → visual_ratio
    'has_table':      has_table,
    'has_chart':      has_chart,
    'weak_label':     label,
    'role_name':      ROLE_NAMES[label],
    'image_path':     slide_png,
})
```

### 2. `_letterbox` 함수 적용

step0(data-source)에서 `_letterbox`가 이미 정의됐다. 재정의하지 말고 호출만 한다.
step0을 거치지 않고 이 step을 단독 실행하는 경우에만 아래 정의를 추가한다.

`pptx_to_thumbnails` 내 저장 루프를 수정한다:

```python
img = Image.open(png_path).convert('RGB')
img = _letterbox(img, size)   # ← 기존 img.resize 대체
```

### 3. LibreOffice 에러 상세 저장

`pptx_to_thumbnails` 함수가 빈 리스트를 반환할 때 원인을 알 수 없다.
`subprocess.run` 실패 시 `RuntimeError`를 발생시켜 변환 루프 `except` 블록에서 기록한다:

```python
def pptx_to_thumbnails(pptx_path: str, output_dir: str, size: int = 224):
    ...
    if result.returncode != 0:
        raise RuntimeError(f'LibreOffice 실패 (rc={result.returncode}): {result.stderr[:300]}')
    if not png_files:
        raise RuntimeError('변환 성공이나 PNG 파일 없음')
    ...
```

변환 루프 `except` 블록:

```python
except Exception as e:
    convert_errors.append({'deck_id': deck_id, 'error': str(e)})
```

변환 완료 후 에러 리스트를 JSON으로 저장한다:

```python
with open(f'{LABELS_DIR}/convert_errors.json', 'w') as f:
    json.dump(convert_errors, f, indent=2, ensure_ascii=False)
```

### 4. PPTX 유효성 검사

다운로드 루프 완료 후 별도 루프에서 손상된 PPTX를 제거한다:

```python
def is_valid_pptx(path: str) -> bool:
    try:
        prs = Presentation(path)
        return len(prs.slides) > 0
    except Exception:
        return False

corrupt = []
for fname in list(downloaded):
    if not is_valid_pptx(fname):
        corrupt.append(fname)
        downloaded.remove(fname)
        os.remove(fname)

with open(f'{LABELS_DIR}/corrupt_files.json', 'w') as f:
    json.dump(corrupt, f)
```

### 5. 클래스 가중치 저장

라벨 CSV 저장 전에 실행한다. numpy int64 키를 str로 변환해야 `json.dump`가 TypeError 없이 직렬화된다:

```python
class_counts = df['weak_label'].value_counts().sort_index()
weights = {str(int(k)): float(1.0 / v) for k, v in class_counts.items()}
with open(f'{LABELS_DIR}/class_weights.json', 'w') as f:
    json.dump(weights, f, indent=2)
```

### 6. HMM 시퀀스 — 최소 길이 조정

1-슬라이드 덱은 HMM 학습에 불필요하므로 `len(seq) >= 3` → `len(seq) >= 2`로 변경한다.

---

## Acceptance Criteria

```bash
python3 -c "
import json, ast, re
nb = json.load(open('notebooks/01_data_preparation.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
ast.parse(re.sub(r'^[!%].*\$', '', src, flags=re.MULTILINE))
print('OK: notebooks/01_data_preparation.ipynb')
"

python3 -c "
import json
nb = json.load(open('notebooks/01_data_preparation.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
assert 'VISUAL_SHAPE_TYPES' in src, 'shape_type expansion missing'
assert '_letterbox' in src, '_letterbox missing'
assert 'visual_ratio' in src, 'visual_ratio column missing'
assert 'convert_errors' in src, 'error logging missing'
assert 'class_weights.json' in src, 'class_weights save missing'
print('All checks passed')
"
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - `get_slide_features`가 `slide.shapes` 이외의 외부 의존성을 추가하지 않았는가?
   - `weak_labels.csv` 컬럼에 `visual_ratio`가 있고 `image_ratio`가 없는가?
   - `_letterbox`가 `pptx_to_thumbnails` 밖에 독립 함수로 정의됐는가?
   - 노트북 셀이 위에서 아래로 순서대로 실행 가능한가?
3. `phases/4-ml-pipeline/index.json`의 step 1을 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "NB01 PPTX 피처 개선: shape_type 확장, letterbox, 에러 저장, class_weights.json 생성"`
   - 수정 3회 시도 후에도 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`
   - 사용자 개입 필요 → `"status": "blocked"`, `"blocked_reason": "구체적 사유"` 후 즉시 중단

## 금지사항

- `get_slide_features`에서 OpenCV, pytesseract 등 외부 의존성을 추가하지 마라. 이 함수는 Colab 기본 환경에서 실행돼야 한다.
- `assign_weak_label`의 반환 타입을 변경하지 마라. `int` (ROLE_* 상수)를 그대로 반환한다.
- 다운로드 루프 순회 중 `downloaded` 리스트를 직접 수정하지 마라. 별도 루프에서 `corrupt`를 제거한다.
- `class_weights.json` 저장 시 `json.dump`에 numpy int64 타입을 직접 넣지 마라. 반드시 `str(int(k))`, `float(v)` 변환 후 저장한다.
