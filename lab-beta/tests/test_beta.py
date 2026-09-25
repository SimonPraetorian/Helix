import json
import tempfile
import unittest
from pathlib import Path

from helix.core import Helix
from helix.experiment import run
from helix.models import Action, Hypothesis, Proposal, Observation


class BetaBoundaryTests(unittest.TestCase):
    def test_fault_injection_and_evidence_report(self):
        with tempfile.TemporaryDirectory() as directory:
            report = run(directory)
            self.assertEqual(report['status'], 'PASS')
            self.assertTrue(all(report['assertions'].values()))
            self.assertEqual(len((Path(directory) / 'decisions.jsonl').read_text().splitlines()), 5)
            self.assertEqual(json.loads((Path(directory) / 'report.json').read_text())['ledger_sha256'], report['ledger_sha256'])

    def test_malformed_sizes_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            for bad in ('0.5', float('nan'), float('inf')):
                h = Helix(directory + '/events.jsonl')
                proposal = h.desk.propose
                def faulty(obs, memory, kelly):
                    p = proposal(obs, memory, kelly)
                    p.proposed_fraction = bad
                    return p
                h.desk.propose = faulty
                if isinstance(bad, str):
                    # Sentinel and risk reject malformed input independently.
                    p = faulty(Observation('X',101,100), h.memory,h.kelly)
                    self.assertFalse(h.sentinel.check(p).approved)
                    self.assertFalse(h.risk.check(p,0.01).approved)
                else:
                    result = h.cycle(Observation('X',101,100),102)
                    self.assertFalse(result.execution['authorized'])

    def test_single_correct_outcome_does_not_validate(self):
        with tempfile.TemporaryDirectory() as directory:
            h = Helix(directory + '/events.jsonl')
            record = h.cycle(Observation('X',101,100),102)
            self.assertTrue(record.outcome['correct_direction'])
            self.assertEqual(len(h.vault.evidence),1)
            self.assertEqual(h.memory.validated,[])
            self.assertFalse(record.learning['updated'])

    def test_security_and_logic_have_separate_vetoes(self):
        h = Helix()
        base = h.desk.propose(Observation('X',101,100),h.memory,h.kelly)
        base.proposed_fraction = -0.25
        security_block = h.sentinel.check(base)
        self.assertFalse(security_block.security_ok)
        self.assertTrue(security_block.logic_ok)
        self.assertFalse(security_block.approved)
        base.proposed_fraction = 0.01
        base.hypothesis.evidence = []
        logic_block = h.sentinel.check(base)
        self.assertTrue(logic_block.security_ok)
        self.assertFalse(logic_block.logic_ok)
        self.assertFalse(logic_block.approved)


if __name__ == '__main__': unittest.main()
