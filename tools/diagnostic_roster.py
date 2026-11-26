"""Use selection-screen labels for diagnostics without changing source or replay IDs."""
import json
from pathlib import Path


def actor_names(project: Path) -> dict[str, str]:
    selection = project / "generated/main/character_selection"
    footer = json.loads((selection / "footer.json").read_text())
    available = json.loads((selection / "available.json").read_text())
    names = {}
    for kind, group in (("fighter", "fighters"), ("helper", "helpers")):
        for source, slug in available[group].items():
            label = footer[source]["text"]
            names[f"{kind}:{source}"] = label
            directory = "forms" if group == "fighters" and slug in available.get("forms", {}) else group
            names[f"res://generated/{directory}/{slug}"] = label
    for combat in (project / "generated/forms").glob("*/combat.json"):
        path = f"res://generated/forms/{combat.parent.name}"
        source = json.loads(combat.read_text())["fighter_id"]
        names.setdefault(path, names.get(f"fighter:{source}", source))
    return names


def publish(project: Path, output: Path) -> None:
    script = (project / "web/crash_archive.js").read_text()
    marker = "/* BVN_DIAGNOSTIC_NAMES */ {}"
    if script.count(marker) != 1:
        raise ValueError("Missing diagnostic roster marker")
    script = script.replace(marker, json.dumps(actor_names(project), ensure_ascii=False, sort_keys=True))
    (output / "crash_archive.js").write_text(script)
    (output / "diagnostics.html").write_bytes((project / "web/diagnostics.html").read_bytes())
