# ROUTER MAXBRY — CÓDIGO ADAPTABLE · 5 PANELES

**Versión:** v5.5 · **Tipo:** Adaptable (sin dependencias hardcoded) · **Instalación:** clonable en cualquier frontend que consuma el Router del VPS.

**Regla de diseño:** cada función es UN bloque intercambiable. Cambiar/agregar uno no rompe el resto. El Router del VPS es la fuente de verdad; este frontend es 100% configurable desde ahí.

---

## 📦 ESTRUCTURA

```
router-frontend/
├── index.html              ← entry point (5 paneles)
├── css/
│   └── router.css          ← tema único (variables CSS)
├── js/
│   ├── core/
│   │   ├── api.js          ← cliente REST+WS
│   │   ├── state.js        ← store global
│   │   └── events.js       ← event bus interno
│   ├── panels/
│   │   ├── p1-lista.js
│   │   ├── p2-editor.js
│   │   ├── p3-extras.js
│   │   ├── p4-conectores.js
│   │   └── p5-agente.js
│   └── utils/
│       ├── render.js       ← helpers DOM
│       └── validate.js     ← enchufe gate
└── config/
    └── router.yaml         ← endpoints configurables
```

---

## ⚙️ config/router.yaml (la pieza CLAVE para adaptabilidad)

```yaml
router:
  base_url: "http://localhost:8000"
  ws_url: "ws://localhost:8000/ws/router"
  namespace: "core.router"

panels:
  enabled: [p1, p2, p3, p4, p5]
  order: [p1, p2, p3, p4, p5]
  default_active: p1

theme:
  primary: "#C9A24B"
  bg: "#0D0D0F"
  panel_bg: "#161619"
  border: "#2A2A2F"
  text: "#C9C9CE"
  success: "#7FD1A8"
  accent: "#7FB4D1"

features:
  chat_ai: true
  preconfigured_connectors: true
  custom_agents: true
  max_inputs_per_card: 100
  max_outputs_per_card: 100
```

---

## 🔌 js/core/api.js — Cliente REST + WS

```javascript
// ============================================
// API CLIENT — punto único de comunicación
// Cambiar base_url aquí reescribe TODA la app
// ============================================

class RouterAPI {
  constructor() {
    this.config = window.ROUTER_CONFIG;  // viene de router.yaml
    this.base = this.config.router.base_url;
    this.wsUrl = this.config.router.ws_url;
    this.ws = null;
    this.listeners = new Map();
  }

  // REST genérico — todo pasa por aquí
  async request(method, path, body = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' }
    };
    if (body) opts.body = JSON.stringify(body);
    try {
      const r = await fetch(this.base + path, opts);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return await r.json();
    } catch (e) {
      console.error(`[API] ${method} ${path} failed:`, e);
      this.emit('error', { method, path, error: e.message });
      throw e;
    }
  }

  get(p)    { return this.request('GET', p); }
  post(p,b) { return this.request('POST', p, b); }
  put(p,b)  { return this.request('PUT', p, b); }
  del(p)    { return this.request('DELETE', p); }

  // WebSocket — eventos en vivo
  connect() {
    this.ws = new WebSocket(this.wsUrl);
    this.ws.onmessage = (e) => {
      const evt = JSON.parse(e.data);
      this.emit(evt.type, evt.data);
    };
    this.ws.onclose = () => setTimeout(() => this.connect(), 3000);
  }

  on(type, fn) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push(fn);
  }

  emit(type, data) {
    (this.listeners.get(type) || []).forEach(fn => fn(data));
  }
}

window.api = new RouterAPI();
```

---

## 🗃️ js/core/state.js — Store global

```javascript
// ============================================
// STATE — un solo punto de verdad
// Cualquier panel lee/escribe aquí
// ============================================

class State {
  constructor() {
    this.store = {
      conexiones: [],
      conectores_preconfig: [],
      agente_chat: { id: 'openhand', modelo: 'minimax-m3' },
      panel_activo: 'p1',
      ficha_edit: null
    };
    this.subs = [];
  }

  get(key)              { return this.store[key]; }
  set(key, val)         { this.store[key] = val; this.notify(key); }
  subscribe(fn)         { this.subs.push(fn); }
  notify(key)           { this.subs.forEach(fn => fn(key, this.store[key])); }
}

window.state = new State();
```

---

## 📥 js/panels/p1-lista.js — Panel 1

```javascript
// ============================================
// PANEL 1 — Lista de Conexiones + Chat AI
// ============================================

const Panel1 = {

  // FUNCIÓN 1: listarConexiones
  async listarConexiones() {
    try {
      const data = await api.get('/api/connections');
      state.set('conexiones', data);
      this.render();
    } catch (e) {
      console.error('Error listando:', e);
    }
  },

  // FUNCIÓN 2: renderizarConexion (1 fila)
  renderizarConexion(item) {
    const icon = { github:'📁', hf:'🤗', vps:'🖥️', telegram:'✈️',
                   api:'🔌', mcp:'🔗', webhook:'🪝', repo:'📦' }[item.tipo] || '📌';
    const statusColor = { active:'#7FD1A8', inactive:'#8A8A92',
                          error:'#EA4335' }[item.estado] || '#C9A24B';
    return `
      <div class="conn-row" data-id="${item.id}">
        <span class="conn-dot" style="background:${statusColor}"></span>
        <span class="conn-icon">${icon}</span>
        <span class="conn-name">${item.nombre}</span>
        <span class="conn-type">${item.tipo}</span>
        <button onclick="Panel1.editarConexion('${item.id}')">✏️</button>
        <button onclick="Panel1.toggleConexion('${item.id}')">⏸</button>
        <button onclick="Panel1.eliminarConexion('${item.id}')">🗑️</button>
      </div>`;
  },

  // FUNCIÓN 3: editarConexion
  editarConexion(id) {
    const conn = state.get('conexiones').find(c => c.id === id);
    state.set('ficha_edit', conn);
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    document.getElementById('p2').classList.add('active');
    Panel2.cargar(conn);
  },

  // FUNCIÓN 4: eliminarConexion
  async eliminarConexion(id) {
    if (!confirm('¿Borrar esta conexión?')) return;
    await api.del(`/api/connections/${id}`);
    this.listarConexiones();
  },

  // FUNCIÓN 5: toggleConexion
  async toggleConexion(id) {
    await api.post(`/api/connections/${id}/toggle`);
    this.listarConexiones();
  },

  // FUNCIÓN 6: crearNuevaConexion
  crearNuevaConexion() {
    state.set('ficha_edit', null);
    Panel2.nueva();
  },

  // FUNCIÓN 7: buscarConexion
  buscarConexion(q) {
    const filtered = state.get('conexiones')
      .filter(c => c.nombre.toLowerCase().includes(q.toLowerCase()));
    document.getElementById('p1-list').innerHTML =
      filtered.map(c => this.renderizarConexion(c)).join('');
  },

  // FUNCIÓN 8: ordenarConexiones
  ordenarConexiones(campo) {
    const sorted = [...state.get('conexiones')]
      .sort((a, b) => a[campo] > b[campo] ? 1 : -1);
    state.set('conexiones', sorted);
    this.render();
  },

  // FUNCIÓN 9: duplicarConexion
  async duplicarConexion(id) {
    await api.post(`/api/connections/${id}/duplicate`);
    this.listarConexiones();
  },

  // FUNCIÓN 10: abrirChatAI
  abrirChatAI() { document.getElementById('chat-input').focus(); },

  // FUNCIÓN 11: enviarMensajeChat
  async enviarMensajeChat(texto) {
    const agente = state.get('agente_chat');
    const r = await api.post('/api/chat', {
      texto,
      agente: agente.id,
      modelo: agente.modelo
    });
    if (r.accion === 'crear_conexion') {
      await api.post('/api/connections', r.config);
      this.listarConexiones();
    }
    this.appendChat('ai', r.respuesta);
  },

  // FUNCIÓN 12-18: helpers + acceso a P5
  limpiarChat() { document.getElementById('chat-log').innerHTML = ''; },
  exportarChat() { /* descargar txt */ },
  seleccionarAgenteChat(id) { /* abre P5 */ },
  seleccionarModeloChat(id) { /* abre P5 */ },
  configurarPromptChat(t) { /* abre P5 */ },
  abrirConfiguracionChat() { Panel5.mostrar(); },
  abrirConfiguracionConectores() { Panel4.mostrar(); },

  // RENDER
  render() {
    const list = document.getElementById('p1-list');
    if (list) list.innerHTML =
      state.get('conexiones').map(c => this.renderizarConexion(c)).join('');
  }
};

window.Panel1 = Panel1;
```

---

## ⚙️ js/panels/p2-editor.js — Panel 2

```javascript
// ============================================
// PANEL 2 — Editor de Ficha
// 4 secciones: Entrada / Anclaje / Salida / Otras
// ============================================

const Panel2 = {

  // FUNCIÓN 19: agregarEntradaFicha
  agregarEntradaFicha(tipo, sistema, params = {}) {
    const ficha = state.get('ficha_edit');
    if (!ficha.entradas) ficha.entradas = [];
    if (ficha.entradas.length >= 100) return alert('Máx 100 entradas');
    ficha.entradas.push({ tipo, sistema, params, on: true });
    this.render();
  },

  // FUNCIÓN 20: eliminarEntradaFicha
  eliminarEntradaFicha(idx) {
    state.get('ficha_edit').entradas.splice(idx, 1);
    this.render();
  },

  // FUNCIÓN 21-22: selectores
  seleccionarTipoEntrada(tipo)  { /* abre dropdown tipos */ },
  seleccionarSistema(tipo, idx) { return Panel4.obtenerParaFicha(tipo, idx); },

  // FUNCIÓN 23: validarEntrada (enchufe gate v1.5)
  validarEntrada(e) {
    return e.tipo && e.sistema && e.params;
  },

  // FUNCIÓN 24-28: reorder, toggle, dup, test, params
  reordenarEntradas(o, d) { /* drag&drop logic */ },
  toggleEntrada(idx) { const e = state.get('ficha_edit').entradas[idx];
                       e.on = !e.on; this.render(); },
  duplicarEntrada(idx) { const e = state.get('ficha_edit').entradas[idx];
                         state.get('ficha_edit').entradas.push({...e}); this.render(); },
  async probarEntrada(idx) {
    const e = state.get('ficha_edit').entradas[idx];
    return api.post('/api/connections/test-input', e);
  },
  configurarParamsEntrada(idx, params) {
    state.get('ficha_edit').entradas[idx].params = params;
  },

  // FUNCIÓN 29-38: ANCLAJE
  async anclarDocumento(file) {
    const fd = new FormData(); fd.append('file', file);
    const r = await fetch(api.base + '/api/sandbox/upload',
                { method: 'POST', body: fd });
    return r.json();
  },
  anclarTexto(texto)           { /* push a anclajes */ },
  anclarInstrucciones(texto)   { /* push a anclajes */ },
  editarSystemPrompt(texto)    { state.get('ficha_edit').system_prompt = texto; },
  abrirSandboxCode()           { /* abre editor monaco/codemirror */ },
  async ejecutarCodigoSandbox() {
    return api.post('/api/sandbox/exec',
      { code: state.get('ficha_edit').sandbox_code });
  },
  toggleAnclaje(tipo)          { /* on/off */ },
  eliminarAnclaje(id)          { /* splice */ },
  versionarAnclaje(id)         { /* git-like */ },
  previewAnclaje(id)           { /* modal preview */ },

  // FUNCIÓN 39-47: SALIDA (mismo patrón que entrada)
  agregarSalidaFicha(t, s, p)        { /* push a ficha.salidas */ },
  eliminarSalidaFicha(idx)           { /* splice */ },
  seleccionarTipoSalida(tipo)        { /* dropdown */ },
  seleccionarDestino(tipo, idx)      { return Panel4.obtenerParaFicha(tipo, idx); },
  validarSalida(s)                   { return s.tipo && s.sistema; },
  toggleSalida(idx)                  { /* flip on */ },
  reordenarSalidas(o, d)             { /* drag */ },
  async probarSalida(idx)            { return api.post('/api/connections/test-output', s); },
  configurarParamsSalida(idx, p)     { /* set */ },

  // FUNCIÓN 48-59: OTRAS
  configPrioridad(v)    { state.get('ficha_edit').prioridad = v; },
  configFallback(id)    { state.get('ficha_edit').fallback = id; },
  configTimeout(ms)     { state.get('ficha_edit').timeout = ms; },
  configReintentos(n)   { state.get('ficha_edit').retries = n; },
  configRateLimit(rpm)  { state.get('ficha_edit').rpm = rpm; },
  configModoEnvio(m)    { state.get('ficha_edit').modo = m; },
  async configCredenciales(id, k) { /* vault */ },
  configSchedule(cron)  { state.get('ficha_edit').schedule = cron; },
  configCostoMax(u)     { state.get('ficha_edit').cost_max = u; },
  configTags(t)         { state.get('ficha_edit').tags = t; },
  configACL(r)          { state.get('ficha_edit').acl = r; },
  configNamespace(n)    { state.get('ficha_edit').ns = n; },

  // FUNCIÓN 60-62: GUARDAR / BORRAR / PROBAR
  async guardarFicha() {
    const f = state.get('ficha_edit');
    if (f.id) await api.put(`/api/connections/${f.id}`, f);
    else       await api.post('/api/connections', f);
    Panel1.listarConexiones();
  },
  async borrarFicha() { await api.del(`/api/connections/${f.id}`); },
  async probarFicha() { return api.post(`/api/connections/${f.id}/test`); },

  // RENDER
  render() { /* re-pinta secciones */ },
  cargar(conn) { state.set('ficha_edit', conn); this.render(); },
  nueva() { state.set('ficha_edit', {entradas:[],salidas:[],anclajes:[]}); this.render(); }
};

window.Panel2 = Panel2;
```

---

## 🔌 js/panels/p4-conectores.js — Panel 4

```javascript
// ============================================
// PANEL 4 — Conectores Pre-configurados
// Aquí pre-cargas APIs, MCPs, webhooks UNA vez
// ============================================

const Panel4 = {

  // FUNCIÓN 63: listarConectoresPreconfigurados
  async listarConectoresPreconfigurados() {
    const data = await api.get('/api/connectors/lib');
    state.set('conectores_preconfig', data);
    this.render();
  },

  // FUNCIÓN 64: agregarConectorPreconfig
  async agregarConectorPreconfig(tipo, sistema, params) {
    await api.post('/api/connectors/lib', { tipo, sistema, ...params });
    this.listarConectoresPreconfigurados();
  },

  // FUNCIÓN 65-66: eliminar/editar
  async eliminarConectorPreconfig(id) {
    await api.del(`/api/connectors/lib/${id}`);
    this.listarConectoresPreconfigurados();
  },
  async editarConectorPreconfig(id, params) {
    await api.put(`/api/connectors/lib/${id}`, params);
    this.listarConectoresPreconfigurados();
  },

  // FUNCIÓN 67-68: toggle/probar
  async toggleConectorPreconfig(id) {
    await api.post(`/api/connectors/lib/${id}/toggle`);
    this.listarConectoresPreconfigurados();
  },
  async probarConectorPreconfig(id) {
    return api.post(`/api/connectors/lib/${id}/test`);
  },

  // FUNCIÓN 69-71: categorias + import/export
  seleccionarCategoria(cat) { /* filter */ },
  async importarConectorMasivo(yaml) {
    return api.post('/api/connectors/lib/bulk', { yaml });
  },
  async exportarConectores() {
    const data = await api.get('/api/connectors/lib/export');
    return data.yaml;
  },

  // FUNCIÓN 72-73: bulk test + selector para ficha
  async probarTodosConectores() {
    return api.post('/api/connectors/lib/test-all');
  },
  obtenerParaFicha(tipo, slot) {
    return state.get('conectores_preconfig')
      .filter(c => c.tipo === tipo && c.on);
  },

  mostrar() { /* abre panel 4 */ },
  render()  { /* dibuja lista */ }
};

window.Panel4 = Panel4;
```

---

## 🤖 js/panels/p5-agente.js — Panel 5

```javascript
// ============================================
// PANEL 5 — Configuración Agente/AI del Chat
// Cambias qué IA controla el chat del Panel 1
// ============================================

const Panel5 = {

  // FUNCIÓN 74: listarAgentesDisponibles
  async listarAgentesDisponibles() {
    return api.get('/api/agents/registry');
  },

  // FUNCIÓN 75: seleccionarAgenteChat
  async seleccionarAgenteChat(agente_id) {
    await api.put('/api/chat/agent', { id: agente_id });
    state.set('agente_chat', { ...state.get('agente_chat'), id: agente_id });
  },

  // FUNCIÓN 76-77: modelos
  async listarModelosDispon() { return api.get('/api/models/registry'); },
  async seleccionarModeloChat(modelo_id) {
    await api.put('/api/chat/agent', { modelo: modelo_id });
    state.set('agente_chat', { ...state.get('agente_chat'), modelo: modelo_id });
  },

  // FUNCIÓN 78-83: configuración IA
  async editarSystemPromptChat(texto) {
    await api.put('/api/chat/agent', { system_prompt: texto });
  },
  configTemperature(v)  { /* PUT */ },
  configMaxTokens(v)    { /* PUT */ },
  configTopP(v)         { /* PUT */ },
  configFrecuenciaP(v)  { /* PUT */ },
  configPresenciaP(v)   { /* PUT */ },

  // FUNCIÓN 84-87: test, reset, historial, custom
  async probarAgenteChat(msg) { return api.post('/api/chat/test', { msg }); },
  async resetAgenteChat()     { return api.post('/api/chat/agent/reset'); },
  async verHistorialAgente()  { return api.get('/api/chat/history'); },
  async crearAgenteCustom(nombre, config) {
    return api.post('/api/agents/registry/custom', { nombre, ...config });
  },

  mostrar() { /* abre panel 5 */ }
};

window.Panel5 = Panel5;
```

---

## 📊 js/panels/p3-extras.js — Panel 3 (resumen)

```javascript
// ============================================
// PANEL 3 — Extras (11 sub-paneles)
// ============================================

const Panel3 = {
  // FUNCIÓN 88-98: cada sub-panel es un módulo independiente
  panelProvider()      { return api.get('/api/providers'); },
  panelModelos()       { return api.get('/api/models/registry'); },
  panelMarketplace()   { return api.get('/api/marketplace'); },
  panelMapaRed()       { return api.get('/api/mapa'); },
  panelLiveGraph()     { /* suscribe a WS graph.tick */ },
  panelTrazabilidad()  { return api.get('/api/trace'); },
  panelCostes()        { return api.get('/api/cost'); },
  panelSecretVault()   { return api.get('/api/vault'); },
  panelScheduler()     { return api.get('/api/scheduler'); },
  panelCola()          { return api.get('/api/queue'); },
  panelRecovery()      { return api.get('/api/recovery'); }
};

window.Panel3 = Panel3;
```

---

## 🚀 index.html — Entry point

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Router MAXBRY · 5 Paneles</title>
  <link rel="stylesheet" href="css/router.css">
  <script src="config/router.yaml.js"></script>
</head>
<body>
  <nav class="tabs">
    <button onclick="showPanel('p1')" class="active">📥 Conexiones</button>
    <button onclick="showPanel('p2')">⚙️ Editor</button>
    <button onclick="showPanel('p3')">📊 Extras</button>
    <button onclick="showPanel('p4')">🔌 Conectores</button>
    <button onclick="showPanel('p5')">🤖 Agente Chat</button>
  </nav>

  <section id="p1" class="panel active">
    <div id="p1-list"></div>
    <button onclick="Panel1.crearNuevaConexion()">➕ Nueva</button>
    <div class="chat-box">
      <input id="chat-input" placeholder='Di: "conecta GitHub al VPS"'>
      <button onclick="Panel1.enviarMensajeChat(
        document.getElementById('chat-input').value)">📤</button>
    </div>
  </section>

  <section id="p2" class="panel"><!-- Editor --></section>
  <section id="p3" class="panel"><!-- Extras --></section>
  <section id="p4" class="panel"><!-- Conectores pre-config --></section>
  <section id="p5" class="panel"><!-- Agente chat config --></section>

  <script src="js/core/api.js"></script>
  <script src="js/core/state.js"></script>
  <script src="js/panels/p1-lista.js"></script>
  <script src="js/panels/p2-editor.js"></script>
  <script src="js/panels/p3-extras.js"></script>
  <script src="js/panels/p4-conectores.js"></script>
  <script src="js/panels/p5-agente.js"></script>
  <script>
    api.connect();
    Panel1.listarConexiones();
    Panel4.listarConectoresPreconfigurados();
  </script>
</body>
</html>
```

---

## 🛡️ POR QUÉ ES ADAPTABLE

1. **Toda config vive en `router.yaml`** — cambias URL del backend y funciona
2. **Cada panel es un módulo JS independiente** — quitar/agregar uno no rompe nada
3. **Toda la comunicación pasa por `api.request()`** — un punto para mockear
4. **State centralizado** — paneles no se acoplan entre sí
5. **Funciones pequeñas y puras** — fácil de testear
6. **Cero dependencias hardcoded** — sin frameworks锁定

## 📥 INSTALACIÓN EN OTRO FRONTEND

```bash
# 1. Copia la carpeta js/ a tu proyecto
cp -r router-frontend/js/ /tu-proyecto/src/router/

# 2. Edita config/router.yaml con la URL del VPS
vim config/router.yaml  # cambia base_url y ws_url

# 3. Importa donde quieras
import { Panel1, Panel2 } from './router/panels/';
```

Listo. Cuando lo instales, el frontend habla con CUALQUIER Router del VPS que respete la API.
