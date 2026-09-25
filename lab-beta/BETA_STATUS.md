# Helix contained beta — status and evidence

## Demonstrated locally

- Eight unit tests pass on Python; the five-case synthetic experiment passes its six assertions.
- The Floor exposes a localhost visual monitor, with run, pause, reset and speed controls.
- Desk proposals, separate Security Sentinel and Logic Review vetoes, Kelly/risk sizing, paper gate, outcome and Black Box record are observable.
- Negative size, oversize and malformed size fault inputs fail closed in the checked paths.
- A single correct outcome is held as evidence and does not become validated Memory.

Run `python -m unittest discover -s tests -v` and
`python -m helix.experiment --output runs/beta-check` from this folder. Review
`runs/beta-check/report.json` and `decisions.jsonl`; the report records that
ledger's SHA-256 digest. The local JSONL file can be altered by anyone with
write access. It is an audit record, not a tamper-proof Vault.

## Open gaps before a broader beta

1. Agent independence: Floor role labels still represent deterministic stages;
   no independent processes, adversarial agents or behavior under prolonged runs.
   Security Sentinel and Logic Review are distinct code roles with separate
   vetoes, but run in one process with shared privileges. Independent enforcement
   and audit authority have not been demonstrated. Neither review assigns
   malicious intent or a strike; that requires investigation.
2. Validation: develop preregistered hypotheses, independent held-out tests,
   repeated trials and promotion criteria before enabling Memory updates.
3. Containment: localhost and absent exchange integrations are useful boundaries,
   but not a security proof or hardened isolation. No hostile process testing.
4. Audit integrity: add a tamper-evident ledger, log verification and safe
   recovery after interrupted writes.
5. Android: the separate Android source archive wraps an earlier fixed-price
   demo. This package is Python/Termux plus local browser; no tested beta APK.
6. Financial performance: synthetic P/L is demonstration arithmetic only.
   Real market data, fees, slippage and out-of-sample evaluation are absent.

There are no credentials, broker/exchange adapters, or live order routes in
this package. Do not infer that isolation, alignment or performance is proven.
