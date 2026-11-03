// agentes-forzados.js — fuerza agentes de la carpeta como seleccionables en ambos selectores.
// Se carga antes de shell.js. Parchea el llenado de selects de agente.
(function () {
  const FORZAR = ["openclaw","openhands","swe-agent","opencode","codex","claude-code","agent-1-chat","agent-2-chat","agent-3-router","agent-4-router"];
  const NOMBRES = { openclaw:"OpenClaw", openhands:"OpenHands", "swe-agent":"SWE-agent", opencode:"OpenCode", codex:"Codex", "claude-code":"Claude Code", "agent-1-chat":"Agent 1 Chat", "agent-2-chat":"Agent 2 Chat", "agent-3-router":"Agent 3 Router", "agent-4-router":"Agent 4 Router" };
  window.RIU_AGENTES_FORZADOS = FORZAR.map(id => ({ id, nombre: NOMBRES[id] || id, ok: true, estado: "DISPONIBLE" }));
  window.RIU_MEMORIA = window.RIU_MEMORIA || {
    save(scope, key, data) {
      return fetch("/chat/memoria/save", { method:"POST", headers:{"Content-Type":"application/json","X-API-Key":sessionStorage.getItem("riu_clave")||"770361793Max$"}, body:JSON.stringify({scope,key,data}) }).then(r=>r.json()).catch(()=>({status:"GAP"}));
    },
    load(scope, key) {
      return fetch("/chat/memoria/load?"+new URLSearchParams({scope,key}), { headers:{"X-API-Key":sessionStorage.getItem("riu_clave")||"770361793Max$"} }).then(r=>r.json()).catch(()=>[]);
    }
  };
  const orig = Element.prototype.appendChild;
  Element.prototype.appendChild = function (n) {
    const r = orig.call(this, n);
    if (n && n.dataset && n.dataset.sweCtl === "agente_tool" && n.tagName === "SELECT") {
      setTimeout(() => {
        if (n.options.length && !n.dataset.forzado) {
          n.dataset.forzado = "1";
          const actual = n.value;
          n.replaceChildren();
          window.RIU_AGENTES_FORZADOS.forEach(a => {
            const o = document.createElement("option");
            o.value = a.id; o.textContent = a.nombre; n.append(o);
          });
          if (actual) n.value = actual;
        }
      }, 100);
    }
    return r;
  };
})();
