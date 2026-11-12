# Router Recovery

Ejecutor determinista de un DAG declarativo. Sin LLM en el camino critico.
Valida con Pydantic, ejecuta en orden topologico y persiste cada nodo en `LEDGER.jsonl`.

## Estructura

```
router_recovery/
├── input_block.yaml      contrato de la mision (verbatim del owner)
├── dag_schema.yaml       DAG declarativo (router.dag/v1)
├── pydantic_models.py    DagSpec, DagNode, LedgerEvent, topo_order
├── checkpoint_store.py   STATE.json (atomico) y LEDGER.jsonl (append + fsync)
├── dispatcher.py         tabla de handlers
├── runner.py             Runner y CLI
└── tests/test_recovery.py
```

## Uso

Desde la raiz del repo:

```bash
python -m router_recovery.runner --dag router_recovery/dag_schema.yaml --store .checkpoints/
python -m pytest router_recovery/tests -q
```

Codigo de salida: `0` completado, `2` BLOCKER (DAG invalido, nada se ejecuta).

## Reglas

- DAG con ciclo, dependencia inexistente, id duplicado, bloque > 200 LOC o acceptance vacio: se rechaza antes de ejecutar.
- Cada nodo deja `node_start` y luego `node_done` o `error` en el ledger.
- `resume` salta los nodos con `node_done` y re-ejecuta los que tienen `node_start` sin `node_done`.
- Lineas parciales o con checksum invalido en el ledger se ignoran.
- `STATE.json` corrupto se reconstruye desde el ledger.

## Limitaciones conocidas (🚩)

- `dispatch_implementer` es un stub: marca el nodo como ejecutado sin hacer trabajo real.
- El bloque `validation` de `dag_schema.yaml` es documental: las reglas se aplican en `pydantic_models.py`.
- La spec ubica los checkpoints en `checkpoints/`, pero el CLI usa `.checkpoints/` por defecto (igual que el nodo N1 de la spec).
- Pausados por decision del owner: anchor, watchdog, ocr, handoff, validate_memory, hybrid_search, memory_auditor, context_fabric, resource_registry, state_delta.
