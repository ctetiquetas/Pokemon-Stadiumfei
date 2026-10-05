@echo off
cd /d "%~dp0"
if not exist "..\PokemonStadiumRecomp\build\PokemonStadiumRecomp.exe" (
  echo Falta compilar el port. Consulta BUILD-STATUS.md.
  pause
  exit /b 1
)
start "Pokemon Stadiumfei" "..\PokemonStadiumRecomp\build\PokemonStadiumRecomp.exe" "..\PokemonStadiumRecomp\baserom.z64"
