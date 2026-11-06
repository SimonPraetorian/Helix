"""Clean Room supervisor: dual review, observation reconciliation and quarantine.

This is a contained testbed, not a hardened hostile-code sandbox. Reviewer
processes are separate OS processes but still run under the same user account.
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .ledger import EvidenceLedger
from .models import Observation, Proposal


class CleanRoom:
    def __init__(self, ledger_path: str | Path, reviewer_timeout: float = 2.0):
        self.ledger = EvidenceLedger(ledger_path)
        self.reviewer_timeout = reviewer_timeout
        self.quarantined: dict[str, str] = {}
        # Reconstruct quarantine state from the verified durable evidence history.
        for record in self.ledger.records():
            payload = record.get("payload", {})
            agent_id = payload.get("agent_id")
            if record.get("event") == "QUARANTINE" and agent_id:
                self.quarantined[agent_id] = payload.get("reason", "quarantined; reason unavailable")
            elif record.get("event") == "QUARANTINE_REVIEW" and agent_id and payload.get("disposition") == "RELEASE":
                self.quarantined.pop(agent_id, None)

    def _review(self, module: str, proposal: dict[str, Any]) -> dict[str, Any]:
        try:
            result = subprocess.run(
                [sys.executable, "-m", module],
                input=json.dumps(proposal, allow_nan=False),
                text=True, capture_output=True, timeout=self.reviewer_timeout,
                cwd=str(Path(__file__).resolve().parent.parent),
            )
            if result.returncode != 0:
                raise RuntimeError("reviewer process exited unsuccessfully")
            review = json.loads(result.stdout)
            if not isinstance(review, dict) or not isinstance(review.get("approved"), bool):
                raise RuntimeError("invalid reviewer response")
            return review
        except Exception as exc:
            return {"reviewer":module.rsplit(".",1)[-1], "approved":False,
                    "reasons":[f"review unavailable: {type(exc).__name__}"], "quarantine_required":True}

    def submit(self, proposal: Proposal) -> dict[str, Any]:
        if proposal.agent_id in self.quarantined:
            return {"status":"QUARANTINED", "reason":self.quarantined[proposal.agent_id]}
        body = proposal.to_dict()
        self.ledger.append("PROPOSAL_RECEIVED", body)
        security = self._review("cleanroom.security_worker", body)
        logic = self._review("cleanroom.logic_worker", body)
        self.ledger.append("REVIEW_RESULT", {"proposal_id":proposal.proposal_id,"security":security,"logic":logic})
        if security.get("quarantine_required") or logic.get("quarantine_required"):
            reason = "; ".join(security.get("reasons", []) + logic.get("reasons", [])) or "review process integrity failure"
            self.quarantined[proposal.agent_id] = reason
            self.ledger.append("QUARANTINE", {"agent_id":proposal.agent_id,"proposal_id":proposal.proposal_id,"reason":reason})
            return {"status":"QUARANTINED","reason":reason,"security":security,"logic":logic}
        if not security["approved"] or not logic["approved"]:
            self.ledger.append("PROPOSAL_REJECTED", {"proposal_id":proposal.proposal_id})
            return {"status":"REJECTED","security":security,"logic":logic}
        self.ledger.append("PROPOSAL_CLEARED", {"proposal_id":proposal.proposal_id})
        return {"status":"CLEARED","security":security,"logic":logic}

    def reconcile(self, proposal: Proposal, observation: Observation) -> dict[str, Any]:
        mismatch = (
            proposal.proposal_id != observation.proposal_id
            or proposal.action != observation.observed_action
            or proposal.target != observation.observed_target
            or proposal.declared_effect != observation.observed_effect
        )
        payload = {"proposal":proposal.to_dict(),"observation":observation.to_dict(),"mismatch":mismatch}
        self.ledger.append("OBSERVATION_RECONCILED", payload)
        if mismatch:
            reason = "agent declaration differs from independent observation"
            self.quarantined[proposal.agent_id] = reason
            self.ledger.append("QUARANTINE", {"agent_id":proposal.agent_id,"proposal_id":proposal.proposal_id,"reason":reason})
            return {"status":"QUARANTINED","reason":reason}
        return {"status":"RECONCILED"}

    def review_quarantine(self, agent_id: str, disposition: str, reviewer_id: str, evidence_ref: str) -> dict[str, Any]:
        if agent_id not in self.quarantined:
            raise ValueError("agent is not quarantined")
        if not reviewer_id.strip() or not evidence_ref.strip():
            raise ValueError("independent reviewer and evidence reference are required")
        if disposition not in {"RETAIN", "RELEASE"}:
            raise ValueError("disposition must be RETAIN or RELEASE")
        self.ledger.append("QUARANTINE_REVIEW", {"agent_id":agent_id,"disposition":disposition,
                           "reviewer_id":reviewer_id,"evidence_ref":evidence_ref})
        if disposition == "RELEASE":
            del self.quarantined[agent_id]
        return {"status":disposition, "agent_id":agent_id}
