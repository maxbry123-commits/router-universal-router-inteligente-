import fs from "node:fs";
import path from "node:path";

const ui = path.resolve("components/ui");
const backup = path.join(ui, "_rare-ui-original-01-05");

const files = {
  "folder-component.tsx": [
    ["backFill: \"black\"", "backFill: \"#1B1B1B\""],
    ["flapFill: \"#292929\"", "flapFill: \"#2A2A2A\""],
    ["flapStroke: \"#979797\"", "flapStroke: \"#525252\""],
    ["cardFill: \"#F1F1F1\"", "cardFill: \"#DADADA\""],
    ["cardStroke: \"#E0E0E0\"", "cardStroke: \"#BFBFBF\""],
    ["cardLineFill: \"#D4D4D4\"", "cardLineFill: \"#A0A0A0\""],

    ["backFill: \"#ffffff\"", "backFill: \"#202020\""],
    ["flapFill: \"#f5f5f5\"", "flapFill: \"#2A2A2A\""],
    ["flapStroke: \"#d4d4d4\"", "flapStroke: \"#525252\""],
    ["cardFill: \"#262626\"", "cardFill: \"#202020\""],
    ["cardStroke: \"#404040\"", "cardStroke: \"#525252\""],
    ["cardLineFill: \"#737373\"", "cardLineFill: \"#A0A0A0\""],

    ["backFill: \"#50B1FD\"", "backFill: \"#0848F7\""],
    ["flapFill: \"#3a9ae8\"", "flapFill: \"#063BC9\""],
    ["flapStroke: \"#7ec8ff\"", "flapStroke: \"#3B6CFF\""],
  ],

  "bounce-sidebar.tsx": [
    ['dotColor = "#FC4C01"', 'dotColor = "#0848F7"'],
  ],

  "hook-sidebar.tsx": [
    ['color = "#FC4C01"', 'color = "#0848F7"'],
  ],

  "family-drawer.tsx": [
    ["border-gray-200 bg-white", "border-[#3A3A3A] bg-[#2A2A2A]"],
    ["text-black", "text-[#EDEDED]"],
    ["hover:bg-[#F9F9F8]", "hover:bg-[#3C3C3C]"],
    ["bg-black/30", "bg-black/45"],

    ["bg-[#FEFFFE]", "bg-[#202020]"],
    ["bg-[#F7F8F9]", "bg-[#2A2A2A]"],
    ["text-[#949595]", "text-[#A0A0A0]"],
    ["text-[#222222]", "text-[#EDEDED]"],
    ["text-[#999999]", "text-[#BFBFBF]"],
    ["border-[#F5F5F5]", "border-[#3A3A3A]"],
    ["bg-[#F0F2F4]", "bg-[#3C3C3C]"],
    ["bg-[#4DAFFF]", "bg-[#0848F7]"],
    ["text-[#FF3F40]", "text-[#FF475F]"],
    ["bg-[#FFF0F0]", "bg-[#2A2A2A]"],
    ["border-[#F7F7F7]", "border-[#3A3A3A]"],

    ['stroke="#999999"', 'stroke="#A0A0A0"'],
    ['fill="#999999"', 'fill="#A0A0A0"'],
    ['stroke="#A5A5A5"', 'stroke="#A0A0A0"'],
    ['fill="#A5A5A5"', 'fill="#A0A0A0"'],
    ['stroke="#8F8F8F"', 'stroke="#A0A0A0"'],
    ['fill="#8F8F8F"', 'fill="#A0A0A0"'],
    ['stroke="#FF3F3F"', 'stroke="#FF475F"'],
    ['fill="#FF3F3F"', 'fill="#FF475F"'],
  ],

  "proximity-sidebar.tsx": [
    ['className: "bg-foreground"', 'className: "bg-[#EDEDED]"'],
    ['className: "bg-muted-foreground/40"', 'className: "bg-[#A0A0A0]/40"'],
    [
      "group-focus-visible:ring-2 group-focus-visible:ring-ring group-focus-visible:ring-offset-2",
      "group-focus-visible:ring-2 group-focus-visible:ring-[#0848F7] group-focus-visible:ring-offset-2"
    ],
  ],
};

fs.mkdirSync(backup, { recursive: true });

let changed = 0;
let substitutions = 0;

for (const [file, rules] of Object.entries(files)) {
  const target = path.join(ui, file);

  if (!fs.existsSync(target)) {
    throw new Error(`Falta ${target}. Instala primero el componente Rare UI original.`);
  }

  const original = fs.readFileSync(target, "utf8");
  const backupFile = path.join(backup, file);

  if (!fs.existsSync(backupFile)) {
    fs.writeFileSync(backupFile, original);
  }

  let next = original;

  for (const [from, to] of rules) {
    const n = next.split(from).length - 1;
    if (n > 0) {
      next = next.split(from).join(to);
      substitutions += n;
    }
  }

  if (next !== original) {
    fs.writeFileSync(target, next);
    changed++;
    console.log(`PATCH ${file}`);
  } else {
    console.log(`SIN CAMBIO ${file}`);
  }
}

console.log(`Archivos modificados: ${changed}/5`);
console.log(`Sustituciones cromáticas: ${substitutions}`);
console.log(`Originales preservados en: ${backup}`);
