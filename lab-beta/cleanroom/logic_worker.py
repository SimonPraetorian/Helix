"""Independent-process evidence/consistency reviewer."""
import json
import sys


def review(proposal: dict) -> dict:
    reasons = []
    declared = proposal.get("declared_effect")
    payload = proposal.get("payload")
    if not isinstance(declared, dict):
        reasons.append("declared_effect must be an object")
    elif not isinstance(payload, dict):
        reasons.append("payload unavailable for consistency review")
    elif declared.get("action") != proposal.get("action") or declared.get("target") != proposal.get("target"):
        reasons.append("declared effect contradicts proposed action or target")
    return {"reviewer":"logic", "approved":not reasons, "reasons":reasons, "quarantine_required":False}


if __name__ == "__main__":
    try:
        data=json.load(sys.stdin)
        print(json.dumps(review(data), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"reviewer":"logic","approved":False,"reasons":[f"reviewer protocol failure: {type(exc).__name__}"],"quarantine_required":True}))
        raise SystemExit(2)
