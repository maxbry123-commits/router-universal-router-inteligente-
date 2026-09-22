# ➡️🛜 README — OSQUESTADOR DEL ROUTER INTELIGENTE (Microsoft Agent Framework + Grok) — plantilla NCT/APEX aplicada

Fecha: 2026-09-22. Estado: **planificación, nada instalado todavía.** Los dos orquestadores que pidió el Director:
1. **Microsoft Agent Framework** (`microsoft/agent-framework`, MIT, confirmado real — sucesor de Semantic Kernel y AutoGen, con flujos por grafo, checkpoints, y adaptadores para NVIDIA/Anthropic/Azure/Ollama) → orquestador CENTRAL de TODO el Router Inteligente Universal.
2. **Grok** (xAI) → orquestador de los agentes DEL CHAT. **Corrección importante: Grok es cerrado, solo por API de pago — no se puede "descargar" como los modelos abiertos.** Falta que el Director dé una clave de API antes de conectarlo.

Su ayudante en ambos casos: el **centinela** (sheriff / policy / guardián / juez), con Qwen 0.6B + Liquid 1B — pedido antes, todavía sin construir.

---

## Plantilla del Director (NCT/APEX), aplicada sin reducir nada

### P1 — El orquestador sigue el carril (21 ítems)
**Grupo 1 · Ubicación y puntero**
1. IP visible en cada mensaje (modo + tarea + paso N de X)
2. Cada mensaje muestra estado actual antes de actuar
3. No puede avanzar sin completar el paso anterior

**Grupo 2 · Carga mínima de contexto**
4. Solo carga la state card del modo activo
5. Archiva lo que ya no necesita antes de cargar lo nuevo
6. Límite configurable por modelo — no valor fijo

**Grupo 3 · Gates y checklist**
7. Gate = checklist booleano ✅/❌ — nunca texto libre
8. Contrato define la regla exacta — no el modelo
9. Si gate falla → PARA + registra motivo + paso + timestamp
10. No continúa hasta que Director resuelve el fallo

**Grupo 4 · Visibilidad de estado**
11. Header fijo (FSM/TASKS/JUEZ) en cada respuesta
12. Mapa mental visible en cada segmento
13. Footer con siguiente acción siempre explícito

**Grupo 5 · FSM + Permisos + Precondiciones**
14. FSM define qué acciones están permitidas en cada estado
15. Verificar permisos antes de ejecutar — si NO → gate falla
16. Verificar precondiciones del GRAFO antes de arrancar
17. Registro de rechazo: motivo + paso + timestamp

**Grupo 6 · Anti-Deriva**
18. Comparar objetivo declarado vs respuesta generada
19. Detectar trabajo no solicitado
20. Detectar contenido fuera del segmento activo
21. Si hay deriva → HALT + reportar al Director

### P2 — El orquestador no olvida (19 ítems)
**Grupo 1 · Medir lo que queda**
1. Sabe cuántos tokens le quedan en tiempo real
2. Alerta a 80% de uso — no espera a llenarse
3. Umbral configurable por modelo

**Grupo 2 · Dividir el trabajo**
4. Divide objetivo en micro-tareas ≤ límite configurable
5. Una micro-tarea a la vez — no mezcla
6. Cada micro-tarea tiene contrato: entrada/salida/criterio

**Grupo 3 · Trazar y detectar invención**
7. Registra input_hash + output_hash por tarea
8. Mide fidelidad — si baja de umbral → HALT
9. Detecta síntesis automática antes de que ocurra

**Grupo 4 · Archivar lo que no necesita**
10. A 80% tokens → archiva traces antiguos
11. Solo mantiene activo: kernel + state card + tarea actual
12. Lo archivado es recuperable — no se pierde

**Grupo 5 · Recuperarse solo**
13. Lee último checkpoint al arrancar
14. Reconstruye IP + modo + estado en menos de 3 mensajes
15. 1 segmento = 1 MD = puntero — no vive en memoria
16. Pegar CORE + SEGMENTO activo → continúa sin explicar de 0

**Grupo 6 · Arrastre mínimo**
17. Solo arrastra: estado actual + frontera activa (3-5 piezas)
18. No arrastra todo lo aprobado — solo resumen por rama
19. Pendientes clasificados: READY / BLOCKED / WAITING

### P3 — El orquestador no miente ni contradice (20 ítems)
**Grupo 1 · Fuente única de verdad activa**
1. ACTIVE_TRUTH = CORE.ESTADO + SEGMENTO_ACTIVO
2. Todo se valida contra eso — no opiniones ni inferencias
3. Jerarquía: CORE > CONTRATOS > DECISIONES > SEGMENTO > GRAFO

**Grupo 2 · Detección de contradicciones**
4. Compara DECISIONES.json vs GRAFO.json vs SEGMENTO_X vs CORE.estado
5. Tipos de conflicto: dato / regla / estado
6. Si hay conflicto → NO avanza — gate falla

**Grupo 3 · Resolución formal P3-A/B/C/D**
7. P3-A Detección: identificar qué archivos contradicen
8. P3-B Validación: clasificar tipo de conflicto
9. P3-C Resolución: aplicar jerarquía — CORE gana siempre
10. P3-D Confirmación: estado validado antes de continuar

**Grupo 4 · Rollback obligatorio**
11. Si inconsistencia crítica → volver a último checkpoint válido
12. Reconstruir desde CORE + SEGMENTO activo
13. Registrar: qué falló + motivo + timestamp

**Grupo 5 · Flujo global del kernel**
14. INPUT → P1 ejecuta → P2 guarda → P3 valida → OUTPUT estable
15. Si P3 falla → rollback a P2 → re-ejecutar desde P1
16. El sistema solo avanza si P3 valida consistencia

**Grupo 6 · Conexión con los 10 archivos**
17. SELF_CHECK ejecuta P3 antes de cada respuesta
18. INVARIANTES define las reglas que P3 verifica
19. CONTRATOS define postcondiciones que P3 confirma
20. DECISIONES registra cada resolución de conflicto

### Mapa mental (10 vistas) — aplicado al Router Inteligente Universal
```
══════════════════════════════════════
🧩 ROUTER INTELIGENTE UNIVERSAL — Mapa Mental (osquestadores)
══════════════════════════════════════

🌐 VISIÓN GLOBAL
DEFINIR ROUTER (hecho: resiliencia, banco, Jev, DSL DAG Sheriff)
      ↓
INSTALAR MODELOS LOCALES (en curso, 0 corriendo en HF real)
      ↓
CONSTRUIR ORQUESTADORES (MS Agent Framework + Grok) ← AQUÍ
      ↓
INTEGRAR CENTINELA + VENTANA SELECTOR
      ↓
AUDITAR Y CERRAR

🏗 ARQUITECTURA GLOBAL
Router (13 agentes) → Modelos locales → Orquestadores → Centinela → UI selector → Sistema final

📍 POSICIÓN ACTUAL
Orquestadores
├─ MS Agent Framework ← ACTUAL (por descargar)
├─ Grok ← BLOQUEADO (falta clave de API; no se descarga, es cerrado)
└─ Centinela (Qwen 0.6B + Liquid 1B) ← sin construir

🔗 ROMPECABEZAS (dependencias cruzadas)
MS Agent Framework necesita: conocer el Router completo (auditoría + mapa mental) antes de orquestar
Grok necesita: clave de API del Director
Centinela necesita: acceso de lectura al Router que controla a los agentes de Claude

🎯 PROPÓSITO
MS Agent Framework: que ningún agente trabaje sin que el orquestador central lo sepa y lo controle
Grok: coordinar específicamente a los agentes del chat

📥 ENTRADA / SALIDA
MS Agent Framework  entrada: estado de los 13 agentes + Router   salida: → decide próxima asignación
Grok                entrada: agentes del chat (1, 2, 3)          salida: → coordina su trabajo
Centinela           entrada: instrucciones del Director + estado de los agentes   salida: → pausa o aprueba

🚀 DESBLOQUEA
MS Agent Framework listo → puede asignar trabajo a cualquiera de los 13 agentes
Grok listo (con clave) → coordina el chat sin que Claude lo haga a mano
Centinela listo → vigila antes que el watchdog de Claude (cada 1-2 h antes)

📊 MADUREZ
Router (13 agentes)        ████████░░ 80%
Modelos locales en HF      ░░░░░░░░░░  0%
MS Agent Framework         ░░░░░░░░░░  0% (por descargar)
Grok                       ░░░░░░░░░░  0% (bloqueado, falta clave)
Centinela                  ░░░░░░░░░░  0%
Ventana selector           ░░░░░░░░░░  0%

⚙️ MICROFLUJO — MS Agent Framework
Descargar → Instalar motores → Leer todo el Router (auditoría) → Construir su propio mapa mental
→ Verificar que entiende cada agente → Empezar a asignar trabajo → Reportar al centinela

🧩 ENSAMBLAJE FINAL
Router (13 agentes, DSL DAG Sheriff)
      ↓
Modelos locales en HF (pendiente)
      ↓
MS Agent Framework (orquestador central)
      ↓
Grok (orquestador del chat) + Centinela (vigilante)
      ↓
Ventana selector (Max marca agentes, da system prompt, ejecuta)
      ↓
SISTEMA FINAL
══════════════════════════════════════
```

### Lista de validación de última tarea
```
✅ P1: 21 ítems (aplicados a los orquestadores)
✅ P2: 19 ítems (aplicados)
✅ P3: 20 ítems (aplicados)
⏳ Microsoft Agent Framework: sin descargar todavía
⏳ Grok: bloqueado, falta clave de API del Director
⏳ Centinela (Qwen 0.6B + Liquid 1B): sin construir
⏳ Ventana selector de agentes con system prompt: sin construir
✅ Mapa mental (10 vistas): hecho para este documento
✅ HANDOFF completo del Router (Claude notas/HANDOFF-COMPLETO-2026-09-22.md): hecho
```

### Modos de trabajo (2 modos, aplicados)
```
┌─────────────────────────────────────────────────────────────┐
│  /arquitecto   → Diseña cómo se conectan MS Agent Framework, │
│                  Grok, el centinela y la ventana selector.   │
│                  No escribe código de implementación.        │
├─────────────────────────────────────────────────────────────┤
│  /ejecutor     → Instala, escribe código concreto, ejecuta   │
│                  pruebas, genera los archivos reales.        │
│                  No rediseña la arquitectura.                │
└─────────────────────────────────────────────────────────────┘
```

### State JSON de recuperación (adaptado al Router)
```json
{
  "RECOVERY_STATE": {
    "version": "1.0-osquestadores",
    "fecha": "2026-09-22",
    "proyecto": "Router Inteligente Universal — Osquestadores",
    "estado_global": "PLANIFICACION_0%_INSTALADO",
    "siguiente_accion": "descargar_microsoft_agent_framework_con_agente_dedicado",
    "lista_validacion": {
      "P1_21_items_aplicados": true,
      "P2_19_items_aplicados": true,
      "P3_20_items_aplicados": true,
      "ms_agent_framework_descargado": false,
      "grok_conectado": false,
      "centinela_construido": false,
      "ventana_selector_construida": false,
      "mapa_mental_10_vistas": true,
      "modos_operativos_2": ["/arquitecto", "/ejecutor"],
      "handoff_completo_router": true
    },
    "bloqueadores": {
      "grok": "falta clave de API de xAI, dada por el Director",
      "centinela": "sin agente asignado todavía",
      "ventana_selector": "sin agente asignado todavía"
    }
  }
}
```

### Dashboard y cierre
```
══════════════════════════════════════
OSQUESTADORES DASHBOARD
══════════════════════════════════════
TOTAL APROBADOS (plantilla aplicada): P1+P2+P3+mapa+modos+state+handoff = 7
TOTAL PENDIENTES: MS Agent Framework, Grok, Centinela, Ventana selector = 4
TOTAL BLOQUEADOS: Grok (falta clave)
ACTUAL: plantilla_lista | SIGUIENTE: descargar_MS_Agent_Framework
══════════════════════════════════════
```
