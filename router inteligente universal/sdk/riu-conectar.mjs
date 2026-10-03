// riu-conectar.mjs — conecta cualquier agente Node al Router Inteligente Universal con solo su token. Sin dependencias (Node 18+).
//   import { Router } from "./riu-conectar.mjs";
//   const r = new Router("riu_...");            // o variable RIU_TOKEN
//   await r.chat("hola"); await r.memoriaGuardar("notas", "k1", {x: 1}); await r.espacioGuardar("a.md", "texto");
//   await r.seccion("mi-ficha", "entrada"); await r.yo();
// Mismo token: cliente OpenAI con baseURL=<puerta>/v1/router; MCP en <puerta>/mcp/ con Authorization: Bearer <token>.
export const PUERTA = "https://comand-center-1-claude-github-mcp-backup.hf.space";

export class Router {
  constructor(token = process.env.RIU_TOKEN, url = process.env.RIU_URL || PUERTA) {
    if (!token) throw new Error("Falta el token (new Router('riu_...') o variable RIU_TOKEN)");
    this.token = token;
    this.url = url.replace(/\/$/, "");
  }

  async call(method, path, body, raw) {
    const headers = { Authorization: `Bearer ${this.token}`, Accept: "application/json" };
    let data = raw;
    if (body !== undefined) { data = JSON.stringify(body); headers["Content-Type"] = "application/json"; }
    const res = await fetch(this.url + path, { method, headers, body: data });
    const text = await res.text();
    if (!res.ok) throw new Error(`${res.status} ${text.slice(0, 300)}`);
    return (res.headers.get("content-type") || "").includes("json") ? JSON.parse(text) : text;
  }

  yo() { return this.call("GET", "/tokens/yo"); }
  async chat(texto, model = "auto", system = "", max_tokens = 1024) {
    const messages = [...(system ? [{ role: "system", content: system }] : []), { role: "user", content: texto }];
    const out = await this.call("POST", "/v1/router/chat/completions", { model, messages, max_tokens });
    return out.choices[0].message.content;
  }
  memoriaGuardar(scope, key, data) { return this.call("POST", "/memoria/save", { scope, key, data }); }
  memoriaLeer(scope, key) { return this.call("GET", `/memoria/load?${new URLSearchParams({ scope, key })}`); }
  espacioGuardar(ruta, contenido) { return this.call("PUT", `/espacio/${encodeURIComponent(ruta)}`, undefined, contenido); }
  espacioLeer(ruta) { return this.call("GET", `/espacio/${encodeURIComponent(ruta)}`); }
  secciones() { return this.call("GET", "/secciones"); }
  seccion(nombre, input) { return this.call("POST", `/secciones/${encodeURIComponent(nombre)}/run`, { input }); }
  computo(command, flavor = "cpu-basic") { return this.call("POST", "/hf/compute/run", { command, flavor }); }
  terminal(comando, flavor = "cpu-basic") { return this.call("POST", "/terminal/run", { comando, flavor }); }
  openaiBaseURL() { return `${this.url}/v1/router`; }
  mcpConfig() { return { url: `${this.url}/mcp/`, headers: { Authorization: `Bearer ${this.token}` } }; }
}
