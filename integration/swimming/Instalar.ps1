param([string]$Pokediscord="$env:USERPROFILE\Documents\GitHub\Pokediscord")
$ErrorActionPreference='Stop'
foreach($name in 'race-core.js','game.js','race-core.test.cjs') { Copy-Item (Join-Path $PSScriptRoot $name) (Join-Path $Pokediscord "experiments\kafei-swimming\$name") -Force }
Copy-Item (Join-Path $PSScriptRoot 'reward-api.cjs') (Join-Path $Pokediscord 'experiments\kafei-battle-royal\reward-api.cjs') -Force
Write-Host 'Reinicia Minuto 29 para cargar la actualización.'
