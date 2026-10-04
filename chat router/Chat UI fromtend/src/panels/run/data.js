// Datos portados de UI-YAIWES-Run.html. Se excluye deepseek-v3 por la regla del director (DeepSeek no es modelo de inferencia).
const RAW_MODELS=[
  ["grok-4","Grok 4","xAI"],
  ["grok-4-fast","Grok 4 Fast","xAI"],
  ["claude-sonnet","Claude Sonnet","Anthropic"],
  ["claude-opus","Claude Opus","Anthropic"],
  ["gpt-4.1","GPT-4.1","OpenAI"],
  ["qwen-coder","Qwen 2.5 Coder","Local"],
  ["deepseek-v3","DeepSeek V3","DeepSeek"],
  ["llama-3.3","Llama 3.3","Local"],
  ["hrm","HRM","Local"],
  ["custom","Custom / BYO","Custom"]
];
export const MODELS = RAW_MODELS.filter(m => !/deepseek/i.test(m[0] + " " + m[1] + " " + m[2]));
export const ROLES=[
  ["analyzer","Analyzer","Normaliza la tarea. No disena arquitectura.","ROL: Analyzer\nNo inventes nodos ni plantillas."],
  ["planner","Planner","Plan dentro de la plantilla fija.","ROL: Planner\nNo agregues nodos."],
  ["coder","Coder","Implementa. Sandbox obligatorio.","ROL: Coder\nEjecuta solo en el sandbox."],
  ["critic","Critic","Red team. Ataca la propuesta.","ROL: Critic\nBusca huecos. No propone DAG nuevo."],
  ["verifier","Verifier","Comprueba schema y evidencia.","ROL: Verifier\nFail closed si falta prueba."],
  ["judge","Judge","ACCEPT o REJECT.","ROL: Judge\nNunca improvisa DAG."],
  ["synthesizer","Synthesizer","Consolida al Output Schema.","ROL: Synthesizer\nProduce el paquete final."],
  ["sentinel","Sentinel","Bloquea transiciones no autorizadas.","ROL: Sentinel\nFail closed."],
  ["architect","Architect","Selecciona plantilla. No la inventa.","ROL: Architect\nSolo plantillas T01-T12."],
  ["researcher","Researcher","Solo fuentes del registry.","ROL: Researcher\nCita o UNKNOWN."],
  ["security","Security","Secretos solo por token_ref.","ROL: Security\nEnchufe Gate obligatorio."],
  ["custom","Custom","Rol libre. El DAG sigue bloqueado.","ROL: Custom\nNo mutes el DAG."]
];
export const DEST=[
  ["agent-api","Agent API","/api/agent/complete"],
  ["webhook","Webhook","https://hooks.example/cascade"],
  ["panel-run","Panel RUN","/api/ws/events"],
  ["filesystem","Filesystem","sandbox://out/result.json"]
];
export const PROC=[["V-01","sumar_uno",function(p){p.a=(p.x||0)+1;return p;}],["V-02","duplicar",function(p){p.b=(p.a||0)*2;return p;}],["V-03","validar",function(p){if(p.b==null) throw new Error("sin b"); p.ok=true;return p;}],["V-04","empaquetar",function(p){p.final=(p.b||0)+(p.x||0);return p;}]];
export const LIB={sumar1:function(p){p.x=(p.x||0)+1;return p;},doblar:function(p){p.x=(p.x||0)*2;return p;},mayus:function(p){p.msg=String(p.msg||"").toUpperCase();return p;},limpiar:function(p){p.msg=String(p.msg||"").trim();return p;},sellar:function(p){p.sello=String(p.x||"")+"-ok";return p;}};
export const DOCS=[["ACTA_DECISIONES.md","gobernanza"],["sequence.json","plan"],["LOTE_1A_fichas.md","fichas"],["providers.yaml","config"],["conexiones.yaml","mapa"],["CASCADE.yaml","dag"]];
export const NODOS=["boot","router","auth","cola","providers","gateway","bus","gcl","loops","witness","memoria","sentinel","runner","generador","fichas","frontend"];
export const role = id => ROLES.find(r => r[0] === id) || ROLES[ROLES.length - 1];
export const model = id => MODELS.find(r => r[0] === id) || MODELS[0];
export const dest = id => DEST.find(r => r[0] === id) || DEST[0];
const uid = () => "n" + Math.random().toString(36).slice(2, 8);
export function mkNode(roleId) {
  const r = role(roleId);
  return { id: uid(), modelId: "grok-4", roleId: r[0], label: r[1], prompt: r[3],
    input: '{"task":""}', output: '{"node":"' + r[0] + '","status":"ok"}',
    backend: "docker", timeout: 30, mem: 512, net: false, on: true, status: "idle" };
}
