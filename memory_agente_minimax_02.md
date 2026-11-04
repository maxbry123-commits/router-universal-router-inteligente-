# memory_agente_minimax_02.md

> Fuente de verdad unica del bucle (yaiwes.node/v2). Escritor: solo el orquestador. Un commit por
> actualizacion. Prohibido: secretos, claves, contrasenas, tokens.
> Ubicacion: raiz del repositorio (allowlist `root_protection`).

```json
{
  "version": 1,
  "objective": "Auditoria X-Ray + migracion de las ventanas del chat a paneles iframe independientes",
  "state": { "node": "N5_validate", "step": "VALIDATE", "fsm": "RESEARCH_PASS" },
  "queue": [
    { "id": "T1", "goal": "Leer yaiwes-panel-bridge.js y loop-panel.js y derivar el contrato real del bridge", "ac_ids": ["AC1"], "depends_on": [] },
    { "id": "T2", "goal": "Crear watchdog-panel.html y cola-panel.html data-driven desde LOOP-wachdog-cola.json", "ac_ids": ["AC2"], "depends_on": ["T1"] },
    { "id": "T3", "goal": "Cablear en cableado.manifest.json y chat-ventanas.js sin tocar shell.js/shell.html", "ac_ids": ["AC3"], "depends_on": ["T2"] },
    { "id": "T4", "goal": "3 revisiones visuales con render headless + capturas; consola limpia; sin 404", "ac_ids": ["AC4"], "depends_on": ["T3"] },
    { "id": "T5", "goal": "Cerrar G2: cablear connectivity, hf_compute, hf_storage, lifeguard leyendo la fase de MAPA.md", "ac_ids": ["AC5"], "depends_on": ["T4"] }
  ],
  "handoff": {
    "next": "T1",
    "missing": [
      "G1: watchdog-panel.html y cola-panel.html no existen (si existen: loop-panel.html 13 KB, loop-panel.js 17.7 KB)",
      "G2: cableado.manifest.json deja connectivity, hf_compute, hf_storage y lifeguard con destino vacio y enlace false",
      "Contrato del bridge sin verificar (yaiwes-panel-bridge.js)",
      "PAT de escritura no provisto: se opera GitHub via Router RIU (github_leer / github_escribir)"
    ]
  },
  "log": [
    "[N1_xray][xray][read_6_source_files][ok][RESEARCH_PASS]",
    "[N2_research][research_20_sources][2 busquedas propias en vivo + 3 subagentes][ok][RESEARCH_PASS]",
    "[N4_execute][write_memory_file][commit ae349408f9 + migracion a memory_agente_minimax_02.md][ok][EXECUTING]",
    "[N5_validate][real_test][read-back + hashes + commit sha][ok][VALIDATING]"
  ],
  "flags": [],
  "research_cache": [
    {
      "keywords": ["iframe panel chat SPA", "postMessage origin validation", "vercel rewrites SPA fallback"],
      "date": "2026-11-03",
      "chosen": "HTML independiente por ventana en iframe, MessageChannel + nonce + envelope validado, estado unico en el padre, catch-all SPA al final",
      "sources": [
        "https://www.chatbase.co/docs/developer-guides/website-integration/iframe",
        "https://raylabs.app/articles/build-a-secure-iframe-widget-for-other-websites/",
        "https://safeguard.sh/resources/blog/postmessage-has-no-default-access-control",
        "https://corewin.ua/en/blog-en/iframe-security-best-practices-for-modern-web-applications/",
        "https://prachub.com/resources/iframe-interview-questions-sandboxing-origins-and-safe-messaging",
        "https://bindbee.dev/blog/secure-cross-window-communication",
        "https://react.codeguides.io/browser-apis/postmessage-basics/",
        "https://www.microsoft.com/en-us/msrc/blog/2025/08/postmessaged-and-compromised",
        "https://www.raijuna.com/blog/postmessage-origin-bypass",
        "https://dev.to/dhinesh_ks_9db13f15d64f7/building-a-new-gen-chat-widget-css-and-javascript-isolation-with-cross-origin-iframes-4ag6",
        "https://vercel.com/docs/project-configuration/vercel-json",
        "https://blog.vercel.com/kb/guide/why-is-my-deployed-project-giving-404",
        "https://github.com/colinhacks/zod/commit/8ac9ae51",
        "https://github.com/colinhacks/zod/pull/6378",
        "https://www.promptcodeai.com/deployment-vercel/03-project-configuration",
        "https://github.com/ShreeChaturvedi/taskflow-calendar/issues/50",
        "https://github.com/tcs-sdlc-ai-assist/spa-routing-reliability-on-vercel-20260318-152647/blob/main/README.md",
        "https://github.com/LuizCorrea-Dev/Nasdara-Dayz-Map-dynamic/blob/main/vercel.json",
        "https://vercel.com/docs/frameworks/frontend/vite",
        "https://github.com/AditthyaSS/iloveAgents/issues/1479"
      ],
      "context_pack_ref": "habilidad yaiwes-node-dag + references/conexiones.md"
    }
  ],
  "progress_pct": 40
}
```

## TRAZABILIDAD — auditoria X-Ray (2026-11-03)

- Repo canonico: `maxbry123-commits/router-universal-router-inteligente-`, rama `main`.
  `abc1tienda-web/router-universal-router-inteligente-` es espejo: no usar.
- Frontend del chat (privado, solo via Router RIU): `chat-router/chat/frontend/`.
- `loop-panel.html` + `loop-panel.js` YA EXISTEN (patron iframe data-driven, con `yaiwes-panel-bridge.js`,
  CSS propios y banner de modo seguro). El boton `#btn-loop` ya existe.
- **G1**: faltan `watchdog-panel.html` y `cola-panel.html`; Watchdog y Cola siguen en `ventana-watchdog.js`
  y `ventana-cola.js` (legacy DOM).
- `api/loop.js`: estado en memoria de proceso (`new Map()`), tope 8 pasos, `ecc_motor.py` con `spawnSync`
  y timeout 2 s. **No es motor persistente**: ninguna vista puede prometer ejecucion de horas.
- **G2**: en `cableado.manifest.json`, `connectivity`, `hf_compute`, `hf_storage` y `lifeguard` tienen
  `destino: ""` y `enlace: false`.
- `LOOP-wachdog-cola.json` es el contrato declarativo (harness `/plugins/loop_wachdog/call/paso`,
  watchdog `intervalo_ms` 3000, `tope` 8, `pausa_si`): los paneles nuevos se derivan de ahi.
- `CIERRE_XRAY_LOOP_CODA.md`: 8 segmentos, 2-8 pendientes de pruebas reales. Vigente: no crear otra raiz,
  no GitHub Actions, no LFS, no desplegar fuera del repo autorizado, no declarar DONE con bloqueos.
- `MAPA.md`: Fase 1 hecha; Fase 6 (backend) requiere autorizacion expresa.

## BITACORA

- 2026-11-03 — Auditoria X-Ray + 20+ fuentes + gaps G1/G2. Migracion del archivo de memoria al nombre y
  ruta que exige el contrato. Sin cambios de codigo en el frontend.
