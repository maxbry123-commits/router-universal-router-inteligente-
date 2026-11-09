<#
.SYNOPSIS
    Reusable launcher for the Blender JSON command bridge (blender_cli.py).

.DESCRIPTION
    Finds the portable Blender installation under -BlenderRoot and runs it in
    background mode with a JSON commands file. The bridge prints a final line:
        BLENDER_CLI_REPORT <json>
    Check that line for "ok": true to verify success.

.PARAMETER Commands
    Path to the JSON commands file (list of ops, or {"ops": [...]}).

.PARAMETER Exec
    Optional raw Python code executed via --python-expr (ad-hoc operations
    beyond the JSON bridge).

.PARAMETER BlenderRoot
    Folder containing the portable Blender install (default: ..\blender).

.EXAMPLE
    powershell .\run_blender.ps1 -Commands .\scenes\my_scene.json
#>
param(
    [string]$Commands,
    [string]$Exec,
    [string]$BlenderRoot = (Join-Path $PSScriptRoot "..\blender"),
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BlenderRoot)) { throw "Blender root not found: $BlenderRoot" }
$exe = Get-ChildItem -Path $BlenderRoot -Filter "blender.exe" -Recurse -ErrorAction SilentlyContinue |
    Select-Object -First 1 -ExpandProperty FullName
if (-not $exe) { throw "blender.exe not found under $BlenderRoot" }
Write-Host "[blender_tool] Using Blender: $exe"
Write-Host "[blender_tool] Project root: $ProjectRoot"

$cli = Join-Path $PSScriptRoot "blender_cli.py"
$env:BLENDER_JSON_PROJECT_ROOT = (Resolve-Path $ProjectRoot).Path
# Blender writes warnings to stderr; keep PowerShell from treating that as fatal.
$ErrorActionPreference = "Continue"
if ($Exec) {
    & $exe --background --factory-startup --python-expr $Exec 2>&1 | Write-Host
} else {
    if (-not $Commands) { throw "Provide -Commands <file.json> or -Exec <python code>" }
    $Commands = (Resolve-Path $Commands).Path
    & $exe --background --factory-startup --python $cli -- $Commands 2>&1 | Write-Host
}
exit $LASTEXITCODE
