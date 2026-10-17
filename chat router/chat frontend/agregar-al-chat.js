// agregar-al-chat.js — hoja «Agregar al chat» (referencia del Director): Cámara / Fotos / Archivos, carpeta de proyecto, interruptores reales y accesos.
// El clip abre esta hoja; «Archivos» hace lo de siempre (selector directo). Los interruptores son los de verdad (workflow, constitución, sandbox, agentes).
import { leer, escribir, KEYS } from "./almacen.js";
import { crearObjetivo, listaWF, listaProyectos } from "./objetivos-ancla.js";
import { el, boton, crearVentana, abrirVentana } from "./ventanas-comun.js";
const KPS = "riu_proyecto_subida_v1";
const SVG = (p) => '<svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + p + "</svg>";
export function montarAgregarAlChat({ root, q, tell }) {
  const btn = q("#btn-adjunto"), inp = q("#adjunto"); if (!btn || !inp || btn.dataset.ag) return; btn.dataset.ag = "1";
  const { sheet, caja } = crearVentana(root, { id: "ventana-agregar", titulo: "Agregar al chat", css: "agregar-al-chat" });
  const cuerpo = el("div", "ag-cuerpo"); caja.append(cuerpo);
  const proyecto = () => { try { return localStorage.getItem(KPS) || ""; } catch (e) { return ""; } };
  const fijarProyecto = (n) => { try { if (n) localStorage.setItem(KPS, n); else localStorage.removeItem(KPS); } catch (e) {} };
  const directo = () => { btn.dataset.directo = "1"; try { btn.click(); } finally { delete btn.dataset.directo; } };
  btn.addEventListener("click", (e) => { if (btn.dataset.directo) return; e.preventDefault(); e.stopImmediatePropagation(); pintar(); abrirVentana(root, sheet); }, true);
  inp.addEventListener("change", () => { const pn = proyecto(); if (!pn) return; const o = crearObjetivo("proyecto", pn); if (o) [...(inp.files || [])].forEach((f) => o.anclados.add(f.name)); });
  const adjuntar = (files) => {
    files = [...files]; if (!files.length) return; const dt = new DataTransfer(); files.forEach((f) => dt.items.add(f));
    btn.dataset.directo = "1"; inp.click = () => {}; try { btn.click(); } finally { delete inp.click; delete btn.dataset.directo; }
    inp.files = dt.files; inp.dispatchEvent(new Event("change", { bubbles: true })); sheet.hidden = true;
  };
  const selector = (capture) => { const i = el("input"); i.type = "file"; i.accept = "image/*"; i.multiple = !capture; if (capture) i.setAttribute("capture", "environment"); i.hidden = true; i.addEventListener("change", () => { adjuntar(i.files || []); i.value = ""; }); return i; };
  const iCam = selector(true), iFoto = selector(false); caja.append(iCam, iFoto);
  const grande = (txt, ic, fn) => { const b = el("button", "ag-grande"); b.type = "button"; b.innerHTML = ic; b.append(el("span", "", txt)); b.addEventListener("click", fn); return b; };
  const fila = (titulo, sub, fn) => { const b = el("button", "ag-fila"); b.type = "button"; const t = el("span", ""); t.append(el("strong", "", titulo)); if (sub) t.append(el("small", "", sub)); b.append(t, el("span", "ag-ch", "›")); b.addEventListener("click", fn); return b; };
  const interruptor = (titulo, sub, getOn, setOn, desactivado) => {
    const f = el("div", "ag-fila"), t = el("span", ""), sw = el("button", "ag-sw"); t.append(el("strong", "", titulo)); if (sub) t.append(el("small", "", sub));
    sw.type = "button"; sw.setAttribute("role", "switch"); sw.setAttribute("aria-label", titulo); sw.setAttribute("aria-checked", String(!!getOn())); sw.disabled = !!desactivado;
    sw.addEventListener("click", () => { if (setOn(!getOn()) === false) return; pintar(); }); f.append(t, sw); return f;
  };
  const acceso = (titulo, sub, sel) => fila(titulo, sub, () => { sheet.hidden = true; const b = q(sel); if (b) b.click(); else tell(titulo + " no está disponible"); });
  function pintar() {
    cuerpo.replaceChildren();
    const g = el("div", "ag-3");
    g.append(grande("Cámara", SVG('<path d="M4 8h3l2-2h6l2 2h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>'), () => iCam.click()),
      grande("Fotos", SVG('<rect x="4" y="5" width="16" height="14" rx="2"/><circle cx="9" cy="10" r="1.5"/><path d="M5 17l5-5 4 4 2-2 3 3"/>'), () => iFoto.click()),
      grande("Archivos", SVG('<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M12 17v-6M9.5 13.5L12 11l2.5 2.5"/>'), () => { sheet.hidden = true; directo(); }));
    cuerpo.append(g);
    const pn = proyecto(), lp = el("div", "ag-lista"); lp.hidden = true;
    ["", ...listaProyectos().map((p) => p.nombre)].forEach((n) => lp.append(boton(n || "Ninguno", "mini" + (n === pn ? " on" : ""), () => { fijarProyecto(n); tell(n ? "Lo que subas se agrega a «" + n + "»" : "Sin carpeta de proyecto"); pintar(); })));
    if (!listaProyectos().length) lp.append(el("div", "fila-desc", "Crea carpetas en Anclaje › Proyecto."));
    cuerpo.append(fila("Agregar al proyecto", pn || "Ninguno", () => { lp.hidden = !lp.hidden; }), lp);
    const obj = (tipo) => crearObjetivo(tipo);
    cuerpo.append(
      interruptor("Workflow Loops code Yaiwes", "Su system prompt y anclas viajan con cada mensaje", () => listaWF().some((w) => w.encendido), (on) => {
        const x = leer(KEYS.workflows, { lista: [], sel: null }); if (!Array.isArray(x.lista) || !x.lista.length) { tell("Crea un workflow primero"); return false; }
        if (!on) x.lista.forEach((w) => { w.encendido = false; }); else (x.lista.find((y) => y.id === x.sel) || x.lista[0]).encendido = true; escribir(KEYS.workflows, x);
      }),
      interruptor("Constitución sentinela", "Sus reglas viajan con cada mensaje", () => obj("constitucion").encendido, (on) => { obj("constitucion").encendido = on; }),
      interruptor("Sandbox anclado", "Sus anclas e instrucciones viajan con cada mensaje", () => obj("sandbox").encendido, (on) => { obj("sandbox").encendido = on; }),
      interruptor("Agentes remotos", "Código fuente + SDK anclados", () => obj("agentes").encendido, (on) => { obj("agentes").encendido = on; }),
    );
    cuerpo.append(acceso("Anclaje", "Enlaces, handoffs, archivos y más", "#btn-ancla"), acceso("Archivos recientes", "La carpeta compartida", "#btn-archivos"), acceso("Workflows", "Crear y configurar", "#pill-workflows"), acceso("Constitución sentinela", "Reglas, anclas y notas", "#pill-constitucion"),
      acceso("Claves", "Secretos y claves", "#pill-claves"),
      fila("Habilidades", "Comandos con «/»", () => { sheet.hidden = true; const m = q("#message"); if (m) { m.value = "/"; m.dispatchEvent(new Event("input", { bubbles: true })); m.focus(); } }),
      interruptor("Memoria", "Siempre activa; no se cambia por chat", () => true, () => false, true));
  }
}
