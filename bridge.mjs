import net from 'node:net';
import readline from 'node:readline';
import { pathToFileURL } from 'node:url';

export class TapCounter {
  remainder = 0;
  add(count) {
    if (!Number.isSafeInteger(count) || count < 0) throw new Error('Cantidad de taps inválida');
    const total = this.remainder + count;
    if (!Number.isSafeInteger(total)) throw new Error('Cantidad demasiado grande');
    const presses = Math.floor(total / 10);
    this.remainder = total % 10;
    return presses;
  }
}

export class Controller {
  constructor(port = 4371) { this.port = port; }
  async connect() {
    this.socket = net.createConnection({ host: '127.0.0.1', port: this.port });
    await new Promise((resolve, reject) => {
      this.socket.once('connect', resolve);
      this.socket.once('error', reject);
    });
    this.lines = readline.createInterface({ input: this.socket })[Symbol.asyncIterator]();
    this.socket.on('error', () => {});
    this.socket.setTimeout(3000, () => this.socket.destroy(new Error('El port no respondió')));
    await this.command({ cmd: 'ping' });
  }
  async command(value) {
    this.socket.write(JSON.stringify(value) + '\n');
    const line = await this.lines.next();
    if (line.done) throw new Error('Conexión al port cerrada');
    const response = JSON.parse(line.value);
    if (!response.ok) throw new Error(response.error || 'Comando rechazado');
    return response;
  }
  async press(holdMs) {
    try {
      await this.command({ cmd: 'set_button', name: 'A', down: true });
      await sleep(holdMs);
    } finally {
      await this.command({ cmd: 'set_button', name: 'A', down: false });
    }
  }
  close() { this.socket?.destroy(); }
}
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function main() {
  const args = process.argv.slice(2);
  const option = (name, fallback) => {
    const index = args.indexOf(name);
    return index < 0 ? fallback : args[index + 1];
  };
  const dry = args.includes('--dry-run');
  const user = option('--live', null);
  const interval = Number(option('--interval-ms', '700'));
  const hold = Number(option('--hold-ms', '100'));
  const port = Number(option('--port', '4371'));
  if (![interval, hold, port].every(Number.isSafeInteger) || hold < 30 || interval < hold + 30 || port < 1 || port > 65535) {
    throw new Error('Puerto o tiempos inválidos; intervalo debe superar la pulsación en al menos 30 ms');
  }
  const controller = dry ? null : new Controller(port);
  const counter = new TapCounter();
  let pending = 0, running = false, stopped = false;
  async function drain() {
    if (running) return;
    running = true;
    try {
      while (pending && !stopped) {
        pending--;
        if (controller) await controller.press(hold);
        console.log(`A enviada | pendientes: ${pending}`);
        await sleep(controller ? interval - hold : interval);
      }
    } catch (error) {
      stopped = true;
      pending = 0;
      controller?.close();
      console.error(`Puente detenido: ${error.message}. Reinicia para reconectar.`);
      process.exitCode = 1;
      input?.close();
      live?.disconnect();
    } finally { running = false; }
  }
  function add(count) {
    if (stopped) return;
    const presses = counter.add(count);
    pending += presses;
    console.log(`+${count} taps | resto: ${counter.remainder}/10 | cola: ${pending}`);
    void drain();
  }
  let input, live;
  try {
    await controller?.connect();
    console.log(dry ? 'Simulación: no controla el juego.' : 'Conectado al port. Abre Magikarp con jugador 1 antes de enviar taps.');
    process.once('SIGINT', () => { stopped = true; pending = 0; input?.close(); live?.disconnect(); });
    if (user) {
      const { TikTokLiveConnection, WebcastEvent } = await import('tiktok-live-connector');
      live = new TikTokLiveConnection(user.replace(/^@/, ''));
      live.on(WebcastEvent.LIKE, event => {
        try { add(Number(event.likeCount)); }
        catch (error) { console.error(error.message); }
      });
      live.on('disconnected', () => { stopped = true; pending = 0; });
      live.on('error', error => { console.error('TikTok:', error.message || error); stopped = true; pending = 0; });
      await live.connect();
      console.log(`LIVE conectado: @${user.replace(/^@/, '')}`);
      while (!stopped) await sleep(100);
    } else {
      input = readline.createInterface({ input: process.stdin, output: process.stdout });
      console.log('Escribe una cantidad de taps y Enter. "reset" borra cola/resto; "q" sale.');
      for await (const line of input) {
        if (line.trim() === 'q') { stopped = true; pending = 0; break; }
        if (line.trim() === 'reset') { pending = 0; counter.remainder = 0; console.log('Cola y resto borrados'); continue; }
        try { add(Number(line.trim())); } catch (error) { console.error(error.message); }
      }
    }
    while (running) await sleep(50);
  } finally {
    stopped = true;
    if (controller?.socket && !controller.socket.destroyed) {
      try { await controller.command({ cmd: 'set_button', name: 'A', down: false }); } catch {}
    }
    controller?.close();
    input?.close();
  }
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(error => { console.error(error.message); process.exitCode = 1; });
}
