# Step 0: Notebook 01 — 데이터 준비 개선

## 개요

`notebooks/01_data_preparation.ipynb`는 ML 파이프라인의 시작점이다.  
현재 코드는 동작하지만 아래 4가지 문제가 있어 데이터 품질과 재현성이 떨어진다.

1. **약한 라벨 품질 저하**: `get_slide_features`가 이미지/텍스트만 보고 표/차트/SmartArt를 구분하지 못함
2. **에러 처리 부실**: LibreOffice 변환 실패가 조용히 무시되어 누락 데이터 파악 불가
3. **데이터 검증 없음**: 다운로드 후 PPTX가 손상됐는지 확인하지 않음
4. **클래스 불균형 미보고**: 라벨 저장 전 분포를 확인하지 않아 Notebook 02에서 뒤늦게 발견

---

## 읽어야 할 파일

- `notebooks/01_data_preparation.ipynb` — 전체 흐름 파악
- `CLAUDE.md` — `SlideFeatureExtractor` 위치 규칙 확인

---

## 개선 작업

### 1. `get_slide_features` — shape_type 분기 추가

현재 코드는 `shape_type == 13` (그림) 하나만 이미지로 인식한다.  
아래처럼 차트(MSO_SHAPE_TYPE.CHART=3), 테이블(19), SmartArt(24)를 시각 영역으로 함께 집계한다.

```python
from pptx.enum.shapes import MSO_SHAPE_TYPE

VISUAL_SHAPE_TYPES = {3, 13, 19, 24}  # Chart, Picture, Table, SmartArt

def get_slide_features(slide, slide_width, slide_height):
    """슬라이드에서 라벨링에 필요한 특징 추출"""
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

`assign_weak_label`도 반환값에 맞게 시그니처를 바꾸고, 테이블/차트가 있으면 `ROLE_VISUAL`로 바로 분류한다:

```python
def assign_weak_label(
    slide_idx: int,
    total_slides: int,
    word_count: int,
    visual_ratio: float,
    has_table: bool,
    has_chart: bool,
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

`records.append(...)` 호출부도 새 반환값에 맞게 수정한다. `image_ratio` 키도 `visual_ratio`로 변경한다:

```python
word_count, visual_ratio, has_table, has_chart = get_slide_features(slide, W, H)
label = assign_weak_label(i, n, word_count, visual_ratio, has_table, has_chart)

records.append({
    'deck_id': deck_id,
    'slide_idx': i,
    'total_slides': n,
    'position_ratio': i / max(n - 1, 1),
    'word_count': word_count,
    'visual_ratio': round(visual_ratio, 4),   # ← image_ratio 에서 이름 변경
    'has_table': has_table,
    'has_chart': has_chart,
    'weak_label': label,
    'role_name': ROLE_NAMES[label],
    'image_path': slide_png,
})
```

Notebook 02의 `SlideRoleDataset`이 `image_ratio` 컬럼을 읽는 부분이 있으면 반드시 `visual_ratio`로 함께 변경한다.

---

### 2. PPTX 유효성 검사 — 다운로드 직후 실행

다운로드 루프 내에서 저장 직후 `Presentation(fname)`을 열어 손상 여부를 확인한다.  
손상된 파일은 삭제하고 `corrupt` 리스트에 기록한다.

```python
from pptx import Presentation

def is_valid_pptx(path: str) -> bool:
    try:
        prs = Presentation(path)
        return len(prs.slides) > 0
    except Exception:
        return False

# 다운로드 루프 마지막에 추가
corrupt = []
for fname in list(downloaded):
    if not is_valid_pptx(fname):
        corrupt.append(fname)
        downloaded.remove(fname)
        os.remove(fname)

print(f'손상된 PPTX 제거: {len(corrupt)}개')
print(f'유효한 PPTX: {len(downloaded)}개')

with open(f'{LABELS_DIR}/corrupt_files.json', 'w') as f:
    json.dump(corrupt, f)
```

---

### 3. LibreOffice 변환 실패 — 상세 에러 저장

`pptx_to_thumbnails` 함수가 빈 리스트를 반환할 때 이유를 알 수 없다.  
`subprocess.run` 결과의 `returncode`와 `stderr`를 기록한다.

```python
def pptx_to_thumbnails(pptx_path: str, output_dir: str, size: int = 224):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            ['libreoffice', '--headless', '--norestore',
             '--convert-to', 'png', '--outdir', tmpdir, pptx_path],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            # 빈 리스트 대신 에러 정보를 포함한 예외를 발생시킴
            raise RuntimeError(f'LibreOffice 실패 (rc={result.returncode}): {result.stderr[:300]}')

        png_files = sorted(Path(tmpdir).glob('*.png'))
        if not png_files:
            raise RuntimeError('변환 성공이나 PNG 파일 없음')

        saved = []
        for i, png_path in enumerate(png_files):
            img = Image.open(png_path).convert('RGB')
            img = _letterbox(img, size)          # ← 직접 resize 금지
            out_path = f'{output_dir}/slide_{i:03d}.png'
            img.save(out_path, 'PNG', optimize=True)
            saved.append(out_path)
        return saved


def _letterbox(img: Image.Image, size: int = 224) -> Image.Image:
    """
    슬라이드 원본 비율(16:9)을 유지하면서 size×size 캔버스에 중앙 배치.
    직접 resize하면 가로가 세로보다 긴 슬라이드가 세로로 찌그러짐.
    흰색 패딩으로 여백을 채운다.
    """
    w, h = img.size
    scale = size / max(w, h)
    new_w, new_h = int(w * scale), int(h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new('RGB', (size, size), (255, 255, 255))
    offset_x = (size - new_w) // 2
    offset_y = (size - new_h) // 2
    canvas.paste(img, (offset_x, offset_y))
    return canvas
```

변환 루프의 `except` 블록도 에러 내용을 저장한다:

```python
except Exception as e:
    convert_errors.append({'deck_id': deck_id, 'error': str(e)})
```

변환 완료 후 에러 리스트를 JSON으로 저장한다:
```python
with open(f'{LABELS_DIR}/convert_errors.json', 'w') as f:
    json.dump(convert_errors, f, indent=2, ensure_ascii=False)
print(f'변환 에러 상세: {LABELS_DIR}/convert_errors.json')
```

---

### 4. 라벨 저장 전 클래스 불균형 체크 및 경고

`df.to_csv(...)` 호출 직전에 클래스 분포를 확인하고 비율이 10% 미만인 클래스에 경고를 출력한다.

```python
print('\n=== 클래스 분포 체크 ===')
dist = df['role_name'].value_counts(normalize=True)
for role, ratio in dist.items():
    flag = ' ⚠ 소수 클래스' if ratio < 0.10 else ''
    print(f'  {role}: {ratio:.1%}{flag}')

# 클래스 가중치 미리 계산해서 저장 (Notebook 02에서 바로 사용)
class_counts = df['weak_label'].value_counts().sort_index()
# numpy int64 키를 str로 변환해야 json.dump가 TypeError 없이 직렬화함
weights = {str(int(k)): float(1.0 / v) for k, v in class_counts.items()}
with open(f'{LABELS_DIR}/class_weights.json', 'w') as f:
    json.dump(weights, f, indent=2)
print('클래스 가중치 저장 완료')
```

---

### 5. HMM 시퀀스 — 짧은 덱 처리 개선

현재 `len(seq) >= 3` 조건으로 필터링하지만 이유가 없다.  
HMM은 최소 2개 관측이 필요하고, 1-슬라이드 덱은 구조 분석 의미가 없으므로 2 이상으로 변경한다:

```python
for deck_id, group in df.groupby('deck_id'):
    group = group.sort_values('slide_idx')
    seq = group['weak_label'].tolist()
    if len(seq) < 2:   # 1-슬라이드 덱은 HMM 학습에 불필요
        continue
    sequences.append({'deck_id': deck_id, 'sequence': seq, 'length': len(seq)})
```

---

## Acceptance Criteria

```
# Colab 셀 실행 기준
- get_slide_features 반환값이 (word_count, visual_ratio, has_table, has_chart) 4개인가?
- assign_weak_label 인자가 6개(slide_idx, total_slides, word_count, visual_ratio, has_table, has_chart)인가?
- 다운로드 후 corrupt_files.json이 생성되는가?
- 변환 에러 발생 시 convert_errors.json에 deck_id + error 문자열이 기록되는가?
- labels/class_weights.json이 생성되는가?
- weak_labels.csv의 컬럼 이름이 image_ratio → visual_ratio로 바뀌었는가?
```

## 금지사항

- `get_slide_features`에서 python-pptx `slide.shapes` 이외의 외부 의존성(OpenCV, pytesseract 등)을 추가하지 마라. 이 함수는 Colab 기본 환경에서 실행돼야 한다.
- `assign_weak_label`의 반환 타입을 변경하지 마라. `int` (ROLE_* 상수)를 그대로 반환한다.
- 다운로드 루프에서 `downloaded` 리스트를 순회 중 직접 수정하지 마라. 별도의 후처리 루프에서 `corrupt`를 제거하라.
- `_letterbox`를 `pptx_to_thumbnails` 함수 본문 안으로 인라인하지 마라. 독립 함수로 유지해야 Notebook 02에서 val_transform에도 동일 padding 로직을 적용할 수 있다.
- Notebook 02의 `SlideRoleDataset`이 `image_ratio` 컬럼 이름을 사용하고 있으면 반드시 함께 수정해야 한다. 이 step에서 양쪽을 모두 변경하거나, Notebook 02 step1에서 처리한다.
