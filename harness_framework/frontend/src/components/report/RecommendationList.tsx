import type { Recommendation } from "../../types/api";

interface Props {
  recommendations: Recommendation[];
}

export default function RecommendationList({ recommendations }: Props) {
  return (
    <ul className="space-y-3">
      {recommendations.map((rec, i) => (
        <li key={i} className="flex items-start justify-between gap-3">
          <p className="text-sm text-neutral-300 leading-relaxed">{rec.action}</p>
          <span className="shrink-0 text-xs text-amber-400 font-medium tabular-nums whitespace-nowrap">
            +{rec.impact_score_delta.toFixed(1)}점
          </span>
        </li>
      ))}
    </ul>
  );
}
