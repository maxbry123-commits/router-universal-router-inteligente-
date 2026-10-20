# Cómo debe funcionar cada una de las 14 fotos (motivo → ventana)

Paleta de la foto = referencia de **layout**. Producto = Matte/Little/Blanco. Naranja solo Cargar/Descargar.

Fotos: [DESCRIPCIONES-39.md](DESCRIPCIONES-39.md) (imágenes visibles).

| ID | Foto | Cómo debe funcionar |
|----|------|---------------------|
| **FOTO-01** grafo | F047 `1000021927` | Mapa de nodos (agentes, skills, docs). Tap nodo → abre esa ventana Lego. Aristas = wires ABS. Zoom/pan. No es adorno. |
| **FOTO-02** terminal Marte | F089 `1000077766` | Log vivo del kernel: cada `ABS.dispatch` se imprime. Estados RUN/DONE/SIN_BACKEND. No HUD naranja de producto. |
| **FOTO-03** versionado | F046 `1000021925` | Historial de `state.json` / manifiestos. Restaurar versión. Diff. Cargar/Descargar snapshot. |
| **FOTO-04** assets | F048 `1000021929` | Biblioteca: fondos, iconos lucide, anims. Elegir fondo de **una** ventana. No mezcla paleta HUD. |
| **FOTO-05** skills | F045 `1000021924` | Lista skills anclables a un agente. On/off. Pegar MD. Hasta N skills. |
| **FOTO-06** navegador | F044 `1000021923` | Explorer del proyecto. Abrir archivo → WALL-05 o sheet. No es el OS entero. |
| **FOTO-07** memory | F043 `1000021922` | Pinear documentos al contexto del run. Adapter local (Dexie). El usuario de producto no ve URLs. |
| **FOTO-08** capas | F041 `1000021920` | Z-order del HOST: mostrar/ocultar iframe. Como capas Photoshop de ventanas. |
| **FOTO-09** storage | F039 `1000021915` | Cupo local, listar keys IndexedDB, Cargar/Descargar. Conector `local`. |
| **FOTO-10** contexto | F035 `1000021897` | Payload actual compartido (input CASCADE). Las otras ventanas leen `FROMTED_CTX`. |
| **FOTO-11** modelos | F032 `1000021889` | Selector modelo (Grok/Claude/local WebLLM). Guardar `token_ref`, nunca el token. |
| **FOTO-12** timeline | F040 `1000021917` | Línea de tiempo de runs del tren/cascade. Tap → evidencia. |
| **FOTO-13** personalidad | F037 `1000021905` | Rol + prompt del agente (analyzer/coder/…). On/off. i18n del nombre. |
| **FOTO-14** evidencia | F036 `1000021900` | Auditor: hashes, 5 clicks, `EVIDENCE.json`. Fail-closed si falta prueba. |

Cada una = 1 HTML + ABS + ficha. Se unen en HOST.
