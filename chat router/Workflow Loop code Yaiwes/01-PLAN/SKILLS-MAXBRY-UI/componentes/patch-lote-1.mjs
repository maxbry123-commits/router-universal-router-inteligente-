import fs from "node:fs";
import path from "node:path";

const base = path.resolve("components/ui");

const edits = {
  "bounce-sidebar.tsx": [
    ['dotColor = "#FC4C01"', 'dotColor = "var(--yaiwes-accent)"'],
  ],
  "hook-sidebar.tsx": [
    ['color = "#FC4C01"', 'color = "var(--yaiwes-accent)"'],
  ],
  "gooey-nav.tsx": [
    ['const BAR = "bg-[#F4F4F9] dark:bg-[#262626]"', 'const BAR = "bg-[#2A2A2A] dark:bg-[#2A2A2A]"'],
    ['const BAR_TEXT = "text-[#F4F4F9] dark:text-[#262626]"', 'const BAR_TEXT = "text-[#2A2A2A] dark:text-[#2A2A2A]"'],
    ['"text-[#868593]"', '"text-[#A0A0A0]"'],
    ['activeColor = "#FC4C01"', 'activeColor = "var(--yaiwes-accent)"'],
    ['activeLabelColor = "#ffffff"', 'activeLabelColor = "var(--yaiwes-text)"'],
  ],
  "family-drawer.tsx": [
    ["#F9F9F8", "#2A2A2A"],
    ["#FEFFFE", "#202020"],
    ["#F7F8F9", "#2A2A2A"],
    ["#949595", "#A0A0A0"],
    ["#222222", "#EDEDED"],
    ["#999999", "#BFBFBF"],
    ["#F5F5F5", "#3A3A3A"],
    ["#F0F2F4", "#3C3C3C"],
    ["#4DAFFF", "#0848F7"],
    ["#FF3F40", "#FF475F"],
    ["#FFF0F0", "#2A2A2A"],
    ["#A5A5A5", "#A0A0A0"],
    ["#FF3F3F", "#FF475F"],
    ["#8F8F8F", "#A0A0A0"],
  ],
};

let changed = 0;
for (const [file, replacements] of Object.entries(edits)) {
  const p = path.join(base, file);
  if (!fs.existsSync(p)) {
    console.warn(`SKIP ${file}: no existe`);
    continue;
  }
  let src = fs.readFileSync(p, "utf8");
  const before = src;
  for (const [from, to] of replacements) src = src.split(from).join(to);
  if (src !== before) {
    fs.writeFileSync(p, src);
    changed++;
    console.log(`PATCH ${file}`);
  } else {
    console.log(`NOCHANGE ${file}`);
  }
}
console.log(`Listo: ${changed} archivo(s) modificados.`);
console.log("proximity-sidebar.tsx se conserva sin cambios en este lote.");
