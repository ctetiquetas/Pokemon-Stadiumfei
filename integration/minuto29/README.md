# Minuto 29 → Magikarp

Seleccionar **Magikarp** abre la ventana vertical del juego para doce jugadores. **Conectar al LIVE**, **Nueva sala**, **Comenzar ronda** y **Terminar y mostrar ganador** están en el mismo panel. Los participantes escriben `!unir`; cada diez taps propios producen un salto.

La sala usa los modelos, texturas y animaciones originales extraídos de la ROM local. Consulta [el juego y sus instrucciones](../../magikarp-arena/README.md). Para OBS: `http://127.0.0.1:4390/`, 1080 × 1920.

`Instalar.ps1` instala los módulos en la interfaz de Shipwright. `app.patch` contiene solo los cambios de esta integración. `legacy-app.patch` permite actualizar la integración anterior de un solo jugador. La aplicación debe reiniciarse después de instalar. Battle Royal y Carrera de agua mantienen sus controles.

Los archivos `stadium_backend.py` y su prueba conservan el puente anterior de control A como referencia; la nueva opción Magikarp utiliza `magikarp_live.py` y la sala multijugador.
