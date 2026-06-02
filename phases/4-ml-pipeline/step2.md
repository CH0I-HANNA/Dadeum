# Step 2: Notebook 03 — HMM 서사 구조 모델 개선

## 개요

`notebooks/03_hmm_structure.ipynb`는 발표자료의 슬라이드 역할 시퀀스를 HMM으로 학습하여 구조 이상을 탐지한다.  
현재 코드는 동작하지만 3가지 핵심 문제가 있다.

1. **모델 선택 기준 없음**: `n_components` 3~5를 그냥 val score 최대값으로 고르는데, log-likelihood는 파라미터가 많을수록 항상 증가하는 경향이 있어 신뢰할 수 없다. BIC로 penalty를 부여해야 한다.
2. **임계값이 불안정**: 단순 5th percentile은 데이터 분포가 skewed할 때 너무 공격적이거나 너무 관대할 수 있다. 정규성 검정 후 방법을 결정해야 한다.
3. **시퀀스 길이 편향**: 슬라이드 수가 많은 덱은 log-likelihood 합이 낮아져 짧은 덱과 단순 비교가 불공평하다. per-step 정규화를 이미 하고 있지만, 검증하지 않고 있다.

---

## 읽어야 할 파일

- `notebooks/03_hmm_structure.ipynb` — 전체 흐름
- `notebooks/01_data_preparation.ipynb` — sequences.csv 컬럼 구조 확인

---

## 개선 작업

### 1. BIC 기반 n_components 선택

현재 val log-likelihood 최대값으로 선택하는 코드를 BIC 최솟값 기준으로 교체한다.

BIC 공식: `BIC = -2 * log_likelihood + k * log(N)`  
- `k`: 모델 파라미터 수 (전이 확률 + 방출 확률)
- `N`: 전체 관측 수

```python
def compute_hmm_bic(model, X, lengths):
    """HMM의 BIC 계산. 낮을수록 좋다."""
    log_likelihood = model.score(X, lengths)
    n_samples = len(X)
    n_components = model.n_components
    n_observations = 5  # NUM_ROLES

    # 파라미터 수: 초기확률(n-1) + 전이행렬(n*(n-1)) + 방출행렬(n*(obs-1))
    n_params = (n_components - 1) + n_components * (n_components - 1) + n_components * (n_observations - 1)
    bic = -2 * log_likelihood + n_params * np.log(n_samples)
    return bic, log_likelihood


results = []
for n_components in [3, 4, 5, 6, 7]:   # 탐색 범위 확장
    model = hmm.CategoricalHMM(
        n_components=n_components,
        n_iter=200,           # 수렴 안정성을 위해 100 → 200
        random_state=42,
        verbose=False,
    )
    model.fit(X_train, lengths_train)
    bic, ll = compute_hmm_bic(model, X_val, lengths_val)
    val_score = ll / len(X_val)
    results.append({
        'n_components': n_components,
        'bic': bic,
        'val_score': val_score,
        'model': model
    })
    print(f'n_components={n_components} | BIC={bic:.1f} | val ll/step={val_score:.4f}')

# BIC 최솟값으로 선택
best_result = min(results, key=lambda r: r['bic'])
best_model = best_result['model']
best_n = best_result['n_components']
best_score = best_result['val_score']
print(f'\nBIC 기준 최적 n_components={best_n} (BIC={best_result["bic"]:.1f})')
```

BIC 결과를 테이블로 시각화한다:

```python
results_df = pd.DataFrame([{
    'n_components': r['n_components'],
    'BIC': round(r['bic'], 1),
    'Val LL/step': round(r['val_score'], 4)
} for r in results])
print(results_df.to_string(index=False))

# BIC 커브
plt.figure(figsize=(7, 4))
plt.plot([r['n_components'] for r in results],
         [r['bic'] for r in results], 'o-', color='steelblue')
plt.axvline(best_n, color='red', linestyle='--', label=f'선택: n={best_n}')
plt.xlabel('은닉 상태 수 (n_components)')
plt.ylabel('BIC')
plt.title('HMM 모델 선택 — BIC')
plt.legend()
plt.tight_layout()
plt.savefig(f'{MODELS_DIR}/hmm_bic_curve.png', dpi=100)
plt.show()
```

---

### 2. 임계값 결정 — 정규성 검정 후 방법 선택

현재 단순 5th/10th percentile을 사용한다. 분포가 정규에 가까우면 3-sigma를 쓰고, 그렇지 않으면 percentile을 유지하도록 자동화한다.

`all_scores`는 기존 노트북의 `## 4. 이상 임계값 결정` 섹션 상단, 즉 `best_model`이 결정된 직후 아래 코드로 계산된다:

```python
# best_model 선택 완료 후 — 전체 데이터에 대한 per-step 스코어 계산
all_scores = []
for seq in seq_df['sequence'].tolist():
    x = np.array(seq).reshape(-1, 1)
    score = best_model.score(x) / len(seq)
    all_scores.append(score)
all_scores = np.array(all_scores)
```

이 계산이 완료된 후 아래의 정규성 검정을 실행한다.

```python
from scipy import stats

# 정규성 검정 (Shapiro-Wilk, 5000개 초과 시 경고를 피하기 위해 샘플링)
sample_for_test = all_scores[:5000]
stat, p_value = stats.shapiro(sample_for_test)
print(f'Shapiro-Wilk: stat={stat:.4f}, p={p_value:.4f}')
is_normal = p_value > 0.05

if is_normal:
    # 정규 분포: mean ± 3σ 방식
    mean_score = float(np.mean(all_scores))
    std_score = float(np.std(all_scores))
    threshold_method = 'gaussian_3sigma'
    threshold_primary = mean_score - 3 * std_score
    print(f'정규 분포 → 3-sigma 임계값: {threshold_primary:.4f}')
else:
    # 비정규 분포: percentile 방식 유지
    threshold_method = 'percentile'
    threshold_primary = float(np.percentile(all_scores, 5))
    print(f'비정규 분포 → 5th percentile 임계값: {threshold_primary:.4f}')

thresholds = {
    'method': threshold_method,
    'threshold_primary': threshold_primary,
    'threshold_5pct': float(np.percentile(all_scores, 5)),
    'threshold_10pct': float(np.percentile(all_scores, 10)),
    'mean': float(np.mean(all_scores)),
    'std': float(np.std(all_scores)),
    'shapiro_p': float(p_value),
    'n_decks': len(all_scores),
}
```

---

### 3. 시퀀스 길이 vs. 이상 점수 상관관계 검증

per-step 정규화가 충분히 길이 편향을 제거했는지 시각화로 확인한다.

```python
lengths_arr = np.array([len(seq) for seq in seq_df['sequence'].tolist()])

# 길이-점수 산점도
plt.figure(figsize=(8, 5))
plt.scatter(lengths_arr, all_scores, alpha=0.3, s=5, color='steelblue')
plt.xlabel('덱 슬라이드 수')
plt.ylabel('Log-Likelihood per Step')
plt.title('시퀀스 길이 vs. 이상 점수')
plt.axhline(thresholds['threshold_primary'], color='red', linestyle='--',
            label=f'임계값: {thresholds["threshold_primary"]:.3f}')
plt.legend()
plt.tight_layout()
plt.savefig(f'{MODELS_DIR}/hmm_length_bias_check.png', dpi=100)
plt.show()

# 피어슨 상관계수
corr, p = stats.pearsonr(lengths_arr, all_scores)
print(f'길이-점수 피어슨 상관: r={corr:.3f}, p={p:.4f}')
if abs(corr) > 0.3:
    print('⚠ 길이 편향 존재. 임베딩 정규화 또는 다른 스코어링 방식 검토 필요.')
else:
    print('길이 편향 없음 (|r| < 0.3)')
```

---

### 4. 이상 시퀀스 샘플 출력 — 해석 가능성

임계값 이하인 덱의 시퀀스 패턴을 직접 출력해 모델이 실제로 이상한 덱을 잡고 있는지 확인한다.

```python
score_series = pd.Series(all_scores, index=seq_df['deck_id'])
anomaly_ids = score_series[score_series < thresholds['threshold_primary']].index.tolist()

print(f'\n=== 이상 탐지된 덱 (하위 5%): {len(anomaly_ids)}개 ===')
for deck_id in anomaly_ids[:10]:
    row = seq_df[seq_df['deck_id'] == deck_id].iloc[0]
    seq = row['sequence']
    readable = ' → '.join([ROLE_NAMES[r] for r in seq])
    score = score_series[deck_id]
    print(f'  {deck_id} (score={score:.3f}): {readable}')
```

이 출력을 보고 이상한 패턴이 실제로 의미 있는지 (예: 표지 없이 시작, 본문 없이 끝나는 덱) 사람 눈으로 검증한다.

---

### 5. HMM 재학습 — CNN 예측 시퀀스 기반

**현재 구조의 핵심 버그**: HMM은 `weak_label` (규칙 기반 라벨)로 학습되지만, Notebook 04 추론 시에는 CNN이 예측한 역할을 시퀀스로 입력한다.  
CNN 예측은 weak_label과 다를 수 있고(특히 경계 케이스), 두 분포가 다른 HMM으로 추론하면 log-likelihood 자체가 의미없는 값이 된다.

**해결**: CNN 학습 완료 후, CNN 예측값으로 시퀀스를 재구성해 HMM을 다시 학습한다.

아래 셀을 `## 1. 시퀀스 데이터 로드` 앞에 추가한다:

```python
import pandas as pd
import numpy as np
import ast
from pathlib import Path

# Notebook 02가 저장한 CNN 예측 결과 확인
pred_csv = Path(f'{LABELS_DIR}/labeled_with_preds.csv')

if pred_csv.exists():
    # CNN 예측 기반 시퀀스 사용 (권장)
    pred_df = pd.read_csv(pred_csv)
    label_col = 'pred_label'
    print(f'CNN 예측 기반 시퀀스 사용 (labeled_with_preds.csv)')
else:
    # Fallback: weak_label 기반 (Notebook 02 미실행 시)
    pred_df = pd.read_csv(f'{LABELS_DIR}/weak_labels.csv')
    label_col = 'weak_label'
    print('⚠ CNN 예측 없음 — weak_label 사용 (Notebook 02 실행 권장)')

# CNN 예측 기반 시퀀스 재생성
sequences_cnn = []
for deck_id, group in pred_df.groupby('deck_id'):
    group = group.sort_values('slide_idx')
    seq = group[label_col].tolist()
    if len(seq) < 2:
        continue
    sequences_cnn.append({'deck_id': deck_id, 'sequence': seq, 'length': len(seq)})

seq_df = pd.DataFrame(sequences_cnn)
print(f'CNN 기반 시퀀스 수: {len(seq_df)}')

# 저장 (이후 섹션에서 seq_df 그대로 사용)
seq_df.to_csv(f'{LABELS_DIR}/sequences_cnn.csv', index=False)
```

`seq_df`가 CNN 예측 기반으로 준비됐으므로 이후 HMM 학습, 임계값 계산, 이상 탐지는 동일 코드로 진행한다.

---

### 6. 전이 행렬 시각화 개선 — seaborn annotation 크기 조정

현재 seaborn heatmap에서 셀 수가 많아지면 annotation이 겹친다.  
`fmt='.2f'`를 `fmt='.1%'`(퍼센트)로 바꾸고 폰트 크기를 지정한다:

```python
sns.heatmap(
    transition_prob,
    annot=True, fmt='.1%',
    annot_kws={'size': 9},
    xticklabels=ROLE_NAMES,
    yticklabels=ROLE_NAMES,
    cmap='YlOrRd',
    linewidths=0.5,
    linecolor='white',
)
```

---

## Acceptance Criteria

```
- labeled_with_preds.csv가 있으면 pred_label을 사용하고, 없으면 weak_label로 fallback하는가?
- seq_df가 CNN 예측 기반으로 생성되고 sequences_cnn.csv로 저장되는가?
- compute_hmm_bic 함수가 정의되어 있는가?
- n_components 탐색 범위가 [3, 4, 5, 6, 7]인가?
- BIC 최솟값으로 best_model이 선택되는가?
- {MODELS_DIR}/hmm_bic_curve.png가 생성되는가?
- Shapiro-Wilk 검정 결과에 따라 threshold_method가 'gaussian_3sigma' 또는 'percentile'로 설정되는가?
- hmm_thresholds.json에 'method' 키가 있는가?
- {MODELS_DIR}/hmm_length_bias_check.png가 생성되는가?
- 피어슨 상관 계수와 p-value가 출력되는가?
```

## 금지사항

- `weak_labels.csv`의 `weak_label` 컬럼을 HMM 학습에 직접 사용하지 마라. `labeled_with_preds.csv`의 `pred_label`을 우선 사용해야 HMM 학습과 Notebook 04 추론 시퀀스가 동일한 분포를 갖는다.
- `n_iter`를 50 이하로 줄이지 마라. CategoricalHMM은 EM 알고리즘으로 학습하며 수렴에 iteration이 많이 필요하다.
- BIC를 train 데이터로 계산하지 마라. 반드시 val 데이터로 계산한다 (과적합 패널티 반영).
- `best_model`을 `results` 리스트 순회 중에 업데이트하는 방식으로 되돌리지 마라. `min(results, key=...)` 패턴을 유지해야 BIC 계산 후 모든 후보를 비교할 수 있다.
- `scipy.stats`를 별도 패키지로 설치하지 마라. Colab에 이미 포함돼 있다.
- 이상 탐지된 덱 목록을 파일로 저장하지 마라. 이 단계는 사람 검증을 위한 print 출력이다. 실제 이상 판정은 Notebook 04에서 한다.
