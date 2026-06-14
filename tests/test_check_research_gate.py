from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from check_research_gate import check_file


class CheckResearchGateTests(unittest.TestCase):
    def check_text(self, text: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.md"
            path.write_text(text, encoding="utf-8")
            return check_file(path)

    def test_generic_training_model_target_is_rejected(self) -> None:
        errors = self.check_text(
            """
# 14B chat 模型 QLoRA 法律问答

## 最可能错在哪里

目标 14B chat 模型可能在法律问答中退化。

## 工程失败信号

已有 issue 显示 LoRA merge 失败、输出异常和效果差。

## 路线分叉

比较 base vs instruct、direct merge transfer 和 prompt-only baseline。

## 兼容性风险

检查 tokenizer、chat template、special tokens、embedding、target_modules、adapter 和 parser。

## 最小 A/B

用 0-GPU 静态检查和 A/B 对照，含法律辖区、时效、引用、拒答、错前提样例，失败条件为幻觉率高。
"""
        )
        self.assertTrue(any("generic model target" in error for error in errors))

    def test_concrete_model_target_passes_specificity_gate(self) -> None:
        errors = self.check_text(
            """
# 具体模型 QLoRA 法律问答

## 最可能错在哪里

目标模型 checkpoint：Qwen/Qwen2.5-14B-Instruct，revision：abc123。

## 工程失败信号

已有 issue 显示 LoRA merge 失败、输出异常和效果差。

## 路线分叉

比较 base vs instruct、direct merge transfer 和 prompt-only baseline。

## 兼容性风险

检查 tokenizer、chat template、special tokens、embedding、target_modules、adapter 和 parser。

## 最小 A/B

用 0-GPU 静态检查和 A/B 对照，含法律辖区、时效、引用、拒答、错前提样例，失败条件为幻觉率高。
"""
        )
        self.assertEqual(errors, [])

    def test_training_report_requires_evaluation_specificity(self) -> None:
        errors = self.check_text(
            """
# 具体模型 LoRA 微调

## 最可能错在哪里

目标模型 checkpoint：Qwen/Qwen2.5-14B-Instruct，revision：abc123。

## 工程失败信号

已有 issue 显示 LoRA merge 失败、输出异常和效果差。

## 路线分叉

比较 base vs instruct、direct merge transfer 和 prompt-only。

## 兼容性风险

检查 tokenizer、chat template、special tokens、embedding、target_modules、adapter 和 parser。
"""
        )
        self.assertTrue(any("evaluation specificity" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
