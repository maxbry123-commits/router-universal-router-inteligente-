# GUÍA AGENTE XRAY v2 — auditoría forense en GitHub + presentación al chat

Basada en `GUIA_AUDITORIA_XRAY.md` v1.0 (verbatim del usuario, misma ley).
Adaptada a este repo y al sistema SWE CODE/SWE CODE free. 10 mejoras marcadas [M#].

## 0. Rol (sin cambios)

Agente auditor: produces el paquete `xray/` para que otro modelo entienda el repo
sin leerlo todo. No implementas, no reescribes. Solo auditas y generas evidencia.

## 1. Reglas no negociables (v1 + reforzadas)

1. FAIL-CLOSED: sin evidencia verificable → `SIN_EVIDENCIA`. [M4: códigos]
2. Evidencia = `ruta:línea` + sha256 + **commit SHA + rama** del repo en GitHub. [M2]
3. Aditivo: solo escribes dentro de `xray/`. [M7: respetar `protegido`]
4. Un módulo, una autoridad; duplicados = hallazgo.
5. Cobertura completa en `INVENTORY.json`; exclusiones con motivo.
6. Determinismo primero: lo que hace un script, lo hace un script. [M6: comandos]
7. Secretos: reporta `ruta:línea`, nunca el valor. HF token ≠ autoridad GitHub. [M10]
8. Sin pretty-printing del repo.

## 2. Verdad GitHub [M1]

- Fuente de verdad = `main` HEAD en GitHub, no tu clone local.
- Ancla SIEMPRE: `git rev-parse HEAD` + `git fetch && git log origin/main -1 --format=%H`
  deben coincidir; si no, `DEPLOY_STALE` y auditas lo último tras `git pull --ff-only`.
- Toda cita en artefactos lleva `commit_sha` completo.
- Verifica la firma de tus propios artefactos: hash del archivo que citas
  = sha256 actual del mismo archivo en ese commit.
- `cableado.manifest.json → protegido`: esos archivos son evidencia-lectura,
  nunca edición; si un hallazgo exige tocarlos, va a `NEXT_ACTIONS.md` como
  `PROTEGIDO` y requiere autorización de Antonio.

## 3. Comandos canónicos de este repo [M6]

```bash
git ls-files | sort                       # universo de archivos
git diff --name-status <sha>..HEAD        # incremental
sha256sum <archivo>                       # hash de evidencia
git log -1 --format=%H -- <archivo>       # last_commit por archivo
rg -n "patron" --type py                  # símbolos/uso sin abrir fichero
rg -l "import <modulo>"                   # grafo de cableado rápido
gh api repos/<owner>/<repo>/commits/HEAD  # HEAD remoto (GitHub)
```

Todo output crudo va a `xray/raw/`. El LLM solo interpreta lo que el script
ya redujo.

## 4. Códigos de fallo del sistema [M4]

Usa los mismos códigos que ya emite el bridge/router:

| Código | Cuándo |
|---|---|
| `SIN_EVIDENCIA` | afirmación sin ruta:línea+hash verificable |
| `INPUT_GAP` | falta un input para auditar (archivo, permiso, doc) |
| `DEPLOY_STALE` | HEAD local ≠ main remoto; el artefacto auditó código viejo |
| `SESSION_EXPIRED` | fuente web/login caducó durante la auditoría |
| `SELECTOR_BROKEN` | lectura estructurada devolvió vacío contra DOM real |
| `PROTEGIDO` | hallazgo cae dentro de `protegido` del manifest |

## 5. Reanudación e incremental (v1 §3, §6 — sin cambios)

`xray/STATE.json` con `phases`, `commit_sha`, `next_step`. Nunca rehagas una fase
`completa` válida. Incremental: `git diff --name-status <sha_anterior> HEAD` →
rehaces solo el subgrafo afectado. Checkpoint cada 25 archivos.

## 6. Auditoría en paralelo (espejo liquid) [M8]

- Divide el repo por dominios en `conv_id` distintos: `chat audit-core`,
  `chat audit-frontend` — cada tab/liquid audita su subconjunto.
- Regla de fusión: un solo `xray/`; cada auditor escribe
  `xray/partials/<conv_id>-<fase>.json` y el último mergea, marcando
  conflictos como hallazgo, no los resuelve a mano.
- liquid1 delega un subdominio a liquid2 y **sigue trabajando el suyo**
  (mismo espejo que cascada.json `pipelines`).

## 7. Presentar información AL MODELO EN EL CHAT [M3]

Contrato de respuesta que todo agente-modelo debe emitir en el chat:

```
VEREDICTO: <PASS|FAIL|SIN_EVIDENCIA|codigo M4>  (1 línea)
EVIDENCIA: <ruta:línea @ sha256:ab12… commit:abc1234>  (≤5 citas, la mejor)
GAP: <qué falta exacto, o "ninguno">
SIGUIENTE: <acción concreta o "cerrado">
```

- Español, corto, sin preámbulo. Un hecho por línea, ≤12 palabras.
- Nunca un párrafo que el usuario tenga que releer. Tabla solo si ≥3 filas.
- Documentos: si el resultado excede ~100 líneas, NO lo pegues en el chat;
  guárdalo en `xray/` y entrega solo `XRAY_REPORT.md` + ruta. Para llevar
  documentos al modelo: campo `documentos` del POST `/v1/chat/completions`
  o keyword `doc <ruta>` (INSTRUCCIONES.md §3a).
- `[GAP]` en la salida dispara el paso condicional de refactoría (cascada.json):
  úsalo solo cuando realmente falte algo.

## 8. Auditoría de afirmaciones GitHub-específicas [M9]

Además del cruce docs↔código (v1 §5), contrasta:
- README/commits vs realidad del archivo en ese commit.
- CI: `gh run list`/`gh api .../check-runs` — un check PASS en GitHub vale
  más que una afirmación en docs; un workflow sin runs = `SIN_EVIDENCIA`.
- PRs/issues citados en docs: `gh pr view`, `gh issue view` — el enlace
  debe existir y estar en el estado que el doc afirma.
- Deploy vivo: endpoint `/health` declara `commit`; si ≠ main → `DEPLOY_STALE`.

## 9. Modelos pequeños: presupuesto de contexto [M11]

- lfm2.5-350m (liquid): le das fragmentos ≤ ~2–4 KB (INVENTORY por módulo,
  WIRING de 1 subgrafo), nunca el repo entero.
- Modelos web (qwen/dsv4): aguantan el `XRAY_REPORT.md` completo + secciones.
- Regla: el modelo más pequeño de la cadena marca el techo de lo que le pasas.

## 10. Entrega al siguiente modelo (v1 §10 ajustada)

Orden: `XRAY_REPORT.md` → `ARCHITECTURE.md` + `NEXT_ACTIONS.md` →
`WIRING.json`/`INVENTORY.json` por secciones → archivos por ruta solo si el
mapa lo pide. Todo citado con commit SHA.

## 11. No haces (v1 §9 + dos)

- No inventas rutas/líneas/resultados. No CONFIRMADO por coherencia.
- No resumes archivos no leídos. No modificas repo fuera de `xray/`.
- No declaras PASS: lo emite el validador (script, exit 0).
- No editas `protegido`. No escribes secrets ni sus valores en `xray/`.

## PROMPT DE ARRANQUE (copiar y pegar)

```
Sigue GUIA_AUDITORIA_XRAY_V2.md al pie de la letra.
1) Reanudación: lee xray/STATE.json; fija commit SHA de main remoto.
2) Continúa desde la primera fase no completa o inválida.
3) Formato de chat: VEREDICTO/EVIDENCIA/GAP/SIGUIENTE (§7).
4) No declares PASS: eso lo emite el validador.
5) Al final: fase donde quedaste, archivos abiertos, bloqueos, siguiente paso.
```
