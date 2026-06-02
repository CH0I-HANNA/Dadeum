import numpy as np
import pytest

from app.pipeline.extractor import SlideFeatureVector
from app.pipeline.scorer import compute_consistency_score


def _make_fv(slide_index: int, values: list[float]) -> SlideFeatureVector:
    """59차원 값 목록으로 SlideFeatureVector를 생성한다."""
    assert len(values) == 59, f"Expected 59 values, got {len(values)}"
    return SlideFeatureVector(
        slide_index=slide_index,
        dominant_font_one_hot=values[0:20],
        font_size_mean=values[20],
        font_size_std=values[21],
        font_size_min=values[22],
        font_size_max=values[23],
        font_size_median=values[24],
        bold_ratio=values[25],
        italic_ratio=values[26],
        font_variety_count=values[27],
        line_spacing_normalized=values[28],
        dominant_color_1=(values[29], values[30], values[31]),
        dominant_color_2=(values[32], values[33], values[34]),
        dominant_color_3=(values[35], values[36], values[37]),
        background_color=(values[38], values[39], values[40]),
        color_variance=values[41],
        saturation_mean=values[42],
        brightness_mean=values[43],
        text_area_ratio=values[44],
        image_area_ratio=values[45],
        whitespace_ratio=values[46],
        alignment_left_ratio=values[47],
        alignment_center_ratio=values[48],
        alignment_right_ratio=values[49],
        margin_top=values[50],
        margin_bottom=values[51],
        margin_left=values[52],
        margin_right=values[53],
        element_count=values[54],
        word_count_normalized=values[55],
        bullet_count_normalized=values[56],
        text_image_ratio=values[57],
        sentence_count_normalized=values[58],
    )


def _uniform_fv(slide_index: int, value: float = 0.5) -> SlideFeatureVector:
    """모든 차원이 동일한 값인 feature vector를 반환한다."""
    return _make_fv(slide_index, [value] * 59)


class TestIdenticalVectors:
    def test_identical_5_slides_total_near_100(self):
        fvs = [_uniform_fv(i) for i in range(5)]
        result = compute_consistency_score(fvs)
        assert result.total >= 95.0

    def test_identical_10_slides_total_near_100(self):
        fvs = [_uniform_fv(i, 0.3) for i in range(10)]
        result = compute_consistency_score(fvs)
        assert result.total >= 95.0

    def test_identical_all_zeros_total_near_100(self):
        fvs = [_uniform_fv(i, 0.0) for i in range(5)]
        result = compute_consistency_score(fvs)
        assert result.total >= 95.0


class TestDiverseVectors:
    def test_skewed_extremes_total_low(self):
        # 9장은 모두 0.0, 1장은 모두 0.9 → mean≈0.09, std≈0.27, CV≈3 → cohesion≈0.25
        fvs = [_uniform_fv(i, 0.0) for i in range(9)]
        fvs.append(_uniform_fv(9, 0.9))
        result = compute_consistency_score(fvs)
        assert result.total <= 50.0

    def test_bimodal_vectors_total_low(self):
        # 절반은 0.0, 절반은 0.9 → 모든 차원에서 분산 극대화
        fvs = [_uniform_fv(i, 0.0 if i < 5 else 0.9) for i in range(10)]
        result = compute_consistency_score(fvs)
        # mean=0.45, std=0.45 → CV=1 → cohesion=0.5 → total=50; ε로 인한 미세 오차 허용
        assert result.total <= 51.0


class TestSingleSlide:
    def test_single_slide_total_is_100(self):
        fv = _uniform_fv(0, 0.5)
        result = compute_consistency_score([fv])
        assert result.total == 100.0

    def test_single_slide_sub_scores_are_100(self):
        fv = _uniform_fv(0, 0.7)
        result = compute_consistency_score([fv])
        assert result.sub_scores.typography == 100.0
        assert result.sub_scores.color == 100.0
        assert result.sub_scores.layout == 100.0
        assert result.sub_scores.content == 100.0


class TestScoreRange:
    def test_all_scores_within_0_to_100(self):
        rng = np.random.default_rng(7)
        fvs = []
        for i in range(15):
            vals = rng.uniform(0.0, 1.0, size=59).tolist()
            fvs.append(_make_fv(i, vals))
        result = compute_consistency_score(fvs)

        assert 0.0 <= result.total <= 100.0
        assert 0.0 <= result.sub_scores.typography <= 100.0
        assert 0.0 <= result.sub_scores.color <= 100.0
        assert 0.0 <= result.sub_scores.layout <= 100.0
        assert 0.0 <= result.sub_scores.content <= 100.0

    def test_identical_slides_all_sub_scores_near_100(self):
        fvs = [_uniform_fv(i, 0.4) for i in range(8)]
        result = compute_consistency_score(fvs)
        assert result.sub_scores.typography >= 95.0
        assert result.sub_scores.color >= 95.0
        assert result.sub_scores.layout >= 95.0
        assert result.sub_scores.content >= 95.0

    def test_total_is_weighted_sum_of_sub_scores(self):
        rng = np.random.default_rng(99)
        fvs = [_make_fv(i, rng.uniform(0.1, 0.9, size=59).tolist()) for i in range(6)]
        result = compute_consistency_score(fvs)

        expected_total = (
            result.sub_scores.typography * 0.30
            + result.sub_scores.color * 0.30
            + result.sub_scores.layout * 0.25
            + result.sub_scores.content * 0.15
        )
        assert abs(result.total - expected_total) < 1e-6
