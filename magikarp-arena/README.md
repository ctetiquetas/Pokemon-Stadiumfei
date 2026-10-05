# Magikarp · Minuto 29

Sala vertical 9:16 para TikTok LIVE y OBS. Hasta 12 espectadores escriben `!unir` para entrar. Cada participante conserva sus propios taps, nombre, foto y color; cada 10 taps identificados del jugador generan un salto. El marcador suma +1 cuando el salto golpea el botón. La ronda tiene cuenta regresiva, duración ajustable de 10 a 300 segundos y pantalla final del ganador. Los empates muestran a los participantes empatados.

## Gráficos originales

Se reutilizan las mallas y las texturas originales del minijuego de Pokémon Stadium, junto con las animaciones de reposo, salto y victoria. El port y su descompilación sirvieron para identificar el formato y los recursos. Las reglas, la sala, la interfaz vertical y el vínculo con TikTok son nuevos para admitir doce jugadores.

`export_models.py` lee la ROM local US 1.0 en formato z64, verifica su MD5, descomprime los recursos PERS-SZP/Yay0 y recorre la geometría y las listas F3DEX2. Los modelos del Magikarp y del botón son las entradas 172 y 173 del archivo de recursos en 0x920000. El código sigue los formatos documentados por `geo_layout.c`, `12D80.c`, `17300.c`, `3FB0.h` y `gbi.h` de la descompilación del port. Se conservan los vértices compartidos por articulaciones y las texturas RGBA16/IA16/I8.

**La ROM y los recursos extraídos no se distribuyen.** `local-assets/` y `node_modules/` están ignorados por Git. Los gráficos se regeneran desde la ROM del usuario con `Preparar.ps1`. El resto de la sala puede subirse al repositorio.

## Uso

1. Ejecuta `Preparar.ps1` si es una instalación nueva. Requiere Python 3, Node/npm y tu ROM local.
2. Instala la integración con `../integration/minuto29/Instalar.ps1` y reinicia la interfaz TikTok.
3. Abre **Minuto 29 → Magikarp**. Se abre automáticamente la ventana vertical.
4. Conecta el LIVE desde ese panel. Los espectadores escriben `!unir`; el anfitrión pulsa **Comenzar ronda**.
5. Para OBS usa una fuente navegador con `http://127.0.0.1:4390/`, ancho **1080**, alto **1920**, a 60 FPS. También puedes capturar la ventana del juego.
6. Al terminar se muestra el ganador. Pulsa **Nueva sala de inscripción** para recibir nuevos participantes.

La sala se sirve únicamente en localhost. Los controles del anfitrión están en `http://127.0.0.1:4390/control`. Desde allí puedes cargar doce jugadores de prueba y enviarles taps después de comenzar una ronda. Abre una sala nueva antes de jugar con personas reales.

## TikTok y pruebas

El proceso TikTok existente reenvía `CommentEvent` y `LikeEvent` con el identificador de usuario; utiliza `count`, no el total global de likes. No asigna taps de usuarios desconocidos o no inscritos. TikTok puede agrupar y retrasar estos eventos; la exactitud en un LIVE real depende de los eventos identificados que entregue el servicio. Si una foto no está disponible, se muestra la inicial del participante. No se usan regalos para generar puntos.

Las animaciones duran 1,1 segundos por salto (clips originales 8 → 10 → 14 → 5 → 6 a 30 FPS; impacto a los 10/30 segundos); los saltos recibidos se encolan por jugador. Solo cuentan los golpes que ocurren antes de acabar el tiempo. Los taps del lobby, la cuenta regresiva y el resultado se ignoran. El servidor lleva la puntuación, independientemente de cuántas ventanas o fuentes OBS estén abiertas.

Pruebas automáticas: `python -m unittest test_game.py`. Se verifican límite de doce, usuarios duplicados, cierre de inscripciones, acumulación individual, impactos, cola, corte de tiempo, ganador, empate y reinicio. Verificación local realizada: doce jugadores y puntuaciones de 1 a 12; pantalla final del ganador y renderizado WebGL sin errores. Falta la validación con participantes de un LIVE real.

## Música original

La inscripción y la cuenta regresiva reproducen la pista de selección de minijuegos (0x16), la partida la de Magikarp (10), y el ganador la fanfarria de victoria (0x1A). Las pistas WAV se generan localmente con el propio motor de audio del port. El navegador cambia de música automáticamente, repite las pistas de sala y partida, y reproduce la victoria una vez por resultado. El control ♫ permite activar, silenciar y ajustar el volumen. Si el navegador impide el inicio automático, pulsa Activar música. En OBS activa **Controlar audio mediante OBS** en la fuente navegador y comprueba su mezclador.

Para regenerar la música, cierra el port y ejecuta `Capturar-musica.ps1`. Instala un hook opcional y compila el port, inicia una instancia de captura y guarda solo las tres pistas en `local-assets/`. Requiere el port ya configurado para compilar. El hook no cambia el juego normal: solo se activa cuando se define `STADIUMFEI_MUSIC_REQUEST`. No se suben la música ni los recursos del juego al repositorio.

La pista de inscripción se verificó en `fragment39_27BCC0.c`: `func_825046AC` carga `kids_club_select_ui` y ejecuta `func_82504370`, que inicia explícitamente la música `0x16`. El capturador comprueba cada segundo el identificador de música activo y descarta la toma si el arranque del port lo cambia.
