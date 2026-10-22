# Importer loud-fail checkpoint (Draft)

This checkpoint is incomplete and must not be merged or deployed. It preserves
work before the remaining weekly quota is exhausted.

## Implemented

- Placement field/flag and finite-number guards, selected gameplay call/argument
  guards, and source-hash-pinned nested timeline control requirements.
- Build-time validation of cached timelines; a scanner for all 62 locked SWFs.
- Extraction and native rendering work for BlurFilter, outer GlowFilter,
  ColorMatrixFilter, and cacheAsBitmap isolation; regenerated affected timelines.
- Regression tests for guards and native/Godot filter probe scripts.

## Verification status

The 64x64 native Flash blur fixture matches Godot exactly for 16 cases and 2,560
sampled alpha values (blur widths 0, 1, 2, 3, 5, 10, 15, 20; qualities 1 and 3).
The smaller 8x8 fixture exposes an unresolved difference for large kernels.
The latest opacity-order/compositor fix has now been rerun: maximum absolute
premultiplied RGBA differences are 2/1 for glow at 100%/50% opacity, 2/1 for
color matrix, and 3 for the combined chain. These differences remain unresolved;
no tolerance was introduced to declare parity.

The blur render test now exits nonzero on any mismatch against the captured
native reference, and passes on the latest code (see blur-reference.log):

```sh
Godot --path godot --rendering-method gl_compatibility \
  --script res://tests/flash_filters_render.gd
```

The color render script still produces measurements rather than regression
assertions. Raw native logs and capture metadata are attached.

Before the renderer changes, the existing whole-roster replay passed 227/227
cases, 130,334 matched samples. This is NOT final-change replay acceptance.
The protected function check printed PROTECTED_FUNCTION_OK (attached log).
The Python suite had seven failures (synthetic build fixture needs guard data;
new Vercel files were not yet tracked), with two skips. Handoff passed. Integrity
verification requires reviewed manifest hash updates. These gates must be rerun.

## Newly detected constructs

- Shipped nonzero BlurFilter: Jiraiya, Aizen (lanran), Orochimaru, Ikkaku (yijiao).
- Shipped outer GlowFilter: Uryu (yulong); ColorMatrixFilter: XG_mfdjx and Ikkaku.
- Shipped cacheAsBitmap: Jinye assist. See shipped-filters.json for source sites.
- Unsupported invert/difference blends in locked, unported source content remain
  hard errors; the full scanner report must be finalized for the PR.
- Rukia's numeric gotoAndPlay(130) and shunbuxg calls need native/compiler handling.
- Clip actions, action ownership and every skip/default site still need review.

The only harmless allowlist entry currently added is Byakuya sprite 631 frame 985
in base form: the conditional transformation-only call is unreachable while the
production transformation gate is disabled. Exact source/SWF hashes and form
scope are required. This needs review; it is not blanket transformation approval.
Juggo child controls and main KO controls have separate source-pinned delegation
records pointing to their existing native consumers.

## Remaining work

1. Resolve small-object blur behavior, verify real shipped filter components and
   finish native reference assertions (including opacity and filter ordering).
2. Complete AS calls/arguments, numeric goto, clip-action and placement audit;
   implement supported semantics or reject them with source locations. Do not
   allowlist real missing behavior merely to get a green build.
3. Validate cached placement obligations, fix test-only fixtures, and reduce
   generated requirement duplication if useful.
4. Finish all locked-SWF issue inventory and shipped-content import acceptance.
5. Run final roster replay, protected gate, Python/Godot checks, integrity,
   handoff and contracts; update reviewed hashes/status and runtime fingerprint.

Source files under game/ and scripts/ were not changed. Attached probe scripts
currently use scratch paths and need packaging before they are reproducible CI
fixtures. No completed-port or one-to-one parity claim is made here.
