import type { RootCause } from "../../types/api";

interface Props {
  rootCauses: RootCause[];
}

const GROUP_LABELS: Record<string, string> = {
  typography: "폰트",
  color: "색상",
  layout: "레이아웃",
  content: "콘텐츠",
};

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
          <p className="text-xs text-neutral-500 leading-relaxed">
            기대: {cause.expected_value} → 실제: {cause.actual_value}
          </p>
        </div>
      ))}
    </div>
  );
}
