import { getThumbnailUrl } from "../../services/api";

interface Props {
  fileId: string;
  slideNum: number;
  isOutlier: boolean;
  isSelected: boolean;
  isCompare?: boolean;
  onClick: () => void;
}

export default function SlideThumbnail({
  fileId,
  slideNum,
  isOutlier,
  isSelected,
  isCompare = false,
  onClick,
}: Props) {
  const url = getThumbnailUrl(fileId, slideNum);

  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "relative w-full overflow-hidden rounded cursor-pointer transition-colors duration-150",
        isOutlier ? "border-2 border-amber-400" : "border border-neutral-800",
        isSelected ? "ring-2 ring-white/40" : "",
        isCompare ? "ring-2 ring-neutral-400/50" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <img
        src={url}
        alt={`슬라이드 ${slideNum + 1}`}
        className="w-full h-auto block"
      />
      <span className="absolute bottom-0.5 left-1 text-[10px] text-white/70 bg-black/50 px-1 rounded">
        {slideNum + 1}
      </span>
      {isCompare && (
        <span className="absolute top-0.5 right-0.5 text-[10px] text-neutral-300 bg-black/70 px-1 rounded">
          B
        </span>
      )}
    </button>
  );
}
