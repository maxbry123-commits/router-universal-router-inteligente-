# 📂 prueba chat — laboratorio UI YAIWES

## Propósito
Esta raíz es el laboratorio de frontend por paneles. Se trabaja por versiones independientes y se valida en **Vercel Preview**. No es producción y no autoriza cambios en `main`.

## Estructura obligatoria

```text
📂 prueba chat/
├── README-INSTRUCCIONES/
├── HANDOFF/
├── Panel chat/
├── Panel configuración/
├── Panel canvas video imágenes/
├── Panel planificación/
├── Panel agente Swarm/
├── Panel router/
└── Panel file/
```

Cada panel mantiene versiones `v001/`, `v002/`, etc. Una versión aprobada se congela; una mejora nueva crea una versión nueva.

## Reglas del Director
1. **NO código monolítico.**
2. **Edición quirúrgica.** No sustituir un bloque completo si el cambio afecta sólo una parte concreta.
3. **Único skill visual autorizado:** `Maxbry UI fromtend`.
4. **Cada ventana/panel vive en archivos propios.** No mezclar componentes de otro panel.
5. **NO MOCK estático.** Un control presentado como funcional debe tener función real o mostrar estado pendiente/bloqueado.
6. **Cada versión candidata debe quedar lista para desplegar.**
7. **Versión aprobada = congelada.** No reescribir una versión aprobada; crear la siguiente.
8. **MOVE → VERIFY → DELETE.** Primero colocar y verificar en destino; sólo después eliminar el origen.
9. **Un panel por cambio/salida**, salvo una orden explícita del Director.
10. **Fail closed.** Sin evidencia real no declarar PASS.

## Regla Vercel
- Esta raíz se prueba **sólo mediante Vercel Preview** de la rama de laboratorio.
- **NO desplegar a Production.**
- **NO fusionar a `main`** sin autorización expresa del Director.
- Un commit en la rama de Preview puede redeplegar el Preview; esto es esperado dentro de este laboratorio.
- El Preview puede consumir backend real. Acciones destructivas o de escritura no se consideran inocuas sólo por estar en Preview.

## Separación de paneles
- `Panel chat/`: conversación y composer.
- `Panel configuración/`: apariencia, paletas y preferencias UI.
- `Panel canvas video imágenes/`: imágenes, vídeo, vista previa y media.
- `Panel planificación/`: seguimiento, Crazy Wall, DAG, eventos, ledger y planificación.
- `Panel agente Swarm/`: agentes, roles, tareas y estados multiagente.
- `Panel router/`: interfaz propia del Router; no inventar funcionalidad sin contrato real.
- `Panel file/`: archivos/documentos; no inventar funcionalidad sin contrato real.

No se permite crear una SPA/tabs que mezcle estos paneles para sustituirlos.

## Fuente visual autorizada
En la salida 2 se moverá y cableará dentro de esta raíz el Skill `Maxbry UI fromtend`, sus imágenes y documentación. Hasta entonces, no sustituir esa fuente por estilos inventados.

## Estado de migración
- **SALIDA 1:** crear raíz + introducir código recuperado/real en versiones `v001`.
- **SALIDA 2:** mover Skill Maxbry UI fromtend + imágenes + documentos de especificación/plan y cablear README/HANDOFF/paneles.

## Regla de limpieza
No borrar una ruta antigua hasta comprobar el read-back del destino y, cuando aplique, el Preview correspondiente. Si falla, conservar el origen y marcar `BLOCKED`.
