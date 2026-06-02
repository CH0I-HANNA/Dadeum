# Step 0: eval-realign

## 읽어야 할 파일

먼저 아래 파일들을 읽고 현재 평가 설계의 근본적 결함을 파악하라:

- `/Users/choehanna/Documents/Dadeum/CLAUDE.md`
- `/Users/choehanna/Documents/Dadeum/docs/ARCHITECTURE.md`
- `/Users/choehanna/Documents/Dadeum/notebooks/04_evaluation.ipynb` — 현재 SlideAudit 평가 코드
- `/Users/choehanna/Documents/Dadeum/phases/5-research-quality/index.json`

**이 step을 시작하기 전에 반드시 이해해야 할 핵심 문제:**

현재 평가는 "구조 이상 탐지기"를 "디자인 결함 라벨(SlideAudit)"로 측정한다.
구조 이상(역할 순서 붕괴, 도입부/결론 누락)과 디자인 결함(폰트 크기, 색상 대비)은 직교(orthogonal)한다.
완벽한 구조 이상 탐지기도 이 평가에서 AUC ≈ 0.5가 나올 수 있다.
이를 해결하지 않으면 다른 모든 개선이 의미 없다.

---

## 작업

`notebooks/05_eval_realign.ipynb`를 새로 생성한다.

### 1. 합성 구조 이상 벤치마크 생성

정상 덱에 통제된 변형을 가해 구조 이상의 ground truth를 확보한다.
3가지 이상 유형 × 강도(mild/severe)로 총 6가지 변형을 정의한다.

```python
import random
import copy

def augment_shuffle_middle(sequence: list, seed: int = None) -> list:
    """중간 슬라이드 순서를 섞는다. 표지/마무리는 유지."""
    seq = copy.deepcopy(sequence)
    if len(seq) <= 3:
        return seq
    rng = random.Random(seed)
    middle = seq[1:-1]
    rng.shuffle(middle)
    return [seq[0]] + middle + [seq[-1]]

def augment_remove_boundary(sequence: list, side: str = 'both') -> list:
    """표지(0번), 마무리(끝) 슬라이드를 제거한다."""
    seq = copy.deepcopy(sequence)
    if side in ('start', 'both') and len(seq) > 2:
        seq = seq[1:]
    if side in ('end', 'both') and len(seq) > 2:
        seq = seq[:-1]
    return seq

def augment_duplicate_section(sequence: list, dup_ratio: float = 0.3, seed: int = None) -> list:
    """중간 슬라이드의 일부를 덱 앞부분에 삽입 (섹션 반복 이상)."""
    seq = copy.deepcopy(sequence)
    if len(seq) <= 4:
        return seq
    rng = random.Random(seed)
    middle = seq[1:-1]
    n_dup = max(1, int(len(middle) * dup_ratio))
    dup = rng.sample(middle, n_dup)
    # 표지 직후에 삽입
    return [seq[0]] + dup + seq[1:]
```

각 정상 덱에 대해 아래 변형을 적용해 `anomaly_type` 컬럼과 `is_anomaly` 컬럼을 부여한다:

```python
AUGMENT_TYPES = [
    ('normal',            lambda seq, i: seq,                                  0),
    ('shuffle_mild',      lambda seq, i: augment_shuffle_middle(seq, seed=i),  1),
    ('shuffle_severe',    lambda seq, i: augment_shuffle_middle(seq, seed=i),  1),  # 전체 랜덤
    ('no_boundary',       lambda seq, i: augment_remove_boundary(seq, 'both'), 1),
    ('no_cover',          lambda seq, i: augment_remove_boundary(seq, 'start'),1),
    ('dup_section',       lambda seq, i: augment_duplicate_section(seq, seed=i),1),
]
```

합성 벤치마크는 정상:이상 = 1:1 비율로 균형을 맞춘다.
`labels/synthetic_anomaly_benchmark.csv`로 저장한다.
컬럼: `deck_id`, `sequence`, `anomaly_type`, `is_anomaly`, `original_deck_id`

### 2. HMM 이상 탐지기로 합성 벤치마크 평가

```python
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

with open(f'{MODELS_DIR}/hmm_model.pkl', 'rb') as f:
    hmm_model = pickle.load(f)
with open(f'{MODELS_DIR}/hmm_thresholds.json') as f:
    thresholds = json.load(f)

benchmark_df = pd.read_csv(f'{LABELS_DIR}/synthetic_anomaly_benchmark.csv')
benchmark_df['sequence'] = benchmark_df['sequence'].apply(ast.literal_eval)

scores = []
for _, row in benchmark_df.iterrows():
    seq = np.array(row['sequence']).reshape(-1, 1)
    if len(seq) < 2:
        scores.append(0.5)
        continue
    ll = hmm_model.score(seq) / len(seq)
    z = (thresholds['mean'] - ll) / (thresholds['std'] + 1e-8)
    scores.append(float(np.clip(z / 3.0, 0, 1)))

benchmark_df['hmm_score'] = scores
labels = benchmark_df['is_anomaly'].values

auc_synthetic = roc_auc_score(labels, scores)
print(f'합성 벤치마크 AUC: {auc_synthetic:.4f}')

# 이상 유형별 분석
print('\n이상 유형별 평균 HMM score:')
for atype, group in benchmark_df.groupby('anomaly_type'):
    print(f'  {atype}: {group["hmm_score"].mean():.4f} (n={len(group)})')
```

### 3. SlideAudit AUC vs 합성 벤치마크 AUC 비교

두 AUC를 함께 리포트하는 셀을 작성한다.

```python
comparison = {
    'slideaudit_auc': '<NB04에서 가져올 것>',
    'synthetic_benchmark_auc': float(auc_synthetic),
    'gap': '<synthetic - slideaudit>',
    'interpretation': (
        'synthetic_benchmark_auc >> slideaudit_auc 이면: '
        '모델은 구조 이상을 실제로 탐지하지만 SlideAudit 평가가 부적절함을 의미.'
        '\nsynthetic_benchmark_auc ≈ slideaudit_auc ≈ 0.5 이면: '
        'HMM 자체가 구조를 인식하지 못하는 것 — weak label 문제로 귀환.'
    )
}
print(json.dumps(comparison, indent=2, ensure_ascii=False))
```

### 4. 이상 유형별 ROC 커브

```python
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 좌: 유형별 AUC 바 차트
type_aucs = {}
for atype in benchmark_df['anomaly_type'].unique():
    if atype == 'normal':
        continue
    subset = benchmark_df[benchmark_df['anomaly_type'].isin(['normal', atype])]
    if subset['is_anomaly'].sum() == 0:
        continue
    type_aucs[atype] = roc_auc_score(subset['is_anomaly'], subset['hmm_score'])

axes[0].barh(list(type_aucs.keys()), list(type_aucs.values()), color='steelblue')
axes[0].axvline(0.5, color='red', linestyle='--', label='Random')
axes[0].set_xlabel('AUC')
axes[0].set_title('이상 유형별 HMM AUC')
axes[0].legend()

# 우: 전체 ROC
fpr, tpr, _ = roc_curve(labels, scores)
axes[1].plot(fpr, tpr, label=f'HMM (AUC={auc_synthetic:.3f})')
axes[1].plot([0,1],[0,1],'k:')
axes[1].set_xlabel('FPR')
axes[1].set_ylabel('TPR')
axes[1].set_title('합성 벤치마크 ROC')
axes[1].legend()

plt.tight_layout()
plt.savefig(f'{MODELS_DIR}/synthetic_benchmark_roc.png', dpi=120)
plt.show()
```

합성 벤치마크 결과를 `models/eval_comparison.json`으로 저장한다.

---

## Acceptance Criteria

```bash
python3 -c "
import json, ast, re
nb = json.load(open('notebooks/05_eval_realign.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
ast.parse(re.sub(r'^[!%].*$', '', src, flags=re.MULTILINE))
print('OK: syntax')
"

python3 -c "
import json
nb = json.load(open('notebooks/05_eval_realign.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
assert 'augment_shuffle_middle' in src,       'shuffle augmentation missing'
assert 'augment_remove_boundary' in src,      'boundary removal missing'
assert 'augment_duplicate_section' in src,    'section duplication missing'
assert 'synthetic_anomaly_benchmark.csv' in src, 'benchmark save missing'
assert 'auc_synthetic' in src,                'synthetic AUC missing'
assert 'eval_comparison.json' in src,         'comparison save missing'
print('All checks passed')
"
```

## 검증 절차

1. AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - `augment_shuffle_severe`가 표지/마무리를 포함한 전체를 섞는가? (mild는 중간만)
   - 정상:이상 비율이 1:1인가?
   - `eval_comparison.json`에 SlideAudit AUC와 합성 AUC가 함께 기록됐는가?
3. 결과 해석:
   - `auc_synthetic < 0.6` → HMM이 구조를 전혀 인식하지 못함 (weak label 문제 확인)
   - `auc_synthetic > 0.7` → HMM은 작동하지만 SlideAudit 평가가 부적절함 (평가 재설계 필요)
4. `phases/5-research-quality/index.json`의 step 0을 업데이트한다:
   - 성공 → `"status": "completed"`, `"summary": "합성 벤치마크 생성 (6종 이상 유형), HMM AUC 측정, SlideAudit 평가와 비교"`
   - 수정 3회 후 실패 → `"status": "error"`, `"error_message": "구체적 에러"`
   - 사용자 개입 필요 → `"status": "blocked"`, `"blocked_reason": "사유"` 후 중단

## 금지사항

- `augment_shuffle_severe`와 `augment_shuffle_mild`를 동일하게 구현하지 마라. mild는 중간 슬라이드만, severe는 표지/마무리를 포함한 전체 순서를 섞는다.
- 정상 샘플과 이상 샘플을 같은 덱에서 생성할 때 `deck_id`를 동일하게 쓰지 마라. `{original_deck_id}_anomaly_{type}` 형태로 고유 ID를 부여한다.
- SlideAudit AUC를 직접 이 노트북에서 계산하지 마라. NB04의 결과를 가져와 비교만 한다.
- 합성 이상 비율을 50% 이상으로 올리지 마라. 실제 이상치 기준과 일치해야 한다.
