# Seis pasadas completas — chat Maxbry (2026-10-04)

Se recorrieron **las 50 instrucciones en cada una de seis pasadas**, no sólo seis secciones independientes. I01–I40 proceden de la lista literal de la auditoría anterior; I41–I50 recogen las instrucciones posteriores. Las columnas son: **L** lectura literal y precedencia; **S** contraste con cada archivo aplicable de la skill; **F** código fuente; **T** pruebas estáticas y build; **R** runtime, seguridad y no-mock; **V** veredicto. Cada fila pasa por las seis columnas. C = cumple para el alcance verificable; P = parcial; B = bloqueado por requisito externo; N = no aplica a esa pasada. C en T **no equivale** a verificación en navegador. El detalle archivo por archivo está en `AUDITORIA-MAXBRY-82.md`.

| ID | Instrucción | L | S | F | T | R | V | Evidencia y límite |
|---|---|---|---|---|---|---|---|---|
| I01 | «usando las skills como referencia principal y exacto la skills Maxbry UI fromtend» | P | P | C | P | P | P | Contrato skill sí; 11 checks navegador no. |
| I02 | «Solo haces 1 panel del chat» + «Un panel para configurar los botones» | C | C | C | C | C | C | chat.js + settings.js. |
| I03 | «dejas las 4 paneles en módulos separados» | P | P | C | P | C | P | 03/04 reservas; demás paneles en segunda fase. |
| I04 | «Cada ventana es un archivo separado» | C | C | C | C | C | C | Cada selector/ventana en src/windows/. |
| I05 | «No mosck estático» | C | C | C | C | C | C | bridge.js requiere ok:true; no respuesta inventada. |
| I06 | «Javascript Html css» | C | C | C | C | C | C | Entrada + 2 CSS + módulos JS. |
| I07 | «todas las conecciones para ponerle la configuración del backend el comando de acción de cada botón» | P | P | C | P | P | P | actionId editable; comandos no implementados fallan cerrados. |
| I08 | «Colocas un Y» (marca visual) | C | C | C | C | C | C | Marca Y en cabecera. |
| I09 | «0. Panel de configuración para colocar el code que activa los botones o modelos y funciones de los selectores» | C | C | C | C | C | C | settings.js edita IDs/opciones. |
| I10 | «1. Un botón con 8 modos niveles de razonamiento avanzado» | P | P | C | P | P | P | 8 slots; API sólo mode-1. |
| I11 | «2. Selector… para poner todos los modelos que necesito» | P | P | C | P | P | P | Catálogo remoto requiere auth; selector local sí. |
| I12 | «3. 5 selectores que abren ventanas… se configura en el panel de configuración» | C | C | C | C | C | C | 5 ventanas con Aplicar/Cancelar. |
| I13 | «4. 8 botones para encender, se configura» | C | C | C | C | C | C | 8 toggles exigen confirmación. |
| I14 | «5. Cruz con 12 campos para colocar funciones» | C | C | C | C | C | C | 12 funciones en +. |
| I15 | «6. Botón para subir documentos» | P | P | C | P | P | P | Documentos requieren auth. |
| I16 | «7. Botones de voz» | P | P | C | P | P | P | MediaRecorder real; host voiceActionId no existe por defecto. |
| I17 | «7. … de Watchdog» | P | P | C | P | P | P | Watchdog requiere bridge host. |
| I18 | «7. … para mandar» | P | P | C | P | P | P | Envío requiere bridge, respuesta real. |
| I19 | «8. Ventana de habilidades y conectores» | P | P | C | P | P | P | Habilidades/conectores necesitan actionId y bridge. |
| I20 | «9. Selector para subir archivos adjuntar» | P | P | C | P | P | P | Archivos adjuntos; upload requiere auth. |
| I21 | «panel configurable para que yo luego pueda poner el nombre en cada selector y en cada botón y el plugins comando de acción» | C | C | C | C | C | C | Nombres y actionIds persistibles. |
| I22 | «en el panel de configuración se escribe la descripción» | C | C | C | C | C | C | Descripciones editables. |
| I23 | «No Github acción» | C | N | C | C | C | C | No se invocan Actions. |
| I24 | «No lfs» | C | N | C | C | C | C | No se utiliza LFS. |
| I25 | «No desplegar» | C | N | C | C | C | C | Sin despliegue. |
| I26 | «No usar vercel» | C | N | C | C | C | C | Sin invocar Vercel. |
| I27 | «No escalar» | C | N | C | C | C | C | Sin escalar. |
| I28 | «No puedes hacer otra tarea» | C | N | C | C | C | C | Únicamente fases pedidas, según orden más reciente. |
| I29 | «No puedes hacer prueba visual sin mi autorización» (Job HF sólo si autorizado) | C | N | C | C | C | C | Sin navegador/Testing Agent; no afirmar visual PASS. |
| I30 | «Main / chat router / chat fromtend / … Todo dentro nada de ese sitio fuera» | C | N | C | C | C | C | Ruta histórica sustituida por la instrucción posterior I46. |
| I31 | «nada de monolítico… no debe existir un solo archivo con el code fuente» | C | C | C | C | C | C | Fuente editable modular; preview generado. |
| I32 | «El nombre… es chat Yaiwes fromtend» | C | N | C | C | C | C | Nombre HTML respetado. |
| I33 | «Conéctalo como plugins… Fables… o harness» + «No vas a usar deepseek» | P | P | P | P | B | B | Rutas HTTP existentes; Fables sin HTTP verificado; 401 sin relay. |
| I34 | «Realiza un archivo HTML css javascript para yo revisarlo» | P | P | C | P | P | P | HTML autocontenido abre file://; CSS/JS separados en ZIP. |
| I35 | «paras solo al terminar paso 5» | C | N | C | C | C | C | Orden antiguo sustituido: nueva instrucción autoriza segunda fase tras chat. |
| I36 | «Pusiste un montón de botones visible no existe los selectores» → sin filas permanentes, selectores reales | P | P | C | P | P | P | No hay tiras permanentes; visual pendiente. |
| I37 | «La estética no es la de mi skills no tiene ni siquiera la paleta de colores» | P | P | C | P | P | P | Siete paletas en tokens.css; comparación visual pendiente. |
| I38 | «no elimines la ventana de configuración» | C | C | C | C | C | C | settings.js conservado. |
| I39 | «revisa 4 veces antes de programar… todo lo que está en el skills… dentro del chat en otros paneles» | P | P | C | P | P | P | 82 entradas auditadas; piezas de otros paneles no portadas al chat. |
| I40 | «comprobar archivo por archivo del skills… y luego revisar mis instrucciones 4 veces» | C | C | C | C | C | C | Matriz archivo por archivo y esta matriz. |
| I41 | Siete paletas: Gris, Little, Matte, Blanco; Crystal, Orange y Blue referenciales | P | P | C | P | P | P | Siete perfiles; 3 referenciales no homologados. |
| I42 | Revisar los 82 archivos Maxbry uno por uno, con destino y brecha | P | P | C | P | P | P | AUDITORIA-MAXBRY-82.md: 82 filas. |
| I43 | Seis lecturas cruzadas completas de estas instrucciones | C | N | C | C | C | C | 50 instrucciones por seis dimensiones; no seis PASS de runtime. |
| I44 | Auditoría X-Ray y los hashes de 82 imágenes, sin confundirlos con prueba visual | P | N | C | P | P | P | 82 SHA-256 coinciden; 0 visual, 0 runtime en X-Ray. |
| I45 | Terminar primero el chat; después abordar el inventario del plan | C | N | C | C | C | C | Vista entregada antes de segunda fase. |
| I46 | Código fuente sólo en chat router/Chat UI fromtend/ | C | N | C | C | C | C | Fuente y artefactos en ruta canónica. |
| I47 | Entregar sólo visual revisable HTML/CSS/JS sin hacer prueba visual propia | C | N | C | C | C | C | Vista adjunta; usuario la prueba, no yo. |
| I48 | Chat 100 % operativo para despliegue con backend autenticado | P | N | P | P | B | B | BLOQUEADO: no hay host/relay autenticado para API. |
| I49 | DeepSeek Harness puede ser infraestructura, no modelo de inferencia | C | C | C | C | C | C | Filtro DeepSeek/auto en selección y respuesta. |
| I50 | 22 Rare UI TSX, 54 iconos V12, tipografía, Wall/Run/Archivos/canvas/DAG en fase posterior, no fingirlos dentro del chat | P | P | C | P | P | P | Sin navegación a Run/Wall desde chat; quedan para segunda fase. |

Evidencia de T: `npm ci` (18 dependencias, 0 vulnerabilidades declaradas), `npm test` 38/38, `npm run check` 68 módulos JS analizados (incluye archivos aislados para la segunda fase), CSS sin advertencias, `npm run build:review` produjo la vista autónoma, `git diff --check` sin errores. No se ejecutaron los 11 checks de navegador de la skill. El frontend no puede proporcionar autenticación sin comprometer una clave: `/chat/providers/{provider}/models`, `/chat/documents` y `/chat/send` usan X-API-Key o Bearer. Se necesita un relevo seguro del servidor/host; no se debe pegar ninguna clave en la configuración ni afirmar despliegue operativo. La segunda fase debe leerse desde el inventario del plan antes de implementar funciones nuevas.
