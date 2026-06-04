from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path

from app.core import task_store
from app.core.exceptions import PipelineError
from app.models.schemas import AnalysisResult, OutlierSlide, SlideStats
from app.pipeline.detector import OutlierDetector
from app.pipeline.explainer import Explainer
from app.pipeline.extractor import SlideFeatureExtractor
from app.pipeline.hmm_scorer import HMMScorer
from app.pipeline.parser import parse_file
from app.pipeline.recommender import Recommender
from app.pipeline.role_classifier import RoleClassifier
from app.pipeline.scorer import compute_consistency_score
from app.pipeline.slide_renderer import render_slides

_TIMEOUT_SECONDS = 180


def run_analysis(file_path: str | Path, file_id: str) -> AnalysisResult:
    """파이프라인 전체를 순서대로 실행하고 AnalysisResult를 반환한다."""
    slides = parse_file(file_path)

    extractor = SlideFeatureExtractor()
    feature_vectors = extractor.extract_all(slides)

    consistency_score = compute_consistency_score(feature_vectors)

    detector = OutlierDetector()
    outlier_results = detector.fit_predict(feature_vectors)

    explainer = Explainer()
    root_causes_by_slide = explainer.explain_all(outlier_results, feature_vectors)

    recommender = Recommender()
    recommendations_by_slide = recommender.recommend_all(root_causes_by_slide, feature_vectors)
    impact_score = recommender.estimate_impact_score(feature_vectors, recommendations_by_slide)

    role_sequence: list[int] | None = None
    hmm_anomaly_score: float | None = None

    # CNN+HMM 파이프라인 (PPTX + PDF 모두 적용)
    if Path(file_path).suffix.lower() in (".pptx", ".pdf"):
        role_classifier = RoleClassifier.load()
        if role_classifier is not None:
            images = render_slides(Path(file_path))
            role_sequence = role_classifier.predict(images)

        hmm_scorer = HMMScorer.load()
        if hmm_scorer is not None and role_sequence:
            hmm_anomaly_score = hmm_scorer.score_sequence(role_sequence)

    known_fonts = SlideFeatureExtractor.KNOWN_FONTS

    slide_stats: list[SlideStats] = []
    for i, (slide, fv) in enumerate(zip(slides, feature_vectors)):
        word_count = sum(len(te.text.split()) for te in slide.text_elements)
        fv_np = fv.to_numpy()
        font_size_mean = round(float(fv_np[20]) * 72, 1)
        text_area_ratio = float(fv_np[44])
        element_count = len(slide.text_elements) + len(slide.image_elements)
        font_freq = fv_np[0:20]
        best_idx = int(font_freq.argmax())
        if float(font_freq[best_idx]) < 1e-8:
            dominant_font = "-"
        elif best_idx < len(known_fonts):
            dominant_font = known_fonts[best_idx]
        else:
            dominant_font = "Other"
        slide_role = role_sequence[i] if role_sequence and i < len(role_sequence) else None
        slide_stats.append(
            SlideStats(
                slide_index=i,
                word_count=word_count,
                font_size_mean=font_size_mean,
                text_area_ratio=round(text_area_ratio, 4),
                element_count=element_count,
                dominant_font=dominant_font,
                slide_role=slide_role,
            )
        )

    outlier_slides: list[OutlierSlide] = []
    for outlier in outlier_results:
        if not outlier.is_outlier:
            continue
        idx = outlier.slide_index
        outlier_slides.append(
            OutlierSlide(
                slide_index=idx,
                anomaly_score=outlier.anomaly_score,
                root_causes=root_causes_by_slide.get(idx, []),
                recommendations=recommendations_by_slide.get(idx, []),
            )
        )

    return AnalysisResult(
        file_id=file_id,
        slide_count=len(slides),
        consistency_score=consistency_score,
        outlier_slides=outlier_slides,
        impact_score_after_fix=impact_score,
        slide_stats=slide_stats,
        role_sequence=role_sequence,
        hmm_anomaly_score=hmm_anomaly_score,
    )


def run_analysis_with_timeout(file_path: str | Path, file_id: str, task_id: str) -> None:
    """BackgroundTask에서 호출되는 함수. timeout 감지 및 task 상태 관리를 포함한다."""
    task_store.set_processing(task_id)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_analysis, file_path, file_id)
        try:
            result = future.result(timeout=_TIMEOUT_SECONDS)
            task_store.set_completed(task_id, result)
        except TimeoutError:
            task_store.set_error(task_id, "분석 시간이 초과되었습니다.")
        except PipelineError as e:
            task_store.set_error(task_id, str(e))
        except Exception:
            task_store.set_error(task_id, "분석 중 예기치 않은 오류가 발생했습니다.")
