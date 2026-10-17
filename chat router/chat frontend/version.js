// Comprobacion minima de version: si el frontend servido no es el commit actual de main, recarga UNA vez con ?v=<commit>.
// Si falla cualquier consulta, no hace nada. Sin bucle: sessionStorage recuerda a que commit ya se recargo.
(function (g) {
  const GH = "https://api.github.com/repos/maxbry123-commits/router-universal-router-inteligente-/commits/main";
  const K = "riu_v_recargado", KT = "riu_v_check_ts";
  async function json(fetchFn, url, ms, headers) {
    const ac = typeof AbortController === "function" ? new AbortController() : null;
    const t = setTimeout(() => ac && ac.abort(), ms);
    try {
      const r = await fetchFn(url, { cache: "no-store", headers: headers || {}, signal: ac ? ac.signal : undefined });
      return r && r.ok ? await r.json() : null;
    } catch (e) { return null; } finally { clearTimeout(t); }
  }
  async function check(d) {
    d = d || {};
    const f = d.fetch || g.fetch, ss = d.sessionStorage || g.sessionStorage, loc = d.location || g.location;
    try {
      const now = Date.now(), last = +(ss.getItem(KT) || 0);
      if (now - last < 5 * 60 * 1000) return "throttle";  // limite de GitHub sin token: 60/h por IP
      ss.setItem(KT, String(now));
      const v = await json(f, "/chat/ui/version.json", 3000);
      const front = v && String(v.commit || "").trim();
      if (!front) return "sin_version";
      const m = await json(f, GH, 3000, { Accept: "application/vnd.github+json" });
      const main = m && String(m.sha || "").trim();
      if (!main) return "sin_red";
      if (front === main) { ss.removeItem(K); return "igual"; }
      if (ss.getItem(K) === main) return "ya_recargado";
      try {  // nunca recargar con una tarea en curso o texto escrito: eso cortaba la respuesta ("se interrumpio al recargar")
        const doc = d.document || g.document, ls = d.localStorage || g.localStorage;
        const enCurso = (doc && doc.querySelector && doc.querySelector(".item.message.pending")) || (ls && ls.getItem("riu_proc_v1") && ls.getItem("riu_proc_v1") !== "{}");
        const caja = doc && doc.querySelector && doc.querySelector("#message");
        if (enCurso || (caja && caja.value && caja.value.trim())) { ss.removeItem(KT); return "ocupado"; }
      } catch (e) {}
      ss.setItem(K, main);
      const u = new URL(loc.href); u.searchParams.set("v", main.slice(0, 12));
      loc.replace(u.toString());
      return "recarga";
    } catch (e) { return "error"; }
  }
  g.RIU_VERSION = { check };
  if (!g.RIU_VERSION_NO_AUTO) check();
})(typeof window !== "undefined" ? window : globalThis);
