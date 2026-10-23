# r13 target graph import

The additional wankai paths have two-node source graphs:

| Source | Base body (parent frame 1) | Replacement body (parent frame 2) | Candidate package |
| --- | --- | --- | --- |
| Byakuya | 631 | 1052 | `/tmp/bvn-loud-fail/r13/byakuya-profile` |
| rifagu | 638 | 951 | `/tmp/bvn-loud-fail/r13/rifagu-profile` |
| rukia | 533 | 976 | `/tmp/bvn-loud-fail/r13/rukia-profile` |

Each bundle contains root load records only at parent frames 1/2. The compiled Byakuya/Rifagu/Rukia replacement AI contexts contain no further parent replacement events. Candidate compilation does not establish native ordering, live-reference, image or gameplay parity; production manifest review and runtime/native tests remain separate requirements.

Two importer corrections:

1. Candidate missing-field discovery now excludes existing direct predicate adapter fields and host HP. Sasuke603 frame312 `ql += 10` remains the existing `energy_delta` event and is never allocated as undefined timeline state. True undeclared `khitn`/`nn` fields retain the r12 undefined/NaN behavior. Tests include the complete shipped Sasuke base context with form compilation enabled.
2. Byakuya1052 uses mask DefineShape882 at frames538/541/616/634, depth27 through29. Its fill table has two slots but only style2 draws edges; style1 is unused. Extraction now counts actual boundaries, allowing its one exact four-edge rectangle. More than one used contour remains a hard error. The source XML shape fixture and regression tests preserve the exact coordinates; the renderer is unchanged.

Byakuya target staging passes all products (248 assets), followed by complete BODY/controller/predicate and sound compilation (28 sound segments). Rukia passes all products (242 assets, 32 sound segments). Logs retain the original Byakuya/Rifagu blockers and subsequent successful Byakuya run.

`python3 -m unittest tools.tests.test_form_undefined_scalars tools.tests.test_mask_fill_slots tools.tests.test_lanran_import tools.tests.test_itachi_import`: 21/21.

Minren parent frame3 body1821 still has a wrapper-level GlowFilter (7x10, strength1.1367188, passes3) at root frame3 depth1. The existing renderer filters nested placements, while its root wrapper currently applies matrix/blend only. Enabling extraction alone would silently omit that authored glow; the precise hard error remains until a whole-root filtered-buffer consumer is implemented and verified.

No allowlist or pixel tolerance was added. Large target/export products stay under `/tmp`, outside production until the lead publishes reviewed complete graphs.

After the independently native-verified energy fallthrough correction, Rifagu951 staging and full profile compilation pass (188 assets, 39 sound segments). Its target AI also has no further form transitions. The initial failure log remains retained; `rifagu-stage.log`/`rifagu-profile.log` record the successful rerun.

Independent review after candidate generation: all three target timelines pass the production cached placement, nested-control and blend guards (9/9; `cached-guards.json`). The preparation tool now runs these guards before publication. Publication stages every new file and its previous bytes on the destination filesystem, publishes the activation last, and rolls back completed replacements on an ordinary I/O error. A fault-injection regression fails while publishing the second node and verifies byte-for-byte restoration of the full installed graph, including removal of a newly added file. This does not claim cross-directory atomicity after process/machine failure; reviewed build hashes continue to reject interrupted graphs. Recovery backups are retained with an explicit error if the rollback itself encounters an I/O failure.

A second independent review found that the base frame-call guard checked shared child effects, but form target contexts did not. Every form node now recursively requires its `frame_child_effect` dependency (`effect.json`) to exist, including conditional branches, with SWF/sprite/frame diagnostics. Preparation carries the shared effects directory into temporary staging so this check applies before publishing. All three new targets use existing XG_rush/XG_hitfloor dependencies. This matches the existing base dependency contract; it does not claim additional image parity.

`python3 -m unittest tools.tests.test_prepare_form_graph tools.tests.test_form_profile_guard`: 14/14 (`prepare-review-tests.log`), including a reviewed target package whose missing shared effect is rejected despite otherwise matching hashes.

Publication follow-up: generated targets may not already have an `ai_controller` directory. Preparation now creates missing destination parents before writing, and removes newly created directories on failed publication rollback. The fault-injection test covers an initially absent controller directory; four prepare tests pass (`prepare-publish-tests.log`). Rifagu/Rukia production preparations subsequently completed with `written=true`, two nodes each. Form activation/native testing remains distinct from placement and package admission.

Online interval integration and its explicit existing simulation-time limitation are documented separately in `../root-interval-authority/README.md`; importer graph/guard success does not establish native online wall-clock parity.
