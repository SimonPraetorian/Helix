from .core import Helix
from .models import Observation

def main():
    h=Helix()
    prices=[100.0,100.5,100.2,100.9,100.7,101.4,101.0,101.8,101.6]
    print("HELIX 0.2 — PAPER LAB")
    print("Frozen loop: observe → model → hypothesis → prediction → act → outcome → compare → learn")
    for previous,a,b in [(prices[i-1],prices[i],prices[i+1]) for i in range(1,len(prices)-1)]:
        r=h.cycle(Observation("HELIX-SYN",a,previous),b)
        print(f"{r.decision_id[:8]}  {r.proposal['action']:8} conf={r.proposal['confidence']:.2f}  gate={r.execution['authorized']}  pnl={r.outcome['pnl_fraction']:.5f}  diverged={r.comparison['diverged']}")
    print("Ledger: runs/black_box.jsonl")

if __name__=="__main__": main()
