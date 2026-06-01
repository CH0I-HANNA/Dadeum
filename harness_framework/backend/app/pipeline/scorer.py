from __future__ import annotations

import numpy as np

from app.models.schemas import ConsistencyScore, SubScore
from app.pipeline.extractor import SlideFeatureVector

_ε = 1e-8

_TYPOGRAPHY_SLICE = slice(0, 29)
_COLOR_SLICE = slice(29, 44)
_LAYOUT_SLICE = slice(44, 55)
_CONTENT_SLICE = slice(55, 59)

_WEIGHTS = {
    "typography": 0.30,
    "color": 0.30,
    "layout": 0.25,
    "content": 0.15,
}


def _group_cohesion(matrix: np.ndarray, group_slice: slice) -> float:
    """차원별 CV를 계산하고 cohesion 평균을 반환한다."""
    group = matrix[:, group_slice]          # (N, D)
    stds = np.std(group, axis=0)            # (D,)
    means = np.mean(group, axis=0)          # (D,)
    cvs = stds / (means + _ε)              # (D,)
    return float(np.mean(1.0 / (1.0 + cvs)))


def compute_consistency_score(
    feature_vectors: list[SlideFeatureVector],
) -> ConsistencyScore:
    """
    슬라이드 전체의 feature vector를 받아 일관성 점수를 반환한다.
    슬라이드가 1장이면 total=100, sub_scores 모두 100을 반환한다.
    """
    if len(feature_vectors) <= 1:
        return ConsistencyScore(
            total=100.0,
            sub_scores=SubScore(typography=100.0, color=100.0, layout=100.0, content=100.0),
        )

    matrix = np.stack([fv.to_numpy() for fv in feature_vectors], axis=0)  # (N, 59)

    typo = _group_cohesion(matrix, _TYPOGRAPHY_SLICE)
    color = _group_cohesion(matrix, _COLOR_SLICE)
    layout = _group_cohesion(matrix, _LAYOUT_SLICE)
    content = _group_cohesion(matrix, _CONTENT_SLICE)

    total = 100.0 * (
        typo * _WEIGHTS["typography"]
        + color * _WEIGHTS["color"]
        + layout * _WEIGHTS["layout"]
        + content * _WEIGHTS["content"]
    )

    return ConsistencyScore(
        total=total,
        sub_scores=SubScore(
            typography=typo * 100.0,
            color=color * 100.0,
            layout=layout * 100.0,
            content=content * 100.0,
        ),
    )
