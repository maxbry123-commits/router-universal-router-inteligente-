# FROMTED × YAIWES — UI funcional / laboratorio visual (v0.2)

**Perfil principal:** Little. **Entrega:** HTML, CSS, JavaScript editables + snapshot autocontenido + tests + SKILL maestro. **Estado:** `REVIEW`, pendiente de aprobación visual. No se alteraron los SKILLS originales.

## Método y norma de trabajo

`REFERENCE + CONTEXT + SKILLS + BROWSER + VERIFIER`

**Microflujo:** REFERENCIA REAL → LEER REPO / AGENTS.md / SKILL.md → IMPLEMENTAR → SERVIR EN LOCALHOST → INSPECCIONAR DOM/CSS/CONSOLA/SCREENSHOTS → CLICK/SELECT/INPUT/TOUCH → COMPARAR REFERENCIA ↔ RESULTADO → CORREGIR ↺ → VERSIONAR Y ENTREGAR.

Leer `SKILL.md` para todo el contrato. **No mocks de respuesta IA**: ninguna función remota se da por ejecutada sin `window.YAIWES_PLUGIN_BRIDGE` y confirmación explícita. Los seis nombres de raíces en Crazy Wall son **referencias editables locales**, no auditoría de repositorio.

## Cómo usar

**Vista rápida sin instalaciones:** abrir `snapshot/index-standalone.html`. Todas las funciones locales ejecutan JavaScript real. Dependiendo del navegador, la persistencia `localStorage` de páginas `file://` puede estar limitada; para probar **RELOAD** correctamente servir por HTTP.

**Fuente editable por navegador real / localhost:** desde esta carpeta:

```bash
python3 -m http.server 5173
# abrir http://localhost:5173
```

**Con Vite (opcional):**

```bash
npm install
npm run dev
# abrir URL local que indique Vite
```

**Tests Playwright:** `npm run test` (instalar navegadores con `npx playwright install chromium` si falta Chromium), o en entorno Python `python tests/run_browser_qa.py`. QA visual original contra Figma/imagen se confirma manualmente, no con un puntaje inventado.

## Funcionalidades locales implementadas

| Módulo | Acciones comprobables | Sin bridge |
|---|---|---|
| Apariencias | 7 paletas, Little predeterminada, tema gris **sin fondos negros** | funciona |
| Estados | verde En curso, azul Encendido, rojo Advertencia, gris Pendiente en **cada** paleta | funciona |
| Chat | modo Rápido/Pensar/Equilibrado, modelo, toggles de tools, adjuntar archivos, borrador, exportar conversación, nuevo chat | envío bloqueado correctamente |
| Archivos | elegir archivo real, buscar, anclar, descargar el **mismo archivo** y borrar | funciona localmente |
| Crazy Wall | ver 6 raíces de referencia, editar estado/nota, añadir raíz, exportar información | funciona localmente (sin afirmar estado remoto) |
| Configuración | es/en/fr/pt, animación, ayudas, export/import de estado y reinicio | funciona |
| Action Bus | evento `yaiwes:ui-action`, IDs allowlisted, llamada `window.YAIWES_PLUGIN_BRIDGE.execute` solo para remoto | `BRIDGE_MISSING` |

**Límite de archivos:** hasta 1 MB se almacenan como `data:` en `localStorage` del navegador. Mayores: solo sesión actual (URL blob), no persisten después de cerrar/recargar. No existe transporte de archivos grandes ni motor IA implementado en este paquete. Los modelos del menú son opciones para un proveedor conectado, no APIs proporcionadas aquí.

## Integración con IA/backend real

El frontend llama `window.YAIWES_PLUGIN_BRIDGE.execute(actionId,payload)` y **solo** procesa confirmación real. Ejemplo del contrato (pseudotest, NO un proveedor de producción):

```js
window.YAIWES_PLUGIN_BRIDGE = {
  async execute(actionId, payload) {
    // Aquí conectar TU endpoint real, con autenticación en el servidor.
    // Debe retornar { ok:true, reply:"texto del modelo real" }
    // o { ok:false, error:"motivo" }.
    throw Error("Bridge aún no configurado");
  }
};
```

No poner secretos en código cliente. El bus admite `chat.close`, `chat.export`, `chat.attach`, `mode.thinking.toggle`, `model.select`, `chat.send`, `tool.document.toggle`, `tool.website.toggle`, `tool.image.toggle` y acciones de archivos/estado/tema. **Enviar sin bridge conserva el borrador y nunca inventa contestaciones.**

## Estructura

```text
UI-YAIWES-CHAT-FINAL-TEST/
├── index.html                    Entrada HTML editable
├── styles.css                    Todos los temas, componentes, responsive y estados
├── app.js                        Lógica funcional, navegación y persistencia
├── src/lib/actionBus.js          Allowlist de acciones, eventos y bridge
├── assets/icons/                 Recursos futuros, sin dependencias CDN
├── assets/images/
├── manifest.json                 Contrato de actions, slots, temas, estados
├── SKILL.md                      Norma maestra, fuentes y método de verificación
├── AGENTS.md                     Arranque breve para Claude, Grok, Codex y GPT
├── ACCEPTANCE.md                 Resultado auditado de pruebas
├── VERSION.md                    Cambios / siguiente iteración
├── README.md                     Este archivo
├── vite.config.js + package.json Servidor/test sin generar backend
├── snapshot/index-standalone.html Copia de visualización autocontenida, NO fuente principal
├── snapshot/reference-*.jpg      Referencias Grok entregadas por el usuario
├── screenshots/                  Evidencia en escritorio y móvil
└── tests/                        Prueba Playwright y log de Chromium
```

## Siguiente etapa después de la aprobación

Convertir el **mismo** comportamiento a React/Vite modular en `src/components/ChatPanel.jsx`, `ChatTopbar.jsx`, `ChatComposer.jsx`, `MessageList.jsx`, `ModelSelector.jsx`, `ToolButton.jsx`, `Icon.jsx`, con Action Bus, estilos y pruebas de paridad. Esta versión **no afirma incluir React**. La regla es preservar fuente HTML/JS funcional → migrar sin cambiar semántica de acciones → comparar → cerrar versión.

## Tratamiento de los colores originales

Little, Matte y Blanco mantienen fondos/HEX exactamente de skill `01`; Crystal, Orange, Blue y el nuevo Gris son **propuestas**. En esta revisión se añade una excepción solicitada de indicadores semánticos azul/verde/rojo a todas las paletas, separada de los acentos de marca. **No se modificaron los originales.**
