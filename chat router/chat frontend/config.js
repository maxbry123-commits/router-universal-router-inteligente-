// Configuracion del chat (solo interfaz; el codigo vive en GitHub y el computo en HF).
// La interfaz abre sin pedir clave. El Router funciona en HF CPU de 16 GB; las claves permanecen en el servidor.
window.RIU_CONFIG = {
  routerStopped: false,
  apiBase: 'https://6ac41820404719ba376595fb--8000.hf.jobs',
  liveUrl: 'https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/LIVE_URL.json',
  harnessUrl: 'https://6ac41820404719ba376595fb--8000.hf.jobs/plugins/puente_chat/call',  // puente dentro del Router (puerta fija)
  authHeader: 'X-API-Key',
  defecto: 'nv-kimi-k3',  // el modelo HF enciende una GPU de pago: no se deja como predeterminado
  modelos: [
    { id: 'ask-consil-factory', etiqueta: '🧠 ask consil factory' },
    { id: 'motor-descarga', etiqueta: '➡️ MOTOR DESCARGA EXTRACCIONES copiar mover' },
    { id: 'motor-xray', etiqueta: '🔬 MOTOR X-RAY auditoría forense' },
    { id: 'motor-auditor-code', etiqueta: '🔎 MOTOR AUDITOR CODE repo' },
    { id: 'hf-1-qwen-3-8', etiqueta: 'HF 1 Qwen 3.8 (27B)' },
    { id: 'hf-2-qwen-3-6', etiqueta: 'HF 2 Qwen 3.6 (35B)' },
    { id: 'groq-qwen-3-8', etiqueta: 'GROQ Qwen 3.8' },
    { id: 'nv-kimi-k3', etiqueta: 'NV Kimi K3' },
    { id: 'nv-glm-5-3', etiqueta: 'NV GLM 5.3' },
    { id: 'nv-nemotron-super', etiqueta: 'NV Nemotron 3 Super' },
    { id: 'nv-nemotron-lightning', etiqueta: 'NV Nemotron 3.5 Lightning' }
  ]
};
