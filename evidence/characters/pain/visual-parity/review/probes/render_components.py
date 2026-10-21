import os
from pathlib import Path
import subprocess

for folder in sorted(
    Path(
        os.path.join(os.environ.get("BVN_REVIEW_DIR", "/tmp/pain-review"), "components")
    ).iterdir()
):
    if not (folder / "cases.json").exists():
        continue
    out = (
        Path(
            os.path.join(os.environ.get("BVN_REVIEW_DIR", "/tmp/pain-review"), "godot")
        )
        / folder.name
    )
    command = [
        os.environ["BVN_GODOT"],
        "--path",
        "godot",
        "--log-file",
        str(folder / "godot-engine.log"),
        "--quit-after",
        "1200",
        "-s",
        "res://tests/visual_component_reference.gd",
        "--",
        str(folder / "cases.json"),
        str(out),
    ]
    p = subprocess.run(command, capture_output=True, text=True, timeout=600)
    log = p.stdout + p.stderr
    (folder / "godot.log").write_text(log)
    print(
        folder.name,
        p.returncode,
        "ok" if "VISUAL_COMPONENT_REFERENCE_OK" in log else log[-2000:],
        flush=True,
    )
    if p.returncode or "SCRIPT ERROR" in log:
        raise SystemExit(1)
