param(
    [string]$MenuFile="$env:USERPROFILE\Downloads\Menumusic.mp3",
    [string]$PlayingFile="$env:USERPROFILE\Downloads\Magikarps.mp3"
)
$ErrorActionPreference='Stop'
foreach ($track in @($MenuFile,$PlayingFile)) {
    if (-not (Test-Path -LiteralPath $track -PathType Leaf)) { throw "No se encontró la canción: $track" }
}
$assets=Join-Path $PSScriptRoot 'local-assets'
New-Item -ItemType Directory -Force -Path $assets | Out-Null
Copy-Item -LiteralPath $MenuFile -Destination (Join-Path $assets 'Menumusic.mp3') -Force
Copy-Item -LiteralPath $PlayingFile -Destination (Join-Path $assets 'Magikarps.mp3') -Force
Write-Host 'MP3 instalados. Recarga la ventana de Magikarp y la fuente OBS.'
