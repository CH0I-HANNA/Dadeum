import type { OutlierSlide } from "../../types/api";
import RootCauseList from "./RootCauseList";
import RecommendationList from "./RecommendationList";

interface Props {
  selectedIndex: number | null;
  outlierSlides: OutlierSlide[];
}

export default function DetailPanel({ selectedIndex, outlierSlides }: Props) {
  if (selectedIndex === null) {
    return (
      <div className="rounded-lg bg-[#111111] border border-neutral-800 p-4 flex items-center justify-center min-h-48">
        <p className="text-sm text-neutral-500 text-center">
          슬라이드를 선택하면 상세 분석 결과가 표시됩니다
        </p>
      </div>
    );
  }

  const outlier = outlierSlides.find((s) => s.slide_index === selectedIndex);

  if (!outlier) {
    return (
      <div className="rounded-lg bg-[#111111] border border-neutral-800 p-4 flex items-center justify-center min-h-48">
        <p className="text-sm text-neutral-400 text-center">
          이 슬라이드는 전체 디자인과 일관성이 높습니다
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-[#111111] border border-neutral-800 p-4 space-y-6">
      <div>
        <p className="text-xs font-medium text-neutral-400 uppercase tracking-wider mb-3">
          원인 분석
        </p>
        <RootCauseList rootCauses={outlier.root_causes} />
      </div>
      {outlier.recommendations.length > 0 && (
        <div>
          <p className="text-xs font-medium text-neutral-400 uppercase tracking-wider mb-3">
            수정 제안
          </p>
          <RecommendationList recommendations={outlier.recommendations} />
        </div>
      )}
    </div>
  );
}
