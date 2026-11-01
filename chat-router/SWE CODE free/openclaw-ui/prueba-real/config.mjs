// prueba-real/config.mjs — genera el openclaw.json del Gateway de PRUEBA a partir de provider-openclaw.json (mismo baseUrl, api_key "${RIU_API_KEY}" y ids exactos).
// node config.mjs <salida.json> <workspace>   (el Gateway sustituye ${RIU_API_KEY} desde su entorno; nunca se escribe el valor)
import fs from 'node:fs'; import path from 'node:path'; import { fileURLToPath } from 'node:url';
const p = JSON.parse(fs.readFileSync(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../provider-openclaw.json'), 'utf8'));
const [salida, ws] = process.argv.slice(2);
const cfg = {
  gateway: { mode: 'local', port: 18790, bind: 'loopback', auth: { mode: 'token', token: 'gw-token-test' }, http: { endpoints: { chatCompletions: { enabled: true } } } },
  models: { mode: 'merge', providers: { [p.provider]: { baseUrl: p.base_url, apiKey: p.api_key, api: 'openai-completions',
    models: p.modelos.map((m) => ({ id: m.id, name: m.nombre, reasoning: false, input: ['text'], contextWindow: 262144, maxTokens: 8192 })) } } },  // contextWindow: lo fija OpenClaw, no el provider (con 32k las ~60 tools directas desbordan)
  agents: { defaults: { workspace: ws, model: { primary: 'swecode/lfm2.5-350m' } } },
  plugins: { allow: ['swe-selector'] },  // el plugin se instala desde archivo local (provenance-invalid): sin allow no carga sus tools
  tools: { toolSearch: false },          // tools directas (sin tool_search/tool_call) para ver los nombres yaiwes_* en la peticion al modelo
};
fs.writeFileSync(salida, JSON.stringify(cfg, null, 2));
console.log(`${salida}: ${cfg.models.providers.swecode.models.length} modelos, baseUrl ${p.base_url}, apiKey ${p.api_key}`);
