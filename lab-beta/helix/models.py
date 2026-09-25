from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import time, uuid

class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    ABSTAIN = "ABSTAIN"

@dataclass(frozen=True)
class Observation:
    symbol: str
    price: float
    previous_price: float
    timestamp: float = field(default_factory=time.time)

    @property
    def return_pct(self) -> float:
        return (self.price / self.previous_price - 1.0) if self.previous_price else 0.0

@dataclass
class Hypothesis:
    statement: str
    predicted_direction: int  # -1 down, 0 flat, +1 up
    confidence: float
    evidence: List[str]

@dataclass
class Proposal:
    decision_id: str
    action: Action
    symbol: str
    rationale: str
    confidence: float
    proposed_fraction: float
    hypothesis: Hypothesis

@dataclass
class SentinelResult:
    approved: bool
    reasons: List[str]
    constitutional_ok: bool
    security_ok: bool = False
    logic_ok: bool = False

@dataclass
class RiskResult:
    approved: bool
    fraction: float
    reasons: List[str]

@dataclass
class Outcome:
    decision_id: str
    entry_price: float
    exit_price: float
    pnl_fraction: float
    correct_direction: Optional[bool]

@dataclass
class DecisionRecord:
    decision_id: str
    observation: Dict[str, Any]
    hypothesis: Dict[str, Any]
    proposal: Dict[str, Any]
    sentinel: Dict[str, Any]
    risk: Dict[str, Any]
    execution: Dict[str, Any]
    outcome: Optional[Dict[str, Any]] = None
    comparison: Optional[Dict[str, Any]] = None
    learning: Optional[Dict[str, Any]] = None
