from __future__ import annotations

import numpy as np

from app.pipeline.extractor import SlideFeatureExtractor, SlideFeatureVector
from app.pipeline.detector import OutlierResult
from app.models.schemas import RootCause

_ε = 1e-8

_TYPO_SLICE = slice(0, 29)
_COLOR_SLICE = slice(29, 44)
_LAYOUT_SLICE = slice(44, 55)
_CONTENT_SLICE = slice(55, 59)

_KNOWN_FONTS = SlideFeatureExtractor.KNOWN_FONTS  # 길이 19


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a < _ε and norm_b < _ε:
        return 1.0  # 둘 다 무신호 → 동일
    if norm_a < _ε or norm_b < _ε:
        return 0.0  # 한쪽만 무신호 → 완전 불일치
    raw = float(np.dot(a, b) / (norm_a * norm_b))
    return max(0.0, min(1.0, raw))


def _font_name(idx: int) -> str:
    if idx < len(_KNOWN_FONTS):
        return _KNOWN_FONTS[idx]
    return "Other"


class Explainer:
    def explain(
        self,
        outlier: OutlierResult,
        all_vectors: list[SlideFeatureVector],
    ) -> list[RootCause]:
        """이상 슬라이드 1개에 대해 원인 RootCause 목록을 반환한다.
        최대 3개까지 반환하며, similarity_score가 낮은 순으로 정렬한다.
        is_outlier == False이면 빈 리스트를 반환한다.
        """
        if not outlier.is_outlier:
            return []

        all_np = np.array([fv.to_numpy() for fv in all_vectors])  # (N, 59)
        baseline = np.median(all_np, axis=0)  # (59,)
        outlier_np = outlier.feature_vector.to_numpy()  # (59,)

        groups: list[tuple[str, slice]] = [
            ("typography", _TYPO_SLICE),
            ("color", _COLOR_SLICE),
            ("layout", _LAYOUT_SLICE),
            ("content", _CONTENT_SLICE),
        ]

        causes: list[RootCause] = []
        for group_name, slc in groups:
            sim = _cosine_similarity(outlier_np[slc], baseline[slc])
            label, expected, actual = _make_label(
                group_name, outlier.feature_vector, baseline
            )
            causes.append(
                RootCause(
                    feature_group=group_name,  # type: ignore[arg-type]
                    label=label,
                    expected_value=expected,
                    actual_value=actual,
                    similarity_score=sim,
                )
            )

        causes.sort(key=lambda c: c.similarity_score)
        filtered = [c for c in causes if c.similarity_score < 0.95]
        # 이상 슬라이드는 원인이 최소 1개 있어야 하므로 필터 결과가 비면 가장 낮은 것 유지
        if not filtered:
            filtered = causes[:1]
        return filtered[:5]

    def explain_all(
        self,
        outliers: list[OutlierResult],
        all_vectors: list[SlideFeatureVector],
    ) -> dict[int, list[RootCause]]:
        """slide_index → RootCause 목록 매핑을 반환한다."""
        return {o.slide_index: self.explain(o, all_vectors) for o in outliers}


def _make_label(
    group: str,
    fv: SlideFeatureVector,
    baseline: np.ndarray,
) -> tuple[str, str, str]:
    if group == "typography":
        return _typography_label(fv, baseline)
    if group == "color":
        return _color_label(fv, baseline)
    if group == "layout":
        return _layout_label(fv, baseline)
    return _content_label(fv, baseline)


def _typography_label(fv: SlideFeatureVector, baseline: np.ndarray) -> tuple[str, str, str]:
    outlier_one_hot = np.array(fv.dominant_font_one_hot)  # (20,)
    baseline_one_hot = baseline[0:20]

    font_diff = float(np.sum(np.abs(outlier_one_hot - baseline_one_hot)))
    size_diff = abs(fv.font_size_mean - float(baseline[20]))

    if font_diff >= size_diff:
        expected_font = _font_name(int(np.argmax(baseline_one_hot)))
        actual_font = _font_name(int(np.argmax(outlier_one_hot)))
        return "폰트 불일치", expected_font, actual_font

    expected_pt = float(baseline[20]) * 72
    actual_pt = fv.font_size_mean * 72
    return "폰트 크기 불일치", f"{expected_pt:.0f}pt", f"{actual_pt:.0f}pt"


def _color_label(fv: SlideFeatureVector, baseline: np.ndarray) -> tuple[str, str, str]:
    expected_rgb = tuple(round(float(v) * 255) for v in baseline[29:32])
    actual_rgb = tuple(round(float(v) * 255) for v in fv.dominant_color_1)
    return "색상 불일치", f"RGB{expected_rgb}", f"RGB{actual_rgb}"


def _layout_label(fv: SlideFeatureVector, baseline: np.ndarray) -> tuple[str, str, str]:
    expected_ratio = float(baseline[44])
    actual_ratio = fv.text_area_ratio
    return (
        "레이아웃 불일치",
        f"텍스트 비율 {expected_ratio:.0%}",
        f"텍스트 비율 {actual_ratio:.0%}",
    )


def _content_label(fv: SlideFeatureVector, baseline: np.ndarray) -> tuple[str, str, str]:
    baseline_word = float(baseline[55])
    actual_word = fv.word_count_normalized
    expected_str = f"약 {baseline_word * 100:.0f}단어"
    actual_str = f"약 {actual_word * 100:.0f}단어"
    if baseline_word > _ε and actual_word >= 2.0 * baseline_word:
        return "과도한 텍스트 밀도", expected_str, actual_str
    return "콘텐츠 밀도 불일치", expected_str, actual_str
