#!/usr/bin/env python3
"""Bridge CodexResearchDesk to the external ResearchSkillArena.

The bridge keeps temporal-holdout evaluation data outside this repository, but
lets Codex run the arena from the Desk workflow with one command per stage.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARENA_ROOT = Path(os.environ.get("RESEARCH_SKILL_ARENA", ROOT.parent / "ResearchSkillArena"))


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return sum(1 for line in f if line.strip())


def arena_root(args: argparse.Namespace) -> Path:
    return Path(args.arena_root or DEFAULT_ARENA_ROOT).resolve()


def require_arena(root: Path) -> Path:
    tool = root / "tools" / "temporal_holdout.py"
    if not tool.exists():
        raise SystemExit(
            "找不到 ResearchSkillArena。请确认路径存在，或设置 RESEARCH_SKILL_ARENA，"
            f"当前检查路径：{root}"
        )
    return tool


def arena_paths(root: Path, project: str, run: str) -> dict[str, Path]:
    return {
        "config": root / "tasks" / project / run / "config.json",
        "task_dir": root / "tasks" / project / run,
        "past_corpus": root / "tasks" / project / run / "past_corpus.jsonl",
        "future_corpus": root / "tasks" / project / run / "future_corpus.jsonl",
        "historical_prompt": root / "tasks" / project / run / "historical_idea_prompt.md",
        "submission_dir": root / "submissions" / project / run,
        "ideas_frozen": root / "submissions" / project / run / "IDEAS_FROZEN.md",
        "metadata": root / "submissions" / project / run / "metadata.json",
        "report_dir": root / "reports" / project / run,
        "ledger": root / "reports" / project / run / "hit_ledger.csv",
        "papers_cool_insights": root / "reports" / project / run / "papers_cool_insights.jsonl",
        "papers_cool_brief": root / "reports" / project / run / "papers_cool_review_brief.md",
        "papers_cool_triage_csv": root / "reports" / project / run / "papers_cool_triage.csv",
        "papers_cool_triage_md": root / "reports" / project / run / "papers_cool_triage.md",
        "report": root / "reports" / project / run / "TEMPORAL_HOLDOUT_REPORT.md",
        "pdf": root / "output" / "pdf" / f"{project}_{run}_temporal_holdout.pdf",
    }


def desk_link_path(project: str, run: str) -> Path:
    return ROOT / "projects" / project / "arena-links" / f"{run}.json"


def update_link(root: Path, project: str, run: str, stage: str, extra: dict[str, Any] | None = None) -> Path:
    paths = arena_paths(root, project, run)
    link = {
        "project": project,
        "run": run,
        "stage": stage,
        "arena_root": str(root),
        "updated_at": utc_now(),
        "note": "Only a lightweight link is stored in CodexResearchDesk. Corpora, ledgers, reports, and PDFs stay in ResearchSkillArena.",
        "paths": {name: str(path) for name, path in paths.items()},
    }
    if paths["config"].exists():
        try:
            config = json.loads(paths["config"].read_text(encoding="utf-8"))
            link["topic"] = config.get("topic")
            link["cutoff_year"] = config.get("cutoff_year")
            link["future_start"] = config.get("future_start")
            link["future_end"] = config.get("future_end")
            link["sources"] = config.get("sources")
            link["max_past"] = config.get("max_past")
            link["max_future"] = config.get("max_future")
        except Exception as exc:  # pragma: no cover - status metadata only
            link["config_read_error"] = str(exc)
    link["reproducibility"] = reproducibility_note(paths)
    if extra:
        link.update(extra)
    target = desk_link_path(project, run)
    json_dump(target, link)
    return target


def run_arena(root: Path, args: list[str]) -> None:
    tool = require_arena(root)
    command = [sys.executable, str(tool), *args]
    print("RUN " + " ".join(f'"{part}"' if " " in part else part for part in command))
    completed = subprocess.run(command, cwd=str(root), text=True, capture_output=True)
    if completed.stdout.strip():
        print(completed.stdout.strip())
    if completed.stderr.strip():
        print(completed.stderr.strip(), file=sys.stderr)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def run_arena_tool(root: Path, relative_tool: str, args: list[str]) -> None:
    tool = root / "tools" / relative_tool
    if not tool.exists():
        raise SystemExit(f"找不到 arena 工具：{tool}")
    command = [sys.executable, str(tool), *args]
    print("RUN " + " ".join(f'"{part}"' if " " in part else part for part in command))
    completed = subprocess.run(command, cwd=str(root), text=True, capture_output=True)
    if completed.stdout.strip():
        print(completed.stdout.strip())
    if completed.stderr.strip():
        print(completed.stderr.strip(), file=sys.stderr)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def run_papers_cool_enrichment(
    root: Path,
    project: str,
    run: str,
    *,
    max_papers: int,
    top_per_idea: int,
    refresh: bool,
    min_score: float,
) -> None:
    args = [
        "enrich-ledger",
        "--project",
        project,
        "--run",
        run,
        "--max-papers",
        str(max_papers),
        "--top-per-idea",
        str(top_per_idea),
        "--min-score",
        str(min_score),
    ]
    if refresh:
        args.append("--refresh")
    run_arena_tool(root, "papers_cool_fetch.py", args)


def run_papers_cool_triage(root: Path, project: str, run: str) -> None:
    run_arena_tool(root, "papers_cool_fetch.py", ["triage-ledger", "--project", project, "--run", run])


def read_ledger(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def ledger_summary(path: Path) -> dict[str, Any]:
    rows = read_ledger(path)
    labels: dict[str, int] = {}
    supports: dict[str, int] = {}
    reviewed = 0
    for row in rows:
        label = (row.get("reviewer_label") or "").strip() or "uncertain"
        support = (row.get("experiment_support") or "").strip() or "not_checked"
        labels[label] = labels.get(label, 0) + 1
        supports[support] = supports.get(support, 0) + 1
        if not (label == "uncertain" and support == "not_checked"):
            reviewed += 1
    return {
        "rows": len(rows),
        "reviewed_rows": reviewed,
        "labels": labels,
        "experiment_support": supports,
    }


def artifact_hashes(paths: dict[str, Path]) -> dict[str, dict[str, Any]]:
    tracked = [
        "config",
        "past_corpus",
        "historical_prompt",
        "ideas_frozen",
        "future_corpus",
        "ledger",
        "papers_cool_insights",
        "papers_cool_triage_csv",
        "papers_cool_triage_md",
        "report",
        "pdf",
    ]
    hashes: dict[str, dict[str, Any]] = {}
    for key in tracked:
        path = paths[key]
        if not path.exists():
            continue
        item: dict[str, Any] = {
            "path": str(path),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        if path.suffix.lower() in {".jsonl", ".csv", ".md"}:
            item["non_empty_lines"] = count_lines(path)
        hashes[key] = item
    return hashes


def reproducibility_note(paths: dict[str, Path]) -> dict[str, Any]:
    return {
        "deterministic_local_steps": [
            "candidate ledger scoring sorts by lexical-overlap score and candidate rank",
            "Papers.cool candidate selection groups by idea_id and sorts by match_score",
            "artifact hashes are recorded for rerun comparison",
        ],
        "external_variability": [
            "OpenAlex/Semantic Scholar/arXiv results can change over time",
            "Papers.cool/Kimi auxiliary interpretations can change unless cached",
        ],
        "hashes": artifact_hashes(paths),
    }


def print_status(root: Path, project: str, run: str) -> None:
    paths = arena_paths(root, project, run)
    print(f"项目：{project}")
    print(f"Run：{run}")
    print(f"Arena：{root}")
    print("")
    for label, key in [
        ("配置", "config"),
        ("过去语料", "past_corpus"),
        ("历史 prompt", "historical_prompt"),
        ("冻结 ideas", "ideas_frozen"),
        ("未来语料", "future_corpus"),
        ("命中账本", "ledger"),
        ("Papers.cool 解读", "papers_cool_brief"),
        ("Papers.cool 预筛", "papers_cool_triage_md"),
        ("报告", "report"),
        ("PDF", "pdf"),
    ]:
        path = paths[key]
        suffix = ""
        if key in {"past_corpus", "future_corpus"} and path.exists():
            suffix = f" ({count_lines(path)} 条)"
        if key == "ledger" and path.exists():
            summary = ledger_summary(path)
            suffix = f" ({summary['reviewed_rows']}/{summary['rows']} 行已审)"
        print(f"{label}：{'OK' if path.exists() else 'MISSING'}  {path}{suffix}")
    hashes = artifact_hashes(paths)
    if hashes:
        print("")
        print("可复现指纹：")
        for key in ["past_corpus", "ideas_frozen", "future_corpus", "ledger", "papers_cool_insights", "report"]:
            item = hashes.get(key)
            if item:
                print(f"- {key}: {item['sha256'][:12]}... ({item['bytes']} bytes)")
    print("")
    if not paths["config"].exists():
        print("下一步：运行 prepare。")
    elif not paths["past_corpus"].exists():
        print("下一步：运行 prepare --refresh-past，或检查 collect-past 失败原因。")
    elif not paths["ideas_frozen"].exists():
        print("下一步：只读取 historical_idea_prompt.md 和 past_corpus.jsonl，生成 IDEAS_FROZEN.md。")
    elif not paths["ledger"].exists():
        print("下一步：运行 make-ledger。")
    else:
        summary = ledger_summary(paths["ledger"])
        if not paths["papers_cool_brief"].exists():
            print("下一步：运行 enrich-cool 生成 Papers.cool/Kimi 辅助解读，或直接审阅 ledger。")
            return
        if not paths["papers_cool_triage_md"].exists():
            print("下一步：运行 triage-cool 生成 PDF 审阅优先级队列。")
            return
        if summary["rows"] and summary["reviewed_rows"] == 0:
            print("下一步：先读 papers_cool_triage.md，只对 yes/maybe 候选打开 PDF 核对实验图表。")
        elif not paths["report"].exists():
            print("下一步：运行 finalize-report。")
        else:
            print("下一步：阅读报告，决定是否要改 research workflow。")


def cmd_prepare(args: argparse.Namespace) -> int:
    root = arena_root(args)
    require_arena(root)
    paths = arena_paths(root, args.project, args.run)
    if not paths["config"].exists() or args.force_init:
        run_arena(
            root,
            [
                "init-run",
                "--project",
                args.project,
                "--run",
                args.run,
                "--topic",
                args.topic,
                "--cutoff-year",
                str(args.cutoff_year),
                "--future-start",
                str(args.future_start),
                "--future-end",
                str(args.future_end),
                "--sources",
                args.sources,
                "--max-past",
                str(args.max_past),
                "--max-future",
                str(args.max_future),
            ],
        )
    else:
        print(f"已有 arena config，跳过 init-run：{paths['config']}")

    if args.no_collect_past:
        print("按参数跳过 collect-past。")
    elif not paths["past_corpus"].exists() or args.refresh_past:
        run_arena(root, ["collect-past", "--project", args.project, "--run", args.run])
    else:
        print(f"已有 past_corpus，跳过 collect-past：{paths['past_corpus']}")

    link = update_link(root, args.project, args.run, "past_corpus_ready")
    print(f"Desk link：{link}")
    print_status(root, args.project, args.run)
    return 0


def cmd_submit_ideas(args: argparse.Namespace) -> int:
    root = arena_root(args)
    require_arena(root)
    paths = arena_paths(root, args.project, args.run)
    source = Path(args.ideas_file).resolve()
    if not source.exists():
        raise SystemExit(f"找不到 ideas 文件：{source}")
    if not paths["config"].exists():
        raise SystemExit(f"找不到 arena config，请先 prepare：{paths['config']}")
    if paths["ideas_frozen"].exists() and not args.force:
        raise SystemExit(f"IDEAS_FROZEN.md 已存在；如需覆盖，加 --force：{paths['ideas_frozen']}")

    paths["submission_dir"].mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, paths["ideas_frozen"])
    metadata = {
        "project": args.project,
        "run": args.run,
        "submitted_at": utc_now(),
        "skill": args.skill,
        "source_ideas_file": str(source),
        "source_sha256": sha256_file(source),
        "ideas_frozen": str(paths["ideas_frozen"]),
        "freeze_rule": "Do not edit IDEAS_FROZEN.md after future corpus collection starts.",
    }
    json_dump(paths["metadata"], metadata)
    link = update_link(root, args.project, args.run, "ideas_frozen", {"submission_metadata": str(paths["metadata"])})
    print(f"已冻结：{paths['ideas_frozen']}")
    print(f"Metadata：{paths['metadata']}")
    print(f"Desk link：{link}")
    return 0


def cmd_make_ledger(args: argparse.Namespace) -> int:
    root = arena_root(args)
    require_arena(root)
    paths = arena_paths(root, args.project, args.run)
    if not paths["ideas_frozen"].exists():
        raise SystemExit(f"缺少 IDEAS_FROZEN.md，请先 submit-ideas：{paths['ideas_frozen']}")
    if not paths["future_corpus"].exists() or args.refresh_future:
        run_arena(root, ["collect-future", "--project", args.project, "--run", args.run])
    else:
        print(f"已有 future_corpus，跳过 collect-future：{paths['future_corpus']}")
    run_arena(root, ["make-ledger", "--project", args.project, "--run", args.run, "--top-k", str(args.top_k)])
    if args.skip_cool:
        print("按参数跳过 Papers.cool/Kimi 辅助解读。")
    else:
        run_papers_cool_enrichment(
            root,
            args.project,
            args.run,
            max_papers=args.cool_max_papers,
            top_per_idea=args.cool_top_per_idea,
            refresh=args.refresh_cool,
            min_score=args.cool_min_score,
        )
    link = update_link(root, args.project, args.run, "ledger_ready")
    print(f"Desk link：{link}")
    print_status(root, args.project, args.run)
    return 0


def cmd_enrich_cool(args: argparse.Namespace) -> int:
    root = arena_root(args)
    require_arena(root)
    paths = arena_paths(root, args.project, args.run)
    if not paths["ledger"].exists():
        raise SystemExit(f"缺少 hit_ledger.csv，请先 make-ledger：{paths['ledger']}")
    run_papers_cool_enrichment(
        root,
        args.project,
        args.run,
        max_papers=args.max_papers,
        top_per_idea=args.top_per_idea,
        refresh=args.refresh,
        min_score=args.min_score,
    )
    link = update_link(root, args.project, args.run, "papers_cool_ready")
    print(f"Papers.cool 解读 JSONL：{paths['papers_cool_insights']}")
    print(f"Papers.cool 审阅简报：{paths['papers_cool_brief']}")
    print(f"Papers.cool 预筛：{paths['papers_cool_triage_md']}")
    print(f"Desk link：{link}")
    return 0


def cmd_triage_cool(args: argparse.Namespace) -> int:
    root = arena_root(args)
    require_arena(root)
    paths = arena_paths(root, args.project, args.run)
    if not paths["ledger"].exists():
        raise SystemExit(f"缺少 hit_ledger.csv，请先 make-ledger：{paths['ledger']}")
    if not paths["papers_cool_insights"].exists():
        raise SystemExit(f"缺少 papers_cool_insights.jsonl，请先 enrich-cool：{paths['papers_cool_insights']}")
    run_papers_cool_triage(root, args.project, args.run)
    link = update_link(root, args.project, args.run, "papers_cool_triage_ready")
    print(f"Papers.cool 预筛 CSV：{paths['papers_cool_triage_csv']}")
    print(f"Papers.cool 预筛 Markdown：{paths['papers_cool_triage_md']}")
    print(f"Desk link：{link}")
    return 0


def cmd_finalize_report(args: argparse.Namespace) -> int:
    root = arena_root(args)
    require_arena(root)
    paths = arena_paths(root, args.project, args.run)
    summary = ledger_summary(paths["ledger"])
    if not summary["rows"]:
        raise SystemExit(f"缺少 hit_ledger.csv，请先 make-ledger：{paths['ledger']}")
    if summary["reviewed_rows"] == 0 and not args.allow_unreviewed:
        raise SystemExit(
            "hit_ledger.csv 还没有审阅痕迹。请先按实验图表填写 reviewer_label、"
            "experiment_support、experiment_units、evidence_basis 和 reviewer_reason；"
            "如只是测试工具，可加 --allow-unreviewed。"
        )
    run_arena(root, ["report", "--project", args.project, "--run", args.run])
    run_arena_tool(root, "check_report_style.py", [str(paths["report"])])
    run_arena_tool(root, "check_ai_style.py", [str(paths["report"])])
    link = update_link(root, args.project, args.run, "report_ready")
    print(f"报告：{paths['report']}")
    print(f"PDF：{paths['pdf']}")
    print(f"Desk link：{link}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = arena_root(args)
    require_arena(root)
    update_link(root, args.project, args.run, "status_checked")
    print_status(root, args.project, args.run)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CodexResearchDesk bridge for the external ResearchSkillArena temporal holdout workflow.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--arena-root", help="ResearchSkillArena root. Defaults to env RESEARCH_SKILL_ARENA or sibling ../ResearchSkillArena.")
    subparsers = parser.add_subparsers(dest="command")

    prepare = subparsers.add_parser("prepare", help="Initialize an arena run and collect the historical corpus")
    prepare.add_argument("--project", required=True)
    prepare.add_argument("--run", required=True)
    prepare.add_argument("--topic", required=True)
    prepare.add_argument("--cutoff-year", type=int, required=True)
    prepare.add_argument("--future-start", type=int, required=True)
    prepare.add_argument("--future-end", type=int, required=True)
    prepare.add_argument("--sources", default="openalex,semantic_scholar,arxiv")
    prepare.add_argument("--max-past", type=int, default=80)
    prepare.add_argument("--max-future", type=int, default=120)
    prepare.add_argument("--force-init", action="store_true", help="Rewrite existing arena config")
    prepare.add_argument("--refresh-past", action="store_true", help="Recollect past corpus")
    prepare.add_argument("--no-collect-past", action="store_true", help="Only initialize config and prompt")
    prepare.set_defaults(func=cmd_prepare)

    submit = subparsers.add_parser("submit-ideas", help="Copy a historical-only idea file into the arena submission directory")
    submit.add_argument("--project", required=True)
    submit.add_argument("--run", required=True)
    submit.add_argument("--ideas-file", required=True)
    submit.add_argument("--skill", default="research-desk")
    submit.add_argument("--force", action="store_true")
    submit.set_defaults(func=cmd_submit_ideas)

    ledger = subparsers.add_parser("make-ledger", help="Collect the future corpus and create the candidate hit ledger")
    ledger.add_argument("--project", required=True)
    ledger.add_argument("--run", required=True)
    ledger.add_argument("--top-k", type=int, default=8)
    ledger.add_argument("--refresh-future", action="store_true")
    ledger.add_argument("--skip-cool", action="store_true", help="Do not fetch Papers.cool/Kimi auxiliary interpretations")
    ledger.add_argument("--refresh-cool", action="store_true", help="Refresh cached Papers.cool/Kimi responses")
    ledger.add_argument("--cool-max-papers", type=int, default=20)
    ledger.add_argument("--cool-top-per-idea", type=int, default=3)
    ledger.add_argument("--cool-min-score", type=float, default=0.0)
    ledger.set_defaults(func=cmd_make_ledger)

    cool = subparsers.add_parser("enrich-cool", help="Fetch Papers.cool/Kimi interpretations for ledger candidates")
    cool.add_argument("--project", required=True)
    cool.add_argument("--run", required=True)
    cool.add_argument("--max-papers", type=int, default=20)
    cool.add_argument("--top-per-idea", type=int, default=3)
    cool.add_argument("--min-score", type=float, default=0.0)
    cool.add_argument("--refresh", action="store_true")
    cool.set_defaults(func=cmd_enrich_cool)

    triage = subparsers.add_parser("triage-cool", help="Create a PDF-review priority queue from cached Papers.cool interpretations")
    triage.add_argument("--project", required=True)
    triage.add_argument("--run", required=True)
    triage.set_defaults(func=cmd_triage_cool)

    report = subparsers.add_parser("finalize-report", help="Render the reviewed temporal holdout report and PDF")
    report.add_argument("--project", required=True)
    report.add_argument("--run", required=True)
    report.add_argument("--allow-unreviewed", action="store_true", help="Allow a report with an entirely unreviewed ledger; for smoke tests only")
    report.set_defaults(func=cmd_finalize_report)

    status = subparsers.add_parser("status", help="Show current arena run status and the next needed action")
    status.add_argument("--project", required=True)
    status.add_argument("--run", required=True)
    status.set_defaults(func=cmd_status)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "command", None):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
