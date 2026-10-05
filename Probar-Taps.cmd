@echo off
cd /d "%~dp0"
node bridge.mjs
if errorlevel 1 pause
