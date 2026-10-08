// Claves secretas: banco del Router (/vault/status|unlock|credentials|rotate). Nunca muestra, guarda ni registra valores.
import { node } from "../api.js";
import { tell } from "./base.js";

const CFG = globalThis.window?.RIU_CONFIG || {};
const JOB = /^https:\/\/[a-f0-9]{24}--8000\.hf\.jobs$/;
const REF = /^[a-z0-9][a-z0-9_.-]*\/[a-z0-9][a-z0-9_.-]*$/;
const TAB_KEY = "riu_clave"; // misma clave de pestaña que usa el chat (sessionStorage, nunca localStorage)
const CODES = {
  INVALID_PASSPHRASE: "Contraseña del banco incorrecta.",
  TOO_MANY_ATTEMPTS: "Demasiados intentos fallidos: el Router bloquea la apertura 10 minutos.",
  VAULT_LOCKED: "El banco está cerrado; ábrelo primero.",
  VAULT_MISSING: "El Router no tiene archivo de banco.",
  VaultError: "El Router rechazó la clave: ya existe o el nombre no es válido.",
  NotFound: "Esa clave no existe en el banco."
};

export function buildInit(method, apiKey, body) {
  const headers = { "X-API-Key": apiKey };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  return { method, headers, credentials: "omit", cache: "no-store", body: body === undefined ? undefined : JSON.stringify(body) };
}

export function explain(status, detail) {
  if (typeof detail === "string" && CODES[detail]) return CODES[detail];
  if (status === 401 || status === 403) return "API key del Router no válida.";
  if (status === 422) return "Datos no válidos: usa minúsculas, números, punto, guion o guion bajo.";
  return typeof detail === "string" ? `Router: ${detail}` : `Router respondió HTTP ${status}.`;
}

export function refOf(provider, account) {
  const ref = `${String(provider).trim().toLowerCase()}/${String(account).trim().toLowerCase()}`;
  if (!REF.test(ref)) throw new Error("Nombre no válido: proveedor/cuenta con minúsculas, números, punto, guion o guion bajo.");
  return ref;
}

let base = "";
let baseAt = 0;
async function routerBase() {
  if (CFG.routerStopped) throw new Error("Router detenido por orden del Director.");
  if (base && Date.now() - baseAt < 30000) return base;
  try {
    const flag = await fetch(`${CFG.liveUrl}?t=${Date.now()}`, { cache: "no-store", credentials: "omit" });
    const info = flag.ok ? await flag.json() : {};
    if (JOB.test(info.LIVE_URL || "")) { base = info.LIVE_URL; baseAt = Date.now(); return base; }
  } catch { /* se usa la última dirección conocida */ }
  if (!base && JOB.test(CFG.apiBase || "")) base = CFG.apiBase;
  if (!base) throw new Error("Dirección del Router no disponible.");
  return base;
}

export function mount(root) {
  let apiKey = sessionStorage.getItem(TAB_KEY) || "";
  let credentials = [];
  let unlocked = false;
  let request = 0;
  const $ = selector => root.querySelector(selector);
  const status = $("#bank-status");
  const setStatus = (text, state) => { status.textContent = text; status.dataset.state = state; };
  const busy = (form, on) => form.querySelectorAll("button,input,select").forEach(el => { el.disabled = on; });

  const call = async (method, path, body) => {
    if (!apiKey) throw new Error("Falta la API key del Router.");
    const url = (await routerBase()) + path;
    let response;
    try { response = await fetch(url, buildInit(method, apiKey, body)); }
    catch { throw new Error("Sin conexión con el Router."); }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(explain(response.status, data.detail));
    return data;
  };

  const showKey = () => {
    const remembered = Boolean(sessionStorage.getItem(TAB_KEY));
    $("#key-status").textContent = !apiKey ? "Sin API key en esta página."
      : remembered ? "API key recordada sólo en esta pestaña. Pulsa Olvidar para borrarla." : "API key sólo en memoria; se pierde al recargar.";
    $("#api-remember").checked = remembered;
  };

  const exists = ref => credentials.some(item => item.credential_ref === ref);
  const currentRef = () => {
    const select = $("#put-provider").value;
    return refOf(select === "otro" ? $("#put-custom").value : select, $("#put-account").value);
  };
  const showMode = () => {
    const mode = $("#put-mode");
    let ref;
    try { ref = currentRef(); } catch { mode.textContent = "Nombre final: proveedor/cuenta (minúsculas, números, punto, guion o guion bajo)."; delete mode.dataset.mode; return; }
    const rotate = exists(ref);
    mode.textContent = rotate ? `${ref} ya existe: se reemplazará su valor.` : `${ref} es nueva: se añadirá al banco.`;
    mode.dataset.mode = rotate ? "rotate" : "put";
    $("#put-submit").textContent = rotate ? "Reemplazar valor" : "Guardar clave";
    for (const item of root.querySelectorAll("#cred-list .item")) item.setAttribute("aria-selected", String(item.dataset.ref === ref));
  };

  const showList = () => {
    const list = $("#cred-list");
    const query = $("#cred-search").value.trim().toLocaleLowerCase();
    list.replaceChildren();
    if (!unlocked) {
      $("#cred-count").textContent = "";
      list.append(node("p", "Abre el banco para ver los nombres de las claves.", "muted"));
      return;
    }
    const matching = credentials.filter(item => `${item.credential_ref} ${item.scope || ""}`.toLocaleLowerCase().includes(query));
    $("#cred-count").textContent = matching.length === credentials.length ? `${credentials.length} claves.` : `${matching.length} de ${credentials.length} claves.`;
    for (const entry of matching) {
      const item = node("div", "", "item");
      item.dataset.ref = entry.credential_ref;
      item.dataset.state = entry.enabled ? "ok" : "pending";
      const name = node("div", "", "cred-name");
      name.append(node("strong", entry.credential_ref),
        node("small", [`proveedor: ${entry.provider}`, `cuenta: ${entry.account}`, `uso: ${entry.scope}`, entry.enabled ? "activa" : "deshabilitada"].join(" · ")));
      const masked = node("span", "••••••••", "masked");
      masked.title = "Valor oculto: el Router nunca lo devuelve";
      const replace = node("button", "Reemplazar valor", "secondary");
      replace.type = "button";
      replace.addEventListener("click", () => {
        const known = [...$("#put-provider").options].some(option => option.value === entry.provider);
        $("#put-provider").value = known ? entry.provider : "otro";
        $("#put-custom").value = known ? "" : entry.provider;
        $("#put-custom-wrap").hidden = known;
        $("#put-account").value = entry.account;
        showMode();
        $("#put-value").focus();
      });
      item.append(name, masked, replace);
      list.append(item);
    }
    if (!matching.length) list.append(node("p", credentials.length ? "Sin claves para este filtro." : "El banco está vacío.", "muted"));
  };

  const refresh = async () => {
    const mine = ++request;
    if (!apiKey) { setStatus("Introduce la API key del Router para consultar el banco.", "pending"); unlocked = false; credentials = []; showList(); return; }
    setStatus("Consultando banco…", "loading");
    try {
      const data = await call("GET", "/vault/status");
      if (mine !== request) return;
      unlocked = Boolean(data.unlocked);
      credentials = unlocked && Array.isArray(data.credentials) ? data.credentials : [];
      if (!data.exists) setStatus("El Router no tiene archivo de banco.", "error");
      else if (unlocked) setStatus(`Banco abierto · ${credentials.length} claves`, "ok");
      else setStatus("Banco cerrado: los modelos no reciben claves.", "pending");
      const ttl = unlocked && data.ttl_seconds ? `se cierra solo en ${Math.round(data.ttl_seconds / 60)} min` : unlocked ? "sin cierre automático" : "";
      $("#bank-detail").textContent = ttl;
      $("#unlock-form").hidden = unlocked;
    } catch (error) {
      if (mine !== request) return;
      unlocked = false;
      credentials = [];
      setStatus(`No disponible: ${error.message}`, "error");
      $("#bank-detail").textContent = "";
      $("#unlock-form").hidden = false;
    }
    showList();
    showMode();
  };

  $("#key-form").addEventListener("submit", event => {
    event.preventDefault();
    const input = $("#api-key");
    const value = input.value.trim();
    input.value = "";
    if (!value) return;
    apiKey = value;
    if ($("#api-remember").checked) sessionStorage.setItem(TAB_KEY, apiKey);
    else sessionStorage.removeItem(TAB_KEY);
    showKey();
    tell("");
    void refresh();
  });
  $("#api-remember").addEventListener("change", event => {
    if (!apiKey) return;
    if (event.target.checked) sessionStorage.setItem(TAB_KEY, apiKey);
    else sessionStorage.removeItem(TAB_KEY);
    showKey();
  });
  $("#api-forget").addEventListener("click", () => {
    apiKey = "";
    $("#api-key").value = "";
    sessionStorage.removeItem(TAB_KEY);
    showKey();
    tell("API key olvidada en esta pestaña.");
    void refresh();
  });
  $("#unlock-form").addEventListener("submit", async event => {
    event.preventDefault();
    const form = event.currentTarget;
    const input = $("#bank-pass");
    const passphrase = input.value;
    input.value = "";
    if (!passphrase) return;
    busy(form, true);
    try {
      const data = await call("POST", "/vault/unlock", { passphrase });
      tell(`Banco abierto · ${data.credentials} claves disponibles para los modelos.`);
    } catch (error) { tell(error.message); }
    finally { busy(form, false); }
    await refresh();
  });
  $("#put-form").addEventListener("submit", async event => {
    event.preventDefault();
    const form = event.currentTarget;
    const input = $("#put-value");
    const secret = input.value;
    input.value = "";
    let ref;
    try { ref = currentRef(); } catch (error) { tell(error.message); return; }
    if (!secret) { tell("Escribe el valor de la clave."); return; }
    if (!unlocked) { tell("El banco está cerrado; ábrelo primero."); return; }
    const rotate = exists(ref);
    if (rotate && !confirm(`¿Reemplazar el valor de ${ref}? El valor anterior deja de funcionar.`)) { tell("Reemplazo cancelado; el valor se borró del campo."); return; }
    busy(form, true);
    try {
      const scope = ref.startsWith("github/") ? "github" : "inference";
      await call("POST", rotate ? "/vault/rotate" : "/vault/credentials", { ref, secret, scope });
      tell(rotate ? `Valor de ${ref} reemplazado.` : `${ref} añadida al banco.`);
    } catch (error) { tell(error.message); }
    finally { busy(form, false); }
    await refresh();
  });
  $("#put-provider").addEventListener("change", event => {
    $("#put-custom-wrap").hidden = event.target.value !== "otro";
    showMode();
  });
  $("#put-custom").addEventListener("input", showMode);
  $("#put-account").addEventListener("input", showMode);
  $("#cred-search").addEventListener("input", showList);
  $("#bank-refresh").addEventListener("click", () => { void refresh(); });

  showKey();
  return refresh();
}

if (globalThis.document?.querySelector("#bank-status")) void mount(document).catch(error => tell(error.message));
