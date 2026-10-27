# s29 — One-cell native global collision geometry

Base `47079ddf0d3ccbd0e3a4353991d18abd59260b4c`; branch
`feat/sampling-geometry-one-cell`. Exactly the s28 tape:
`didala__attack__neutral__ground__near`. No game runtime/importer changes.

## Results

Real Flash capture: **6,084 events**, **61/61 root geometry samples**, **240 box
records** (238 hurt, 2 attack), **9 observed instance IDs**. `k1atm` appears at
root ticks 13–14, the same ID both times. Both fighters have receiver geometry
at every sampled tick. Helper/stage attack lists are explicitly empty for this
cell. Native receipt revalidation and geometry gate pass. Deleting a whole
sample or one box from the real event stream rejects; original stream rechecks.
**50 focused tests + 19 probe tests pass**, plus integrity/handoff/contracts.

`geometry.json` contains per-frame arrays, role-specific empty arrays, authored
SWF/script origins, instance IDs, first scripted initialization display tick,
current source frame/depth, concatenated global matrix and local bounds.
Global rectangle bounds are derived from all four local corners without
rounding/tolerance. `observed_lifetimes` retains first/last sampled tick per ID.

This is capture completeness, **not native/Godot geometry parity**.
`native_parity_proven=false`; `production_admitted=false`.

## Source and scope

The existing Godot `geometry_probe` accepts selected actor-local names/frame
ranges; it cannot prove this global native scope. We reuse the static native
builder/capture/receipt chain and the native `getBounds`/matrix approach already
used by the hit-receive observer, adding an opt-in `--sampling-geometry` observer.
The original tape and gameplay source files are unchanged.

At the same root boundary after actor state sampling, walk `_root.game` child
MovieClips (direct-parent check, visited paths). The shared source collision
clips expose `getHitObj` and `getStgHitObj`; inspect their `_fsArray`,
`_fzfsArray` and `stgks` to include fighter attacks, both helpers, and stage
`mian` candidates, not only the current fighter's local boxes. Existing loaded
source implementations use `player[key + afterFix]` and stage `.mian` (Didala
sprites 2/539/69, Yihu sprites 2/639). A missing source list or an unbound live
candidate emits an error that the gate rejects.

Attack and hurt shapes share DefineSprite_2. The first diagnostic erroneously
classified `k1atm` as hurt based on methods alone; no geometry was dropped.
Final capture uses the source `*atm` attack-name convention for these shared
clips. Only the corrected capture is accepted/archived. Source scripts in the
instrumented copy stamp each clip once; new instances receive new IDs. Sources
are original script paths, not invented PlaceObject tag locations.

The inventory is **present collision candidates**, not a claim that each one
can damage on this tick: source canhit/pause/guard logic is not replaced or
inferred. Sampling is at root boundaries, so transient intra-frame placements
and exact destruction time are not claimed. Birth is first scripted
initialization; first/last observation is bounded by the 61 samples. Lifetime
IDs are not an emulation of AVM1 live references. Nonempty helper/stage attack
scenes, unscripted candidate symbols and arbitrary dynamic duplication need
separate evidence; unknown source candidates reject, not skip. No general
all-roster geometry admission is claimed.

## Reproduction

Use the s28 case in this directory and fresh native paths/run ID:

```sh
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec.jar \
  --output /tmp/bvn-s29-final-build --run-id s29-didala-final-20261027 --frames 60 \
  --move-case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-geometry
python3 -m tools.sampling_native \
  --case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --build /tmp/bvn-s29-final-build --trace /tmp/bvn-s29-final-capture.log \
  --receipt /tmp/bvn-s29-final-receipts/didala__attack__neutral__ground__near.json \
  --allow-window-activation
python3 -m tools.sampling_geometry \
  --case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s29-final-receipts/didala__attack__neutral__ground__near.json \
  --output /tmp/s29-geometry.json
```

Capture-only escalation for ps/player launch/cleanup was explicitly authorized.
Flash Debugger 32.0.0.465 executable hash is the same as s28. JPEXS hash and
all source/instrumented SWF/probe hashes are in native-build.json/receipt.
The prior legacy boot-label and static-loader-attestation limits from s28 remain.

Raw capture is losslessly gzip-compressed. The approximately 11 MB build archive
retains only build metadata/diff and five receipt-bound instrumented SWFs.
Restore its `bvn-s29-final-build` directory under `/private/tmp`, the raw capture
to `/private/tmp/bvn-s29-final-capture.log` and the original case to the path
above to revalidate the archived receipt. Do not overwrite existing runs.
Original absolute worktree/player paths are required; references are not
rewritten to accommodate changed environments.

## Follow-ups

Godot/native geometry comparison, exact PlaceObject creation/destruction events,
other input cells, BitmapData, child display list, full camera and DoAction
remain open. Jinye/Yijiao residuals are unchanged. No full-roster rerun, parity
claim, production admission, merge, deployment or Worker change.
