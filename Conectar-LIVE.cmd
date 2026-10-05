@echo off
cd /d "%~dp0"
echo Abre Magikarp e inicia la ronda antes de continuar.
echo Conectando al LIVE de @xkafei. Ctrl+C detiene el puente.
node bridge.mjs --live xkafei
if errorlevel 1 pause
