# PLAN v2 — Pasos 1 a 5 (sustituye el orden de PLAN_PASOS_1_A_5.md)

Estado: 2026-11-09 · Rama: `ccr-f01c3de9-bmry0s` · Fuente: input block §5 (orden exacto) + informe C-2.

## Decisiones de S-1 y C-2 aplicadas
| 🚩 | Decisión | Estado |
|---|---|---|
| 3 | Limpieza HF/MiniMax BLOQUEADA hasta autorización expresa por escrito del owner y entrega de la lista. Watchdog Vercel sí autorizado por directiva. | 🚩 bloqueado |
| 8 | `chat-router/` se mantiene por instrucción explícita del owner, registrada como EXCEPCIÓN. El owner decide si la raíz cambia. | 🚩 excepción |
| 9 | Las fases 1, 2, 3, 4, 5, 7, 10, 11 y 12 se añaden como nodos (ver orden). | cerrado en el plan |
| 10 | Orden reemplazado por el orden exacto del input block §5. p5 ya no es "independiente". | cerrado en el plan |

## Orden de ejecución (input block §5)
1. Fase 1 — auditoría histórica (A-2, sin sandbox).
2. Fase 2 — auditoría actual y grafo AST (A-2).
3. Fase 3 — registro central `connections/wiring_registry.yaml` (A-2).
4. Fase 4 — contratos Harness DeepSeek (A-2 o A-5).
5. Fase 5 — System Prompt y motores (A-2).
6. Fases 6 y 8 — Chat YAIWES y OpenClaw (A-1, sandbox; C-1 prueba). Solo después del paso 5.
7. Fase 6 — OpenClaw independiente (A-2).
8. Fase 7 — componentes, skills, Loop/ECC (A-6).
9. Fases 8 y 9 — agentes: selectores, ON/OFF, herramientas (A-6).
10. Fase 9 — NVIDIA y modelos locales: p3 (A-4) → p4 (A-5).
11. Fase 9 — memoria y storage: p2 (A-3).
12. Fase 7 — guardianes y código huérfano, en `_quarantine/` (A-2).
13. Fase 11 — automatización: `ops/launch.sh`, `ops/launch_hf.py`, sin GitHub Actions (A-2). S-1 confirma.
14. Fase 10 — Job Test J01 a J13 (C-1 o Job HF `cpu-upgrade`).
15. Fase 12 — cierre: README, bitácora, handoff, repo limpio. C-2 verifica sandbox limpio. S-1 emite PASS final.

## Estado actual de agentes
| Agente | Nodo | Estado |
|---|---|---|
| A-3 | p2 | 🚩 parcial: plugin HTTP existe, no hay MCP real. |
| A-1 | p1b, p1c | en curso (reintento con ruta correcta). |
| A-2 | p1 y fases 1, 2, 3, 5 | pendiente. |
| A-4 | p3 | pendiente. |
| A-5 | p4 | pendiente (depende de p2 y p3). |
| A-6 | p5 (A2, A3, B, C, D) y fases 7, 8, 9 | pendiente. |
| S-1 | verificación del input block | informe entregado; 🚩 3, 8, 9, 10 registrados aquí. |
| C-2 | gaps | informe entregado; orden propuesto aquí. |

## Hallazgos abiertos (sin cerrar)
- A. `AGENTS.md` no existe en la raíz de la rama, aunque §0 del input block lo referencia.
- B. `kernel/` no existe en la raíz de la rama; el input block está en `ccr-4806d6f4`.
- C. Jobs J01 a J13 pueden requerir sandbox, fuera de la regla actual. S-1 decide.
- D. Fuentes de la UI de Chat YAIWES y OpenClaw: pendiente del reintento de A-1.
