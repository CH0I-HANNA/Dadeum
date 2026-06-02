from __future__ import annotations

import pytest

from app.pipeline.extractor import SlideFeatureVector
from app.pipeline.detector import OutlierResult
from app.pipeline.explainer import Explainer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fv(
    slide_index: int,
    *,
    font_idx: int = 4,          # 4=Arial (KNOWN_FONTS)
    font_size_mean: float = 24.0 / 72,
    dominant_color_1: tuple[float, float, float] = (0.0, 0.0, 0.0),
    text_area_ratio: float = 0.5,
    word_count_normalized: float = 0.2,
) -> SlideFeatureVector:
    one_hot = [0.0] * 20
    one_hot[font_idx] = 1.0
    return SlideFeatureVector(
        slide_index=slide_index,
        dominant_font_one_hot=one_hot,
        font_size_mean=font_size_mean,
        font_size_std=0.0,
        font_size_min=font_size_mean,
        font_size_max=font_size_mean,
        font_size_median=font_size_mean,
        bold_ratio=0.0,
        italic_ratio=0.0,
        font_variety_count=0.2,
        line_spacing_normalized=0.5,
        dominant_color_1=dominant_color_1,
        dominant_color_2=(0.0, 0.0, 0.0),
        dominant_color_3=(0.0, 0.0, 0.0),
        background_color=(1.0, 1.0, 1.0),
        color_variance=0.0,
        saturation_mean=0.0,
        brightness_mean=0.0,
        text_area_ratio=text_area_ratio,
        image_area_ratio=0.1,
        whitespace_ratio=max(0.0, 1.0 - text_area_ratio - 0.1),
        alignment_left_ratio=1.0,
        alignment_center_ratio=0.0,
        alignment_right_ratio=0.0,
        margin_top=0.1,
        margin_bottom=0.1,
        margin_left=0.1,
        margin_right=0.1,
        element_count=0.15,
        word_count_normalized=word_count_normalized,
        bullet_count_normalized=0.05,
        text_image_ratio=0.8,
        sentence_count_normalized=0.1,
    )


def _make_outlier(fv: SlideFeatureVector, is_outlier: bool = True) -> OutlierResult:
    return OutlierResult(
        slide_index=fv.slide_index,
        is_outlier=is_outlier,
        anomaly_score=0.8 if is_outlier else 0.1,
        feature_vector=fv,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestExplainer:
    def setup_method(self):
        self.explainer = Explainer()

    # 1. is_outlier=False → 빈 리스트
    def test_non_outlier_returns_empty(self):
        fv = _make_fv(0)
        outlier = _make_outlier(fv, is_outlier=False)
        all_vectors = [_make_fv(i) for i in range(5)]
        result = self.explainer.explain(outlier, all_vectors)
        assert result == []

    # 2. RootCause 최대 3개
    def test_max_three_root_causes(self):
        all_vectors = [_make_fv(i) for i in range(5)]
        fv_outlier = _make_fv(5, font_idx=6, font_size_mean=48.0 / 72)
        outlier = _make_outlier(fv_outlier)
        result = self.explainer.explain(outlier, all_vectors)
        assert len(result) <= 3

    # 3. similarity_score가 0~1 범위
    def test_similarity_score_range(self):
        all_vectors = [_make_fv(i) for i in range(5)]
        fv_outlier = _make_fv(5, font_idx=6)
        outlier = _make_outlier(fv_outlier)
        result = self.explainer.explain(outlier, all_vectors)
        for rc in result:
            assert 0.0 <= rc.similarity_score <= 1.0, (
                f"similarity_score out of range: {rc.similarity_score}"
            )

    # 4. 폰트만 다른 슬라이드 → typography가 첫 번째 원인
    def test_font_mismatch_typography_first(self):
        # 4개 슬라이드는 Arial(index=4), 1개 슬라이드는 Times New Roman(index=6)
        all_vectors = [_make_fv(i, font_idx=4) for i in range(4)]
        fv_outlier = _make_fv(4, font_idx=6)
        all_vectors_with_outlier = all_vectors + [fv_outlier]
        outlier = _make_outlier(fv_outlier)

        result = self.explainer.explain(outlier, all_vectors_with_outlier)
        assert len(result) >= 1
        assert result[0].feature_group == "typography"

    # 5. 폰트 불일치 시 label이 "폰트 불일치"이고 expected/actual이 폰트명
    def test_font_mismatch_label(self):
        all_vectors = [_make_fv(i, font_idx=4) for i in range(4)]  # Arial
        fv_outlier = _make_fv(4, font_idx=6)  # Times New Roman
        all_vectors_with_outlier = all_vectors + [fv_outlier]
        outlier = _make_outlier(fv_outlier)

        result = self.explainer.explain(outlier, all_vectors_with_outlier)
        typo_cause = next(r for r in result if r.feature_group == "typography")
        assert typo_cause.label == "폰트 불일치"
        assert typo_cause.expected_value == "Arial"
        assert typo_cause.actual_value == "Times New Roman"

    # 6. 폰트 크기만 다른 경우 → "폰트 크기 불일치" 레이블
    def test_font_size_mismatch_label(self):
        # 동일한 폰트(Arial), 다른 슬라이드는 24pt, 이상치 슬라이드는 72pt
        all_vectors = [_make_fv(i, font_idx=4, font_size_mean=24.0 / 72) for i in range(5)]
        fv_outlier = _make_fv(5, font_idx=4, font_size_mean=72.0 / 72)
        all_vectors_with_outlier = all_vectors + [fv_outlier]
        outlier = _make_outlier(fv_outlier)

        result = self.explainer.explain(outlier, all_vectors_with_outlier)
        typo_cause = next(r for r in result if r.feature_group == "typography")
        assert typo_cause.label == "폰트 크기 불일치"
        assert "pt" in typo_cause.expected_value
        assert "pt" in typo_cause.actual_value

    # 7. 과도한 텍스트 밀도 → "과도한 텍스트 밀도" 레이블
    def test_excessive_text_density_label(self):
        all_vectors = [_make_fv(i, word_count_normalized=0.2) for i in range(5)]
        fv_outlier = _make_fv(5, word_count_normalized=0.9)  # 0.9 >= 2 * 0.2
        all_vectors_with_outlier = all_vectors + [fv_outlier]
        outlier = _make_outlier(fv_outlier)

        result = self.explainer.explain(outlier, all_vectors_with_outlier)
        content_cause = next(r for r in result if r.feature_group == "content")
        assert content_cause.label == "과도한 텍스트 밀도"

    # 8. explain_all이 dict[int, list[RootCause]]를 반환
    def test_explain_all_returns_dict(self):
        all_vectors = [_make_fv(i) for i in range(5)]
        fv_outlier = _make_fv(5, font_idx=6)
        all_vectors_with_outlier = all_vectors + [fv_outlier]
        outlier = _make_outlier(fv_outlier)

        result = self.explainer.explain_all([outlier], all_vectors_with_outlier)
        assert isinstance(result, dict)
        assert 5 in result
        assert isinstance(result[5], list)

    # 9. 슬라이드가 1장만 있을 때도 크래시 없이 동작
    def test_single_slide(self):
        fv = _make_fv(0)
        outlier = _make_outlier(fv)
        result = self.explainer.explain(outlier, [fv])
        assert isinstance(result, list)
        assert len(result) <= 3

    # 10. similarity_score가 낮은 순으로 정렬됨
    def test_sorted_by_similarity_score(self):
        all_vectors = [_make_fv(i) for i in range(5)]
        fv_outlier = _make_fv(5, font_idx=6)
        outlier = _make_outlier(fv_outlier)
        result = self.explainer.explain(outlier, all_vectors + [fv_outlier])
        scores = [r.similarity_score for r in result]
        assert scores == sorted(scores)

    # 11. 동일한 색상값을 가진 아웃라이어 슬라이드에서 color RootCause 제외
    def test_same_color_no_color_root_cause(self):
        # 모든 슬라이드 dominant_color_1이 (0,0,0)으로 동일 → color similarity = 1.0 → 필터됨
        all_vectors = [_make_fv(i) for i in range(5)]
        fv_outlier = _make_fv(5, font_idx=6)  # 폰트만 다름, 색상은 동일
        outlier = _make_outlier(fv_outlier)
        result = self.explainer.explain(outlier, all_vectors + [fv_outlier])
        color_causes = [r for r in result if r.feature_group == "color"]
        assert len(color_causes) == 0

    # 12. 모든 feature가 베이스라인과 동일한 슬라이드는 RootCause가 0개
    def test_identical_features_no_root_cause(self):
        all_vectors = [_make_fv(i) for i in range(5)]
        fv_outlier = _make_fv(5)  # 기본값과 동일한 feature
        outlier = _make_outlier(fv_outlier)
        result = self.explainer.explain(outlier, all_vectors + [fv_outlier])
        assert len(result) == 0
