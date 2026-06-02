# Step 3: hmm-structure

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트 구조와 설계 의도를 파악하라:

- `/Users/choehanna/Documents/Dadeum/CLAUDE.md`
- `/Users/choehanna/Documents/Dadeum/docs/ARCHITECTURE.md`
- `/Users/choehanna/Documents/Dadeum/notebooks/03_hmm_structure.ipynb`
- `/Users/choehanna/Documents/Dadeum/phases/4-ml-pipeline/step2.md` — CNN 학습 후 생성 파일 목록 확인
  - `labels/labeled_with_preds.csv` (CNN pred_label 포함)
  - `models/pca_model.pkl`, `labels/embeddings_pca.npy`

이전 step(cnn-training)에서 CNN이 학습되고 `labeled_with_preds.csv`에 `pred_label` 컬럼이 추가됐다.
HMM은 반드시 weak_label이 아닌 `pred_label` 기반 시퀀스로 학습해야 한다.
추론 시에도 CNN 예측 역할을 시퀀스로 사용하기 때문에, 학습과 추론의 분포가 일치해야 한다.

---

## 작업

`notebooks/03_hmm_structure.ipynb`에 아래 개선 사항을 적용한다.

### 1. CNN 예측 기반 시퀀스 재생성

`## 1. 시퀀스 데이터 로드` 섹션 앞에 아래 셀을 삽입한다.
`labeled_with_preds.csv`가 있으면 `pred_label`을 사용하고, 없으면 `weak_label`로 fallback한다:

```python
from pathlib import Path
import pandas as pd

pred_csv = Path(f'{LABELS_DIR}/labeled_with_preds.csv')

if pred_csv.exists():
    pred_df   = pd.read_csv(pred_csv)
    label_col = 'pred_label'
    print(f'CNN 예측 기반 시퀀스 사용 (labeled_with_preds.csv)')
else:
    pred_df   = pd.read_csv(f'{LABELS_DIR}/weak_labels.csv')
    label_col = 'weak_label'
    print('⚠ CNN 예측 없음 — weak_label 사용 (step2 먼저 실행 권장)')

sequences_cnn = []
for deck_id, group in pred_df.groupby('deck_id'):
    group = group.sort_values('slide_idx')
    seq   = group[label_col].tolist()
    if len(seq) < 2:
        continue
    sequences_cnn.append({'deck_id': deck_id, 'sequence': seq, 'length': len(seq)})

seq_df = pd.DataFrame(sequences_cnn)
seq_df.to_csv(f'{LABELS_DIR}/sequences_cnn.csv', index=False)
print(f'CNN 기반 시퀀스: {len(seq_df)}개')
```

CSV로 저장된 `sequence` 컬럼은 `"[0, 2, 4]"` 형태의 문자열로 읽힌다.
기존 노트북의 `seq_df['sequence'].apply(ast.literal_eval)` 파싱 코드가 이미 있는지 확인하고,
없으면 아래를 추가한다:

```python
import ast
seq_df['sequence'] = seq_df['sequence'].apply(ast.literal_eval)
```

이후 모든 셀에서 `seq_df`를 이 CNN 기반 버전으로 사용한다.

### 2. BIC 기반 n_components 선택

현재 val log-likelihood 최대값으로 선택하는 코드를 BIC 최솟값 기준으로 교체한다:

```python
def compute_hmm_bic(model, X, lengths) -> tuple[float, float]:
    """HMM BIC 계산. 낮을수록 좋다."""
    ll         = model.score(X, lengths)
    n_samples  = len(X)
    n_obs      = 5   # NUM_ROLES
    nc         = model.n_components
    n_params   = (nc - 1) + nc * (nc - 1) + nc * (n_obs - 1)
    bic        = -2 * ll + n_params * np.log(n_samples)
    return bic, ll
```

탐색 범위를 [3, 4, 5, 6, 7]로 확장하고 `n_iter=200`으로 설정한다:

```python
results = []
for nc in [3, 4, 5, 6, 7]:
    model = hmm.CategoricalHMM(n_components=nc, n_iter=200, random_state=42, verbose=False)
    model.fit(X_train, lengths_train)
    bic, ll = compute_hmm_bic(model, X_val, lengths_val)
    results.append({'n_components': nc, 'bic': bic, 'val_score': ll / len(X_val), 'model': model})
    print(f'n_components={nc} | BIC={bic:.1f} | val ll/step={ll/len(X_val):.4f}')

best_result = min(results, key=lambda r: r['bic'])
best_model  = best_result['model']
best_n      = best_result['n_components']
```

BIC 커브를 시각화하고 `models/hmm_bic_curve.png`로 저장한다.

### 3. 임계값 결정 — 정규성 검정 후 방법 선택

`all_scores` 계산 코드(`best_model.score(x) / len(seq)` 루프)를 먼저 실행한 후 아래를 실행한다:

```python
from scipy import stats

stat, p_value = stats.shapiro(all_scores[:5000])
is_normal     = p_value > 0.05
print(f'Shapiro-Wilk: stat={stat:.4f}, p={p_value:.4f}')

if is_normal:
    threshold_method  = 'gaussian_3sigma'
    threshold_primary = float(np.mean(all_scores) - 3 * np.std(all_scores))
else:
    threshold_method  = 'percentile'
    threshold_primary = float(np.percentile(all_scores, 5))

thresholds = {
    'method':            threshold_method,
    'threshold_primary': threshold_primary,
    'threshold_5pct':    float(np.percentile(all_scores, 5)),
    'threshold_10pct':   float(np.percentile(all_scores, 10)),
    'mean':              float(np.mean(all_scores)),
    'std':               float(np.std(all_scores)),
    'shapiro_p':         float(p_value),
    'n_decks':           len(all_scores),
}
```

### 3-B. best_model 및 thresholds 저장

기존 노트북에 있는 모델 저장 코드가 개선된 `best_model`을 저장하는지 확인한다.
없으면 아래를 추가한다:

```python
import pickle

with open(f'{MODELS_DIR}/hmm_model.pkl', 'wb') as f:
    pickle.dump(best_model, f)
print(f'HMM 모델 저장: {MODELS_DIR}/hmm_model.pkl (n_components={best_n})')

with open(f'{MODELS_DIR}/hmm_thresholds.json', 'w') as f:
    json.dump(thresholds, f, indent=2)
print(f'임계값 저장: {MODELS_DIR}/hmm_thresholds.json')
```

`thresholds` dict는 `threshold_primary` 계산 후 저장한다.
step4에서 `hmm_model.pkl`과 `hmm_thresholds.json` 두 파일 모두 참조한다.

### 4. 길이 편향 검증

per-step 정규화가 길이 편향을 충분히 제거했는지 산점도로 확인한다:

```python
lengths_arr = np.array([len(seq) for seq in seq_df['sequence'].tolist()])
corr, p     = stats.pearsonr(lengths_arr, all_scores)
print(f'길이-점수 피어슨 상관: r={corr:.3f}, p={p:.4f}')
if abs(corr) > 0.3:
    print('⚠ 길이 편향 존재. 스코어링 방식 재검토 필요.')
```

`models/hmm_length_bias_check.png`로 저장한다.

### 5. 이상 시퀀스 샘플 출력

임계값 이하 덱의 시퀀스 패턴을 출력해 모델이 의미 있는 이상을 탐지하는지 확인한다:

```python
score_series = pd.Series(all_scores, index=seq_df['deck_id'])
anomaly_ids  = score_series[score_series < thresholds['threshold_primary']].index.tolist()

print(f'\n이상 탐지된 덱: {len(anomaly_ids)}개 (상위 10개)')
for deck_id in anomaly_ids[:10]:
    seq      = seq_df[seq_df['deck_id'] == deck_id].iloc[0]['sequence']
    readable = ' → '.join([ROLE_NAMES[r] for r in seq])
    print(f'  {deck_id} (score={score_series[deck_id]:.3f}): {readable}')
```

---

## Acceptance Criteria

```bash
python3 -c "
import json, ast, re
nb = json.load(open('notebooks/03_hmm_structure.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
ast.parse(re.sub(r'^[!%].*\$', '', src, flags=re.MULTILINE))
print('OK: notebooks/03_hmm_structure.ipynb')
"

python3 -c "
import json
nb = json.load(open('notebooks/03_hmm_structure.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
assert 'labeled_with_preds.csv' in src, 'CNN pred sequence missing'
assert 'compute_hmm_bic' in src,        'BIC function missing'
assert '[3, 4, 5, 6, 7]' in src,        'n_components range not expanded'
assert 'shapiro' in src,                'normality test missing'
assert 'threshold_primary' in src,      'threshold selection missing'
assert 'pearsonr' in src,               'length bias check missing'
print('All checks passed')
"
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - `labeled_with_preds.csv`가 있으면 `pred_label`을 사용하고, 없으면 `weak_label`로 fallback하는가?
   - `compute_hmm_bic`가 val 데이터로 계산하는가? (train 데이터 아님)
   - `hmm_thresholds.json`에 `method` 키가 있는가?
   - `sequences_cnn.csv`가 저장되는가?
3. `phases/4-ml-pipeline/index.json`의 step 3을 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "NB03 HMM 개선: CNN pred 시퀀스 재학습, BIC 선택(n=[3..7]), 정규성 검정 기반 임계값 결정"`
   - 수정 3회 시도 후에도 실패 → `"status": "error"`, `"error_message": "구체적 에러 내용"`
   - 사용자 개입 필요 → `"status": "blocked"`, `"blocked_reason": "구체적 사유"` 후 즉시 중단

## 금지사항

- `weak_labels.csv`의 `weak_label`을 HMM 학습에 직접 사용하지 마라. 반드시 `labeled_with_preds.csv`의 `pred_label`을 우선 사용한다. 학습과 추론 분포 불일치 방지가 핵심이다.
- BIC를 train 데이터로 계산하지 마라. 과적합 패널티를 반영하려면 val 데이터로 계산해야 한다.
- `n_iter`를 50 이하로 줄이지 마라. CategoricalHMM은 EM 알고리즘 수렴에 iteration이 많이 필요하다.
- `best_model`을 순회 중 업데이트하지 마라. `min(results, key=lambda r: r['bic'])` 패턴을 유지한다.
- 이상 탐지된 덱 목록을 파일로 저장하지 마라. 이 단계는 사람 검증용 출력이다. 실제 이상 판정은 step4에서 한다.
