from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT_MARKERS = ("AGENTS.md", "README.md", ".agents")


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if all((candidate / marker).exists() for marker in ROOT_MARKERS):
            return candidate
    raise SystemExit("Could not locate CodexResearchDesk root. Run from inside the repository.")


def resolve_tool(name: str, root: Path | None = None) -> Path:
    repo = root or find_repo_root()
    candidate = repo / "tools" / name
    if not candidate.exists():
        raise SystemExit(f"Tool not found: {candidate}")
    return candidate


def resolve_skill(name: str, root: Path | None = None) -> Path:
    repo = root or find_repo_root()
    candidate = repo / ".agents" / "skills" / name
    if not (candidate / "SKILL.md").exists():
        raise SystemExit(f"Skill not found: {candidate}")
    return candidate


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve CodexResearchDesk bundled ARIS paths.")
    parser.add_argument("kind", choices=("root", "tool", "skill"))
    parser.add_argument("name", nargs="?")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    root = find_repo_root()
    if args.kind == "root":
        result = root
    elif args.kind == "tool":
        if not args.name:
            raise SystemExit("tool resolution requires a name")
        result = resolve_tool(args.name, root)
    else:
        if not args.name:
            raise SystemExit("skill resolution requires a name")
        result = resolve_skill(args.name, root)

    if args.json:
        print(json.dumps({"path": str(result)}, ensure_ascii=False))
    else:
        print(result)


if __name__ == "__main__":
    main()
