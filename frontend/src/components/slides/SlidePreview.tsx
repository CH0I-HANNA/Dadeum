import type { OutlierSlide } from "../../types/api";
import { getThumbnailUrl } from "../../services/api";

const GROUP_LABEL: Record<string, string> = {
  typography: "폰트",
  color: "색상",
  layout: "레이아웃",
  content: "콘텐츠",
};

interface Props {
  fileId: string;
  slideIndex: number | null;
  outlierSlides: OutlierSlide[];
}

export default function SlidePreview({ fileId, slideIndex, outlierSlides }: Props) {
  if (slideIndex === null) {
    return (
      <div className="w-full aspect-video bg-[#111111] border border-neutral-800 rounded-lg flex items-center justify-center">
        <p className="text-sm text-neutral-600">슬라이드를 선택하세요</p>
      </div>
    );
  }

  const outlier = outlierSlides.find((s) => s.slide_index === slideIndex);
  const groups = outlier
    ? [...new Set(outlier.root_causes.map((rc) => rc.feature_group))]
    : [];

  return (
    <div className="relative w-full rounded-lg overflow-hidden border border-neutral-800">
      <img
        src={getThumbnailUrl(fileId, slideIndex)}
        alt={`슬라이드 ${slideIndex + 1}`}
        className="w-full h-auto block"
      />

      {/* 슬라이드 번호 */}
      <span className="absolute bottom-3 left-3 text-xs text-white/80 bg-black/60 px-2 py-0.5 rounded">
        {slideIndex + 1}
      </span>

      {/* 이슈 뱃지 */}
      {groups.length > 0 && (
        <div className="absolute top-3 right-3 flex flex-col gap-1 items-end">
          {groups.map((g) => (
            <span
              key={g}
              className="text-xs bg-amber-400/90 text-black font-medium px-2 py-0.5 rounded"
            >
              {GROUP_LABEL[g] ?? g}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
