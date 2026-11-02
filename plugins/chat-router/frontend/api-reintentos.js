// api-reintentos.js — reintentos automáticos y timeouts más largos para todas las llamadas de modelo.
// Se carga después de api.js. Envuelve window.fetch para reintentar errores de red en /chat/send y /v1/.
(function () {
  const ORIG = window.fetch;
  const TIMEOUTS = {
    "/chat/send": 120000,
    "/v1/chat/completions": 90000,
    "/web/v1/chat/completions": 90000,
    "/chat/swe/": 180000,
    default: 30000,
  };
  function timeoutDe(url) {
    for (const [p, t] of Object.entries(TIMEOUTS)) {
      if (p !== "default" && url.includes(p)) return t;
    }
    return TIMEOUTS.default;
  }
  function esRed(e) {
    const m = String(e && (e.message || e)).toLowerCase();
    return e && (e.name === "AbortError" || e.name === "TypeError" || /network|failed to fetch|timeout|abort/.test(m));
  }
  window.fetch = async function (url, opts) {
    const u = String(url);
    const esModelo = /\/chat\/send|\/v1\/chat\/completions|\/chat\/swe\//.test(u);
    if (!esModelo) return ORIG.call(this, url, opts);
    const max = 3;
    const back = [800, 1600, 3200];
    let last;
    for (let i = 0; i < max; i++) {
      try {
        const ac = new AbortController();
        const ms = timeoutDe(u);
        const t = setTimeout(() => ac.abort(), ms);
        const r = await ORIG.call(this, url, { ...opts, signal: ac.signal });
        clearTimeout(t);
        if (r.ok || r.status < 500) return r;
        last = new Error("HTTP " + r.status);
        if (r.status < 500) return r;
      } catch (e) {
        last = e;
        if (!esRed(e) && i === 0) throw e;
      }
      if (i < max - 1) {
        try { window.dispatchEvent(new CustomEvent("router-connection", { detail: "Reintentando (" + (i + 1) + ")…" })); } catch (x) {}
        await new Promise((ok) => setTimeout(ok, back[i] || 2000));
      }
    }
    const g = new Error("GAP: network error · " + (last && last.message || "sin respuesta"));
    g.causa = "red";
    throw g;
  };
})();
