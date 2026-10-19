# Troubleshooting

## `blender.exe not found under ...`

Ejecuta:

```powershell
.\scripts\install_blender.ps1
```

Si Blender está en otra carpeta, pásala explícitamente:

```powershell
.\tools\blender_tool\run_blender.ps1 `
  -BlenderRoot 'D:\Apps\BlenderPortable' `
  -Commands .\scenes\smoke_test.json
```

## PowerShell bloquea el script

Ejecuta una sola vez con una política limitada al proceso actual:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

Después vuelve a lanzar el comando. No es necesario cambiar la política de todo el equipo.

## `unknown op`

El nombre no aparece en el diccionario `OPS` de `blender_cli.py`. Consulta [scene-format.md](scene-format.md) para la lista actual.

## Error con `ico` o `sphere`

`add_mesh` usa el sufijo real de la operación de Blender. Sustituye:

```text
ico    -> ico_sphere
sphere -> uv_sphere
```

## Error con `BLENDER_EEVEE_NEXT`

La versión verificada acepta `BLENDER_EEVEE`. Ese es el identificador usado por `ai_scene.json`.

## La resolución no es la esperada

En el JSON, `scale` es un factor. Usa `1.0` para el 100 %. El puente multiplica internamente por 100 antes de asignar `resolution_percentage`.

## El glow aparece en Viewer, pero no en el PNG

En Blender 5.2 no basta con conectar Glare al nodo Viewer. El archivo guardado necesita esta ruta:

```text
Render Layers.Image -> Glare.Image -> Group Output.Image
```

`verify_ai_scene.json` comprueba ese enlace. La prueba A/B local produjo imágenes distintas en 2303 de 2304 píxeles al intercambiar las conexiones de Group Output y Viewer.

## El nodo Glare rechaza `FOG_GLOW`

En la API verificada, el valor de la entrada `Type` es `Fog Glow`. La escena final configura:

```text
Type      = Fog Glow
Threshold = 0.4
Strength  = 5.0
```

## El informe termina con `"ok": false`

Lee el array `errors`. Cada entrada contiene el nombre de la operación y la excepción real. El proceso también devuelve un código distinto de cero, por lo que una automatización puede detenerse sin analizar todo el log.

## Advertencias sobre `use_nodes`

Blender 5.2 puede mostrar avisos de deprecación para `World.use_nodes` y `Material.use_nodes`. En la versión objetivo son avisos, no errores; el criterio de éxito es `BLENDER_CLI_REPORT`.

## El experimento de flythrough falla

`tools/blender_tool/scenes/demo_flythrough.json` fue una prueba incompleta, no parte del flujo reproducible. El log local muestra dos causas:

- La función de keyframes termina intentando llamar `keyframe_insert` sobre un `Vector`.
- `FFMPEG` no aparece entre los formatos válidos de imagen en esa configuración de Blender.

El archivo se conserva localmente como evidencia de investigación y está excluido del repositorio mediante `.gitignore`.

