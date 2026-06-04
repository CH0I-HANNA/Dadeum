import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAnalysis } from "../hooks/useAnalysis";
import { getReportUrl, downloadFixedFile } from "../services/api";
import ConsistencyScoreCard from "../components/score/ConsistencyScoreCard";
import StructureScoreCard from "../components/score/StructureScoreCard";
import SlideGrid from "../components/slides/SlideGrid";
import IssueFilter from "../components/slides/IssueFilter";
import type { FilterGroup } from "../components/slides/IssueFilter";
import SlidePreview from "../components/slides/SlidePreview";
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
  const { result, status, error, stage } = useAnalysis(taskId ?? "");
  const [copied, setCopied] = useState(false);
  const [downloading, setDownloading] = useState(false);

  function handleCopyLink() {
    navigator.clipboard.writeText(window.location.href).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  }

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
          {stage && <p className="text-xs text-neutral-500">{stage}</p>}
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
      <div className="max-w-screen-xl mx-auto space-y-5">
        {/* 헤더 */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-white">분석 결과</h1>
            <p className="mt-1 text-sm text-neutral-400">
              슬라이드 {result.slide_count}장
              {result.slide_count < 3 && (
                <span className="ml-2 text-amber-400">
                  · 슬라이드가 3장 미만이어서 이상 슬라이드 탐지를 수행하지 않았습니다.
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => navigate("/")}
              className="shrink-0 rounded-md border border-neutral-700 text-neutral-300 text-sm px-4 py-2 hover:border-neutral-500 transition-colors duration-150"
            >
              새 파일 분석
            </button>
            <button
              type="button"
              onClick={handleCopyLink}
              className="shrink-0 rounded-md border border-neutral-700 text-neutral-300 text-sm px-4 py-2 hover:border-neutral-500 transition-colors duration-150"
            >
              {copied ? "복사됨 ✓" : "링크 복사"}
            </button>
            <button
              type="button"
              onClick={() => downloadJson(result)}
              className="shrink-0 rounded-md border border-neutral-700 text-neutral-300 text-sm px-4 py-2 hover:border-neutral-500 transition-colors duration-150"
            >
              결과 내보내기
            </button>
            <button
              type="button"
              onClick={() => window.open(getReportUrl(taskId ?? ""), "_blank")}
              className="shrink-0 rounded-md border border-neutral-700 text-neutral-300 text-sm px-4 py-2 hover:border-neutral-500 transition-colors duration-150"
            >
              PDF 보고서
            </button>
            <button
              type="button"
              disabled={downloading}
              onClick={async () => {
                setDownloading(true);
                try {
                  await downloadFixedFile(result.file_id, taskId ?? "");
                } catch {
                  alert("수정 파일 생성에 실패했습니다.");
                } finally {
                  setDownloading(false);
                }
              }}
              className="shrink-0 rounded-md border border-neutral-700 text-neutral-300 text-sm px-4 py-2 hover:border-neutral-500 transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {downloading ? "수정 중..." : "수정 파일 다운로드"}
            </button>
          </div>
        </div>

        {/* 점수 카드 */}
        <ConsistencyScoreCard score={result.consistency_score} />
        <StructureScoreCard
          roleSequence={result.role_sequence}
          hmmAnomalyScore={result.hmm_anomaly_score}
        />

        {result.outlier_slides.length > 0 && (
          <p className="text-sm text-amber-400">
            슬라이드 {result.slide_count}장 중{" "}
            <span className="font-medium">{result.outlier_slides.length}장</span>에서 디자인 이상 감지
            {result.impact_score_after_fix > result.consistency_score.total && (
              <span className="ml-2 text-neutral-400">
                · 수정 시 <span className="text-white">{Math.round(result.impact_score_after_fix)}점</span> 예상
              </span>
            )}
          </p>
        )}

        {/* 0 outliers 상태 */}
        {result.outlier_slides.length === 0 ? (
          <div className="rounded-lg bg-[#111111] border border-neutral-800 p-8 text-center">
            <p className="text-lg text-white mb-2">디자인이 일관성 있게 구성되어 있습니다</p>
            <p className="text-sm text-neutral-400">이상 슬라이드가 감지되지 않았습니다.</p>
          </div>
        ) : (
        /* 3패널 레이아웃 */
        <div className="flex gap-4 items-start">

          {/* 왼쪽: 슬라이드 목록 */}
          <div className="w-56 shrink-0 space-y-3">
            <p className="text-xs text-neutral-500 uppercase tracking-wider">슬라이드 목록</p>
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
            <div className="overflow-y-auto max-h-[calc(100vh-260px)] pr-1">
              <SlideGrid
                fileId={result.file_id}
                slideCount={result.slide_count}
                outlierSlides={filteredOutlierSlides}
                selectedSlide={activeSlide}
                compareSlide={compareMode ? compareSlide : null}
                onSelectSlide={handleSelectSlide}
                slideStats={result.slide_stats}
              />
            </div>
          </div>

          {/* 가운데: 선택된 슬라이드 미리보기 */}
          <div className="flex-1 min-w-0 space-y-3">
            <div className="flex items-center justify-end">
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

            <SlidePreview
              fileId={result.file_id}
              slideIndex={activeSlide}
              outlierSlides={result.outlier_slides}
            />

            <p className="text-xs text-neutral-600">
              썸네일은 실제 슬라이드와 다를 수 있습니다.
            </p>
          </div>

          {/* 오른쪽: 상세 분석 */}
          <div className="w-72 shrink-0">
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
        )}
      </div>
    </main>
  );
}
