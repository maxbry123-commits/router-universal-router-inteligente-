// ventana-archivos.js — "Archivos (motor)": cola de descargar / extraer / copiar / mover / listar / buscar con origen y destino a mano.
// Llama a POST /plugins/motor_archivos/call/<accion> con api.js (plugin). La clave sale de la sesión, no del código.
import { plugin } from "./api.js";
import { el, btn, ventana } from "./ventanas-control.js";

export const ACCIONES = ["descargar", "extraer", "copiar", "mover", "listar", "buscar"];
const SIN_DESTINO = ["listar", "buscar"];
const KF = "riu_motor_filas_v1", KQ = "riu_motor_cola_v1";
const ICONO = '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/><path d="M12 10v5m0 0-2-2m2 2 2-2"/>';

export const filaVacia = () => ({ accion: "descargar", origen: "", destino: "", extraer: false, readme: false, patron: "" });
const bool = (v) => v === true || /^(true|si|sí|yes|1|on)$/i.test(String(v == null ? "" : v).trim());
const sinComillas = (s) => { s = String(s).trim(); return /^(".*"|'.*')$/.test(s) ? s.slice(1, -1) : s; };

// objeto de un trabajo (JSON o YAML) -> fila editable; descarta lo que no es del contrato
export function filaDe(o) {
  o = o && typeof o === "object" ? o : {};
  const accion = ACCIONES.includes(String(o.accion).toLowerCase()) ? String(o.accion).toLowerCase() : "descargar";
  return { accion, origen: String(o.origen == null ? "" : o.origen).trim(), destino: String(o.destino == null ? "" : o.destino).trim(),
    extraer: bool(o.extraer), readme: bool(o.readme), patron: String(o.patron == null ? "" : o.patron) };
}
// YAML mínimo: lista de "- clave: valor" (con o sin guion inicial por trabajo, claves planas)
export function parsearYaml(txt) {
  const out = []; let cur = null;
  String(txt).split(/\r?\n/).forEach((raw) => {
    const l = raw.replace(/^\s*#.*$/, "");
    if (!l.trim() || /^\s*(cola|trabajos)\s*:\s*$/.test(l)) return;
    const m = /^\s*(-\s+)?([A-Za-z_]+)\s*:\s*(.*)$/.exec(l);
    if (!m) return;
    if (m[1] || !cur) { cur = {}; out.push(cur); }
    cur[m[2].toLowerCase()] = sinComillas(m[3].replace(/\s+#.*$/, ""));
  });
  return out;
}
// pegado libre -> filas. Acepta lista JSON, {cola:[...]} o YAML.
export function parsearPegado(txt) {
  const t = String(txt || "").trim();
  if (!t) throw new Error("No hay nada pegado");
  let lista = null;
  if (/^[\[{]/.test(t)) {
    let j; try { j = JSON.parse(t); } catch (e) { throw new Error("JSON no válido: " + e.message); }
    lista = Array.isArray(j) ? j : (j && (j.cola || j.trabajos)) || (j && j.accion ? [j] : null);
  } else lista = parsearYaml(t);
  if (!Array.isArray(lista) || !lista.length) throw new Error("No encontré trabajos en el texto");
  return lista.map(filaDe);
}
// filas -> {cola:[trabajo]}; lanza Error con el número de fila si falta algo
export function armarPayload(filas) {
  const cola = [];
  (filas || []).forEach((f, i) => {
    const a = String(f.accion || "").toLowerCase(), origen = String(f.origen || "").trim(), destino = String(f.destino || "").trim();
    if (!origen && !destino && !f.patron) return;  // fila en blanco: se ignora
    if (!ACCIONES.includes(a)) throw new Error("Fila " + (i + 1) + ": acción no válida");
    if (!origen) throw new Error("Fila " + (i + 1) + ": falta el origen");
    if (!SIN_DESTINO.includes(a) && !destino) throw new Error("Fila " + (i + 1) + ": falta el destino");
    const t = { accion: a, origen, sobrescribir: false };
    if (!SIN_DESTINO.includes(a)) t.destino = destino;
    if (a === "descargar") { t.extraer = !!f.extraer; t.readme = !!f.readme; }
    if (a === "extraer") t.extraer = true;
    if (a === "buscar") { const p = String(f.patron || "").trim(); if (!p) throw new Error("Fila " + (i + 1) + ": falta el texto a buscar"); t.patron = p; t.max = 200; }
    if (a === "listar") t.max = 200;
    cola.push(t);
  });
  if (!cola.length) throw new Error("La cola está vacía");
  return { cola };
}
const hayBytes = (n) => { n = Number(n) || 0; return n < 1024 ? n + " B" : n < 1048576 ? (n / 1024).toFixed(1) + " KB" : n < 1073741824 ? (n / 1048576).toFixed(1) + " MB" : (n / 1073741824).toFixed(2) + " GB"; };
export const bytesLegibles = hayBytes;
export const terminal = (e) => ["terminado", "error", "cancelado"].includes(e);

if (typeof document !== "undefined") {
  const guardar = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const leerLS = (k, d) => { try { const v = JSON.parse(localStorage.getItem(k) || "null"); return v == null ? d : v; } catch (e) { return d; } };
  let sondeo = null;

  const pintar = (cuerpo) => {
    clearInterval(sondeo); sondeo = null;
    const borrador = leerLS(KF, []);
    let filas = (Array.isArray(borrador) && borrador.length ? borrador : [filaVacia()]).map(filaDe);
    const aviso = el("div", "cv-est"); aviso.setAttribute("role", "status"); aviso.setAttribute("aria-live", "polite");
    const tabla = el("div"), estado = el("div"), raizTxt = el("div", "fila-desc", "Raíz del motor: consultando…"), explor = el("div"), rutaExp = el("input");
    let sel = -1, idCola = String(leerLS(KQ, "") || "");
    const dec = (m) => { aviso.textContent = m || ""; };
    const falla = (e) => { dec(e && e.message ? e.message : String(e)); };
    const volcar = () => guardar(KF, filas);
    const exito = (r) => { if (r && r.error) throw new Error(r.error); return r; };

    const pintarFilas = () => {
      tabla.replaceChildren();
      filas.forEach((f, i) => {
        const caja = el("div", "cv-fila"); caja.style.outline = i === sel ? "1px solid var(--azul-electrico,#1F6BFF)" : "none";
        const a = el("select"); a.setAttribute("aria-label", "Acción fila " + (i + 1));
        ACCIONES.forEach((x) => { const o = el("option", "", x); o.value = x; if (x === f.accion) o.selected = true; a.append(o); });
        const o = el("input"); o.placeholder = "Origen: URL, github.com/dueño/repo o ruta"; o.value = f.origen; o.setAttribute("aria-label", "Origen fila " + (i + 1));
        const d = el("input"); d.placeholder = "Destino (relativo a la raíz): proyectos/ejemplo"; d.value = f.destino; d.setAttribute("aria-label", "Destino fila " + (i + 1));
        const p = el("input"); p.placeholder = "Texto a buscar"; p.value = f.patron; p.setAttribute("aria-label", "Texto a buscar fila " + (i + 1));
        const chk = (txt, k) => { const l = el("label", "vn-check"), c = el("input"); c.type = "checkbox"; c.checked = !!f[k]; c.addEventListener("change", () => { f[k] = c.checked; volcar(); }); l.append(c, el("span", "", txt)); return l; };
        const ajustar = () => {
          const sd = SIN_DESTINO.includes(f.accion);
          d.hidden = sd; p.hidden = f.accion !== "buscar"; ex.hidden = f.accion !== "descargar"; rd.hidden = f.accion !== "descargar";
        };
        const ex = chk("extraer", "extraer"), rd = chk("readme", "readme");
        a.addEventListener("change", () => { f.accion = a.value; ajustar(); volcar(); });
        o.addEventListener("input", () => { f.origen = o.value; volcar(); });
        d.addEventListener("input", () => { f.destino = d.value; volcar(); });
        p.addEventListener("input", () => { f.patron = p.value; volcar(); });
        [a, o, d, p].forEach((n) => n.addEventListener("focus", () => { sel = i; }));
        ajustar(); caja.append(a, o, d, p, ex, rd); tabla.append(caja);
      });
    };
    const quitar = () => { if (filas.length > 1) filas.splice(sel >= 0 ? sel : filas.length - 1, 1); else filas = [filaVacia()]; sel = -1; volcar(); pintarFilas(); };
    const duplicar = () => { const i = sel >= 0 ? sel : filas.length - 1; filas.splice(i + 1, 0, { ...filas[i] }); sel = i + 1; volcar(); pintarFilas(); };
    const añadir = () => { filas.push(filaVacia()); sel = filas.length - 1; volcar(); pintarFilas(); };

    const pega = el("textarea"); pega.rows = 5; pega.hidden = true; pega.setAttribute("aria-label", "Pegar YAML o JSON");
    pega.placeholder = "- accion: descargar\n  origen: github.com/dueño/repo\n  destino: proyectos/repo\n  extraer: true\n  readme: true";
    const aplicarPega = btn("Llenar filas", "secondary", () => { try { filas = parsearPegado(pega.value); sel = -1; volcar(); pintarFilas(); pega.value = ""; pega.hidden = true; aplicarPega.hidden = true; dec(filas.length + " fila(s) cargadas"); } catch (e) { falla(e); } });
    aplicarPega.hidden = true;
    const bPegar = btn("Pegar YAML o JSON", "secondary", () => { pega.hidden = !pega.hidden; aplicarPega.hidden = pega.hidden; if (!pega.hidden) pega.focus(); });

    const pintarEstado = (r) => {
      estado.replaceChildren();
      if (!r) return;
      estado.append(el("div", "cv-sec", "Cola " + r.id + " · " + r.estado));
      (r.trabajos || []).forEach((t) => {
        const f = el("div", "cv-fila"), n = el("div", "cv-n");
        n.append(el("div", "", "#" + t.n + " " + t.accion + " · " + t.estado + (t.archivos != null ? " · " + t.archivos + " archivos · " + hayBytes(t.bytes) : "")));
        n.append(el("small", "", (t.origen || "") + (t.destino ? " → " + t.destino : "")));
        if (t.error) n.append(el("small", "", t.error));
        if (t.resumen) n.append(el("small", "", t.resumen));
        if (Array.isArray(t.muestra) && t.muestra.length) { const m = el("pre", "cv-msg", t.muestra.join("\n")); m.style.maxHeight = "140px"; m.style.overflow = "auto"; n.append(m); }
        f.append(n); estado.append(f);
      });
    };
    const consultar = async () => {
      if (!idCola) return;
      try {
        const r = exito(await plugin("motor_archivos", "estado", { id: idCola }));
        pintarEstado(r);
        if (terminal(r.estado)) { clearInterval(sondeo); sondeo = null; dec("Cola " + r.estado); verRaiz(); }
        else if (!sondeo) sondeo = setInterval(consultar, 2000);
      } catch (e) { falla(e); clearInterval(sondeo); sondeo = null; }
    };
    const ejecutar = btn("Ejecutar cola", "action", async () => {
      let p; try { p = armarPayload(filas); } catch (e) { falla(e); return; }
      ejecutar.disabled = true; dec("enviando…");
      try {
        const r = exito(await plugin("motor_archivos", "ejecutar", p));
        idCola = r.id; guardar(KQ, idCola); dec("Cola " + r.id + " · " + r.trabajos + " trabajo(s)"); await consultar();
        if (!sondeo && !(estado.textContent.includes("terminado"))) sondeo = setInterval(consultar, 2000);
      } catch (e) { falla(e); } finally { ejecutar.disabled = false; }
    });
    const cancelar = btn("Cancelar", "secondary", async () => {
      if (!idCola) { dec("No hay cola en curso"); return; }
      try { exito(await plugin("motor_archivos", "cancelar", { id: idCola })); dec("Cancelando…"); await consultar(); } catch (e) { falla(e); }
    });

    async function verRaiz() {
      try {
        const r = exito(await plugin("motor_archivos", "raiz", {}));
        raizTxt.textContent = "Raíz del motor: " + r.raiz + (r.libre_bytes != null ? " · libre " + hayBytes(r.libre_bytes) : "");
      } catch (e) { raizTxt.textContent = "Raíz del motor: " + (e.message || e); }
    }
    async function explorar(ruta) {
      rutaExp.value = ruta || "";
      try {
        const r = exito(await plugin("motor_archivos", "listar_raiz", { ruta: ruta || "" }));
        explor.replaceChildren(el("div", "fila-desc", "/" + (r.ruta || "")));
        if (r.ruta) { const arriba = r.ruta.split("/").filter(Boolean).slice(0, -1).join("/"); explor.append(btn("..", "secondary", () => explorar(arriba))); }
        (r.entradas || []).forEach((x) => {
          const full = [r.ruta, x.nombre].filter(Boolean).join("/");
          const f = el("div", "cv-fila");
          if (x.tipo === "dir") f.append(btn(x.nombre + "/", "secondary", () => explorar(full)));
          else f.append(el("span", "cv-n", x.nombre + " · " + hayBytes(x.bytes)));
          if (x.tipo === "dir") f.append(btn("Usar como destino", "secondary", () => { const i = sel >= 0 ? sel : filas.length - 1; filas[i].destino = full; volcar(); pintarFilas(); dec("Destino de la fila " + (i + 1) + ": " + full); }));
          explor.append(f);
        });
        if (!(r.entradas || []).length) explor.append(el("div", "fila-desc", "Carpeta vacía."));
      } catch (e) { explor.replaceChildren(el("div", "fila-desc", e.message || String(e))); }
    }
    rutaExp.placeholder = "Ruta dentro de la raíz (vacía = raíz)"; rutaExp.setAttribute("aria-label", "Ruta del explorador");
    rutaExp.addEventListener("keydown", (ev) => { if (ev.key === "Enter") explorar(rutaExp.value.trim()); });
    const bExp = btn("Ver carpeta", "secondary", () => explorar(rutaExp.value.trim()));

    const barra = el("div", "cv-form"); barra.append(btn("Añadir fila", "secondary", añadir), btn("Duplicar", "secondary", duplicar), btn("Quitar", "secondary", quitar), bPegar);
    const acc = el("div", "cv-form"); acc.append(ejecutar, cancelar);
    const fe = el("div", "cv-form"); fe.append(rutaExp, bExp);
    cuerpo.replaceChildren(
      el("div", "fila-desc", "Escribe origen y destino a mano; cada ejecución usa lo que ves aquí. El destino es relativo a la raíz."),
      raizTxt, el("div", "cv-sec", "Trabajos"), tabla, barra, pega, aplicarPega, acc, aviso,
      el("div", "cv-sec", "Estado"), estado, el("div", "cv-sec", "Explorador del destino"), fe, explor);
    pintarFilas(); verRaiz(); explorar(""); if (idCola) consultar();
  };

  const montar = () => {
    const ya = document.querySelector("#btn-motor-archivos");
    ventana("motor-archivos", "Archivos (motor)", pintar);
    const b = document.querySelector("#btn-motor-archivos");
    if (b && !ya) { const s = b.querySelector("svg"); if (s) s.innerHTML = ICONO; }  // icono de línea propio (ICONOS de ventanas-control no lo trae)
  };
  new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
  montar();
}
