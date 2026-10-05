# Estado de compilación — 5 de octubre de 2026

## Preparación completada

- Clang de Visual Studio Community 18 instalado.
- WSL y Ubuntu funcionando tras reiniciar; herramientas MIPS y entorno Python instalados.
- ROM US 1.0 convertida localmente a z64 y verificada. No se sube al repositorio.
- Extracción y reconstrucción de pret completadas: ROM reconstruida con MD5 ed1378bc12115f71209a77844965ba50 y resultado OK.
- ELF generado: PokemonStadiumRecomp/disasm/build/pokestadium-us.elf.
- N64Recomp.exe compilado; generación de código C del juego completada.
- Ejecutable Windows compilado correctamente (build rc=0) y arranque comprobado con la ROM local.
- Paquetes Node instalados; importación del conector TikTok y dos pruebas del puente pasan.
- Usuario para el LIVE: @xkafei. Regla: 10 likes recibidos = una pulsación A del jugador 1.

## Revisiones usadas

- Port: c99ed8effd71f9dcea6ede78f606512daa57ea2a.
- pret/disasm: 756f7e332ee3837ead17197276cebc071108e8c6.
- N64Recomp para generación estática: 2b949c5c3f1c41dd76023e7626a6302a4a262a8a (n64recomp.pin).
- N64ModernRuntime: d4bf8828514c567df42ff049e1e90505bdcdb734.
- N64Recomp del runtime: c955b4e03fc42e75877b27901424c75ee7fe7be5. El pin del submódulo del runtime no incluye las fuentes TCC que su código usa; se alineó con main para obtenerlas.
- RT64: 821a8676963a1b486ca693ebaf8dd606f6c31c64.

## Ajustes necesarios

- Finales de línea LF en scripts y fuentes de pret: contenido idéntico al comparar ignorando finales de línea; se conserva la modificación previa de tools/n64splat.
- fmt: respetar FMT_USE_CONSTEVAL=0 para compatibilidad con Clang/VS actual. build-port.ps1 aplica este ajuste idempotente en las dos copias de fmt.
- Ares opcional desactivado: los commits de ese submódulo no están disponibles en su remoto. No se usa para jugar.
- SDL: guard del builtin _m_prefetch tomado del SDL upstream actual para Clang moderno; aplicado en las dos cabeceras usadas.
- ImGui: inicializar empty_string a cero para evitar el diagnóstico de variable no inicializada.
- Entrada analógica: parche local input-deadzone.patch normaliza ejes para suplir la función ausente del runtime.
- TinyCC local copiado a build/tcc para las cargas dinámicas del runtime.
- Puerto TCP del juego: 4371.

## Uso previsto

1. Abrir-Port.cmd abre el launcher. Selecciona la ROM local y asigna teclado o mando al jugador 1.
2. Entra en Kids' Club, selecciona Magikarp e inicia una ronda.
3. Probar-Taps.cmd: escribe 10 y Enter, o 9 y después 1. reset borra la cola; q detiene el puente.
4. Conectar-LIVE.cmd conecta @xkafei si el LIVE está activo. Detén y reinicia el puente entre rondas.

Prueba del puente contra el ejecutable real completada: 9 + 1 taps generaron una sola pulsación A (presión, liberación y limpieza al salir). El contador VI avanzó y A quedó liberada. El usuario confirmó que pudo entrar a Magikarp y jugar una partida.

La duración de A y el intervalo todavía necesitan calibración jugando. El código de Magikarp (fragmento 6) consulta pulsaciones y A sostenido durante las fases de animación; una pulsación enviada no garantiza un punto. La prueba real del LIVE también sigue pendiente.

Procedimiento de ELF: BUILD-WSL.md. Recompilación nativa: build-port.ps1.
