# Memoria y almacenamiento (cascada)

Todo pasa por una sola puerta: `/almacen` del Router (`mvp/hf_store.py`), que escribe en HF (bucket `yaiwes-memoria-storage`). GitHub guarda solo código.

```
Banco (claves, cifrado) ──► Router ──► /almacen ──► HF
                              │
 Control del chat ────────────┤  chat_estado/control.json  (ON/OFF, conexiones sin secretos, pendientes, salas, yaiwes.md, sandbox, agentes)
 Archivos subidos ────────────┤  chat_archivos/<espacio>/<nombre>
 Anclajes (archivo/foto/nota/URL) ─┘  se leen de /almacen al armar cada mensaje
```

**Cascada hacia el modelo** en cada mensaje (`_chat_ficha`): formato ➡️ system prompt (si ON) ➡️ modo ➡️ constitución + yaiwes.md + sandbox + pendientes ➡️ anclados ➡️ conversación ➡️ Harness (que usa `almacen`, `pendientes`, `sala`, `yaiwes_md` por MCP).
**Si HF falla:** el estado sigue en memoria y la interfaz avisa que no se guardará tras reiniciar.
**Límites conocidos:** `secreto:` nunca viaja al modelo; la lectura inicial fallida puede sobrescribir lo remoto con la memoria (documentado en CHAT_CONTROLES).
