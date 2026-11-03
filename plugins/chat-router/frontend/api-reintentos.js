// api-reintentos.js — Groq/NVIDIA: presupuesto global 120 s, sin reintentos ciegos.
// El puente chat_async gestiona sus reintentos y su request_id en api.js.
// NO se interceptan otros modelos, rutas del Router ni streaming ya iniciado.
(function () {
  const original = window.fetch;
  function entrada(opts) {
    try {
      const b = typeof opts?.body === "string" ? JSON.parse(opts.body) : null;
      if (!b || typeof b !== "object") return null;
      const model = String(b.model || b.modelo || b.qwen?.modelo || "");
      const provider = String(b.provider || "").toLowerCase();
      const externo = /^(groq|nvidia)\//.test(model) || provider === "groq" || provider === "nvidia";
      return externo ? { seguro: !!b.request_id, model } : null;
    } catch (e) { return null; }
  }
  window.fetch = async function (url, opts) {
    const u = String(typeof url === "string" ? url : (url?.url || url));
    const esChat = /\/chat\/send|\/v1\/chat\/completions/.test(u);
    const dato = esChat ? entrada(opts) : null;
    if (!dato) return original.call(this, url, opts);
    const externoSignal = opts?.signal || null;
    const fin = Date.now() + 120000;
    let fallo = null;
    const max = dato.seguro ? 3 : 1; // sin idempotencia no se duplica un POST ambiguo
    for (let intento = 0; intento < max; intento++) {
      if (externoSignal?.aborted) throw new DOMException("Solicitud detenida", "AbortError");
      const tiempo = fin - Date.now();
      if (tiempo <= 0) break;
      const ctrl = new AbortController();
      const cortar = () => ctrl.abort();
      if (externoSignal) externoSignal.addEventListener("abort", cortar, { once: true });
      const timer = setTimeout(cortar, Math.max(1, tiempo));
      try {
        const r = await original.call(this, url, { ...(opts || {}), signal: ctrl.signal });
        // La respuesta puede incluir streaming: se devuelve sin leer ni rehacerla.
        if (r.ok || !dato.seguro || ![408, 429, 500, 502, 503, 504].includes(r.status)) return r;
        fallo = new Error("HTTP " + r.status);
      } catch (e) {
        if (externoSignal?.aborted) throw e;
        fallo = e;
        if (!dato.seguro) throw e;
        const m = String(e?.message || e);
        if (!/network|failed to fetch|timeout|abort/i.test(m) && e?.name !== "AbortError" && e?.name !== "TypeError") throw e;
      } finally {
        clearTimeout(timer);
        if (externoSignal) externoSignal.removeEventListener("abort", cortar);
      }
      if (intento + 1 < max) {
        const pausa = Math.min(800 * (intento + 1), Math.max(0, fin - Date.now() - 250));
        if (pausa <= 0) break;
        window.dispatchEvent(new CustomEvent("router-connection", { detail: "Groq/NVIDIA: reintento " + (intento + 1) + "/" + (max - 1) }));
        await new Promise((ok) => setTimeout(ok, pausa));
      }
    }
    const e = new Error("GAP: GROQ_NVIDIA_120_S · 2 minutos o reintentos agotados" + (fallo ? " · " + String(fallo.message || fallo).slice(0, 100) : ""));
    e.causa = "timeout_proveedor"; throw e;
  };
})();
