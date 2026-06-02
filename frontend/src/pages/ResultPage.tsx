import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAnalysis } from "../hooks/useAnalysis";
import ConsistencyScoreCard from "../components/score/ConsistencyScoreCard";
import SlideGrid from "../components/slides/SlideGrid";
import DetailPanel from "../components/report/DetailPanel";

export default function ResultPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [selectedSlide, setSelectedSlide] = useState<number | null>(null);

  const { result, status, error } = useAnalysis(taskId ?? "");

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

  return (
    <main className="min-h-screen bg-[#0a0a0a] px-4 py-6">
      <div className="max-w-6xl mx-auto space-y-6">
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

        <ConsistencyScoreCard score={result.consistency_score} />

        <p className="text-xs text-neutral-600">
          썸네일은 레이아웃을 간략히 표현한 것입니다. 실제 슬라이드 외관과 다를 수 있습니다.
        </p>

        <div className="flex gap-6 items-start">
          <div className="w-2/3">
            <SlideGrid
              fileId={result.file_id}
              slideCount={result.slide_count}
              outlierSlides={result.outlier_slides}
              selectedSlide={selectedSlide}
              onSelectSlide={setSelectedSlide}
            />
          </div>
          <div className="w-1/3 sticky top-6">
            <DetailPanel
              selectedIndex={selectedSlide}
              outlierSlides={result.outlier_slides}
            />
          </div>
        </div>
      </div>
    </main>
  );
}
