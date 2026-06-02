# Step 3: Notebook 04 — 평가 파이프라인 개선

## 개요

`notebooks/04_evaluation.ipynb`는 CNN + HMM 파이프라인의 이상 탐지 성능을 SlideAudit 데이터셋으로 측정한다.  
현재 코드는 4가지 핵심 문제가 있다.

1. **슬라이드 단위 배치 추론 없음**: 이미지 하나씩 GPU로 보내는 for 루프는 A100에서 10~20배 느리다.
2. **점수 가중치 근거 없음**: `0.7 × IF + 0.3 × HMM`은 임의 값이다. 그리드 탐색으로 최적 가중치를 찾아야 한다.
3. **Ablation 없음**: IF만 / HMM만 / 결합이 각각 얼마나 기여하는지 알 수 없다.
4. **결함 유형별 분석 없음**: SlideAudit의 폰트/색상/레이아웃 결함을 구분하지 않고 뭉뚱그려 AUC를 계산한다.

---

## 읽어야 할 파일

- `notebooks/04_evaluation.ipynb` — 전체 흐름
- `notebooks/02_cnn_role_classifier.ipynb` — SlideRoleClassifier 정의 (동일하게 복사)
- `notebooks/03_hmm_structure.ipynb` — hmm_thresholds.json 구조 확인

---

## 개선 작업

### 1. 배치 추론으로 교체 — DataLoader 사용

`compute_anomaly_score` 내부의 이미지-by-이미지 for 루프를 제거하고 DataLoader 배치 추론으로 교체한다.

**새 헬퍼 클래스 추가 (모델 정의 셀 다음에):**

```python
from torch.utils.data import Dataset, DataLoader

class InferenceDataset(Dataset):
    def __init__(self, image_paths: list[str], transform):
        self.paths = image_paths
        self.transform = transform

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        img = Image.open(self.paths[idx]).convert('RGB')
        return self.transform(img), self.paths[idx]


def extract_embeddings_batch(
    image_paths: list[str],
    model: nn.Module,
    transform,
    batch_size: int = 64,
) -> tuple[np.ndarray, np.ndarray]:
    """
    이미지 경로 리스트를 받아 (embeddings, pred_roles) 반환.
    GPU 배치 추론으로 단일 이미지 루프 대비 10~20× 빠름.
    """
    dataset = InferenceDataset(image_paths, transform)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False,
                        num_workers=2, pin_memory=True)

    all_emb, all_roles = [], []
    model.eval()
    with torch.no_grad():
        for imgs, _ in loader:
            imgs = imgs.to(device)
            emb = model.extract_features(imgs)          # (B, 1536)
            logits = model.classifier(emb)
            roles = logits.argmax(dim=1)
            all_emb.append(emb.cpu().numpy())
            all_roles.append(roles.cpu().numpy())

    return np.concatenate(all_emb), np.concatenate(all_roles)
```

`compute_anomaly_score`를 배치 추론 버전으로 교체한다:

```python
def compute_anomaly_score(image_paths: list[str]) -> dict:
    if len(image_paths) < 2:
        return {'slide_scores': [0.5] * len(image_paths),
                'pred_roles': [2] * len(image_paths),
                'deck_structural_score': 0.5,
                'if_scores': [0.5] * len(image_paths)}

    # 배치 추론 (단일 이미지 루프 제거)
    embeddings_np, pred_roles = extract_embeddings_batch(image_paths, cnn_model, transform)

    # Isolation Forest (덱 내)
    if len(embeddings_np) >= 3:
        iso = IsolationForest(n_estimators=100, contamination=0.2, random_state=42)
        iso.fit(embeddings_np)
        raw = iso.decision_function(embeddings_np)
        s_min, s_max = raw.min(), raw.max()
        if_scores = 1.0 - (raw - s_min) / (s_max - s_min + 1e-8)
    else:
        if_scores = np.full(len(embeddings_np), 0.5)

    # HMM 구조 점수
    seq = pred_roles.reshape(-1, 1)
    log_likelihood = hmm_model.score(seq) / len(seq)
    z = (thresholds['mean'] - log_likelihood) / (thresholds['std'] + 1e-8)
    hmm_score = float(np.clip(z / 3.0, 0, 1))

    return {
        'slide_scores': (0.7 * if_scores + 0.3 * hmm_score).tolist(),
        'pred_roles': pred_roles.tolist(),
        'deck_structural_score': hmm_score,
        'if_scores': if_scores.tolist(),
        'hmm_score': hmm_score,
    }
```

---

### 1-B. IsolationForest 전역 학습으로 개선

현재 `compute_anomaly_score` 내에서 `IsolationForest`를 덱마다 새로 `fit`한다.  
슬라이드가 5장인 덱에서 fit하면 outlier 판정에 통계적 의미가 없고(샘플 수 부족), 덱마다 수백 번 fit하므로 매우 느리다.

올바른 접근: Notebook 01/02에서 수집한 전체 임베딩으로 IF를 한 번 학습하고 저장한다.

```python
# 이 코드는 모델 정의 섹션(## 2. 파이프라인 구성) 다음에 한 번만 실행한다
import pickle

# PCA 모델 로드 (Notebook 02 step1-8에서 저장)
with open(f'{MODELS_DIR}/pca_model.pkl', 'rb') as f:
    pca_bundle = pickle.load(f)
pca_scaler = pca_bundle['scaler']
pca_model = pca_bundle['pca']

# PCA 축소 임베딩으로 전역 IF 학습
# embeddings_pca.npy는 이미 PCA 변환된 50~150차원
all_embeddings_pca = np.load(f'{LABELS_DIR}/embeddings_pca.npy')

global_iso = IsolationForest(n_estimators=200, contamination=0.15, random_state=42)
global_iso.fit(all_embeddings_pca)

with open(f'{MODELS_DIR}/isolation_forest.pkl', 'wb') as f:
    pickle.dump(global_iso, f)
print(f'전역 IsolationForest 학습 완료: {all_embeddings_pca.shape} (PCA 축소 임베딩)')
```

`compute_anomaly_score`도 PCA 변환 후 IF를 적용한다:

```python
def compute_anomaly_score(image_paths: list[str]) -> dict:
    if len(image_paths) < 2:
        return {'slide_scores': [0.5] * len(image_paths),
                'pred_roles': [2] * len(image_paths),
                'deck_structural_score': 0.5,
                'if_scores': [0.5] * len(image_paths),
                'hmm_score': 0.5}

    embeddings_np, pred_roles = extract_embeddings_batch(image_paths, cnn_model, transform)

    # PCA 변환 후 전역 IF 적용 (1536차원 직접 입력 금지)
    emb_scaled = pca_scaler.transform(embeddings_np)
    emb_pca = pca_model.transform(emb_scaled)
    raw = global_iso.decision_function(emb_pca)
    s_min, s_max = raw.min(), raw.max()
    if_scores = 1.0 - (raw - s_min) / (s_max - s_min + 1e-8)

    # HMM 구조 점수
    seq = pred_roles.reshape(-1, 1)
    log_likelihood = hmm_model.score(seq) / len(seq)
    z = (thresholds['mean'] - log_likelihood) / (thresholds['std'] + 1e-8)
    hmm_score = float(np.clip(z / 3.0, 0, 1))

    return {
        'slide_scores': (0.7 * if_scores + 0.3 * hmm_score).tolist(),
        'pred_roles': pred_roles.tolist(),
        'deck_structural_score': hmm_score,
        'if_scores': if_scores.tolist(),
        'hmm_score': hmm_score,
    }
```

`pca_model.pkl` 또는 `embeddings_pca.npy`가 없으면 Notebook 02 step1-8을 먼저 실행해야 한다.

---

### 2. Ablation Study — IF / HMM / 결합 비교

AUC 계산 셀 다음에 각 컴포넌트를 단독으로 평가하는 셀을 추가한다.

```python
# --- Ablation: IF만 ---
# all_labels는 슬라이드 단위(flatten)이므로 if_scores도 동일하게 슬라이드 단위로 flatten해야 한다
# (덱 평균을 내면 all_labels 길이와 불일치해 roc_auc_score가 에러를 낸다)
if_scores_flat = np.array([s for r in all_results for s in r['if_scores']])
auc_if_only = roc_auc_score(all_labels, if_scores_flat)

# --- Ablation: HMM만 ---
# HMM 점수는 덱 단위이므로 슬라이드 수만큼 broadcast한 뒤 all_labels와 비교
hmm_scores_flat = np.array([
    r['hmm_score']
    for r, (_, group) in zip(all_results, valid_groups)
    for _ in range(len(group))
])
auc_hmm_only = roc_auc_score(all_labels, hmm_scores_flat)

print('\n=== Ablation Study ===')
print(f'IF만:                  AUC = {auc_if_only:.4f}')
print(f'HMM만:                 AUC = {auc_hmm_only:.4f}')
print(f'IF (0.7) + HMM (0.3): AUC = {auc_new:.4f}')
print(f'IF baseline:           AUC = {auc_baseline:.4f}')
```

---

### 3. 점수 가중치 그리드 탐색

`0.7/0.3` 가중치가 최적인지 확인하기 위해 그리드 탐색을 수행한다.

```python
# IF 가중치 α를 0.0 ~ 1.0으로 탐색 (HMM 가중치 = 1 - α)
alphas = np.linspace(0.0, 1.0, 21)  # 0.0, 0.05, ..., 1.0
auc_by_alpha = []

for alpha in alphas:
    combined = []
    for result in all_results:
        # 슬라이드별 최종 점수
        slide_scores = [alpha * s + (1 - alpha) * result['hmm_score']
                        for s in result['if_scores']]
        combined.extend(slide_scores)

    combined = np.array(combined)
    auc = roc_auc_score(all_labels, combined)
    auc_by_alpha.append(auc)

best_alpha = alphas[np.argmax(auc_by_alpha)]
best_auc_alpha = max(auc_by_alpha)
print(f'최적 IF 가중치: α={best_alpha:.2f} (AUC={best_auc_alpha:.4f})')

# 가중치-AUC 커브
plt.figure(figsize=(8, 4))
plt.plot(alphas, auc_by_alpha, 'o-', color='steelblue')
plt.axvline(best_alpha, color='red', linestyle='--', label=f'최적 α={best_alpha:.2f}')
plt.axvline(0.7, color='gray', linestyle=':', label='기존 α=0.70')
plt.xlabel('IF 가중치 (α)')
plt.ylabel('AUC')
plt.title('점수 가중치 그리드 탐색')
plt.legend()
plt.tight_layout()
plt.savefig(f'{MODELS_DIR}/weight_grid_search.png', dpi=100)
plt.show()
```

최적 가중치를 `final_results.json`에 저장한다:

```python
final_results['best_alpha'] = float(best_alpha)
final_results['best_auc_with_optimal_alpha'] = float(best_auc_alpha)
final_results['ablation'] = {
    'if_only': float(auc_if_only),
    'hmm_only': float(auc_hmm_only),
    'combined_0.7_0.3': float(auc_new),
    'combined_optimal': float(best_auc_alpha),
}
```

---

### 4. 결함 유형별 AUC 분석

SlideAudit에 결함 유형 컬럼(`defect_types` 또는 `typography`, `color`, `layout` 등)이 있으면 유형별 AUC를 계산한다.

```python
# SlideAudit 컬럼 구조에 따라 수정 필요
# 예시: slideaudit_df에 'typography', 'color', 'layout' 불리언 컬럼이 있다고 가정

DEFECT_TYPES = ['typography', 'color', 'layout', 'content']
available_types = [t for t in DEFECT_TYPES if t in slideaudit_df.columns]

if available_types:
    print('\n=== 결함 유형별 AUC ===')
    type_aucs = {}
    for defect_type in available_types:
        # 해당 결함 유형 라벨 매핑
        type_labels = []
        type_scores = []
        for result, (deck_id, group) in zip(all_results, valid_groups):
            if defect_type in group.columns:
                type_labels.extend(group[defect_type].astype(int).tolist())
                type_scores.extend(result['slide_scores'])

        if len(set(type_labels)) < 2:
            print(f'  {defect_type}: 이진 라벨 없음 (스킵)')
            continue

        auc = roc_auc_score(type_labels, type_scores)
        type_aucs[defect_type] = auc
        print(f'  {defect_type}: AUC = {auc:.4f}')

    final_results['per_defect_auc'] = {k: float(v) for k, v in type_aucs.items()}
else:
    print('결함 유형 컬럼 없음 — slideaudit_df 구조를 확인하고 컬럼 이름을 수동으로 지정')
```

SlideAudit 데이터셋 구조를 실제로 확인한 후 `DEFECT_TYPES`와 컬럼 이름을 맞춰야 한다.

---

### 5. 평가 루프 리팩터링 — 결과를 리스트로 수집

현재 코드는 `all_scores`와 `all_labels`를 각각 `extend`한다.  
Ablation과 유형별 분석을 모두 지원하려면 덱 단위 결과를 보존해야 한다.

`## 4. SlideAudit로 AUC 측정` 셀을 아래처럼 교체한다:

```python
all_results = []       # 덱별 anomaly score dict
valid_groups = []      # 덱별 (deck_id, group) 튜플

for deck_id, group in tqdm(slideaudit_df.groupby('deck_id'), desc='AUC 계산'):
    if 'slide_idx' in group.columns:
        group = group.sort_values('slide_idx')

    image_paths = group['image_path'].tolist()
    valid_pairs = [(p, row) for p, (_, row) in zip(image_paths, group.iterrows())
                   if Path(p).exists()]
    if len(valid_pairs) < 2:   # 1-슬라이드 덱 스킵
        continue

    valid_paths = [p for p, _ in valid_pairs]
    valid_group = group[group['image_path'].isin(valid_paths)]

    result = compute_anomaly_score(valid_paths)
    all_results.append(result)
    valid_groups.append((deck_id, valid_group))

# 슬라이드 레벨로 flatten
all_scores = np.array([s for r in all_results for s in r['slide_scores']])
all_labels = np.array([
    label
    for _, group in valid_groups
    for label in group['has_defect'].astype(int).tolist()
])

print(f'평가 슬라이드 수: {len(all_scores)}')
print(f'이상 슬라이드 비율: {all_labels.mean():.2%}')
auc_new = roc_auc_score(all_labels, all_scores)
print(f'새 파이프라인 AUC: {auc_new:.4f}')
```

---

### 6. AUC 해석 가이드 — SlideAudit와 우리 모델의 태스크 미스매치

SlideAudit의 라벨과 우리 파이프라인이 탐지하는 "이상"은 다른 개념이다.

| | 우리 파이프라인 | SlideAudit |
|---|---|---|
| **탐지 대상** | 구조 이상(역할 시퀀스), 임베딩 outlier | 디자인 결함(폰트, 색상, 정렬) |
| **단위** | 덱 전체 구조 + 슬라이드별 비주얼 | 슬라이드별 디자인 |
| **기준** | Zenodo10K 정상 덱에서 학습 | 사람이 레이블한 디자인 오류 |

AUC가 0.6~0.65라면 이것이 "모델이 나쁘다"는 의미가 아닐 수 있다. 두 태스크의 overlap이 제한적이기 때문이다. 결과를 해석할 때 아래를 추가로 출력한다:

```python
# AUC 결과 해석 출력
print('\n=== AUC 해석 가이드 ===')
print(f'새 파이프라인 AUC: {auc_new:.4f}')
print()
if auc_new >= 0.75:
    print('✓ 우수: 우리 파이프라인이 SlideAudit 디자인 결함과 높은 상관을 보임')
elif auc_new >= 0.65:
    print('△ 보통: 일부 디자인 결함은 구조/비주얼 이상과 겹침')
else:
    print('▲ 참고: SlideAudit는 디자인 결함을 레이블함. 우리 모델은 구조/비주얼 이상을 탐지함.')
    print('  → 태스크 불일치 가능성. IF 점수와 HMM 점수를 분리해 각각 해석할 것.')
    print(f'  IF만 AUC: {auc_if_only:.4f} / HMM만 AUC: {auc_hmm_only:.4f}')
    print('  어느 컴포넌트가 SlideAudit와 더 aligned되는지 확인한다.')
```

---

## Acceptance Criteria

```
- pca_model.pkl을 로드하고 compute_anomaly_score 내에서 PCA 변환 후 IF를 적용하는가?
- compute_anomaly_score 내에 이미지-by-이미지 for 루프가 없는가?
- compute_anomaly_score 내에 IsolationForest.fit() 호출이 없는가? (전역 모델 사용)
- {MODELS_DIR}/isolation_forest.pkl이 생성되는가?
- {MODELS_DIR}/weight_grid_search.png가 생성되는가?
- final_results.json에 'best_alpha' 키가 있는가?
- final_results.json에 'ablation' 키 아래 if_only, hmm_only, combined 세 값이 있는가?
- Ablation IF 점수가 슬라이드 단위 flatten이고 all_labels와 길이가 일치하는가?
- 평가 루프가 all_results 리스트를 수집하는 구조인가?
- AUC 해석 출력이 있는가?
```

## 금지사항

- `compute_anomaly_score`에 1536차원 원본 임베딩을 그대로 IF에 입력하지 마라. 반드시 `pca_scaler.transform` → `pca_model.transform` 순서로 변환 후 입력한다. 고차원 IF는 차원의 저주로 anomaly 판별이 사실상 불가능하다.
- `compute_anomaly_score` 내에서 `IsolationForest`를 `fit`하지 마라. 반드시 전역 학습된 `global_iso`를 사용해야 한다. 덱 단위 fit은 샘플 수가 너무 적어 통계적으로 무의미하다.
- Ablation IF 점수를 덱 단위 평균으로 계산하지 마라. `all_labels`는 슬라이드 단위이므로 `if_scores`도 슬라이드 단위로 flatten해야 `roc_auc_score`가 에러 없이 실행된다.
- 그리드 탐색 범위를 100분할 이상으로 설정하지 마라. AUC 계산이 슬라이드 수만큼 반복되므로 21분할(0.05 간격)으로 충분하다.
- `compute_anomaly_score` 함수를 클래스로 바꾸지 마라. 함수 형태를 유지해야 Notebook 05(백엔드 통합) 작성 시 그대로 `backend/app/pipeline/`에 이식할 수 있다.
- SlideAudit 데이터가 없는 상태에서 AUC 코드를 실행하지 마라. 먼저 `## 1. SlideAudit 데이터셋 로드` 섹션을 완료하고 `slideaudit_df`에 'deck_id', 'image_path', 'has_defect' 컬럼이 있는지 확인한다.
- `baseline_scores` 계산을 재실행하지 않고 그리드 탐색과 함께 실행하지 마라. 베이스라인 임베딩 추출은 한 번만 실행하고 결과를 변수에 보존한다.
- `all_results`를 직접 수정하지 마라. 추론 후 불변으로 유지해야 여러 분석(Ablation, 그리드 탐색, 유형별 AUC)에 재사용할 수 있다.
