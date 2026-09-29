# Contratos · Router Universal

## Artifact schema

```python
@dataclass
class Artifact:
    artifact_id: str   # ^art_[a-z0-9]{8,32}$
    estado: str         # pending|approved|rejected|completed|expired
    kind: str           # text|code|file|image|consensus|manifest
    transport: str      # http|sse|ws|file|ipc
    sandbox: str        # pyodide|wasm|native|none|docker
    timeout_ms: int     # 100..600000
    payload: Any
    hash: str           # SHA256 del payload
    signature: str      # HMAC-SHA256 (opcional)
    created_at: int     # epoch ms
    ttl_ms: int         # default 3600000 (1h)
```

## Flujo

1. **Crear artifact** con payload
2. **Calcular hash** = SHA256(json(payload, sort_keys=True))
3. **Firmar** = HMAC-SHA256(artifact_id|estado|kind|hash, secret)
4. **Gate** valida: regex, estado, kinds, transports, sandbox, hash, expiración
5. **Router** elige conector según `transport`
6. **Sandbox** ejecuta según `sandbox`
7. **Tracking** registra en cost log + bridge events
