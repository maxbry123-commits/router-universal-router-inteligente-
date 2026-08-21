# Método de trabajo

## Procedimiento ZIP → nueva raíz

1. Localizar el ZIP exacto en el repositorio y verificar nombre, ruta, SHA y tamaño.
2. Descargar el ZIP como archivo binario; no interpretarlo como UTF-8.
3. Extraer todos los archivos y directorios a un área temporal.
4. Inventariar la extracción y detectar si existe una carpeta envolvente creada por el ZIP.
5. Crear una sola raíz nueva con el nombre solicitado.
6. Colocar dentro de esa raíz TODO el contenido extraído, quitando únicamente la carpeta envolvente si existe.
7. Mantener nombres, rutas internas y contenido sin modificaciones.
8. Comparar ZIP ↔ raíz desplegada por archivos, directorios, tamaños y SHA/contenido cuando sea posible.
9. Crear tree/commit conservando el resto del repositorio y actualizar la rama destino.
10. Verificar directamente en GitHub que la nueva raíz contiene todo el contenido esperado.

## Reglas

- ZIP original intacto salvo instrucción expresa.
- No clasificar, mover, borrar ni reescribir otros documentos durante esta tarea.
- GitHub es la fuente de verdad.
- TERMINADA solo después de la verificación cruzada.

Flujo: `ZIP → binario → extracción → inventario → nueva raíz → despliegue completo → comparación → commit → push → verificación`.