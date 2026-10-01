export function parseDesignMd(content: string): {
  title: string;
  theme: string;
  accent: string;
} {
  const titleMatch = content.match(/^# (.+)/m);
  const title = titleMatch
    ? titleMatch[1].replace(/\s*Design System\s*$/i, "").trim()
    : "Unknown";

  const themeMatch = content.match(/## 1\. Visual Theme & Atmosphere\n\n([^\n]+)/);
  const theme = themeMatch ? themeMatch[1].trim() : "";

  const colorMatches = [...content.matchAll(/`(#[A-Fa-f0-9]{6})(?![A-Fa-f0-9])/g)];
  const colors = [...new Set(colorMatches.map((match) => match[1]))].slice(0, 12);

  const accent =
    colors.find((color) => {
      const r = parseInt(color.slice(1, 3), 16);
      const g = parseInt(color.slice(3, 5), 16);
      const b = parseInt(color.slice(5, 7), 16);
      const brightness = (r * 299 + g * 587 + b * 114) / 1000;
      return brightness > 80;
    }) ??
    colors[0] ??
    "#888888";

  return { title, theme, accent };
}
