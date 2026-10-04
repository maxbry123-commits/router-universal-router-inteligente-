// Se corre UNA vez en tu dispositivo (telefono con Termux): OAuth oficial local y envio de la credencial protegida al puente.
// Uso: RIU_BANCO_CLAVE=... PUENTE_URL=https://.../chatgpt PUENTE_CLAVE=... node login-local.mjs [perfil]
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { homedir } from "node:os";
import { createChatGPT } from "@siwc/local";
import { cifradoBanco } from "./cifrado.mjs";
const perfil = process.argv[2] || "A";
const dir = join(homedir(), ".yaiwes-chatgpt", perfil);
const chatgpt = createChatGPT({ appName: "YAIWES Proyectos", appId: `yaiwes-proyectos-${perfil.toLowerCase()}`, redirectPort: 0,
  storageDir: dir, credentialEncryption: cifradoBanco(process.env.RIU_BANCO_CLAVE),
  openBrowser: (u) => console.log("\nAbre este enlace en el navegador de este mismo telefono:\n" + u + "\n") });
const s = await chatgpt.signIn();
if (s.status !== "connected" || !s.sharing) { console.error("No se autorizo el uso del plan:", s.error || s.status); process.exit(1); }
console.log("Sesion lista. Modelos:", (await chatgpt.listModels()).map(m => m.slug).join(", "));
const auth = JSON.parse(await readFile(join(dir, "chatgpt-auth.json"), "utf8")); // solo la credencial; el host ID local se queda aqui
const r = await fetch(`${process.env.PUENTE_URL}/perfiles/${perfil}/importar`, { method: "POST",
  headers: { "content-type": "application/json", "x-puente-clave": process.env.PUENTE_CLAVE }, body: JSON.stringify({ auth }) });
console.log("Puente:", r.status, await r.text());
