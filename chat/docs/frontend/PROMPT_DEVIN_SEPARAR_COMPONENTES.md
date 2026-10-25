# Prompt para Devin — separar componentes y agentes de terceros del sistema de código propio (ANTES de mover)

```
Eres Devin. Trabajas para el Director (Antonio). Responde en español, corto, con números y evidencia real (salida de comandos). No inventes. No imprimas secretos (usa los tokens del entorno sin mostrarlos).

OBJETIVO
Separar, dentro del repo `maxbry123-commits/frontend` (824.821 archivos), dos cosas que hoy están mezcladas:
  A) EL SISTEMA DE CÓDIGO PROPIO (lo creado por el Director y sus agentes: UI YAIWES, YAIWES NN, Wordflow LOOP, documentos del proyecto, motores de descarga/extracción/copia/movimiento, bitácoras, HTML originales, contratos, skills propias).
  B) COMPONENTES DE TERCEROS y AGENTES (código open source descargado: librerías, frameworks, agentes listos, runtimes como OpenJDK/Electron/Wails, vendor, node_modules, _work, repos clonados).
La separación se hace ANTES de mover nada al destino. Cada grupo se entrega EMPAQUETADO EN ZIP (en partes) usando los motores del repo `maxbry123-commits/router-universal-router-inteligente-` (carpeta chat-router/motores/: motor 1 extraer, motor 2 descarga+extracción en cola, motor 3 copia por lotes con sha256, motor 4 mover). Lee cada motor antes de usarlo.

DESTINOS
- Código propio (A): repo `maxbry123-commits/ui-yaiwes` (ya contiene "UI YAIWES interface" completo y 5.687 archivos propios traídos; compara por sha256 y sube solo lo que falte).
- Componentes y agentes de terceros (B): NO se suben a `ui-yaiwes`. Se dejan como zips en partes + manifiesto en la ubicación que Antonio elija en la FASE 3 (opciones: bucket de Hugging Face de COMAND-CENTER-1, repo aparte `ui-yaiwes-componentes`, o assets de un release).

REGLAS DURAS
1. Nada se borra en el origen. Nada se mueve en las fases 0–2.
2. Clasificación por evidencia, no por nombre: LICENSE/COPYING de otro autor, package.json/pyproject/go.mod con repositorio upstream, carpetas vendor/node_modules/_work/.git anidados, hashes que coinciden con un upstream, o commits de autores externos => terceros (B). Archivos creados por el Director o sus agentes (autoría en git log del propio repo, carpetas "UI YAIWES", "YAIWES NN", "readme arquitectura", "Wordflow LOOP", "Documentos del proyecto", "motores de descarga…", HTML originales subidos por él) => propio (A).
3. Lo dudoso va a la clase C ("a decidir por Antonio") con la razón; no lo decidas tú.
4. Cada archivo queda registrado con: ruta, tamaño, sha256, blob de git, clase (A/B/C), motivo, licencia detectada.
5. Zips en partes de máx. 90 MB (límite de GitHub 100 MB), nombre `<grupo>.zip.part-0001…`, con `<grupo>.manifest.json` (lista de archivos + sha256 + sha256 de cada parte) y un test de integridad (reconstruir y listar sin extraer).
6. Disco y empuje limitados: trabaja por lotes, borra temporales, no empujes lotes grandes de una vez (HTTP 413); reintentos máx. 4 con espera 2/4/8/16 s. Sin GitHub Actions. Sin PR. Sin force-push.

FASES (detente al final de cada una y reporta)
FASE 0 — Inventario y clasificación (solo lectura): tabla por clase A/B/C con nº de archivos y MB, y por carpeta de primer nivel. Entrega `clasificacion.csv` y `resumen.md`. ESPERA la aprobación de Antonio.
FASE 1 — Empaquetado: crea los zips en partes de B y de C con los motores y verifica sha256 de cada parte. El grupo A no se empaqueta: se compara contra `ui-yaiwes` y se lista lo que falta.
FASE 2 — Verificación cruzada: re-extrae una muestra del 1 % de cada zip y compara con el origen; cuenta archivos origen = A + B + C (sin pérdidas ni duplicados). Entrega la tabla de cuadre.
FASE 3 — Movimiento (solo con "OK" explícito de Antonio y destino confirmado): sube A faltante a `ui-yaiwes`; sube B/C empaquetados al destino elegido; registra todo en `REGISTRO-MOVIDOS-SEPARACION.md` y `.manifest.json`.

ENTREGA
Tabla final: clase | archivos | MB | zips | sha256 verificado | destino. Lista de decisiones pendientes para Antonio. Lo que no pudiste hacer y por qué.
```

Contexto del Director (para quien lo lea): en `ui-yaiwes` ya están los 2.566 + 3.121 archivos propios movidos con el motor 3; quedan por clasificar unos 743.000 archivos de terceros del repo `frontend` (componentes OSS ~552.000, Empaque-local/Download programas ~95.000, Watchdog UI ~25.600, runtime/vendor ~24.300, Download librerías ~14.400, ENGINE ADAPTER ~11.300, _work ~6.200).
