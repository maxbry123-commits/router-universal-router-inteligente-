import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { transformSync } from "esbuild";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
let count = 0;
function check(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const file = join(directory, entry.name);
    if (entry.isDirectory()) check(file);
    else if (/\.(?:js|mjs)$/.test(entry.name)) {
      const result = spawnSync(process.execPath, ["--check", file], { stdio: "inherit" });
      if (result.status !== 0) process.exit(result.status || 1);
      count++;
    }
  }
}
for (const directory of ["src", "scripts", "tests"]) check(join(root, directory));
console.log(`${count} JavaScript modules checked.`);
for (const file of readdirSync(join(root, "styles"))) {
  if (!file.endsWith(".css")) continue;
  const result = transformSync(readFileSync(join(root, "styles", file), "utf8"), { loader: "css", logLevel: "silent" });
  if (result.warnings.length) throw new Error(JSON.stringify(result.warnings));
}
console.log("Stylesheets parsed without warnings.");
