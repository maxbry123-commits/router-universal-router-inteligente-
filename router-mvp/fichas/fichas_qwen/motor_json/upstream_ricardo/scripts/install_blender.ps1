param(
    [string]$Destination = (Join-Path $PSScriptRoot "..\tools\blender")
)

$ErrorActionPreference = "Stop"
$Version = "5.2.2"
$archiveName = "blender-$Version-windows-x64.zip"
$downloadUrl = "https://download.blender.org/release/Blender5.2/$archiveName"
$expectedSha256 = "3849d17a682cba006075aaa3f3597ecb5c9c30ec31035b2e092c53e40679b535"
$destinationPath = [System.IO.Path]::GetFullPath($Destination)
$installPath = Join-Path $destinationPath "blender-$Version-windows-x64"
$blenderExe = Join-Path $installPath "blender.exe"

if (Test-Path -LiteralPath $blenderExe) {
    Write-Host "Blender $Version is already available at $blenderExe"
    & $blenderExe --version | Select-Object -First 1
    exit $LASTEXITCODE
}

New-Item -ItemType Directory -Force -Path $destinationPath | Out-Null
$archivePath = Join-Path ([System.IO.Path]::GetTempPath()) $archiveName

Write-Host "Downloading $downloadUrl"
Invoke-WebRequest -UseBasicParsing -Uri $downloadUrl -OutFile $archivePath

$actualSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $archivePath).Hash.ToLowerInvariant()
if ($actualSha256 -ne $expectedSha256) {
    throw "SHA-256 mismatch for $archiveName. Expected $expectedSha256, got $actualSha256"
}

Write-Host "Checksum verified. Extracting to $destinationPath"
Expand-Archive -LiteralPath $archivePath -DestinationPath $destinationPath -Force
Remove-Item -LiteralPath $archivePath -Force

if (-not (Test-Path -LiteralPath $blenderExe)) {
    throw "Installation completed, but blender.exe was not found at $blenderExe"
}

& $blenderExe --version | Select-Object -First 1
