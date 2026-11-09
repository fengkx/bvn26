# M0-02 r06: one live validation of prepared r05

One authorized live attempt completed in **84.878 seconds**, movie PID **42900**,
unique tag **m002-r06-live-20261109-1654**. The physical menu reached Vs Com,
Ichigo/Naruto, Kon/Gaara, present-world stage and an active fight. A physical J
was held for 0.5 seconds at the final fight step. No second run was performed.

**No fight-key-return event was observed.** The prepared 39 Ichigo decision sites
therefore have no live execution/return proof in this run. Physical J delivery
and a visible fight do not prove query consumption or the source-site binding.
No cause is asserted from silence; the active loaded decision path needs separate
investigation. The offline r05 reachability assumption remains unvalidated.

The new timer observer did emit **24 entries and 24 exits** (local timer ordinals
1–24). These are descriptive observations, not admitted oracle state: **10 timer
boundaries contain undefined actor state**. The first boundary (seq183,
getTimer57086, camera ordinal30, timer ordinal1) is paused, with undefined HP for
both actors. The unchanged r05 analyzer stops at `Incomplete actor state at clock
boundary`; both ordinary analysis and `--require-oracle` return **1**. No failing
prefix was removed and no gate was weakened.

`production_admitted=false`, `native_parity_proven=false`,
`oracle_accepted=false`; **M0-02 remains pending**.

## Retained receipts and attribution

- `run-01/session.json`: pinned player SHA, OS/architecture/Rosetta-command and
  trace configuration receipts, all 75 original/copy hashes, lock acquisition,
  unique movie command/PID, nine physical operations and owned-process cleanup.
- AX/CG snapshots, physical input results and nine screenshots retained.
  Initial pre-activation frontmost PID was87154. All subsequent 17 sampled
  before/after probes show42900. No focus-loss or TCC blocker was reported.
  Checks are sampled at operation boundaries, not a continuous focus monitor;
  this is not proof against every transient focus change between probes.
- Cleanup left `remaining_movie_pids=[]`; only the owned movie was terminated.
  Original assets and **both modified copies** passed final hash verification.
- Raw prelaunch/baseline/final/delta flashlogs and tagged.log retained. Baseline125
  bytes → final1,197,627 bytes, append delta1,197,502. Startup log reset is retained
  in the session; the driver did not truncate the log.
- Fresh tag and strict contiguous sequence: **4,871 events**. Counts:741 camera
  entry/exit pairs,3,060 actor states,278 intro queries,1 music random return,
  24 timer pairs,1 boot,1 ready marker. Zero fight queries, zero positive fight
  queries. The source end marker at900 camera callbacks was not reached.
- The inherited account-wide attribution text in session.json is preserved raw;
  scoped fresh-tag selection is separately checked. A tag is not OS per-write PID
  attestation, a complete exclusive contract trace, or global tick identity.

## Build and driver

The unchanged r05 builder produced `/tmp/bvn-m002-r06-live-01` with the new tag.
`build.json`, original-stage instrumentation.diff.gz and extension.diff.gz pin
source/compiler/output identity. Final tag audit versus originals: four main
DoAction payloads and one Ichigo DoAction, exactly as r05; every other tag/header/
topology and73 other assets unchanged. No original asset/runtime/shared validator
or r01–r05 evidence was edited. All SWF outputs are temporary.

The local capture driver is the r03 physical PID driver with the build-source
check extended to require r05 plus **both main and Ichigo** original hashes.
All75 output hashes are checked before and after. Tape version4 changes only the
final fight-J hold from0.15s to0.5s. AX/CG ownership, input-PID and foreground guards,
capture lock, and owned cleanup are retained. No CUA app-string selection, global
API hijack, forced timeline or AS-as-input was used.

## Offline recheck (does not launch Flash)

```sh
python3.11 evidence/oracle/native-fight-r05/analyze.py \
  --build evidence/oracle/native-fight-r06/build.json \
  --directory evidence/oracle/native-fight-r06/run-01
# Repeat with --require-oracle: both commands exit 1.
python3.11 -m unittest discover -s evidence/oracle/native-fight-r06 -v
python3.11 -m unittest discover -s evidence/oracle/native-fight-r05 -v
python3.11 -m unittest discover -s evidence/oracle/native-fight-r03 -v
python3.11 evidence/oracle/native-fight-r06/summarize.py
```

`summarize.py` reports counts without changing admission. Its copy/tag recheck
requires the receipt-pinned temporary movie copy to remain present; raw log/gate
rechecks use repository receipts only. `analysis-gates.json` preserves refusals;
`checks.json` records tests and project gates. Compiler logs are compressed.

Unproved: positive fight-path query execution, downstream input consumption/ticks,
exact initial-state boundary, certified global ExecutionProfile clock, full random
tape/provenance, exclusive complete state trace, deterministic repeat and
SOURCE_FIRST original/instrumented same-input noninterference. Timer observations
and successful menu delivery close none of these acceptance obligations.

Codex remaining percentage was not visible in the official UI this turn; no
credential/session files or unofficial quota APIs were inspected.
