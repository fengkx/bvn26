# Sampling fix priority after s253

Baseline: master `53d35fcd` / #131. The s249–s253 queue is delivered;
this ranking uses its results, not its former rank numbers. Impact means
prerequisites recovered, never full gates green. `production_admitted=false`;
`native_parity_proven=false`. Only rank 1 is authorized for exclusive s254.

| Rank | Theme / new evidence | Why this position now | First thin cut | Excluded |
| --- | --- | --- | --- | --- |
| 1 | Non-display completion boundary ([s249](s249/README.md), [s232](s232/README.md)) | s249 recovered a shared display receipt prerequisite while explicitly excluding non-display. Geometry s218/s232, ordinary s231, DoAction s228/s235 and call-site s223/s237 still reject before their dimensions can be admitted. This is upstream of source/receiver resolution, with a bounded root-boundary hypothesis; shared symptom is not proof of a shared fix. | **s254:** diagnose the complete retained s232 geometry stream against its archived bootstrap. Separate terminal-period callbacks from the next root observation, rerun the unchanged rejection, and specify the missing native control before any extension of the closure. Evidence-only if unproved. | No closure rollout, suffix trimming, historical receipts, other non-display captures, mixed modes, bitmap policy, gameplay or validator changes. |
| 2 | AImain unloaded identity ([s250](s250/README.md)) | Five captures/610 observations isolate fighter Sprite3 slots, but frame0 is not authored frame1. Wider known display reach than receiver issues; the next needed evidence is now precise. | Observe one initCtrl unload lifetime with receiver/depth occupant identity before/after unload and at first sample. | No 0→1 alias, unloaded-node exemption, masks/camera fixes or blanket binding. |
| 3 | Geometry P1 receiver availability ([s251](s251/README.md), [s247](s247/README.md)) | The atm1 stamp is fixed in its opt-in lifetime. Full geometry now reaches missing P1 receivers at ticks11/41, also present in old traces. This is a newly exposed prerequisite; nested Yulong ownership is related only at the gate level. | Diagnose one s251 P1 receiver lifetime at tick11 against source placement/removal and live identity before changing eligibility. | No repeat stamp fix, ancestor-pn substitution, tick41 expansion, Yulong probe, BitmapData or geometry exemptions. |
| 4 | Positive AS continuation discriminator ([s252](s252/README.md)) | Fresh capture and compiled P-code eliminate missing emitted markers as an explanation, but still do not witness return. A harder observation problem than identifying a receiver lifetime. | Observe the first post-goto instruction independently of invalidated-target lookup on the exact Chad call. | No synthetic call_after, removal-as-return model, full AS or nested receiver change. |
| 5 | Recorded countdown / common visual phase ([s253](s253/README.md)) | Matching actor states and countdown47/59 localize a distinct clock prerequisite. Encoding median1980ms makes guessed 30Hz deadlines invalid; a paired callback tape is required before renderer work. | Record one countdown callback's registration/firings/guards/digit frames relative to the unchanged snapshot and replay only proved events. | No image offset search, timer reset, threshold relaxation, baseline replacement or renderer rewrite. |

Ranks 2–5 are planning only. s249's other display recaptures and unresolved
symbols/masks/camera, full geometry and AS coverage, runtime-loader identity,
and strict rasterization remain deferred obligations, not additional s254 work.
The s241–s244 evidence queue stays delivered. s254 recovers a bounded diagnosis,
not an admitted receipt; potential prerequisite reach is not a measured pass count.
