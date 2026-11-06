# Fondability Clean Room 0.1 — contained qualification harness

This is an additive first tranche built beside the Helix 0.2 synthetic lab.

## What it does

- Receives a bounded agent proposal.
- Runs mechanical Security and evidence/consistency Logic reviews in separate OS processes.
- Clears only proposals that pass both reviews.
- Quarantines on prohibited actions, reviewer protocol failures, or mismatch between an agent declaration and an independent observation.
- Records proposal, review, reconciliation, quarantine and release events in an append-only SHA-256 hash chain.
- Requires a named reviewer and evidence reference to release an agent from quarantine.

Ordinary logic rejection is not automatically treated as misconduct and does not create a strike. A mismatch triggers protective quarantine, not a finding of intent. Strikes or disciplinary conclusions require a separate independent investigation and are deliberately not implemented here.

## Run

From `lab-beta`:

```sh
python -m unittest discover -s tests -v
```

The Clean Room tests use only Python's standard library.

## Important security boundary

The reviewer roles are separate OS processes, but they still run under the same operating-system user and inherit broadly similar privileges. This is **process separation, not a hardened security sandbox**. There is no container, restricted token, seccomp, AppContainer, VM, filesystem policy, network namespace or hostile-code execution in this tranche.

The ledger is hash-chained and detects ordinary alteration. An attacker able to rewrite the entire ledger can recompute the chain. Strong tamper evidence requires an independently held checkpoint/signature or external custody. No SEC-001/Spine receipt is claimed.

The supervisor's in-memory quarantine set is not yet restart-persistent. The event ledger preserves quarantine decisions, but recovery/reconstruction of live quarantine state is a required next gate.

There is no live model, external tool, shell, filesystem or network action adapter. The harness evaluates structured proposals and externally supplied observations only. No autonomous agent or production system is being supervised yet.
