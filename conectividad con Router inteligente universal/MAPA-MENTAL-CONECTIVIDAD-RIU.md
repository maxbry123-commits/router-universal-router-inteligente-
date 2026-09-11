# MAPA MENTAL — Conectividad con Router Inteligente Universal

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · rama `main`.

## Objetivo
Centralizar en el Router Inteligente Universal el inventario y la ruta de todas las conexiones de proyectos: GitHub, Hugging Face, MCP, cómputo, memoria, almacenamiento, APIs, VPS y puentes entre repositorios. Ningún proyecto debe depender de una conexión dispersa o implícita.

## Ruta transversal canónica
`PROYECTO -> PUENTE-RIU-<repo>.yaml -> Router Inteligente Universal -> registry -> Enchufe Gate -> RedUniversal -> adapter -> destino -> verifier -> respuesta`

## Regla de archivos por proyecto
Cada repositorio de `maxbry123-commits` tiene una única raíz `conectividad con Router inteligente universal/` y dentro un solo archivo canónico `PUENTE-RIU-<repo>.yaml`. Ese archivo describe conectividad y referencias externas, pero nunca contiene credenciales crudas.

## Conexiones recuperadas
### Claude / GitHub MCP
- Patrón recuperado: Claude Managed Agents + recurso `github_repository` + servidor MCP GitHub.
- Endpoint observado en la documentación/skill existente: `https://api.githubcopilot.com/mcp/`.
- Autenticación: vault/runtime externo; no se persiste en Git.
- Fuente histórica: `maxbry123-commits/TAREA-1/skills/claude-api/`.

### Claude / memoria persistente
- Fuente recuperada: `maxbry123-commits/TAREA-1/skills/claude-api/shared/managed-agents-memory.md`.
- Recurso observado: `memory_store` dentro de `resources[]` de la sesión Managed Agent.
- Semántica: memoria persistente entre sesiones; se registra como capacidad del Router pero no se declara operativa hasta E2E.
- El archivo `PUENTE-RIU-TAREA-1.yaml` fue enriquecido con esta conexión.

### Hugging Face
- Cuenta/proyecto observado: `COMAND-CENTER-1`.
- Cómputo real previamente usado: Hugging Face Jobs CPU/GPU.
- Workflow histórico localizado: `maxbry123-commits/TAREA-1/.github/workflows/yaiwes-hf-static-publish.yml`.
- El Router debe consumir credenciales únicamente desde runtime/secret store; el archivo puente registra la referencia lógica y el estado, nunca el valor.

### GitHub
- Los proyectos son repositorios propiedad de `maxbry123-commits` en rama `main`.
- El Router es el punto central para operaciones GitHub y debe verificar permisos/identidad antes de promover una conexión a PASS.

### Memoria / estado propios
- Repositorios dedicados observados: `MEMORIA`, `BIBLIOTECA`, `BITACORA-MAXBRY`, `Cerebro`.
- Su conexión queda registrada como capacidad candidata; no se declara operativa hasta prueba de lectura/escritura mediante el Router.

## Inventario de repositorios administrados
1. agentes
2. Agentes-motores-Wordflow-YAIWES
3. BIBLIOTECA
4. BITACORA-MAXBRY
5. Cerebro
6. comand-Center
7. frontend
8. Grupo-Trabajo-1
9. Grupo-Trabajo-2
10. informaci-n-auditor-
11. Maxbry-AGI
12. MEMORIA
13. nct-core
14. nct-hub
15. Orquestador-Maxbry-
16. osquestador-auditor
17. router-universal-router-inteligente-
18. TAREA-1
19. TAREA-2

## Estado material actual
- raíz central creada
- registry maestro creado
- 19/19 archivos puente persistidos
- Claude/GitHub MCP recuperado y referenciado
- Claude `memory_store` recuperado y referenciado
- Hugging Face `COMAND-CENTER-1`/Jobs CPU-GPU recuperado y referenciado
- validación credenciales/E2E: pendiente

## Estados
- `DISCOVERED`: conexión o recurso localizado.
- `BRIDGE_DECLARED`: archivo puente creado.
- `CREDENTIAL_PENDING`: falta validar credencial/runtime.
- `TEST_PENDING`: credencial existe pero no hay prueba E2E.
- `PASS`: identidad + permiso + operación mínima + verificación final pasaron.
- `FLAG/GAP`: bloqueo preservado con evidencia.

## Política de seguridad
- Prohibido almacenar tokens, PAT, claves API o OAuth en este árbol.
- Solo referencias lógicas a secretos gestionados externamente.
- GitHub/Codespaces/Actions, Hugging Face y vaults pueden actuar como almacenes externos; el Router solo conoce referencias y capacidades.
- Toda conexión es fail-closed hasta prueba.

## Criterio de cierre de esta capa
`ALL_REPOS_BRIDGED + ROUTER_REGISTRY_COMPLETE + GITHUB_ACCESS_VERIFIED + HF_ACCESS_VERIFIED + MCP_BOUNDARY_VERIFIED + HANDOFF_SYNCHRONIZED`.
