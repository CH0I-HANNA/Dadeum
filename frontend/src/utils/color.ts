/** "RGB(0, 0, 0)" → { css: "rgb(0,0,0)", hex: "#000000" } | null */
export function parseRgbString(val: string): { css: string; hex: string } | null {
  const match = val.match(/^RGB\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$/i);
  if (!match) return null;
  const r = parseInt(match[1], 10);
  const g = parseInt(match[2], 10);
  const b = parseInt(match[3], 10);
  const css = `rgb(${r},${g},${b})`;
  const hex = `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
  return { css, hex };
}
