# Step 4: pipeline-eval

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트 구조와 설계 의도를 파악하라:

- `/Users/choehanna/Documents/Dadeum/CLAUDE.md`
- `/Users/choehanna/Documents/Dadeum/docs/ARCHITECTURE.md`
- `/Users/choehanna/Documents/Dadeum/notebooks/04_evaluation.ipynb`
- `/Users/choehanna/Documents/Dadeum/phases/4-ml-pipeline/step2.md` — pca_model.pkl, embeddings_pca.npy, slide_norm.json 경로 확인
- `/Users/choehanna/Documents/Dadeum/phases/4-ml-pipeline/step3.md` — hmm_model.pkl, hmm_thresholds.json 구조 확인

이전 step들에서 생성된 파일:
- `models/pca_model.pkl` — scaler + PCA 번들 (step2)
- `labels/embeddings_pca.npy` — PCA 축소 임베딩 (N, k) (step2)
- `models/slide_norm.json` — SLIDE_MEAN, SLIDE_STD (step2)
- `models/hmm_model.pkl` (step3)
- `models/hmm_thresholds.json` — `method`, `threshold_primary`, `mean`, `std` 포함 (step3)

---

## 작업

`notebooks/04_evaluation.ipynb`에 아래 개선 사항을 적용한다.

### 0. 정규화 통계 로드 및 transform 교체

step2에서 저장한 `slide_norm.json`을 로드해 NB04의 `transform` 정규화 값을 교체한다.
기존 ImageNet 통계(`[0.485, 0.456, 0.406]`)를 그대로 두면 NB02와 임베딩 분포가 달라진다:

```python
import json

with open(f'{MODELS_DIR}/slide_norm.json') as f:
    norm = json.load(f)
SLIDE_MEAN = norm['mean']
SLIDE_STD  = norm['std']

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=SLIDE_MEAN, std=SLIDE_STD),  # ImageNet 통계 교체
])
print(f'정규화 통계 로드 완료: mean={[round(v,4) for v in SLIDE_MEAN]}')
```

### 1. 전역 Isolation Forest — PCA 임베딩 기반

현재 `compute_anomaly_score` 내에서 덱마다 IsolationForest를 `fit`한다. 이를 두 가지 이유로 제거한다:
- 슬라이드 5~20장으로 fit하면 통계적으로 무의미하다
- 1536차원 원본 임베딩을 직접 사용하면 차원의 저주로 anomaly 판별이 불가능하다

모델 로드 섹션 직후에 아래 셀을 삽입한다:

```python
import pickle
from sklearn.ensemble import IsolationForest

# PCA 모델 로드 (step2에서 저장)
with open(f'{MODELS_DIR}/pca_model.pkl', 'rb') as f:
    pca_bundle = pickle.load(f)
pca_scaler = pca_bundle['scaler']
pca_model  = pca_bundle['pca']

# PCA 축소 임베딩으로 전역 IF 학습
all_embeddings_pca = np.load(f'{LABELS_DIR}/embeddings_pca.npy')
global_iso = IsolationForest(n_estimators=200, contamination=0.15, random_state=42)
global_iso.fit(all_embeddings_pca)

with open(f'{MODELS_DIR}/isolation_forest.pkl', 'wb') as f:
    pickle.dump(global_iso, f)
print(f'전역 IF 학습 완료: {all_embeddings_pca.shape} (PCA 축소 임베딩)')
```

### 2. 배치 추론 함수 추가

이미지 하나씩 GPU로 보내는 for 루프를 DataLoader 배치 추론으로 교체한다:

```python
from torch.utils.data import Dataset, DataLoader

class InferenceDataset(Dataset):
    def __init__(self, image_paths: list[str], transform):
        self.paths     = image_paths
        self.transform = transform
    def __len__(self):
        return len(self.paths)
    def __getitem__(self, idx):
        return self.transform(Image.open(self.paths[idx]).convert('RGB')), self.paths[idx]

def extract_embeddings_batch(
    image_paths: list[str],
    model: nn.Module,
    transform,
    batch_size: int = 64,
) -> tuple[np.ndarray, np.ndarray]:
    loader = DataLoader(InferenceDataset(image_paths, transform),
                        batch_size=batch_size, shuffle=False, num_workers=2, pin_memory=True)
    all_emb, all_roles = [], []
    model.eval()
    with torch.no_grad():
        for imgs, _ in loader:
            emb   = model.extract_features(imgs.to(device))
            roles = model.classifier(emb).argmax(dim=1)
            all_emb.append(emb.cpu().numpy())
            all_roles.append(roles.cpu().numpy())
    return np.concatenate(all_emb), np.concatenate(all_roles)
```

### 3. compute_anomaly_score 교체

덱 단위 IF fit 제거, PCA 변환 후 전역 IF 사용:

```python
def compute_anomaly_score(image_paths: list[str]) -> dict:
    if len(image_paths) < 2:
        return {'slide_scores': [0.5] * len(image_paths),
                'pred_roles':   [2]   * len(image_paths),
                'deck_structural_score': 0.5,
                'if_scores':    [0.5] * len(image_paths),
                'hmm_score':    0.5}

    embeddings_np, pred_roles = extract_embeddings_batch(image_paths, cnn_model, transform)

    # PCA 변환 후 전역 IF (1536차원 직접 입력 금지)
    emb_pca = pca_model.transform(pca_scaler.transform(embeddings_np))
    raw     = global_iso.decision_function(emb_pca)
    s_min, s_max = raw.min(), raw.max()
    if_scores = 1.0 - (raw - s_min) / (s_max - s_min + 1e-8)

    # HMM 구조 점수
    seq          = pred_roles.reshape(-1, 1)
    ll           = hmm_model.score(seq) / len(seq)
    z            = (thresholds['mean'] - ll) / (thresholds['std'] + 1e-8)
    hmm_score    = float(np.clip(z / 3.0, 0, 1))

    return {
        'slide_scores': (0.7 * if_scores + 0.3 * hmm_score).tolist(),
        'pred_roles':   pred_roles.tolist(),
        'deck_structural_score': hmm_score,
        'if_scores':    if_scores.tolist(),
        'hmm_score':    hmm_score,
    }
```

### 4. 평가 루프 — 덱별 결과 보존

Ablation과 가중치 탐색을 지원하기 위해 덱 단위 결과를 리스트로 보존한다:

```python
all_results  = []
valid_groups = []

for deck_id, group in tqdm(slideaudit_df.groupby('deck_id'), desc='AUC 계산'):
    if 'slide_idx' in group.columns:
        group = group.sort_values('slide_idx')
    image_paths = group['image_path'].tolist()
    valid_pairs = [(p, row) for p, (_, row) in zip(image_paths, group.iterrows())
                   if Path(p).exists()]
    if len(valid_pairs) < 2:
        continue
    valid_paths = [p for p, _ in valid_pairs]
    valid_group = group[group['image_path'].isin(valid_paths)]
    result      = compute_anomaly_score(valid_paths)
    all_results.append(result)
    valid_groups.append((deck_id, valid_group))

all_scores = np.array([s for r in all_results for s in r['slide_scores']])
all_labels = np.array([l for _, g in valid_groups for l in g['has_defect'].astype(int).tolist()])
auc_new    = roc_auc_score(all_labels, all_scores)
print(f'새 파이프라인 AUC: {auc_new:.4f}')
```

### 5. Ablation Study

```python
# IF만 — 슬라이드 단위 flatten
if_scores_flat = np.array([s for r in all_results for s in r['if_scores']])
auc_if_only    = roc_auc_score(all_labels, if_scores_flat)

# HMM만 — 덱 점수를 슬라이드 수만큼 broadcast
hmm_flat = np.array([r['hmm_score'] for r, (_, g) in zip(all_results, valid_groups)
                     for _ in range(len(g))])
auc_hmm_only = roc_auc_score(all_labels, hmm_flat)

print('\n=== Ablation Study ===')
print(f'IF만:                  AUC = {auc_if_only:.4f}')
print(f'HMM만:                 AUC = {auc_hmm_only:.4f}')
print(f'IF(0.7) + HMM(0.3):   AUC = {auc_new:.4f}')
```

### 6. 가중치 그리드 탐색

```python
alphas       = np.linspace(0.0, 1.0, 21)
auc_by_alpha = []

for alpha in alphas:
    combined = np.array([
        alpha * s + (1 - alpha) * r['hmm_score']
        for r in all_results for s in r['if_scores']
    ])
    auc_by_alpha.append(roc_auc_score(all_labels, combined))

best_alpha     = alphas[np.argmax(auc_by_alpha)]
best_auc_alpha = max(auc_by_alpha)
print(f'최적 IF 가중치: α={best_alpha:.2f} (AUC={best_auc_alpha:.4f})')
```

`models/weight_grid_search.png`로 커브를 저장한다.

### 7. final_results.json 저장

```python
final_results = {
    'baseline_auc':               float(auc_baseline),
    'new_pipeline_auc':           float(auc_new),
    'improvement':                float(auc_new - auc_baseline),
    'best_alpha':                 float(best_alpha),
    'best_auc_with_optimal_alpha': float(best_auc_alpha),
    'n_eval_slides':              int(len(all_labels)),
    'defect_ratio':               float(all_labels.mean()),
    'ablation': {
        'if_only':          float(auc_if_only),
        'hmm_only':         float(auc_hmm_only),
        'combined_0.7_0.3': float(auc_new),
        'combined_optimal': float(best_auc_alpha),
    },
}
with open(f'{MODELS_DIR}/final_results.json', 'w') as f:
    json.dump(final_results, f, indent=2)
print(json.dumps(final_results, indent=2))
```

### 8. AUC 해석 가이드

SlideAudit(디자인 결함)과 우리 모델(구조+비주얼 이상)은 탐지 대상이 다르다.
낮은 AUC가 반드시 모델 실패를 의미하지 않는다:

```python
print('\n=== AUC 해석 ===')
if auc_new >= 0.75:
    print(f'✓ 우수 (AUC={auc_new:.4f}): 파이프라인이 SlideAudit 결함과 높은 상관')
elif auc_new >= 0.65:
    print(f'△ 보통 (AUC={auc_new:.4f}): 일부 결함이 구조/비주얼 이상과 겹침')
else:
    print(f'▲ 참고 (AUC={auc_new:.4f}): SlideAudit는 디자인 결함, 우리 모델은 구조/비주얼 이상')
    print(f'  IF만={auc_if_only:.4f} / HMM만={auc_hmm_only:.4f} 로 컴포넌트별 기여 확인')
```

---

## Acceptance Criteria

```bash
python3 -c "
import json, ast, re
nb = json.load(open('notebooks/04_evaluation.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
ast.parse(re.sub(r'^[!%].*\$', '', src, flags=re.MULTILINE))
print('OK: notebooks/04_evaluation.ipynb')
"

python3 -c "
import json
nb = json.load(open('notebooks/04_evaluation.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
assert 'slide_norm.json' in src,          'SLIDE_MEAN load missing'
assert 'pca_model.pkl' in src,            'PCA load missing'
assert 'global_iso' in src,              'global IF missing'
assert 'extract_embeddings_batch' in src, 'batch inference missing'
assert '.fit(all_embeddings_pca)' in src, 'global IF not trained on PCA embeddings'
assert 'auc_if_only' in src,             'ablation missing'
assert 'auc_by_alpha' in src,            'grid search missing'
assert 'all_results' in src,             'result accumulation missing'
assert 'final_results.json' in src,      'final_results.json save missing'
print('All checks passed')
"
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - `compute_anomaly_score` 내에 `IsolationForest().fit()` 호출이 없는가?
   - `pca_scaler.transform` → `pca_model.transform` 순서로 변환하는가?
   - Ablation IF 점수가 슬라이드 단위 flatten이고 `all_labels`와 길이가 일치하는가?
   - `final_results.json`에 `best_alpha`, `ablation` 키가 있는가?
3. `phases/4-ml-pipeline/index.json`의 step 4를 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "NB04 평가 개선: PCA+전역IF, 배치 추론, Ablation, 가중치 그리드 탐색(best_alpha 저장)"`
   - 수정 3회 시도 후에도 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`
   - 사용자 개입 필요 → `"status": "blocked"`, `"blocked_reason": "구체적 사유"` 후 즉시 중단

## 금지사항

- `compute_anomaly_score`에 1536차원 원본 임베딩을 IF에 직접 입력하지 마라. 반드시 PCA 변환 후 입력한다. 고차원 IF는 차원의 저주로 동작하지 않는다.
- `compute_anomaly_score` 내에서 `IsolationForest().fit()`을 호출하지 마라. 반드시 전역 `global_iso`를 사용한다. 덱 단위 fit은 샘플 수 부족으로 통계적으로 무의미하다.
- Ablation IF 점수를 덱 단위 평균으로 계산하지 마라. `all_labels`는 슬라이드 단위이므로 `if_scores`도 슬라이드 단위로 flatten해야 `roc_auc_score`가 에러 없이 실행된다.
- `all_results` 리스트를 추론 후 수정하지 마라. Ablation, 그리드 탐색, 유형별 AUC가 모두 이 리스트를 공유한다.
- `compute_anomaly_score`를 클래스로 리팩터링하지 마라. 함수 형태를 유지해야 `backend/app/pipeline/`에 이식할 때 인터페이스가 유지된다.
