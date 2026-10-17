// Comprobacion de version: compara version.json desplegado con la version CARGADA en esta pagina (no con GitHub).
// Solo recarga si Vercel ya publico otro commit, y nunca con una tarea en curso o texto escrito.
// Si falla cualquier consulta, no hace nada. Sin bucle: sessionStorage recuerda a que commit ya se recargo.
(function (g) {
  const K = "riu_v_recargado", KT = "riu_v_check_ts";
  async function json(fetchFn, url, ms) {
    const ac = typeof AbortController === "function" ? new AbortController() : null;
    const t = setTimeout(() => ac && ac.abort(), ms);
    try {
      const r = await fetchFn(url, { cache: "no-store", signal: ac ? ac.signal : undefined });
      return r && r.ok ? await r.json() : null;
    } catch (e) { return null; } finally { clearTimeout(t); }
  }
  function ocupado(d) {
    try {
      const doc = d.document || g.document, ls = d.localStorage || g.localStorage, ch = d.RIU_CHAT || g.RIU_CHAT;
      if (ch && typeof ch.ocupado === "function" && ch.ocupado()) return true;
      if (ch && ch.chat && ch.chat() && ch.chat().ocupado) return true;
      if (doc && doc.querySelector && doc.querySelector(".item.message.pending")) return true;
      const pr = ls && ls.getItem("riu_proc_v1"); if (pr && pr !== "{}") return true;  // proceso_id pendiente
      const caja = doc && doc.querySelector && doc.querySelector("#message");
      if (caja && caja.value && caja.value.trim()) return true;
    } catch (e) {}
    return false;
  }
  const R = { cargada: null };
  async function check(d) {
    d = d || {};
    const f = d.fetch || g.fetch, ss = d.sessionStorage || g.sessionStorage, loc = d.location || g.location;
    try {
      const now = Date.now(), last = +(ss.getItem(KT) || 0);
      if (R.cargada && !d.forzar && now - last < 5 * 60 * 1000) return "throttle";
      ss.setItem(KT, String(now));
      const v = await json(f, "/chat/ui/version.json?t=" + now, 4000);
      const front = v && String(v.commit || "").trim();
      if (!front) return "sin_version";
      if (!R.cargada) { R.cargada = front; ss.removeItem(K); return "inicial"; }  // primera lectura = version servida en esta carga
      if (front === R.cargada) return "igual";
      if (ocupado(d)) { ss.removeItem(KT); return "ocupado"; }  // reintenta en el siguiente ciclo
      if (ss.getItem(K) === front) return "ya_recargado";
      ss.setItem(K, front);
      const u = new URL(loc.href); u.searchParams.set("v", front.slice(0, 12));
      loc.replace(u.toString());
      return "recarga";
    } catch (e) { return "error"; }
  }
  R.check = check; R.ocupado = ocupado;
  g.RIU_VERSION = R;
  if (!g.RIU_VERSION_NO_AUTO) {
    check();
    setInterval(() => check(), 5 * 60 * 1000);
    if (g.document && g.document.addEventListener) g.document.addEventListener("visibilitychange", () => { if (g.document.visibilityState === "visible") check(); });
  }
})(typeof window !== "undefined" ? window : globalThis);
