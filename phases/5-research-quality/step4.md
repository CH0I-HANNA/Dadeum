# Step 4: stats-significance

## 읽어야 할 파일

먼저 아래 파일들을 읽어라:

- `/Users/choehanna/Documents/Dadeum/CLAUDE.md`
- `/Users/choehanna/Documents/Dadeum/notebooks/04_evaluation.ipynb`
- `/Users/choehanna/Documents/Dadeum/models/baseline_results.json` (step2 결과)
- `/Users/choehanna/Documents/Dadeum/models/sensitivity_results.json` (step3 결과)
- `/Users/choehanna/Documents/Dadeum/phases/5-research-quality/step3.md`

**이 step의 동기:**

현재 모든 AUC는 단일 run, 단일 seed의 point estimate다.
AUC 0.72 vs 0.68의 차이가 noise인지 signal인지 알 수 없다.
NeurIPS/ICLR 논문에서는 최소한 bootstrap confidence interval이 요구된다.
이 step은 모든 주요 결과에 통계적 유의성을 추가한다.

이전 step에서 생성된 파일:
- `models/baseline_results.json` (step2)
- `models/sensitivity_results.json` (step3)
- `labels/synthetic_anomaly_benchmark.csv` (step0)

---

## 작업

`notebooks/09_stats_significance.ipynb`를 새로 생성한다.

### 1. Bootstrap Confidence Interval for AUC

```python
import numpy as np
from sklearn.metrics import roc_auc_score

def bootstrap_auc_ci(
    y_true: np.ndarray,
    y_score: np.ndarray,
    n_bootstrap: int = 1000,
    ci: float = 0.95,
    seed: int = 42,
) -> tuple[float, float, float]:
    """
    Bootstrap으로 AUC의 신뢰구간을 계산.
    Returns: (auc_mean, ci_lower, ci_upper)
    """
    rng = np.random.RandomState(seed)
    auc_scores = []
    n = len(y_true)

    for _ in range(n_bootstrap):
        idx = rng.choice(n, n, replace=True)
        yt, ys = y_true[idx], y_score[idx]
        if len(np.unique(yt)) < 2:
            continue
        auc_scores.append(roc_auc_score(yt, ys))

    auc_arr = np.array(auc_scores)
    alpha = (1 - ci) / 2
    return float(np.mean(auc_arr)), float(np.percentile(auc_arr, alpha * 100)), float(np.percentile(auc_arr, (1 - alpha) * 100))
```

모든 베이스라인과 제안 방법에 대해 CI를 계산한다:

```python
all_methods = {
    'B0_random':        (benchmark_labels, random_scores),
    'B1_position':      (benchmark_labels, position_scores),
    'B2_clip_if':       (benchmark_labels, clip_if_scores),
    'B3_dino_if':       (benchmark_labels, dino_if_scores),
    'proposed_combined': (benchmark_labels, proposed_scores),
}

ci_results = {}
for name, (yt, ys) in all_methods.items():
    mean, lo, hi = bootstrap_auc_ci(yt, ys, n_bootstrap=1000)
    ci_results[name] = {'mean': mean, 'ci_lower': lo, 'ci_upper': hi, 'ci_width': hi - lo}
    print(f'{name}: AUC={mean:.4f} [{lo:.4f}, {hi:.4f}]')
```

### 2. McNemar Test — Proposed vs Best Baseline

두 방법이 같은 샘플에서 다르게 예측하는지 검정한다.
threshold는 0.5 (또는 최적 threshold):

```python
from statsmodels.stats.contingency_tables import mcnemar

def scores_to_binary(scores, threshold=0.5):
    return (np.array(scores) > threshold).astype(int)

proposed_pred  = scores_to_binary(proposed_scores)
best_base_pred = scores_to_binary(best_baseline_scores)
labels_binary  = np.array(benchmark_labels)

# 혼동 행렬 구성
b = np.sum((proposed_pred == 1) & (best_base_pred == 0) & (labels_binary == 1))
c = np.sum((proposed_pred == 0) & (best_base_pred == 1) & (labels_binary == 1))

result = mcnemar([[0, b], [c, 0]], exact=True)
print(f'McNemar test: p={result.pvalue:.4f}')
if result.pvalue < 0.05:
    print('✓ 두 방법 간 통계적으로 유의미한 차이 (p<0.05)')
else:
    print('⚠ 두 방법 간 통계적으로 유의미한 차이 없음 (p≥0.05) — 논문 claim 수정 필요')
```

### 3. 다중 Seed 검증 (3 seeds)

단일 seed 결과의 안정성을 검증한다:

```python
SEEDS = [42, 123, 2024]
multi_seed_results = []

for seed in SEEDS:
    np.random.seed(seed)
    # 동일한 파이프라인을 seed만 바꿔 재실행
    # (실제 CNN 재학습은 시간이 걸리므로, bootstrap으로 데이터 분할만 변경)
    idx = np.random.permutation(len(benchmark_labels))
    yt = np.array(benchmark_labels)[idx]
    ys = np.array(proposed_scores)[idx]
    auc = roc_auc_score(yt, ys)
    multi_seed_results.append({'seed': seed, 'auc': float(auc)})
    print(f'Seed {seed}: AUC={auc:.4f}')

seed_std = np.std([r['auc'] for r in multi_seed_results])
print(f'\nAUC std across seeds: {seed_std:.4f}')
if seed_std > 0.02:
    print('⚠ 결과가 seed에 민감함 — 더 많은 seed에서 검증 필요')
```

### 4. 통계적 검정 결과 통합 보고서

논문 Table 형식으로 결과를 정리한다:

```python
import pandas as pd

table_rows = []
for name, ci in ci_results.items():
    table_rows.append({
        'Method':    name,
        'AUC':       f'{ci["mean"]:.4f}',
        '95% CI':    f'[{ci["ci_lower"]:.4f}, {ci["ci_upper"]:.4f}]',
        'CI Width':  f'{ci["ci_width"]:.4f}',
    })

result_table = pd.DataFrame(table_rows)
print(result_table.to_string(index=False))
print()

# 결과 저장
stats_report = {
    'ci_results': ci_results,
    'mcnemar_pvalue': float(result.pvalue),
    'mcnemar_significant': bool(result.pvalue < 0.05),
    'multi_seed_std': float(seed_std),
    'seed_stable': bool(seed_std <= 0.02),
}
with open(f'{MODELS_DIR}/stats_significance.json', 'w') as f:
    json.dump(stats_report, f, indent=2)
print(json.dumps(stats_report, indent=2))
```

### 5. CI 시각화 (Error Bar Plot)

```python
import matplotlib.pyplot as plt

names  = list(ci_results.keys())
means  = [ci_results[n]['mean'] for n in names]
errors = [
    [ci_results[n]['mean'] - ci_results[n]['ci_lower'] for n in names],
    [ci_results[n]['ci_upper'] - ci_results[n]['mean'] for n in names],
]

fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(names, means, xerr=errors, capsize=5, color='steelblue', alpha=0.7, ecolor='black')
ax.axvline(0.5, color='red', linestyle='--', label='Random')
ax.set_xlabel('AUC ± 95% CI')
ax.set_title('방법별 AUC 비교 (Bootstrap 95% CI)')
ax.legend()
plt.tight_layout()
plt.savefig(f'{MODELS_DIR}/auc_with_ci.png', dpi=120)
plt.show()
```

---

## Acceptance Criteria

```bash
python3 -c "
import json, ast, re
nb = json.load(open('notebooks/09_stats_significance.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
ast.parse(re.sub(r'^[!%].*$', '', src, flags=re.MULTILINE))
print('OK: syntax')
"

python3 -c "
import json
nb = json.load(open('notebooks/09_stats_significance.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
assert 'bootstrap_auc_ci' in src,         'bootstrap CI function missing'
assert 'n_bootstrap' in src,              'bootstrap param missing'
assert 'mcnemar' in src,                  'McNemar test missing'
assert 'pvalue' in src,                   'p-value missing'
assert 'stats_significance.json' in src,  'result save missing'
assert 'auc_with_ci.png' in src,          'CI plot missing'
print('All checks passed')
"
```

## 검증 절차

1. AC 커맨드를 실행한다.
2. 체크리스트:
   - bootstrap n_bootstrap ≥ 1000인가?
   - `mcnemar_significant == false`이면 → 논문에서 "우리 방법이 유의미하게 낫다"는 claim을 제거하거나 약화해야 한다
   - 95% CI가 베이스라인과 겹치면 → 방법론적 기여 claim을 재검토해야 한다
3. `phases/5-research-quality/index.json`의 step 4를 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "Bootstrap CI (n=1000), McNemar test, multi-seed std 계산 완료"`
   - 수정 3회 후 실패 → `"status": "error"`
   - 사용자 개입 필요 → `"status": "blocked"`

## 금지사항

- bootstrap에서 stratified sampling 없이 label 비율이 무너지는 경우를 처리하지 않으면 안 된다. `if len(np.unique(yt)) < 2: continue` 처리를 반드시 포함한다.
- McNemar test를 exact=False로 실행하지 마라. 샘플 수가 충분하지 않을 때는 exact test가 더 보수적으로 정확하다.
- p값을 0.05를 기준으로 이분법적으로 해석하지 마라. effect size와 CI width를 함께 보고한다.
- 통계 결과가 불리하다고 해서 threshold를 조정하거나 subset을 선택해 유의미한 결과를 만들지 마라. 이는 p-hacking이다.
