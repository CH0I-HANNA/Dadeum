import type { SlideStats, OutlierSlide } from "../../types/api";
import { getThumbnailUrl } from "../../services/api";

interface Props {
  fileId: string;
  indexA: number;
  indexB: number;
  slideStats: SlideStats[];
  outlierSlides: OutlierSlide[];
}

function StatRow({
  label,
  a,
  b,
  highlight,
}: {
  label: string;
  a: string;
  b: string;
  highlight: boolean;
}) {
  return (
    <tr className={highlight ? "text-amber-400" : ""}>
      <td className="text-xs text-neutral-500 py-1 pr-3 whitespace-nowrap">{label}</td>
      <td className="text-sm text-center py-1 px-2">{a}</td>
      <td className="text-sm text-center py-1 px-2">{b}</td>
    </tr>
  );
}

export default function ComparePanel({
  fileId,
  indexA,
  indexB,
  slideStats,
  outlierSlides,
}: Props) {
  const statsA = slideStats.find((s) => s.slide_index === indexA);
  const statsB = slideStats.find((s) => s.slide_index === indexB);
  const outlierA = outlierSlides.find((s) => s.slide_index === indexA);
  const outlierB = outlierSlides.find((s) => s.slide_index === indexB);

  function diff(a: number, b: number): boolean {
    return Math.abs(a - b) > 0.05;
  }

  return (
    <div className="rounded-lg bg-[#111111] border border-neutral-800 p-4 space-y-4">
      <p className="text-xs font-medium text-neutral-400 uppercase tracking-wider">
        슬라이드 비교
      </p>

      <div className="grid grid-cols-2 gap-2">
        {[
          { idx: indexA, outlier: outlierA },
          { idx: indexB, outlier: outlierB },
        ].map(({ idx, outlier }) => (
          <div key={idx} className="space-y-1">
            <div
              className={[
                "overflow-hidden rounded",
                outlier ? "border border-amber-400" : "border border-neutral-700",
              ].join(" ")}
            >
              <img
                src={getThumbnailUrl(fileId, idx)}
                alt={`슬라이드 ${idx + 1}`}
                className="w-full h-auto block"
              />
            </div>
            <p className="text-xs text-center text-neutral-400">
              슬라이드 {idx + 1}
              {outlier && <span className="ml-1 text-amber-400">·이상</span>}
            </p>
          </div>
        ))}
      </div>

      {statsA && statsB && (
        <table className="w-full">
          <thead>
            <tr>
              <th className="text-left" />
              <th className="text-xs text-neutral-500 font-normal pb-1">
                {indexA + 1}번
              </th>
              <th className="text-xs text-neutral-500 font-normal pb-1">
                {indexB + 1}번
              </th>
            </tr>
          </thead>
          <tbody>
            {statsA.slide_role != null && statsB.slide_role != null && (
              <StatRow
                label="역할"
                a={["표지", "섹션헤더", "본문", "도표/시각자료", "마무리"][statsA.slide_role] ?? ""}
                b={["표지", "섹션헤더", "본문", "도표/시각자료", "마무리"][statsB.slide_role] ?? ""}
                highlight={statsA.slide_role !== statsB.slide_role}
              />
            )}
            <StatRow
              label="주요 폰트"
              a={statsA.dominant_font}
              b={statsB.dominant_font}
              highlight={statsA.dominant_font !== statsB.dominant_font}
            />
            <StatRow
              label="폰트 크기"
              a={statsA.font_size_mean > 0 ? `${statsA.font_size_mean}pt` : "-"}
              b={statsB.font_size_mean > 0 ? `${statsB.font_size_mean}pt` : "-"}
              highlight={diff(statsA.font_size_mean, statsB.font_size_mean)}
            />
            <StatRow
              label="텍스트 영역"
              a={`${(statsA.text_area_ratio * 100).toFixed(0)}%`}
              b={`${(statsB.text_area_ratio * 100).toFixed(0)}%`}
              highlight={diff(statsA.text_area_ratio, statsB.text_area_ratio)}
            />
            <StatRow
              label="단어 수"
              a={`${statsA.word_count}개`}
              b={`${statsB.word_count}개`}
              highlight={
                Math.abs(statsA.word_count - statsB.word_count) >
                Math.max(statsA.word_count, statsB.word_count) * 0.3
              }
            />
            <StatRow
              label="요소 수"
              a={`${statsA.element_count}개`}
              b={`${statsB.element_count}개`}
              highlight={statsA.element_count !== statsB.element_count}
            />
          </tbody>
        </table>
      )}
    </div>
  );
}
