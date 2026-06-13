from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from decision_gate import check_decision, latest_decision


def write_decision(root: Path, idea_id: str, verdict: str, **extra) -> Path:
    folder = root / idea_id
    folder.mkdir(parents=True, exist_ok=True)
    data = {
        "idea_id": idea_id,
        "project_id": "test-project",
        "title": idea_id,
        "verdict": verdict,
        "confidence": "medium",
        "max_gpu_hours_allowed": 0,
        "allowed_next_actions": [],
        "blocking_reasons": ["blocked for test"],
        "memo_md": f"decisions/{idea_id}/DECISION_MEMO.md",
        "memo_pdf": f"output/pdf/{idea_id}_decision_memo.pdf",
        "created_at": extra.pop("created_at", "2026-06-13T00:00:00Z"),
    }
    data.update(extra)
    path = folder / "decision.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class DecisionGateTests(unittest.TestCase):
    def test_go_allows_experiment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_decision(Path(tmp), "go", "GO")
            result = check_decision(path, mode="experiment")
            self.assertTrue(result.allowed)

    def test_static_only_blocks_experiment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_decision(Path(tmp), "static", "STATIC_ONLY")
            result = check_decision(path, mode="experiment")
            self.assertFalse(result.allowed)
            self.assertEqual(result.verdict, "STATIC_ONLY")

    def test_static_only_allows_static(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_decision(Path(tmp), "static", "STATIC_ONLY")
            result = check_decision(path, mode="static")
            self.assertTrue(result.allowed)

    def test_needs_more_evidence_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_decision(Path(tmp), "needs", "NEEDS_MORE_EVIDENCE")
            result = check_decision(path, mode="experiment")
            self.assertFalse(result.allowed)

    def test_no_go_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_decision(Path(tmp), "no", "NO_GO")
            result = check_decision(path, mode="experiment")
            self.assertFalse(result.allowed)

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
