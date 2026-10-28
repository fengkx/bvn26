# Ichigo zero-stage attack: reproduction and evidence contract

Base `70951935`, branch `feat/sampling-ichigo-attack-one-cell`.
Only `ichigo__attack__neutral__ground__near`; the exact locked paths are
`game/fighter/ichigo.swf` and `scripts/fighter/ichigo.json`.
The native catalog key is **一护2** (零段), root form 1 places Sprite 274.
The catalog key 一护 loads `yihu.swf`, a different asset. Sprite 632 is another
ichigo form and is not selected by this slice's call-site observer.

The production Godot catalog does not contain ichigo and there is no generated
ichigo fighter. The campaign generator correctly rejects this fighter; its
rejection is retained in `campaign-gate.txt`. The fixture below uses the existing
pure fixture function without changing the catalog or accepting a fabricated
campaign. Native receipts accept the locked native catalog identity independently.
No Godot execution, Godot images, pixel comparison or geometry parity is claimed.

## Fixture and builds

Run from this checkout with Python 3.11 and Pillow; tests also use
`requirements-dev.txt`. The recorded interpreter is `/tmp/bvn-rukia-venv/bin/python`.
JPEXS is `/tmp/bvn-s66-tools/ffdec/ffdec.jar` (hash retained in each build).
Use fresh directories and run IDs for fresh captures.

```python
import json
from pathlib import Path
from tools.sampling_matrix import fixture
cell = dict(zip(('fighter', 'key', 'direction', 'posture', 'distance'),
                ('ichigo', 'attack', 'neutral', 'ground', 'near')))
case = fixture(cell, require_native=True)
p = Path('/tmp/bvn-s224-campaign/cases')
p.mkdir(parents=True, exist_ok=True)
(p / (case['id'] + '.json')).write_text(
    json.dumps(case, ensure_ascii=False, indent=2) + '\n')
```

Build dimensions in order: s224/native (omit flag), s225/geometry,
s226/display, s227/bitmap, s228/doaction, s229/clipaction, s230/callsite.

```sh
python3 tools/probes/build_ai_reference.py \
  --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s225-build --run-id s225-ichigo-attack-20261028 \
  --frames 60 \
  --move-case /tmp/bvn-s224-campaign/cases/ichigo__attack__neutral__ground__near.json \
  --p1-character 一护2 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 \
  --sampling-geometry
```

Each folder retains the capture command, build metadata, instrumented five-SWF
archive, exact fixture, environment, complete untrimmed trace and capture result.
For n=224..230, the capture wrapper calls the following; command-scoped escalation
was needed for native process inspection/launch and account-wide Flash logs.

```python
from pathlib import Path
from tools.probes import capture_native_player as player
from tools.sampling_native import seal
n = 225
case = Path('/tmp/bvn-s224-campaign/cases/ichigo__attack__neutral__ground__near.json')
build = Path(f'/tmp/bvn-s{n}-build').resolve()
trace = Path(f'/tmp/bvn-s{n}-capture/native.log').resolve()
trace.parent.mkdir(parents=True, exist_ok=True)
player.preflight()
assert player.capture(build, trace, 600, lock_timeout=1800)
seal(case, build, trace, player.BINARY,
     Path(f'/tmp/bvn-s{n}-receipts') / case.name)
```

The capture API serializes all launches under
`/tmp/bvn-native-flash-capture.lock`; it never kills another worktree's player.
Window activation is possible. `runtime_fighter=null` preserves the static-loader
attestation limitation; config/source hashes are not independent runtime identity.
If sealing rejects a capture, retain the entire trace; do not trim its suffix.

## Gates and native image decoding

Per-folder `gate-command.json` contains each exact collector command.
Native completeness is revalidated with `tools.sampling_native.validate(case, receipt)`.
Geometry uses `tools.sampling_geometry`; display uses `tools.sampling_display`;
s228/s229 use `tools.sampling_doaction`; s230 uses `tools.sampling_callsite`.
All commands require the exact case and their own receipt, never another dimension's.
The BitmapData gate deliberately fails without an ichigo Godot image manifest.
The absence is not a measured pixel mismatch and is not assigned an exact-frame count.

Decode native bitmap samples only after validating the s227 receipt:

```python
import json
from pathlib import Path
from PIL import Image
from tools.sampling_native import validate
from tools.sampling_bitmap import collect
case = Path('/tmp/bvn-s224-campaign/cases/ichigo__attack__neutral__ground__near.json')
rp = Path('/tmp/bvn-s227-receipts') / case.name
validate(case, rp)
r = json.loads(rp.read_text())
m = json.loads((Path(r['build']) / 'build.json').read_text())
frames = collect(Path(r['trace']).read_text().splitlines(), m['run_id'], 60)
out = Path('/tmp/bvn-s227-native-images')
out.mkdir(exist_ok=True)
for tick, rgba in enumerate(frames):
    Image.frombytes('RGBA', (600, 400), rgba).save(out / f'{tick:03d}.png')
```

## Restore and limitations

Restore each native build archive into `/private/tmp/bvn-sNN-build`, raw trace into
`/private/tmp/bvn-sNN-capture/native.log`, and case/receipts into the paths above.
Keep this checkout at the recorded absolute path for receipt hash validation.
Per-folder artifact hashes bind packaged evidence; native receipts bind source,
probe, engine, build, case and full trace bytes. They do not prove parity.

Display joins reuse main/yihu/helpers from `../s30/source-exports.tar.gz` at their
recorded `/tmp/bvn-s30-source` paths. Restore s226's ichigo XML archive into
`/tmp/bvn-s226-source`, and its `source-exports.json` into `/tmp/bvn-s226-exports.json`.
The fresh export used `java -jar /tmp/bvn-s66-tools/ffdec/ffdec.jar -swf2xml
 game/fighter/ichigo.swf /tmp/bvn-s226-source/fighter-ichigo.xml`.
Source/XML hashes were checked before joining.

Captures are independent runs: timing, random effects and instrumentation can differ.
Global candidate geometry does not prove damage eligibility or exact intra-frame
lifetimes. Hierarchy/transforms/camera observations do not prove dynamic masks or
framebuffer clipping. BitmapData is losslessly decoded opaque 600x400 RGBA without
crop, resize, alignment, gamma correction or tolerance. AS entries and selected
call/branch markers do not prove every statement, callee body, dynamic dispatch,
or Godot ownership. Full inventories retain unvisited and uninstrumented items.
`production_admitted=false`; `native_parity_proven=false` throughout.
