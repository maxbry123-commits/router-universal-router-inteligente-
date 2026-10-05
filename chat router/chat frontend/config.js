// Configuracion del chat (solo interfaz; el codigo vive en GitHub y el computo en HF).
// La pagina habla con el puente /api/chat (hace el papel del harness DeepSeek). Los tokens NUNCA van aqui.
window.RIU_CONFIG = {
  apiBase: '',
  harnessUrl: '/api/chat',
  authHeader: 'X-API-Key',
  defecto: 'nv-kimi-k3',  // el modelo HF enciende una GPU de pago: no se deja como predeterminado
  modelos: [
    { id: 'hf-1-qwen-3-8', etiqueta: 'HF 1 Qwen 3.8 (27B)' },
    { id: 'hf-2-qwen-3-6', etiqueta: 'HF 2 Qwen 3.6 (35B)' },
    { id: 'groq-qwen-3-8', etiqueta: 'GROQ Qwen 3.8' },
    { id: 'nv-kimi-k3', etiqueta: 'NV Kimi K3' },
    { id: 'nv-glm-5-3', etiqueta: 'NV GLM 5.3' },
    { id: 'nv-nemotron-super', etiqueta: 'NV Nemotron 3 Super' },
    { id: 'nv-nemotron-lightning', etiqueta: 'NV Nemotron 3.5 Lightning' }
  ]
};
