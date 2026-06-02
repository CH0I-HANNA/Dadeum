import type { Recommendation } from "../../types/api";

interface Props {
  recommendations: Recommendation[];
}

export default function RecommendationList({ recommendations }: Props) {
  const sorted = [...recommendations]
    .filter((r) => r.impact_score_delta >= 0.05)
    .sort((a, b) => b.impact_score_delta - a.impact_score_delta);
  const totalDelta = sorted.reduce((sum, r) => sum + r.impact_score_delta, 0);

  if (sorted.length === 0) {
    return <p className="text-sm text-neutral-500">개선 제안이 없습니다</p>;
  }

  return (
    <div>
      <ul className="space-y-3">
        {sorted.map((rec, i) => (
          <li key={i} className="flex items-start justify-between gap-3">
            <div className="space-y-0.5">
              {i === 0 && (
                <span className="text-xs text-neutral-500">가장 효과적</span>
              )}
              <p className="text-sm text-neutral-300 leading-relaxed">{rec.action}</p>
            </div>
            <span className="shrink-0 text-xs text-amber-400 font-medium tabular-nums whitespace-nowrap">
              +{rec.impact_score_delta.toFixed(1)}점
            </span>
          </li>
        ))}
      </ul>
      {totalDelta > 0 && (
        <p className="text-xs text-neutral-500 mt-3 pt-3 border-t border-neutral-800">
          모두 적용 시 최대 +{totalDelta.toFixed(1)}점 향상 가능
        </p>
      )}
    </div>
  );
}
