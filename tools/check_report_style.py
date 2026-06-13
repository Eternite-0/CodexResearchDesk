from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ENGLISH_BOILERPLATE = [
    "Decision Memo",
    "Executive Decision",
    "Premise Check",
    "First-Principles Decomposition",
    "Multi-Perspective Reasoning",
    "PI / Advisor View",
    "Resource Manager View",
    "Skeptical Reviewer View",
    "Evidence Ledger",
    "Critical Evaluation",
    "Lowest-Cost Kill Test",
    "Resource Budget",
    "Recommended Research Narrowing",
    "Final Gate",
    "Self-Audit",
    "Advantages",
    "Weaknesses / Risks",
    "Failure Modes",
]

ENGLISH_TABLE_HEADERS = [
    "| Item | Assessment |",
    "| Question | Answer |",
    "| Type | Evidence | Strength | Notes |",
    "| Item | Plan |",
    "| Stage | Allowed? | Budget | Notes |",
]

ENGLISH_LABELS = [
    "Decision",
    "Reason",
    "User premise",
    "Correction needed?",
    "Evidence status",
    "Retrieval used",
    "Upside",
    "Concern",
    "Decision pressure",
    "Information gained per cost",
    "Resource risk",
    "Stop condition",
    "Strongest objection",
    "Likely rejection reason",
    "Required evidence",
    "Test type",
    "Inputs",
    "Metric / observable",
    "Pass condition",
    "Kill condition",
    "Estimated cost",
    "Topic fit",
    "Factual accuracy",
    "Logic closure",
    "Overclaim check",
]


def strip_fenced_blocks(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def check_text(text: str, path: Path | None = None) -> list[str]:
    body = strip_fenced_blocks(text)
    errors: list[str] = []
    source = str(path) if path else "<text>"

    for lineno, line in enumerate(body.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue

        heading = re.sub(r"^#+\s*", "", stripped).strip()
        for phrase in ENGLISH_BOILERPLATE:
            if heading == phrase:
                errors.append(f"{source}:{lineno}: English report heading remains: {phrase}")

        compact = re.sub(r"\s+", " ", stripped)
        for header in ENGLISH_TABLE_HEADERS:
            if compact == header:
                errors.append(f"{source}:{lineno}: English table header remains: {header}")

        label_match = re.match(r"^-?\s*(?:\*\*)?([A-Za-z][A-Za-z /?-]+)(?:\*\*)?\s*[:：]", stripped)
        if label_match:
            label = label_match.group(1).strip()
            if label in ENGLISH_LABELS:
                errors.append(f"{source}:{lineno}: English list/table label remains: {label}")

    return errors


def check_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8-sig")
    return check_text(text, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Chinese research reports for English boilerplate leftovers.")
    parser.add_argument("files", nargs="+", type=Path, help="Markdown files to check.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    for path in args.files:
        errors.extend(check_file(path))

    if errors:
        for error in errors:
            print(error)
        return 2

    print("Report style check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
