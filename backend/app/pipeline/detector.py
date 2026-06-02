from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import IsolationForest

from app.pipeline.extractor import SlideFeatureVector

_ε = 1e-8


@dataclass
class OutlierResult:
    slide_index: int
    is_outlier: bool
    anomaly_score: float  # 0~1, 높을수록 이상
    feature_vector: SlideFeatureVector


def _dynamic_contamination(n: int) -> float:
    if n <= 5:
        return 0.15
    if n <= 15:
        return 0.20
    return 0.25


class OutlierDetector:
    def __init__(self, contamination: float | None = None) -> None:
        self._fixed_contamination = contamination

    def fit_predict(
        self,
        feature_vectors: list[SlideFeatureVector],
    ) -> list[OutlierResult]:
        """Isolation Forest를 fit하고 각 슬라이드의 이상 여부와 anomaly score를 반환한다.
        슬라이드가 3장 미만이면 빈 리스트를 반환한다.
        """
        if len(feature_vectors) < 3:
            return []

        contamination = (
            self._fixed_contamination
            if self._fixed_contamination is not None
            else _dynamic_contamination(len(feature_vectors))
        )

        X = np.array([fv.to_numpy() for fv in feature_vectors])

        model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
        )
        labels = model.fit_predict(X)  # 1=정상, -1=이상치
        raw_scores = model.decision_function(X)  # 음수일수록 이상치

        # decision_function 값을 0~1로 정규화 후 반전 (높을수록 이상치)
        score_min = raw_scores.min()
        score_max = raw_scores.max()
        normalized = (raw_scores - score_min) / (score_max - score_min + _ε)
        anomaly_scores = 1.0 - normalized

        results: list[OutlierResult] = []
        for i, fv in enumerate(feature_vectors):
            results.append(
                OutlierResult(
                    slide_index=fv.slide_index,
                    is_outlier=bool(labels[i] == -1),
                    anomaly_score=float(anomaly_scores[i]),
                    feature_vector=fv,
                )
            )
        return results
