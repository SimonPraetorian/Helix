from dataclasses import asdict
import math
from pathlib import Path
import json, time
from .models import *

class BlackBox:
    def __init__(self, path="runs/black_box.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
    def record(self, event, payload):
        row = {"ts": time.time(), "event": event, "payload": payload}
        def clean(value):
            if isinstance(value, float) and not math.isfinite(value): return str(value)
            if isinstance(value, dict): return {key: clean(item) for key, item in value.items()}
            if isinstance(value, (list, tuple)): return [clean(item) for item in value]
            return value
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(clean(row), sort_keys=True, allow_nan=False) + "\n")

class Vault:
    """Bounded append-only evidence store for the POC."""
    def __init__(self): self.evidence = []
    def store(self, item): self.evidence.append(item)

class Memory:
    def __init__(self): self.validated = []
    def promote(self, statement, evidence, confidence):
        # A single correct synthetic prediction is an observation, not validation.
        raise RuntimeError("memory promotion requires an independent validation protocol")

class Kelly:
    def size(self, edge, win_prob, payoff=1.0, cap=0.10):
        # Bounded Kelly fraction. Invalid inputs become zero rather than guessing.
        if payoff <= 0 or not 0 < win_prob < 1: return 0.0
        f = (win_prob * payoff - (1-win_prob)) / payoff
        return max(0.0, min(cap, f * 0.25))  # quarter-Kelly for the laboratory

class SecuritySentinel:
    """Mechanical veto: action type, exposure and input integrity. No intent verdicts."""
    def check(self, proposal: Proposal) -> SentinelResult:
        reasons=[]; ok=True
        if not isinstance(proposal, Proposal):
            return SentinelResult(False,["malformed proposal"],False)
        if not isinstance(proposal.action, Action):
            return SentinelResult(False,["unknown action"],False)
        if not isinstance(proposal.symbol, str) or not proposal.symbol.strip():
            ok=False; reasons.append("missing symbol")
        if not isinstance(proposal.proposed_fraction, (int, float)) or not math.isfinite(proposal.proposed_fraction):
            return SentinelResult(False,["invalid proposed size"],False)
        if proposal.action in (Action.BUY, Action.SELL) and proposal.proposed_fraction <= 0:
            ok=False; reasons.append("trade proposal has non-positive size")
        if proposal.action in (Action.BUY, Action.SELL) and proposal.proposed_fraction > RiskEngine.MAX_FRACTION:
            ok=False; reasons.append("trade proposal exceeds position cap")
        if not reasons: reasons.append("security checks passed")
        return SentinelResult(ok, reasons, ok, security_ok=ok)

class LogicReview:
    """Evidence/consistency review. Cannot grant security clearance or assign strikes."""
    def check(self, proposal: Proposal) -> SentinelResult:
        if not isinstance(proposal, Proposal):
            return SentinelResult(False,["malformed proposal"],False)
        reasons=[]
        if not isinstance(proposal.hypothesis, Hypothesis) or not proposal.hypothesis.evidence:
            reasons.append("missing hypothesis evidence")
        if not isinstance(proposal.confidence, (int, float)) or not math.isfinite(proposal.confidence) or not 0 <= proposal.confidence <= 1:
            reasons.append("confidence outside [0,1]")
        if proposal.action == Action.ABSTAIN:
            reasons.append("abstention is explicitly permitted")
        ok = not any(reason != "abstention is explicitly permitted" for reason in reasons)
        if not reasons: reasons.append("logic checks passed")
        return SentinelResult(ok, reasons, ok, logic_ok=ok)

class Sentinel:
    """Combines separate reviews with AND; neither reviewer can override the other."""
    def __init__(self):
        self.security=SecuritySentinel()
        self.logic=LogicReview()
    def check(self, proposal: Proposal) -> SentinelResult:
        security=self.security.check(proposal)
        logic=self.logic.check(proposal)
        approved=security.approved and logic.approved
        return SentinelResult(approved,
            ["security: " + r for r in security.reasons] + ["logic: " + r for r in logic.reasons],
            approved, security_ok=security.approved, logic_ok=logic.approved)

class RiskEngine:
    MAX_FRACTION=0.10
    def check(self, proposal: Proposal, kelly_fraction: float) -> RiskResult:
        if not isinstance(proposal.proposed_fraction, (int, float)) or not math.isfinite(proposal.proposed_fraction) or proposal.proposed_fraction < 0:
            return RiskResult(False,0.0,["invalid proposed size"])
        f=min(proposal.proposed_fraction,max(kelly_fraction,0.0),self.MAX_FRACTION)
        if proposal.action in (Action.HOLD, Action.ABSTAIN):
            return RiskResult(True,0.0,["no position opened"])
        if f <= 0: return RiskResult(False,0.0,["risk model produced zero allowable size"])
        return RiskResult(True,f,["within laboratory position cap"])

class ExecutionGate:
    PAPER_ONLY=True
    def authorize(self, sentinel: SentinelResult, risk: RiskResult):
        if not self.PAPER_ONLY: return False,"live execution path is forbidden in 0.2"
        if not sentinel.approved: return False,"Sentinel rejected proposal"
        if not risk.approved: return False,"Risk engine rejected proposal"
        return True,"paper execution authorized"

class Desk:
    def propose(self, obs: Observation, memory: Memory, kelly: Kelly):
        direction=1 if obs.return_pct>0 else -1 if obs.return_pct<0 else 0
        confidence=min(0.95, 0.50 + min(abs(obs.return_pct)*20,0.40))
        action=Action.BUY if direction>0 else Action.SELL if direction<0 else Action.ABSTAIN
        hyp=Hypothesis(
            statement=f"Short-horizon momentum continues for {obs.symbol}",
            predicted_direction=direction,
            confidence=confidence,
            evidence=[f"one-step return={obs.return_pct:.4%}"])
        edge=max(0.0,(confidence-0.5)*2)
        fraction=kelly.size(edge, confidence)
        return Proposal(str(__import__('uuid').uuid4()),action,obs.symbol,
                        "bounded one-step momentum hypothesis",confidence,fraction,hyp)

class Helix:
    def __init__(self, ledger_path="runs/black_box.jsonl"):
        self.black_box=BlackBox(ledger_path); self.vault=Vault(); self.memory=Memory()
        self.kelly=Kelly(); self.sentinel=Sentinel(); self.risk=RiskEngine(); self.gate=ExecutionGate(); self.desk=Desk()

    def cycle(self, obs: Observation, next_price: float):
        if not all(math.isfinite(x) and x > 0 for x in (obs.price,obs.previous_price,next_price)):
            raise ValueError("prices must be finite and positive")
        proposal=self.desk.propose(obs,self.memory,self.kelly)
        sent=self.sentinel.check(proposal)
        risk=self.risk.check(proposal,self.kelly.size(max(0,(proposal.confidence-.5)*2),proposal.confidence))
        authorized, gate_reason=self.gate.authorize(sent,risk)
        direction=1 if next_price>obs.price else -1 if next_price<obs.price else 0
        pnl=0.0
        if authorized and proposal.action==Action.BUY: pnl=(next_price/obs.price-1)*risk.fraction
        elif authorized and proposal.action==Action.SELL: pnl=(obs.price/next_price-1)*risk.fraction if next_price else 0
        outcome=Outcome(proposal.decision_id,obs.price,next_price,pnl,
                        None if proposal.action==Action.ABSTAIN else direction==proposal.hypothesis.predicted_direction)
        comparison={"predicted_direction":proposal.hypothesis.predicted_direction,"actual_direction":direction,
                     "diverged": proposal.action!=Action.ABSTAIN and direction!=proposal.hypothesis.predicted_direction}
        learning={"updated":False,"rule":"observations are retained; independent validation required for promotion"}
        if authorized and outcome.correct_direction is not None:
            self.vault.store({"decision_id":proposal.decision_id,"outcome":asdict(outcome)})
        record=DecisionRecord(proposal.decision_id,asdict(obs),asdict(proposal.hypothesis),asdict(proposal),asdict(sent),asdict(risk),
                              {"authorized":authorized,"reason":gate_reason},asdict(outcome),comparison,learning)
        self.black_box.record("DECISION",asdict(record))
        return record
