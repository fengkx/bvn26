# M0-02 r22: live three-prefix literal Trace discrimination

Base: `35d5cd00aceb59b2e13dacb0c3d76a6703f7c2d6`. One fresh r21 build and one r22 physical-PID capture; no Computer Use or Locked use. Historical evidence and local failed b97e/c62f packages are unchanged and excluded from this commit.

## Actual run

Run `m002-r22-live-20261111-e84a`, movie PID 69946, elapsed 92.08485794067383 seconds. Guardian/on-request require_escalated was approved for the capture command; the session remained workspace-write. Accessibility and Screen Recording preflight were true/true. Preflight frontmost was PID60360; Escape returned exact movie PID69946 with frontmost=true. All 17 subsequent focus samples matched69946; samples are not continuous focus proof. All nine physical tape operations completed through fight J (0.5 seconds). Owned cleanup targeted only69946; remaining_movie_pids=[]; asset recheck passed. No password, grant request, focus/TCC blocker or second capture. Focus restoration to a particular application after cleanup was not independently observed.

The pre-existing Flash PID50810 appears in window receipts. No causal role in focus failure is established; this successful run does not prove it universally harmless. Coordinator identified preflight PID60360 as Grok Bot; this capture's own preflight supplies the PID.

Freshness passed for M002, M002SIDE and M002LITERAL. `combined.log` is byte-identical to `flashlog.after.log`, preserving all bytes and raw order (including non-UTF8 lines); `tagged.log` is the root selection only. Source/player pins, before/after copied resources and six original-to-copy DoAction changes passed. All75 copied resource hashes were independently checked. Build receipts/diffs are retained; SWFs remain temporary outputs, never locked asset edits.

## Observations and refusal

- 7629 root events;1914 fight-key queries, one positive at yihu-decision-9 (key74).
- Two loader requests, four load-complete entries/exits, one chushi HP before/after pair;26 timer entry/exit pairs. Twelve early incomplete HP boundaries remain intact.
- One startFight/menu shape interval seq3350–3357.
-161 doAllAction consumer candidates:160 false intervals validate; one true candidate is refused. No doStand candidate observed.
- True candidate: helper `/game/p1/mc/instance3413`, serial1, query seq6513, key queries6514–6517, predicate=true6518, goto-before6519, continuation-prep6520, adjacent direct Trace-before then literal Trace-before. Next root event is6521.
- Direct before1/after0; literal before1/after0; sink breadcrumb0; dynamic consumer-goto-after0. Classification: `literal-before-without-after`; cause=unproved. Literal alone has no helper identity; the complete adjacent prefix supplies bounded attribution.

The no-local/register literal after channel also remains silent despite three-prefix freshness and byte-identical raw logs. This refuses an explanation that after was hidden **only** by local/register dependence in this observation. It does not establish absent continuation, helper removal, native goto non-return, AVM abort or Trace delivery failure. Static encoded placement is not execution proof.

Both analyzer modes exit1 with unchanged `Incomplete actor state at clock boundary`. All five flags remain false: production_admitted, native_parity_proven, oracle_accepted, certified_global_tick, os_input_join_proven. M0-02 pending. No certified global initial state/tick, OS issuance/dispatch join, complete RNG tape, deterministic repeat, observer noninterference, native dispatcher return or downstream action proof is claimed.

## Next step

First inspect receipt-matched target `砍1` timeline and PlaceObject/RemoveObject/helper placement offline, including what lifetime/context the current Trace channels share. Design a discriminating observation independent of that context only if source evidence supports it. A later authorized live is needed to test a justified discriminator; repeating this run is not itself a diagnosis. No additional live in this slice.

## Recheck

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r22-live-03/analyze.py
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r22-live-03/analyze.py --require-oracle
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/native-fight-r22-live-03 -p 'test_*.py'
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
```

See checks.json for actual exits. Capture/analyzer/tape and14 existing adapter tests are retained unchanged from r22; additive live regression tests check the new raw prefix and refusal. Official Codex remaining UNKNOWN; no current meter was available and no above-floor claim is made.
