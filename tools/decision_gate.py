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
ALLOWED_RISK_LEVELS = {"low", "medium", "high"}

STATIC_ACTION_KEYWORDS = {
    "static",
    "literature",
    "review",
    "survey",
    "checkpoint",
    "analysis",
    "audit",
    "probe",
    "non-training",
    "non training",
    "baseline check",
    "查新",
    "文献",
    "静态",
    "公开",
    "非训练",
    "分析",
    "复核",
    "审计",
    "补证",
}

EXPERIMENT_ACTION_KEYWORDS = {
    "experiment",
    "training",
    "train",
    "gpu",
    "pilot",
    "run-experiment",
    "experiment-bridge",
    "fine-tune",
    "finetune",
    "实验",
    "训练",
    "试验",
    "微调",
}


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


def nonempty_list(data: dict[str, Any], key: str) -> bool:
    value = data.get(key)
    if not isinstance(value, list):
        return False
    return any(str(item).strip() for item in value)


def action_texts(data: dict[str, Any]) -> list[str]:
    actions = data.get("allowed_next_actions")
    if not isinstance(actions, list):
        return []
    return [str(action).lower() for action in actions]


def has_keyword(texts: list[str], keywords: set[str]) -> bool:
    return any(keyword in text for text in texts for keyword in keywords)


def has_static_next_action(data: dict[str, Any]) -> bool:
    return has_keyword(action_texts(data), STATIC_ACTION_KEYWORDS)


def has_resource_budget(data: dict[str, Any]) -> bool:
    if "max_gpu_hours_allowed" in data:
        return True
    budget = data.get("resource_budget")
    if isinstance(budget, (dict, list)):
        return bool(budget)
    if isinstance(budget, str):
        return bool(budget.strip())
    return budget is not None


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
    if "blocked_actions" in data and not isinstance(data["blocked_actions"], list):
        errors.append("blocked_actions must be a list")
    if "top_risks" in data and not isinstance(data["top_risks"], list):
        errors.append("top_risks must be a list")
    if "evidence_gaps" in data and not isinstance(data["evidence_gaps"], list):
        errors.append("evidence_gaps must be a list")
    if "kill_tests" in data and not isinstance(data["kill_tests"], list):
        errors.append("kill_tests must be a list")
    if "main_claim" in data and not isinstance(data["main_claim"], str):
        errors.append("main_claim must be a string")
    if "next_review_condition" in data and not isinstance(data["next_review_condition"], str):
        errors.append("next_review_condition must be a string")
    if "external_signal_summary" in data and not isinstance(data["external_signal_summary"], str):
        errors.append("external_signal_summary must be a string")
    if "external_signal_ledger" in data and not isinstance(data["external_signal_ledger"], str):
        errors.append("external_signal_ledger must be a string")
    if "hype_risk" in data and data["hype_risk"] not in ALLOWED_RISK_LEVELS:
        errors.append("hype_risk must be one of low, medium, high")
    if "paper_code_summary" in data and not isinstance(data["paper_code_summary"], str):
        errors.append("paper_code_summary must be a string")
    if "paper_code_ledger" in data and not isinstance(data["paper_code_ledger"], str):
        errors.append("paper_code_ledger must be a string")
    if "code_availability_risk" in data and data["code_availability_risk"] not in ALLOWED_RISK_LEVELS:
        errors.append("code_availability_risk must be one of low, medium, high")
    if "risk_level" in data and data["risk_level"] not in ALLOWED_RISK_LEVELS:
        errors.append("risk_level must be one of low, medium, high")
    if "direction_score" in data:
        try:
            score = float(data["direction_score"])
            if score < 0 or score > 100:
                errors.append("direction_score must be between 0 and 100")
        except (TypeError, ValueError):
            errors.append("direction_score must be numeric")
    if "external_signal_score" in data:
        try:
            score = float(data["external_signal_score"])
            if score < 0 or score > 100:
                errors.append("external_signal_score must be between 0 and 100")
        except (TypeError, ValueError):
            errors.append("external_signal_score must be numeric")
    if "paper_code_trace_score" in data:
        try:
            score = float(data["paper_code_trace_score"])
            if score < 0 or score > 100:
                errors.append("paper_code_trace_score must be between 0 and 100")
        except (TypeError, ValueError):
            errors.append("paper_code_trace_score must be numeric")
    if "max_gpu_hours_allowed" in data:
        try:
            max_gpu_hours = float(data["max_gpu_hours_allowed"])
            if max_gpu_hours < 0:
                errors.append("max_gpu_hours_allowed must be non-negative")
        except (TypeError, ValueError):
            errors.append("max_gpu_hours_allowed must be numeric")
    if verdict == "STATIC_ONLY" and not has_static_next_action(data):
        errors.append("STATIC_ONLY requires at least one static allowed_next_actions item")
    if verdict == "NEEDS_MORE_EVIDENCE" and not (nonempty_list(data, "evidence_gaps") or nonempty_list(data, "blocking_reasons")):
        errors.append("NEEDS_MORE_EVIDENCE requires evidence_gaps or blocking_reasons")
    if verdict == "NO_GO" and not nonempty_list(data, "blocking_reasons"):
        errors.append("NO_GO requires blocking_reasons")
    if verdict == "GO" and not has_resource_budget(data):
        errors.append("GO requires resource_budget or max_gpu_hours_allowed")
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
