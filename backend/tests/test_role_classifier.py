import sys
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from app.pipeline.role_classifier import RoleClassifier


def _make_rgb_image(width: int = 224, height: int = 224, color=(128, 128, 128)) -> Image.Image:
    return Image.new("RGB", (width, height), color)


def _make_mock_model(predicted_class: int = 2) -> MagicMock:
    """항상 predicted_class를 반환하는 mock 모델."""
    import torch

    def fake_forward(tensor):
        batch_size = tensor.shape[0]
        logits = torch.zeros(batch_size, 5)
        logits[:, predicted_class] = 1.0
        return logits

    model = MagicMock()
    model.side_effect = fake_forward
    return model


def _make_classifier(predicted_class: int = 2) -> RoleClassifier:
    import torch
    return RoleClassifier(_make_mock_model(predicted_class), torch.device("cpu"))


# ── load() ────────────────────────────────────────────────────────────────────

class TestLoad:
    def test_load_no_file_returns_none(self, tmp_path):
        with patch("app.pipeline.role_classifier.MODELS_DIR", tmp_path):
            result = RoleClassifier.load()
        assert result is None

    def test_load_corrupted_file_returns_none(self, tmp_path):
        pt_path = tmp_path / "role_classifier_clip_best.pt"
        pt_path.write_bytes(b"not a valid pytorch checkpoint")
        with patch("app.pipeline.role_classifier.MODELS_DIR", tmp_path):
            result = RoleClassifier.load()
        assert result is None

    def test_load_import_error_returns_none(self, tmp_path):
        """torch/timm 미설치 시 None 반환 (예외 전파 금지)."""
        pt_path = tmp_path / "role_classifier_clip_best.pt"
        pt_path.write_bytes(b"fake checkpoint")
        with patch("app.pipeline.role_classifier.MODELS_DIR", tmp_path):
            with patch.dict(sys.modules, {"torch": None, "timm": None}):
                result = RoleClassifier.load()
        assert result is None

    def test_load_returns_none_or_role_classifier(self, tmp_path):
        """torch/timm 설치 여부에 관계없이 None 또는 RoleClassifier 반환."""
        with patch("app.pipeline.role_classifier.MODELS_DIR", tmp_path):
            result = RoleClassifier.load()
        assert result is None or isinstance(result, RoleClassifier)


# ── predict() ─────────────────────────────────────────────────────────────────

class TestPredict:
    def test_predict_empty_returns_empty(self):
        classifier = _make_classifier()
        assert classifier.predict([]) == []

    def test_predict_length_matches_input(self):
        classifier = _make_classifier()
        images = [_make_rgb_image() for _ in range(5)]
        result = classifier.predict(images)
        assert len(result) == 5

    def test_predict_values_in_zero_to_four(self):
        """각 예측값이 0 이상 4 이하의 정수여야 한다."""
        classifier = _make_classifier(predicted_class=3)
        images = [_make_rgb_image() for _ in range(4)]
        result = classifier.predict(images)
        for val in result:
            assert isinstance(val, int)
            assert 0 <= val <= 4

    def test_predict_single_image(self):
        classifier = _make_classifier(predicted_class=0)
        result = classifier.predict([_make_rgb_image()])
        assert len(result) == 1
        assert isinstance(result[0], int)
        assert 0 <= result[0] <= 4

    def test_predict_returns_correct_class(self):
        """mock 모델이 class 2를 예측하면 결과도 모두 2여야 한다."""
        classifier = _make_classifier(predicted_class=2)
        images = [_make_rgb_image() for _ in range(3)]
        result = classifier.predict(images)
        assert all(v == 2 for v in result)

    def test_predict_pil_image_list(self):
        """다양한 크기의 PIL Image 리스트를 입력받아 정상 동작한다."""
        classifier = _make_classifier()
        images = [
            Image.new("RGB", (800, 600), (255, 0, 0)),
            Image.new("RGB", (1920, 1080), (0, 255, 0)),
            Image.new("RGB", (400, 300), (0, 0, 255)),
        ]
        result = classifier.predict(images)
        assert len(result) == 3
        for val in result:
            assert 0 <= val <= 4

    def test_predict_rgba_image_converts_to_rgb(self):
        """RGBA 이미지도 RGB로 변환하여 정상 처리된다."""
        classifier = _make_classifier(predicted_class=1)
        images = [Image.new("RGBA", (224, 224), (0, 128, 255, 200))]
        result = classifier.predict(images)
        assert len(result) == 1
        assert 0 <= result[0] <= 4

    def test_predict_batch_larger_than_32(self):
        """배치 크기 32를 초과하는 입력도 정상 처리된다."""
        classifier = _make_classifier(predicted_class=4)
        images = [_make_rgb_image() for _ in range(40)]
        result = classifier.predict(images)
        assert len(result) == 40
        assert all(isinstance(v, int) and 0 <= v <= 4 for v in result)
