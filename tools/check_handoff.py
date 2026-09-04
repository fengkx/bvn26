"""Check local documentation links, task dependencies and coverage against baseline."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def main():
    errors = []
    manifest = load("manifest.json")
    plan = load("plan/tasks.json")
    tasks = plan["tasks"]
    by_id = {task["id"]: task for task in tasks}
    if len(by_id) != len(tasks):
        errors.append("Duplicate task ID")
    spec = (ROOT / "SPEC.md").read_text(encoding="utf-8")
    requirements = set(re.findall(r"\b(?:FR|TR)-\d{2}\b", spec))
    visiting, visited = set(), set()

    def visit(identifier):
        if identifier in visiting:
            raise ValueError("Task dependency cycle at " + identifier)
        if identifier in visited:
            return
        if identifier not in by_id:
            raise ValueError("Missing dependency: " + identifier)
        visiting.add(identifier)
        for dep in by_id[identifier]["depends_on"]:
            visit(dep)
        visiting.remove(identifier)
        visited.add(identifier)

    for task in tasks:
        identifier = task["id"]
        try:
            visit(identifier)
        except ValueError as error:
            errors.append(str(error))
        if task["status"] not in plan["status_values"]:
            errors.append(identifier + ": invalid status")
        if not set(task["requirements"]) <= requirements:
            errors.append(identifier + ": unknown requirement")
        if not task["outputs"] or not task["acceptance"]:
            errors.append(identifier + ": missing output or acceptance criteria")
        if task["status"] == "completed":
            if any(by_id.get(dep, {}).get("status") != "completed" for dep in task["depends_on"]):
                errors.append(identifier + ": completed despite incomplete dependency")
            if not task["evidence"]:
                errors.append(identifier + ": completed without evidence")
            for path in task["evidence"] + task["outputs"]:
                if not (ROOT / path).exists():
                    errors.append(identifier + ": missing completed artifact " + path)
    covered = {requirement for task in tasks for requirement in task["requirements"]}
    if requirements - covered:
        errors.append("Unassigned requirements: " + str(sorted(requirements - covered)))

    coverage = load("plan/coverage.json")
    for section, catalog_key in (("fighters", "fighter_catalog"), ("maps", "map_catalog")):
        identifiers = [item["id"] for item in coverage[section]]
        if len(identifiers) != len(set(identifiers)) or set(identifiers) != set(manifest[catalog_key]):
            errors.append(section + ": coverage does not match baseline catalog")

    docs = [ROOT / "README.md", ROOT / "SPEC.md", ROOT / "IMPLEMENTATION_PLAN.md", ROOT / "AGENTS.md"]
    docs += sorted((ROOT / "docs").glob("*.md"))
    link_count = 0
    for path in docs:
        source = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", source):
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                continue
            link_count += 1
            resolved = (path.parent / target.split("#", 1)[0]).resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.exists():
                errors.append(path.name + ": broken local link " + target)
        for identifier in re.findall(r"\b(?:M[0-7]|B)-\d{2}\b", source):
            if identifier not in by_id:
                errors.append(path.name + ": unknown task " + identifier)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(json.dumps({"status": "passed", "documents": len(docs), "local_links": link_count,
                      "tasks": len(tasks), "requirements": len(requirements),
                      "fighter_configs": len(coverage["fighters"]), "maps": len(coverage["maps"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
