// temp-160.js — fuerza temperature: 1.6 en todas las llamadas de modelo.
(function () {
  const ORIG = window.fetch;
  window.fetch = function (url, opts) {
    const u = String(url);
    if (/\/chat\/send|\/v1\/chat\/completions|\/chat\/swe\//.test(u) && opts && opts.body) {
      try {
        const b = JSON.parse(opts.body);
        if (b && typeof b === "object" && !b.temperature) b.temperature = 1.6;
        opts = { ...opts, body: JSON.stringify(b) };
      } catch (e) {}
    }
    return ORIG.call(this, url, opts);
  };
})();
