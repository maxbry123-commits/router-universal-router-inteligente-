# Nota de arquitectura — Backend + Frontend + Diseño UI YAIWES interface

Fecha: 2026-09-27  
Repo: `maxbry123-commits/frontend`  
Branch: `main`

## Propósito

Esta nota conecta en un solo punto la arquitectura visual de **UI YAIWES interface**, la separación entre **frontend** y **backend**, el documento de arquitectura que se vaya a subir y las evidencias visuales del proyecto.

## Frontend

El frontend es la capa visible e interactiva de UI YAIWES interface.

Incluye:
- ventanas y superficies visuales;
- editor/interfaz;
- layouts, paneles, navegación y componentes;
- interacción del usuario;
- estados visuales;
- referencias de diseño;
- integración de componentes OSS que pertenecen a la experiencia de interfaz.

Ruta principal del proyecto:
`UI YAIWES interface/`

Referencia de arquitectura:
`readme arquitectura UI YAIWES interface beta/README.md`

## Backend

El backend es la capa que recibe las acciones originadas en la interfaz y las conecta con capacidades externas o internas.

Flujo base documentado actualmente:

`BOTÓN / UI -> Action Bus -> HOST -> kernel -> local | web | github | huggingface | gdrive | database`

Regla: la interfaz no debe convertirse en propietaria de secretos, estado global o ejecución de proveedores. La UI solicita una acción; el backend/kernel resuelve la ejecución.

## Relación Frontend ↔ Backend

`USUARIO -> FRONTEND -> ACTION BUS / CONTRATO -> HOST -> BACKEND / KERNEL -> SERVICIO / TOOL -> RESULTADO -> FRONTEND`

La arquitectura de diseño debe conservar esta separación:
- **Frontend** = presentación + interacción.
- **Backend** = ejecución + integración + datos + servicios.
- **Contrato/Action Bus** = puente controlado entre ambos.

## Documento de actualización de arquitectura

Los archivos nuevos de arquitectura/diseño que se suban para actualizar este proyecto deben colocarse en:

`UI YAIWES interface/readme arquitectura UI YAIWES interface beta/actualizaciones arquitectura/`

Carpeta:
https://github.com/maxbry123-commits/frontend/tree/main/UI%20YAIWES%20interface/readme%20arquitectura%20UI%20YAIWES%20interface%20beta/actualizaciones%20arquitectura

Subir archivo:
https://github.com/maxbry123-commits/frontend/upload/main/UI%20YAIWES%20interface/readme%20arquitectura%20UI%20YAIWES%20interface%20beta/actualizaciones%20arquitectura

El archivo que se suba allí debe considerarse **extensión de arquitectura** y debe quedar referenciado desde el README principal antes de declararlo parte de la arquitectura vigente.

## Evidencias visuales — fotos del proyecto

### Parte 1
Commit:
https://github.com/maxbry123-commits/frontend/commit/13f4e932866284fb5ddfaaf6ada5ce4809f82f46

Estas imágenes quedaron bajo:
`UI YAIWES interface/Ui Yaiwes interface beta/01-original/FOTOS-REF/`

### Parte 2
Commit:
https://github.com/maxbry123-commits/frontend/commit/c50fc98d19debe1a85817cf1129b55a99c895c9f

### Parte 3
Commit:
https://github.com/maxbry123-commits/frontend/commit/430809bd98c614435ad7597493ed46c16d6552a3

## Cableado documental

`README PRINCIPAL -> NOTA BACKEND/FRONTEND/DISEÑO -> ACTUALIZACIÓN DE ARQUITECTURA SUBIDA -> FOTOS PARTE 1/2/3 -> IMPLEMENTACIÓN -> VALIDACIÓN`

Las fotos son evidencia visual y referencia de diseño. No sustituyen el contrato técnico del frontend/backend; el archivo de arquitectura define el comportamiento y las fotos ayudan a validar que la interfaz resultante conserva la intención visual.
