# M0-02 r23: body-target discriminator preparation (offline)

Base `6d1370295a184f87f848a9f94dc1e2f66d3070e3` (#266 squash). New branch created by checkout from that commit; published history was not rebased/reset. Local untracked b97e/c62f receipts and all historical evidence remain unchanged. No Flash, Computer Use, input, capture or deployment in this slice. Official remaining UNKNOWN.

## Receipt-matched facts

`input-pins.json` locks e84a raw logs, build/session and original source/SWF. The surviving e84a temporary yihu SWF matched the committed build hash before P-code export. Reconstructed source equals its retained compiler input byte-for-byte. `bytecode-receipt.json`, `e84a-source.as.gz`, `e84a.pcode.gz` retain these checks. The pinned compiler is identified by SHA256; temporary tool paths in commands are provenance, not requirements for offline replay.

- Helper installation seq6511 identifies yihu-sprite16 at `/game/p1/mc/instance3413`.
- Query seq6513 records helper serial1, doAllAction, body `/game/p1/mc`, body frame2 (binary number encoding `f:1:1:67108864:0`), useAI=false. Keys6514–6517 are true/false/false/false; predicate6518 true; goto-before6519; prep6520; adjacent side-before and literal-before; next root event6521. All after channels absent.
- The reconstructed source/P-code retains original goto once, followed by literal Trace-after, local Trace-after, saved sink and dynamic after. No explicit Return occurs between the call and literal after. Static encoding does not establish actual continuation.
- `timeline-audit.json` compares every original/e84a tag: only Sprite16's instrumented DoAction differs in yihu. **All body Sprite638 timeline tags are byte-identical**. `diagnosis.json` retains ordered label/placement/removal/action rows, not a fabricated runtime timeline.
- Sprite638 labels: 站立 at frame1, 砍1 at frame173. Frame1 places Sprite16 at depth31 (move=false), with an existing enterFrame callback `if(gameRunning()) { doAllAction(); }`. Encoded frame13 removes depth31. Frame173 places another Sprite16 at depth34 (move=false); its enterFrame script tests wankai, not doAllAction. Frame175 removes/replaces depth34. Frame174 has existing body DoAction `动作 = 1;`.

These facts identify a static lifetime discontinuity to investigate. They do **not** bind the auto-generated name instance3413 directly to a native depth/lifetime receipt, prove which removal executed during goto processing, or prove that removal cancels the invoking action context. Timeline jump handling/native scheduling is not inferred from a sequential static scan. Helper removal, goto nonreturn, action abort and Trace delivery failure remain unproved causes. A fresh helper installation is not an old-helper destruction receipt.

## Narrow independent-context observation

`build_observer.py` layers the unchanged r21 observer, then prepends one direct Trace to the **existing body** `DefineSprite_638/frame_174/DoAction.as`:

```actionscript
trace("M002TARGET|UNIQUE_TAG|yihu638-frame174|" + escape(this._target) + "|" + this._currentframe);
动作 = 1;
```

This runs only if the player's normal timeline executes that existing body script. It does not wait for the original helper function to resume, read helper locals/registers, invoke the root observer sink, or modify control flow. It uses body property reads, escape, Trace and the same player/log delivery: **independent of the originating helper continuation, not independent of all execution or output infrastructure**. It is not a marker at frame173, native call return or helper removal. It cannot distinguish other routes into frame174 from the particular observed goto. No pending attribution mailbox is invented.

The tag audit expands honestly from six to **seven DoAction tags**: inherited five main tags + Sprite16 decision + Sprite638 frame174 `root/644:39/sprite638/308:12`. No placement/removal/clip-action changes. All75 copied assets checked; locked inputs unchanged. Offline tag `m002-r23-offline-20261111`, temp output `/tmp/bvn-m002-r23-offline-01`, not a live run. Target P-code has one Trace immediately before the unchanged 动作 assignment. Compiler stderr/stdout are retained, including any host warnings.

SOURCE_FIRST bounds: (1) exact frame174 script retained in source-sites.json; (2) frame1/13/173/175 placements/removals above; (3) source doAllAction uses original gotoAndPlay once, no forced transition added; (4) predicate/short-circuit/goto and body assignment preserved; (5) original/copy same-input comparison is **missing**. Therefore no runtime mechanism change or completion claim.

## Parser and acceptance

`analyze.py` replays immutable e84a and the unchanged r05 full-prefix structural gate. Both CLI modes exit1: `Incomplete actor state at clock boundary`. No missing HP row is trimmed/filled. Five flags false: production_admitted, native_parity_proven, oracle_accepted, certified_global_tick, os_input_join_proven. M0-02 pending.

The additive target parser rejects foreign tags, wrong body owner, wrong frame and malformed records. It preserves repeated visits as separate observations and always reports initiating_call_join_proven=false/helper_lifetime_proven=false. Existing e84a has zero target markers because this facility was not installed; that absence is **not** an observed failure of frame174. Synthetic target lines exist only in tests.

## Exact next step before any later authorized live

Prepare a capture/provenance adapter for **four** fresh prefixes M002/M002SIDE/M002LITERAL/M002TARGET, receipt-match this r23 build, preserve byte-original combined==flashlog.after, and reject foreign target tags. The historical r22 three-prefix adapter must not be used unchanged: it does not certify the new channel's freshness/build identity. This package is offline builder/parser preparation, not that capture adapter.

A later authorized physical-PID live is needed to ask whether the body frame174 marker is observed when helper after channels are silent. If present, it proves body source execution/output at174, not the exact initiating call, original-helper survival or native return. If absent, target reachability and output remain unresolved; do not infer death/abort. Any later call/lifetime join needs independent per-instance/edge evidence. Global tick, OS input join, full RNG/trace, deterministic repeat and noninterference remain separate gaps. No live should precede independent review and adapter preparation.

## Validation

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/native-fight-r23 -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r23/analyze.py
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r23/analyze.py --require-oracle
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
```

Eight targeted tests cover static edges, exact patch/source refusal, malformed/foreign/wrong-context target refusal, repeated visits without a call join, encoded P-code and historical structural refusal. Replay/tests use repository files only; no surviving temporary SWF is required. Actual exits are in checks.json. Rebuild using receipt-pinned FFDec with `build_observer.py --ffdec JAR --output NEW_TEMP_DIRECTORY --run-id FRESH_TAG`; never write to locked game/scripts.
