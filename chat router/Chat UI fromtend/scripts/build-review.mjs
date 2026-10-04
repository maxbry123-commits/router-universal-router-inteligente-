import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { build } from "esbuild";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const source = await readFile(join(root, "chat Yaiwes fromtend.html"), "utf8");
const tokens = await readFile(join(root, "styles/tokens.css"), "utf8");
const chat = await readFile(join(root, "styles/chat.css"), "utf8");
const result = await build({
  entryPoints: [join(root, "src/app.js")],
  bundle: true,
  write: false,
  platform: "browser",
  format: "iife",
  target: "es2022",
  logLevel: "silent",
});

const cssLinks = ["./styles/tokens.css", "./styles/chat.css"];
let html = source;
for (const link of cssLinks) {
  const tag = `<link rel="stylesheet" href="${link}">`;
  if (!html.includes(tag)) throw new Error(`Falta el enlace CSS: ${link}`);
  html = html.replace(tag, `<style>${(link.includes("tokens") ? tokens : chat).replaceAll("</style", "<\\/style")}</style>`);
}
const moduleTag = '<script type="module" src="./src/app.js"></script>';
if (!html.includes(moduleTag) || result.outputFiles.length !== 1 || !html.includes("</body>")) {
  throw new Error("Entrada modular o resultado del empaquetado inesperados");
}
html = html.replace(moduleTag, "");
html = html.replace(
  "No se cargaron los módulos del chat. Este HTML es la fuente modular: abre la carpeta mediante un servidor o usa la vista autónoma de revisión.",
  "No se pudo iniciar el chat en este visor. Descarga este archivo y ábrelo directamente en tu navegador.",
);
html = html.replace("</body>", `<script>${result.outputFiles[0].text.replaceAll("</script", "<\\/script")}</script>\n</body>`);
html = `<!-- Vista autónoma generada desde los módulos: editar src/ y styles/, no este archivo. -->\n${html}`;
const output = join(root, "chat Yaiwes fromtend.revisar.html");
await writeFile(output, html);
console.log(`Vista autónoma creada: ${output}`);
