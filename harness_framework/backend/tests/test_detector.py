import pytest

from app.pipeline.extractor import SlideFeatureVector
from app.pipeline.detector import OutlierDetector, OutlierResult


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


def _normal_vector(slide_index: int) -> SlideFeatureVector:
    """일관된 '정상' 슬라이드 feature vector (모든 값 0.3)."""
    return _make_fv(slide_index, [0.3] * 59)


def _outlier_vector(slide_index: int) -> SlideFeatureVector:
    """극단적으로 다른 '이상' 슬라이드 feature vector (모든 값 1.0)."""
    return _make_fv(slide_index, [1.0] * 59)


# ── 슬라이드 수 부족 ──────────────────────────────────────────────────────────

class TestInsufficientSlides:
    def test_empty_returns_empty(self):
        detector = OutlierDetector()
        assert detector.fit_predict([]) == []

    def test_one_slide_returns_empty(self):
        detector = OutlierDetector()
        fvs = [_normal_vector(0)]
        assert detector.fit_predict(fvs) == []

    def test_two_slides_returns_empty(self):
        detector = OutlierDetector()
        fvs = [_normal_vector(0), _normal_vector(1)]
        assert detector.fit_predict(fvs) == []

    def test_three_slides_returns_results(self):
        detector = OutlierDetector()
        fvs = [_normal_vector(i) for i in range(3)]
        results = detector.fit_predict(fvs)
        assert len(results) == 3


# ── 반환 타입 및 구조 ────────────────────────────────────────────────────────

class TestReturnStructure:
    def test_returns_list_of_outlier_result(self):
        detector = OutlierDetector()
        fvs = [_normal_vector(i) for i in range(5)]
        results = detector.fit_predict(fvs)
        assert all(isinstance(r, OutlierResult) for r in results)

    def test_result_count_equals_input_count(self):
        detector = OutlierDetector()
        fvs = [_normal_vector(i) for i in range(10)]
        results = detector.fit_predict(fvs)
        assert len(results) == 10

    def test_slide_index_preserved(self):
        detector = OutlierDetector()
        fvs = [_normal_vector(i) for i in range(5)]
        results = detector.fit_predict(fvs)
        for r, fv in zip(results, fvs):
            assert r.slide_index == fv.slide_index

    def test_feature_vector_preserved(self):
        detector = OutlierDetector()
        fvs = [_normal_vector(i) for i in range(5)]
        results = detector.fit_predict(fvs)
        for r, fv in zip(results, fvs):
            assert r.feature_vector is fv


# ── anomaly_score 범위 ───────────────────────────────────────────────────────

class TestAnomalyScoreRange:
    def test_all_scores_in_zero_one(self):
        detector = OutlierDetector()
        fvs = [_normal_vector(i) for i in range(10)]
        results = detector.fit_predict(fvs)
        for r in results:
            assert 0.0 <= r.anomaly_score <= 1.0, (
                f"slide {r.slide_index}: anomaly_score={r.anomaly_score}"
            )

    def test_scores_with_outlier_in_zero_one(self):
        detector = OutlierDetector()
        fvs = [_normal_vector(i) for i in range(9)] + [_outlier_vector(9)]
        results = detector.fit_predict(fvs)
        for r in results:
            assert 0.0 <= r.anomaly_score <= 1.0


# ── 이상치 탐지 정확도 ────────────────────────────────────────────────────────

class TestOutlierDetection:
    def test_extreme_outlier_is_detected(self):
        """10개의 유사 벡터 중 극단적으로 다른 1개가 이상치로 탐지되어야 한다."""
        detector = OutlierDetector(contamination=0.2)
        fvs = [_normal_vector(i) for i in range(9)] + [_outlier_vector(9)]
        results = detector.fit_predict(fvs)

        # 극단 슬라이드(index=9)가 이상치여야 한다
        outlier_result = next(r for r in results if r.slide_index == 9)
        assert outlier_result.is_outlier, "극단 슬라이드가 이상치로 탐지되어야 한다"

    def test_extreme_outlier_has_higher_score(self):
        """이상 슬라이드의 anomaly_score가 정상 슬라이드보다 높아야 한다."""
        detector = OutlierDetector(contamination=0.2)
        fvs = [_normal_vector(i) for i in range(9)] + [_outlier_vector(9)]
        results = detector.fit_predict(fvs)

        outlier_score = next(r.anomaly_score for r in results if r.slide_index == 9)
        normal_scores = [r.anomaly_score for r in results if r.slide_index != 9]
        avg_normal = sum(normal_scores) / len(normal_scores)

        assert outlier_score > avg_normal, (
            f"이상 슬라이드 score({outlier_score:.3f})가 "
            f"정상 평균({avg_normal:.3f})보다 높아야 한다"
        )

    def test_is_outlier_is_bool(self):
        detector = OutlierDetector()
        fvs = [_normal_vector(i) for i in range(5)]
        results = detector.fit_predict(fvs)
        for r in results:
            assert isinstance(r.is_outlier, bool)

    def test_contamination_affects_outlier_count(self):
        """contamination=0.2이면 10장 중 이상치 수가 contamination 비율 이하여야 한다.
        9개의 정상 슬라이드 + 1개의 극단 슬라이드 → 이상치 ≤ 2장.
        """
        detector = OutlierDetector(contamination=0.2)
        fvs = [_normal_vector(i) for i in range(9)] + [_outlier_vector(9)]
        results = detector.fit_predict(fvs)
        outlier_count = sum(1 for r in results if r.is_outlier)
        # contamination=0.2 → 최대 ceil(10 * 0.2) = 2장
        assert 1 <= outlier_count <= 2, (
            f"이상치 수({outlier_count})는 1~2 범위여야 한다 (contamination=0.2)"
        )
