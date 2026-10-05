# Magikarp en Minuto 29

Integración con la interfaz existente de Shipwright. Utiliza sus eventos LikeEvent de TikTok; 10 taps acumulados = una pulsación A del jugador 1.

En la interfaz: **Minuto 29 → Magikarp → Abrir Pokémon Stadium → Conectar al LIVE**. Entra manualmente a Kids’ Club y comienza Magikarp; después pulsa **Activar taps**. Pausa al terminar la ronda. **Probar +10 taps** verifica el control sin un LIVE.

Captura la ventana de Pokémon Stadium desde OBS o TikTok LIVE Studio para transmitirla. El botón conecta el control al LIVE; la emisión de vídeo se configura en tu programa de transmisión.

La aplicación debe reiniciarse después de instalar. Los módulos se copian a `Shipwright/tools/tiktok-live-bridge/` y `app.patch` contiene solamente los cambios del botón y el reenvío de taps. Usa `Instalar.ps1` para reinstalar. Battle Royal y Carrera de agua conservan sus controles originales.

El port se busca en la carpeta hermana `PokemonStadiumRecomp/build/PokemonStadiumRecomp.exe`, con la ROM local `PokemonStadiumRecomp/baserom.z64`. No se incluyen ROMs ni binarios del juego.

Pruebas: `python -m unittest test_stadium_backend.py`. Se verifica acumulación, resto, pausa y desconexión. La puntuación dentro de una ronda de Magikarp y los eventos de un LIVE real aún requieren prueba con el usuario. Ajusta la duración de A y el intervalo en el panel si el salto necesita otro ritmo.
