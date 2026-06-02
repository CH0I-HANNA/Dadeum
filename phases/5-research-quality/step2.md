# Step 2: baseline-suite

## 읽어야 할 파일

먼저 아래 파일들을 읽어라:

- `/Users/choehanna/Documents/Dadeum/CLAUDE.md`
- `/Users/choehanna/Documents/Dadeum/notebooks/04_evaluation.ipynb` — 현재 파이프라인 평가
- `/Users/choehanna/Documents/Dadeum/notebooks/05_eval_realign.ipynb` — 합성 벤치마크
- `/Users/choehanna/Documents/Dadeum/phases/5-research-quality/step1.md`

**이 step의 동기:**

현재 유일한 베이스라인은 "PCA 없이 원본 임베딩으로 IF 돌리기"다.
이는 trivially 질 수밖에 없는 straw man baseline이다.
리뷰어가 가장 먼저 요구하는 것은 다양한 베이스라인과의 비교다.
이 step은 5개 베이스라인을 구현하고 합성 벤치마크와 SlideAudit에서 모두 비교한다.

이전 step에서 생성된 파일:
- `labels/synthetic_anomaly_benchmark.csv` (step0)
- `labels/weak_labels_clip.csv`, `models/role_classifier_clip_best.pt` (step1)

---

## 작업

`notebooks/07_baseline_suite.ipynb`를 새로 생성한다.

### 1. Baseline 정의

5개 베이스라인을 구현한다:

```python
BASELINES = {
    'B0_random':        'AUC=0.5 확인용 랜덤 스코어',
    'B1_position':      '슬라이드 수 편차만 사용 (정상 덱의 평균 길이에서 벗어나는 정도)',
    'B2_clip_zeroshot': 'CLIP 임베딩 + IF (CNN 학습 없음)',
    'B3_dino_if':       'DINOv2 ViT-S/14 임베딩 + Global IF (학습 없음)',
    'B4_text_bert':     'slide 텍스트를 SBERT로 임베딩 + IF (이미지 없음)',
}
```

### 2. B0: Random Baseline

```python
import numpy as np
from sklearn.metrics import roc_auc_score

np.random.seed(42)
random_scores = np.random.rand(len(benchmark_labels))
auc_b0 = roc_auc_score(benchmark_labels, random_scores)
print(f'B0 Random AUC: {auc_b0:.4f}  (expected ≈ 0.5)')
```

### 3. B1: Position-only Baseline

슬라이드 수의 이상도만으로 탐지한다.
정상 덱의 길이 분포에서 벗어날수록 이상으로 판정:

```python
import pandas as pd
from scipy.stats import zscore

df = pd.read_csv(f'{LABELS_DIR}/weak_labels.csv')
deck_lengths = df.groupby('deck_id').size()

normal_mean = deck_lengths.mean()
normal_std  = deck_lengths.std()

def length_anomaly_score(seq_len: int) -> float:
    z = abs(seq_len - normal_mean) / (normal_std + 1e-8)
    return float(np.clip(z / 3.0, 0, 1))
```

합성 벤치마크의 각 시퀀스 길이로 이상 점수를 계산해 AUC를 측정한다.

### 4. B2: CLIP 임베딩 + Global IF

```python
import open_clip, torch, pickle
from sklearn.ensemble import IsolationForest

model_clip, _, preprocess_clip = open_clip.create_model_and_transforms(
    'ViT-B-32', pretrained='openai'
)
model_clip = model_clip.to(device).eval()

def extract_clip_embeddings(image_paths: list, batch_size: int = 64) -> np.ndarray:
    all_emb = []
    for i in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[i:i+batch_size]
        imgs = torch.stack([
            preprocess_clip(Image.open(p).convert('RGB'))
            for p in batch_paths if Path(p).exists()
        ]).to(device)
        with torch.no_grad():
            emb = model_clip.encode_image(imgs)
            emb = emb / emb.norm(dim=-1, keepdim=True)
        all_emb.append(emb.cpu().numpy())
    return np.concatenate(all_emb)

# 학습 데이터 CLIP 임베딩으로 Global IF 학습
train_clip_emb = extract_clip_embeddings(train_image_paths)
clip_iso = IsolationForest(n_estimators=200, contamination=0.15, random_state=42)
clip_iso.fit(train_clip_emb)
```

### 5. B3: DINOv2 임베딩 + Global IF

```python
!pip install -q timm

import timm

dino_model = timm.create_model('vit_small_patch14_dinov2', pretrained=True, num_classes=0)
dino_model = dino_model.to(device).eval()

dino_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

def extract_dino_embeddings(image_paths: list, batch_size: int = 64) -> np.ndarray:
    # CLIP과 동일한 구조의 배치 추론
    ...

dino_iso = IsolationForest(n_estimators=200, contamination=0.15, random_state=42)
dino_iso.fit(dino_embeddings_train)
```

DINOv2는 슬라이드처럼 구조화된 이미지에서 EfficientNet보다 더 나은 범용 특징을 제공할 가능성이 있다. 이 baseline이 우리 학습 CNN보다 높으면 "학습 없는 방법이 더 낫다"는 중요한 발견이다.

### 6. B4: 텍스트 기반 SBERT Baseline

이미지 없이 텍스트만 사용하는 baseline. 시각 특징의 실제 기여를 검증한다:

```python
!pip install -q sentence-transformers

from sentence_transformers import SentenceTransformer

sbert = SentenceTransformer('all-MiniLM-L6-v2')

# weak_labels.csv의 이미지를 OCR하거나 stanford_slide의 텍스트 필드를 사용
# 텍스트 필드가 없으면 이 baseline을 skip하고 명시적으로 기록
text_col = 'text' if 'text' in df.columns else None
if text_col is None:
    print('텍스트 필드 없음 — B4 baseline skip. 이유: stanford_slide 이미지 전용 데이터셋')
    auc_b4 = None
else:
    ...
```

### 7. 결과 통합 및 시각화

모든 베이스라인과 제안 방법을 동일 플롯에 표시한다:

```python
results = {
    'B0_random':          auc_b0,
    'B1_position':        auc_b1,
    'B2_clip_if':         auc_b2,
    'B3_dino_if':         auc_b3,
    'B4_text_sbert':      auc_b4,
    'proposed_if_only':   auc_if_only_synth,
    'proposed_hmm_only':  auc_hmm_only_synth,
    'proposed_combined':  auc_combined_synth,
}

# 합성 벤치마크 결과 바 차트
fig, ax = plt.subplots(figsize=(10, 5))
names  = [k for k, v in results.items() if v is not None]
values = [v for v in results.values() if v is not None]
colors = ['gray' if n.startswith('B') else 'steelblue' for n in names]
ax.barh(names, values, color=colors)
ax.axvline(0.5, color='red', linestyle='--', label='Random')
ax.axvline(max(values), color='green', linestyle='--', label='Best')
ax.set_xlabel('AUC (합성 벤치마크)')
ax.set_title('베이스라인 비교 — 합성 구조 이상 벤치마크')
ax.legend()
plt.tight_layout()
plt.savefig(f'{MODELS_DIR}/baseline_comparison.png', dpi=120)
plt.show()

with open(f'{MODELS_DIR}/baseline_results.json', 'w') as f:
    json.dump({k: (float(v) if v is not None else None) for k, v in results.items()}, f, indent=2)
print(json.dumps(results, indent=2))
```

---

## Acceptance Criteria

```bash
python3 -c "
import json, ast, re
nb = json.load(open('notebooks/07_baseline_suite.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
ast.parse(re.sub(r'^[!%].*$', '', src, flags=re.MULTILINE))
print('OK: syntax')
"

python3 -c "
import json
nb = json.load(open('notebooks/07_baseline_suite.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
assert 'auc_b0' in src,               'random baseline missing'
assert 'length_anomaly_score' in src,  'position baseline missing'
assert 'open_clip' in src,             'CLIP baseline missing'
assert 'dinov2' in src or 'dino' in src, 'DINOv2 baseline missing'
assert 'baseline_results.json' in src, 'result save missing'
assert 'baseline_comparison.png' in src, 'comparison plot missing'
print('All checks passed')
"
```

## 검증 절차

1. AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - B0 AUC가 0.45~0.55 범위에 있는가? (범위 벗어나면 benchmark label 문제)
   - B3(DINOv2)가 제안 방법보다 높으면 → "학습 기반 CNN의 기여가 없다"는 발견으로 논문에 명시해야 함
   - `baseline_results.json`에 null 값은 명시적으로 skip 이유가 주석으로 코드에 있는가?
3. 결과 해석:
   - 제안 방법 > 모든 baseline → 기여 입증 가능
   - B3 DINOv2 > 제안 방법 → CNN 대신 DINOv2 특징 사용으로 방향 전환 필요
   - B1 position > 제안 방법 → 심각한 문제: 덱 길이만으로 더 잘 탐지됨 (weak label 문제 확인)
4. `phases/5-research-quality/index.json`의 step 2를 업데이트한다.

## 금지사항

- B3 DINOv2를 fine-tuning하지 마라. pretrained 그대로 사용해야 "학습 없는 baseline"으로 의미가 있다.
- 베이스라인 IF에 우리 파이프라인과 다른 `contamination` 값을 사용하지 마라. 동일한 0.15를 사용해야 공정한 비교다.
- B4 SBERT를 텍스트 없다는 이유로 0.5로 채우지 마라. 명시적으로 `None`으로 표시하고 skip 이유를 기록한다.
- 합성 벤치마크와 SlideAudit 결과를 같은 플롯에 섞지 마라. 두 평가가 다른 것을 측정하므로 반드시 분리해서 표시한다.
