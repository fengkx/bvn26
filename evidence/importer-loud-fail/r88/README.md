# r88 — actual component lossless PNG roundtrip is already exact

The54-image component inventory reaches23 distinct embedded bitmap IDs. Source SWFs, timeline source hashes and generated asset PNG hashes are checked.21 are DefineBitsLossless2:3 ARGB format5 and18 indexed RGBA format3. The decoder preserves native premultiplied bytes, palette indices and4-byte row padding; malformed lengths/indices/non-premultiplied bytes reject loudly. Reader layout is independently checked against the pinned FFDEC bytecode excerpts retained here (RGBA palette, ARGB_PRE image).

All21 measured bitmaps, **1031306/1031306 texels**, exactly roundtrip from the current exported PNG under each of the three globally specified candidate constructions. Crucially, source alpha is **only0 or255** (210301 transparent,821005 opaque). This inventory cannot discriminate partial-alpha arithmetic and must not be used to generalize r86's external-PNG behavior. It does rule out loss of raw lossless texels as the cause of these particular component raster differences.

Two source encodings remain explicitly unmeasured:

- `game/fighter/fz/jinye.swf`, DefineBitsJPEG3 **55**.
- `game/fighter/orochimaru.swf`, DefineBitsJPEG3 **340**.

No JPEG decoder is substituted without native evidence. All source IDs/component associations, dimensions, PNG/raw hashes, alpha histograms and model scores are in [inventory.json](inventory.json). [Provenance](provenance.json) pins all source assets and the independent FFDEC reader evidence. This is a source-byte inventory, **not a fresh native component-image pass**;54-suite remains historical9/54.

## Reproduce

```sh
python3 -m tools.probes.inventory_bitmap_roundtrip --output /tmp/bvn-r88/recheck.json
python3 -m unittest tools.tests.test_bitmap_roundtrip_inventory
```

Next bind a failing lossless component such as Jiraiya DefineShape274/bitmap273 to the admitted sampler using its **actual fractional transforms and authored mask**, with original raw tags in native Flash. Its source texels now have exact proof, so isolate fractional coverage/shape placement rather than tuning filter math or PNG arithmetic. Keep JPEG3 IDs55/340 separately pending. Only a complete component-image gate may widen production eligibility.

[Acceptance](acceptance.json). `production_admitted=false`; no production change, no tolerance/allowlist/reference rewrite. Full AS/clip-action ownership, fractional coverage/affine/implicit buffers, JPEG3 and remaining exact components stay open. Full roster/Web and54 component renders not rerun. Draft only; no merge/deploy/Worker.
