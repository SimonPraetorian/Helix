import json
import tempfile
import unittest
from pathlib import Path

from cleanroom.ledger import EvidenceLedger, LedgerError
from cleanroom.models import Observation, Proposal
from cleanroom.supervisor import CleanRoom


def proposal(**overrides):
    data = dict(proposal_id="p-1", agent_id="agent-A", action="SIMULATE", target="scene-1",
                payload={"seed":1}, declared_effect={"action":"SIMULATE","target":"scene-1"})
    data.update(overrides)
    return Proposal(**data)


class CleanRoomTests(unittest.TestCase):
    def test_dual_review_clears_consistent_allowlisted_proposal(self):
        with tempfile.TemporaryDirectory() as d:
            room=CleanRoom(Path(d)/"events.jsonl")
            self.assertEqual(room.submit(proposal())["status"],"CLEARED")
            self.assertTrue(room.ledger.verify()["valid"])

    def test_security_violation_quarantines_agent(self):
        with tempfile.TemporaryDirectory() as d:
            room=CleanRoom(Path(d)/"events.jsonl")
            result=room.submit(proposal(action="DELETE"))
            self.assertEqual(result["status"],"QUARANTINED")
            self.assertEqual(room.submit(proposal(proposal_id="p-2"))["status"],"QUARANTINED")

    def test_logic_contradiction_rejects_without_automatic_strike(self):
        with tempfile.TemporaryDirectory() as d:
            room=CleanRoom(Path(d)/"events.jsonl")
            bad=proposal(declared_effect={"action":"DELETE","target":"scene-1"})
            self.assertEqual(room.submit(bad)["status"],"REJECTED")
            self.assertNotIn("agent-A",room.quarantined)

    def test_observation_mismatch_quarantines_and_preserves_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            room=CleanRoom(Path(d)/"events.jsonl")
            p=proposal()
            obs=Observation("p-1","DELETE","scene-1",{"action":"DELETE","target":"scene-1"},"external-observer-1")
            self.assertEqual(room.reconcile(p,obs)["status"],"QUARANTINED")
            self.assertEqual(room.ledger.records()[-1]["event"],"QUARANTINE")

    def test_release_requires_reviewer_and_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            room=CleanRoom(Path(d)/"events.jsonl")
            room.submit(proposal(action="DELETE"))
            with self.assertRaises(ValueError):
                room.review_quarantine("agent-A","RELEASE","","")
            self.assertEqual(room.review_quarantine("agent-A","RELEASE","reviewer-2","evidence:sha256:x")["status"],"RELEASE")
            self.assertNotIn("agent-A",room.quarantined)

    def test_ledger_detects_record_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"events.jsonl"
            ledger=EvidenceLedger(path)
            ledger.append("A",{"value":1})
            rows=path.read_text().splitlines()
            row=json.loads(rows[0]); row["payload"]["value"]=2
            path.write_text(json.dumps(row)+"\n")
            with self.assertRaises(LedgerError):
                EvidenceLedger(path)


if __name__ == "__main__":
    unittest.main()
