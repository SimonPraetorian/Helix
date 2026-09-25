"""Reproducible, bounded fault and behavior checks for the synthetic lab."""
import argparse
import hashlib
import json
from pathlib import Path

from .core import Helix
from .models import Action, Observation

CASES = (
    ("momentum", 100, 101, 102, None),
    ("reversal", 100, 101, 99, None),
    ("flat_abstention", 100, 100, 100, None),
    ("invalid_negative_size", 100, 101, 102, -0.25),
    ("oversize_proposal", 100, 101, 102, 0.50),
)


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    ledger = output / "decisions.jsonl"
    ledger.unlink(missing_ok=True)
    helix = Helix(ledger)
    cases = []
    for name, previous, price, future, injected_size in CASES:
        original = helix.desk.propose
        if injected_size is not None:
            def faulty(obs, memory, kelly, size=injected_size):
                proposal = original(obs, memory, kelly)
                proposal.proposed_fraction = size
                return proposal
            helix.desk.propose = faulty
        try:
            record = helix.cycle(Observation("HELIX-SYN", price, previous, timestamp=0), future)
        finally:
            helix.desk.propose = original
        cases.append({
            "case": name, "action": record.proposal["action"].value,
            "sentinel_approved": record.sentinel["approved"],
            "gate_authorized": record.execution["authorized"],
            "paper_pnl_fraction": record.outcome["pnl_fraction"],
            "memory_promoted": record.learning["updated"],
            "reasons": record.sentinel["reasons"],
        })
    rows = [json.loads(line) for line in ledger.read_text().splitlines()]
    assertions = {
        "one_record_per_case": len(rows) == len(CASES),
        "flat_abstains": cases[2]["action"] == Action.ABSTAIN.value and cases[2]["paper_pnl_fraction"] == 0,
        "negative_size_blocked": not cases[3]["gate_authorized"] and not cases[3]["sentinel_approved"],
        "oversize_blocked": not cases[4]["gate_authorized"] and not cases[4]["sentinel_approved"],
        "no_unvalidated_promotion": not helix.memory.validated and all(not c["memory_promoted"] for c in cases),
        "all_ledger_decisions_have_outcomes": all(r.get("event") == "DECISION" and r["payload"].get("outcome") for r in rows),
    }
    report = {
        "kind": "synthetic_behavior_check", "status": "PASS" if all(assertions.values()) else "FAIL",
        "cases": cases, "assertions": assertions,
        "ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
        "limitations": ["Fixed synthetic prices only", "No autonomous agents or learned policy", "No real market performance evidence", "Local append-only log is not tamper-proof", "Future price is supplied by the scenario harness for scoring"],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="runs/beta-check")
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps({"status": result["status"], "assertions": result["assertions"], "report": str(Path(args.output) / "report.json")}, indent=2))
    if result["status"] != "PASS": raise SystemExit(1)


if __name__ == "__main__": main()
