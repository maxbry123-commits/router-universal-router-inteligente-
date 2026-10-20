# Plan de fábrica · para leer (cableado)

Orden: advertencia → DAG → fases → 39 → seguridad → empaque.

## 1. Advertencia (2 funciones)

1. Fábrica interna (clave). El usuario **no entra**.  
2. Runtime plantilla: el usuario usa lo publicado.

https://github.com/maxbry123-commits/frontend/blob/main/fabrica%20de%20UI%20INTERFACE%20fromtend/00-ADVERTENCIA-Y-MODELO.md  
https://github.com/maxbry123-commits/frontend/blob/main/fabrica%20de%20UI%20INTERFACE%20fromtend/PLAN-FUSION-Y-CABLEADO.md

## 2. DAG determinista (otro chat sigue esto, no inventa)

https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/fabrica-ui/PLAN-DAG-DETERMINISTA.json  
https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/fabrica-ui/PLAN-PASO-A-PASO.md  
Bitácora nodos: https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/fabrica-ui/bitacora-fabrica/state.json

Nodos F0…F12: inventario 39 → copiar lote-01 → ABS/security/connectors → HOST → PWA → Tauri → Capacitor → conector user-picked → cifrar wires → strip Factory → Action 39 → OK por ID → `03-producto`.

## 3. Kernel que ya vive

https://github.com/maxbry123-commits/frontend/tree/main/UI%20YAIWES%20interface/fabrica-ui/runtime/lote-01-nucleo-host  
ABS: `03-action-bus.js` · Wire: `10-wire.js` · Clave: `06-access-key.js`

Botón (JS del HTML) → ABS → HOST iframe → kernel (local | web | github | huggingface | gdrive | database).

## 4. 39 ventanas

Descripciones + **fotos visibles**:  
https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/Ui%20Yaiwes%20interface%20beta/02-fromted/DESCRIPCIONES-39.md  
Host: https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/Ui%20Yaiwes%20interface%20beta/02-fromted/HOST.html  
Índice: https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/Ui%20Yaiwes%20interface%20beta/02-fromted/INDEX.json

## 5. Llegó / falta

https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/fabrica-ui/LLEGO-VS-FALTA.md  
https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/fabrica-ui/OSS-USAR.md

## 6. 50 justificaciones

https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/fabrica-ui/50-JUSTIFICACION.md

## 7. Seguridad

https://github.com/maxbry123-commits/frontend/tree/main/UI%20YAIWES%20interface/seguridad

## 8. Empaque

https://github.com/maxbry123-commits/frontend/tree/main/UI%20YAIWES%20interface/empaque

## 9. Skill + LOOP + goals

https://github.com/maxbry123-commits/frontend/blob/main/Skills%20arquitectura%20frontend%20Yaiwes/fromted-frontend-architecture/SKILL.md  
https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/readme%20arquitectura%20UI%20YAIWES%20interface%20beta/LOOP-OPERATIVO.md  
https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/readme%20arquitectura%20UI%20YAIWES%20interface%20beta/GOALS-12.md

## 10. Handoff

https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/handoff%20UI%20YAIWES%20interface.md

## Subir ZIPs / fotos (tú)

Fotos: https://github.com/maxbry123-commits/frontend/upload/main/UI%20YAIWES%20interface/Ui%20Yaiwes%20interface%20beta/01-original/FOTOS-REF  
ZIPs fábrica: https://github.com/maxbry123-commits/frontend/upload/main/fabrica%20de%20UI%20INTERFACE%20fromtend/componentes%20para%20fabrica%20de%20interface
