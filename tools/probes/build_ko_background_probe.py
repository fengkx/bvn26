"""Retain original KO background symbols in an isolated native-player probe."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zlib

from build_minimal_swf import rect, tag

ROOT = Path(__file__).resolve().parents[2]
SYMBOLS = {535, 591, 1507, 1508, 1509, 1510}


def build(ffdec: Path, output: Path, run_id: str) -> None:
    output.mkdir(parents=True, exist_ok=False)
    (output / "game").mkdir()
    raw = (ROOT / "game/main.swf").read_bytes()
    data = raw if raw[:3] == b"FWS" else raw[:8] + zlib.decompress(raw[8:])
    offset = 8 + (5 + 4 * (data[8] >> 3) + 7) // 8 + 4
    selected = []
    while offset < len(data):
        start = offset
        header = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        code, size = header >> 6, header & 63
        if size == 63:
            size = struct.unpack_from("<I", data, offset)[0]
            offset += 4
        payload = data[offset:offset + size]
        offset += size
        if code in (2, 22, 32, 83, 39) and struct.unpack_from("<H", payload)[0] in SYMBOLS:
            selected.append(data[start:offset])
    assert len(selected) == len(SYMBOLS)
    body = rect(0, 12000, 0, 8000) + struct.pack("<HH", 30 * 256, 1)
    body += b"".join(selected) + tag(56, struct.pack("<HH", 1, 1510) + b"background\0")
    body += tag(12, b"\0") + tag(1) + tag(0)
    base = output / "base.swf"
    base.write_bytes(b"FWS" + bytes([8]) + struct.pack("<I", len(body) + 8) + body)
    scripts = output / "scripts/frame_1"
    scripts.mkdir(parents=True)
    script = '''stop();
var bg = attachMovie("background","bg",1);
bg.gotoAndStop("KO");
var tick = 0;
function sample() {
 var child;
 for(var key in bg) { if(typeof(bg[key]) == "movieclip") child = bg[key]; }
 trace(PREFIX + tick + "|0|root|0|frame|" + bg._currentframe + "," + child._currentframe);
}
sample();
onEnterFrame = function() {
 tick++;
 sample();
 if(tick == 35) { trace(PREFIX + "36|0|root|0|done|ok"); fscommand("quit"); }
};
'''.replace("PREFIX", json.dumps("AIREF|" + run_id + "|"))
    (scripts / "DoAction.as").write_text(script)
    with (output / "build.log").open("w") as log:
        subprocess.run(["java", "-Djava.awt.headless=true", "-jar", str(ffdec),
                        "-importScript", str(base), str(output / "game/main.swf"),
                        str(output / "scripts")], check=True, stdout=log, stderr=subprocess.STDOUT)
    (output / "build.json").write_text(json.dumps({
        "run_id": run_id, "source_sha256": hashlib.sha256(raw).hexdigest(),
        "symbols": sorted(SYMBOLS), "script_sha256": hashlib.sha256(script.encode()).hexdigest(),
        "scope": "Unmodified source symbols; isolated gotoAndStop(KO), not a full match"
    }, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffdec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    build(args.ffdec, args.output, args.run_id)
