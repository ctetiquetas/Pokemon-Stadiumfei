# Pokémon Stadiumfei: Magikarp interactivo

Primera versión del puente: **10 taps/likes recibidos = una pulsación de A para el jugador 1**. Se suman los taps de toda la audiencia. Los restos se conservan: 9 + 1 produce una pulsación; 25 produce dos y deja 5.

## Prueba

Necesitas Node.js 22 o posterior y un ejecutable de PokemonStadiumRecomp con el servidor TCP del código local (127.0.0.1:4371). El puente no incluye el port ni la ROM.

1. Abre el port, asigna teclado o mando al jugador 1 y entra manualmente a Magikarp's Splash. Inicia la ronda.
2. En esta carpeta ejecuta `node bridge.mjs`.
3. Escribe `10` y Enter para enviar una pulsación; prueba también `9` y después `1`.
4. `reset` descarta los taps y pulsaciones pendientes entre rondas. `q` o Ctrl+C detiene el puente. Una pulsación que ya comenzó termina antes de salir.

Sin el juego puedes probar el contador con `node bridge.mjs --dry-run`. Las pruebas automáticas se ejecutan con `node --test`.

## TikTok LIVE

Ejecuta `npm install` y luego `node bridge.mjs --live TU_USUARIO`. Debes estar en directo y dentro de la ronda antes de conectar. Se utiliza `likeCount` de cada evento, no el total acumulado del directo. El conector es no oficial: https://github.com/zerodytrash/TikTok-Live-Connector.

Los regalos todavía no tienen una regla asignada y no generan pulsaciones.

## Ajuste pendiente en el juego

Por defecto A se mantiene 100 ms y cada pulsación empieza cada 700 ms. Prueba `node bridge.mjs --interval-ms 1000 --hold-ms 100` si el juego ignora saltos. El intervalo necesita calibración jugando: una pulsación enviada no garantiza un salto ni un punto. El juego original determina la puntuación.

Esta versión no detecta inicio/fin de ronda ni aterrizaje: detén el puente al terminar una ronda y usa reset antes de empezar otra. No permite extraer el minijuego ni arrancarlo automáticamente. Ante una desconexión descarta la cola; reinicia el puente para reconectar.

## Estado de validación

Contador y protocolo TCP cubiertos por pruebas con servidor simulado. La prueba visual con Magikarp y la conexión a un LIVE real todavía están pendientes. El port local ya se compiló y arrancó; el usuario pudo jugar Magikarp. La prueba TCP real confirmó una pulsación A por 9 + 1 taps. Falta verificar los puntos usando el puente dentro de una ronda.

Los recursos originales del juego se mantienen fuera del repositorio. El proyecto conserva este puente separado del código GPL del port.


## Sala Magikarp de 12 jugadores

La opción **Minuto 29 → Magikarp** abre ahora una sala vertical 9:16 con gráficos originales, `!unir`, taps individuales, doce colores y pantalla del ganador. Consulta [las instrucciones de la sala](magikarp-arena/README.md) y [la integración](integration/minuto29/README.md).
