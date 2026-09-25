# HELIX contained beta — synthetic behavior lab

This beta packages the 0.2 engine and visual Floor with an executable fault
check. It is a **contained lab beta**, not a trading system or autonomous
multi-agent beta. The named Floor roles are displays of rule-based stages.
These tests establish no profitable strategy, validated learning, or safe
autonomous behavior.

A deliberately small, paper-only laboratory for the Helix architecture.

## Frozen loop
observe → model → hypothesis → prediction → act → outcome → compare → investigate/correct → update belief → remember → next decision

## Safety boundary
- PAPER_ONLY: no broker, exchange, credential, network or live-order integration.
- Security Sentinel checks mechanical boundaries and Logic Review checks evidence;
  both must clear a proposal. These are separate roles in one Python process,
  not independent security domains.
- Risk engine constrains sizing.
- Deterministic execution gate can approve, reject or abstain.
- Black Box records immutable decision/audit events.
- Outcomes are held as observations; promotion is disabled pending an independent validation protocol.
- No self-modifying code.

## Run
```bash
python -m helix.demo
python -m unittest discover -s tests -v
python -m helix.experiment --output runs/beta-check
```

The demo runs a tiny synthetic market and produces a decision ledger under `runs/`.
The experiment writes `report.json` and `decisions.jsonl`; the digest identifies
the ledger for that run. UUIDs and timestamps vary, so repeated runs do not
have identical ledger bytes, though the case results and assertions repeat.
Run from this directory with Python 3.10 or newer; no pip packages.

## Watch a contained run
Run from the `helix_0.2` directory:
```bash
python -m helix.watch
```
The terminal shows five synthetic scenarios, including a reversal, abstention,
and an invalid size injected into Desk. Use `--delay 0` for an immediate run or
`--ledger runs/my-run.jsonl` for a separate decision log. No network or broker
code is present. This watches deterministic rules, not autonomous agents or
emergent behaviour. `runs/watch.jsonl` is appended to on each run; use a new
ledger name for a clean experiment. The ledger is an append-only local JSONL
file, not tamper-proof storage. A correct prediction is retained in Vault as
an observation, not promoted to validated Memory.

## Helix Floor: visual Android dashboard
In Termux, from the `helix_0.2` directory:
```sh
python -m helix.floor
```
Keep Termux open and open `http://127.0.0.1:8765` in the **same phone's** browser.
Press RUN, PAUSE, RESET or SPEED on the dashboard. Press Ctrl+C in Termux to
stop the server. It binds to localhost only; the page has no outside assets or
network requests. `runs/floor.jsonl` appends across sessions. Prices are seeded,
synthetic and capped at 60 steps. Roles on the floor are rule-based displays,
not autonomous AI processes. At cycle 11, 22, etc., an invalid proposed size
is deliberately inserted to show Sentinel's response. This is not a trading
system or evidence that a strategy works.

## One-tap phone setup (Termux:Widget)
Install **Termux:Widget from the same source as Termux** (e.g. both F-Droid).
From the directory containing the unzipped `helix_0.2` folder, run:
```sh
bash helix_0.2/install-one-tap.sh
```
Add a Termux:Widget launcher shortcut or widget to the Android home screen and
choose **Helix Floor**. Tap it to start the local server and open the browser.
If already running, it reopens the floor without launching a second server.
The first install copies Helix to Termux's private home, avoiding repeated
Downloads unzips. A Termux window remains active while the server runs. Ctrl+C
there stops it; tap the shortcut again to restart. No APK is included.
