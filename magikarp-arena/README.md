# Magikarp · Minuto 29

Sala vertical 9:16 para TikTok LIVE y OBS. Hasta 12 espectadores escriben `!unir` para entrar. Cada participante conserva sus propios taps, nombre, foto y color; cada 10 taps identificados del jugador generan un salto. El marcador suma +1 cuando el salto golpea el botón. La duración se calcula desde `Magikarps.mp3`: la ronda termina al acabar la canción. Los empates muestran a los participantes empatados.

## Gráficos originales

Se reutilizan las mallas y las texturas originales del minijuego de Pokémon Stadium, junto con las animaciones de reposo, salto y victoria. El port y su descompilación sirvieron para identificar el formato y los recursos. Las reglas, la sala, la interfaz vertical y el vínculo con TikTok son nuevos para admitir doce jugadores.

La cuenta regresiva usa las cuatro imágenes originales de Ditto (3, 2, 1 y salida) extraídas por `export_ui.py`, con intervalos de 27 fotogramas a 30 FPS. Los taps se habilitan después de los 2,7 segundos de preparación. El botón usa su modelo original, su animación de impacto y las ruedas numéricas articuladas para mostrar los puntos.

El fondo «Kafeacuario · Zona de Magikarps» es una imagen nueva generada para esta sala. Se distribuye en `assets/`. La cuadrícula se adapta a los inscritos: una columna hasta tres, dos hasta seis y tres hasta doce; la última fila queda centrada y no se dibujan puestos vacíos.

`export_models.py` lee la ROM local US 1.0 en formato z64, verifica su MD5, descomprime los recursos PERS-SZP/Yay0 y recorre la geometría y las listas F3DEX2. Los modelos del Magikarp y del botón son las entradas 172 y 173 del archivo de recursos en 0x920000. El código sigue los formatos documentados por `geo_layout.c`, `12D80.c`, `17300.c`, `3FB0.h` y `gbi.h` de la descompilación del port. Se conservan los vértices compartidos por articulaciones y las texturas RGBA16/IA16/I8.

**La ROM y los recursos extraídos no se distribuyen.** `local-assets/` y `node_modules/` están ignorados por Git. Los gráficos se regeneran desde la ROM del usuario con `Preparar.ps1`. El resto de la sala puede subirse al repositorio.

## Uso

1. Ejecuta `Preparar.ps1` si es una instalación nueva. Requiere Python 3, Node/npm y tu ROM local.
2. Instala la integración con `../integration/minuto29/Instalar.ps1` y reinicia la interfaz TikTok.
3. Abre **Minuto 29 → Magikarp**. Se abre automáticamente la ventana vertical.
4. Conecta el LIVE desde ese panel. Los espectadores escriben `!unir`; el anfitrión pulsa **Comenzar ronda**.
5. Para OBS usa una fuente navegador con `http://127.0.0.1:4390/`, ancho **1080**, alto **1920**, a 60 FPS. También puedes capturar la ventana del juego.
6. Al terminar se muestra el ganador. Pulsa **Nueva sala de inscripción** para recibir nuevos participantes.

La sala se sirve únicamente en localhost. Los controles del anfitrión están en `http://127.0.0.1:4390/control`. Desde allí puedes elegir de uno a doce jugadores de prueba y enviarles taps después de comenzar una ronda. Abre una sala nueva antes de jugar con personas reales.

## TikTok y pruebas

El proceso TikTok existente reenvía `CommentEvent` y `LikeEvent` con el identificador de usuario; utiliza `count`, no el total global de likes. No asigna taps de usuarios desconocidos o no inscritos. TikTok puede agrupar y retrasar estos eventos; la exactitud en un LIVE real depende de los eventos identificados que entregue el servicio. Si una foto no está disponible, se muestra la inicial del participante. No se usan regalos para generar puntos.

Las animaciones duran 1,1 segundos por salto (clips originales 8 → 10 → 14 → 5 → 6 a 30 FPS; impacto a los 10/30 segundos); los saltos recibidos se encolan por jugador. Solo cuentan los golpes que ocurren antes de acabar el tiempo. Los taps del lobby, la cuenta regresiva y el resultado se ignoran. El servidor lleva la puntuación, independientemente de cuántas ventanas o fuentes OBS estén abiertas.

Pruebas automáticas: `python -m unittest test_game.py`. Se verifican límite de doce, usuarios duplicados, cierre de inscripciones, acumulación individual, impactos, cola, corte de tiempo, ganador, empate y reinicio. Verificación local realizada: doce jugadores y puntuaciones de 1 a 12; pantalla final del ganador y renderizado WebGL sin errores. Falta la validación con participantes de un LIVE real.

## Música y efectos

La inscripción reproduce el archivo local `Menumusic.mp3` en bucle. Al comenzar la cuenta regresiva se detiene el menú; cuando Ditto muestra el **1** (últimos 0,9 segundos), comienza `Magikarps.mp3` y continúa durante la competencia sin reiniciarse al salir Ditto. La canción de partida se reproduce una sola vez. `audio_duration.py` lee los fotogramas MP3 y el recorte de codificación Xing/LAME: el archivo actual dura 34,156553 segundos y quedan 33,256553 segundos de juego después de la salida. El servidor relee la duración al comenzar cada ronda y sincroniza los reproductores con su reloj.

En los últimos 2,7 segundos se muestran las imágenes de Ditto en orden inverso **1 → 2 → 3**, con los efectos de aviso originales. Al finalizar el MP3 se congelan los puntos y suena el timbre original **0x20009**. La pantalla del ganador y su fanfarria (0x1A) aparecen después del timbre. Los controles ya no permiten elegir una duración manual. La cuenta, salto e impacto conservan los efectos originales 0x20001, 0x20006 y 0x20008. `python check_music_round.py` verifica la secuencia completa en una sala local con jugadores de prueba.

Ejecuta `Instalar-musica.ps1` para copiar `Menumusic.mp3` y `Magikarps.mp3` desde Descargas a `local-assets/`. Acepta `-MenuFile` y `-PlayingFile` para otras rutas. Los MP3 se guardan solo en el equipo y quedan ignorados por Git. Recarga la ventana del juego y la fuente OBS después de cambiar los archivos.

El control ♫ permite activar, silenciar y ajustar el volumen. Si el navegador impide el inicio automático, pulsa Activar música. En OBS activa **Controlar audio mediante OBS** en la fuente navegador y comprueba su mezclador. `node test_music.mjs` verifica el inicio en el 1, la continuidad de la canción al comenzar la partida y el cambio de ronda.

Para preparar el audio en una instalación nueva, ejecuta `Instalar-musica.ps1` y `Capturar-musica.ps1` antes de abrir la sala. Para regenerar los efectos, cierra el port y ejecuta `Capturar-musica.ps1`. Instala hooks opcionales, compila el port e inicia una instancia de captura. Durante la captura bloquea los sonidos de la demostración automática para evitar mezclarlos con las tomas; guarda las tres pistas y los cuatro efectos, incluido `buzzer.wav`, en `local-assets/`. Requiere el port ya configurado para compilar. Los hooks solo se activan cuando se define `STADIUMFEI_MUSIC_REQUEST`. No se suben la música ni los recursos del juego al repositorio.

El capturador conserva las antiguas pistas originales para archivo local, pero la sala usa únicamente los MP3 elegidos para inscripción y partida.
