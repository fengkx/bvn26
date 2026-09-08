# Source compiler progress

Date: 2026-09-08. The fixed VS COM battle is not implemented or accepted yet.

## Native predicate compilation

`tools/importer/compile_ai_predicates.py` specializes the explicit player branch
out of the retained Sprite 16 controller and compiles 27 predicate functions to
native GDScript. It retains ordered guards, strict combo checks, scalar comparison
semantics, local variables and rush's facing writes. Unsupported expressions,
assignments and statements fail compilation. Generated code contains no source
parser or AVM interpreter. It is currently generated outside the game project;
the battle context adapter and ordered dispatch are still required.

The context ABI uses numeric, boolean and string fields. JSON null in the test
fixture denotes an absent AS2 value, not explicit AS2 null. It does not claim
general ActionScript coercion compatibility. Sensors are supplied outcomes;
MovieClip geometry and missing-instance lookup are not verified by this test.

```bash
python3 tools/importer/compile_ai_predicates.py \
  --output /tmp/bvn-ai-compile/predicates.gd
python3 tools/probes/check_ai_predicates.py \
  --godot /absolute/path/to/Godot \
  --output /tmp/bvn-ai-predicate-check
```

The independent reference executes the retained functions in Node with a fixture
object graph. Godot executes the generated native functions against the same
scalar inputs. 52,650 cases match both return values and facing writes. This is
translation evidence, not proof of AVM1 scheduling, RNG timing, geometry or a
complete fight. See `predicate-translation.json` for source and artifact hashes.
The retained `predicate-native.log` also records sandbox-denied macOS user-data
directory creation and certificate access; the fixture writes its results under
the temporary project and all 52,650 native results were produced and compared.

## Parent goto removes the executing clip

The native Adobe FP32 debugger produced `parent-goto.log` from
`tools/probes/as2/ai_parent_goto`. The root stops at frame 1. Its child's first
enterFrame jumps the parent to frame 3, whose display list removes that child.
The source then contains two trace calls and a second goto, but neither trace
nor frame 2's script executes. Frame 3's trace does execute.

- Player SHA-256: `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`
- Probe SWF SHA-256: `7c3d6944805a5cdd934c9d1fb775cdbb66d81d14e7cdb804f53cf8aec9a2d17c`
- Build: `tools/probes/build_schedule_probes.py` with JPEXS 26.2.1.
- Capture: opened `/tmp/bvn-ai-parent.swf` in the native debugger and extracted
  only the `AI_PARENT_GOTO` lines from its shared trace log.

This narrows AI-U05: a plain parent goto in the removed clip's callback does not
continue like the earlier root-level goto probe. The separate
`ai_parent_function` probe tests a function call and a retained-then-removed clip;
it has been built but has **not** been observed successfully. Do not generalize
the callback result to all call-stack configurations or close AI-U05 yet.

Next integration work: verify the function-call case, compile source decision
windows and action-state writes, bind the real sensor geometry, and implement
the source timer/RNG lifecycle before enabling the fixed easy CPU mode.
