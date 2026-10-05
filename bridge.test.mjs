import { test } from 'node:test';
import assert from 'node:assert/strict';
import net from 'node:net';
import readline from 'node:readline';
import { TapCounter, Controller } from './bridge.mjs';

test('acumula lotes: 9+1 y 25+5, conserva restos', () => {
  const counter = new TapCounter();
  assert.equal(counter.add(9), 0);
  assert.equal(counter.add(1), 1);
  assert.equal(counter.add(25), 2);
  assert.equal(counter.remainder, 5);
  assert.equal(counter.add(5), 1);
  for (const value of [-1, NaN, 1.5]) assert.throws(() => counter.add(value));
});
test('protocolo del port: ping, A abajo y A arriba', async () => {
  const commands = [];
  const server = net.createServer(socket => {
    const lines = readline.createInterface({ input: socket });
    lines.on('line', line => {
      commands.push(JSON.parse(line));
      socket.write('{"ok":true}\n');
    });
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const controller = new Controller(server.address().port);
  try {
    await controller.connect();
    await controller.press(30);
    assert.deepEqual(commands, [
      { cmd: 'ping' },
      { cmd: 'set_button', name: 'A', down: true },
      { cmd: 'set_button', name: 'A', down: false }
    ]);
  } finally {
    controller.close();
    await new Promise(resolve => server.close(resolve));
  }
});
