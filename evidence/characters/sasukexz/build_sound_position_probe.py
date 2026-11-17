"""Build a fresh read-only event-sound position observer; never reuse a live probe."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path("tools/probes").resolve()))
from build_ai_reference import build
from instrument_start_sound_tags import instrument

root = Path.cwd()
output = root / "evidence/characters/sasukexz/probe-sound-position-r04"
ffdec = Path("/Users/fengkx/me/agent-code/toolchains/jpexs-26.2.1/ffdec-cli.jar")
run_id = "sasukexz-sound-position-r04"
build(ffdec, output, run_id, 360,
      move_case=root / "evidence/characters/sasukexz/cases/super.json",
      p1_character="佐助须佐", p2_character="一护",
      p1_helper="我爱罗", p2_helper="魂", profile="diagnostic",
      diagnostic_auto_start=True, diagnostic_key_injection=True,
      diagnostic_trace_hooks=True)
target = output / "game/fighter/sasukexz.swf"
base = output / "base-sasukexz.swf"
target.rename(base)
report = instrument(ffdec, base, target,
                    Path("/private/tmp/bvn-sasukexz-export"),
                    Path("/private/tmp/bvn-sasukexz-export/sasukexz.xml"),
                    run_id, 727, 776, 2600, 25)
(output / "sound-instrumentation.json").write_text(json.dumps(report, indent=2) + "\n")
manifest_path = output / "build.json"
original = manifest_path.read_text()
(output / "base-build.json").write_text(original)
manifest = json.loads(original)
manifest["outputs_sha256"]["game/fighter/sasukexz.swf"] = hashlib.sha256(target.read_bytes()).hexdigest()
manifest["additional_observer"] = "sound-instrumentation.json: StartSound tags and read-only Sound.position/duration"
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
print("SOUND_POSITION_PROBE_BUILT", report["tag_count"])
