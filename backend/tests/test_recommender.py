from __future__ import annotations

import pytest

from app.models.schemas import RootCause, Recommendation
from app.pipeline.extractor import SlideFeatureVector
from app.pipeline.recommender import Recommender


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fv(slide_index: int, *, font_idx: int = 4, word_count: float = 0.2) -> SlideFeatureVector:
    one_hot = [0.0] * 20
    one_hot[font_idx] = 1.0
    return SlideFeatureVector(
        slide_index=slide_index,
        dominant_font_one_hot=one_hot,
        font_size_mean=24.0 / 72,
        font_size_std=0.0,
        font_size_min=24.0 / 72,
        font_size_max=24.0 / 72,
        font_size_median=24.0 / 72,
        bold_ratio=0.0,
        italic_ratio=0.0,
        font_variety_count=0.2,
        line_spacing_normalized=0.5,
        dominant_color_1=(0.0, 0.0, 0.0),
        dominant_color_2=(0.0, 0.0, 0.0),
        dominant_color_3=(0.0, 0.0, 0.0),
        background_color=(1.0, 1.0, 1.0),
        color_variance=0.0,
        saturation_mean=0.0,
        brightness_mean=0.0,
        text_area_ratio=0.5,
        image_area_ratio=0.1,
        whitespace_ratio=0.4,
        alignment_left_ratio=1.0,
        alignment_center_ratio=0.0,
        alignment_right_ratio=0.0,
        margin_top=0.1,
        margin_bottom=0.1,
        margin_left=0.1,
        margin_right=0.1,
        element_count=0.15,
        word_count_normalized=word_count,
        bullet_count_normalized=0.05,
        text_image_ratio=0.8,
        sentence_count_normalized=0.1,
    )


def _make_root_cause(
    label: str = "폰트 불일치",
    feature_group: str = "typography",
    similarity_score: float = 0.5,
    expected_value: str = "Arial",
    actual_value: str = "Calibri",
) -> RootCause:
    return RootCause(
        feature_group=feature_group,  # type: ignore[arg-type]
        label=label,
        expected_value=expected_value,
        actual_value=actual_value,
        similarity_score=similarity_score,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRecommender:
    def setup_method(self):
        self.recommender = Recommender()
        self.all_vectors = [_make_fv(i) for i in range(5)]

    # 1. action 문구가 비어있지 않다
    def test_action_not_empty(self):
        rc = _make_root_cause("폰트 불일치", "typography")
        rec = self.recommender.recommend(rc, 0, self.all_vectors)
        assert rec.action and len(rec.action) > 0

    # 2. impact_score_delta가 0 이상
    def test_impact_score_delta_non_negative(self):
        rc = _make_root_cause("폰트 불일치", "typography", similarity_score=0.7)
        rec = self.recommender.recommend(rc, 0, self.all_vectors)
        assert rec.impact_score_delta >= 0.0

    # 3. similarity_score=1.0이면 delta=0
    def test_delta_zero_when_similarity_is_one(self):
        rc = _make_root_cause(similarity_score=1.0)
        rec = self.recommender.recommend(rc, 0, self.all_vectors)
        assert rec.impact_score_delta == 0.0

    # 4. 폰트 불일치 action 형식
    def test_action_font_mismatch(self):
        rc = _make_root_cause("폰트 불일치", expected_value="Arial", actual_value="Calibri")
        rec = self.recommender.recommend(rc, 0, self.all_vectors)
        assert "Calibri" in rec.action
        assert "Arial" in rec.action
        assert "변경 권장" in rec.action

    # 5. 폰트 크기 불일치 action 형식
    def test_action_font_size_mismatch(self):
        rc = _make_root_cause("폰트 크기 불일치", "typography", expected_value="24pt", actual_value="48pt")
        rec = self.recommender.recommend(rc, 0, self.all_vectors)
        assert "폰트 크기" in rec.action
        assert "조정 권장" in rec.action

    # 6. 색상 불일치 action 형식 — RGB 원시값이 노출되지 않아야 함
    def test_action_color_mismatch(self):
        rc = _make_root_cause("색상 불일치", "color", expected_value="RGB(0, 0, 0)", actual_value="RGB(255,0,0)")
        rec = self.recommender.recommend(rc, 0, self.all_vectors)
        assert "주 색상" in rec.action
        assert "RGB" not in rec.action

    # 7. 레이아웃 불일치 action 형식
    def test_action_layout_mismatch(self):
        rc = _make_root_cause("레이아웃 불일치", "layout", expected_value="텍스트 비율 50%", actual_value="텍스트 비율 80%")
        rec = self.recommender.recommend(rc, 0, self.all_vectors)
        assert "텍스트 영역 비율" in rec.action
        assert "조정 권장" in rec.action

    # 8. 과도한 텍스트 밀도 action 형식
    def test_action_excessive_text_density(self):
        rc = _make_root_cause("과도한 텍스트 밀도", "content")
        rec = self.recommender.recommend(rc, 0, self.all_vectors)
        assert "텍스트 양을 줄이거나" in rec.action

    # 9. 기타 레이블 → "{label} 수정 권장" 형식
    def test_action_fallback(self):
        rc = _make_root_cause("알 수 없는 원인", "typography")
        rec = self.recommender.recommend(rc, 0, self.all_vectors)
        assert "알 수 없는 원인" in rec.action
        assert "수정 권장" in rec.action

    # 10. recommend_all이 dict를 반환하고 모든 슬라이드 포함
    def test_recommend_all_returns_dict(self):
        rc_map = {
            0: [_make_root_cause("폰트 불일치", "typography")],
            2: [_make_root_cause("색상 불일치", "color"), _make_root_cause("레이아웃 불일치", "layout")],
        }
        result = self.recommender.recommend_all(rc_map, self.all_vectors)
        assert 0 in result and 2 in result
        assert len(result[0]) == 1
        assert len(result[2]) == 2
        for recs in result.values():
            for rec in recs:
                assert isinstance(rec, Recommendation)

    # 11. estimate_impact_score 반환값이 0~100 범위
    def test_estimate_impact_score_range(self):
        rc_map = {
            0: [_make_root_cause("폰트 불일치", "typography", similarity_score=0.0)],
            1: [_make_root_cause("색상 불일치", "color", similarity_score=0.0)],
            2: [_make_root_cause("레이아웃 불일치", "layout", similarity_score=0.0)],
            3: [_make_root_cause("과도한 텍스트 밀도", "content", similarity_score=0.0)],
        }
        recs_map = self.recommender.recommend_all(rc_map, self.all_vectors)
        score = self.recommender.estimate_impact_score(self.all_vectors, recs_map)
        assert 0.0 <= score <= 100.0

    # 12. 수정안이 없으면 estimate_impact_score는 현재 점수와 동일
    def test_estimate_impact_score_no_recommendations(self):
        from app.pipeline.scorer import compute_consistency_score
        current = compute_consistency_score(self.all_vectors).total
        score = self.recommender.estimate_impact_score(self.all_vectors, {})
        assert score == pytest.approx(current, abs=1e-6)

    # 13. estimate_impact_score는 100을 초과하지 않는다
    def test_estimate_impact_score_capped_at_100(self):
        rc_map = {
            i: [
                _make_root_cause("폰트 불일치", "typography", similarity_score=0.0),
                _make_root_cause("색상 불일치", "color", similarity_score=0.0),
                _make_root_cause("레이아웃 불일치", "layout", similarity_score=0.0),
            ]
            for i in range(5)
        }
        recs_map = self.recommender.recommend_all(rc_map, self.all_vectors)
        score = self.recommender.estimate_impact_score(self.all_vectors, recs_map)
        assert score <= 100.0
