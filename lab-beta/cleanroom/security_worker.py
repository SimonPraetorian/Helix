"""Independent-process mechanical security reviewer."""
import json
import sys


def review(proposal: dict) -> dict:
    reasons = []
    action = proposal.get("action")
    target = proposal.get("target")
    if not isinstance(proposal.get("proposal_id"), str) or not proposal["proposal_id"].strip():
        reasons.append("missing proposal identity")
    if not isinstance(proposal.get("agent_id"), str) or not proposal["agent_id"].strip():
        reasons.append("missing agent identity")
    if action not in {"OBSERVE", "PROPOSE", "SIMULATE"}:
        reasons.append("action outside Clean Room allowlist")
    if not isinstance(target, str) or not target.strip():
        reasons.append("missing target")
    if not isinstance(proposal.get("payload"), dict):
        reasons.append("payload must be an object")
    return {"reviewer":"security", "approved":not reasons, "reasons":reasons, "quarantine_required":bool(reasons)}


if __name__ == "__main__":
    try:
        data=json.load(sys.stdin)
        print(json.dumps(review(data), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"reviewer":"security","approved":False,"reasons":[f"reviewer protocol failure: {type(exc).__name__}"],"quarantine_required":True}))
        raise SystemExit(2)
