export interface UploadResponse {
  file_id: string;
  slide_count: number;
  filename: string;
}

export interface AnalyzeResponse {
  task_id: string;
}

export interface TaskStatus {
  task_id: string;
  status: "pending" | "processing" | "completed" | "error";
  error_message?: string;
}

export interface ResultResponse extends TaskStatus {
  result?: AnalysisResult;
}

export interface SubScore {
  typography: number;
  color: number;
  layout: number;
  content: number;
}

export interface ConsistencyScore {
  total: number;
  sub_scores: SubScore;
}

export interface RootCause {
  feature_group: "typography" | "color" | "layout" | "content";
  label: string;
  expected_value: string;
  actual_value: string;
  similarity_score: number;
}

export interface Recommendation {
  root_cause: RootCause;
  action: string;
  impact_score_delta: number;
}

export interface SlideStats {
  slide_index: number;
  word_count: number;
  font_size_mean: number;
  text_area_ratio: number;
  element_count: number;
  dominant_font: string;
}

export interface OutlierSlide {
  slide_index: number;
  anomaly_score: number;
  root_causes: RootCause[];
  recommendations: Recommendation[];
}

export interface AnalysisResult {
  file_id: string;
  slide_count: number;
  consistency_score: ConsistencyScore;
  outlier_slides: OutlierSlide[];
  impact_score_after_fix: number;
  slide_stats: SlideStats[];
}
