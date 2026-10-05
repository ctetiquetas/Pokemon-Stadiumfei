# Generar ELF con Ubuntu/WSL

La distribución Ubuntu y sus herramientas ya están instaladas en este equipo. Desde PowerShell, entra con `wsl -d Ubuntu -u root` y ejecuta:

```bash
cd /mnt/c/Users/xkafe/Documents/GitHub/PokemonStadiumRecomp/disasm
source .venv/bin/activate
make setup
make extract
make -j4 RUN_CC_CHECK=0
```

Antes del primer uso en Windows, normaliza a LF los scripts .py/.sh y las fuentes .c/.h/.s/.inc de include/, src/, tools/ y lib/. Los archivos llegaron con CRLF; el IDO antiguo y los intérpretes de Linux los rechazan. La normalización no debe alterar el contenido: comprobar con `git diff --ignore-space-at-eol`.

No ejecutar `make init` sobre una copia con cambios existentes: incluye una limpieza. La extracción escribe en asm/us y assets/us; conservar antes cualquier cambio manual en esas carpetas.

La salida obtenida en este equipo reconstruyó la ROM con MD5 ed1378bc12115f71209a77844965ba50 y terminó con OK. El ELF resultante sirve de entrada a N64Recomp.

Después ejecuta `powershell -ExecutionPolicy Bypass -File .\build-port.ps1` desde Pokemon-Stadiumfei. El script asume las dependencias ya preparadas en la carpeta hermana PokemonStadiumRecomp y usa el ajuste de compatibilidad de fmt necesario en este equipo.
