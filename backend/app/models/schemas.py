from typing import Literal, Optional
from pydantic import BaseModel


class UploadResponse(BaseModel):
    file_id: str
    slide_count: int
    filename: str


class AnalyzeResponse(BaseModel):
    task_id: str


class TaskStatus(BaseModel):
    task_id: str
    status: Literal["pending", "processing", "completed", "error"]
    error_message: Optional[str] = None


class SubScore(BaseModel):
    typography: float
    color: float
    layout: float
    content: float


class ConsistencyScore(BaseModel):
    total: float
    sub_scores: SubScore


class RootCause(BaseModel):
    feature_group: Literal["typography", "color", "layout", "content"]
    label: str
    expected_value: str
    actual_value: str
    similarity_score: float


class Recommendation(BaseModel):
    root_cause: RootCause
    action: str
    impact_score_delta: float


class SlideStats(BaseModel):
    slide_index: int
    word_count: int
    font_size_mean: float
    text_area_ratio: float
    element_count: int
    dominant_font: str


class OutlierSlide(BaseModel):
    slide_index: int
    anomaly_score: float
    root_causes: list[RootCause]
    recommendations: list[Recommendation]


class AnalysisResult(BaseModel):
    file_id: str
    slide_count: int
    consistency_score: ConsistencyScore
    outlier_slides: list[OutlierSlide]
    impact_score_after_fix: float
    slide_stats: list[SlideStats] = []


class ResultResponse(TaskStatus):
    result: Optional[AnalysisResult] = None
