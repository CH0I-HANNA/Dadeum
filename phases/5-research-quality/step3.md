# Step 3: sensitivity-analysis

## 읽어야 할 파일

먼저 아래 파일들을 읽어라:

- `/Users/choehanna/Documents/Dadeum/CLAUDE.md`
- `/Users/choehanna/Documents/Dadeum/notebooks/02_cnn_role_classifier.ipynb` — PCA 코드
- `/Users/choehanna/Documents/Dadeum/notebooks/03_hmm_structure.ipynb` — HMM 코드
- `/Users/choehanna/Documents/Dadeum/notebooks/04_evaluation.ipynb` — IF contamination 코드
- `/Users/choehanna/Documents/Dadeum/phases/5-research-quality/step2.md`

**이 step의 동기:**

현재 세 가지 핵심 하이퍼파라미터가 전혀 근거 없이 고정돼 있다:
1. IF `contamination=0.15` — 이 값이 precision/recall 전체를 결정한다
2. PCA `n_components=0.95` — 실제 차원이 몇인지 컨트롤 안 됨
3. HMM+IF 결합 가중치 `α=0.7` — NB04에서 grid search하지만 train set 기반이라 overfit 위험

이 세 파라미터의 sensitivity를 체계적으로 분석하지 않으면 리뷰어가 즉시 지적한다.
"결과가 이 파라미터에 민감하게 달라진다면 방법론이 robust하지 않다"는 reject 사유가 된다.

이전 step에서 생성된 파일:
- `labels/synthetic_anomaly_benchmark.csv` (step0)
- `models/pca_model.pkl`, `models/hmm_model.pkl`, `models/isolation_forest.pkl` (NB02~04)
- `models/baseline_results.json` (step2)

---

## 작업

`notebooks/08_sensitivity_analysis.ipynb`를 새로 생성한다.

### 1. IF contamination sensitivity

```python
import numpy as np
import pandas as pd
import pickle, json
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score

CONTAMINATION_RANGE = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]

all_emb_pca = np.load(f'{LABELS_DIR}/embeddings_pca.npy')
benchmark_df = pd.read_csv(f'{LABELS_DIR}/synthetic_anomaly_benchmark.csv')
# 벤치마크에서 이미지 경로 기반으로 PCA 임베딩 서브셋 추출하는 코드

contamination_results = []
for cont in CONTAMINATION_RANGE:
    iso = IsolationForest(n_estimators=200, contamination=cont, random_state=42)
    iso.fit(all_emb_pca)
    # 합성 벤치마크 슬라이드에 대해 score 계산
    raw = iso.decision_function(benchmark_emb_pca)
    s_min, s_max = raw.min(), raw.max()
    scores = 1.0 - (raw - s_min) / (s_max - s_min + 1e-8)
    auc = roc_auc_score(benchmark_labels, scores)
    contamination_results.append({'contamination': cont, 'auc': float(auc)})
    print(f'contamination={cont:.2f} | AUC={auc:.4f}')

# AUC 변화 폭이 0.05 이상이면 민감 파라미터로 표시
auc_range = max(r['auc'] for r in contamination_results) - min(r['auc'] for r in contamination_results)
print(f'\nAUC 변화 폭: {auc_range:.4f}')
if auc_range > 0.05:
    print('⚠ contamination에 민감함 — 논문에서 최적값 선택 근거 명시 필요')
```

### 2. PCA 차원 수 sensitivity

95% variance 유지가 아니라 고정 차원으로 재실험한다:

```python
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

embeddings_raw = np.load(f'{LABELS_DIR}/embeddings.npy')  # (N, 1536)
pca_dims = [16, 32, 64, 128, 256, 512]

pca_results = []
for n_dim in pca_dims:
    scaler = StandardScaler()
    emb_scaled = scaler.fit_transform(embeddings_raw)
    pca = PCA(n_components=n_dim, random_state=42)
    emb_pca = pca.fit_transform(emb_scaled)
    variance_ratio = pca.explained_variance_ratio_.sum()

    iso = IsolationForest(n_estimators=200, contamination=0.15, random_state=42)
    iso.fit(emb_pca)
    # 벤치마크 슬라이드 transform 후 score 계산
    raw = iso.decision_function(benchmark_emb_pca_ndim)
    s_min, s_max = raw.min(), raw.max()
    scores = 1.0 - (raw - s_min) / (s_max - s_min + 1e-8)
    auc = roc_auc_score(benchmark_labels, scores)

    pca_results.append({
        'n_components': n_dim,
        'variance_explained': float(variance_ratio),
        'auc': float(auc)
    })
    print(f'PCA dim={n_dim} | variance={variance_ratio:.3%} | AUC={auc:.4f}')

# 최적 차원 결정: AUC가 더 이상 오르지 않는 elbow point
optimal_dim = pca_dims[np.argmax([r['auc'] for r in pca_results])]
print(f'\\n최적 PCA 차원: {optimal_dim}')
```

### 3. HMM+IF 가중치 sensitivity (train/val split 분리)

NB04의 alpha grid search는 train 데이터로 탐색해서 test로 평가하지 않는다.
올바른 방법: train에서 alpha 탐색 → 독립 test set에서 1회만 평가:

```python
benchmark_df['split'] = np.where(
    np.arange(len(benchmark_df)) < int(len(benchmark_df) * 0.7), 'train', 'test'
)

# Train split으로 alpha 탐색
alphas = np.linspace(0.0, 1.0, 21)
train_mask = benchmark_df['split'] == 'train'
test_mask  = benchmark_df['split'] == 'test'

train_aucs = []
for alpha in alphas:
    combined = alpha * train_if_scores + (1 - alpha) * train_hmm_scores
    auc = roc_auc_score(train_labels, combined)
    train_aucs.append(auc)

best_alpha_train = alphas[np.argmax(train_aucs)]
print(f'Train 최적 α: {best_alpha_train:.2f}')

# Test split에서 1회만 평가 (data leakage 방지)
test_combined = best_alpha_train * test_if_scores + (1 - best_alpha_train) * test_hmm_scores
auc_test_proper = roc_auc_score(test_labels, test_combined)
print(f'Test AUC (proper split): {auc_test_proper:.4f}')

# NB04 방식(전체 데이터 grid search)과 비교
print(f'NB04 방식 AUC: {best_auc_from_nb04:.4f}')
gap = best_auc_from_nb04 - auc_test_proper
print(f'Overfit gap: {gap:.4f}')
if gap > 0.02:
    print('⚠ NB04의 alpha grid search가 test set에 overfit됨 — 논문에서 수정 필요')
```

### 4. label_smoothing sensitivity

NB02의 `label_smoothing=0.15`가 실제로 효과적인지 검증한다:

```python
smoothing_values = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25]
# 각 값으로 CNN을 재학습하는 것은 시간이 많이 걸리므로
# val_acc 변화를 기록하는 그래프를 생성하는 코드를 작성한다.
# (실제 재학습은 선택 사항 — 이미 완료된 결과가 있으면 그것을 사용)

# 최소한 현재 설정(0.15)과 no smoothing(0.0)을 비교한다.
```

### 5. Sensitivity 결과 저장

```python
sensitivity_results = {
    'contamination': {
        'values': CONTAMINATION_RANGE,
        'aucs': [r['auc'] for r in contamination_results],
        'range': float(auc_range),
        'sensitive': bool(auc_range > 0.05),
        'selected': 0.15,
        'selection_reason': 'standard default — requires justification if sensitive',
    },
    'pca_dim': {
        'values': pca_dims,
        'aucs': [r['auc'] for r in pca_results],
        'optimal': optimal_dim,
        'current_mode': '95% variance',
    },
    'alpha': {
        'overfit_gap': float(gap),
        'train_best_alpha': float(best_alpha_train),
        'test_auc_proper': float(auc_test_proper),
    },
}
with open(f'{MODELS_DIR}/sensitivity_results.json', 'w') as f:
    json.dump(sensitivity_results, f, indent=2)
print(json.dumps(sensitivity_results, indent=2))
```

### 6. Sensitivity 시각화

3개 파라미터를 subplot으로 표시:

```python
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# contamination
axes[0].plot(CONTAMINATION_RANGE, [r['auc'] for r in contamination_results], 'o-')
axes[0].axvline(0.15, color='red', linestyle='--', label='현재 설정')
axes[0].set_xlabel('contamination')
axes[0].set_ylabel('AUC')
axes[0].set_title('IF contamination sensitivity')
axes[0].legend()

# PCA dim
axes[1].plot(pca_dims, [r['auc'] for r in pca_results], 's-')
axes[1].axvline(optimal_dim, color='green', linestyle='--', label=f'최적 dim={optimal_dim}')
axes[1].set_xlabel('PCA n_components')
axes[1].set_title('PCA 차원 sensitivity')
axes[1].legend()

# alpha (train vs test)
axes[2].plot(alphas, train_aucs, 'o-', label='Train (grid search)')
axes[2].axvline(best_alpha_train, color='red', linestyle='--')
axes[2].axhline(auc_test_proper, color='blue', linestyle='--', label=f'Test AUC={auc_test_proper:.3f}')
axes[2].set_xlabel('α (IF 가중치)')
axes[2].set_title('Alpha 가중치 sensitivity')
axes[2].legend()

plt.tight_layout()
plt.savefig(f'{MODELS_DIR}/sensitivity_analysis.png', dpi=120)
plt.show()
```

---

## Acceptance Criteria

```bash
python3 -c "
import json, ast, re
nb = json.load(open('notebooks/08_sensitivity_analysis.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
ast.parse(re.sub(r'^[!%].*$', '', src, flags=re.MULTILINE))
print('OK: syntax')
"

python3 -c "
import json
nb = json.load(open('notebooks/08_sensitivity_analysis.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
assert 'CONTAMINATION_RANGE' in src,      'contamination sweep missing'
assert 'pca_dims' in src,                 'PCA dim sweep missing'
assert 'overfit_gap' in src,              'alpha overfit analysis missing'
assert 'sensitivity_results.json' in src, 'result save missing'
assert 'sensitive' in src,                'sensitivity flag missing'
print('All checks passed')
"
```

## 검증 절차

1. AC 커맨드를 실행한다.
2. `sensitivity_results.json`을 확인한다:
   - `contamination.sensitive == true` → 논문에서 최적값 선택 근거를 추가해야 함
   - `alpha.overfit_gap > 0.02` → NB04의 alpha grid search를 train/test split으로 수정해야 함
   - `pca_dim.optimal != 현재 사용 차원` → NB02/NB04에서 PCA 차원 수정 필요
3. `phases/5-research-quality/index.json`의 step 3을 업데이트한다.

## 금지사항

- alpha sensitivity를 train/test 분리 없이 전체 데이터로 측정하지 마라. 이것이 NB04의 문제이며 이 step에서 올바르게 수정한다.
- PCA sensitivity를 95% variance 유지 모드만으로 비교하지 마라. 반드시 고정 차원 [16, 32, 64, 128, 256, 512]와 비교한다.
- contamination sensitivity가 "민감하지 않다"는 결론이 나와도 조작하지 마라. 민감하다면 논문에서 그것을 솔직하게 보고하고 해결책(cross-validation 기반 선택 등)을 제시한다.
