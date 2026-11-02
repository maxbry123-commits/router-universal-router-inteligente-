// swe-directo.js — los modelos de SWE CODE / SWEN CODE free del selector responden por su router propio (el bridge), sin pasar por el Router MVP.
// El chat llama POST /v1/chat/completions del mismo origen (el proxy del Space manda web-* y swecode-* al bridge); mismo historial, misma sesion.
const REAL = { "hf-liquid-lfm25": "lfm2.5-350m", "swe-agent-lfm25": "lfm2.5-350m", "swe-openhands-lfm25": "lfm2.5-350m",
  "swe-codex-qwen25-15b": "qwen2.5-coder-1.5b", "hf-qwen25-coder-15b": "qwen2.5-coder-1.5b", "swe-opencode-qwen35-08b": "qwen3.5-0.8b", "hf-qwen35-08b": "qwen3.5-0.8b", "hf-qwen3-06b": "qwen3-0.6b" };  // los alias swe-* son ids viejos (solo para lo ya guardado): la lista ya no mezcla agentes con modelos
const LOCALES = ["lfm2.5-350m", "qwen2.5-coder-1.5b", "qwen3.5-0.8b", "qwen3-0.6b"];
const MAX_HISTORIAL = 20;  // mensajes previos: un modelo de 350M-1.5B o una UI web se desbordan con el chat entero

// Ventanas con el selector central: [id del modelo, etiqueta, descripcion]. SOLO nombres de modelo: el agente se elige en el selector central y
// los modos de SWEN (asesoria, revision...) son MODO DE TRABAJO (MODOS_TRABAJO), no modelos.
export const SWE_LISTAS = {
  "swe-code": { nombre: "SWE CODE", titulo: "SWE CODE · modelos locales (HF)", modelos: [
    ["hf-liquid-lfm25", "Liquid LFM2.5 350M", "HF local"],
    ["hf-qwen25-coder-15b", "Qwen2.5 Coder 1.5B", "HF local"],
    ["hf-qwen35-08b", "Qwen3.5 0.8B", "HF local"],
    ["hf-qwen3-06b", "Qwen3 0.6B", "HF local"]] },
  "swen-code-free": { nombre: "SWEN CODE free", titulo: "SWEN CODE free · cuentas web", modelos: [
    ["swecode-consulta", "Concilio · los 3 web", "los 3 modelos web a la vez + síntesis"],
    ["web-qwen38max", "Qwen 3.8 Max (web)", "Código complejo · via bridge"],
    ["web-qwen37max", "Qwen 3.7 Max (web)", "Razonamiento · via bridge"],
    ["web-dsv4-flash", "DeepSeek V4 Flash (web)", "Código rápido · via bridge"],
    ["hf-liquid-lfm25", "Liquid LFM2.5 350M", "HF local"],
    ["hf-qwen25-coder-15b", "Qwen2.5 Coder 1.5B", "HF local"],
    ["hf-qwen35-08b", "Qwen3.5 0.8B", "HF local"],
    ["hf-qwen3-06b", "Qwen3 0.6B", "HF local"],
    ["groq/qwen/qwen3.8-27b", "Qwen 3.8 Groq", "API Groq"],
    ["nvidia/minimaxai/minimax-m3.1-flash", "MiniMax M3.1 Flash", "API NVIDIA"],
    ["nvidia/meta/muse-glimmer-30b", "Muse Glimmer 30B", "API NVIDIA"],
    ["nvidia/nvidia/nemotron-3-ultra-550b-a55b", "Nemotron 3 Ultra", "API NVIDIA"],
    ["nvidia/z-ai/glm-5.3", "GLM 5.3", "API NVIDIA"],
    ["deepseek/deepseek-v4-pro", "DeepSeek V4 Pro", "API DeepSeek"],
    ["deepseek/deepseek-flash", "DeepSeek Flash", "API DeepSeek"],
    ["minimax/MiniMax-M3", "MiniMax M3", "API MiniMax"],
    ["minimax/MiniMax-M2.7", "MiniMax M2.7", "API MiniMax"],
    ["openai/gpt-5.6", "OpenAI GPT-5.6", "API OpenAI"],
    ["openai/gpt-5.5", "OpenAI GPT-5.5", "API OpenAI"]] },
};
// Modelos web de SWEN CODE free (cuentas web del bridge): no estan en el catalogo del Harness, solo sirven para el chat directo por el bridge.
export const MODELOS_WEB = [["swecode-consulta", "Concilio · los 3 web"], ["web-qwen38max", "Qwen 3.8 Max (web)"], ["web-qwen37max", "Qwen 3.7 Max (web)"], ["web-dsv4-flash", "DeepSeek V4 Flash (web)"]];
// MODO DE TRABAJO (antes «modelos» swecode-<modo>): el bridge ya acepta `modo` junto a cualquier modelo (server.js: conPreambulo). Vacio = sin modo.
export const MODOS_TRABAJO = [["asesoria", "Asesoría"], ["revision", "Revisión"], ["solucion", "Solución"], ["arquitectura", "Arquitectura"], ["archivos", "Archivos"], ["prompt_code", "Prompt code"], ["despliega", "Despliega"]];
export const esSelectorSwe = (id) => typeof id === "string" && Object.hasOwn(SWE_LISTAS, id);

export const esSwe = (id) => typeof id === "string" && (/^(web-|swecode-|groq\/|nvidia\/|deepseek\/|minimax\/|openai\/)/.test(id) || Object.hasOwn(REAL, id) || LOCALES.includes(id) || (id.startsWith("hf/") && LOCALES.includes(id.slice(3))));

// Salida de las tools (contrato externo `ejecutor_tools`): quien ejecuta los tool_calls. NO es un segundo control: se DERIVA de AGENTE QUE EJECUTA (agente_tool).
// 'openclaw' = el bridge devuelve los tool_calls tal cual a OpenClaw (seccion WAIT_TOOLS); cualquier otro agente = 'swe' (el SWE-agent via bridge/Harness, como hoy).
// Contrato en SWE CODE free/ARQUITECTURA.md. Viaja en cada peticion como `ejecutor_tools`; no hay key propia en localStorage.
export const EJECUTORES_TOOLS = ["swe", "openclaw"];
const normEjecutor = (v) => (EJECUTORES_TOOLS.includes(v) ? v : "swe");
export const ejecutorDeAgente = (agente) => (agente === "openclaw" ? "openclaw" : "swe");
export function leerEjecutorTools() { return ejecutorDeAgente(leerSeleccion().agente_tool); }

// ---- Selectores de agente/modelo/workflow (contrato TareaSWE de chat-router/agentes/adaptadores/contrato.py) ----
// Catalogo unico de agentes/adaptadores/modelos.py: el frontend solo lo refleja; el servidor valida y la disponibilidad real la reporta el Harness.
export const MODELOS_SWE = [
  ["hf/lfm2.5-350m", "Liquid LFM2.5 350M", "HF local"], ["hf/qwen2.5-coder-1.5b", "Qwen2.5 Coder 1.5B", "HF local"],
  ["hf/qwen3.5-0.8b", "Qwen3.5 0.8B", "HF local"], ["hf/qwen3-0.6b", "Qwen3 0.6B", "HF local"],
  ["groq/qwen/qwen3.8-27b", "Qwen 3.8 Groq", "API Groq"], ["nvidia/minimaxai/minimax-m3.1-flash", "MiniMax M3.1 Flash", "API NVIDIA"],
  ["nvidia/meta/muse-glimmer-30b", "Muse Glimmer 30B", "API NVIDIA"], ["nvidia/nvidia/nemotron-3-ultra-550b-a55b", "Nemotron 3 Ultra", "API NVIDIA"],
  ["nvidia/z-ai/glm-5.3", "GLM 5.3", "API NVIDIA"],
  ["deepseek/deepseek-v4-pro", "DeepSeek V4 Pro", "API DeepSeek"],
  ["deepseek/deepseek-flash", "DeepSeek Flash", "API DeepSeek"],
  ["minimax/MiniMax-M3", "MiniMax M3", "API MiniMax"],
  ["minimax/MiniMax-M2.7", "MiniMax M2.7", "API MiniMax"],
  ["openai/gpt-5.6", "OpenAI GPT-5.6", "API OpenAI"],
  ["openai/gpt-5.5", "OpenAI GPT-5.5", "API OpenAI"]];
export const AGENTES_SWE = [["openclaw", "OpenClaw"], ["swe-agent", "SWE-agent"], ["openhands", "OpenHands"], ["opencode", "OpenCode"], ["codex", "Codex"], ["claude-code", "Claude Code"]];
export const WORKFLOWS_SWE = [["individual", "Individual"], ["swe_code", "SWE CODE cuatro pasos"], ["liquid_mirror", "Liquid Mirror"]];
// Liquid Mirror: dos participantes propios (mismo modelo, servidores HF independientes), sin mezclar con los modelos web.
export const LIQUID_MIRROR = [{ id: "liquid1", etiqueta: "LIQUID 1 — LECTOR", servidor: "S2", modelo: "hf/lfm2.5-350m" }, { id: "liquid2", etiqueta: "LIQUID 2 — EJECUTOR", servidor: "S3", modelo: "hf/lfm2.5-350m" }];
const LIQUID = "hf/lfm2.5-350m", REVISOR = "hf/qwen3.5-0.8b", VERIFICADOR = "openhands";  // fijos del workflow SWE CODE (workflows.py)
export const SEL_DEFECTO = { modelo_responde: LIQUID, modelo_tool: "hf/qwen2.5-coder-1.5b", agente_responde: "openclaw", agente_tool: "swe-agent", modo_agentico: false, workflow: "individual", modo_trabajo: "" };
const K_SEL = "riu_swe_seleccion";
const en = (lista, v) => typeof v === "string" && lista.some((x) => x[0] === v);
function normSeleccion(x, base) {
  const o = x && typeof x === "object" ? x : {};
  return {
    modelo_responde: en(MODELOS_SWE, o.modelo_responde) || en(MODELOS_WEB, o.modelo_responde) ? o.modelo_responde : base.modelo_responde,  // los web-* solo sirven para el chat directo (validarSeleccion)
    modelo_tool: en(MODELOS_SWE, o.modelo_tool) ? o.modelo_tool : base.modelo_tool,
    agente_responde: en(AGENTES_SWE, o.agente_responde) ? o.agente_responde : base.agente_responde,
    agente_tool: en(AGENTES_SWE, o.agente_tool) ? o.agente_tool : base.agente_tool,
    modo_agentico: typeof o.modo_agentico === "boolean" ? o.modo_agentico : base.modo_agentico,
    workflow: en(WORKFLOWS_SWE, o.workflow) ? o.workflow : base.workflow,
    modo_trabajo: o.modo_trabajo === "" || en(MODOS_TRABAJO, o.modo_trabajo) ? o.modo_trabajo : base.modo_trabajo || "" };
}
export function leerSeleccion() { try { return normSeleccion(JSON.parse(localStorage.getItem(K_SEL) || "{}"), SEL_DEFECTO); } catch (e) { return { ...SEL_DEFECTO }; } }
function escribirSeleccion(sel) { try { localStorage.setItem(K_SEL, JSON.stringify(sel)); } catch (e) {} return sel; }
export function guardarSeleccion(parcial) {
  return escribirSeleccion(normSeleccion({ ...leerSeleccion(), ...(parcial && typeof parcial === "object" ? parcial : {}) }, leerSeleccion()));  // un valor invalido no pisa el anterior; cada campo es independiente (agente_tool, modelo_tool, modelo_responde); ejecutor_tools no se guarda: se deriva de agente_tool
}
export const requiereHarness = (sel) => !!sel && (sel.workflow !== "individual" || sel.modo_agentico === true);
// modelo del selector clasico (alias hf-*, ids locales, groq/, nvidia/) -> id del catalogo; null si no esta registrado (p. ej. web-*, swecode-*)
export function idCatalogo(id) {
  const real = Object.hasOwn(REAL, id) ? REAL[id] : id;
  if (LOCALES.includes(real)) return "hf/" + real;
  return en(MODELOS_SWE, id) ? id : null;
}
// Lo que el workflow elegido ya fija solo (workflows.py): SWE CODE usa modelos fijos por paso (el contrato modelo_responde/modelo_tool no influye) y su agente que responde no se usa;
// Liquid Mirror igual (el tool es siempre LIQUID 2). En Individual todo aplica. La hoja deshabilita y rotula «fijo por el workflow» estos controles.
export const camposFijos = (workflow) => new Set(workflow === "swe_code" || workflow === "liquid_mirror" ? ["modelo_responde", "agente_responde", "modelo_tool"] : []);
// id de la lista de la hoja (selector `lista`) equivalente al modelo del catalogo `cat` (desplegable «Responde»); conserva la entrada actual si ya equivale; null si la lista no lo tiene
export function entradaParaCatalogo(lista, cat, actual) {
  const l = SWE_LISTAS[lista]; if (!l) return null;
  if (actual && l.modelos.some((m) => m[0] === actual) && idCatalogo(actual) === cat) return actual;
  const m = l.modelos.find((x) => idCatalogo(x[0]) === cat);
  return m ? m[0] : null;
}
// Modelo que la hoja de `lista` envia cuando se elige `cat` (id del catalogo) en el desplegable «Responde»: la entrada de la lista si la hay;
// si la lista no lo trae, el id del bridge (hf/x -> x; groq/ y nvidia/ tal cual) con su etiqueta. Lo que muestra el desplegable es lo que se envia. null = fuera del catalogo.
export function modeloParaLista(lista, cat, actual) {
  const mid = entradaParaCatalogo(lista, cat, actual);
  if (mid) return { model_id: mid, label: SWE_LISTAS[lista].modelos.find((m) => m[0] === mid)[1] };
  if (!SWE_LISTAS[lista] || !en(MODELOS_SWE, cat)) return null;
  return { model_id: cat.startsWith("hf/") ? cat.slice(3) : cat, label: nombreDe(MODELOS_SWE, cat) };
}
// Lo guardado en localStorage (id de la lista o id del bridge elegido desde el desplegable) -> {model_id, label}; lo desconocido, la primera entrada
export function modeloGuardado(lista, guardado) {
  const l = SWE_LISTAS[lista], ent = l.modelos.find((x) => x[0] === guardado);
  if (ent) return { model_id: ent[0], label: ent[1] };
  const cat = typeof guardado === "string" ? idCatalogo(guardado) : null;
  return (cat && modeloParaLista(lista, cat, "")) || { model_id: l.modelos[0][0], label: l.modelos[0][1] };
}
export const AGENTE_CORTO = { codex: "Codex", opencode: "OpenCode", "swe-agent": "SWE-agent", openhands: "OpenHands", openclaw: "OpenClaw", "claude-code": "Claude Code" };
const ident = (v, defecto) => { const t = String(v == null ? "" : v).replace(/[^A-Za-z0-9_-]/g, "-").slice(0, 64); return t || defecto; };
export function nuevoTaskId() { return "yaiwes-" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8); }
export function armarTarea({ sel, mensaje, sesion, proyecto, task_id }) {
  const s = normSeleccion(sel, SEL_DEFECTO), lm = s.workflow === "liquid_mirror";
  return { task_id: task_id || nuevoTaskId(), origen: "yaiwes", workflow: s.workflow, mensaje: String(mensaje == null ? "" : mensaje),
    modelo_responde: s.modelo_responde, modelo_lector: LIQUID, modelo_tool: lm ? LIQUID : s.modelo_tool, modelo_revisor: REVISOR,
    agente_responde: s.agente_responde, agente_tool: s.agente_tool, agente_verificador: VERIFICADOR,
    modo_agentico: s.modo_agentico, aprobacion: false,  // la aprobacion NUNCA sale del cliente: la da el operador por /chat/swe/aprobar
    sesion: ident(sesion, ""), proyecto: ident(proyecto, "yaiwes") };
}

// Disponibilidad real: la reporta el Harness (GET /chat/swe/capacidades). Lo que no reporta NO se presenta como funcional.
export function normalizarCapacidades(p) {
  const o = p && typeof p === "object" ? p : {};
  const m = (x) => (x && typeof x === "object" ? x : {});
  return { harness: typeof o.harness === "string" ? o.harness : "desconocido", agentes: m(o.agentes), workflows: m(o.workflows), modelos: m(o.modelos) };
}
// Estados reales (instruccion 37). SIN VERIFICAR = la comprobacion no se pudo hacer o no dio un resultado firme: NUNCA se muestra como NO INSTALADO ni como DISPONIBLE.
export const ETIQUETA_ESTADO = { DISPONIBLE: "DISPONIBLE", NO_INSTALADO: "NO INSTALADO", NO_CONFIGURADO: "NO CONFIGURADO", NO_COMPATIBLE: "NO COMPATIBLE", NO_DISPONIBLE_PROVEEDOR: "NO DISPONIBLE EN PROVEEDOR", SIN_VERIFICAR: "SIN VERIFICAR" };
// el Harness puede decir el estado explicito (`estado`); si solo da {disponible, motivo} se deduce del motivo (disponibilidad.py nombra la causa)
const estadoDeMotivo = (tipo, motivo) => {
  if (/sin verificar|no se pudo comprobar|cache\)/i.test(motivo) && !/no est[aá] instalado|ausente del PATH/i.test(motivo)) return "SIN_VERIFICAR";
  if (/no est[aá] instalado|ausente del PATH|no instalad/i.test(motivo)) return "NO_INSTALADO";
  if (/incompatible|no compatible/i.test(motivo)) return "NO_COMPATIBLE";
  if (tipo === "modelo" && /no figura en GET \/models|no esta en el catalogo del proveedor|no publica|404/i.test(motivo)) return "NO_DISPONIBLE_PROVEEDOR";
  if (/sin configurar|instalado pero|\bfalta[n]?\b|invalida|no es un ejecutable|API_KEY|_URL|TOKEN|no responde en la URL/i.test(motivo)) return "NO_CONFIGURADO";
  return tipo === "modelo" ? "NO_DISPONIBLE_PROVEEDOR" : "SIN_VERIFICAR";
};
const sinHarness = (cap) => cap.harness !== "ok";
const motivoSinHarness = { sin_respuesta: "el Harness no respondió", sin_credencial: "falta la clave de acceso del chat", no_configurado: "el Harness no está configurado en el servidor", no_disponible: "el Harness no está disponible", desconocido: "el Harness no ha reportado" };
// `causa` del Harness: texto libre (se muestra tal cual) o CODIGO estable (disponibilidad.py). Un codigo se explica en claro: primero el `motivo` concreto del Harness, si no esta, este texto; nunca el codigo crudo.
export const CAUSAS = { binario_ausente: "el agente no está instalado en el servidor del Harness (falta su binario)", sdk_ausente: "el SDK del agente no está instalado en el servidor del Harness", python_no_ejecutable: "el Python del agente no es ejecutable en el servidor del Harness",
  falta_token_gateway: "falta el token del gateway de OpenClaw en el Harness", falta_pasarela: "falta configurar la pasarela del agente en el Harness", falta_docker: "falta Docker en el servidor del Harness", gateway_sin_respuesta: "el gateway no responde",
  servidor_hf_sin_respuesta: "ningún servidor HF responde ahora (un Space dormido tarda en arrancar)", dependencias: "faltan agentes conectados de los que depende", comprobacion_fallida: "no se pudo comprobar", url_invalida: "la URL configurada no es válida", sin_clave: "falta la clave en el Harness", verificacion_desactivada: "la verificación está desactivada" };
const causaLegible = (causa, motivo) => (/^[a-z][a-z0-9]*(_[a-z0-9]+)*$/.test(causa) ? motivo || CAUSAS[causa] || causa.replace(/_/g, " ") : causa || motivo);
export function estadoOpcion(cap, tipo, id, modelo) {
  const e = (tipo === "agente" ? cap.agentes : tipo === "workflow" ? cap.workflows : cap.modelos)[id];
  const txt = (v) => (typeof v === "string" && v ? v : "");
  const motivo = e ? causaLegible(txt(e.causa), txt(e.motivo)) : "";  // A5: `causa` concreta (sin credenciales); `motivo` es el formato anterior
  const r = (estado, m, ok = estado === "DISPONIBLE", extra = {}) => ({ ok, estado, motivo: m, elegible: ok || extra.elegible === true, ...extra });
  if (tipo === "workflow" && id === "individual") return r("DISPONIBLE", "");
  if (!e && sinHarness(cap)) return r("SIN_VERIFICAR", "sin verificar: " + (motivoSinHarness[cap.harness] || motivoSinHarness.desconocido) + (tipo === "agente" ? " (sin adaptador conectado que lo confirme)" : ""), tipo === "modelo");  // un modelo sin verificar no bloquea el chat normal; un agente/workflow si
  if (!e) return r("SIN_VERIFICAR", "sin verificar: el Harness no lo reporta", tipo === "modelo");
  const explicito = txt(e.estado).toUpperCase().replace(/[\s-]+/g, "_").replace("_EN_PROVEEDOR", "_PROVEEDOR"), intentable = e.intentable === true, nombre = txt(e.nombre);
  const extra = { ...(nombre ? { nombre } : {}), ...(e.verificado === false ? { verificado: false } : {}) };
  const sinVer = (m, okModelo) => r("SIN_VERIFICAR", m, okModelo, { ...extra, elegible: okModelo || intentable });  // intentable: se puede elegir con aviso y reintentar la verificacion (A5)
  if (Object.hasOwn(ETIQUETA_ESTADO, explicito)) {  // estado explicito del Harness (instruccion 37): manda sobre `disponible`
    if (explicito === "SIN_VERIFICAR") return sinVer(motivo || "sin verificar", tipo === "modelo");
    if (explicito !== "DISPONIBLE") return r(explicito, motivo || (tipo === "modelo" ? "no esta en el catalogo del proveedor" : "el Harness no lo reporta conectado"), false, extra);
    if (tipo === "agente" && modelo && Array.isArray(e.modelos) && !e.modelos.includes(modelo)) return r("NO_COMPATIBLE", "incompatible con " + modelo, false, extra);
    return r("DISPONIBLE", "", true, extra);
  }
  if (e.disponible === false) { const est = estadoDeMotivo(tipo, motivo); return est === "SIN_VERIFICAR" ? sinVer(motivo, tipo === "modelo") : r(est, motivo || (tipo === "modelo" ? "no esta en el catalogo del proveedor" : "el Harness no lo reporta conectado"), false, extra); }
  if (e.disponible !== true) return sinVer(motivo || "sin verificar: el Harness no dio un estado firme", tipo === "modelo");
  if (/sin verificar/i.test(motivo)) return r("SIN_VERIFICAR", motivo, true, { ...extra, elegible: true });
  if (tipo === "agente" && modelo && Array.isArray(e.modelos) && !e.modelos.includes(modelo)) return r("NO_COMPATIBLE", "incompatible con " + modelo, false, extra);
  return r("DISPONIBLE", "", true, extra);
}
// Hoja compacta: disponibles arriba; lo que no esta disponible se agrupa por su estado real y se muestra en UNA linea cada grupo, no como filas largas.
export function agruparOpciones(cap, tipo, lista, modelo) {
  const g = { ok: [], noInstalado: [], incompatible: [], sinVerificar: [], otros: [] };
  for (const [id, etq] of lista) {
    const st = estadoOpcion(cap, tipo, id, modelo), x = { id, etq: tipo === "modelo" && st.nombre ? st.nombre : etq, motivo: st.motivo, estado: st.estado, elegible: st.elegible };
    (st.ok ? g.ok : st.estado === "NO_INSTALADO" ? g.noInstalado : st.estado === "NO_COMPATIBLE" ? g.incompatible : st.estado === "SIN_VERIFICAR" ? g.sinVerificar : g.otros).push(x);
  }
  return g;
}
export const lineaNoInstalados = (g) => (g.noInstalado.length ? "No instalados: " + g.noInstalado.map((x) => x.etq).join(", ") : "");
export const lineaSinVerificar = (g) => (g.sinVerificar.length ? "Sin verificar: " + g.sinVerificar.map((x) => x.etq).join(", ") : "");
export const lineaOtros = (g) => (g.otros.length ? "No configurados / no disponibles: " + g.otros.map((x) => x.etq + " (" + ETIQUETA_ESTADO[x.estado].toLowerCase() + ")").join(", ") : "");
// MODELO QUE RESPONDE / PARA TOOL por ventana (25, 26): cada ventana muestra SOLO sus modelos; `proveedor` = {id: bool} del catalogo del Router (false = el proveedor no lo publica)
const SOLO = { "swe-code": (id) => id.startsWith("hf/"), groq: (id) => id.startsWith("groq/"), nvidia: (id) => id.startsWith("nvidia/"), "swen-code-free": () => true };
export const VENTANAS_CENTRAL = ["swe-code", "swen-code-free", "groq", "nvidia"];
export function opcionesModeloVentana(ventana, cap, proveedor = {}, { web = ventana === "swen-code-free" } = {}) {
  const lista = [...(web ? MODELOS_WEB : []), ...MODELOS_SWE.filter((m) => (SOLO[ventana] || SOLO["swen-code-free"])(m[0]))];
  return lista.map(([id, etq]) => {
    let st = estadoOpcion(cap, "modelo", id);
    const pv = proveedor ? proveedor[id] : undefined;  // false = el proveedor no lo publica; "NO_CONFIGURADO" / "SIN_VERIFICAR" = su catalogo no se pudo leer
    if (pv === false) st = { ok: false, elegible: false, estado: "NO_DISPONIBLE_PROVEEDOR", motivo: "el proveedor no publica el identificador seleccionado; no se sustituye por otro" };
    else if (pv === "NO_CONFIGURADO") st = { ok: false, elegible: false, estado: "NO_CONFIGURADO", motivo: id.startsWith("hf/") ? "ningún servidor local está configurado en el bridge" : "el banco del bridge no tiene clave para este proveedor" };
    else if (pv === true) st = { ok: true, elegible: true, estado: "DISPONIBLE", motivo: "" };  // GET /models del mismo bridge que hace inferencia, no del Harness de agentes
    else if (pv === "SIN_VERIFICAR") st = { ok: true, elegible: true, estado: "SIN_VERIFICAR", motivo: "el bridge no pudo verificar el catálogo; puedes intentar este modelo" };
    else if (pv === undefined && /^(groq\/|nvidia\/|hf\/)/.test(id)) {
      // El Harness enumera agentes, NO es autoridad sobre modelos del bridge.
      // Sin respuesta del bridge, habilitar solo intento directo, sin certificarlo como DISPONIBLE.
      st = { ok: true, elegible: true, estado: "SIN_VERIFICAR", motivo: "sin catálogo del bridge; modelo seleccionable para probar su conexión" };
    }
    const nom = st.nombre || etq;  // A5: el NOMBRE sale del catalogo del Harness cuando lo reporta (163)
    return { id, etq: nom + (st.estado === "DISPONIBLE" ? "" : " — " + ETIQUETA_ESTADO[st.estado]), nombre: nom, ok: st.ok, elegible: st.elegible !== false && (st.ok || st.elegible === true), estado: st.estado, motivo: st.motivo };
  });
}
const nombreDe = (lista, id) => (lista.find((x) => x[0] === id) || [id, id])[1];
export function validarSeleccion(sel, cap) {
  if (!requiereHarness(sel)) return { ok: true, problemas: [] };
  const problemas = [], plano = (m) => String(m).replace(/\s*\(([^()]*)\)/g, ": $1").replace(/[()]/g, ""), mal = (etq, r) => { if (!r.ok) problemas.push(etq + ": " + ETIQUETA_ESTADO[r.estado] + (r.motivo ? ", " + plano(r.motivo) : "")); };
  // SWE CODE cuatro pasos corre agentes (escribe/revisa/ejecuta/verifica) que solo se activan con el modo agentico (workflows.py: MODO_AGENTICO_APAGADO): se dice ANTES de crear la tarea
  if (sel.workflow === "swe_code" && !sel.modo_agentico) problemas.push("WORKFLOW " + nombreDe(WORKFLOWS_SWE, sel.workflow) + " exige MODO AGÉNTICO ON");
  mal("WORKFLOW " + nombreDe(WORKFLOWS_SWE, sel.workflow), estadoOpcion(cap, "workflow", sel.workflow));
  // agente_responde no lo usa ningun workflow del backend (plan_de: «responde» es un LLM sin agente) y modelo_responde solo cuenta en Individual (camposFijos): no se validan
  if (!camposFijos(sel.workflow).has("modelo_responde")) {
    if (en(MODELOS_WEB, sel.modelo_responde)) problemas.push("MODELO QUE RESPONDE " + nombreDe(MODELOS_WEB, sel.modelo_responde) + ": " + ETIQUETA_ESTADO.NO_COMPATIBLE + ", el contrato del Harness solo admite modelos del catálogo (elige uno HF, Groq o NVIDIA)");
    else mal("MODELO QUE RESPONDE " + nombreDe(MODELOS_SWE, sel.modelo_responde), estadoOpcion(cap, "modelo", sel.modelo_responde));
  }
  if (sel.modo_agentico) {
    const tool = sel.workflow === "liquid_mirror" ? LIQUID : sel.modelo_tool;
    mal("MODELO PARA TOOL " + nombreDe(MODELOS_SWE, tool), estadoOpcion(cap, "modelo", tool));
    mal("AGENTE QUE EJECUTA " + nombreDe(AGENTES_SWE, sel.agente_tool), estadoOpcion(cap, "agente", sel.agente_tool, tool));
    if (sel.workflow !== "individual") mal("AGENTE VERIFICADOR " + nombreDe(AGENTES_SWE, VERIFICADOR), estadoOpcion(cap, "agente", VERIFICADOR, LIQUID));
  }
  return { ok: problemas.length === 0, problemas };
}
let _cap = { t: 0, v: null };
const capVigente = () => !!_cap.v && Date.now() - _cap.t < 30000;
export const olvidarCapacidades = () => { _cap = { t: 0, v: null }; };
export async function cargarCapacidades(api, { forzar = false } = {}) {
  if (!forzar && capVigente()) return _cap.v;
  let v;
  try { v = normalizarCapacidades(await api("/chat/swe/capacidades")); } catch (e) { v = normalizarCapacidades(null); v.harness = "sin_respuesta"; }
  _cap = { t: Date.now(), v };
  return v;
}

// ---- Tarea SWE: el frontend manda el contrato al backend YAIWES (/chat/swe/*), este al Harness, este a los adaptadores. Nunca llama a una herramienta directo. ----
// Parar de avanzar: DONE (hecho), GAP (fallo sin efectos), REQUIERE_APROBACION (espera al operador) y RECONCILIAR (operacion iniciada sin confirmar: la verifica un operador).
const TERMINALES = ["DONE", "GAP", "REQUIERE_APROBACION", "RECONCILIAR"];
export const MAX_AVANCES = 24;
const PARA_CHATEAR = "Para chatear: abre SWE CODE/SWEN → Agentes → Modo agéntico OFF y Workflow Individual";
const PARA_AGENTICO = "Enciende SWE CODE/SWEN → Agentes → Modo agéntico ON, o elige Workflow Individual";
const TASK_RE = /^[A-Za-z0-9_-]{1,64}$/, OP_RE = /^[A-Za-z0-9_-]{1,80}$/;
const resultadoDe = (r, op) => {
  const x = r && r.ok === true ? r.resultado : null;
  if (!x || typeof x !== "object") throw new Error("GAP: SWE_HARNESS_ERROR · " + op + " sin resultado");
  return x;
};
const DETENIDO = "PROCESO_DETENIDO";
async function operacion(api, op, cuerpo, signal, headers) {
  let r;
  try { r = await api("/chat/swe/" + op, { method: "POST", body: cuerpo, ...(signal ? { signal } : {}), ...(headers ? { headers } : {}) }); } catch (e) { const m = String((e && e.message) || e); if (m === DETENIDO) throw new Error(DETENIDO); const g = new Error(m.startsWith("GAP:") ? m : "GAP: " + (/^[A-Z][A-Z0-9_]+\b/.test(m) ? m : "SWE_HARNESS_ERROR · " + m)); if (e && e.status) g.status = e.status; throw g; }
  return resultadoDe(r, op);
}
const base = ({ task_id, sesion, proyecto }) => {
  if (!TASK_RE.test(String(task_id))) throw new Error("GAP: TASK_ID_INVALIDO");
  return { task_id, origen: "yaiwes", sesion: ident(sesion, ""), proyecto: ident(proyecto, "yaiwes") };
};
export const estadoTareaSwe = async (api, d) => operacion(api, "estado", base(d), d.signal);
export const reanudarTareaSwe = async (api, d) => operacion(api, "reanudar", base(d), d.signal);
export const aprobarTareaSwe = async (api, d) => {  // quien aprueba es el operador autenticado en el servidor, no un campo del cuerpo; op_id = la operacion que el Harness dejo pendiente
  if (typeof d.op_id !== "string" || !OP_RE.test(d.op_id)) throw new Error("GAP: OP_ID_INVALIDO");
  return operacion(api, "aprobar", { ...base(d), op_id: d.op_id }, d.signal, d.headers);  // d.headers = x-operador / x-operator-token de quien aprueba: solo cabeceras de ESTA peticion
};
const lineaEvidencia = (e) => (typeof e === "string" ? e : JSON.stringify(e)).slice(0, 300);
const texto = (v) => (typeof v === "string" ? v : v == null ? "" : JSON.stringify(v));
// El Harness devuelve la "vista" de la tarea: estado, paso_actual, plan, pasos_terminados[{paso,agente,servidor,recibo,resultado,herramientas,evidencias}], resultado_tool, evidencia[], pendiente_aprobacion, error{codigo,mensaje}.
function aRespuesta(x, tarea) {
  const estado = String(x.estado || ""), pasos = Array.isArray(x.pasos_terminados) ? x.pasos_terminados.filter((p) => p && typeof p === "object") : [];
  const idTarea = x.task_id || tarea.task_id;
  if (estado === "GAP") { const e = x.error && typeof x.error === "object" ? x.error : { codigo: x.codigo, mensaje: x.error }; throw new Error("GAP: " + (e.codigo || "GAP") + (e.mensaje ? " · " + texto(e.mensaje) : "")); }
  if (estado === "RECONCILIAR") { const r = x.pendiente_reconciliacion || {}; throw new Error("GAP: RECONCILIAR · la operación " + (r.op_id || "?") + " (" + (r.paso || "?") + ") quedó iniciada sin confirmar" + (r.motivo ? " (" + r.motivo + ")" : "") + ": un operador debe verificar su estado real antes de reanudar la tarea " + idTarea); }
  const pide = estado === "REQUIERE_APROBACION", pend = pide && x.pendiente_aprobacion && typeof x.pendiente_aprobacion === "object" ? x.pendiente_aprobacion : null;
  const final = x.resultado_tool || x.texto || x.resultado || x.reply || (pasos.length ? pasos[pasos.length - 1].resultado : "");
  const evid = [...(Array.isArray(x.evidencia) ? x.evidencia : []), ...(Array.isArray(x.evidencias) ? x.evidencias : [])].map(lineaEvidencia);
  pasos.filter((p) => p.recibo).forEach((p) => evid.push("recibo " + p.paso + " (" + (p.servidor || p.agente || "?") + "): " + p.recibo));
  const permisos = pend && pend.permisos ? Object.keys(pend.permisos).filter((k) => pend.permisos[k]).join(" y ") : "";
  const cabecera = pend ? "Requiere aprobación del operador: paso " + pend.paso + " con " + pend.agente + " (" + pend.modelo + ")" + (permisos ? " · " + permisos : "") + (pend.objetivo ? "\n" + texto(pend.objetivo) : "") : pide ? "Requiere aprobación del operador antes de continuar." : "";
  const reply = [cabecera, texto(final), evid.length ? "Evidencias:\n" + evid.map((e) => "- " + e).join("\n") : ""].filter(Boolean).join("\n\n");
  const tools = [...new Set(pasos.flatMap((p) => (Array.isArray(p.herramientas) ? p.herramientas : []).map((h) => (typeof h === "string" ? h : (h && h.nombre) || "tool"))))];
  return { reply, tools, finish_reason: estado === "DONE" ? "stop" : null, estado, task_id: idTarea, requiere_aprobacion: pide, pendiente: pend,
    nota: `SWE · ${tarea.workflow} · ${tarea.agente_responde}→${tarea.agente_tool} · tarea ${idTarea} · ${estado || "?"}${x.ejecucion_s2_s3 ? " · S2/S3 " + x.ejecucion_s2_s3 : ""}` };
}
const textoPaso = (x) => { const plan = Array.isArray(x.plan) ? x.plan : [], p = plan[x.paso_actual] || plan[plan.length - 1]; return "SWE · " + (x.estado || "?") + (p && p.paso ? " · " + p.paso : "") + (Number.isInteger(x.paso_actual) && plan.length ? " (" + Math.min(x.paso_actual + 1, plan.length) + "/" + plan.length + ")" : ""); };
// ctl = { parar, signal }: Detener = parar y esperar. parar() se consulta antes de cada paso (no se llama a avanzar tras Detener) y signal aborta la peticion en vuelo.
const alto = (ctl) => { if (ctl && ((typeof ctl.parar === "function" && ctl.parar()) || (ctl.signal && ctl.signal.aborted))) throw new Error(DETENIDO); };
async function conducir(api, x, tarea, alPaso, ctl = {}) {  // avanza paso a paso (el estado se guarda en el Harness en cada paso) hasta un estado terminal o de aprobacion
  const ref = { task_id: tarea.task_id, origen: "yaiwes", sesion: tarea.sesion, proyecto: tarea.proyecto }, avisa = (v) => { try { if (alPaso) alPaso(textoPaso(v), v); } catch (e) {} };
  avisa(x);
  for (let i = 0; i < MAX_AVANCES && !TERMINALES.includes(String(x.estado)); i++) { alto(ctl); x = await operacion(api, "avanzar", ref, ctl.signal); avisa(x); }
  if (!TERMINALES.includes(String(x.estado))) throw new Error("GAP: SWE_SIN_PROGRESO · la tarea " + tarea.task_id + " sigue en " + (x.estado || "?") + "; reanúdala con el mismo task_id");
  return aRespuesta(x, tarea);
}
export async function enviarTareaSwe(api, { mensaje, sesion, proyecto, task_id, alPaso, parar, signal }) {
  const ctl = { parar, signal };
  alto(ctl);
  const sel = leerSeleccion(), enCache = capVigente();
  let v = validarSeleccion(sel, await cargarCapacidades(api));
  if (!v.ok && enCache) v = validarSeleccion(sel, await cargarCapacidades(api, { forzar: true }));  // un "no disponible" viejo no se queda pegado: se vuelve a preguntar al Harness
  if (!v.ok) throw new Error("GAP: SELECCION_NO_DISPONIBLE · " + v.problemas.join(" · ") + ". " + (v.problemas.some((p) => /exige MODO AGÉNTICO ON/.test(p)) ? PARA_AGENTICO : PARA_CHATEAR));  // no se cambia en silencio a otro modelo ni agente
  const tarea = armarTarea({ sel, mensaje, sesion, proyecto, task_id });
  alto(ctl);
  return conducir(api, await operacion(api, "iniciar", tarea, signal), tarea, alPaso, ctl);
}
// el operador pulsa Aprobar: el servidor lo identifica; despues la tarea sigue desde su ultimo checkpoint (mismo task_id)
export async function aprobarYContinuarSwe(api, d, alPaso) {
  const tarea = armarTarea({ sel: leerSeleccion(), mensaje: "(continuación)", sesion: d.sesion, proyecto: d.proyecto, task_id: base(d).task_id });
  return conducir(api, await aprobarTareaSwe(api, d), tarea, alPaso, { parar: d.parar, signal: d.signal });
}

export function armar({ model, historial = [], mensaje, sesion, proyecto, ejecutor_tools, modo, tools = false, agente_tool = false, llm_tool = false }) {
  const h = historial.slice(-MAX_HISTORIAL);
  const m = modo === undefined ? leerSeleccion().modo_trabajo : modo, mt = en(MODOS_TRABAJO, m) ? m : "";  // MODO DE TRABAJO: `modo` junto al modelo; Concilio lleva el modo en el id (swecode-<modo>)
  const real = Object.hasOwn(REAL, model) ? REAL[model]
    : typeof model === "string" && model.startsWith("hf/") && LOCALES.includes(model.slice(3)) ? model.slice(3) : model;
  // R1: el navegador NUNCA guarda ni reenvia claves de API: el banco cifrado del servidor es la unica fuente (swe-claves.js solo informa su estado)
  return { model: mt && real === "swecode-consulta" ? "swecode-" + mt : real, messages: [...h, { role: "user", content: mensaje }], conv_id: sesion, stream: true, tools: tools === true, agente_tool: agente_tool === true, llm_tool: llm_tool === true, ejecutor_tools: ejecutor_tools === undefined ? leerEjecutorTools() : normEjecutor(ejecutor_tools), ...(mt && real !== "swecode-consulta" ? { modo: mt } : {}), ...(proyecto ? { proyecto } : {}) };
}

// El proxy del Space solo manda /v1/* al bridge si el modelo empieza por web-/swecode-; el resto (locales HF, groq/, nvidia/) caeria en el Router
// (400 MODEL_NOT_IN_CERTIFIED_REGISTRY). /web/* va SIEMPRE al bridge (igual que /web/v1/claves): por ahi viajan los demas ids.
// Todos los modelos entran por Harness DeepSeek, que decide Router MVP (API)
// o Router SWE CODE (HF/local/web) por HTTP. Nunca conectar la UI directamente a /web.
export const rutaSwe = (_id) => "/plugins/deepseek_harness/modelos/v1/chat/completions";

// ---- Streaming SSE (bridge): lector tolerante a CRLF, comentarios (": keepalive"), eventos partidos entre chunks y lineas data: multiples ----
export async function leerSSE(response, alEvento, signal) {
  const detenido = () => !!(signal && signal.aborted);
  const rd = response.body && typeof response.body.getReader === "function" ? response.body.getReader() : null;
  const dec = new TextDecoder("utf-8");
  let buf = "", pend = "", fin = false;
  const evento = (bloque) => {
    const datos = [];
    for (const linea of bloque.split("\n")) {
      if (!linea || linea[0] === ":") continue;  // comentario / keepalive
      const m = linea.match(/^data:?(.*)$/);
      if (m) datos.push(m[1].startsWith(" ") ? m[1].slice(1) : m[1]);
    }
    if (!datos.length) return;
    const t = datos.join("\n");
    if (t.trim() === "[DONE]") { fin = true; return; }
    let o; try { o = JSON.parse(t); } catch (e) { return; }  // un evento roto no tumba el resto
    alEvento(o);
  };
  const consumir = (texto, final) => {
    texto = pend + texto; pend = "";
    if (!final && texto.endsWith("\r")) { pend = "\r"; texto = texto.slice(0, -1); }  // un \r\n partido entre chunks no se cuenta como dos saltos
    buf += texto.replace(/\r\n?/g, "\n");
    let i;
    while ((i = buf.indexOf("\n\n")) >= 0) { const b = buf.slice(0, i); buf = buf.slice(i + 2); evento(b); }
    if (final && buf.trim()) { const b = buf; buf = ""; evento(b); }
  };
  if (!rd) { consumir(await response.text(), true); return { fin }; }
  const cortar = () => { try { rd.cancel().catch(() => {}); } catch (e) {} };
  if (signal) { if (signal.aborted) cortar(); else signal.addEventListener("abort", cortar, { once: true }); }
  try {
    for (;;) {
      if (detenido()) throw new Error(DETENIDO);
      let r;
      try { r = await rd.read(); } catch (e) { if (detenido()) throw new Error(DETENIDO); throw e; }
      if (r.done) break;
      consumir(dec.decode(r.value, { stream: true }), false);
      if (detenido()) throw new Error(DETENIDO);
    }
    consumir(dec.decode(), true);
  } finally { if (signal) signal.removeEventListener("abort", cortar); }
  if (detenido()) throw new Error(DETENIDO);
  return { fin };
}
// junta los chat.completion.chunk en la misma forma que el JSON de /v1/chat/completions
async function respuestaDeSSE(response, datos) {
  const a = { texto: "", llamadas: [], fin: null, error: null, extra: {} };
  const { fin: hecho } = await leerSSE(response, (o) => {
    if (!o || typeof o !== "object") return;
    for (const k of ["modelo_usado", "via_respaldo", "via_primaria"]) if (typeof o[k] === "string") a.extra[k] = o[k];
    if (o.error && typeof o.error === "object") a.error = o.error;
    const c = Array.isArray(o.choices) ? o.choices[0] : null;
    if (!c || typeof c !== "object") return;
    const d = c.delta && typeof c.delta === "object" ? c.delta : {};
    if (typeof d.content === "string" && d.content) { a.texto += d.content; if (typeof datos.alParcial === "function") { try { datos.alParcial(a.texto); } catch (e) {} } }
    for (const tc of Array.isArray(d.tool_calls) ? d.tool_calls : []) {
      if (!tc || typeof tc !== "object") continue;
      const idx = Number.isInteger(tc.index) ? tc.index : a.llamadas.length;
      const slot = (a.llamadas[idx] = a.llamadas[idx] || { id: tc.id, type: "function", function: { name: "", arguments: "" } });
      if (tc.id && !slot.id) slot.id = tc.id;
      if (tc.function && typeof tc.function.name === "string" && tc.function.name) slot.function.name = tc.function.name;
      if (tc.function && typeof tc.function.arguments === "string") slot.function.arguments += tc.function.arguments;
    }
    if (c.finish_reason) a.fin = c.finish_reason;
  }, datos.signal);
  if (a.fin === "error" && !a.error) a.error = { code: "STREAM_ERROR", message: "el servidor cerró el stream con error" };
  if (!a.error && !a.fin && !hecho && (a.texto || a.llamadas.length)) a.error = { code: "STREAM_CORTADO", message: "el stream terminó sin finish_reason" };
  return { ...a.extra, ...(a.error ? { error: a.error } : {}), choices: [{ message: { content: a.texto, ...(a.llamadas.length ? { tool_calls: a.llamadas.filter(Boolean) } : {}) }, finish_reason: a.error ? "error" : a.fin }] };
}

export async function enviarSwe(api, datos) {
  const cuerpo = armar(datos), opc = { method: "POST", body: cuerpo, sse: true };
  if (datos.signal) opc.signal = datos.signal;
  let r = await api(rutaSwe(datos.model), opc);
  if (r && r.__sse) r = await respuestaDeSSE(r.__sse, datos);  // si el servidor respondio JSON normal, r ya es el JSON: camino de siempre
  const msg = (r && r.choices && r.choices[0] && r.choices[0].message) || {};
  const llamadas = Array.isArray(msg.tool_calls) ? msg.tool_calls.filter(Boolean) : [];
  // R4: una respuesta con tool_calls (con o sin texto) NUNCA pierde las llamadas pendientes: las ejecuta el cliente (OpenClaw) o el SWE-agent, no es un fallo
  const nombres = llamadas.map((t) => (t && t.function && t.function.name) || "tool"), quien = cuerpo.ejecutor_tools === "openclaw" ? "OpenClaw" : "SWE-agent";
  if (!msg.content && llamadas.length) return { reply: "Tools pedidas: " + nombres.join(", "), tools: [], pedidas: nombres, tool_calls: llamadas, ejecutor: quien, finish_reason: r.choices[0].finish_reason || "tool_calls", nota: `SWE · ${r.modelo_usado || datos.model} · tools → ${quien}` };
  const texto = msg.content;
  if (!texto) {  // un fallo no se pinta como respuesta del modelo (entraria al historial del turno siguiente)
    const e = (r && r.error) || {};
    throw new Error("GAP: " + (e.code || "SIN_RESPUESTA") + (e.message ? " · " + e.message : ""));
  }
  const via = r.via_respaldo ? ` · respondió ${r.via_respaldo}` : r.via_primaria ? ` · vía ${r.via_primaria}` : "";
  if (r.error && r.choices[0].finish_reason === "error") {  // stream cortado con texto ya entregado: se conserva lo recibido y el corte se dice en la nota (no se da por completo)
    return { reply: texto, tools: [], ...(llamadas.length ? { pedidas: nombres, tool_calls: llamadas, ejecutor: quien } : {}), finish_reason: "error", nota: `SWE · ${r.modelo_usado || datos.model}${via} · GAP: ${r.error.code || "STREAM_ERROR"}${r.error.message ? " · " + r.error.message : ""} (respuesta parcial)` };
  }
  return { reply: texto, tools: [], ...(llamadas.length ? { pedidas: nombres, tool_calls: llamadas, ejecutor: quien } : {}), finish_reason: r.choices[0].finish_reason || (llamadas.length ? "tool_calls" : null), nota: `SWE · ${r.modelo_usado || datos.model}${via}${llamadas.length ? " · tools → " + quien : ""}` };
}

