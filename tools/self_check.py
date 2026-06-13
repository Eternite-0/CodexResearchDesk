from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_SKILLS = [
    "research-desk",
    "decision-memo",
    "preflight-gate",
    "aris-runner",
    "research-lit",
    "arxiv",
    "openalex",
    "semantic-scholar",
    "deepxiv",
    "novelty-check",
    "research-review",
    "kill-argument",
    "research-wiki",
    "wiki-enrich",
    "experiment-plan",
    "experiment-bridge",
    "run-experiment",
    "monitor-experiment",
    "result-to-claim",
    "citation-audit",
    "paper-claim-audit",
    "paper-plan",
]

REQUIRED_TOOLS = [
    "aris_tool_resolver.py",
    "arxiv_fetch.py",
    "decision_gate.py",
    "openalex_fetch.py",
    "render_markdown_pdf.py",
    "research_wiki.py",
    "semantic_scholar_fetch.py",
    "threat_scan.py",
]

SAMPLE_PROJECT = ROOT / "projects" / "sae-moe-interpretability"

REQUIRED_PACKAGES = [
    "reportlab",
    "pypdf",
    "fitz",
    "PIL",
    "requests",
    "yaml",
]


def check(condition: bool, ok: str, fail: str, errors: list[str]) -> None:
    if condition:
        print(f"OK   {ok}")
    else:
        print(f"FAIL {fail}")
        errors.append(fail)


def contains_forbidden_path(path: Path, needle: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return needle in text


def main() -> int:
    errors: list[str] = []

    check((ROOT / "AGENTS.md").exists(), "AGENTS.md exists", "AGENTS.md missing", errors)
    check((ROOT / ".agents" / "skills").exists(), ".agents/skills exists", ".agents/skills missing", errors)
    check((ROOT / "projects").exists(), "projects directory exists", "projects directory missing", errors)
    check(SAMPLE_PROJECT.exists(), "sample project exists", "sample project missing", errors)
    check((SAMPLE_PROJECT / "decisions").exists(), "sample project decisions exists", "sample project decisions missing", errors)
    check((SAMPLE_PROJECT / "research-wiki").exists(), "sample project wiki exists", "sample project wiki missing", errors)
    check((SAMPLE_PROJECT / "output" / "pdf").exists(), "sample project pdf output exists", "sample project pdf output missing", errors)
    check((SAMPLE_PROJECT / "tmp" / "pdfs").exists(), "sample project preview output exists", "sample project preview output missing", errors)
    check(
        (SAMPLE_PROJECT / "decisions" / "sae-moe-routing-saes" / "decision.json").exists(),
        "sample project decision.json exists",
        "sample project decision.json missing",
        errors,
    )

    for skill in REQUIRED_SKILLS:
        path = ROOT / ".agents" / "skills" / skill / "SKILL.md"
        check(path.exists(), f"skill {skill}", f"missing skill: {skill}", errors)

    check((ROOT / ".agents" / "skills" / "shared-references").exists(), "shared-references exists", "shared-references missing", errors)

    for tool in REQUIRED_TOOLS:
        path = ROOT / "tools" / tool
        check(path.exists(), f"tool {tool}", f"missing tool: {tool}", errors)

    for package in REQUIRED_PACKAGES:
        check(importlib.util.find_spec(package) is not None, f"python package {package}", f"missing python package: {package}", errors)

    text_files = [
        *ROOT.glob("*.md"),
        *ROOT.glob("*.txt"),
        *ROOT.glob("*.py"),
        *ROOT.glob("*.json"),
        *ROOT.glob("*.yaml"),
        *ROOT.glob("*.yml"),
        *ROOT.glob("**/*.md"),
        *ROOT.glob("**/*.py"),
        *ROOT.glob("**/*.json"),
        *ROOT.glob("**/*.yaml"),
        *ROOT.glob("**/*.yml"),
    ]
    forbidden_path = "D:" + "\\AutoResearch"
    leaked = sorted({str(path.relative_to(ROOT)) for path in text_files if contains_forbidden_path(path, forbidden_path)})
    check(not leaked, "no local upstream checkout path leaks", f"absolute path leaks: {leaked}", errors)

    if errors:
        print("\nSelf-check failed.")
        return 2

    print("\nSelf-check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
