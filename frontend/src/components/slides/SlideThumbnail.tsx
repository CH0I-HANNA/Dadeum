import { getThumbnailUrl } from "../../services/api";

const ROLE_LABELS: Record<number, string> = {
  0: "표지",
  1: "섹션",
  2: "본문",
  3: "도표",
  4: "마무리",
};

const ROLE_COLORS: Record<number, string> = {
  0: "text-purple-400",
  1: "text-blue-400",
  2: "text-neutral-300",
  3: "text-green-400",
  4: "text-orange-400",
};

interface Props {
  fileId: string;
  slideNum: number;
  isOutlier: boolean;
  isSelected: boolean;
  isCompare?: boolean;
  onClick: () => void;
  slideRole?: number | null;
}

export default function SlideThumbnail({
  fileId,
  slideNum,
  isOutlier,
  isSelected,
  isCompare = false,
  onClick,
  slideRole,
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
      <span className="absolute bottom-1 left-1 text-xs text-white/80 bg-black/60 px-1.5 py-0.5 rounded">
        {slideNum + 1}
      </span>
      {slideRole != null && (
        <span
          className={`absolute top-0.5 right-0.5 text-[10px] px-1 rounded bg-black/70 ${ROLE_COLORS[slideRole] ?? "text-neutral-300"}`}
        >
          {ROLE_LABELS[slideRole] ?? ""}
        </span>
      )}
      {isCompare && (
        <span className="absolute top-0.5 right-0.5 text-[10px] text-neutral-300 bg-black/70 px-1 rounded">
          B
        </span>
      )}
    </button>
  );
}
