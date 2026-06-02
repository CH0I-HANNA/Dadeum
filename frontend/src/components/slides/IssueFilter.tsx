import type { OutlierSlide } from "../../types/api";

type FilterGroup = "all" | "typography" | "color" | "layout" | "content";

const LABELS: Record<FilterGroup, string> = {
  all: "전체",
  typography: "폰트",
  color: "색상",
  layout: "레이아웃",
  content: "콘텐츠",
};

interface Props {
  outlierSlides: OutlierSlide[];
  activeFilter: FilterGroup;
  onFilterChange: (filter: FilterGroup) => void;
}

export type { FilterGroup };

export default function IssueFilter({ outlierSlides, activeFilter, onFilterChange }: Props) {
  function countForGroup(group: FilterGroup): number {
    if (group === "all") return outlierSlides.length;
    return outlierSlides.filter((s) =>
      s.root_causes.some((rc) => rc.feature_group === group),
    ).length;
  }

  const groups: FilterGroup[] = ["all", "typography", "color", "layout", "content"];

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {groups.map((group) => {
        const count = countForGroup(group);
        if (group !== "all" && count === 0) return null;
        const isActive = activeFilter === group;
        return (
          <button
            key={group}
            type="button"
            onClick={() => onFilterChange(group)}
            className={[
              "text-xs px-3 py-1 rounded-sm border transition-colors duration-150",
              isActive
                ? "border-amber-400 text-amber-400 bg-amber-400/10"
                : "border-neutral-700 text-neutral-400 hover:border-neutral-500",
            ].join(" ")}
          >
            {LABELS[group]}
            {group !== "all" && (
              <span className="ml-1 text-neutral-500">{count}</span>
            )}
          </button>
        );
      })}
    </div>
  );
}
