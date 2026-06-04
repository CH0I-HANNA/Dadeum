import type { ConsistencyScore } from "../../types/api";

interface Props {
  score: ConsistencyScore;
}

function scoreColor(value: number): string {
  if (value >= 70) return "#22c55e";
  if (value >= 40) return "#f59e0b";
  return "#ef4444";
}

interface BarRowProps {
  label: string;
  value: number;
}

function BarRow({ label, value }: BarRowProps) {
  const color = scoreColor(value);
  return (
    <div className="flex items-center gap-3">
      <span className="w-16 text-xs text-neutral-400 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-neutral-800 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{ width: `${value}%`, backgroundColor: color }}
        />
      </div>
      <span
        className="w-8 text-xs text-right tabular-nums"
        style={{ color }}
      >
        {Math.round(value)}
      </span>
    </div>
  );
}

export default function ConsistencyScoreCard({ score }: Props) {
  const color = scoreColor(score.total);
  const level = score.total >= 70 ? "높음" : score.total >= 40 ? "보통" : "낮음";

  return (
    <div className="rounded-lg bg-[#111111] border border-neutral-800 p-4 h-full">
      <div className="flex items-end gap-4 mb-4">
        <span className="text-5xl font-bold text-white tabular-nums">
          {Math.round(score.total)}
        </span>
        <div className="pb-1">
          <p className="text-xs text-neutral-500 uppercase tracking-wider">
            Consistency Score
          </p>
          <p className="text-sm font-medium" style={{ color }}>
            {level}
          </p>
        </div>
      </div>
      <div className="space-y-2">
        <BarRow label="폰트" value={score.sub_scores.typography} />
        <BarRow label="색상" value={score.sub_scores.color} />
        <BarRow label="레이아웃" value={score.sub_scores.layout} />
        <BarRow label="콘텐츠" value={score.sub_scores.content} />
      </div>
    </div>
  );
}
