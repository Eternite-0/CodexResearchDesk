from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from decision_gate import check_decision, latest_decision


REMOVE = object()


def write_decision(root: Path, idea_id: str, verdict: str, **extra) -> Path:
    folder = root / idea_id
    folder.mkdir(parents=True, exist_ok=True)

    allowed_next_actions = {
        "GO": ["bounded GPU experiment"],
        "STATIC_ONLY": ["literature review"],
        "NEEDS_MORE_EVIDENCE": [],
        "NO_GO": [],
        "USER_OVERRIDE": ["bounded GPU experiment"],
    }.get(verdict, [])
    blocking_reasons = {
        "GO": [],
        "STATIC_ONLY": ["experiment work is blocked for test"],
        "NEEDS_MORE_EVIDENCE": [],
        "NO_GO": ["blocked for test"],
        "USER_OVERRIDE": ["blocked unless override is accepted"],
    }.get(verdict, [])

    data = {
        "idea_id": idea_id,
        "project_id": "test-project",
        "title": idea_id,
        "verdict": verdict,
        "confidence": "medium",
        "max_gpu_hours_allowed": 1 if verdict in {"GO", "USER_OVERRIDE"} else 0,
        "allowed_next_actions": allowed_next_actions,
        "blocking_reasons": blocking_reasons,
        "memo_md": f"decisions/{idea_id}/DECISION_MEMO.md",
        "memo_pdf": f"output/pdf/{idea_id}_decision_memo.pdf",
        "created_at": extra.pop("created_at", "2026-06-13T00:00:00Z"),
    }
    if verdict == "NEEDS_MORE_EVIDENCE":
        data["evidence_gaps"] = ["missing evidence for test"]

    for key, value in extra.items():
        if value is REMOVE:
            data.pop(key, None)
        else:
            data[key] = value

    path = folder / "decision.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class DecisionGateTests(unittest.TestCase):
    def test_legacy_decision_json_compatibility(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_decision(
                Path(tmp),
                "legacy-static",
                "STATIC_ONLY",
                allowed_next_actions=["literature review", "static protocol analysis"],
                blocking_reasons=["legacy blocker"],
            )
            result = check_decision(path, mode="static")
            self.assertTrue(result.allowed)

    def test_go_allows_experiment_with_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_decision(Path(tmp), "go", "GO", max_gpu_hours_allowed=2)
            result = check_decision(path, mode="experiment")
            self.assertTrue(result.allowed)

    def test_go_requires_resource_budget_when_experiment_actions_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_decision(
                Path(tmp),
                "go-no-budget",
                "GO",
                max_gpu_hours_allowed=REMOVE,
                resource_budget=REMOVE,
                allowed_next_actions=["GPU pilot"],
            )
            result = check_decision(path, mode="experiment")
            self.assertFalse(result.allowed)
            self.assertEqual(result.verdict, "INVALID")
            self.assertIn("GO requires resource_budget", result.reason)

    def test_static_only_blocks_experiment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_decision(Path(tmp), "static", "STATIC_ONLY")
            result = check_decision(path, mode="experiment")
            self.assertFalse(result.allowed)
            self.assertEqual(result.verdict, "STATIC_ONLY")

    def test_static_only_with_static_actions_allows_static(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_decision(Path(tmp), "static", "STATIC_ONLY", allowed_next_actions=["文献查新"])
            result = check_decision(path, mode="static")
            self.assertTrue(result.allowed)

    def test_static_only_requires_static_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_decision(Path(tmp), "static", "STATIC_ONLY", allowed_next_actions=["write paper"])
            result = check_decision(path, mode="static")
            self.assertFalse(result.allowed)
            self.assertEqual(result.verdict, "INVALID")
            self.assertIn("STATIC_ONLY requires", result.reason)

    def test_needs_more_evidence_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_decision(Path(tmp), "needs", "NEEDS_MORE_EVIDENCE")
            result = check_decision(path, mode="experiment")
            self.assertFalse(result.allowed)
            self.assertEqual(result.verdict, "NEEDS_MORE_EVIDENCE")

    def test_needs_more_evidence_requires_evidence_gaps_or_blocking_reasons(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_decision(Path(tmp), "needs", "NEEDS_MORE_EVIDENCE", evidence_gaps=[], blocking_reasons=[])
            result = check_decision(path, mode="experiment")
            self.assertFalse(result.allowed)
            self.assertEqual(result.verdict, "INVALID")
            self.assertIn("NEEDS_MORE_EVIDENCE requires", result.reason)

    def test_no_go_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_decision(Path(tmp), "no", "NO_GO")
            result = check_decision(path, mode="experiment")
            self.assertFalse(result.allowed)
            self.assertEqual(result.verdict, "NO_GO")

    def test_no_go_requires_blocking_reasons(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_decision(Path(tmp), "no", "NO_GO", blocking_reasons=[])
            result = check_decision(path, mode="experiment")
            self.assertFalse(result.allowed)
            self.assertEqual(result.verdict, "INVALID")
            self.assertIn("NO_GO requires", result.reason)

    def test_kill_tests_accepted_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_decision(
                Path(tmp),
                "static-with-kill-tests",
                "STATIC_ONLY",
                kill_tests=[
                    {
                        "test_name": "closest-prior-work check",
                        "hypothesis": "The claim is not already covered.",
                        "expected_cost": "2 hours, 0 GPU",
                        "pass_condition": "No direct overlap.",
                        "fail_condition": "Recent work already covers the claim.",
                        "decision_change_if_failed": "NO_GO",
                    }
                ],
            )
            result = check_decision(path, mode="static")
            self.assertTrue(result.allowed)
            self.assertEqual(result.data["kill_tests"][0]["decision_change_if_failed"], "NO_GO")

    def test_user_override_requires_flag_and_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_decision(Path(tmp), "override", "USER_OVERRIDE", override_reason="user accepted risk")
            blocked = check_decision(path, mode="experiment")
            allowed = check_decision(path, mode="experiment", allow_override=True)
            self.assertFalse(blocked.allowed)
            self.assertTrue(allowed.allowed)

    def test_missing_file_blocks(self) -> None:
        result = check_decision(Path("missing.json"), mode="experiment")
        self.assertFalse(result.allowed)
        self.assertEqual(result.verdict, "INVALID")

    def test_latest_uses_created_at(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = write_decision(root, "old", "NO_GO", created_at="2026-06-01T00:00:00Z")
            new = write_decision(root, "new", "GO", created_at="2026-06-13T00:00:00Z")
            self.assertEqual(latest_decision(root), new)
            self.assertNotEqual(latest_decision(root), old)

    def test_latest_accepts_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "projects" / "demo"
            decisions = project / "decisions"
            path = write_decision(decisions, "go", "GO")
            self.assertEqual(latest_decision(project), path)


if __name__ == "__main__":
    unittest.main()
