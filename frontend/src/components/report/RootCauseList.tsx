import type { RootCause } from "../../types/api";
import { parseRgbString } from "../../utils/color";

interface Props {
  rootCauses: RootCause[];
}

const GROUP_LABELS: Record<string, string> = {
  typography: "폰트",
  color: "색상",
  layout: "레이아웃",
  content: "콘텐츠",
};

function ColorValue({ value }: { value: string }) {
  const parsed = parseRgbString(value);
  if (!parsed) return <span>{value}</span>;
  return (
    <span className="flex items-center gap-1.5">
      <span
        style={{ background: parsed.css }}
        className="w-4 h-4 rounded-full inline-block border border-neutral-600 align-middle shrink-0"
      />
      <span>{parsed.hex}</span>
    </span>
  );
}

export default function RootCauseList({ rootCauses }: Props) {
  return (
    <div className="space-y-3">
      {rootCauses.map((cause, i) => (
        <div key={i}>
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="rounded-sm bg-neutral-800 text-neutral-300 text-xs px-2 py-1">
              {GROUP_LABELS[cause.feature_group] ?? cause.feature_group}
            </span>
            <span className="rounded-sm bg-neutral-800 text-amber-400 text-xs px-2 py-1">
              {cause.label}
            </span>
          </div>
          <p className="text-xs text-neutral-500 leading-relaxed flex flex-wrap items-center gap-x-1 gap-y-1">
            <span>기대:</span>
            <ColorValue value={cause.expected_value} />
            <span>→ 실제:</span>
            <ColorValue value={cause.actual_value} />
          </p>
        </div>
      ))}
    </div>
  );
}
