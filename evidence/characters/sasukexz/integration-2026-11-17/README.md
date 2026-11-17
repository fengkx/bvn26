# Susanoo Sasuke current-version integration

The targeted delivery adds the 35th selectable fighter to offline and friend-room
selection while retaining all 34 existing fighters and six assists. It includes
source portraits, footer, natural opening, attacks and the shared shine backdrop
correction described in `../shine-backdrop-source.md`.

The author-lane source questions and original recordings are retained unchanged.
Current-runtime replay matches all 19 original fixtures / 14,198 actor states on
14 fields, including repeated casts, changed target positions, both facings,
guard, interruption and energy rejection. No execution or teardown errors occurred.
The accumulated replay process time was 412.214 seconds; this is not person-days.

Native selection, online reselection, host-authority projection against Sage
Naruto with Orihime, ultimate rollback/next round, sound pause/resume/cleanup and
headed selection/super rendering pass. The sound/visual checks now exit cleanly;
the historical author-lane leaks remain recorded. The shine renderer regression
passes. Eleven source/intro/audit tests, 32 backend tests, package integrity,
handoff links, contracts and font coverage pass. The first backend run was
blocked by sandbox loopback restrictions; the approved rerun passed. The first
sound invocation omitted its output argument; the corrected invocation passed.
The first Web build used the default missing template path; the rerun uses the
installed matching 4.7.2 template. Standard Web export and Chromium WebGL boot pass. The exported PCK contains all
35 fighters and six helpers, with Sasuke portraits and opening.
`web/build-metadata.json` retains the dirty product-snapshot provenance;
`web/boot.json` and `packed.log.gz` bind the executed checks.
The backend catalog was deployed as version
`67b985df-0b85-466e-bc69-24d44ebac31c`.

`summary.json`, retained logs and `replay-raw.tar.gz` contain current evidence.
Native screenshots were inspected: the selectable card, full portrait/footer,
HUD, actor and attack are present. These are render checks, not pixel equality.

Remaining full acceptance work: complete raster/audio parity, hidden-opponent
interruption timing, and physical browser focus recovery. These are separate
follow-up coverage, not additional gates for this targeted character delivery.
All six proof/admission flags and M6 remain unchanged. Frontend production deployment is separate from this local Web validation.
