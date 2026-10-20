# 10 ÓRDENES DE CORRECCIÓN — QWEN / YAIWES

**Repositorio:** `maxbry123-commits/router-universal-router-inteligente-` · **Rama:** `feat/modos-router`  
**Alcance:** `plugins/puente_chat/`, `plugins/fichas_qwen/`. No modificar el Router principal, Vercel ni HF Jobs. No añadir agentes.  
**Regla:** aplicar por orden → prueba real → conservar aprobación y receipts → registrar PASS/FAIL → no fusionar si falla.

## ORDEN 07 — LOOP CODE: evidencia exclusiva de cada vuelta y cierre verificable

**Archivos:** `plugins/fichas_qwen/plugin.py` y `plugins/fichas_qwen/modos/motor_objetivo.py`.

**A.** En `_correr_objetivo`, dentro de `llamar(modo, prompt)`, sustituir la rama `modo == 'code'` que llama al DAG por:

```python
if modo == 'code' and str(ficha.get('ficha') or '') in (
    'ficha2-dag-codigo', 'ficha3-frontend'
):
    import re as _re_m
    encontrado = _re_m.search(r'TAREA ACTUAL\s*\((T\d+)\)', prompt)
    tid = encontrado.group(1) if encontrado else 'SIN_ID'
    opts_vuelta = dict(opts)
    opts_vuelta['herr'] = {}
    opts_vuelta['recibo_tarea'] = 'MOTOR:' + tid
    try:
        r_final, _tr = _correr(ficha, prompt, elegido, pid, opts_vuelta)
    except Exception as exc:
        return {
            'texto': 'GAP ' + str(exc)[:200],
            'herramientas_ok': 0,
            'mutaciones_ok': 0,
        }
    evidencias = [
        item
        for valores in opts_vuelta.get('herr', {}).values()
        for item in valores
        if isinstance(item, dict)
    ]
    opts.setdefault('herr', {}).setdefault('MOTOR', []).extend(evidencias)
    return {
        'texto': str(r_final),
        'herramientas_ok': sum(bool(x.get('ok')) for x in evidencias),
        'mutaciones_ok': sum(
            bool(x.get('ok') and x.get('mutacion_real'))
            for x in evidencias
        ),
    }
```

**B.** En `motor_objetivo.py`, sustituir el bloque desde `j = _json_de(r['texto'])` hasta antes de `if j.get('estado') == 'hecho'...` por:

```python
j = _json_de(r.get('texto') or '') or {}
if not j:
    j = {
        'tarea': t['id'],
        'estado': 'sigue',
        'resultado': 'Falta resultado JSON verificable',
        'evidencia': '',
        'nuevas_tareas': [],
        'nota_siguiente': 'Revisar evidencia real del DAG',
    }
modo_actual = t.get('modo') or 'code'
ok_ev = (
    int(r.get('mutaciones_ok') or 0) > 0
    if modo_actual == 'code'
    else int(r.get('herramientas_ok') or 0) > 0
        or modo_actual in ('rapido', 'planificador')
)
```

Conservar el condicional siguiente `if j.get('estado') == 'hecho' and ok_ev:`. Las tareas CODE con cambios deben acreditar **mutación real**, no solamente una lectura. El verificador final de pruebas y destino sigue siendo obligatorio.

**PASS:** una herramienta de lectura no cierra una tarea de modificación; un informe narrativo no se convierte automáticamente en `hecho`; cada vuelta tiene evidencia propia.