// orquestador.js — "Chat BOTS": seccion debajo del chat abierto (como Chat 1/2/3). Cada agente es un sub-chat aislado
// (hilo, system, memoria, archivos y sandbox propios), max 50 por seccion. Antonio les escribe desde aqui.
// Backend: plugin orquestador; LLM por HTTP al harness puente_chat. Cambio quirurgico: solo inserta #chat-bots debajo del chat (despues de #composer).
import { accion } from "./api.js";
import { crearCola, marcarEnCola, devolverACaja } from "./cola-envio.js";
const el = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
const btn = (txt, cls, fn, id) => { const b = el("button", cls || "secondary", txt); b.type = "button"; if (id) b.id = id; b.onclick = fn; return b; };
const ESTADO_TXT = { activo: "Activo", trabajando: "Trabajando", bloqueado: "Bloqueado", aprobacion: "Necesita aprobación", terminado: "Terminado", error: "Error" };
const fmt = (ms) => Math.floor(ms / 1000) + " s " + String(ms % 1000).padStart(3, "0") + " ms";
let MODELOS = [], AGENTES = [], SEL = null, timer = null, SECCION = "";
// escribir sin esperar: mientras el agente trabaja la caja sigue libre; lo enviado queda "en cola" (por agente) y sale en orden cuando termina
// (el plugin acepta un turno por agente: AGENTE_OCUPADO). pintar() redibuja el panel, así que la cola guarda solo textos.
const COLAS = {}, ENVIANDO = {};
const ocupadoAg = (id) => !!ENVIANDO[id] || (AGENTES.find((a) => a.id === id) || {}).estado === "trabajando";
const colaDe = (id) => COLAS[id] || (COLAS[id] = crearCola({ ocupado: () => ocupadoAg(id), enviar: (x) => { enviarYa(id, x.texto); } }));
async function enviarYa(id, t) {
  ENVIANDO[id] = true; let r = {};
  try { r = await orq("enviar", { id, mensaje: t }); } catch (x) { r = { error: x.message }; }
  ENVIANDO[id] = false;
  if (r.error === "AGENTE_OCUPADO") colaDe(id).items.unshift({ texto: t });  // seguía ocupado: vuelve al frente de la cola, no se pierde
  else if (r.error) alert(r.error);
  await refrescar();
}

async function orq(acc, payload) {
  let base = ""; try { base = localStorage.getItem("riu_orq_base") || ""; } catch (e) {}
  if (!base) { await accion("status", {}).catch(() => {}); base = (window.RIU_CONFIG?.harnessUrl || "").replace(/\/plugins\/puente_chat\/call\/?$/, ""); }
  const h = { "Content-Type": "application/json" }; const pw = sessionStorage.getItem("riu_clave"); if (pw) h["X-API-Key"] = pw;
  const ac = new AbortController(); const t = setTimeout(() => ac.abort(), /chat_crear|ejecutar|deploy/.test(acc) ? 300000 : 20000);
  try {
    const r = await fetch(base.replace(/\/+$/, "") + "/plugins/orquestador/call/" + acc, { method: "POST", headers: h, body: JSON.stringify(Object.assign({ seccion: SECCION }, payload || {})), signal: ac.signal });
    const env = await r.json().catch(() => ({}));
    if (!r.ok || env.status !== "ok") throw new Error(env.reason || env.detail || ("HTTP " + r.status));
    return env.result || {};
  } finally { clearTimeout(t); }
}
// seccion = sesion del chat abierto (chip activo "Chat N — sesión X")
const seccionActiva = () => { const on = document.querySelector("#chat-tabs .chip.on"); const m = /sesión\s+(\S+)/.exec(on?.title || ""); return m ? m[1] : (sessionStorage.getItem("riu_sesion") || "web-general"); };
const selModelo = (val, id) => { const s = el("select"); if (id) s.id = id; MODELOS.forEach((m) => s.append(new Option(m.nombre, m.id))); if (val) s.value = val; return s; };
const sem = (estado, id) => { const i = el("i", "orq-sem " + estado); if (id) i.id = id; i.dataset.estado = estado; i.title = ESTADO_TXT[estado]; return i; };

function tira() {
  const bar = el("div", "bots-tira"); bar.id = "bots-tira";
  bar.append(el("span", "bots-tit", "🤖 Chat BOTS " + AGENTES.length + "/50"));
  AGENTES.forEach((a) => {
    const b = el("button", "chip bot-chip" + (SEL === a.id ? " on" : "")); b.type = "button"; b.dataset.id = a.id; b.title = a.nombre + " · " + ESTADO_TXT[a.estado];
    b.append(el("span", "", a.icono || "🤖"), sem(a.estado), el("span", "bot-n", a.nombre)); b.onclick = () => abrir(SEL === a.id ? null : a.id); bar.append(b);
  });
  const add = btn("＋", "chip", () => abrir("nuevo"), "bots-nuevo"); add.title = "Nuevo agente / mirror"; bar.append(add);
  return bar;
}

function formNuevo() {
  const f = el("div", "orq-sec"); f.id = "orq-form-nuevo";
  const nom = el("input"); nom.placeholder = "Nombre del agente"; nom.id = "orq-n-nombre";
  const sis = el("textarea"); sis.rows = 2; sis.placeholder = "Instrucciones / system del agente"; sis.id = "orq-n-sistema";
  const mod = selModelo("ficha-qwen38flash", "orq-n-modelo");
  const crear = btn("Crear", "action", async () => { crear.disabled = true; try { const r = await orq("crear", { nombre: nom.value, sistema: sis.value, modelo: mod.value }); if (r.error) throw new Error(r.error); SEL = r.agente.id; await refrescar(); } catch (x) { alert(x.message); crear.disabled = false; } }, "orq-n-crear");
  const ped = el("input"); ped.placeholder = "Pídele a la LLM del chat que cree un agente…"; ped.id = "orq-llm-pedido";
  const llm = btn("🧠 Crear con LLM", "secondary", async () => { llm.disabled = true; llm.textContent = "🧠 pensando…"; try { const r = await orq("chat_crear", { pedido: ped.value }); if (r.error) throw new Error(r.error + " " + (r.detalle || "")); SEL = r.agente.id; await refrescar(); } catch (x) { alert(x.message); } llm.disabled = false; llm.textContent = "🧠 Crear con LLM"; }, "orq-llm-crear");
  const mirSel = el("select"); mirSel.id = "orq-mirror-de"; mirSel.append(new Option("Mirror del chat abierto", "chat")); AGENTES.forEach((a) => mirSel.append(new Option("Mirror de " + a.nombre, a.id)));
  const r1 = el("div", "orq-row"); r1.append(ped, llm);
  const r2 = el("div", "orq-row"); r2.append(mirSel, btn("🪞 Añadir mirror", "secondary", () => mirror(mirSel.value), "orq-mirror-crear"));
  f.append(el("strong", "", "Nuevo agente"), nom, sis, el("div", "muted", "Modelo (ficha 4)"), mod, crear, el("strong", "", "La LLM del chat lo crea (tool crear_agente)"), r1, el("strong", "", "Mirror (copia que trabaja en paralelo)"), r2);
  return f;
}

async function mirror(de) {
  const p = { de };
  if (de === "chat") { const h = [...document.querySelectorAll("#histories .chat-history:not([hidden]) > *")].slice(-12); p.mensajes = h.map((m) => ({ role: /user|usuario|yo/.test(m.className) ? "user" : "assistant", content: (m.innerText || "").slice(0, 3000) })).filter((m) => m.content); }
  const r = await orq("mirror", p); if (r.error) { alert(r.error); return; } SEL = r.agente.id; await refrescar();
}

function seccion(a) {
  const s = el("div", "orq-sec"); s.id = "orq-sec"; s.dataset.id = a.id;
  const h = el("div", "orq-head");
  const mod = selModelo(a.modelo, "orq-modelo"); mod.title = "Modelo de la ficha 4 que usa este agente";
  mod.onchange = async () => { const r = await orq("configurar", { id: a.id, modelo: mod.value }); if (r.error) alert(r.error); refrescar(); };
  h.append(el("span", "", a.icono), el("strong", "", a.nombre), sem(a.estado, "orq-sem"), el("span", "orq-badge", ESTADO_TXT[a.estado]), mod, btn("✕", "secondary", () => abrir(null), "orq-cerrar"));
  const info = el("div", "muted", "Hace: " + (a.sistema || "agente general").slice(0, 140) + " · memoria " + a.memoria_id + " · " + (a.archivos || []).length + " archivos · creado por " + a.creado_por + (a.origen ? " · mirror de " + a.origen : "") + (a.latencia_ms ? " · última respuesta " + fmt(a.latencia_ms) : ""));
  info.id = "orq-info";
  const st = el("div", "orq-stream"); st.id = "orq-stream"; (a.stream || []).slice(-4).forEach((l) => st.append(el("div", "", l)));
  const hilo = el("div", "orq-hilo"); hilo.id = "orq-hilo";
  (a.mensajes || []).forEach((m) => { const d = el("div", "orq-msg " + m.role, m.content); if (m.ms) d.append(el("em", "", fmt(m.ms))); hilo.append(d); });
  colaDe(a.id).items.forEach((x) => { const d = el("div", "orq-msg user", x.texto); marcarEnCola(d, true); hilo.append(d); });  // lo que espera turno, marcado "en cola"
  const inp = el("input"); inp.placeholder = "Escríbele a " + a.nombre + "…"; inp.id = "orq-input";
  const enviar = async () => { const t = inp.value.trim(); if (!t) return; inp.value = ""; if (colaDe(a.id).poner({ texto: t })) { await pintar(); inp.focus(); } };  // ocupado -> en cola (se ve en el hilo); libre -> sale ya
  inp.onkeydown = (e) => { if (e.key === "Enter") enviar(); };
  const plus = el("div", "orq-plus"); plus.hidden = true; plus.id = "orq-plus";
  const file = el("input"); file.type = "file"; file.id = "orq-file";
  file.onchange = async () => { const f = file.files[0]; if (!f) return; const b64 = await new Promise((ok) => { const r = new FileReader(); r.onload = () => ok(String(r.result).split(",")[1] || ""); r.readAsDataURL(f); }); const r = await orq("subir", { id: a.id, nombre: f.name, datos_b64: b64 }); if (r.error) alert(r.error); await refrescar(); };
  const ins = el("input"); ins.placeholder = "Instrucción extra para este agente"; ins.id = "orq-ins";
  const ri = el("div", "orq-row"); ri.append(ins, btn("Añadir", "secondary", async () => { if (!ins.value.trim()) return; await orq("subir", { id: a.id, instruccion: ins.value }); await refrescar(); }, "orq-ins-ok"));
  plus.append(el("strong", "", "Añadir archivo o instrucción"), file, ri);
  const hablar = btn("🎙", "secondary", () => { const SR = window.SpeechRecognition || window.webkitSpeechRecognition; if (!SR) { inp.focus(); return; } const r = new SR(); r.lang = "es-CO"; r.onresult = (e) => { inp.value = e.results[0][0].transcript; enviar(); }; r.start(); }, "orq-hablar");
  hablar.title = "Hablar con el agente que ejecuta la tarea";
  const fila = el("div", "orq-row"); fila.append(btn("+", "secondary", () => { plus.hidden = !plus.hidden; }, "orq-mas"), inp, hablar, btn("Enviar", "action", enviar, "orq-enviar"));
  const acc = el("div", "orq-row");
  const nCola = colaDe(a.id).length;
  if (nCola) { const vc = btn("✕ cola (" + nCola + ")", "secondary", () => { const caja = document.getElementById("orq-input"); devolverACaja(caja, colaDe(a.id).vaciar().map((x) => x.texto)); pintar(); }, "orq-vaciar-cola"); vc.title = "Quitar lo que está en cola y devolverlo a la caja (lo que ya corre sigue)"; acc.append(vc); }  // en su fila: la caja no se encoge
  const ej = btn("▶ Ejecutar", "secondary", async () => { ej.disabled = true; const r = await orq("ejecutar", { id: a.id }); if (r.error) alert(r.error); ej.disabled = false; refrescar(); }, "orq-ejecutar"); ej.title = "Ejecuta en su sandbox aislado el último bloque de código del agente";
  if (a.estado === "aprobacion") acc.append(btn("✅ Aprobar", "action", async () => { await orq("aprobar", { id: a.id }); refrescar(); }, "orq-aprobar"));
  acc.append(ej, btn("🪞 Mirror", "secondary", () => mirror(a.id), "orq-mirror"), btn("🗑", "secondary", async () => { if (!confirm("¿Borrar " + a.nombre + " y su sandbox?")) return; await orq("borrar", { id: a.id }); SEL = null; refrescar(); }, "orq-borrar"));
  if ((a.archivos || []).length) acc.append(el("span", "muted", "📎 " + a.archivos.join(", ")));
  // enrutador de deploy: GitHub / Hugging Face / Vercel. El token se manda una vez y el backend nunca lo devuelve.
  const dep = el("details", "orq-plus"); dep.id = "orq-deploy"; dep.append(el("summary", "", "🚀 Deploy (GitHub · Hugging Face · Vercel)"));
  const dst = el("select"); dst.id = "orq-dep-destino"; [["github", "GitHub"], ["hf", "Hugging Face"], ["vercel", "Vercel"]].forEach(([v, t]) => dst.append(new Option(t, v)));
  const repo = el("input"); repo.placeholder = "usuario/repo · spaces/usuario/space · nombre-proyecto"; repo.id = "orq-dep-repo";
  const tok = el("input"); tok.type = "password"; tok.placeholder = "token de acceso (se guarda como secreto)"; tok.id = "orq-dep-token"; tok.autocomplete = "off";
  const out = el("div", "muted"); out.id = "orq-dep-out";
  const rt = el("div", "orq-row"); rt.append(tok, btn("Guardar token", "secondary", async () => { const r = await orq("token_guardar", { destino: dst.value, token: tok.value }); tok.value = ""; out.textContent = r.error || ("Token de " + dst.value + (r.cifrado ? " guardado cifrado ✓" : " solo en RAM ⚠ " + (r.aviso || ""))); }, "orq-dep-guardar"));
  const rd = el("div", "orq-row"); rd.append(btn("Plan", "secondary", async () => { const r = await orq("deploy", { id: a.id, destino: dst.value, repo: repo.value, dry_run: true }); out.textContent = JSON.stringify(r); }, "orq-dep-plan"), btn("Desplegar", "action", async () => { if (!confirm("¿Desplegar los archivos de " + a.nombre + " a " + dst.value + "?")) return; const r = await orq("deploy", { id: a.id, destino: dst.value, repo: repo.value, confirmado: true }); out.textContent = JSON.stringify(r); refrescar(); }, "orq-dep-ir"));
  dep.append(dst, repo, rt, rd, out);
  s.append(h, info, el("div", "muted", "Actividad"), st, hilo, plus, fila, acc, dep);
  setTimeout(() => { hilo.scrollTop = hilo.scrollHeight; }, 0);
  return s;
}

async function pintar() {
  const caja = document.getElementById("chat-bots"); if (!caja) return;
  let det = null;
  if (SEL && SEL !== "nuevo") { try { det = (await orq("estado", { id: SEL })).agente; } catch (x) { det = null; } if (det) AGENTES = AGENTES.map((a) => (a.id === det.id ? det : a)); }
  const foco = document.activeElement?.id, val = document.getElementById("orq-input")?.value, plusAb = document.getElementById("orq-plus")?.hidden === false, depAb = document.getElementById("orq-deploy")?.open;
  const depRepo = document.getElementById("orq-dep-repo")?.value, depDst = document.getElementById("orq-dep-destino")?.value;  // fallo 3: el deploy no pierde lo escrito al redibujar
  const panel = SEL === "nuevo" ? formNuevo() : det ? seccion(det) : null;
  caja.replaceChildren(...(panel ? [panel] : []), tira());  // la tira va debajo (del chat o del sub-chat abierto): Controles no la tapa
  // sub-chat abierto: ocupa el lugar del hilo principal (el chat sigue intacto debajo, oculto)
  const hist = document.getElementById("histories"), comp = document.getElementById("composer");
  if (hist) hist.hidden = !!panel; if (comp) comp.hidden = !!panel; caja.classList.toggle("abierto", !!panel);
  if (val && document.getElementById("orq-input")) document.getElementById("orq-input").value = val;
  if (plusAb && document.getElementById("orq-plus")) document.getElementById("orq-plus").hidden = false;
  if (depAb && document.getElementById("orq-deploy")) document.getElementById("orq-deploy").open = true;
  if (depDst && document.getElementById("orq-dep-destino")) document.getElementById("orq-dep-destino").value = depDst;
  if (depRepo && document.getElementById("orq-dep-repo")) document.getElementById("orq-dep-repo").value = depRepo;
  if (foco && document.getElementById(foco) && foco !== "orq-file") document.getElementById(foco).focus();
  for (const id in COLAS) if (COLAS[id].length && !ocupadoAg(id)) COLAS[id].siguiente();  // terminó el turno: sale el siguiente en cola
  clearTimeout(timer);
  if (AGENTES.some((a) => a.estado === "trabajando")) timer = setTimeout(refrescar, 1200);
}
async function abrir(id) { SEL = id; await pintar(); }
async function refrescar() {
  SECCION = seccionActiva();
  try { if (!MODELOS.length) MODELOS = (await orq("modelos", {})).modelos || []; AGENTES = (await orq("listar", {})).agentes || []; }
  catch (x) { const c = document.getElementById("chat-bots"); if (c) c.replaceChildren(el("div", "muted", "🤖 Chat BOTS sin conexión: " + x.message)); return; }
  if (SEL && SEL !== "nuevo" && !AGENTES.some((a) => a.id === SEL)) SEL = null;
  await pintar();
}

function instalar() {
  const hist = document.getElementById("histories");
  if (!hist || document.getElementById("chat-bots")) return;
  const caja = el("div", "chat-bots"); caja.id = "chat-bots"; (document.getElementById("composer") || hist).after(caja);  // debajo del chat abierto (antes: hist.before)
  document.getElementById("chat-tabs")?.addEventListener("click", () => setTimeout(() => { SEL = null; refrescar(); }, 50));  // otro Chat N -> su propia seccion de bots
  refrescar();
}
window.RIU_ORQ = { orq, refrescar };
new MutationObserver(() => { try { instalar(); } catch (e) { console.warn("orquestador", e); } }).observe(document.body, { childList: true, subtree: true });
try { instalar(); } catch (e) {}
