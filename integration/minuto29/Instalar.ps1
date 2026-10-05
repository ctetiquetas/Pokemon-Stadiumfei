param([string]$Shipwright = "$env:USERPROFILE\Documents\GitHub\Shipwright")
$ErrorActionPreference = 'Stop'
$patch = Join-Path $PSScriptRoot 'app.patch'
git -C $Shipwright apply --reverse --check $patch 2>$null
if ($LASTEXITCODE -ne 0) {
    git -C $Shipwright apply --check $patch
    if ($LASTEXITCODE -ne 0) { throw 'La interfaz cambió; revisa app.patch antes de instalar.' }
    git -C $Shipwright apply $patch
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo aplicar la integración.' }
}
foreach ($name in 'stadium_backend.py','stadium_minuto29.py') {
    Copy-Item (Join-Path $PSScriptRoot $name) (Join-Path $Shipwright "tools\tiktok-live-bridge\$name") -Force
}
Write-Host 'Integración instalada. Reinicia la interfaz de TikTok y abre Minuto 29 → Magikarp.'
