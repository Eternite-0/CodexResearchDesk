from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


SEVERITY_ORDER = {"error": 0, "warning": 1, "review": 2}


@dataclass(frozen=True)
class Rule:
    rule_id: str
    severity: str
    pattern: str
    description: str
    suggestion: str


@dataclass(frozen=True)
class Finding:
    path: str
    line_number: int
    severity: str
    rule_id: str
    matched_text: str
    line: str
    suggestion: str


RULES = [
    Rule(
        "chat_residue",
        "error",
        r"(希望这对[您你]有帮助|如果[您你]想让我|请告诉我|随时(?:告诉|联系)|您说得完全正确|这是一个很好的观点)",
        "chatbot conversation residue remains in the report.",
        "删除对话式客套语，直接写事实、判断或下一步。",
    ),
    Rule(
        "assistant_opener",
        "error",
        r"^\s*(?:当然|没问题|好的|好问题)[！!，,]",
        "assistant-style opener remains in content.",
        "删除助手式开场，保留正文结论。",
    ),
    Rule(
        "ai_disclaimer",
        "error",
        r"(作为(?:一个|一名)?\s*(?:AI|人工智能)(?:语言模型|助手|模型)|我的知识截止|知识截止日期|根据我(?:最后的)?训练|截至我的知识|我无法(?:浏览|访问|获取).{0,12}(?:互联网|网页|实时))",
        "AI limitation disclaimer remains in the report.",
        "用已核验来源、证据缺口或低置信度说明替代 AI 免责声明。",
    ),
    Rule(
        "vague_authority",
        "warning",
        r"(专家认为|观察者指出|行业报告显示|业内人士认为|多方认为|一些批评者认为|有观点认为)",
        "vague authority attribution weakens evidence quality.",
        "给出具体论文、机构、数据或把它改成未核验观点。",
    ),
    Rule(
        "grand_significance",
        "warning",
        r"(至关重要|关键作用|持久影响|不可磨灭的印记|奠定(?:了)?(?:坚实的?)?基础|标志着.{0,18}(?:关键|重要).{0,8}(?:时刻|转变)|彰显(?:了)?(?:其)?(?:重要性|意义)|凸显(?:了)?(?:其)?(?:重要性|意义)|作为.{0,18}的证明|是.{0,18}的体现)",
        "inflated significance language may overstate the claim.",
        "改成可验证的作用、数据、范围或证据强度。",
    ),
    Rule(
        "promo_language",
        "warning",
        r"(深入探讨|不断演变的.{0,8}格局|充满活力|令人叹为观止|必游之地|丰富的文化底蕴|无缝(?:、|，|和|的)?|直观(?:的)?(?:体验|流程|界面)|追求卓越|革命性|开创性)",
        "promotional or generic AI-flavored wording appears.",
        "用具体对象、任务、指标或限制条件替代宣传腔。",
    ),
    Rule(
        "contrast_formula",
        "warning",
        r"(不仅仅?是.{0,40}而是|不只是.{0,40}而是)",
        "formulaic not-only-but framing appears.",
        "直接写核心判断，避免戏剧化二元对比。",
    ),
    Rule(
        "generic_positive_close",
        "warning",
        r"(未来.{0,12}(?:光明|充满希望)|激动人心的时代|向正确方向迈出(?:的)?(?:重要)?一步)",
        "generic optimistic closing weakens decision discipline.",
        "改成下一步证据、停止条件或门控结论。",
    ),
    Rule(
        "emoji",
        "warning",
        r"[\U0001F300-\U0001FAFF]",
        "emoji appears in a formal artifact.",
        "正式研究交付物中删除表情符号。",
    ),
    Rule(
        "transition_crutch",
        "review",
        r"(此外|然而|值得注意的是|值得一提的是|综上所述|总之)",
        "common transition crutch; acceptable when used sparingly.",
        "检查是否可以删除，或改成更具体的逻辑关系。",
    ),
    Rule(
        "uncited_research_claim",
        "review",
        r"(研究表明|已有研究显示|通常认为|普遍认为)",
        "broad evidence claim may need a citation or scoped wording.",
        "补充具体来源；若没有来源，改成推断或开放不确定性。",
    ),
]


def strip_fenced_blocks_preserving_lines(text: str) -> str:
    lines = text.splitlines()
    cleaned: list[str] = []
    in_fence = False
    for line in lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            cleaned.append("")
            continue
        cleaned.append("" if in_fence else line)
    return "\n".join(cleaned)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def check_text(text: str, path: Path | None = None) -> list[Finding]:
    source = str(path) if path else "<text>"
    body = strip_fenced_blocks_preserving_lines(text)
    findings: list[Finding] = []

    for line_number, line in enumerate(body.splitlines(), 1):
        if not line.strip():
            continue
        for rule in RULES:
            for match in re.finditer(rule.pattern, line, flags=re.IGNORECASE):
                matched_text = match.group(0).strip()
                findings.append(
                    Finding(
                        path=source,
                        line_number=line_number,
                        severity=rule.severity,
                        rule_id=rule.rule_id,
                        matched_text=matched_text,
                        line=line.strip(),
                        suggestion=rule.suggestion,
                    )
                )
    return findings


def check_file(path: Path) -> list[Finding]:
    return check_text(read_text(path), path)


def format_finding(finding: Finding) -> str:
    return (
        f"{finding.path}:{finding.line_number}: {finding.severity}: "
        f"{finding.rule_id}: {finding.matched_text}\n"
        f"  line: {finding.line}\n"
        f"  suggestion: {finding.suggestion}"
    )


def count_by_severity(findings: list[Finding]) -> dict[str, int]:
    return {
        severity: sum(1 for finding in findings if finding.severity == severity)
        for severity in SEVERITY_ORDER
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Chinese research artifacts for chatbot residue, vague attribution, and AI-flavored filler."
    )
    parser.add_argument("files", nargs="+", type=Path, help="Markdown or text files to check.")
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Return a non-zero exit code when warning-level findings are present.",
    )
    parser.add_argument(
        "--hide-review",
        action="store_true",
        help="Hide review-level findings from the printed report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings: list[Finding] = []
    for path in args.files:
        findings.extend(check_file(path))

    visible_findings = [finding for finding in findings if not (args.hide_review and finding.severity == "review")]
    visible_findings.sort(key=lambda item: (item.path, item.line_number, SEVERITY_ORDER[item.severity], item.rule_id))

    counts = count_by_severity(findings)
    if not findings:
        print("AI style check passed.")
        return 0

    print(
        "AI style check found "
        f"{counts['error']} error(s), {counts['warning']} warning(s), {counts['review']} review item(s)."
    )
    for finding in visible_findings:
        print(format_finding(finding))

    if counts["error"] > 0:
        return 2
    if args.fail_on_warning and counts["warning"] > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
