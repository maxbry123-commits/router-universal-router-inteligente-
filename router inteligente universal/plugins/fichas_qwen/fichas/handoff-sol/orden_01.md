# 10 ÓRDENES DE CORRECCIÓN — QWEN / YAIWES

**Repositorio:** `maxbry123-commits/router-universal-router-inteligente-` · **Rama:** `feat/modos-router`  
**Alcance:** `plugins/puente_chat/`, `plugins/fichas_qwen/`. No modificar el Router principal, Vercel ni HF Jobs. No añadir agentes.  
**Regla:** aplicar por orden → prueba real → conservar aprobación y receipts → registrar PASS/FAIL → no fusionar si falla.

## ORDEN 01 — GLM 5.2: activar `tool_stream` solo para Function Calling

**Archivo:** `router inteligente universal/plugins/fichas_qwen/fichas/politicas_modelo.json`.

En `politicas_modelo.ficha-glm52.con_tools`, cambiar solo:

```json
"tool_stream": true
```

En `router inteligente universal/plugins/puente_chat/plugin.py`, la función `_extras()` ya propaga `tool_stream` cuando hay herramientas; comprobarlo. No aplicarlo globalmente a otros modelos.

```python
# Contrato existente en _extras(pol, tools):
if tools and (pol.get('con_tools') or {}).get('tool_stream'):
    ex['tool_stream'] = True
```

**PASS:** `ficha-glm52` recibe `tool_stream=True` únicamente con tools; SSE recompone `function.name` y `arguments` hasta obtener JSON válido; la herramienta se ejecuta. **FAIL:** HTTP 400, argumentos parciales o cero ejecuciones: revertir solo este ajuste y documentar el mensaje real del proveedor.