import tempfile, unittest
from helix.core import Helix
from helix.models import Observation, Action

class TestHelix02(unittest.TestCase):
    def test_paper_only_and_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            h=Helix(d+"/ledger.jsonl")
            r=h.cycle(Observation("X",100,99),101)
            self.assertTrue(h.gate.PAPER_ONLY)
            self.assertIn(r.proposal["action"],[x.value for x in Action])
            self.assertIsNotNone(r.outcome)

    def test_abstains_on_flat(self):
        with tempfile.TemporaryDirectory() as d:
            h=Helix(d+"/ledger.jsonl")
            r=h.cycle(Observation("X",100,100),100)
            self.assertEqual(r.proposal["action"],Action.ABSTAIN.value)
            self.assertEqual(r.risk["fraction"],0.0)

    def test_sentinel_rejects_bad_size(self):
        from helix.models import Proposal, Hypothesis
        p=Proposal("x",Action.BUY,"X","test",.8,0,Hypothesis("x",1,.8,[]))
        s=Helix().sentinel.check(p)
        self.assertFalse(s.approved)

if __name__=="__main__": unittest.main()
