// App principal · Router Universal UI

const STORAGE_sats = 'nct_router_sats';
const STORAGE_log = 'nct_router_log';
const STORAGE_cfg = 'nct_router_cfg';

let satellites = JSON.parse(localStorage.getItem(STORAGE_sats) || '[]');
let responses = JSON.parse(localStorage.getItem(STORAGE_log) || '[]');
let CFG = JSON.parse(localStorage.getItem(STORAGE_cfg) || '{}');

const DEFAULT_SATS = [
  { name: 'openclaw', url: 'http://95.111.232.89:7001', cap: 'text', transport: 'http', sandbox: 'native', online: false },
  { name: 'claude-code', url: 'http://95.111.232.89:7002', cap: 'code', transport: 'http', sandbox: 'native', online: false },
  { name: 'mimo-code', url: 'http://95.111.232.89:7003', cap: 'code', transport: 'http', sandbox: 'native', online: false },
  { name: 'nct', url: 'http://95.111.232.89:7004', cap: 'text', transport: 'http', sandbox: 'pyodide', online: false },
  { name: 'ocr', url: 'http://95.111.232.89:9001', cap: 'image', transport: 'http', sandbox: 'native', online: false },
  { name: 'obsidian', url: 'http://95.111.232.89:8001', cap: 'file', transport: 'http', sandbox: 'none', online: false },
  { name: 'graphiti', url: 'http://95.111.232.89:8002', cap: 'graph', transport: 'http', sandbox: 'none', online: false },
];

function init() {
  if (!satellites.length) {
    satellites = DEFAULT_SATS;
    saveSats();
  }
  if (!CFG.theme) CFG.theme = 'dark';
  applyTheme();
  applyColors();
  renderSidebar();
  renderResponses();
  Inspector.renderContract();
  Inspector.renderTopology(satellites);
  bindHandlers();
  // Health check inicial
  checkAllHealth();
  setInterval(checkAllHealth, 30000);
}

function bindHandlers() {
  document.getElementById('sendBtn').onclick = sendOne;
  document.getElementById('broadcastBtn').onclick = sendBroadcast;
  document.getElementById('clearBtn').onclick = () => {
    responses = []; saveResponses(); renderResponses();
    showToast('🗑 Limpio');
  };
  document.getElementById('satSearch').oninput = renderSidebar;
  document.getElementById('addSatellite').onclick = () => document.getElementById('addSatBackdrop').classList.add('open');
  document.getElementById('closeAddSat').onclick = () => document.getElementById('addSatBackdrop').classList.remove('open');
  document.getElementById('cancelAddSat').onclick = () => document.getElementById('addSatBackdrop').classList.remove('open');
  document.getElementById('saveAddSat').onclick = addSatellite;
  document.getElementById('openSettings').onclick = () => {
    document.getElementById('routerBaseUrl').value = CFG.baseUrl || '';
    document.getElementById('hmacSecret').value = CFG.secret || '';
    document.getElementById('userColor').value = CFG.colors?.user || '#00b8ff';
    document.getElementById('modelColor').value = CFG.colors?.model || '#c9d1d9';
    document.getElementById('titleColor').value = CFG.colors?.title || '#00d4aa';
    document.getElementById('bgColor').value = CFG.colors?.bg || '#000000';
    document.getElementById('settingsBackdrop').classList.add('open');
  };
  document.getElementById('closeSettings').onclick = () => document.getElementById('settingsBackdrop').classList.remove('open');
  document.getElementById('saveSettings').onclick = saveSettings;
  document.getElementById('toggleTheme').onclick = () => {
    CFG.theme = CFG.theme === 'dark' ? 'light' : 'dark';
    saveCfg(); applyTheme();
  };
  // Tabs
  document.querySelectorAll('.tab-btn').forEach(b => b.onclick = () => {
    document.querySelectorAll('.tab-btn').forEach(x => x.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    document.getElementById('tab-' + b.dataset.tab).classList.add('active');
    if (b.dataset.tab === 'topology') Inspector.renderTopology(satellites);
  });
  // Modals backdrop click
  document.querySelectorAll('.modal-backdrop').forEach(b => b.onclick = e => {
    if (e.target === e.currentTarget) e.currentTarget.classList.remove('open');
  });
}

function renderSidebar() {
  const search = document.getElementById('satSearch').value.toLowerCase();
  const filtered = satellites.filter(s => !search || s.name.toLowerCase().includes(search));
  const list = document.getElementById('satList');
  list.innerHTML = filtered.map(s => `
    <li class="${s.online ? 'online' : ''}" onclick="selectSatellite('${s.name}')">
      <span class="sat-dot"></span>
      <span style="flex:1">${s.name}</span>
      <span class="sat-cap">${s.cap || '?'}</span>
    </li>
  `).join('');
  document.getElementById('satCount').textContent = `${satellites.length} satélites`;
  document.getElementById('routerState').innerHTML = satellites.some(s => s.online) ? '<span style="color:#00d4aa">● online</span>' : '<span style="color:#ff6b6b">○ offline</span>';
}

window.selectSatellite = name => {
  const sat = satellites.find(s => s.name === name);
  if (!sat) return;
  document.querySelectorAll('.sat-list li').forEach(li => li.classList.remove('active'));
  event.currentTarget && event.currentTarget.classList.add('active');
  Inspector.renderInspector(sat);
  // Activar tab inspector
  document.querySelector('.tab-btn[data-tab="inspector"]').click();
};

window.testSatellite = async name => {
  const sat = satellites.find(s => s.name === name);
  if (!sat) return;
  showToast('🔬 Testeando ' + name + '...');
  const ok = await RouterClient.health(sat);
  sat.online = ok;
  saveSats(); renderSidebar();
  showToast(ok ? `✅ ${name} online` : `❌ ${name} offline`);
};

window.deleteSatellite = name => {
  if (!confirm('¿Eliminar satélite ' + name + '?')) return;
  satellites = satellites.filter(s => s.name !== name);
  saveSats(); renderSidebar(); Inspector.renderTopology(satellites);
  showToast('Satélite eliminado');
};

function addSatellite() {
  const name = document.getElementById('newSatName').value.trim();
  const url = document.getElementById('newSatUrl').value.trim();
  if (!name || !url) return showToast('⚠️ Nombre y URL requeridos');
  if (satellites.find(s => s.name === name)) return showToast('⚠️ Nombre ya existe');
  satellites.push({
    name, url,
    cap: document.getElementById('newSatCap').value,
    transport: document.getElementById('newSatTransport').value,
    sandbox: document.getElementById('newSatSandbox').value,
    online: false,
  });
  saveSats(); renderSidebar(); Inspector.renderTopology(satellites);
  document.getElementById('addSatBackdrop').classList.remove('open');
  showToast('✓ Satélite agregado');
}

async function checkAllHealth() {
  for (const s of satellites) {
    try {
      s.online = await RouterClient.health(s);
    } catch { s.online = false; }
  }
  saveSats(); renderSidebar(); Inspector.renderTopology(satellites);
}

async function sendOne() {
  const name = satellites.find(s => document.querySelector(`.sat-list li.active`))?.name;
  if (!name) return showToast('⚠️ Selecciona un satélite');
  const sat = satellites.find(s => s.name === name);
  let payload;
  try { payload = JSON.parse(document.getElementById('payloadEditor').value); }
  catch { return showToast('⚠️ Payload debe ser JSON válido'); }
  const opts = {
    kind: document.getElementById('capabilitySelect').value,
    transport: document.getElementById('transportSelect').value,
    sandbox: document.getElementById('sandboxSelect').value,
    timeoutMs: parseInt(document.getElementById('timeoutMs').value) || 30000,
  };
  if (CFG.secret) RouterClient.secret = CFG.secret;
  showToast('▶ Enviando a ' + name + '...');
  const r = await RouterClient.send(sat, payload, opts);
  responses.unshift({ ...r, sat: name, ts: Date.now() });
  if (responses.length > 100) responses = responses.slice(0, 100);
  saveResponses(); renderResponses();
  Inspector.selectResponse(r);
  showToast(r.ok ? '✅ Respuesta OK' : '❌ ' + (r.error || 'fail'));
}

async function sendBroadcast() {
  let payload;
  try { payload = JSON.parse(document.getElementById('payloadEditor').value); }
  catch { return showToast('⚠️ Payload debe ser JSON válido'); }
  const opts = {
    kind: document.getElementById('capabilitySelect').value,
    sandbox: document.getElementById('sandboxSelect').value,
    timeoutMs: parseInt(document.getElementById('timeoutMs').value) || 30000,
  };
  if (CFG.secret) RouterClient.secret = CFG.secret;
  showToast('📡 Broadcast a ' + satellites.length + ' satélites...');
  const results = await RouterClient.broadcast(payload, satellites, opts);
  for (let i = 0; i < results.length; i++) {
    responses.unshift({ ...results[i], sat: satellites[i].name, ts: Date.now() });
  }
  if (responses.length > 100) responses = responses.slice(0, 100);
  saveResponses(); renderResponses();
  const ok = results.filter(r => r.ok).length;
  showToast(`📡 ${ok}/${results.length} respondieron`);
}

function renderResponses() {
  const list = document.getElementById('responseList');
  list.innerHTML = responses.map((r, i) => `
    <div class="response-card ${r.ok ? 'ok' : 'err'}" onclick="Inspector.selectResponse(responses[${i}])">
      <div class="response-card-h">
        <span class="sat-name">${r.sat}</span>
        <span class="art-id">${r.artifact?.artifact_id?.slice(0, 18) || '—'}</span>
        <span style="color:${r.ok ? '#00d4aa' : '#ff6b6b'}">${r.ok ? '✓' : '✗'} ${r.status || ''}</span>
      </div>
      <div class="response-card-b">${r.ok ? JSON.stringify(r.result, null, 2).slice(0, 400) : (r.error || '—')}</div>
    </div>
  `).join('') || '<p class="hint">Sin respuestas aún. Envía un payload para empezar.</p>';
  document.getElementById('responseCount').textContent = `${responses.length} respuestas`;
}

function saveSettings() {
  CFG.baseUrl = document.getElementById('routerBaseUrl').value;
  CFG.secret = document.getElementById('hmacSecret').value;
  CFG.colors = {
    user: document.getElementById('userColor').value,
    model: document.getElementById('modelColor').value,
    title: document.getElementById('titleColor').value,
    bg: document.getElementById('bgColor').value,
  };
  saveCfg(); applyColors();
  document.getElementById('settingsBackdrop').classList.remove('open');
  showToast('✓ Settings guardados');
}

function applyTheme() {
  document.documentElement.dataset.theme = CFG.theme || 'dark';
}

function applyColors() {
  const c = CFG.colors || {};
  const root = document.documentElement.style;
  if (c.user) root.setProperty('--user-color', c.user);
  if (c.model) root.setProperty('--model-color', c.model);
  if (c.title) root.setProperty('--title-color', c.title);
  if (c.bg) root.setProperty('--bg-color', c.bg);
}

function saveSats() { localStorage.setItem(STORAGE_sats, JSON.stringify(satellites)); }
function saveResponses() { localStorage.setItem(STORAGE_log, JSON.stringify(responses)); }
function saveCfg() { localStorage.setItem(STORAGE_cfg, JSON.stringify(CFG)); }

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove('show'), 2500);
}

// Init
init();
console.log('[Router Universal UI v1.0] ready · ' + satellites.length + ' satélites · ' + responses.length + ' respuestas');