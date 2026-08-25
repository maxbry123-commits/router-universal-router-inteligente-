# METODO_ZIP_COPY_DETERMINISTA

**Método de trabajo obligatorio** — copiar desde ZIP a GitHub **sin reescribir** contenido + verificación cruzada.

**Fuente canónica:** https://github.com/maxbry123-commits/agentes/blob/main/METODO_ZIP_COPY_DETERMINISTA.md  
**Repo:** router-universal-router-inteligente-

## Principio
ZIP bytes → extract sin modificar → blob exacto → commit → verify SHA. Fail-closed. Sin force-push. Token solo por ref.

## 10 métodos (resumen)
1 Local unzip+git · 2 Actions unzip · 3 Contents API · 4 **Git Data API** (recomendado) · 5 zip-deployer · 6 PyGithub · 7 gh CLI · 8 curl · 9 clone+unzip · 10 Marketplace Action

## Schema
EXTRACT → MANIFEST(path+sha256) → TOKEN → HEAD → WRITE → VERIFY → EVIDENCE

## Verify
`sha256(destino) == sha256(zip)` por archivo o FAIL.

## Raíz paralela
`apps/ packages/ tools/ docs/ CODEOWNERS`

## PASS checklist
Manifest · token ref · expected_head · no force · sha256 match · evidence · HOLD protegidos · dry_run primero.
