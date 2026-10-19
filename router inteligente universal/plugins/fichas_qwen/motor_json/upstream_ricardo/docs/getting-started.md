# Guía de inicio

Esta guía reproduce el proyecto desde un clon limpio en Windows x64.

## 1. Instalar Blender portable

Abre PowerShell en la raíz del repositorio:

```powershell
.\scripts\install_blender.ps1
```

El script descarga `blender-5.2.2-windows-x64.zip` desde `download.blender.org`, comprueba el SHA-256 oficial y extrae la aplicación en `tools/blender/`.

La suma esperada es:

```text
3849d17a682cba006075aaa3f3597ecb5c9c30ec31035b2e092c53e40679b535
```

Si ya existe esa instalación, el script muestra la versión y no vuelve a descargarla.

## 2. Ejecutar el smoke test

```powershell
.\tools\blender_tool\run_blender.ps1 -Commands .\scenes\smoke_test.json
```

Comprueba que el informe final tenga `"ok": true`, `"ops_total": 11` y `"errors": []`. Deben aparecer:

```text
output/smoke_test.png
output/smoke_test.blend
```

## 3. Crear AI Neural Core

```powershell
.\tools\blender_tool\run_blender.ps1 -Commands .\scenes\ai_scene.json
```

El comando debe terminar con 34 operaciones y 0 errores. Genera:

```text
output/ai_scene.png
output/ai_scene.blend
```

## 4. Verificar el `.blend`

```powershell
.\tools\blender_tool\run_blender.ps1 -Commands .\scenes\verify_ai_scene.json
```

La prueba abre el archivo guardado y valida su estructura sin volver a guardarlo.

## 5. Abrir la escena en Blender

```powershell
& .\tools\blender\blender-5.2.2-windows-x64\blender.exe .\output\ai_scene.blend
```

## Rutas alternativas

`run_blender.ps1` acepta una instalación y una raíz de salida diferentes:

```powershell
.\tools\blender_tool\run_blender.ps1 `
  -BlenderRoot 'D:\Apps\BlenderPortable' `
  -ProjectRoot 'D:\Renders\ai-neural-core' `
  -Commands .\scenes\ai_scene.json
```

El puente sustituye `${PROJECT_ROOT}` dentro del JSON antes de ejecutar las operaciones.

## Entorno verificado

- Windows x64
- PowerShell 7.6.5
- Blender 5.2.2 LTS
- Python 3.13.13 integrado en Blender
- EEVEE

No hay instalación de paquetes con `pip` ni `npm`.

