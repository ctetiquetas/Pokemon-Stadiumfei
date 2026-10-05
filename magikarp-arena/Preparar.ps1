param([string]$Rom="$env:USERPROFILE\Documents\GitHub\PokemonStadiumRecomp\baserom.z64")
$ErrorActionPreference='Stop'
$arenaPython=Join-Path $env:LOCALAPPDATA 'Python\pythoncore-3.14-64\python.exe'
if (-not (Test-Path $arenaPython)) { $arenaPython=(Get-Command python).Source }
$arenaNpm=(Get-Command npm.cmd).Source
Push-Location $PSScriptRoot
try {
    & $arenaNpm ci --ignore-scripts
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar el motor 3D' }
    & $arenaPython export_models.py --rom $Rom
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron extraer los gráficos locales' }
    & $arenaPython export_ui.py --rom $Rom
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo extraer la cuenta regresiva original' }
} finally { Pop-Location }
Write-Host 'Magikarp listo. Abre Minuto 29 → Magikarp en tu interfaz TikTok.'
