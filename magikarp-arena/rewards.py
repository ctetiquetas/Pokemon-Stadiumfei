"""Atomic, replay-safe Minuto 29 payouts. Demo rounds never call this ledger."""
import json
import sys
import uuid
from pathlib import Path

BRIDGE = Path.home() / 'Documents/GitHub/Shipwright/tools/tiktok-live-bridge'
sys.path.insert(0, str(BRIDGE))
from shared_wallet import Wallet, wallet_path, user_key
from movement_history import describe

def request(wallet, payload):
    game = payload['game']
    if game not in ('magikarp', 'swimming'): raise ValueError('Juego inválido')
    with wallet.transaction() as db:
        db.execute('CREATE TABLE IF NOT EXISTS minuto29_pots (game TEXT PRIMARY KEY, carry INTEGER NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS minuto29_rounds (id TEXT PRIMARY KEY, game TEXT, roster TEXT, result TEXT)')
        db.execute('INSERT OR IGNORE INTO minuto29_pots VALUES (?,0)', (game,))
        carry = db.execute('SELECT carry FROM minuto29_pots WHERE game=?', (game,)).fetchone()[0]
        action = payload['action']
        if action == 'status': return dict(carry=carry, base=45)
        if action == 'begin':
            roster = list(dict.fromkeys(user_key(u) for u in payload['roster']))
            if not 1 <= len(roster) <= 16: raise ValueError('Participantes inválidos')
            rid = str(uuid.uuid4())
            db.execute('INSERT INTO minuto29_rounds VALUES (?,?,?,NULL)', (rid,game,json.dumps(roster)))
            return dict(round=rid, carry=carry)
        if action != 'finish': raise ValueError('Acción inválida')
        row = db.execute('SELECT game,roster,result FROM minuto29_rounds WHERE id=?', (payload['round'],)).fetchone()
        if not row or row[0] != game: raise ValueError('Ronda inválida')
        if row[2]: return json.loads(row[2])
        winners = list(dict.fromkeys(user_key(u) for u in payload['winners']))
        if not winners or not set(winners).issubset(json.loads(row[1])): raise ValueError('Ganadores inválidos')
        # Swimming pays 45 to each champion; Magikarp shares its 45 on a tie.
        total = (45 * len(winners) if game == 'swimming' else 45) + carry
        quotient, remainder = divmod(total, len(winners))
        paid, unpaid = {}, {}
        for i, user in enumerate(winners):
            amount = quotient + (i < remainder)
            if db.execute('SELECT 1 FROM balances WHERE user=?', (user,)).fetchone():
                db.execute('UPDATE balances SET balance=balance+? WHERE user=?', (amount,user))
                describe(db,user,f'Ganó {game} · ronda {payload["round"]}')
                paid[user] = amount
            else: unpaid[user] = amount
        result = dict(paid=paid, unpaid=unpaid, carry=sum(unpaid.values()))
        db.execute('UPDATE minuto29_pots SET carry=? WHERE game=?', (result['carry'],game))
        db.execute('UPDATE minuto29_rounds SET result=? WHERE id=?', (json.dumps(result),payload['round']))
        return result

if __name__ == '__main__':
    try:
        if not wallet_path().is_file(): raise ValueError('No se encontró la cartera compartida')
        print(json.dumps(request(Wallet(),json.load(sys.stdin))))
    except Exception as exc:
        print(json.dumps(dict(error=str(exc)))); sys.exit(1)
