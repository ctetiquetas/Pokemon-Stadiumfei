# Preparación de compilación — 4 de octubre de 2026

- Visual Studio Community 18: Clang instalado y clang-cl.exe comprobado.
- WSL instalado. Microsoft-Windows-Subsystem-Linux habilitado mediante DISM; código de salida 3010: requiere reiniciar Windows.
- VirtualMachinePlatform aparece habilitado. Antes del reinicio WSL2 informa que no puede iniciar por virtualización; volver a comprobar después de reiniciar. WSL1 es una alternativa si no hay virtualización disponible.
- La ROM local se convirtió a z64 y se verificó contra MD5 ed1378bc12115f71209a77844965ba50 (US 1.0). Se mantiene fuera de GitHub.
- Dependencias descargadas en la carpeta local PokemonStadiumRecomp: mstan/N64ModernRuntime, mstan/rt64, mstan/N64Recomp, concurrentqueue y SlotMap.
- n64recomp fijado al SHA 2b949c5c3f1c41dd76023e7626a6302a4a262a8a indicado por n64recomp.pin.
- Subdependencias esenciales de N64Recomp y RT64 inicializadas. Los commits del emulador Ares opcional ya no están disponibles en su remoto; se omiten usando WITH_ARES_BRIDGE=OFF. No afectan la prueba de Magikarp prevista, pero la compilación final aún debe validarse.
- El runtime trae su propia revisión de N64Recomp; comprobar compatibilidad al configurar antes de regenerar el juego.
- Puerto corregido del puente: 4371, según src/main/main.cpp del port. Dos pruebas automáticas pasan.

## Continuación después del reinicio

1. Comprobar WSL e instalar una distribución Ubuntu para generar disasm/build/pokestadium-us.elf siguiendo docs/disasm-build.md del port.
2. Instalar dependencias Linux de pret, ejecutar la extracción y generar el ELF. Respetar las modificaciones existentes en el submódulo disasm.
3. Compilar el recompiler fijado y generar los archivos C usando game.toml.
4. Configurar y compilar con build_ssanne.bat; resolver las dependencias restantes y comprobar compatibilidad.
5. Abrir Magikarp y probar el puente con taps simulados. Ajustar el intervalo; todavía no se ha verificado un salto ni un punto dentro del juego.
6. Probar TikTok LIVE con el usuario del transmisor; la integración real y la instalación de paquetes Node siguen pendientes.

No se ha generado aún un ejecutable jugable. No se reinició automáticamente el equipo.
