# AS / nested-control / cached-call gate review

## Focused fix

`tools/importer/visual_control_guard.py:10–32` previously excluded any dot-qualified control name, so `this.stop()` and `this.gotoAndPlay(...)` produced no nested-control requirement at all. The guard now detects only explicit self-qualified playhead calls (including whitespace around the dot), records the original SWF/sprite/frame/script hash, and rejects them as requiring an owner. It does not fabricate compiled events or extend an allowlist. Existing unqualified supported controls retain exact event comparison. Other object calls are not falsely relabeled as self controls.

Regression: `tools/tests/test_qualified_visual_control_guard.py` covers stop/play, literal/numeric/expression goto, whitespace, source-location errors, unchanged bare-stop ownership, and unrelated member scope. The focused guard suites pass38/38.

All62 retained source bundles were recomputed against the existing visual-control requirement catalog: zero catalog changes. Four existing explicit-self occurrences are clip-action bodies in main.swf DefineSprite836 placements691/698/709/735; these are outside this DoAction-only guard and remain in the separately declared full clip-action ownership scope. They were not removed, allowlisted, or represented as newly handled.

## Existing enforced wiring

- `compile_ai_context.py:627–745`: selected movement/service/playhead call forms either compile their concrete event or reject an unsupported recognized form. Movement expression trees permit only bounded arithmetic over declared fields; selected conditional blocks use whole-source matching. Numeric and parent/form transfers require actual retained destinations/consumers.
- `frame_call_guard.py:18–80`: cached contexts require source hash/sprite identity, reviewed source requirements, exact frame-call digests, parent initialization, nested-stage frames, wrapper-filter initialization, form-package manifest and required effect assets. Changed/missing cached calls are hard errors with source frame paths.
- `visual_control_guard.py:54–99`: included nested definitions require exact source-pinned self-playhead controls or exact hash-scoped delegated ownership. Unsupported nested argument/conditional forms and changed cached events fail hard. Extraction/materialization invokes this validation; build validation uses the reviewed catalog.
- `clip_action_fields.py`: unknown serialized fields/events/flags, malformed action bytes, KeyPress/keyCode loss and inconsistent event summaries fail hard. This explicitly validates metadata serialization, not the semantic owner of every action byte.
- `build_online_manifest.py:168–175`: every generated timeline runs blend, nested-control and placement obligation checks; each shipped fighter additionally runs cached frame-call validation. These guards are on the actual Web build path.
- `import_guards.py:141–155`: existing reviewed frame exception remains SWF hash + script hash + exact path + form-frame scoped, with reason/evidence mandatory. No new exception was added.

## Fresh measurements and honest limit

`python3 tools/importer/audit_frame_calls.py --output /tmp/bvn-merge/as-frame-audit.json` passes26/26 compile contexts and26/26 caches; its1438 broader candidate sites remain `requires_scope_and_consumer_review`. Its overall label remains `incomplete_semantic_audit`.

The selected-call guards are not a complete ActionScript parser or universal ownership proof. Arbitrary calls outside their recognized grammar, first-frame function ownership, unrelated nested receivers and every clip-action body still require the separate complete audit. `audit_importer.py` explicitly inventories this incomplete ownership and exits nonzero; `clip_action_fields.py` explicitly disclaims semantic ownership. Do not describe the merge as “all AS silently dropped behavior is impossible” or “full AS audit passed.” A narrower fail-loud-first merge can accurately claim the enforced, source-pinned checks above and keep this ownership inventory deferred and visible.

No runtime/source SWF/generated-cache output changed. No r251 pixel WIP was created by this worker. Only the focused visual-control guard and its new tests are proposed code changes.

Fresh `python3 tools/build_online_manifest.py --check` also passes: fighters26/helpers5/stages10; build `cc019662780a912bc6231cb7ab824498680067590ad8b5c2f0983e5b9698d2a1`, content `c6ac37d953b958bd27c8d1f07e68251a3948b914735a55e08b6d07cce30c2b23`, unchanged from the preceding checkpoint.
