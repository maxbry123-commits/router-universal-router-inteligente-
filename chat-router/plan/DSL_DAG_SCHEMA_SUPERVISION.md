# DSL DAG — Esquema de supervisión (S-1)

**Rama:** `ccr-f01c3de9-bmry0s` · **Fecha:** 2026-11-09 · **Plan:** `chat-router/plan/PLAN_PASOS_1_A_5.md`
**Input block verificado:** `kernel/INPUT_BLOCK_YAIWES_CABLEADO.md`, rama `ccr-4806d6f4-xv37ed`, commit `f13f38ab738c4fbdc3a4d370914bb241ee95734a`.

Este esquema lo usan todos los sub-agentes (S-1, A-1 a A-6, C-1, C-2) para declarar su trabajo.

---

## 1. Regla de supervisión

- **El centinela supervisa; el orquestador no.** S-1 verifica el input block y las reglas, y emite PASS o 🚩 sobre cada nodo. El orquestador reparte tareas y consolida, pero no emite PASS sobre trabajo propio.
- Ningún sub-agente se marca PASS a sí mismo. El PASS lo confirma S-1 con evidencia.
- El sandbox solo lo usan A-1 y C-1. S-1 vigila que nadie lo use fuera de esa regla.

## 2. Esquema mínimo de nodo

Cada sub-agente publica un bloque con estos campos:

```yaml
id: A-2                        # S-1 | A-1 ... A-6 | C-1 | C-2
rol: backend-router            # función del sub-agente
tareas:                        # máximo 3
  - p1: cablear selector > chat > harness DeepSeek HTTP > Router MVP v1 / LLM HF
deps: [p1]                     # nodos que deben cerrar antes (vacío si ninguno)
sandbox: no                    # "sí" solo para A-1 y C-1
criterio_cierre:              # todos obligatorios
  - cableado real en la ruta indicada
  - prueba funcional de C-1 con respuesta real
  - tiempo de respuesta registrado
entregable:
  tipo: commit                 # commit | informe | resultados
  url: https://github.com/...  # obligatorio para PASS
evidencia:
  ubicacion: ruta del código responsable
  consumidor: quién llama
  proveedor: quién responde
  prueba: resultado de la ejecución
estado: PASS                   # PASS | 🚩
```

## 3. Reglas de estado y de ejecución

1. **PASS** solo si todos los criterios de cierre tienen evidencia con URL y S-1 lo confirma.
2. **Configurado no es activo.** Una conexión no pasa a PASS por superar una prueba superficial. Se aplica el umbral de 7 condiciones del input block (§4.4). Los estados del registro (DISCOVERED → CONFIGURED → TESTING → ACTIVE; FAILED / BLOCKED / DEPRECATED / ORPHANED) se toman del input block (§0), no de este esquema.
3. **Bloqueos:** se marcan 🚩 con evidencia. No se escala; se listan al final.
4. **Claves:** ningún campo ni entregable contiene credenciales. Van solo por entorno.
5. **Motor `research_prepass.py` (línea 89):** intocable sin autorización expresa del owner.
6. **Sin GitHub Actions ni LFS.** Los tests corren en local o como Job de HF `cpu-upgrade`.
7. **Vercel y Hugging Face:** ninguna escritura sin autorización expresa.

## 4. Asignación de sub-agentes (según el plan)

| Id | Rol | Sandbox | Nodo |
|---|---|---|---|
| S-1 | supervisor | no | verificación de input block y reglas |
| A-1 | frontend | **sí** | p1b, p1c |
| A-2 | backend-router | no | p1 |
| A-3 | almacenamiento | no | p2 |
| A-4 | llm-locales | no | p3 |
| A-5 | proveedores | no | p4 |
| A-6 | pendientes-CC4 | no | p5 |
| C-1 | centinela 1 (tests) | **sí** | pruebas de p1, p1b |
| C-2 | centinela 2 (gaps y limpieza) | no | cierre: sandbox limpio |

---

## Verificación del input block

Verificado contra `kernel/INPUT_BLOCK_YAIWES_CABLEADO.md` (commit `f13f38ab738c4fbdc3a4d370914bb241ee95734a`).

| # | Punto del input block | Sección | Resultado | Nota |
|---|---|---|---|---|
| 1 | Sin GitHub Actions | §5, §6 | PASS | El esquema no define ni invoca Actions. |
| 2 | Sin LFS | §6 | PASS | Ninguna entrega usa LFS. |
| 3 | Vercel y HF sin autorización expresa | §6 | 🚩 | El plan p5 incluye "limpieza HF"; la lista de MiniMax no existe en el repo (🚩 abierto #1 del plan). Hace falta autorización expresa antes de escribir en HF. Este esquema no la concede. |
| 4 | Claves no expuestas ni tocadas | §1, §6 | PASS | Sin campos de credenciales; claves NVIDIA/Groq solo por entorno. |
| 5 | Motor `research_prepass.py` intacto | §6 | PASS | Regla 5 del esquema; ningún nodo del plan lo modifica. |
| 6 | Servidores de pago de 32 GB RAM/CPU | §4.1 | PASS | El esquema no define infraestructura; no contradice la política. |
| 7 | Umbral ACTIVE: no activar por prueba superficial | §1, §4.4 | PASS | Regla 2 y criterio de evidencia; PASS exige ejecución real. |
| 8 | Estructura de raíces canónicas | §0 | 🚩 | La ruta `chat-router/` no figura entre las raíces canónicas. Se mantiene por instrucción explícita del plan; el owner debe decidir si se mueve a una raíz canónica. |
| 9 | Cobertura de las 12 fases | §5 | 🚩 | El plan p1 a p5 no cubre las fases 1 (auditoría histórica), 2 (auditoría actual), 3 (registro central `connections/wiring_registry.yaml`), 4 (contratos del harness), 5 (System Prompt), 7 (guardianes), 10 (Job Test J01 a J13), 11 (automatización) ni 12 (cierre). |
| 10 | Orden exacto de ejecución | §5 | 🚩 | El plan marca p5 como "independiente" y empieza por Chat YAIWES. El input block exige auditoría, registro, contratos y System Prompt antes de Chat YAIWES. |
| 11 | Criterio final de aceptación (5 puntos) | §3 | PASS | El bloque de evidencia exige ubicación, consumidor, proveedor, prueba y URL. |
| 12 | Input block en modo VERBATIM, solo lectura | §7 | PASS | No se modifica el fichero del input block. |

**Resultado global:** 🚩. Ocho puntos PASS y cuatro 🚩 (3, 8, 9 y 10). Los 🚩 no bloquean crear este esquema. Sí impiden cerrar el plan: el cierre exige S-1 PASS, y el input block no está cubierto por completo.
