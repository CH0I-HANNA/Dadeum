from __future__ import annotations

from app.models.schemas import Recommendation, RootCause
from app.pipeline.extractor import SlideFeatureVector
from app.pipeline.scorer import compute_consistency_score

_GROUP_WEIGHT = {"typography": 0.30, "color": 0.30, "layout": 0.25, "content": 0.15}


def _make_action(root_cause: RootCause) -> str:
    label = root_cause.label
    actual = root_cause.actual_value
    expected = root_cause.expected_value

    if label == "폰트 불일치":
        return f"{actual} → {expected} 로 변경 권장"
    if label == "폰트 크기 불일치":
        return f"폰트 크기 {actual} → {expected} 로 조정 권장"
    if label == "색상 불일치":
        return "주 색상을 다른 슬라이드와 통일하세요"
    if label == "레이아웃 불일치":
        return f"텍스트 영역 비율을 {expected} 에 맞게 조정 권장"
    if label == "과도한 텍스트 밀도":
        return "텍스트 양을 줄이거나 슬라이드를 분리 권장"
    return f"{label} 수정 권장"


def _compute_delta(root_cause: RootCause) -> float:
    improvement_potential = 1.0 - root_cause.similarity_score
    weight = _GROUP_WEIGHT.get(root_cause.feature_group, 0.0)
    return improvement_potential * weight * 100 * 0.5


class Recommender:
    def recommend(
        self,
        root_cause: RootCause,
        slide_index: int,
        all_vectors: list[SlideFeatureVector],
    ) -> Recommendation:
        return Recommendation(
            root_cause=root_cause,
            action=_make_action(root_cause),
            impact_score_delta=_compute_delta(root_cause),
        )

    def recommend_all(
        self,
        root_causes_by_slide: dict[int, list[RootCause]],
        all_vectors: list[SlideFeatureVector],
    ) -> dict[int, list[Recommendation]]:
        return {
            slide_index: [
                self.recommend(rc, slide_index, all_vectors) for rc in causes
            ]
            for slide_index, causes in root_causes_by_slide.items()
        }

    def estimate_impact_score(
        self,
        all_vectors: list[SlideFeatureVector],
        recommendations_by_slide: dict[int, list[Recommendation]],
    ) -> float:
        current_score = compute_consistency_score(all_vectors).total
        total_delta = sum(
            rec.impact_score_delta
            for recs in recommendations_by_slide.values()
            for rec in recs
        )
        return min(100.0, current_score + total_delta)
