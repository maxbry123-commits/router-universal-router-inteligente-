// Configuracion del chat (solo interfaz; el codigo vive en GitHub y el computo en HF).
// La pagina habla con el HARNESS DeepSeek, y el harness con las fichas de modelos. Las claves NUNCA van aqui.
window.RIU_CONFIG = {
  apiBase: '',
  harnessUrl: '',  // PENDIENTE: direccion HTTP del harness DeepSeek (la entrega el equipo de Opus)
  puerta: 'https://comand-center-1-claude-github-mcp-backup.hf.space',  // puerta fija del Router: no cambia nunca
  authHeader: 'X-API-Key',
  modelos: [
    { id: 'ficha-kimi-k3', etiqueta: 'Kimi K3 (NVIDIA)' },
    { id: 'ficha-glm-5', etiqueta: 'GLM 5.3 (NVIDIA)' },
    { id: 'ficha-nemotron-super', etiqueta: 'Nemotron 3 Super 120B (NVIDIA)' },
    { id: 'ficha-groq-qwen', etiqueta: 'Qwen 3.8 (Groq)' },
    { id: 'ficha-nemotron-lightning', etiqueta: 'Nemotron 3.5 Lightning (NVIDIA)' },
    { id: 'respaldo-27b', etiqueta: 'Respaldo HF L4: Qwen 3.8 27B (plan y revision)' },
    { id: 'respaldo-35b', etiqueta: 'Respaldo HF L4: Qwen 3.6 35B (codigo)' }
  ]
};
