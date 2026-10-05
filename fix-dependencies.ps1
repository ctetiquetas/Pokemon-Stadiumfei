param([Parameter(Mandatory)][string]$PortPath)
$ErrorActionPreference = 'Stop'
$PortPath = (Resolve-Path -LiteralPath $PortPath).Path
# Backport SDL's builtin guard for current Clang, preserving older compiler fallback.
foreach ($relative in @('lib\rt64\src\contrib\mupen64plus-win32-deps\SDL2-2.26.3\include\SDL_endian.h','build\_deps\sdl2-src\include\SDL_endian.h')) {
    $path = Join-Path $PortPath $relative
    $content = [IO.File]::ReadAllText($path)
    $content = $content.Replace('#ifdef __clang__','#if defined(__clang__) && !_SDL_HAS_BUILTIN(_m_prefetch)')
    $content = $content.Replace('#if defined(__clang__) && !__has_builtin(_m_prefetch)','#if defined(__clang__) && !_SDL_HAS_BUILTIN(_m_prefetch)')
    if ($content -ne [IO.File]::ReadAllText($path)) { [IO.File]::WriteAllText($path,$content) }
}
$path = Join-Path $PortPath 'lib\rt64\src\contrib\imgui\imgui_widgets.cpp'
$content = [IO.File]::ReadAllText($path)
$updated = $content.Replace('IMSTB_TEXTEDIT_CHARTYPE empty_string;','IMSTB_TEXTEDIT_CHARTYPE empty_string = 0;')
if ($updated -ne $content) { [IO.File]::WriteAllText($path,$updated) }
$patch = Join-Path $PSScriptRoot 'patches\input-deadzone.patch'
& git -C $PortPath apply --reverse --check $patch 2>$null
if ($LASTEXITCODE -ne 0) {
    & git -C $PortPath apply --check $patch
    if ($LASTEXITCODE -ne 0) { throw 'El parche de entrada no coincide; revisar cambios locales antes de aplicarlo' }
    & git -C $PortPath apply $patch
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo aplicar el parche de entrada' }
}
Write-Host 'Compatibilidad SDL/ImGui/entrada preparada.'
