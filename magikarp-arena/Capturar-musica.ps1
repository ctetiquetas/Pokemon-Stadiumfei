param([string]$Port="$env:USERPROFILE\Documents\GitHub\PokemonStadiumRecomp")
$ErrorActionPreference='Stop'
$arenaPython=Join-Path $env:LOCALAPPDATA 'Python\pythoncore-3.14-64\python.exe'
if (-not (Test-Path $arenaPython)) { $arenaPython=(Get-Command python).Source }
$exe=Join-Path $Port 'build\PokemonStadiumRecomp.exe'
if (Get-Process PokemonStadiumRecomp -ErrorAction SilentlyContinue) { throw 'Cierra el port antes de capturar la música.' }
$assets=Join-Path $PSScriptRoot 'local-assets'
New-Item -ItemType Directory -Force $assets | Out-Null
& $arenaPython (Join-Path $PSScriptRoot 'install_audio_capture.py') $Port
if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar el capturador' }
& (Join-Path $Port '_tmp_build_port.bat')
if ($LASTEXITCODE -ne 0) { throw 'No se pudo compilar el port' }
$previous=@{}
foreach ($name in 'PSR_AUTOBOOT','PSR_DEBUG_PORT','STADIUMFEI_MUSIC_REQUEST') { $previous[$name]=[Environment]::GetEnvironmentVariable($name,'Process') }
$captureProcess=$null
try {
    $env:PSR_AUTOBOOT='1'; $env:PSR_DEBUG_PORT='4372'
    $env:STADIUMFEI_MUSIC_REQUEST=Join-Path $assets 'music-request.txt'
    Set-Content -LiteralPath $env:STADIUMFEI_MUSIC_REQUEST -Value '0 -1' -Encoding ascii
    $captureProcess=Start-Process $exe -WorkingDirectory (Split-Path $exe) -WindowStyle Hidden -RedirectStandardError (Join-Path $assets 'music-capture.log') -PassThru
    & $arenaPython (Join-Path $PSScriptRoot 'capture_music.py') --assets $assets
    if ($LASTEXITCODE -ne 0) { throw 'Falló la captura; consulta local-assets/music-capture.log' }
} finally {
    if ($captureProcess -and -not $captureProcess.HasExited) { Stop-Process -Id $captureProcess.Id }
    foreach ($name in $previous.Keys) { [Environment]::SetEnvironmentVariable($name,$previous[$name],'Process') }
}
Write-Host 'Música y efectos originales listos para la sala, la cuenta, los saltos y el ganador.'
