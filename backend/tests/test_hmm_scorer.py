import json
import pickle
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.pipeline.hmm_scorer import HMMScorer


class _PicklableHMM:
    """pickle 가능한 HMM 스텁 (load() 테스트 전용)."""

    def score(self, seq):
        return -1.0 * len(seq)


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _make_mock_model(score_per_step: float = -1.0) -> MagicMock:
    """HMM 모델 mock: model.score(seq) → score_per_step * len(seq)."""
    model = MagicMock()
    model.score.side_effect = lambda seq: score_per_step * len(seq)
    return model


def _make_thresholds(mean: float, std: float) -> dict:
    return {"mean": mean, "std": std, "threshold_primary": mean - 2 * std}


# ── score_sequence 기본 동작 ──────────────────────────────────────────────────

class TestScoreSequenceEdgeCases:
    def test_empty_returns_half(self):
        scorer = HMMScorer(_make_mock_model(), _make_thresholds(-1.0, 0.5))
        assert scorer.score_sequence([]) == 0.5

    def test_length_1_returns_half(self):
        scorer = HMMScorer(_make_mock_model(), _make_thresholds(-1.0, 0.5))
        assert scorer.score_sequence([0]) == 0.5

    def test_length_2_returns_half(self):
        scorer = HMMScorer(_make_mock_model(), _make_thresholds(-1.0, 0.5))
        assert scorer.score_sequence([0, 1]) == 0.5

    def test_length_3_returns_half(self):
        scorer = HMMScorer(_make_mock_model(), _make_thresholds(-1.0, 0.5))
        assert scorer.score_sequence([0, 1, 2]) == 0.5

    def test_length_4_returns_half(self):
        scorer = HMMScorer(_make_mock_model(), _make_thresholds(-1.0, 0.5))
        assert scorer.score_sequence([0, 1, 2, 3]) == 0.5


# ── score_sequence 범위 ───────────────────────────────────────────────────────

class TestScoreSequenceRange:
    def test_score_always_in_zero_one(self):
        """다양한 시퀀스에 대해 반환값이 항상 [0, 1] 범위 내여야 한다."""
        model = _make_mock_model(score_per_step=-1.0)
        scorer = HMMScorer(model, _make_thresholds(-1.0, 0.5))
        for length in range(5, 20):
            seq = list(range(length))
            score = scorer.score_sequence(seq)
            assert 0.0 <= score <= 1.0, f"length={length}, score={score}"

    def test_score_clipped_at_one(self):
        """z >= 3이면 score = 1.0 (clip)."""
        # ll/len = -10.0, mean = -1.0, std = 1.0 → z = (-1 - (-10)) / (1 + 1e-8) = 9 → clip → 1.0
        model = _make_mock_model(score_per_step=-10.0)
        scorer = HMMScorer(model, _make_thresholds(-1.0, 1.0))
        score = scorer.score_sequence([0, 1, 2, 3, 4])
        assert score == 1.0

    def test_score_clipped_at_zero(self):
        """ll이 mean보다 높으면 z < 0 → score = 0.0 (clip)."""
        # ll/len = 0.0, mean = -1.0, std = 1.0 → z = (-1 - 0) / (1 + 1e-8) < 0 → clip → 0.0
        model = _make_mock_model(score_per_step=0.0)
        scorer = HMMScorer(model, _make_thresholds(-1.0, 1.0))
        score = scorer.score_sequence([0, 1, 2, 3, 4])
        assert score == 0.0


# ── score_sequence 정상/이상 구분 ────────────────────────────────────────────

class TestScoreSequenceNormalVsAbnormal:
    def test_ll_equal_to_mean_gives_zero_score(self):
        """ll이 mean과 같으면 z = 0 → score = 0.0 (정상)."""
        mean = -2.0
        # score_per_step = mean이면 ll/len = mean
        model = _make_mock_model(score_per_step=mean)
        scorer = HMMScorer(model, _make_thresholds(mean, 0.5))
        score = scorer.score_sequence([0, 1, 2, 3, 4])
        assert score == pytest.approx(0.0, abs=1e-6)

    def test_high_anomaly_z_gives_max_score(self):
        """z >= 3이면 score = 1.0."""
        # ll/len = -10.0, mean = -1.0, std = 1.0 → z = 9 → clip → 1.0
        model = _make_mock_model(score_per_step=-10.0)
        scorer = HMMScorer(model, _make_thresholds(-1.0, 1.0))
        score = scorer.score_sequence([0, 1, 2, 3, 4])
        assert score == 1.0

    def test_abnormal_score_higher_than_normal(self):
        """이상 시퀀스(낮은 ll) score > 정상 시퀀스(높은 ll) score."""
        mean = -2.0
        std = 0.5
        thresholds = _make_thresholds(mean, std)

        # 정상: ll/len ≈ mean
        normal_model = _make_mock_model(score_per_step=mean)
        normal_scorer = HMMScorer(normal_model, thresholds)
        normal_score = normal_scorer.score_sequence([0, 1, 2, 3, 4])

        # 이상: ll/len << mean
        abnormal_model = _make_mock_model(score_per_step=-10.0)
        abnormal_scorer = HMMScorer(abnormal_model, thresholds)
        abnormal_score = abnormal_scorer.score_sequence([0, 1, 2, 3, 4])

        assert abnormal_score > normal_score


# ── std=0 엣지케이스 ──────────────────────────────────────────────────────────

class TestScoreSequenceStdZero:
    def test_std_zero_no_division_error(self):
        """std=0일 때 ZeroDivisionError 없이 동작해야 한다."""
        model = _make_mock_model(score_per_step=-5.0)
        scorer = HMMScorer(model, _make_thresholds(-1.0, 0.0))
        score = scorer.score_sequence([0, 1, 2, 3, 4])
        assert 0.0 <= score <= 1.0


# ── load() ────────────────────────────────────────────────────────────────────

class TestLoad:
    def test_load_no_files_returns_none(self, tmp_path):
        with patch("app.pipeline.hmm_scorer.MODELS_DIR", tmp_path):
            result = HMMScorer.load()
        assert result is None

    def test_load_pkl_only_no_json_returns_none(self, tmp_path):
        # pkl만 존재하고 json 없음
        pkl_path = tmp_path / "hmm_model.pkl"
        pkl_path.write_bytes(b"fake")
        with patch("app.pipeline.hmm_scorer.MODELS_DIR", tmp_path):
            result = HMMScorer.load()
        assert result is None

    def test_load_json_only_no_pkl_returns_none(self, tmp_path):
        # json만 존재하고 pkl 없음
        json_path = tmp_path / "hmm_thresholds.json"
        json_path.write_text(json.dumps({"mean": -1.0, "std": 0.5}))
        with patch("app.pipeline.hmm_scorer.MODELS_DIR", tmp_path):
            result = HMMScorer.load()
        assert result is None

    def test_load_corrupted_pkl_returns_none(self, tmp_path):
        # pkl 파일이 손상됨
        pkl_path = tmp_path / "hmm_model.pkl"
        pkl_path.write_bytes(b"not a valid pickle")
        json_path = tmp_path / "hmm_thresholds.json"
        json_path.write_text(json.dumps({"mean": -1.0, "std": 0.5}))
        with patch("app.pipeline.hmm_scorer.MODELS_DIR", tmp_path):
            result = HMMScorer.load()
        assert result is None

    def test_load_valid_files_returns_hmm_scorer(self, tmp_path):
        # 유효한 pkl + json
        pkl_path = tmp_path / "hmm_model.pkl"
        pkl_path.write_bytes(pickle.dumps(_PicklableHMM()))
        json_path = tmp_path / "hmm_thresholds.json"
        json_path.write_text(json.dumps({"mean": -1.0, "std": 0.5, "threshold_primary": -2.0}))
        with patch("app.pipeline.hmm_scorer.MODELS_DIR", tmp_path):
            result = HMMScorer.load()
        assert isinstance(result, HMMScorer)
