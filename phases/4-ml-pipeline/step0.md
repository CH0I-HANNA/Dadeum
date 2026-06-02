# Step 0: data-source

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트 구조와 설계 의도를 파악하라:

- `/Users/choehanna/Documents/Dadeum/CLAUDE.md`
- `/Users/choehanna/Documents/Dadeum/docs/ARCHITECTURE.md`
- `/Users/choehanna/Documents/Dadeum/notebooks/01_data_preparation.ipynb` — 교체할 셀 파악

---

## 작업

`notebooks/01_data_preparation.ipynb`의 데이터 소스를 Zenodo10K에서 `jinaai/stanford_slide`로 교체한다.

변경 범위:
- 데이터 로드: Zenodo10K → jinaai/stanford_slide, TARGET 5000 → 10000
- 이미지 추출: stanford_slide가 이미지로 제공되면 LibreOffice 변환 단계 생략
- 약한 라벨: python-pptx 없이 `position_ratio`만으로 단순화
- CSV 출력 포맷: Notebook 02~04와의 호환성 유지 (컬럼명 그대로)

### 1. 패키지 설치 셀 수정

`## 1. 패키지 설치` 셀을 아래로 교체한다.
stanford_slide는 이미지로 제공될 가능성이 높으므로 `python-pptx`와 `libreoffice`는 조건부 주석으로만 남긴다.

```python
!pip install -q datasets pillow tqdm pandas

# PPTX 파일이 제공되는 경우에만 아래 셀을 실행
# !pip install -q python-pptx
# !apt-get install -q libreoffice

print('설치 완료')
```

### 2. 데이터셋 구조 탐색 셀 추가 (NEW)

`## 2. Zenodo10K PPTX 다운로드` 섹션 앞에 삽입한다.
이 셀을 먼저 실행해 컬럼 이름을 확인한 뒤, 이후 셀에서 필드 이름을 맞춰야 한다.

```python
from datasets import load_dataset

print('jinaai/stanford_slide 데이터셋 구조 탐색 중...')
ds_explore = load_dataset('jinaai/stanford_slide', split='train', streaming=True)

first_items = []
for item in ds_explore:
    first_items.append(item)
    if len(first_items) >= 3:
        break

print(f'\n컬럼 목록: {list(first_items[0].keys())}')
print('\n각 컬럼 타입 및 샘플 값:')
for key, val in first_items[0].items():
    print(f'  {key}: {type(val).__name__} = {repr(val)[:120]}')

print('\n--- 덱 구조 파악용: 첫 3개 항목 비교 ---')
CANDIDATE_DECK_FIELDS = ['deck_id', 'presentation_id', 'pptx_id', 'source', 'url', 'id']
CANDIDATE_IDX_FIELDS  = ['slide_index', 'slide_idx', 'page_no', 'page', 'index', 'position']

for i, item in enumerate(first_items):
    print(f'\n항목 {i}:')
    for field in CANDIDATE_DECK_FIELDS + CANDIDATE_IDX_FIELDS:
        if field in item:
            print(f'  {field}: {repr(item[field])[:80]}')
```

탐색 결과를 확인한 뒤 아래 변수를 수정하는 셀을 삽입한다:

```python
# ← 위 탐색 결과를 보고 실제 필드 이름으로 수정
DECK_ID_FIELD   = 'deck_id'      # 덱(프레젠테이션) 식별자 필드
SLIDE_IDX_FIELD = 'slide_index'  # 덱 내 슬라이드 순서 필드 (없으면 None)
IMAGE_FIELD     = 'image'        # 이미지 필드 (PIL.Image 또는 bytes)

print(f'DECK_ID_FIELD   = {DECK_ID_FIELD}')
print(f'SLIDE_IDX_FIELD = {SLIDE_IDX_FIELD}')
print(f'IMAGE_FIELD     = {IMAGE_FIELD}')
```

### 3. 데이터 로드 셀 교체

기존 `Zenodo10K 메타데이터 로딩` 셀과 `PPTX 다운로드` 셀을 아래 하나의 셀로 교체한다.

세션 재시작 시 재개 전략: 스트리밍 데이터셋은 재시작 시 처음부터 다시 읽어야 하므로
`samples`를 Google Drive에 pickle로 캐싱한다.
`SLIDES_DIR`의 파일 존재 여부가 이미지 저장 루프의 체크포인트 역할을 한다.

```python
from datasets import load_dataset
from pathlib import Path
from PIL import Image
import io, json, pickle
from tqdm import tqdm

TARGET = 10000   # 기존 5000 → 10000

# 체크포인트 1: samples 캐시 (Drive에 저장 — 스트리밍 재로딩 방지)
samples_cache = Path(f'{LABELS_DIR}/samples_cache.pkl')

if samples_cache.exists():
    with open(samples_cache, 'rb') as f:
        samples = pickle.load(f)
    print(f'samples 캐시 로드 완료: {len(samples)}개 (스트리밍 재로딩 건너뜀)')
else:
    print(f'jinaai/stanford_slide 스트리밍 로딩 중... (목표: {TARGET}장)')
    ds = load_dataset('jinaai/stanford_slide', split='train', streaming=True)
    samples = []
    for item in tqdm(ds, total=TARGET, desc='샘플 수집'):
        samples.append(item)
        if len(samples) >= TARGET:
            break
    with open(samples_cache, 'wb') as f:
        pickle.dump(samples, f)
    print(f'수집 완료: {len(samples)}개 → {samples_cache} 저장')

print(f'첫 항목 키: {list(samples[0].keys())}')
```

### 4. 썸네일 추출 셀 교체

기존 `pptx_to_thumbnails` 함수와 변환 루프를 아래로 교체한다.

체크포인트 2: 이미지 저장 루프에서 `Path(out_path).exists()`를 확인해 이미 저장된 파일을 건너뛴다.
세션이 끊겨도 `SLIDES_DIR` 안의 파일이 남아 있으므로 셀 재실행 시 자동 재개된다.

```python
IMG_SIZE = 224

def _letterbox(img: Image.Image, size: int = 224) -> Image.Image:
    """비율 유지 후 흰색 패딩으로 size×size 캔버스 채움"""
    w, h = img.size
    scale = size / max(w, h)
    new_w, new_h = int(w * scale), int(h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new('RGB', (size, size), (255, 255, 255))
    canvas.paste(img, ((size - new_w) // 2, (size - new_h) // 2))
    return canvas

def extract_image(item: dict) -> Image.Image | None:
    raw = item.get(IMAGE_FIELD)
    if raw is None:
        return None
    if isinstance(raw, bytes):
        return Image.open(io.BytesIO(raw)).convert('RGB')
    if hasattr(raw, 'convert'):
        return raw.convert('RGB')
    return None

def get_deck_id(item: dict, fallback_idx: int) -> str:
    if DECK_ID_FIELD and DECK_ID_FIELD in item:
        return str(item[DECK_ID_FIELD])
    url = item.get('url') or item.get('source') or ''
    if url:
        import hashlib
        return 'deck_' + hashlib.md5(url.encode()).hexdigest()[:8]
    return f'deck_{fallback_idx:05d}'

def get_slide_idx(item: dict) -> int | None:
    if SLIDE_IDX_FIELD and SLIDE_IDX_FIELD in item:
        return int(item[SLIDE_IDX_FIELD])
    return None

all_slide_paths = {}
save_errors = []

for i, item in enumerate(tqdm(samples, desc='이미지 저장')):
    deck_id  = get_deck_id(item, i)
    slide_idx = get_slide_idx(item)
    out_dir  = Path(f'{SLIDES_DIR}/{deck_id}')
    out_dir.mkdir(parents=True, exist_ok=True)
    if slide_idx is None:
        slide_idx = len(list(out_dir.glob('*.png')))
    out_path = str(out_dir / f'slide_{slide_idx:03d}.png')
    if Path(out_path).exists():
        all_slide_paths.setdefault(deck_id, []).append((slide_idx, out_path))
        continue
    img = extract_image(item)
    if img is None:
        save_errors.append({'idx': i, 'deck_id': deck_id, 'reason': 'image_field_missing'})
        continue
    _letterbox(img, IMG_SIZE).save(out_path, 'PNG', optimize=True)
    all_slide_paths.setdefault(deck_id, []).append((slide_idx, out_path))

total_slides = sum(len(v) for v in all_slide_paths.values())
print(f'저장 완료: {len(all_slide_paths)}개 덱, {total_slides}장 슬라이드')
print(f'에러: {len(save_errors)}건')

with open(f'{LABELS_DIR}/save_errors.json', 'w') as f:
    json.dump(save_errors, f, indent=2)

# 체크포인트 갱신 (samples_cache와 별개로 진행 현황 기록)
checkpoint_path = Path(f'{LABELS_DIR}/stanford_checkpoint.json')
with open(checkpoint_path, 'w') as f:
    json.dump({'processed': total_slides, 'decks': len(all_slide_paths)}, f)
```

### 5. 약한 라벨 생성 셀 교체

`## 4. 약한 라벨(Weak Label) 자동 생성` 섹션 전체를 아래로 교체한다.
python-pptx 없이 위치 정보만으로 라벨을 부여한다.

```python
ROLE_COVER   = 0
ROLE_SECTION = 1   # 미사용
ROLE_BODY    = 2
ROLE_VISUAL  = 3   # 미사용
ROLE_CLOSING = 4
ROLE_NAMES   = ['표지', '섹션헤더', '본문', '도표/시각자료', '마무리']

def assign_weak_label_image(slide_idx: int, total_slides: int) -> int:
    if slide_idx == 0:
        return ROLE_COVER
    if slide_idx == total_slides - 1:
        return ROLE_CLOSING
    return ROLE_BODY

records = []
for deck_id, slides in tqdm(all_slide_paths.items(), desc='약한 라벨 생성'):
    slides_sorted = sorted(slides, key=lambda x: x[0])
    n = len(slides_sorted)
    for rank, (slide_idx, img_path) in enumerate(slides_sorted):
        label = assign_weak_label_image(rank, n)
        records.append({
            'deck_id':        deck_id,
            'slide_idx':      rank,
            'total_slides':   n,
            'position_ratio': round(rank / max(n - 1, 1), 4),
            'word_count':     0,
            'visual_ratio':   0.0,
            'has_table':      False,
            'has_chart':      False,
            'weak_label':     label,
            'role_name':      ROLE_NAMES[label],
            'image_path':     img_path,
        })

df = pd.DataFrame(records)
print(f'총 슬라이드: {len(df)}장')
print(df['role_name'].value_counts())
print('\n⚠ 클래스 1(섹션헤더), 3(도표)은 미사용 — Notebook 02 class_weights 주의')
```

### 6. 클래스 가중치 저장

```python
print('\n=== 클래스 분포 체크 ===')
for role, ratio in df['role_name'].value_counts(normalize=True).items():
    flag = ' ⚠ 소수 클래스' if ratio < 0.10 else ''
    print(f'  {role}: {ratio:.1%}{flag}')

class_counts = df['weak_label'].value_counts().sort_index()

# 부재 클래스(1, 3)는 weight=0.0 — CrossEntropyLoss가 자동 무시
weights = {str(i): float(1.0 / class_counts[i]) if i in class_counts.index else 0.0
           for i in range(5)}
with open(f'{LABELS_DIR}/class_weights.json', 'w') as f:
    json.dump(weights, f, indent=2)

df.to_csv(f'{LABELS_DIR}/weak_labels.csv', index=False)
print(f'저장 완료: {LABELS_DIR}/weak_labels.csv')
```

---

## Acceptance Criteria

```bash
# NB01 코드 셀 Python 구문 검사
python3 -c "
import json, ast, re
nb = json.load(open('notebooks/01_data_preparation.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
ast.parse(re.sub(r'^[!%].*\$', '', src, flags=re.MULTILINE))
print('OK: notebooks/01_data_preparation.ipynb')
"

# 필수 변경 사항 확인
python3 -c "
import json
nb = json.load(open('notebooks/01_data_preparation.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
assert 'jinaai/stanford_slide' in src, 'data source not changed'
assert 'TARGET = 10000' in src, 'TARGET not updated'
assert '_letterbox' in src, '_letterbox function missing'
assert 'assign_weak_label_image' in src, 'weak label function missing'
assert 'samples_cache' in src, 'checkpoint missing'
print('All checks passed')
"
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - Google Drive 경로(`BASE_DIR = '/content/drive/MyDrive/dadeum_ml'`)가 유지됐는가?
   - `weak_labels.csv`에 `word_count`, `visual_ratio`, `has_table`, `has_chart` 컬럼이 존재하는가?
   - `class_weights.json`에 키 `"0"~"4"` 5개가 모두 존재하는가?
   - 노트북 셀이 위에서 아래로 순서대로 실행 가능한가?
3. `phases/4-ml-pipeline/index.json`의 step 0을 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "NB01 데이터 소스를 stanford_slide로 교체, TARGET=10000, letterbox/checkpoint 추가"`
   - 수정 3회 시도 후에도 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`
   - 사용자 개입 필요 → `"status": "blocked"`, `"blocked_reason": "구체적 사유"` 후 즉시 중단

## 금지사항

- 탐색 셀 결과를 확인하기 전에 이후 셀을 실행하지 마라. DECK_ID_FIELD, IMAGE_FIELD가 틀리면 모든 슬라이드가 단일 덱으로 그룹화되거나 이미지가 None으로 처리된다.
- `class_weights.json`에서 부재 클래스를 키에서 제거하지 마라. Notebook 02의 로드 코드가 `raw[str(i)] for i in range(5)` 형태로 5개 키를 모두 참조하므로 KeyError가 발생한다.
- `weak_labels.csv`에서 `word_count`, `visual_ratio`, `has_table`, `has_chart` 컬럼을 빼지 마라. Notebook 02의 `SlideRoleDataset`이 이 컬럼들을 참조할 수 있다.
- `assign_weak_label_image`를 픽셀 분석으로 확장하지 마라. 이 step의 범위를 벗어난다.
- Notebook 02~04를 수정하지 마라. CSV 포맷 호환성으로 기존 노트북이 그대로 작동해야 한다.
