"""Build a nested ClipAction lifetime/order probe without game assets."""

from pathlib import Path
import argparse
import hashlib
import json
import struct
import subprocess

from build_minimal_swf import rect, tag


def placement(character: int, depth: int, name: str) -> bytes:
    actions = struct.pack("<HI", 0, 2) + struct.pack("<II", 2, 1) + b"\0" + struct.pack("<I", 0)
    return tag(26, bytes([0xA6]) + struct.pack("<HH", depth, character)
               + b"\0" + name.encode() + b"\0" + actions)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffdec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    child = tag(39, struct.pack("<HH", 1, 1) + tag(12, b"\0") + tag(1) + tag(0))
    parent = (struct.pack("<HH", 2, 3) + placement(1, 1, "child")
              + tag(12, b"\0") + tag(1) + tag(12, b"\0") + tag(1)
              + tag(28, struct.pack("<H", 1)) + tag(12, b"\0") + tag(1) + tag(0))
    tags = child + tag(39, parent) + placement(2, 1, "a") + placement(2, 2, "b")
    body = rect(0, 20, 0, 20) + struct.pack("<HH", 30 * 256, 1) + tags + tag(12, b"\0") + tag(1) + tag(0)
    base = args.output / "base.swf"
    base.write_bytes(b"FWS" + bytes([8]) + struct.pack("<I", len(body) + 8) + body)
    sources = Path(__file__).parent / "as2/callback_registry"
    output = args.output / "registry.swf"
    with (args.output / "build.log").open("w") as stream:
        subprocess.run(["java", "-Djava.awt.headless=true", "-jar", str(args.ffdec),
                        "-importScript", str(base), str(output), str(sources)],
                       check=True, stdout=stream, stderr=subprocess.STDOUT)
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    report = {"status": "built_not_run", "ffdec_sha256": sha(args.ffdec),
              "swf_sha256": sha(output), "source_sha256": {
                  str(path.relative_to(sources)): sha(path) for path in sorted(sources.rglob("*.as"))}}
    (args.output / "build.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
