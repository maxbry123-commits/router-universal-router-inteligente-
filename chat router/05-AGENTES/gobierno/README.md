# Gobierno del equipo YAIWES (T01)

Piezas de **código** del gobierno de agentes, tal como las definió el Director
en los documentos 22 y 23. Sheriff, Judge y Sentinel son **deterministas**
(no son LLMs). Los agentes nunca se mandan mensajes libres: todo pasa por los
contratos (`Job`, `Result`, `Task`, `State`).

## Piezas

| Módulo | Nivel | Rol |
|---|---|---|
| `contratos.py` | — | Job/Result (doc 22) + Task/State (doc 23) |
| `sheriff.py` | 3 | policy_gate: allow/deny/restrict |
| `sentinel.py` | 6 | runtime_watchdog: RECOVER/REASSIGN/BLOCK/CONTINUE |
| `judge.py` | 8 | final_verifier: PASS/REVISE/BLOCK |
| `mirror_manager.py` | — | worktree mirrors selectivos (doc 22) |

## Diagrama (doc 23)

