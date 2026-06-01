import { getThumbnailUrl } from "../../services/api";

interface Props {
  fileId: string;
  slideNum: number;
  isOutlier: boolean;
  isSelected: boolean;
  onClick: () => void;
}

export default function SlideThumbnail({
  fileId,
  slideNum,
  isOutlier,
  isSelected,
  onClick,
}: Props) {
  const url = getThumbnailUrl(fileId, slideNum);

  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "relative w-full overflow-hidden rounded-lg cursor-pointer transition-colors duration-150",
        isOutlier
          ? "border-2 border-amber-400 ring-1 ring-amber-400/20"
          : "border border-neutral-800",
        isSelected ? "ring-2 ring-white/30" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <img
        src={url}
        alt={`슬라이드 ${slideNum + 1}`}
        className="w-full h-auto block"
      />
      <span className="absolute bottom-1 left-1 text-xs text-white/70 bg-black/50 px-1 rounded">
        {slideNum + 1}
      </span>
    </button>
  );
}
