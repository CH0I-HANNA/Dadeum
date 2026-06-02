# Step 1: Notebook 02 — CNN 역할 분류기 개선

## 개요

`notebooks/02_cnn_role_classifier.ipynb`는 EfficientNet-B3로 슬라이드 역할을 분류한다.  
현재 코드는 동작하지만 A100 GPU를 충분히 활용하지 못하고, 약한 라벨(Weak Label)의 노이즈를 고려하지 않아 과적합 위험이 있다.

개선 포인트:
1. **Mixed Precision 미사용**: A100에서 FP16 활성화 시 학습 속도 1.5~2× 향상
2. **데이터 증강 부적절**: 슬라이드는 가로/세로 방향이 고정돼 있어 `RandomHorizontalFlip`이 오히려 방해
3. **Label Smoothing 없음**: 약한 라벨은 10~20% 오류율이 있으므로 hard-target CrossEntropy는 노이즈에 취약
4. **Early Stopping 없음**: 검증 정확도가 plateau에 도달해도 계속 학습해 시간 낭비
5. **임베딩 시각화 없음**: 역할별 클러스터링을 눈으로 확인할 방법이 없음

---

## 읽어야 할 파일

- `notebooks/02_cnn_role_classifier.ipynb` — 전체 흐름
- `notebooks/01_data_preparation.ipynb` — weak_labels.csv 컬럼 구조 확인

---

## 개선 작업

### 1. Mixed Precision Training (torch.amp)

`## 4. 학습` 섹션의 학습 루프를 Mixed Precision으로 교체한다.

```python
from torch.amp import autocast, GradScaler

scaler = GradScaler('cuda')

for epoch in range(EPOCHS):
    model.train()
    train_loss = 0.0
    t0 = time.time()

    for imgs, labels in train_loader:
        imgs, labels = imgs.to(device), labels.to(device)
        optimizer.zero_grad()

        with autocast('cuda'):           # FP16 자동 전환
            logits = model(imgs)
            loss = criterion(logits, labels)

        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)  # 그래디언트 클리핑
        scaler.step(optimizer)
        scaler.update()

        train_loss += loss.item()

    # ... (검증 루프는 변경 없음, torch.no_grad() 내부는 autocast 불필요)
```

`GradScaler`와 `clip_grad_norm_`은 한 셋으로 항상 같이 쓴다. 클리핑 없이 FP16을 쓰면 gradient explosion 위험이 있다.

---

### 2. Normalize 값 — ImageNet 통계 대신 슬라이드 데이터 실측값 사용

현재 `Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])`는 ImageNet 통계다.  
슬라이드는 흰 배경·텍스트 위주라 자연 이미지와 픽셀 분포가 크게 다르다. 잘못된 정규화는 훈련 초기에 gradient를 불안정하게 만든다.

데이터 로더 정의 전에 아래 셀로 실제 통계를 계산한다:

```python
from tqdm import tqdm as tqdm_plain

# 서브샘플 5000장으로 계산 (전체 계산 시 너무 오래 걸림)
sample_df = train_df.sample(min(5000, len(train_df)), random_state=42)
raw_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
])

mean_sum = torch.zeros(3)
sq_sum = torch.zeros(3)
n = 0

for _, row in tqdm_plain(sample_df.iterrows(), total=len(sample_df), desc='정규화 통계 계산'):
    if not Path(row['image_path']).exists():
        continue
    img = Image.open(row['image_path']).convert('RGB')
    t = raw_transform(img)           # (3, 224, 224)
    mean_sum += t.mean(dim=(1, 2))
    sq_sum += (t ** 2).mean(dim=(1, 2))
    n += 1

SLIDE_MEAN = (mean_sum / n).tolist()
SLIDE_STD = ((sq_sum / n - torch.tensor(SLIDE_MEAN) ** 2).sqrt()).tolist()
print(f'슬라이드 mean: {[round(v, 4) for v in SLIDE_MEAN]}')
print(f'슬라이드 std:  {[round(v, 4) for v in SLIDE_STD]}')
```

이후 `train_transform`과 `val_transform`의 `Normalize`에 `SLIDE_MEAN`, `SLIDE_STD`를 사용한다:

```python
transforms.Normalize(mean=SLIDE_MEAN, std=SLIDE_STD)
```

Notebook 04의 `transform`도 동일한 값으로 교체해야 한다. 두 노트북에서 다른 정규화를 쓰면 임베딩 분포가 달라진다.

---

### 3. 데이터 증강 수정 — 슬라이드 특성 반영

슬라이드는 항상 가로가 긴 직사각형이고 좌우 대칭 콘텐츠가 없다. `RandomHorizontalFlip`을 제거하고 슬라이드에 적합한 증강으로 교체한다.

```python
train_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    # RandomHorizontalFlip 제거: 슬라이드는 좌우 반전 시 텍스트가 뒤집혀 의미 없음
    transforms.RandomAffine(
        degrees=0,
        translate=(0.03, 0.03),   # 미세 이동 (레이아웃 견고성)
        scale=(0.95, 1.05),       # 미세 스케일 변화
    ),
    transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1),
    transforms.RandomGrayscale(p=0.05),   # 흑백 슬라이드 대비
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])
```

---

### 4. Backbone Freeze — 2단계 Fine-tuning

현재 전체 파라미터(backbone + head)를 lr=1e-4로 처음부터 학습한다.  
EfficientNet-B3의 1200만 파라미터 전체가 noisy weak label을 기억하려 하면 과적합이 빠르게 발생한다.

2단계 전략: **1단계 → head만 warm-up → 2단계 → backbone 전체 fine-tune (낮은 lr)**

```python
# 1단계: backbone 동결, head만 학습 (5 epoch)
for param in model.backbone.parameters():
    param.requires_grad = False

optimizer_stage1 = AdamW(model.classifier.parameters(), lr=3e-4, weight_decay=1e-2)
scheduler_stage1 = CosineAnnealingLR(optimizer_stage1, T_max=5, eta_min=1e-5)

print('=== Stage 1: Head warm-up (backbone frozen) ===')
for epoch in range(5):
    # 학습 루프 (위와 동일, optimizer_stage1 사용)
    ...
    scheduler_stage1.step()

# 2단계: backbone 해제, 차등 학습률 적용
for param in model.backbone.parameters():
    param.requires_grad = True

optimizer_stage2 = AdamW([
    {'params': model.backbone.parameters(), 'lr': 1e-5},  # backbone: 낮은 lr
    {'params': model.classifier.parameters(), 'lr': 1e-4}, # head: 높은 lr
], weight_decay=1e-2)
scheduler_stage2 = CosineAnnealingLR(optimizer_stage2, T_max=15, eta_min=1e-6)

print('=== Stage 2: Full fine-tune (differential lr) ===')
for epoch in range(15):
    # 학습 루프 (optimizer_stage2 사용)
    ...
    scheduler_stage2.step()
```

Stage 1 5 epoch + Stage 2 15 epoch = 총 20 epoch으로 기존 epoch 수를 유지한다.  
Early stopping은 Stage 2에만 적용한다 (Stage 1은 head warm-up이므로 전 과정 실행).

---

### 5. Label Smoothing 적용

약한 라벨(Weak Label)은 규칙 기반으로 생성되어 실제 오류율이 15~20%다.  
`nn.CrossEntropyLoss`에 `label_smoothing=0.15`를 추가해 모델이 과도하게 확신하는 것을 방지한다.

```python
# 기존
criterion = nn.CrossEntropyLoss(weight=class_weights)

# 개선
criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.15)
```

`label_smoothing` 값 가이드:
- `0.0`: 노이즈 없는 완벽한 라벨일 때
- `0.1`: 약간의 어노테이션 오류 (사람이 작성한 경우)
- `0.15~0.2`: 규칙 기반 약한 라벨처럼 오류율이 높을 때

---

### 6. Early Stopping 추가

20 epoch 모두 학습하지 않고, 검증 정확도가 `patience=5` epoch 동안 개선되지 않으면 중단한다.

```python
# 학습 루프 시작 전에 추가
patience = 5
no_improve_count = 0

# 학습 루프 내 최고 모델 저장 블록 뒤에 추가
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        no_improve_count = 0
        torch.save({...}, f'{MODELS_DIR}/role_classifier_best.pt')
        print(f'  → 최고 모델 저장 (val_acc={val_acc:.4f})')
    else:
        no_improve_count += 1
        if no_improve_count >= patience:
            print(f'\nEarly stopping at epoch {epoch+1} (no improvement for {patience} epochs)')
            break
```

---

### 7. 클래스 가중치 — class_weights.json에서 로드

Step 0에서 생성한 `class_weights.json`을 사용해 Notebook 01/02 간 일관성을 유지한다.

```python
# 기존: df에서 직접 계산
class_counts = train_df['weak_label'].value_counts().sort_index().values
class_weights = torch.tensor(1.0 / class_counts, dtype=torch.float32).to(device)

# 개선: Notebook 01이 저장한 파일에서 로드
import json
with open(f'{LABELS_DIR}/class_weights.json') as f:
    raw_weights = json.load(f)

# key가 문자열로 저장됐으므로 정수로 변환 후 정렬
class_weights_list = [raw_weights[str(i)] for i in range(NUM_CLASSES)]
class_weights = torch.tensor(class_weights_list, dtype=torch.float32).to(device)
class_weights = class_weights / class_weights.sum() * NUM_CLASSES  # 정규화
```

`class_weights.json`이 없으면 (Step 0 미실행 시) train_df에서 계산하는 fallback을 추가한다:

```python
json_path = Path(f'{LABELS_DIR}/class_weights.json')
if json_path.exists():
    with open(json_path) as f:
        raw = json.load(f)
    class_weights_list = [raw[str(i)] for i in range(NUM_CLASSES)]
    class_weights = torch.tensor(class_weights_list, dtype=torch.float32).to(device)
else:
    class_counts = train_df['weak_label'].value_counts().sort_index().values
    class_weights = torch.tensor(1.0 / class_counts, dtype=torch.float32).to(device)

class_weights = class_weights / class_weights.sum() * NUM_CLASSES
```

---

### 8. PCA 차원 축소 — Isolation Forest 입력 준비

EfficientNet-B3 임베딩은 1536차원이다. **Isolation Forest는 고차원에서 차원의 저주**로 인해 모든 포인트 간 거리가 수렴해 outlier 판별이 불가능해진다. 50~100차원 이하로 줄여야 한다.

임베딩 추출 완료 후 (`embeddings_np` 생성 직후) PCA를 적용한다:

```python
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# 1. 스케일 정규화 (PCA 전 필수)
scaler = StandardScaler()
embeddings_scaled = scaler.fit_transform(embeddings_np)   # (N, 1536)

# 2. PCA — 분산 95% 보존 (보통 100~150차원으로 수렴)
pca = PCA(n_components=0.95, svd_solver='full', random_state=42)
embeddings_pca = pca.fit_transform(embeddings_scaled)     # (N, k)

print(f'PCA 결과: {embeddings_np.shape[1]}차원 → {embeddings_pca.shape[1]}차원')
print(f'보존된 분산: {pca.explained_variance_ratio_.sum():.3%}')

# 3. PCA 모델 저장 (Notebook 04에서 재사용)
import pickle
with open(f'{MODELS_DIR}/pca_model.pkl', 'wb') as f:
    pickle.dump({'scaler': scaler, 'pca': pca}, f)

# 4. 축소된 임베딩 저장
np.save(f'{LABELS_DIR}/embeddings_pca.npy', embeddings_pca)
print(f'PCA 임베딩 저장 완료: {embeddings_pca.shape}')
```

`embeddings.npy` (1536차원)는 UMAP 시각화용으로 유지하고, `embeddings_pca.npy`는 Isolation Forest 학습용으로 별도 저장한다.

---

### 9. 임베딩 시각화 — UMAP

`## 5. CNN 임베딩으로 역할별 Feature 추출` 섹션 마지막에 UMAP 시각화 셀을 추가한다.  
임베딩이 역할별로 잘 클러스터링됐는지 눈으로 확인한다.

```python
# UMAP은 Colab 기본 환경에 없으므로 반드시 설치 셀을 주석 해제하고 실행한다
!pip install -q umap-learn

import umap
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# 시각화용 서브샘플 (전체 N이 크면 UMAP이 느림)
SAMPLE_N = 3000
sample_idx = np.random.choice(len(embeddings_np), min(SAMPLE_N, len(embeddings_np)), replace=False)
sample_emb = embeddings_np[sample_idx]
sample_labels = labels_np[sample_idx]

reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=30, min_dist=0.1)
emb_2d = reducer.fit_transform(sample_emb)

colors = plt.cm.tab10(np.linspace(0, 1, NUM_CLASSES))
fig, ax = plt.subplots(figsize=(10, 8))
for role_id, color in enumerate(colors):
    mask = sample_labels == role_id
    ax.scatter(emb_2d[mask, 0], emb_2d[mask, 1],
               c=[color], label=ROLE_NAMES[role_id],
               alpha=0.6, s=10)

ax.legend(markerscale=3, loc='upper right')
ax.set_title('EfficientNet-B3 임베딩 UMAP (역할별 색상)')
ax.axis('off')
plt.tight_layout()
plt.savefig(f'{MODELS_DIR}/embedding_umap.png', dpi=120)
plt.show()
print('UMAP 시각화 저장 완료')
```

역할 클러스터가 뭉쳐 있으면 분류기가 잘 학습된 것이다.  
표지(0)와 마무리(4) 클러스터가 겹치면 Notebook 01의 약한 라벨을 다시 점검한다.

---

## Acceptance Criteria

```
- SLIDE_MEAN, SLIDE_STD 변수가 정의되고 Normalize에 적용됐는가?
- 학습 루프에 GradScaler와 autocast('cuda') 쌍이 있는가?
- clip_grad_norm_(max_norm=1.0)이 scaler.unscale_ 이후에 위치하는가?
- Stage 1(backbone frozen)과 Stage 2(differential lr)로 구분되어 있는가?
- train_transform에 RandomHorizontalFlip이 없는가?
- CrossEntropyLoss에 label_smoothing=0.15가 설정됐는가?
- patience 변수가 선언되고 early stopping 로직이 있는가?
- {MODELS_DIR}/pca_model.pkl과 {LABELS_DIR}/embeddings_pca.npy가 생성되는가?
- {MODELS_DIR}/embedding_umap.png가 생성되는가?
```

## 금지사항

- `Normalize`에 ImageNet 기본값([0.485, 0.456, 0.406])을 그대로 쓰지 마라. 반드시 슬라이드 데이터에서 계산한 `SLIDE_MEAN`, `SLIDE_STD`를 사용한다.
- Isolation Forest에 `embeddings.npy` (1536차원)를 직접 입력하지 마라. 반드시 PCA를 거친 `embeddings_pca.npy`를 사용한다. 고차원 IF는 차원의 저주로 anomaly 판별이 불가능하다.
- Stage 1을 생략하고 처음부터 전체 fine-tuning하지 마라. weak label의 노이즈가 backbone에 과적합된다.
- `autocast` 블록을 검증 루프에도 적용하지 마라. `torch.no_grad()`만으로 충분하다.
- `label_smoothing` 값을 0.3 이상으로 설정하지 마라. 너무 높으면 모델이 아무것도 배우지 못한다.
- UMAP을 학습 루프 내에서 호출하지 마라. 임베딩 추출이 완료된 후 한 번만 실행한다.
- `BATCH_SIZE`를 512 이상으로 올리지 마라. A100 40GB에서 EfficientNet-B3는 256 정도가 안전한 상한이다.
- `EarlyStopping`을 별도 클래스로 추상화하지 마라. 루프 내 5줄 이내의 인라인 로직으로 충분하다.
