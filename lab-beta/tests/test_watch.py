import tempfile
import unittest
from helix.core import Helix
from helix.models import Observation

class TestDecisionBoundary(unittest.TestCase):
    def test_invalid_proposal_cannot_trade_or_promote(self):
        with tempfile.TemporaryDirectory() as directory:
            h = Helix(directory + '/events.jsonl')
            propose = h.desk.propose
            def invalid(obs, memory, kelly):
                p = propose(obs, memory, kelly)
                p.proposed_fraction = -0.25
                return p
            h.desk.propose = invalid
            result = h.cycle(Observation('X', 101, 100), 102)
            self.assertFalse(result.sentinel['approved'])
            self.assertFalse(result.risk['approved'])
            self.assertFalse(result.execution['authorized'])
            self.assertEqual(result.risk['fraction'], 0)
            self.assertFalse(result.learning['updated'])
            self.assertEqual(h.memory.validated, [])

if __name__ == '__main__': unittest.main()
