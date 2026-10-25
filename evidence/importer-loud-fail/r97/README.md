# r97 — signed half-quarter controls independently select ties-to-even

720 native nested/direct draw controls vary30 positive/negative child origins, outer scale0.5/1.5/2.5/3, child scale1/1.23333740234375, and outer draw translations-0.125/0/4.125.180 cases land on exact half-quarter values; immediate neighboring authored twips are retained. All480 source texels and actual matrix properties are explicitly read back. Each output uses an independent1×1 clip with integral vertical interpolation.

The common nested construction is now distinguished on this bounded diagonal domain:

```
translation = round_to_even(child_translation * outer_scale * 4) / 4
            + trunc(outer_draw_translation * 4) / 4
```

The existing scalar initializer then consumes this translation and the composed scale. **86749/86749** nested RGB samples match. Ties-away gives75179/86749; ties toward positive infinity75756/86749. The direct-composed controls remain86749/86749. The same ties-even construction retains all r96 scale controls83423/83423 and (via r96 regression) all r95 translation controls26538/26538. No RGB-selected branch, per-pixel coefficient, epsilon or tolerance is introduced.

This explains the bounded Jiraiya cleared-wrapper input (r95:240000/240000 exact), while preserving the isolated GPU leaf/old sampler evidence. It does not establish a complete authored Blur wrapper or arbitrary affine transform. No production binding is enabled.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-nested-ties --output /tmp/bvn-r97/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r97/native /tmp/bvn-r97/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_bitmap_nested_ties --native evidence/importer-loud-fail/r97/native --output /tmp/bvn-r97/analysis.json
python3 -m unittest tools.tests.test_bitmap_nested_ties
```

[Summary](summary.json), complete failures/old controls in `analysis.json.gz`, [hashes](provenance.json), original capture under `native/`, [acceptance](acceptance.json).

Next discriminator: explicitly materialize the proven cleared-wrapper input in native BitmapData, compare applyFilter(Blur15,0,3) and display filtering of the same bytes against the authored wrapper. Retain pre/post input readbacks. Independently test the existing common integer blur before assuming its input equals the implicit authored filter buffer. Only then connect a complete GPU wrapper; do not enable production from input-only success.

`production_admitted=false`; historical54-suite9/54. Full filtered components, general affine/coverage, implicit buffer boundaries and full AS ownership remain open. Draft only; no merge/deploy/Worker.

Fresh Python734 pass +2skip; caches26/26, fingerprint, protected, integrity, handoff/contracts green. Full roster/Web not rerun: production unchanged.
