# Formato de escena JSON

El puente acepta una lista de operaciones o este formato recomendado:

```json
{
  "meta": {
    "name": "example",
    "note": "human-readable context"
  },
  "ops": [
    {"op": "new_scene"}
  ]
}
```

Los ángulos se expresan en grados. Las posiciones, rotaciones y escalas usan listas `[x, y, z]`. `${PROJECT_ROOT}` está disponible en cualquier cadena.

## Operaciones disponibles

| Operación | Función |
| --- | --- |
| `new_scene` | Elimina objetos y datos huérfanos; crea un mundo nuevo. |
| `load_blend` | Abre un archivo `.blend`. |
| `set_world` | Configura color y fuerza del fondo. |
| `add_mesh` | Añade una primitiva de `bpy.ops.mesh`. |
| `set_transform` | Cambia posición, rotación o escala de un objeto. |
| `add_material` | Crea o actualiza un material Principled BSDF. |
| `assign_material` | Asigna un material por patrones de nombre. |
| `add_light` | Añade luz `point`, `sun`, `spot` o `area`. |
| `add_camera` | Añade y activa una cámara. |
| `add_empty` | Añade un objeto Empty. |
| `track_to` | Hace que un objeto apunte a un Empty. |
| `connect` | Une dos puntos con uno o más cilindros. |
| `neural_net` | Genera capas de nodos y enlaces entre ellas. |
| `set_render` | Configura motor, resolución, escala, muestras y dispositivo. |
| `render` | Renderiza una imagen fija y la guarda. |
| `save` | Guarda el archivo `.blend`. |
| `delete` | Elimina objetos usando patrones. |
| `exec` | Ejecuta Python de confianza dentro de Blender. |

## Ejemplo mínimo

```json
{
  "ops": [
    {"op": "new_scene"},
    {"op": "add_mesh", "kind": "cube", "name": "Cube", "size": 1.0},
    {"op": "add_camera", "name": "Cam", "location": [4, -6, 3]},
    {"op": "track_to", "object": "Cam", "location": [0, 0, 0]},
    {"op": "set_render", "engine": "BLENDER_EEVEE", "width": 640, "height": 360, "scale": 1.0},
    {"op": "render", "path": "${PROJECT_ROOT}/output/example.png"}
  ]
}
```

## Detalles importantes

### Primitivas

`kind` se inserta en `bpy.ops.mesh.primitive_<kind>_add`. En Blender 5.2, los nombres usados por este proyecto son `cube`, `plane`, `torus`, `ico_sphere` y `uv_sphere`.

### Escala de render

El formato usa un factor:

```json
{"op": "set_render", "scale": 1.0}
```

El puente calcula `resolution_percentage = round(scale * 100)`. Un valor JSON de `100` intentaría establecer 10000 % y no representa una escala completa.

### Motor

La escena fue creada y comprobada con:

```json
{"op": "set_render", "engine": "BLENDER_EEVEE"}
```

### `exec`

`exec` recibe acceso a `bpy`, `math` y `Vector`, y el código puede importar otros módulos disponibles en Blender. No uses escenas JSON no confiables.

