"""Offline, localhost-only visual observer for Helix's synthetic paper laboratory."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock, Thread
import json, math, random, time
from .core import Helix
from .models import Observation

HTML = Path(__file__).with_name('floor.html').read_bytes()
SCENE = Path(__file__).with_name('floor-scene.jpg').read_bytes()

class Lab:
    def __init__(self):
        self.lock = Lock()
        self.reset()

    def reset(self):
        with getattr(self, 'lock', Lock()):
            self.running = False
            self.generation = getattr(self, 'generation', 0) + 1
            self.rng = random.Random(2048)
            self.prices = [100.0, 100.0]
            self.step = 0
            self.speed = 1.0
            self.helix = Helix('runs/floor.jsonl')
            self.events = [{'id': 0, 'kind': 'system', 'actor': 'FLOOR', 'target': '', 'message': 'Synthetic tape ready. Press RUN to start.', 'detail': ''}]
            self.history = [100.0]
            self.stats = {'decisions': 0, 'approved': 0, 'blocked': 0, 'correct': 0, 'wrong': 0, 'paper_pnl_pct': 0.0}
            self.agents = {name: {'status': 'Waiting', 'last': '—'} for name in ['TAPE', 'DESK', 'SHADOW', 'SENTINEL', 'KELLY', 'MEMORY']}

    def add(self, kind, actor, target, message, detail=''):
        self.events.append({'id': self.step * 10 + len(self.events), 'kind': kind, 'actor': actor, 'target': target, 'message': message, 'detail': detail})
        self.events = self.events[-60:]

    def tick(self):
        with self.lock:
            if not self.running: return
            self.step += 1
            previous, price = self.prices[-2:]
            change = self.rng.choice([-1, -0.7, -0.4, 0, 0.4, 0.7, 1]) / 100
            next_price = round(price * (1 + change), 4)
            if self.step % 13 == 0: next_price = round(price * 0.982, 4)
            if next_price <= 0: return
            self.agents['TAPE'] = {'status': 'Broadcasting', 'last': f'{price:.2f} → {next_price:.2f}'}
            self.add('tape', 'TAPE', 'DESK', f'New print {next_price:.2f}', f'Synthetic change {change:+.2%}')
            self.agents['SHADOW'] = {'status': 'Observing', 'last': 'Reversal watch' if (next_price-price)*(price-previous)<0 else 'Momentum watch'}
            self.add('shadow', 'SHADOW', 'DESK', self.agents['SHADOW']['last'], 'Advisory only; no veto power')
            original = self.helix.desk.propose
            if self.step % 11 == 0:
                def faulty(obs, memory, kelly):
                    proposal = original(obs, memory, kelly)
                    if proposal.action.value in ('BUY','SELL'): proposal.proposed_fraction = -0.25
                    return proposal
                self.helix.desk.propose = faulty
            try:
                record = self.helix.cycle(Observation('HELIX-SYN', price, previous), next_price)
            finally:
                self.helix.desk.propose = original
            p, s, r = record.proposal, record.sentinel, record.risk
            action = p['action'].value
            self.agents['DESK'] = {'status': 'Proposing', 'last': f'{action} • {p["confidence"]:.0%}'}
            self.agents['KELLY'] = {'status': 'Sizing', 'last': f'{r["fraction"]:.1%} allowed'}
            self.add('proposal', 'DESK', 'SENTINEL', f'{action} at {p["confidence"]:.0%} confidence', f'Requested size {p["proposed_fraction"]:.1%}')
            self.add('risk', 'KELLY', 'SENTINEL', f'Allowed size {r["fraction"]:.1%}', '; '.join(r['reasons']))
            allowed = record.execution['authorized']
            self.agents['SENTINEL'] = {'status': 'Cleared' if allowed else 'Blocked', 'last': '; '.join(s['reasons'])}
            self.add('clear' if allowed else 'block', 'SENTINEL', 'DESK', 'Paper gate cleared' if allowed else 'Proposal blocked', '; '.join(s['reasons']))
            self.stats['decisions'] += 1
            self.stats['approved' if allowed else 'blocked'] += 1
            if allowed and action in ('BUY','SELL'):
                self.stats['correct' if record.outcome['correct_direction'] else 'wrong'] += 1
                self.stats['paper_pnl_pct'] += record.outcome['pnl_fraction'] * 100
                label = 'Hit' if record.outcome['correct_direction'] else 'Miss'
                self.add('outcome', 'TAPE', 'MEMORY', f'{label} • paper P/L {record.outcome["pnl_fraction"]:+.3%}', f'Price {price:.2f} → {next_price:.2f}')
            if record.outcome['correct_direction'] is not None:
                self.add('memory', 'MEMORY', 'DESK', 'Outcome retained', 'No promotion without independent validation')
            self.agents['MEMORY'] = {'status': 'Holding evidence', 'last': f'{len(self.helix.vault.evidence)} observed • 0 validated'}
            self.prices.append(next_price)
            self.history.append(next_price)
            self.history = self.history[-42:]
            if self.step >= 60:
                self.running = False
                self.add('system', 'FLOOR', '', '60-step run complete. Reset to repeat.', '')

    def snapshot(self):
        with self.lock:
            return {'running': self.running, 'step': self.step, 'price': self.prices[-1], 'history': self.history[:], 'stats': self.stats.copy(), 'agents': self.agents.copy(), 'events': self.events[-22:], 'speed': self.speed}

lab = Lab()

def loop():
    while True:
        lab.tick()
        time.sleep(max(0.15, lab.speed))

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def reply(self, status, data, mime):
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def do_GET(self):
        if self.path == '/': self.reply(200, HTML, 'text/html; charset=utf-8')
        elif self.path == '/scene': self.reply(200, SCENE, 'image/jpeg')
        elif self.path == '/api/state': self.reply(200, json.dumps(lab.snapshot()).encode(), 'application/json')
        else: self.reply(404, b'Not found', 'text/plain')
    def do_POST(self):
        if self.path != '/api/control': return self.reply(404, b'Not found', 'text/plain')
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length > 256: raise ValueError('body too large')
            data = json.loads(self.rfile.read(length))
            action = data.get('action')
            if action == 'reset': lab.reset()
            elif action in ('run', 'pause'):
                with lab.lock: lab.running = action == 'run' and lab.step < 60
            elif action == 'speed' and data.get('value') in (0.3, 1, 2):
                with lab.lock: lab.speed = data['value']
            else: raise ValueError('unknown control')
            self.reply(200, json.dumps(lab.snapshot()).encode(), 'application/json')
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self.reply(400, str(exc).encode(), 'text/plain')

def main():
    Thread(target=loop, daemon=True).start()
    server = ThreadingHTTPServer(('127.0.0.1', 8765), Handler)
    print('HELIX FLOOR • synthetic paper lab • offline localhost only', flush=True)
    print('Open http://127.0.0.1:8765 in your phone browser. Ctrl+C stops it.', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__ == '__main__': main()
