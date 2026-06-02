import { useState } from "react";
import type { OutlierSlide, SlideStats } from "../../types/api";
import RootCauseList from "./RootCauseList";
import RecommendationList from "./RecommendationList";
import { getThumbnailUrl, getPreviewFixUrl } from "../../services/api";

interface Props {
  selectedIndex: number | null;
  outlierSlides: OutlierSlide[];
  slideStats: SlideStats[];
  fileId: string;
  taskId: string;
}

function FixedPreviewImage({ src }: { src: string }) {
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  if (error) return null;
  return (
    <div className="relative w-full">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-neutral-900 rounded">
          <p className="text-xs text-neutral-500">로딩 중...</p>
        </div>
      )}
      <img
        src={src}
        alt="수정 후 슬라이드"
        className="w-full rounded"
        onLoad={() => setLoading(false)}
        onError={() => { setError(true); setLoading(false); }}
      />
    </div>
  );
}

export default function DetailPanel({ selectedIndex, outlierSlides, slideStats, fileId, taskId }: Props) {
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
        <p className="text-sm text-neutral-400">
          이 슬라이드는 전체 디자인과 일관성이 높습니다
        </p>
        {stats && (
          <div>
            <p className="text-xs font-medium text-neutral-400 uppercase tracking-wider mb-3">
              슬라이드 통계
            </p>
            <div className="grid grid-cols-2 gap-y-2">
              <span className="text-xs text-neutral-500">주요 폰트</span>
              <span className="text-sm text-neutral-300">{stats.dominant_font}</span>
              <span className="text-xs text-neutral-500">평균 폰트 크기</span>
              <span className="text-sm text-neutral-300">
                {stats.font_size_mean > 0 ? `${stats.font_size_mean}pt` : "-"}
              </span>
              <span className="text-xs text-neutral-500">텍스트 영역</span>
              <span className="text-sm text-neutral-300">
                {(stats.text_area_ratio * 100).toFixed(0)}%
              </span>
              <span className="text-xs text-neutral-500">단어 수</span>
              <span className="text-sm text-neutral-300">{stats.word_count}개</span>
              <span className="text-xs text-neutral-500">요소 수</span>
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
      <div>
        <p className="text-xs font-medium text-neutral-400 uppercase tracking-wider mb-3">
          수정 미리보기
        </p>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <p className="text-xs text-neutral-500 mb-1">현재</p>
            <img
              src={getThumbnailUrl(fileId, selectedIndex)}
              alt="현재 슬라이드"
              className="w-full rounded"
            />
          </div>
          <div>
            <p className="text-xs text-neutral-500 mb-1">수정 후</p>
            <FixedPreviewImage
              src={getPreviewFixUrl(fileId, selectedIndex, taskId)}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
