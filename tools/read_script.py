"""Read exact paths or search literal text in a retained AS2 script bundle."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--path", help="Exact source path within the bundle")
    selection.add_argument("--search", help="Case-sensitive literal in path or source")
    parser.add_argument("--limit", type=int, default=5, help="Maximum search results (default 5)")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")
    try:
        data = json.loads(args.bundle.read_text(encoding="utf-8"))
        if data.get("format") != "bvn26-as2-scripts-v1":
            raise ValueError("Unsupported script bundle format")
        scripts = data["scripts"]
        matches = [s for s in scripts if s["path"] == args.path] if args.path else [
            s for s in scripts if args.search in s["source"] or args.search in s["path"]
        ]
        if not matches:
            print("No matching script", file=sys.stderr)
            return 1
        if args.path:
            # Do not add a header to exact-path output; it can be redirected to .as.
            sys.stdout.buffer.write(matches[0]["source"].encode("utf-8"))
        else:
            for script in matches[:args.limit]:
                print(f"\n// {args.bundle} :: {script['path']}")
                print(script["source"])
            print(f"Shown {min(len(matches), args.limit)} of {len(matches)} matches", file=sys.stderr)
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
