# Step 2: cnn-training

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트 구조와 설계 의도를 파악하라:

- `/Users/choehanna/Documents/Dadeum/CLAUDE.md`
- `/Users/choehanna/Documents/Dadeum/docs/ARCHITECTURE.md`
- `/Users/choehanna/Documents/Dadeum/notebooks/02_cnn_role_classifier.ipynb`
- `/Users/choehanna/Documents/Dadeum/phases/4-ml-pipeline/step1.md` — weak_labels.csv 컬럼 구조, class_weights.json 포맷 확인

이전 step(data-prep)에서 `weak_labels.csv`에 `visual_ratio`(구 `image_ratio`) 컬럼이 추가됐고
`class_weights.json`이 `{"0": float, ..., "4": float}` 형태로 저장됐다.

---

## 작업

`notebooks/02_cnn_role_classifier.ipynb`에 아래 개선 사항을 적용한다.

### 1. 슬라이드 데이터 정규화 통계 계산

현재 `Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])`는 ImageNet 통계다.
슬라이드는 흰 배경·텍스트 위주라 자연 이미지와 픽셀 분포가 다르다.
데이터 로더 정의 전에 슬라이드 데이터 실제 통계를 계산하는 셀을 삽입한다:

```python
from tqdm import tqdm as tqdm_plain

sample_df = train_df.sample(min(5000, len(train_df)), random_state=42)
raw_transform = transforms.Compose([transforms.Resize((IMG_SIZE, IMG_SIZE)), transforms.ToTensor()])

mean_sum = torch.zeros(3)
sq_sum   = torch.zeros(3)
n = 0
for _, row in tqdm_plain(sample_df.iterrows(), total=len(sample_df), desc='정규화 통계 계산'):
    if not Path(row['image_path']).exists():
        continue
    t = raw_transform(Image.open(row['image_path']).convert('RGB'))
    mean_sum += t.mean(dim=(1, 2))
    sq_sum   += (t ** 2).mean(dim=(1, 2))
    n += 1

SLIDE_MEAN = (mean_sum / n).tolist()
SLIDE_STD  = ((sq_sum / n - torch.tensor(SLIDE_MEAN) ** 2).sqrt()).tolist()
print(f'슬라이드 mean: {[round(v, 4) for v in SLIDE_MEAN]}')
print(f'슬라이드 std:  {[round(v, 4) for v in SLIDE_STD]}')

# Notebook 04에서 동일한 값을 사용하도록 저장
import json
with open(f'{MODELS_DIR}/slide_norm.json', 'w') as f:
    json.dump({'mean': SLIDE_MEAN, 'std': SLIDE_STD}, f)
print(f'정규화 통계 저장: {MODELS_DIR}/slide_norm.json')
```

이후 `train_transform`과 `val_transform`의 `Normalize`에 `SLIDE_MEAN`, `SLIDE_STD`를 사용한다.
Notebook 04는 `models/slide_norm.json`을 로드해 동일한 값을 사용해야 임베딩 분포가 일치한다.

### 2. 데이터 증강 수정

슬라이드는 16:9 고정 방향이다. `RandomHorizontalFlip`을 제거하고 슬라이드에 적합한 증강으로 교체한다:

```python
train_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomAffine(degrees=0, translate=(0.03, 0.03), scale=(0.95, 1.05)),
    transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1),
    transforms.RandomGrayscale(p=0.05),
    transforms.ToTensor(),
    transforms.Normalize(mean=SLIDE_MEAN, std=SLIDE_STD),
])
```

### 3. 클래스 가중치 — class_weights.json에서 로드

step1에서 저장한 파일을 사용해 일관성을 유지한다.
파일이 없으면 train_df에서 직접 계산하는 fallback을 포함한다:

```python
json_path = Path(f'{LABELS_DIR}/class_weights.json')
if json_path.exists():
    with open(json_path) as f:
        raw = json.load(f)
    class_weights_list = [raw[str(i)] for i in range(NUM_CLASSES)]
    class_weights = torch.tensor(class_weights_list, dtype=torch.float32).to(device)
else:
    counts = train_df['weak_label'].value_counts().sort_index().values
    class_weights = torch.tensor(1.0 / counts, dtype=torch.float32).to(device)

class_weights = class_weights / class_weights.sum() * NUM_CLASSES
```

### 4. Label Smoothing

약한 라벨은 규칙 기반으로 오류율이 15~20%다. `label_smoothing=0.15`를 추가한다:

```python
criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.15)
```

### 5. 2단계 Backbone Freeze Fine-tuning

전체 파라미터를 처음부터 약한 라벨로 학습하면 과적합된다. 2단계 전략을 적용한다:

```python
# Stage 1: backbone 동결, head만 warm-up (5 epoch)
for param in model.backbone.parameters():
    param.requires_grad = False

optimizer_s1 = AdamW(model.classifier.parameters(), lr=3e-4, weight_decay=1e-2)
scheduler_s1 = CosineAnnealingLR(optimizer_s1, T_max=5, eta_min=1e-5)

for epoch in range(5):
    # 학습/검증 루프 (위와 동일 구조, optimizer_s1 사용)
    ...
    scheduler_s1.step()

# Stage 2: backbone 해제, 차등 학습률
for param in model.backbone.parameters():
    param.requires_grad = True

optimizer_s2 = AdamW([
    {'params': model.backbone.parameters(),   'lr': 1e-5},
    {'params': model.classifier.parameters(), 'lr': 1e-4},
], weight_decay=1e-2)
scheduler_s2 = CosineAnnealingLR(optimizer_s2, T_max=15, eta_min=1e-6)
```

Early stopping(`patience=5`)은 Stage 2에만 적용한다.

### 6. Mixed Precision Training

A100에서 FP16 활성화로 학습 속도 1.5~2× 향상한다:

```python
from torch.amp import autocast, GradScaler

scaler = GradScaler('cuda')

# 학습 루프 내
with autocast('cuda'):
    logits = model(imgs)
    loss   = criterion(logits, labels)

scaler.scale(loss).backward()
scaler.unscale_(optimizer)
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
scaler.step(optimizer)
scaler.update()
```

### 7. PCA 차원 축소 — Isolation Forest 입력 준비

임베딩 추출 완료 후 1536차원을 PCA로 축소한다.
Isolation Forest는 고차원에서 차원의 저주로 동작하지 않으므로 반드시 필요하다:

```python
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import pickle

# 변수명 주의: GradScaler와 구분하기 위해 pca_scaler 사용
pca_scaler = StandardScaler()
embeddings_scaled = pca_scaler.fit_transform(embeddings_np)

pca = PCA(n_components=0.95, svd_solver='full', random_state=42)
embeddings_pca = pca.fit_transform(embeddings_scaled)

print(f'PCA: {embeddings_np.shape[1]}차원 → {embeddings_pca.shape[1]}차원')
print(f'보존 분산: {pca.explained_variance_ratio_.sum():.3%}')

with open(f'{MODELS_DIR}/pca_model.pkl', 'wb') as f:
    pickle.dump({'scaler': pca_scaler, 'pca': pca}, f)

np.save(f'{LABELS_DIR}/embeddings_pca.npy', embeddings_pca)
```

### 8. UMAP 임베딩 시각화

임베딩이 역할별로 클러스터링됐는지 확인한다:

```python
!pip install -q umap-learn
import umap

SAMPLE_N   = 3000
sample_idx = np.random.choice(len(embeddings_np), min(SAMPLE_N, len(embeddings_np)), replace=False)
emb_2d     = umap.UMAP(n_components=2, random_state=42).fit_transform(embeddings_np[sample_idx])

fig, ax = plt.subplots(figsize=(10, 8))
for role_id in range(NUM_CLASSES):
    mask = labels_np[sample_idx] == role_id
    ax.scatter(emb_2d[mask, 0], emb_2d[mask, 1], label=ROLE_NAMES[role_id], alpha=0.6, s=10)

ax.legend(markerscale=3)
ax.set_title('EfficientNet-B3 임베딩 UMAP (역할별 색상)')
ax.axis('off')
plt.savefig(f'{MODELS_DIR}/embedding_umap.png', dpi=120)
plt.show()
```

---

## Acceptance Criteria

```bash
python3 -c "
import json, ast, re
nb = json.load(open('notebooks/02_cnn_role_classifier.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
ast.parse(re.sub(r'^[!%].*\$', '', src, flags=re.MULTILINE))
print('OK: notebooks/02_cnn_role_classifier.ipynb')
"

python3 -c "
import json
nb = json.load(open('notebooks/02_cnn_role_classifier.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
assert 'SLIDE_MEAN' in src,          'slide normalization missing'
assert 'GradScaler' in src,          'mixed precision missing'
assert 'requires_grad = False' in src, 'backbone freeze missing'
assert 'label_smoothing' in src,     'label smoothing missing'
assert 'PCA' in src,                 'PCA missing'
assert 'embeddings_pca' in src,      'PCA embeddings missing'
assert 'pca_model.pkl' in src,       'pca_model save missing'
assert 'RandomHorizontalFlip' not in src, 'HorizontalFlip not removed'
print('All checks passed')
"
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - `SLIDE_MEAN`, `SLIDE_STD`가 Normalize에 적용됐는가?
   - Stage 1(backbone frozen) → Stage 2(differential lr) 순서인가?
   - `pca_model.pkl`과 `embeddings_pca.npy`가 저장되는가?
   - `GradScaler`와 `clip_grad_norm_`이 함께 쓰이는가?
3. `phases/4-ml-pipeline/index.json`의 step 2를 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "NB02 CNN 개선: mixed precision, 2단계 freeze, PCA(embeddings_pca.npy), UMAP 시각화 추가"`
   - 수정 3회 시도 후에도 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`
   - 사용자 개입 필요 → `"status": "blocked"`, `"blocked_reason": "구체적 사유"` 후 즉시 중단

## 금지사항

- `Normalize`에 ImageNet 기본값(`[0.485, 0.456, 0.406]`)을 그대로 쓰지 마라. 슬라이드와 자연 이미지는 픽셀 분포가 다르다.
- Isolation Forest에 `embeddings.npy`(1536차원)를 직접 입력하지 마라. 반드시 PCA를 거친 `embeddings_pca.npy`를 사용한다.
- Stage 1 없이 처음부터 전체 fine-tuning하지 마라. 약한 라벨의 노이즈가 backbone에 과적합된다.
- `autocast` 블록을 검증 루프에 적용하지 마라. `torch.no_grad()`만으로 충분하다.
- `label_smoothing`을 0.3 이상으로 설정하지 마라. 모델이 아무것도 배우지 못한다.
- UMAP 설치(`!pip install -q umap-learn`) 셀을 주석 처리하지 마라. Colab 기본 환경에 없다.
