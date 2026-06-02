# Step 1: clip-weak-label

## 읽어야 할 파일

먼저 아래 파일들을 읽고 현재 weak label의 결함을 이해하라:

- `/Users/choehanna/Documents/Dadeum/CLAUDE.md`
- `/Users/choehanna/Documents/Dadeum/notebooks/01_data_preparation.ipynb` — 현재 position-only 라벨링 코드
- `/Users/choehanna/Documents/Dadeum/notebooks/02_cnn_role_classifier.ipynb` — CNN 학습 코드
- `/Users/choehanna/Documents/Dadeum/phases/5-research-quality/step0.md`

**이 step의 전제 조건 및 동기:**

`assign_weak_label_image`는 위치만 사용한다 (first→COVER, last→CLOSING, 나머지→BODY).
이 라벨로 학습한 CNN은 slide position을 외울 뿐 슬라이드 내용을 이해하지 못한다.
CLIP의 zero-shot 능력을 활용하면 학습 없이 더 의미 있는 역할 라벨을 부여할 수 있다.
이 step은 CNN 재학습 없이 라벨 품질 개선 → 기존 CNN과 CLIP 라벨 CNN의 downstream AUC 비교로 기여를 증명한다.

---

## 작업

`notebooks/06_clip_weak_label.ipynb`를 새로 생성한다.

### 1. CLIP 설치 및 로드

```python
!pip install -q open-clip-torch

import open_clip
import torch
from PIL import Image

device = 'cuda' if torch.cuda.is_available() else 'cpu'

model, _, preprocess = open_clip.create_model_and_transforms(
    'ViT-B-32', pretrained='openai'
)
model = model.to(device).eval()
tokenizer = open_clip.get_tokenizer('ViT-B-32')
print('CLIP 로드 완료')
```

### 2. 역할별 텍스트 프롬프트 정의

각 역할에 대해 다수의 프롬프트를 사용하는 prompt ensemble 전략을 적용한다.
단일 프롬프트보다 평균 임베딩을 사용하면 zero-shot 정확도가 약 3~5% 향상된다:

```python
ROLE_PROMPTS = {
    0: [  # 표지 (COVER)
        "a title slide of a presentation",
        "a cover slide with the presentation title and author",
        "the first slide of a PowerPoint presentation showing the main title",
    ],
    1: [  # 섹션헤더 (SECTION HEADER)
        "a section header slide dividing presentation topics",
        "a chapter title slide with a single large heading",
        "a transition slide announcing a new section",
    ],
    2: [  # 본문 (BODY / CONTENT)
        "a content slide with bullet points and text",
        "a slide with detailed information and body text",
        "a presentation slide showing data analysis or explanation",
    ],
    3: [  # 도표/시각자료 (VISUAL)
        "a slide with a chart, graph, or data visualization",
        "a slide showing a diagram, table, or figure",
        "a visual slide with an infographic or illustration",
    ],
    4: [  # 마무리 (CLOSING)
        "a thank you slide ending a presentation",
        "a conclusion slide with summary or next steps",
        "the last slide of a presentation with contact information",
    ],
}
```

텍스트 임베딩을 미리 계산해서 캐싱한다:

```python
import numpy as np

role_text_embeddings = {}
for role_id, prompts in ROLE_PROMPTS.items():
    tokens = tokenizer(prompts).to(device)
    with torch.no_grad():
        embs = model.encode_text(tokens)
        embs = embs / embs.norm(dim=-1, keepdim=True)
    role_text_embeddings[role_id] = embs.mean(dim=0)  # prompt ensemble 평균

print('텍스트 임베딩 계산 완료')
```

### 3. CLIP zero-shot 역할 분류 함수

```python
def clip_classify_role(image_path: str) -> tuple[int, list[float]]:
    """
    CLIP으로 슬라이드 역할을 분류.
    Returns: (predicted_role_id, similarity_scores_per_role)
    """
    img = preprocess(Image.open(image_path).convert('RGB')).unsqueeze(0).to(device)
    with torch.no_grad():
        img_emb = model.encode_image(img)
        img_emb = img_emb / img_emb.norm(dim=-1, keepdim=True)

    sims = []
    for role_id in range(5):
        text_emb = role_text_embeddings[role_id].unsqueeze(0)
        sim = (img_emb @ text_emb.T).item()
        sims.append(sim)

    return int(np.argmax(sims)), sims
```

### 4. 전체 슬라이드에 CLIP 라벨 부여

체크포인트: `labels/clip_labels_cache.pkl`로 중간 결과를 저장한다.
배치 처리로 속도를 높인다 (이미지 64장씩 CLIP 인퍼런스):

```python
from pathlib import Path
from tqdm import tqdm
import pickle, pandas as pd

df = pd.read_csv(f'{LABELS_DIR}/weak_labels.csv')

clip_cache = Path(f'{LABELS_DIR}/clip_labels_cache.pkl')
if clip_cache.exists():
    with open(clip_cache, 'rb') as f:
        cached = pickle.load(f)
    print(f'CLIP 라벨 캐시 로드: {len(cached)}개')
else:
    cached = {}

clip_labels = []
clip_scores = []

for _, row in tqdm(df.iterrows(), total=len(df), desc='CLIP 분류'):
    path = row['image_path']
    if path in cached:
        label, scores = cached[path]
    else:
        if not Path(path).exists():
            label, scores = 2, [0.0] * 5  # fallback: BODY
        else:
            label, scores = clip_classify_role(path)
        cached[path] = (label, scores)
    clip_labels.append(label)
    clip_scores.append(scores)

with open(clip_cache, 'wb') as f:
    pickle.dump(cached, f)

df['clip_label']     = clip_labels
df['clip_label_name'] = [ROLE_NAMES[l] for l in clip_labels]
df['clip_scores']    = clip_scores

df.to_csv(f'{LABELS_DIR}/weak_labels_clip.csv', index=False)
print(f'CLIP 라벨 저장: {LABELS_DIR}/weak_labels_clip.csv')
```

### 5. Position 라벨 vs CLIP 라벨 분포 비교

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Position 라벨 분포
pos_counts = df['weak_label'].value_counts().sort_index()
axes[0].bar([ROLE_NAMES[i] for i in pos_counts.index], pos_counts.values, color='tomato')
axes[0].set_title('Position-only 라벨 분포')
axes[0].set_ylabel('슬라이드 수')
axes[0].tick_params(axis='x', rotation=30)

# CLIP 라벨 분포
clip_counts = df['clip_label'].value_counts().sort_index()
axes[1].bar([ROLE_NAMES[i] for i in clip_counts.index], clip_counts.values, color='steelblue')
axes[1].set_title('CLIP zero-shot 라벨 분포')
axes[1].tick_params(axis='x', rotation=30)

plt.tight_layout()
plt.savefig(f'{MODELS_DIR}/label_distribution_comparison.png', dpi=120)
plt.show()

# 일치율 분석
agreement = (df['weak_label'] == df['clip_label']).mean()
print(f'Position vs CLIP 일치율: {agreement:.2%}')
print('\n혼동 행렬 (position → CLIP):')
from sklearn.metrics import confusion_matrix
cm = confusion_matrix(df['weak_label'], df['clip_label'])
print(pd.DataFrame(cm, index=ROLE_NAMES, columns=ROLE_NAMES))
```

### 6. CLIP 라벨로 CNN 재학습 — NB02 파라미터 재사용

`weak_labels_clip.csv`의 `clip_label`을 사용해 NB02를 재실행하는 셀을 작성한다.
재학습 결과를 `models/role_classifier_clip_best.pt`로 저장한다.
기존 `role_classifier_best.pt`(position 라벨)와 동일한 아키텍처/하이퍼파라미터를 유지한다 — 라벨 품질 효과만 격리하기 위해.

```python
# NB02와 동일한 학습 코드를 여기에 복사하되, 아래 두 줄만 바꾼다:
# df = pd.read_csv(f'{LABELS_DIR}/weak_labels_clip.csv')   ← clip 라벨 파일
# label_col = 'clip_label'                                  ← clip_label 사용
# 저장 경로: f'{MODELS_DIR}/role_classifier_clip_best.pt'
```

### 7. Position 라벨 CNN vs CLIP 라벨 CNN 비교

합성 벤치마크(NB05에서 생성)와 SlideAudit 모두에서 두 모델의 AUC를 비교한다:

```python
comparison = {
    'position_label_cnn': {
        'val_acc': '<NB02 결과>',
        'synthetic_auc': '<NB05 결과>',
        'slideaudit_auc': '<NB04 결과>',
    },
    'clip_label_cnn': {
        'val_acc': '<재학습 결과>',
        'synthetic_auc': '<이 노트북에서 측정>',
        'slideaudit_auc': '<이 노트북에서 측정>',
    },
}
print(json.dumps(comparison, indent=2, ensure_ascii=False))
```

결과를 `models/label_quality_comparison.json`으로 저장한다.

---

## Acceptance Criteria

```bash
python3 -c "
import json, ast, re
nb = json.load(open('notebooks/06_clip_weak_label.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
ast.parse(re.sub(r'^[!%].*$', '', src, flags=re.MULTILINE))
print('OK: syntax')
"

python3 -c "
import json
nb = json.load(open('notebooks/06_clip_weak_label.ipynb'))
src = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
assert 'open_clip' in src,                    'CLIP library missing'
assert 'ROLE_PROMPTS' in src,                 'prompt ensemble missing'
assert 'clip_labels_cache.pkl' in src,        'checkpoint missing'
assert 'weak_labels_clip.csv' in src,         'clip label save missing'
assert 'label_quality_comparison.json' in src,'comparison save missing'
assert 'agreement' in src,                    'agreement metric missing'
print('All checks passed')
"
```

## 검증 절차

1. AC 커맨드를 실행한다.
2. 아키텍처 체크리스트:
   - CLIP 라벨 분포에서 5개 클래스가 모두 non-zero인가? (position 라벨은 3개만 사용)
   - `clip_labels_cache.pkl`이 저장돼서 세션 재시작 시 CLIP 재실행을 건너뛰는가?
   - CNN 재학습 시 NB02와 동일한 아키텍처/하이퍼파라미터를 사용하는가?
   - `label_quality_comparison.json`에 두 모델의 AUC가 모두 기록됐는가?
3. 결과 해석:
   - CLIP CNN val_acc > position CNN val_acc → CLIP 라벨이 더 의미 있는 특징을 학습시킴 (논문에서 주요 contribution으로 사용 가능)
   - CLIP CNN val_acc ≈ position CNN val_acc → 이미지에서 역할을 구별하기 어려운 데이터셋 (모델 architecture 문제로 전환)
4. `phases/5-research-quality/index.json`의 step 1을 업데이트한다.

## 금지사항

- CLIP을 fine-tuning하지 마라. zero-shot 성능만 측정한다. fine-tuning하면 position label CNN과의 공정한 비교가 불가능하다.
- `clip_classify_role`을 배치 없이 이미지 1장씩 처리하지 마라. 10K 슬라이드를 1장씩 처리하면 수 시간이 걸린다.
- CLIP 라벨로 NB02를 재학습할 때 모델 저장 경로를 `role_classifier_best.pt`로 덮어쓰지 마라. 반드시 `role_classifier_clip_best.pt`로 분리 저장한다.
- `label_quality_comparison.json`에 아직 측정 안 된 값을 `0.0`으로 채우지 마라. 빈 문자열이나 `null`로 표시한다.
