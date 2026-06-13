from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_VERDICTS = {
    "GO",
    "STATIC_ONLY",
    "NEEDS_MORE_EVIDENCE",
    "NO_GO",
    "USER_OVERRIDE",
}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}


@dataclass
class GateResult:
    allowed: bool
    verdict: str
    reason: str
    decision_path: Path | None
    data: dict[str, Any] | None = None

    def to_json(self) -> str:
        payload = {
            "allowed": self.allowed,
            "verdict": self.verdict,
            "reason": self.reason,
            "decision_path": str(self.decision_path) if self.decision_path else None,
            "data": self.data or {},
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def load_decision(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"decision file does not exist: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("decision JSON must be an object")
    return data


def validate_decision(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    verdict = data.get("verdict")
    confidence = data.get("confidence")
    if verdict not in ALLOWED_VERDICTS:
        errors.append(f"invalid verdict: {verdict!r}")
    if confidence not in ALLOWED_CONFIDENCE:
        errors.append(f"invalid confidence: {confidence!r}")
    if not data.get("idea_id"):
        errors.append("missing idea_id")
    if not data.get("project_id"):
        errors.append("missing project_id")
    if not data.get("memo_md"):
        errors.append("missing memo_md")
    if not data.get("memo_pdf"):
        errors.append("missing memo_pdf")
    if "blocking_reasons" in data and not isinstance(data["blocking_reasons"], list):
        errors.append("blocking_reasons must be a list")
    if "allowed_next_actions" in data and not isinstance(data["allowed_next_actions"], list):
        errors.append("allowed_next_actions must be a list")
    if "max_gpu_hours_allowed" in data:
        try:
            float(data["max_gpu_hours_allowed"])
        except (TypeError, ValueError):
            errors.append("max_gpu_hours_allowed must be numeric")
    return errors


def resolve_decisions_dir(path: Path) -> Path:
    if (path / "decisions").is_dir():
        return path / "decisions"
    return path


def latest_decision(decisions_dir: Path) -> Path:
    decisions_root = resolve_decisions_dir(decisions_dir)
    candidates = list(decisions_root.glob("*/decision.json"))
    if not candidates:
        raise ValueError(f"no decision.json files found under {decisions_root}")

    def sort_key(path: Path) -> tuple[float, float]:
        try:
            data = load_decision(path)
            created = parse_time(str(data.get("created_at", "")))
            created_ts = created.timestamp() if created else 0.0
        except Exception:
            created_ts = 0.0
        return (created_ts, path.stat().st_mtime)

    return max(candidates, key=sort_key)


def check_decision(path: Path, mode: str, allow_override: bool = False, max_age_days: int | None = None) -> GateResult:
    try:
        data = load_decision(path)
        errors = validate_decision(data)
    except Exception as exc:
        return GateResult(False, "INVALID", str(exc), path)

    if errors:
        return GateResult(False, "INVALID", "; ".join(errors), path, data)

    if max_age_days is not None:
        created = parse_time(str(data.get("created_at", "")))
        if not created:
            return GateResult(False, "INVALID", "created_at is missing or invalid", path, data)
        now = datetime.now(timezone.utc)
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age_days = (now - created).total_seconds() / 86400
        if age_days > max_age_days:
            return GateResult(False, data["verdict"], f"decision is stale: {age_days:.1f} days old", path, data)

    verdict = data["verdict"]
    reasons = data.get("blocking_reasons") or []
    reason_text = "; ".join(str(item) for item in reasons) if reasons else "no blocking reason recorded"

    if verdict == "GO":
        return GateResult(True, verdict, "GO permits experiment and static work", path, data)
    if verdict == "STATIC_ONLY":
        if mode == "static":
            return GateResult(True, verdict, "STATIC_ONLY permits static work only", path, data)
        return GateResult(False, verdict, "STATIC_ONLY blocks experiment work", path, data)
    if verdict == "USER_OVERRIDE":
        override_reason = str(data.get("override_reason", "")).strip()
        if allow_override and override_reason:
            return GateResult(True, verdict, f"USER_OVERRIDE accepted: {override_reason}", path, data)
        return GateResult(False, verdict, "USER_OVERRIDE requires --allow-override and override_reason", path, data)
    if verdict in {"NEEDS_MORE_EVIDENCE", "NO_GO"}:
        return GateResult(False, verdict, reason_text, path, data)
    return GateResult(False, "INVALID", f"unhandled verdict: {verdict}", path, data)


def print_result(result: GateResult, as_json: bool) -> None:
    if as_json:
        print(result.to_json())
    else:
        status = "ALLOW" if result.allowed else "BLOCK"
        print(f"{status}: {result.verdict} - {result.reason}")
        if result.decision_path:
            print(result.decision_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether a research idea may enter the requested stage.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Check a specific decision.json file.")
    check.add_argument("decision_json", type=Path)
    check.add_argument("--mode", choices=("experiment", "static"), default="experiment")
    check.add_argument("--allow-override", action="store_true")
    check.add_argument("--max-age-days", type=int)
    check.add_argument("--json", action="store_true")

    latest = subparsers.add_parser("latest", help="Check the newest decision under a project root or decisions directory.")
    latest.add_argument("project_or_decisions_dir", type=Path)
    latest.add_argument("--mode", choices=("experiment", "static"), default="experiment")
    latest.add_argument("--allow-override", action="store_true")
    latest.add_argument("--max-age-days", type=int)
    latest.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.command == "latest":
        try:
            decision_path = latest_decision(args.project_or_decisions_dir)
        except Exception as exc:
            result = GateResult(False, "MISSING", str(exc), None)
            print_result(result, args.json)
            return 2
    else:
        decision_path = args.decision_json

    result = check_decision(decision_path, args.mode, args.allow_override, args.max_age_days)
    print_result(result, args.json)
    return 0 if result.allowed else 2


if __name__ == "__main__":
    sys.exit(main())
