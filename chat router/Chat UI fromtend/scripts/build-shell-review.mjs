import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { build } from "esbuild";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
let html = await readFile(join(root, "paneles Yaiwes fromtend.html"), "utf8");
for (const name of ["tokens", "chat", "icon-library", "typography", "rareui", "shell", "run", "wall"]) {
  const link = `<link rel="stylesheet" href="./styles/${name}.css">`;
  if (!html.includes(link)) throw new Error(`CSS_NOT_LINKED:${name}`);
  const css = await readFile(join(root, "styles", `${name}.css`), "utf8");
  html = html.replace(link, `<style>${css.replaceAll("</style", "<\\/style")}</style>`);
}
const entry = '<script type="module" src="./src/shell-app.js"></script>';
const result = await build({
  entryPoints: [join(root, "src/shell-app.js")], bundle: true, write: false,
  platform: "browser", format: "iife", target: "es2022", logLevel: "silent",
});
if (!html.includes(entry) || result.outputFiles.length !== 1) throw new Error("SHELL_BUNDLE_INVALID");
html = html.replace(entry, "");
html = html.replace(
  "No se cargaron los módulos. Abre esta carpeta con un servidor o usa el archivo .revisar.html.",
  "No se pudo iniciar esta vista en el visor. Descarga el HTML y ábrelo en tu navegador.",
);
html = html.replace("</body>", `<script>${result.outputFiles[0].text.replaceAll("</script", "<\\/script")}</script>\n</body>`);
const output = join(root, "paneles Yaiwes fromtend.revisar.html");
await writeFile(output, `<!-- Vista generada: editar los archivos fuente por separado. -->\n${html}`);
console.log(`Vista autónoma creada: ${output}`);
