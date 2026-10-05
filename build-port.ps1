param([string]$PortPath = (Join-Path $PSScriptRoot '..\PokemonStadiumRecomp'))
$ErrorActionPreference = 'Stop'
$PortPath = (Resolve-Path -LiteralPath $PortPath).Path
$vswhere = 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'
$vs = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (!$vs) { throw 'Falta Visual Studio con herramientas C++' }
$cmake = Join-Path $vs 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
$clangDir = Join-Path $vs 'VC\Tools\Llvm\x64\bin'
$ninjaDir = Join-Path $vs 'Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja'
if (!(Test-Path -LiteralPath (Join-Path $clangDir 'clang-cl.exe'))) { throw 'Falta C++ Clang tools for Windows' }
# fmt 10.2.2 overwrites this compatibility option. Preserve the caller override.
foreach ($relative in @('n64recomp\lib\fmt\include\fmt\base.h','lib\N64ModernRuntime\N64Recomp\lib\fmt\include\fmt\base.h')) {
    $path = Join-Path $PortPath $relative
    $content = [IO.File]::ReadAllText($path)
    $needle = '#if !defined(__cpp_lib_is_constant_evaluated)'
    $replacement = "#if defined(FMT_USE_CONSTEVAL)`n// Respect the caller compatibility override.`n#elif !defined(__cpp_lib_is_constant_evaluated)"
    if ($content.Contains($needle)) { [IO.File]::WriteAllText($path,$content.Replace($needle,$replacement)) }
}
$elf = Join-Path $PortPath 'disasm\build\pokestadium-us.elf'
if (!(Test-Path -LiteralPath $elf)) { throw 'Primero genera el ELF en WSL siguiendo BUILD-STATUS.md' }
$batch = @"
@echo off
call "$vs\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
set "PATH=$clangDir;$ninjaDir;%PATH%"
cd /d "$PortPath"
"$cmake" -S n64recomp -B n64recomp/build -G Ninja -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_FLAGS=/EHsc /DFMT_USE_CONSTEVAL=0" -DWITH_ARES_BRIDGE=OFF
if errorlevel 1 exit /b 1
"$cmake" --build n64recomp/build --target N64RecompCLI -j 4
if errorlevel 1 exit /b 1
n64recomp\build\N64Recomp.exe game.toml
if errorlevel 1 exit /b 1
"$cmake" -S . -B build -G Ninja -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_FLAGS=/EHsc /DFMT_USE_CONSTEVAL=0" -DPSR_NO_CONSOLE=ON -DWITH_ARES_BRIDGE=OFF -DWITH_DEV_DIVERGENCE=OFF
if errorlevel 1 exit /b 1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\fix-dependencies.ps1" -PortPath "$PortPath"
if errorlevel 1 exit /b 1
"$cmake" --build build --target PokemonStadiumRecomp -j 4
exit /b %errorlevel%
"@
$batchPath = Join-Path $PortPath '_tmp_stadiumfei_build.bat'
[IO.File]::WriteAllText($batchPath,$batch,[Text.Encoding]::ASCII)
& cmd.exe /c $batchPath
if ($LASTEXITCODE -ne 0) { throw "Compilación falló: $LASTEXITCODE" }
New-Item -ItemType Directory -Path (Join-Path $PortPath "build\tcc") -Force | Out-Null
Copy-Item -Path (Join-Path $PortPath "lib\N64ModernRuntime\N64Recomp\lib\tcc\*") -Destination (Join-Path $PortPath "build\tcc") -Recurse -Force
Write-Host "Ejecutable: $PortPath\build\PokemonStadiumRecomp.exe"
