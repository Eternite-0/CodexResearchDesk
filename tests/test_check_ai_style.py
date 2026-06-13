from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from check_ai_style import check_text


class CheckAiStyleTests(unittest.TestCase):
    def test_chat_residue_is_error(self) -> None:
        findings = check_text("当然！这是一个研究方向。希望这对您有帮助。")
        self.assertTrue(any(item.severity == "error" and item.rule_id == "chat_residue" for item in findings))
        self.assertTrue(any(item.severity == "error" and item.rule_id == "assistant_opener" for item in findings))

    def test_ai_flavored_filler_is_warning(self) -> None:
        findings = check_text("本研究深入探讨模型在不断演变的工业格局中的关键作用。")
        warnings = [item for item in findings if item.severity == "warning"]
        self.assertGreaterEqual(len(warnings), 1)

    def test_scientific_proof_word_is_not_flagged_by_itself(self) -> None:
        findings = check_text("该消融实验不能证明方法具有跨数据集泛化能力。")
        self.assertEqual(findings, [])

    def test_fenced_code_blocks_are_ignored(self) -> None:
        findings = check_text(
            "\n".join(
                [
                    "正文没有问题。",
                    "```text",
                    "当然！希望这对您有帮助。",
                    "```",
                ]
            )
        )
        self.assertEqual(findings, [])

    def test_broad_research_claim_is_review_only(self) -> None:
        findings = check_text("已有研究显示该指标和人工判断相关。")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "review")


if __name__ == "__main__":
    unittest.main()
