import type { OutlierSlide, SlideStats } from "../../types/api";
import RootCauseList from "./RootCauseList";
import RecommendationList from "./RecommendationList";

interface Props {
  selectedIndex: number | null;
  outlierSlides: OutlierSlide[];
  slideStats: SlideStats[];
}

export default function DetailPanel({ selectedIndex, outlierSlides, slideStats }: Props) {
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
  const stats = slideStats.find((s) => s.slide_index === selectedIndex);

  if (!outlier) {
    return (
      <div className="rounded-lg bg-[#111111] border border-neutral-800 p-4 space-y-4">
        <p className="text-sm text-neutral-300">
          이 슬라이드는 전체 디자인과 일관성이 높습니다
        </p>
        {stats && (
          <div>
            <p className="text-xs font-medium text-neutral-300 uppercase tracking-wider mb-3">
              슬라이드 통계
            </p>
            <div className="grid grid-cols-2 gap-y-2">
              {stats.slide_role != null && (
                <>
                  <span className="text-xs text-neutral-400">역할</span>
                  <span className="text-sm text-neutral-300">
                    {["표지", "섹션헤더", "본문", "도표/시각자료", "마무리"][stats.slide_role]}
                  </span>
                </>
              )}
              <span className="text-xs text-neutral-400">주요 폰트</span>
              <span className="text-sm text-neutral-300">{stats.dominant_font}</span>
              <span className="text-xs text-neutral-400">평균 폰트 크기</span>
              <span className="text-sm text-neutral-300">
                {stats.font_size_mean > 0 ? `${stats.font_size_mean}pt` : "-"}
              </span>
              <span className="text-xs text-neutral-400">텍스트 영역</span>
              <span className="text-sm text-neutral-300">
                {(stats.text_area_ratio * 100).toFixed(0)}%
              </span>
              <span className="text-xs text-neutral-400">단어 수</span>
              <span className="text-sm text-neutral-300">{stats.word_count}개</span>
              <span className="text-xs text-neutral-400">요소 수</span>
              <span className="text-sm text-neutral-300">{stats.element_count}개</span>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-[#111111] border border-neutral-800 p-4 space-y-6">
      <div>
        <p className="text-xs font-medium text-neutral-300 uppercase tracking-wider mb-3">
          원인 분석
        </p>
        <RootCauseList rootCauses={outlier.root_causes} />
      </div>
      {outlier.recommendations.length > 0 && (
        <div>
          <p className="text-xs font-medium text-neutral-300 uppercase tracking-wider mb-3">
            수정 제안
          </p>
          <RecommendationList recommendations={outlier.recommendations} />
        </div>
      )}
      {stats && (
        <div>
          <p className="text-xs font-medium text-neutral-300 uppercase tracking-wider mb-3">
            슬라이드 통계
          </p>
          <div className="grid grid-cols-2 gap-y-2">
            {stats.slide_role != null && (
              <>
                <span className="text-xs text-neutral-400">역할</span>
                <span className="text-sm text-neutral-300">
                  {["표지", "섹션헤더", "본문", "도표/시각자료", "마무리"][stats.slide_role]}
                </span>
              </>
            )}
            <span className="text-xs text-neutral-400">주요 폰트</span>
            <span className="text-sm text-neutral-300">{stats.dominant_font}</span>
            <span className="text-xs text-neutral-400">평균 폰트 크기</span>
            <span className="text-sm text-neutral-300">
              {stats.font_size_mean > 0 ? `${stats.font_size_mean}pt` : "-"}
            </span>
            <span className="text-xs text-neutral-400">텍스트 영역</span>
            <span className="text-sm text-neutral-300">
              {(stats.text_area_ratio * 100).toFixed(0)}%
            </span>
            <span className="text-xs text-neutral-400">단어 수</span>
            <span className="text-sm text-neutral-300">{stats.word_count}개</span>
            <span className="text-xs text-neutral-400">요소 수</span>
            <span className="text-sm text-neutral-300">{stats.element_count}개</span>
          </div>
        </div>
      )}
    </div>
  );
}
