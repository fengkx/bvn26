# M0-02 r26: r25 dispatch identity and lifetime bounds (offline)

Base `5f53c156e8703a81bb0a4f0ac1f44082543f150f` (#269 squash), branch feat/m0-02-oracle-r26-offline. Tracked tree was clean; only the two expected untracked b97e/c62f directories existed and remain untouched/uncommitted. No live, Flash launch, Computer Use, input, deployment action or runtime/asset changes. Official weekly remaining UNKNOWN; no supported current quota meter was exposed by the available TUI tools.

## What the existing bytes establish

Input pins cover the r25 raw/session/build receipts and locked yihu source/asset. Replay verifies four-prefix freshness/foreign checks, byte-identical combined/final logs and root selection. The surviving r25 yihu copy was hash-matched against its committed build receipt before offline FFDec P-code export; compiler hash also matched. bytecode-receipt.json and compressed exports retain exact input hashes, commands, exit and output hashes. Tests/replay use repository artifacts only, not surviving temp copies.

- instance2915 has one decision-installed root marker at seq4498. There are127 consumer-query-before events with that exact path, ending in the validated true prefix for serial127, prep6925. The last root event with its exact path is6925. This is last **observation**, not a termination time.
- The inherited full non-AI prefix validator accepts the lexical source-prefix identity for the true doAllAction candidate. The literal/direct/sink classifications remain unmodified; no post-goto continuation is observed.
- Target raw line7058 records only `/game/p1/mc`, frame174, and the literal source-site/run tag. It is between root6932 and6933. Root6926–6931 and another helper's installation6932 intervene after prep. instance3071 appears once, in that installation. Installation of another path does not observe destruction of the old path.
- Exactly one preceding validated true prefix has the same **body path string**. Even uniqueness among observed prefixes is insufficient: path equality/order is not a generation, dispatch or call token.

The source-site inventory adds an important bound: Sprite16 is shared. Both body638 and body1672 have `frame_1/PlaceObject2_16_31` enterFrame scripts calling doAllAction; body1180 uses Sprite651. The generic `yihu-sprite16` installation marker contains only `this._target`, not parent character definition, depth or generation. Thus the prior static body638 depth31 placement/removal13 is not itself a runtime lifetime binding for instance2915. The target marker specifically names body638/frame174, but does not prove the preceding helper's parent-definition/generation was the same object. No claim of an actual form switch is made.

Receipt-matched target P-code reads this._target and this._currentframe, then Trace, then the unchanged 动作 assignment. It contains no initiating helper/serial or removal/dispatch token. These omitted fields cannot be reconstructed from a nearby installation name. All channels still share native runtime and output delivery; no bytecode export proves execution of a silent after instruction.

## Tighter refusal, not a new association

`analyze.py` produces `body-target-observed-dispatch-identity-unjoined`, retaining:

- actual target body/frame and immediate root neighbors;
- all prior installation paths under that body path, their query counts and last exact-path root observations (never a live/dead set);
- preceding validated source-prefix candidates, explicitly not a selected causal caller;
- separate missing witnesses: target→invocation token, parent-definition/depth/generation binding, native removal/interrupt edge, and dispatch entry/exit identity.

initiating_call_join_proven, helper_lifetime_proven, removal_edge_proven and native_return_proven all stay false. Cause=unproved. Even an artificially adjacent target or a single candidate remains unjoined; duplicate target visits are retained rather than assigned to one return. A mismatched owner cannot inherit the old candidate. The classifier does not use timestamp proximity or local ordinal/serial as a global identity.

Compatible unresolved explanations include helper execution context ending versus continued execution with unavailable post-call emission. The evidence does not choose between these or prove either occurred. Body-frame174 output rules in that body source observation; it does not rule out specific helper/context-local failures. No absence of a log line is promoted to a native lifetime event.

## Next discriminator requirements (not implemented)

No new SWF marker is justified as a dispatch/lifetime fix by these bytes. A source-only parent-definition/depth/installation token could reduce source-placement ambiguity, but would still not certify native destruction or dispatch return. A root mailbox or nearest target pairing would merely encode an assumption if intervening transitions are unobserved; this slice does not add one.

The next step after review is offline feasibility work: identify a sanctioned, independently observable per-instance removal/dispatch boundary and its actual identity fields, then define how that witness would be bound to both the initiating helper and the body target. Any proposed witness must distinguish reincarnation/replacement, missing/repeated/interleaved callbacks and absent after emission. If no such boundary is available, retain the refusal rather than another live of the same marker set. Later live is conditional on a reviewed discriminator and separate authorization; this slice requests no live.

## Gates and validation

Both CLI modes exit1 with unchanged `Incomplete actor state at clock boundary`; r25's ten incomplete rows remain intact. The analyzer reads raw receipts, never rewrites historical reports. Five flags remain false: production_admitted, native_parity_proven, oracle_accepted, certified_global_tick, os_input_join_proven. M0-02 pending. No full RNG, deterministic repeat, original/copy noninterference, OS join or certified clock claim.

Eight tests cover real identity bounds, foreign/wrong-owner target refusal, synthetic adjacency/duplicates/missing-prefix without a join, shared-parent source sites and receipt-matched target P-code. Synthetic transformations are tests only. No new SWF compile is needed because this is an offline classifier, not new instrumentation. verify/handoff/diff checks and actual exits are retained in checks.json.

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r26/analyze.py
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r26/analyze.py --require-oracle
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/native-fight-r26 -p 'test_*.py'
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
```
