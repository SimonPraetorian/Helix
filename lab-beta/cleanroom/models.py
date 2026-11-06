from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    agent_id: str
    action: str
    target: str
    payload: dict[str, Any]
    declared_effect: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Observation:
    proposal_id: str
    observed_action: str
    observed_target: str
    observed_effect: dict[str, Any]
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Review:
    reviewer: str
    approved: bool
    reasons: tuple[str, ...]
    quarantine_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
