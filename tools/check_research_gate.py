from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TRAINING_TERMS = [
    "微调",
    "训练",
    "SFT",
    "LoRA",
    "QLoRA",
    "DPO",
    "GRPO",
    "RLHF",
    "post-training",
    "fine-tuning",
    "adapter",
    "merge",
    "合并",
    "量化",
    "部署",
]

ENGINEERING_SECTIONS = [
    "工程现实检查",
    "工程失败信号",
    "路线分叉",
    "兼容性风险",
    "最小 A/B",
    "最可能错在哪里",
]

FAILURE_TERMS = [
    "失败",
    "负面信号",
    "bad case",
    "bad output",
    "abnormal",
    "issue",
    "issues",
    "讨论",
    "日志",
    "输出异常",
    "效果差",
    "not working",
    "退化",
]

ROUTE_SPLIT_TERMS = [
    "base vs instruct",
    "base",
    "instruct",
    "direct",
    "merge",
    "transfer",
    "迁移",
    "合并",
    "prompt-only",
    "SFT vs",
    "DPO",
]

COMPATIBILITY_TERMS = [
    "tokenizer",
    "embedding",
    "chat template",
    "special tokens",
    "target_modules",
    "层名",
    "adapter",
    "rope",
    "parser",
]

AB_TERMS = [
    "A/B",
    "ablation",
    "对照",
    "baseline",
    "kill test",
    "0-GPU",
    "静态检查",
]

MODEL_SPEC_TERMS = [
    "checkpoint",
    "checkpoints",
    "model id",
    "model_id",
    "repo id",
    "repo_id",
    "huggingface",
    "modelscope",
    "revision",
    "commit",
    "sha",
    "hash",
    "权重",
    "检查点",
    "模型仓库",
    "仓库地址",
    "模型版本",
    "版本号",
    "基座路径",
]

GENERIC_MODEL_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\b\d+\s*[bB]\s+(?:chat|instruct)\s+model\b",
        r"\b\d+\s*[bB]\s*(?:chat|instruct)?\s*模型\b",
        r"目标\s*(?:\d+\s*[bB]\s*)?(?:chat|instruct)?\s*基座",
        r"目标\s*(?:\d+\s*[bB]\s*)?(?:chat|instruct)?\s*模型",
        r"某个\s*(?:\d+\s*[bB]\s*)?(?:chat|instruct)?\s*模型",
        r"一个\s*(?:\d+\s*[bB]\s*)?(?:chat|instruct)?\s*模型",
    ]
]

MODEL_ID_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"\b[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\b",
        r"\b(?:Qwen|Llama|Llama-3|Llama-4|DeepSeek|Yi|Baichuan|ChatGLM|InternLM|Mistral|Gemma|Phi)[A-Za-z0-9_.:/-]*\b",
    ]
]

MODEL_SPEC_LINE_TERMS = [
    "目标模型",
    "目标基座",
    "基座模型",
    "model id",
    "model_id",
    "repo id",
    "repo_id",
    "checkpoint",
    "checkpoints",
    "权重",
    "检查点",
    "模型仓库",
    "仓库地址",
    "模型版本",
    "版本号",
    "基座路径",
]

EVAL_SPEC_TERMS = [
    "评测",
    "评价",
    "指标",
    "metric",
    "metrics",
    "rubric",
    "评分",
    "打分",
    "benchmark",
    "基准",
    "数据集",
    "eval set",
    "holdout",
    "样例",
    "测试集",
    "拒答",
    "引用",
    "准确率",
    "幻觉率",
    "pass_condition",
    "fail_condition",
    "失败条件",
]

HIGH_RISK_DOMAIN_TERMS = [
    "法律",
    "法条",
    "司法",
    "法院",
    "律师",
    "合同",
    "医疗",
    "医学",
    "临床",
    "诊断",
    "药物",
    "金融",
    "投资",
    "信贷",
    "保险",
]

HIGH_RISK_BOUNDARY_TERMS = [
    "辖区",
    "时效",
    "日期",
    "引用",
    "来源",
    "法条",
    "拒答",
    "追问",
    "错前提",
    "免责声明",
    "越权",
    "安全边界",
    "citation",
    "jurisdiction",
    "refusal",
    "abstain",
]


def strip_fenced_blocks(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def has_any(text: str, terms: list[str]) -> bool:
    low = text.lower()
    for term in terms:
        if term.lower() in low:
            return True
    return False


def has_pattern(text: str, patterns: list[re.Pattern[str]]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def line_hits(text: str, terms: list[str]) -> list[str]:
    hits: list[str] = []
    low_terms = [term.lower() for term in terms]
    for lineno, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        if any(term in low for term in low_terms):
            hits.append(f"{lineno}: {line.strip()}")
    return hits


def has_concrete_model_spec(text: str) -> bool:
    low_terms = [term.lower() for term in MODEL_SPEC_LINE_TERMS]
    for line in text.splitlines():
        low = line.lower()
        if not any(term in low for term in low_terms):
            continue
        if has_any(line, MODEL_SPEC_TERMS) or has_pattern(line, MODEL_ID_PATTERNS):
            return True
    return False


def check_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    body = strip_fenced_blocks(text)
    errors: list[str] = []
    source = str(path)

    training_relevant = has_any(body, TRAINING_TERMS)
    if not training_relevant:
        return errors

    if not has_any(body, ENGINEERING_SECTIONS):
        errors.append(
            f"{source}: training/deployment terms detected but no engineering gate section "
            "(工程现实检查 / 工程失败信号 / 路线分叉 / 最可能错在哪里)."
        )

    if not has_any(body, FAILURE_TERMS):
        errors.append(
            f"{source}: training/deployment route lacks failure evidence terms "
            "(issues, bad case, 输出异常, 效果差, 退化, etc.)."
        )

    if not has_any(body, ROUTE_SPLIT_TERMS):
        errors.append(
            f"{source}: training/deployment route lacks route-split terms "
            "(base vs instruct, direct vs merge/transfer, prompt-only vs training)."
        )

    if not has_any(body, COMPATIBILITY_TERMS):
        errors.append(
            f"{source}: training/deployment route lacks compatibility terms "
            "(tokenizer, embedding, chat template, target_modules, parser, etc.)."
        )

    if not has_any(body, AB_TERMS):
        errors.append(
            f"{source}: training/deployment route lacks minimal A/B or kill-test terms."
        )

    generic_model = has_pattern(body, GENERIC_MODEL_PATTERNS)
    concrete_model = has_concrete_model_spec(body)
    if generic_model and not concrete_model:
        errors.append(
            f"{source}: training/deployment route names a generic model target "
            "(for example '14B chat model') but lacks a concrete checkpoint/repo/version/path."
        )

    if not has_any(body, EVAL_SPEC_TERMS):
        errors.append(
            f"{source}: training/deployment route lacks evaluation specificity "
            "(rubric, metrics, benchmark, holdout set, sample table, pass/fail conditions)."
        )

    if has_any(body, HIGH_RISK_DOMAIN_TERMS) and not has_any(body, HIGH_RISK_BOUNDARY_TERMS):
        errors.append(
            f"{source}: high-risk domain route lacks boundary-condition terms "
            "(jurisdiction/time/source/citation/refusal/wrong-premise/safety boundary)."
        )

    if errors:
        hits = line_hits(body, TRAINING_TERMS)[:8]
        if hits:
            errors.append(f"{source}: triggering lines:\n  " + "\n  ".join(hits))

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Mechanical research gate for CodexResearchDesk artifacts. "
            "Fails training/deployment reports that lack engineering failure, "
            "route split, compatibility, and A/B evidence."
        )
    )
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

    print("Research gate check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
