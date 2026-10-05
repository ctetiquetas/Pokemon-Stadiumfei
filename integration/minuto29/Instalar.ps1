param([string]$Shipwright="$env:USERPROFILE\Documents\GitHub\Shipwright")
$ErrorActionPreference='Stop'
$patch=Join-Path $PSScriptRoot 'app.patch'
$legacy=Join-Path $PSScriptRoot 'legacy-app.patch'
git -C $Shipwright apply --ignore-space-change --reverse --check $patch 2>$null
if ($LASTEXITCODE -ne 0) {
    $revertedLegacy=$false
    git -C $Shipwright apply --ignore-space-change --reverse --check $legacy 2>$null
    if ($LASTEXITCODE -eq 0) {
        git -C $Shipwright apply --ignore-space-change --reverse $legacy
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo actualizar la integración anterior' }
        $revertedLegacy=$true
    }
    git -C $Shipwright apply --ignore-space-change --check $patch
    if ($LASTEXITCODE -ne 0) {
        if ($revertedLegacy) { git -C $Shipwright apply --ignore-space-change $legacy }
        throw 'La interfaz cambió; revisa app.patch antes de instalar.'
    }
    git -C $Shipwright apply --ignore-space-change $patch
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo aplicar la integración' }
}
foreach ($name in 'stadium_minuto29.py','magikarp_live.py','magikarp_gifts.py') {
    Copy-Item (Join-Path $PSScriptRoot $name) (Join-Path $Shipwright "tools\tiktok-live-bridge\$name") -Force
}
Write-Host 'Integración instalada. Reinicia la interfaz TikTok y abre Minuto 29 → Magikarp.'
