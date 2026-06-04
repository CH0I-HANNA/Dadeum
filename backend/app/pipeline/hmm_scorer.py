from __future__ import annotations

import json
import pickle
from typing import Optional

import numpy as np

from app.core.config import MODELS_DIR


class HMMScorer:
    def __init__(self, model, thresholds: dict) -> None:
        self._model = model
        self._mean: float = thresholds["mean"]
        self._std: float = thresholds["std"]

    def score_sequence(self, role_sequence: list[int]) -> float:
        """역할 시퀀스 → 이상 점수 (0~1, 높을수록 이상).
        시퀀스 길이 < 5이면 0.5 반환.
        """
        if len(role_sequence) < 5:
            return 0.5

        seq = np.array(role_sequence).reshape(-1, 1)
        ll = self._model.score(seq) / len(role_sequence)
        z = (self._mean - ll) / (self._std + 1e-8)
        return float(np.clip(z / 3.0, 0.0, 1.0))

    @classmethod
    def load(cls) -> Optional["HMMScorer"]:
        """MODELS_DIR/hmm_model.pkl + hmm_thresholds.json 로드.
        파일 미존재 또는 로드 실패 시 None 반환.
        """
        pkl_path = MODELS_DIR / "hmm_model.pkl"
        json_path = MODELS_DIR / "hmm_thresholds.json"

        if not pkl_path.exists() or not json_path.exists():
            return None

        try:
            with open(pkl_path, "rb") as f:
                model = pickle.load(f)
            with open(json_path, "r") as f:
                thresholds = json.load(f)
            return cls(model, thresholds)
        except Exception:
            return None
