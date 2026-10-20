# 10 ÓRDENES DE CORRECCIÓN — QWEN / YAIWES

**Repositorio:** `maxbry123-commits/router-universal-router-inteligente-` · **Rama:** `feat/modos-router`  
**Alcance:** `plugins/puente_chat/`, `plugins/fichas_qwen/`. No modificar el Router principal, Vercel ni HF Jobs. No añadir agentes.  
**Regla:** aplicar por orden → prueba real → conservar aprobación y receipts → registrar PASS/FAIL → no fusionar si falla.

## ORDEN 05 — Modo agéntico: garantizar catálogo READ sin elevar permisos WRITE

**Archivo:** `router inteligente universal/plugins/puente_chat/plugin.py` · función `_chat`.

En el bloque que calcula `_cap_c = _cap_chat(pregunta)` cuando el llamante no suministra capacidades, insertar inmediatamente después:

```python
if _cap_c == 'none' and (
    p.get('requiere_tools') is True
    or str(p.get('perfil') or '') in ('code', 'auditoria')
):
    _cap_c = 'read'
```

Mantener las líneas existentes:

```python
_CAP_TOOLS.set(_cap_c)
_TOOLS_HAB.set(_cap_c != 'none')
```

En `plugins/fichas_qwen/plugin.py`, dentro de `_llamar_harness`, conservar la lógica existente `escribe = _escribe_nodo(...)` y `cap_nodo='write'` **solo** si el nodo está autorizado/aprobado. No sustituir el control de aprobación por un detector de palabras.

**PASS:** una tarea CODE con `requiere_tools=True` obtiene al menos READ; preguntas normales siguen con CAP_NONE; las escrituras sin `/aprobar` continúan bloqueadas.