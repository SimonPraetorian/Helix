"""Observable, synthetic, paper-only behaviour run."""
import argparse
import time
from .core import Helix
from .models import Observation

SCENARIOS = [
    ("rising", 100.0, 101.0, 102.0),
    ("reversal", 101.0, 102.0, 100.0),
    ("flat", 100.0, 100.0, 100.0),
    ("falling", 100.0, 99.0, 98.0),
    ("invalid proposal", 99.0, 98.0, 97.0),
]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", default="runs/watch.jsonl")
    parser.add_argument("--delay", type=float, default=0.7)
    args = parser.parse_args()
    if args.delay < 0: parser.error("delay must be nonnegative")
    helix = Helix(args.ledger)
    print("HELIX 0.2 | SYNTHETIC PAPER RUN | no network or orders", flush=True)
    print("scenario         action    confidence  proposed  allowed  sentinel  gate  prediction  memory", flush=True)
    for label, previous, price, next_price in SCENARIOS:
        original = helix.desk.propose
        if label == "invalid proposal":
            def faulty(obs, memory, kelly):
                proposal = original(obs, memory, kelly)
                proposal.proposed_fraction = -0.25
                return proposal
            helix.desk.propose = faulty
        try:
            record = helix.cycle(Observation("HELIX-SYN", price, previous), next_price)
        finally:
            helix.desk.propose = original
        p, s, r = record.proposal, record.sentinel, record.risk
        prediction = "diverged" if record.comparison["diverged"] else "matched/flat"
        print(f"{label:16} {p['action'].value:8} {p['confidence']:10.2f} {p['proposed_fraction']:9.3f} {r['fraction']:8.3f} {str(s['approved']):8} {str(record.execution['authorized']):5} {prediction:12} {record.learning['updated']}", flush=True)
        if not s['approved']: print("  Sentinel:", "; ".join(s['reasons']), flush=True)
        if args.delay: time.sleep(args.delay)
    print(f"Ledger: {args.ledger} | memory promotions: {len(helix.memory.validated)}", flush=True)

if __name__ == "__main__": main()
