# M0-02 r22: three-prefix capture adaptation (offline)

Base `f6981c04a4f3062eb737e01673728401e30f8ba3` (merged #264 / r21 literal Trace facility).
No Flash launch or live capture in this slice. All five flags remain false:
production_admitted, native_parity_proven, oracle_accepted, certified_global_tick,
os_input_join_proven. M0-02 pending. Official remaining UNKNOWN; not claiming above
the floor.

## What r21 established

R21 prepared literal Trace-before/after at both true-branch gotos while retaining
direct-local, saved-sink and dynamic channels. Historical r18/r20 receipts still
show prep and (for r20) direct-before without matching after markers; cause remains
**unproved**. R21 added an offline parser/classifier only — not a capture driver.

## What this slice adds

`capture_observer.py` adapts the retained r20 physical PID / System Events menu
path for **r21 observer builds** (`facility` must be `r21`). Future live receipts
must retain byte-original `combined.log` (identical to `flashlog.after.log`) with
all three prefixes in combined order:

- root `M002|<run_id>|`
- side `M002SIDE|<run_id>,...|before|after`
- literal `M002LITERAL|<run_id>|<site>|before|after`

The driver refuses launch when any channel prefix is already present in prelaunch
flashlog, pins main+yihu source hashes, records `side_line_count` and
`literal_line_count`, and keeps the legacy root-only `tagged.log` selection.
Unknown lines remain ordering barriers; nothing is filtered into a synthetic union.

`analyze.py` layers the r21 combined parser/classifier on the unchanged r20
provenance gates (fresh append, foreign root/side/**literal** tags, combined byte
equality, build/session/player/tape/tool pins, physical input and owned cleanup).
Literal pairing rules remain fail-closed; matched literal sequences are
observations only, never admission.

`build.json` pins the offline r21 instrumentation receipt as the expected observer
shape. The next authorized live must compile a **fresh** tag via
`evidence/oracle/native-fight-r21/build_observer.py` into a temporary directory;
do not reuse `m002-r21-offline-20261110` as capture identity.

## Not proved here

No live run exists under `native-fight-r22/run-01`. Historical r20 logs contain
zero `M002LITERAL` lines; they cannot answer whether literal post-goto Trace
executes or delivers. CLI analysis without a receipt exits 1 with an explicit
refusal. Silence after goto remains **unproved**; no root cause is diagnosed.

## Next step (required)

Authorized live with r22 driver + fresh r21 build, then `analyze.py --directory`
on the new receipt. Even matched literal/side-after observations would not certify
global tick, OS input join, repeat, or noninterference.

## Recheck

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r22/analyze.py
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r22/analyze.py --require-oracle
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/native-fight-r22 -p 'test_*.py'
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
```

Both CLI analysis modes exit 1 until a live receipt exists. Eight unit tests cover
prefix freshness, foreign literal refusal, combined-order integrity, and r20→r22
facility mismatch refusal.
