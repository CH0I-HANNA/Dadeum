import { Fragment } from "react";

interface Props {
  roleSequence: number[] | null | undefined;
  hmmAnomalyScore: number | null | undefined;
}

const ROLE_LABELS = ["표지", "섹션", "본문", "도표", "마무리"];
const ROLE_COLORS = [
  "text-purple-400",
  "text-blue-400",
  "text-neutral-300",
  "text-green-400",
  "text-orange-400",
];

function anomalyScoreColor(score: number): string {
  if (score <= 30) return "#22c55e";
  if (score <= 60) return "#f59e0b";
  return "#ef4444";
}

interface RoleChipProps {
  roleIndex: number;
}

function RoleChip({ roleIndex }: RoleChipProps) {
  const label = ROLE_LABELS[roleIndex] ?? `역할${roleIndex}`;
  const colorClass = ROLE_COLORS[roleIndex] ?? "text-neutral-300";
  return <span className={`text-xs font-medium ${colorClass}`}>{label}</span>;
}

export default function StructureScoreCard({ roleSequence, hmmAnomalyScore }: Props) {
  if (hmmAnomalyScore == null && roleSequence == null) return null;

  const anomalyDisplay =
    hmmAnomalyScore != null ? Math.round(hmmAnomalyScore * 100) : null;

  const totalSlides = roleSequence?.length ?? 0;
  const displaySequence: (number | "ellipsis")[] | null =
    roleSequence == null
      ? null
      : roleSequence.length <= 12
        ? roleSequence
        : [
            ...roleSequence.slice(0, 6),
            "ellipsis" as const,
            ...roleSequence.slice(-3),
          ];

  return (
    <div className="rounded-lg bg-[#111111] border border-neutral-800 p-4 space-y-4">
      {anomalyDisplay != null && (
        <div>
          <div className="flex items-end gap-4 mb-1">
            <span
              className="text-5xl font-bold tabular-nums"
              style={{ color: anomalyScoreColor(anomalyDisplay) }}
            >
              {anomalyDisplay}
            </span>
            <div className="pb-1">
              <p className="text-xs text-neutral-500 uppercase tracking-wider">
                발표 구조 이상 점수
              </p>
            </div>
          </div>
          <p className="text-xs text-neutral-500">
            발표 흐름이 자연스러울수록 낮게 나타납니다
          </p>
        </div>
      )}
      {displaySequence != null && (
        <div>
          <p className="text-xs text-neutral-500 uppercase tracking-wider mb-2">
            슬라이드 역할 흐름
          </p>
          <div className="flex flex-wrap items-center gap-y-1">
            {displaySequence.map((item, i) => {
              if (item === "ellipsis") {
                return (
                  <Fragment key="ellipsis">
                    <span className="text-xs text-neutral-600 mx-0.5">→</span>
                    <span
                      className="text-xs text-neutral-500 cursor-default"
                      title={`전체 ${totalSlides}장`}
                    >
                      ···
                    </span>
                  </Fragment>
                );
              }
              return (
                <Fragment key={i}>
                  {i > 0 && (
                    <span className="text-xs text-neutral-600 mx-0.5">→</span>
                  )}
                  <RoleChip roleIndex={item} />
                </Fragment>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
