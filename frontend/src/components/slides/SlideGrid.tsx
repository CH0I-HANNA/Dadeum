import type { OutlierSlide, SlideStats } from "../../types/api";
import SlideThumbnail from "./SlideThumbnail";

interface Props {
  fileId: string;
  slideCount: number;
  outlierSlides: OutlierSlide[];
  selectedSlide: number | null;
  compareSlide?: number | null;
  onSelectSlide: (index: number) => void;
  slideStats?: SlideStats[];
}

export default function SlideGrid({
  fileId,
  slideCount,
  outlierSlides,
  selectedSlide,
  compareSlide = null,
  onSelectSlide,
  slideStats,
}: Props) {
  const outlierSet = new Set(outlierSlides.map((s) => s.slide_index));

  return (
    <div className="flex flex-col gap-2">
      {Array.from({ length: slideCount }, (_, i) => (
        <SlideThumbnail
          key={i}
          fileId={fileId}
          slideNum={i}
          isOutlier={outlierSet.has(i)}
          isSelected={selectedSlide === i}
          isCompare={compareSlide === i}
          onClick={() => onSelectSlide(i)}
          slideRole={slideStats?.find((s) => s.slide_index === i)?.slide_role}
        />
      ))}
    </div>
  );
}
