import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAnalysis } from "../hooks/useAnalysis";
import ConsistencyScoreCard from "../components/score/ConsistencyScoreCard";
import SlideGrid from "../components/slides/SlideGrid";
import IssueFilter from "../components/slides/IssueFilter";
import type { FilterGroup } from "../components/slides/IssueFilter";
import DetailPanel from "../components/report/DetailPanel";
import ComparePanel from "../components/report/ComparePanel";
import type { AnalysisResult } from "../types/api";

function downloadJson(result: AnalysisResult) {
  const blob = new Blob([JSON.stringify(result, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `dadeum-result-${result.file_id.slice(0, 8)}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ResultPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const { result, status, error } = useAnalysis(taskId ?? "");

  const [selectedSlide, setSelectedSlide] = useState<number | null>(null);
  const [activeFilter, setActiveFilter] = useState<FilterGroup>("all");
  const [compareMode, setCompareMode] = useState(false);
  const [compareSlide, setCompareSlide] = useState<number | null>(null);

  const firstOutlierIndex =
    result && result.outlier_slides.length > 0
      ? result.outlier_slides[0].slide_index
      : null;
  const activeSlide = selectedSlide ?? firstOutlierIndex;

  function handleSelectSlide(index: number) {
    if (!compareMode) {
      setSelectedSlide(index);
      return;
    }
    if (activeSlide === null) {
      setSelectedSlide(index);
    } else if (index !== activeSlide) {
      setCompareSlide(index);
    }
  }

  function toggleCompareMode() {
    setCompareMode((prev) => {
      if (prev) setCompareSlide(null);
      return !prev;
    });
  }

  const filteredOutlierSlides =
    !result || activeFilter === "all"
      ? result?.outlier_slides ?? []
      : result.outlier_slides.filter((s) =>
          s.root_causes.some((rc) => rc.feature_group === activeFilter),
        );

  if (status === "pending" || status === "processing") {
    return (
      <main className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-6 h-6 border-2 border-neutral-600 border-t-amber-400 rounded-full animate-spin" />
          <p className="text-sm text-neutral-400">분석 중...</p>
        </div>
      </main>
    );
  }

  if (status === "error" || !result) {
    return (
      <main className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-sm text-red-400">
            {error ?? "분석 중 오류가 발생했습니다. 다시 시도해주세요."}
          </p>
          <button
            type="button"
            className="rounded-md border border-neutral-700 text-neutral-300 text-sm px-4 py-2 hover:border-neutral-500 transition-colors duration-150"
            onClick={() => navigate("/")}
          >
            다시 시도
          </button>
        </div>
      </main>
    );
  }

  const showCompare = compareMode && activeSlide !== null && compareSlide !== null;

  return (
    <main className="min-h-screen bg-[#0a0a0a] px-4 py-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-white">분석 결과 <span className="text-xs text-amber-400">v2</span></h1>
            <p className="mt-1 text-sm text-neutral-400">
              슬라이드 {result.slide_count}장
              {result.slide_count < 3 && (
                <span className="ml-2 text-amber-400">
                  · 슬라이드가 3장 미만이어서 이상 슬라이드 탐지를 수행하지 않았습니다.
                </span>
              )}
            </p>
          </div>
          <button
            type="button"
            onClick={() => downloadJson(result)}
            className="shrink-0 rounded-md border border-neutral-700 text-neutral-300 text-sm px-4 py-2 hover:border-neutral-500 transition-colors duration-150"
          >
            결과 내보내기
          </button>
        </div>

        <ConsistencyScoreCard score={result.consistency_score} />

        {result.outlier_slides.length > 0 && (
          <p className="text-sm text-amber-400">
            슬라이드 {result.slide_count}장 중{" "}
            <span className="font-medium">{result.outlier_slides.length}장</span>에서 디자인 이상 감지
          </p>
        )}

        <p className="text-xs text-neutral-600">
          썸네일은 레이아웃을 간략히 표현한 것입니다. 실제 슬라이드 외관과 다를 수 있습니다.
        </p>

        <div className="flex gap-6 items-start">
          <div className="w-2/3 space-y-3">
            <div className="flex items-center justify-between gap-3">
              {result.outlier_slides.length > 0 && (
                <IssueFilter
                  outlierSlides={result.outlier_slides}
                  activeFilter={activeFilter}
                  onFilterChange={(f) => {
                    setActiveFilter(f);
                    setCompareSlide(null);
                  }}
                />
              )}
              <button
                type="button"
                onClick={toggleCompareMode}
                className={[
                  "shrink-0 text-xs px-3 py-1 rounded-sm border transition-colors duration-150",
                  compareMode
                    ? "border-white text-white"
                    : "border-neutral-700 text-neutral-400 hover:border-neutral-500",
                ].join(" ")}
              >
                {compareMode ? "비교 종료" : "비교"}
              </button>
            </div>
            {compareMode && (
              <p className="text-xs text-neutral-500">
                {activeSlide === null
                  ? "첫 번째 슬라이드를 선택하세요"
                  : compareSlide === null
                    ? `슬라이드 ${activeSlide + 1} 선택됨 · 비교할 슬라이드를 선택하세요`
                    : `슬라이드 ${activeSlide + 1} vs ${compareSlide + 1}`}
              </p>
            )}
            <SlideGrid
              fileId={result.file_id}
              slideCount={result.slide_count}
              outlierSlides={filteredOutlierSlides}
              selectedSlide={activeSlide}
              compareSlide={compareMode ? compareSlide : null}
              onSelectSlide={handleSelectSlide}
            />
          </div>
          <div className="w-1/3 sticky top-6">
            {showCompare ? (
              <ComparePanel
                fileId={result.file_id}
                indexA={activeSlide}
                indexB={compareSlide}
                slideStats={result.slide_stats}
                outlierSlides={result.outlier_slides}
              />
            ) : (
              <DetailPanel
                selectedIndex={activeSlide}
                outlierSlides={result.outlier_slides}
                slideStats={result.slide_stats}
              />
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
