# Step 4: Notebook 01 — 데이터 소스 교체 (Zenodo10K → jinaai/stanford_slide)

## 개요

현재 Notebook 01은 Zenodo10K(학술 논문 발표 슬라이드)를 사용한다.  
우리 서비스 대상은 비즈니스/교육용 슬라이드이므로 SlideShare 기반의 `jinaai/stanford_slide`로 교체한다.

변경 범위:
- **데이터 로드**: Zenodo10K → jinaai/stanford_slide, TARGET 5000 → 10000
- **이미지 추출**: stanford_slide가 이미지로 제공되면 LibreOffice 변환 단계 생략
- **약한 라벨**: python-pptx 없이 `position_ratio`만으로 단순화
- **CSV 출력 포맷**: Notebook 02~04와의 호환성 유지 (컬럼명 그대로)

step0의 PPTX 개선 내용(`get_slide_features`, `assign_weak_label` 확장 등)은 PPTX 데이터가 있을 때 별도로 적용한다.  
이 step은 데이터 소스 교체만 다룬다.

---

## 읽어야 할 파일

- `notebooks/01_data_preparation.ipynb` — 전체 흐름, 교체할 셀 파악
- `CLAUDE.md` — 아키텍처 규칙 확인

---

## 수정 작업

### 1. 패키지 설치 셀 수정

`## 1. 패키지 설치` 셀을 아래로 교체한다.  
stanford_slide는 이미지로 제공될 가능성이 높으므로 `python-pptx`와 `libreoffice`는 조건부로만 설치한다.

```python
# 필수 패키지 (이미지 기반 파이프라인)
!pip install -q datasets pillow tqdm pandas

# PPTX 파일이 제공되는 경우에만 아래 셀을 실행
# !pip install -q python-pptx
# !apt-get install -q libreoffice

print('설치 완료')
```

---

### 2. 데이터셋 구조 탐색 셀 추가 (NEW)

`## 2. Zenodo10K PPTX 다운로드` 섹션 앞에 아래 탐색 셀을 삽입한다.  
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

**탐색 결과를 확인한 뒤 아래 두 변수를 직접 수정하고 다음 셀을 실행한다:**

```python
# ← 위 탐색 결과를 보고 실제 필드 이름으로 수정
DECK_ID_FIELD  = 'deck_id'      # 덱(프레젠테이션) 식별자 필드
SLIDE_IDX_FIELD = 'slide_index' # 덱 내 슬라이드 순서 필드 (없으면 None)
IMAGE_FIELD    = 'image'        # 이미지 필드 (PIL.Image 또는 bytes)

# 필드가 없으면 None으로 유지하면 아래 로직에서 자동 처리
print(f'DECK_ID_FIELD  = {DECK_ID_FIELD}')
print(f'SLIDE_IDX_FIELD = {SLIDE_IDX_FIELD}')
print(f'IMAGE_FIELD    = {IMAGE_FIELD}')
```

---

### 3. 데이터 로드 셀 교체

기존 `Zenodo10K 메타데이터 로딩` 셀과 `PPTX 다운로드` 셀을 아래 하나의 셀로 교체한다.

**Colab 세션 재시작 시 재개 전략**:  
스트리밍 데이터셋은 재시작 시 처음부터 다시 읽어야 하므로 `samples`를 Google Drive에 저장한다.  
`SLIDES_DIR`의 파일 존재 여부가 "진짜 체크포인트" 역할을 하며, 이미지 저장 루프에서 이미 저장된 파일은 자동으로 건너뛴다.

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

`samples_cache.pkl`이 있으면 스트리밍을 다시 실행하지 않는다. 처음부터 다시 수집하려면 파일을 삭제한다.

---

### 4. 썸네일 추출 셀 교체 — 이미지 직접 사용 (LibreOffice 불필요)

기존 `pptx_to_thumbnails` 함수와 변환 루프를 아래로 교체한다.

**체크포인트 2**: 이미지 저장 루프는 이미 저장된 파일(`Path(out_path).exists()`)을 건너뛴다.  
세션이 끊겨도 `SLIDES_DIR` 안의 파일들이 그대로 남아 있으므로, 셀을 다시 실행하면 중단된 지점부터 자동으로 재개된다.

```python
from PIL import Image
import io

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
    """항목에서 PIL Image 추출 — bytes, PIL.Image, URL 순으로 시도"""
    raw = item.get(IMAGE_FIELD)
    if raw is None:
        return None
    if isinstance(raw, bytes):
        return Image.open(io.BytesIO(raw)).convert('RGB')
    if hasattr(raw, 'convert'):   # PIL.Image
        return raw.convert('RGB')
    return None


def get_deck_id(item: dict, fallback_idx: int) -> str:
    """덱 식별자 추출 — DECK_ID_FIELD 없으면 URL 해시 또는 인덱스로 대체"""
    if DECK_ID_FIELD and DECK_ID_FIELD in item:
        return str(item[DECK_ID_FIELD])
    # URL 기반 해시
    url = item.get('url') or item.get('source') or ''
    if url:
        import hashlib
        return 'deck_' + hashlib.md5(url.encode()).hexdigest()[:8]
    # 최후 수단: 순번 기반 (덱 그룹화 포기, 슬라이드 하나가 하나의 덱)
    return f'deck_{fallback_idx:05d}'


def get_slide_idx(item: dict) -> int | None:
    """덱 내 슬라이드 순서 — 없으면 None (삽입 순서로 대체)"""
    if SLIDE_IDX_FIELD and SLIDE_IDX_FIELD in item:
        return int(item[SLIDE_IDX_FIELD])
    return None


# 이미지 추출 및 저장
all_slide_paths = {}   # deck_id → [(slide_idx, path), ...]
save_errors = []

for i, item in enumerate(tqdm(samples, desc='이미지 저장')):
    deck_id = get_deck_id(item, i)
    slide_idx = get_slide_idx(item)

    out_dir = Path(f'{SLIDES_DIR}/{deck_id}')
    out_dir.mkdir(parents=True, exist_ok=True)

    # slide_idx가 없으면 덱 내 삽입 순서로 부여
    if slide_idx is None:
        existing = len(list(out_dir.glob('*.png')))
        slide_idx = existing

    out_path = str(out_dir / f'slide_{slide_idx:03d}.png')

    # 이미 저장된 경우 스킵 (체크포인트)
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

# 체크포인트 갱신
with open(checkpoint_path, 'w') as f:
    json.dump({'processed': total_slides, 'decks': len(all_slide_paths)}, f)

with open(f'{LABELS_DIR}/save_errors.json', 'w') as f:
    json.dump(save_errors, f, indent=2)
```

---

### 5. 약한 라벨 생성 셀 교체 — position_ratio 기반 단순화

python-pptx 없이 슬라이드 내부를 파싱할 수 없으므로 위치 정보만으로 라벨을 부여한다.  
기존 5-클래스에서 3-클래스(표지·본문·마무리)만 사용한다.

`## 4. 약한 라벨(Weak Label) 자동 생성` 섹션 전체를 아래로 교체한다.

```python
ROLE_COVER   = 0
ROLE_SECTION = 1   # 이 step에서 미사용 — Notebook 02 class_weights 주의사항 참고
ROLE_BODY    = 2
ROLE_VISUAL  = 3   # 이 step에서 미사용
ROLE_CLOSING = 4
ROLE_NAMES   = ['표지', '섹션헤더', '본문', '도표/시각자료', '마무리']


def assign_weak_label_image(slide_idx: int, total_slides: int) -> int:
    """
    이미지 기반 약한 라벨 — python-pptx 없이 위치만으로 분류.
    클래스 1(섹션헤더), 3(도표)은 할당하지 않음.
    """
    if slide_idx == 0:
        return ROLE_COVER
    if slide_idx == total_slides - 1:
        return ROLE_CLOSING
    return ROLE_BODY


records = []

for deck_id, slides in tqdm(all_slide_paths.items(), desc='약한 라벨 생성'):
    slides_sorted = sorted(slides, key=lambda x: x[0])  # slide_idx 기준 정렬
    n = len(slides_sorted)

    for rank, (slide_idx, img_path) in enumerate(slides_sorted):
        position_ratio = rank / max(n - 1, 1)
        label = assign_weak_label_image(rank, n)

        records.append({
            'deck_id':        deck_id,
            'slide_idx':      rank,               # 덱 내 정렬 순서 (0-based)
            'total_slides':   n,
            'position_ratio': round(position_ratio, 4),
            'word_count':     0,                  # PPTX 없음 — 기본값
            'visual_ratio':   0.0,                # PPTX 없음 — 기본값
            'has_table':      False,
            'has_chart':      False,
            'weak_label':     label,
            'role_name':      ROLE_NAMES[label],
            'image_path':     img_path,
        })

df = pd.DataFrame(records)
print(f'총 슬라이드: {len(df)}장')
print('\n역할별 분포:')
print(df['role_name'].value_counts())
print('\n⚠ 클래스 1(섹션헤더), 3(도표)은 이 데이터셋에서 미사용.')
print('  → Notebook 02 class_weights 계산 시 해당 클래스 제외 필요 (step1 금지사항 참고)')
```

---

### 6. 클래스 불균형 체크 및 저장

라벨 CSV 저장 전 클래스 분포를 확인한다.  
클래스 1, 3은 샘플이 없으므로 `class_weights.json`에서 해당 키를 0으로 처리하지 않도록 주의한다.

```python
print('\n=== 클래스 분포 체크 ===')
dist = df['role_name'].value_counts(normalize=True)
for role, ratio in dist.items():
    flag = ' ⚠ 소수 클래스' if ratio < 0.10 else ''
    print(f'  {role}: {ratio:.1%}{flag}')

# 클래스 가중치 — 존재하는 클래스만 계산
class_counts = df['weak_label'].value_counts().sort_index()
present_classes = class_counts.index.tolist()
absent_classes  = [i for i in range(5) if i not in present_classes]

if absent_classes:
    print(f'\n⚠ 부재 클래스 {absent_classes}: class_weights.json에 weight=0 저장')
    print('  Notebook 02의 class_weights 로드 코드가 absent class를 건너뛰도록 수정 필요')

# weight=0 은 CrossEntropyLoss에서 해당 클래스를 무시하는 효과
weights = {}
for i in range(5):
    if i in class_counts.index:
        weights[str(i)] = float(1.0 / class_counts[i])
    else:
        weights[str(i)] = 0.0   # absent class — CrossEntropyLoss가 무시

with open(f'{LABELS_DIR}/class_weights.json', 'w') as f:
    json.dump(weights, f, indent=2)

label_path = f'{LABELS_DIR}/weak_labels.csv'
df.to_csv(label_path, index=False)
print(f'\n저장 완료: {label_path}')
```

---

## 다운스트림 호환성 주의사항

### Notebook 02 (CNN)

`class_weights.json`에서 클래스 1, 3의 weight가 0.0이다.  
step1의 `class_weights` 로드 코드에서 weight=0인 클래스를 CrossEntropyLoss에 그대로 전달하면 해당 클래스를 무시(mask)하는 효과가 있어 동작 자체는 정상이다.  
단, 모델은 클래스 1, 3을 예측하지 못하므로 Notebook 02의 `classification_report`에서 해당 클래스는 0으로 표시된다.

### Notebook 03 (HMM)

`sequences.csv`의 시퀀스에 0, 2, 4만 등장한다.  
HMM의 `n_observations`는 5로 유지하되, 실제 등장하는 전이는 0→2, 2→2, 2→4로 단순해진다.  
BIC 탐색에서 n_components가 작은 값(3)으로 선택될 가능성이 높다.

### Notebook 04 (평가)

입력 형식(이미지 경로, CSV)이 동일하므로 변경 불필요.

---

## Acceptance Criteria

```
- load_dataset('jinaai/stanford_slide', split='train', streaming=True) 로 로드하는가?
- TARGET = 10000 인가?
- 데이터셋 탐색 셀이 컬럼 이름과 타입을 출력하는가?
- DECK_ID_FIELD, SLIDE_IDX_FIELD, IMAGE_FIELD 변수를 명시적으로 선언하는가?
- _letterbox 함수가 정의되고 이미지 저장에 사용되는가?
- python-pptx / libreoffice 설치 코드가 주석 처리되어 있는가?
- assign_weak_label_image 함수가 position 기반으로만 라벨을 부여하는가?
- weak_labels.csv에 word_count, visual_ratio, has_table, has_chart 컬럼이 기본값으로 존재하는가?
- class_weights.json에서 부재 클래스(1, 3)의 weight가 0.0인가?
- stanford_checkpoint.json 체크포인트가 저장되는가?
```

## 완료 후 커밋

모든 Acceptance Criteria 통과 확인 후 `develop` 브랜치에 커밋한다.

```bash
git add notebooks/01_data_preparation.ipynb
git commit -m "feat(data): replace zenodo10k with jinaai/stanford_slide dataset

- change data source to stanford_slide (SlideShare-based business/edu slides)
- increase TARGET from 5000 to 10000
- add dataset structure exploration cell
- skip LibreOffice conversion; use images directly with letterbox resize
- simplify weak labels to position-based (cover/body/closing only)
- add samples_cache.pkl checkpoint for Colab session resume
- maintain weak_labels.csv schema compatibility with notebooks 02-04"
```

커밋 범위: `notebooks/01_data_preparation.ipynb` 만 포함한다.  
`phases/4-ml-pipeline/` 변경이 있으면 별도 커밋으로 분리한다:

```bash
git add phases/4-ml-pipeline/
git commit -m "docs(phases): add step4 for stanford_slide data source migration"
```

---

## 금지사항

- 탐색 셀(`## 2-A. 데이터셋 구조 탐색`) 결과를 확인하기 전에 이후 셀을 실행하지 마라. DECK_ID_FIELD, IMAGE_FIELD가 틀리면 모든 슬라이드가 단일 덱으로 그룹화되거나 이미지가 None으로 처리된다.
- `class_weights.json`에서 부재 클래스를 키에서 제거하지 마라. Notebook 02의 로드 코드가 `raw[str(i)] for i in range(5)` 형태로 5개 키를 모두 참조하므로 KeyError가 발생한다.
- `weak_labels.csv`에서 `word_count`, `visual_ratio`, `has_table`, `has_chart` 컬럼을 빼지 마라. Notebook 02의 `SlideRoleDataset`이 이 컬럼들을 참조할 수 있다.
- `assign_weak_label_image`를 확장해 이미지 픽셀 분석(밝기, 색 분포 등)으로 SECTION, VISUAL을 추론하려 하지 마라. 이 step의 범위를 벗어나며, 해당 기능은 PPTX 개선(step0)에서 다룬다.
- Notebook 02~04를 수정하지 마라. CSV 포맷 호환성으로 기존 노트북이 그대로 작동해야 한다.
