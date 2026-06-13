from __future__ import annotations

import argparse
import base64
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
DEFAULT_TIMEOUT = 20
USER_AGENT = "CodexResearchDesk-external-signal-scout/1.0"
KNOWN_INSTITUTION_OWNERS = {
    "microsoft",
    "huggingface",
    "openai",
    "google",
    "google-research",
    "deepmind",
    "anthropic",
    "meta",
    "facebookresearch",
    "nvidia",
    "stanford",
    "stanfordnlp",
    "berkeley",
    "mit",
    "mit-ibm-watson-ai-lab",
    "allenai",
}
METRIC_KEYWORDS = (
    "benchmark",
    "leaderboard",
    "metric",
    "metrics",
    "evaluation",
    "eval",
    "trace",
    "traces",
    "fixed budget",
    "budget",
    "mle-bench",
    "arc-bench",
    "autolab",
    "reproduc",
    "score",
    "scores",
)
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "using",
    "based",
    "research",
    "paper",
    "papers",
    "model",
    "models",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clamp(value: float, minimum: float = 0, maximum: float = 100) -> int:
    return int(round(max(minimum, min(maximum, value))))


def days_since(value: str | None, now: datetime | None = None) -> float | None:
    if not value:
        return None
    now = now or datetime.now(timezone.utc)
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (now - parsed).total_seconds() / 86400


def request_text(url: str, *, headers: dict[str, str] | None = None, timeout: int = DEFAULT_TIMEOUT) -> tuple[str | None, str]:
    merged_headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if headers:
        merged_headers.update(headers)
    req = urllib.request.Request(url, headers=merged_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
        return body, "ok"
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return None, f"http_{exc.code}: {body[:160]}"
    except Exception as exc:
        return None, f"error: {exc}"


def request_json(url: str, *, headers: dict[str, str] | None = None, timeout: int = DEFAULT_TIMEOUT) -> tuple[Any | None, str]:
    text, status = request_text(url, headers=headers, timeout=timeout)
    if text is None:
        return None, status
    try:
        return json.loads(text), "ok"
    except json.JSONDecodeError as exc:
        return None, f"json_error: {exc}"


def query_tokens(query: str) -> set[str]:
    tokens = set(re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_-]{2,}", query.lower()))
    expanded = set(tokens)
    if "sae" in tokens:
        expanded.update({"sparse", "autoencoder", "autoencoders"})
    if "moe" in tokens:
        expanded.update({"mixture", "experts", "expert", "routing", "router"})
    return {token for token in expanded if token not in STOPWORDS}


def is_relevant_to_query(query: str, *values: Any) -> bool:
    tokens = query_tokens(query)
    if not tokens:
        return True
    text = " ".join(str(value).lower() for value in values if value is not None)
    hits = sum(1 for token in tokens if token in text)
    return hits >= 1 if len(tokens) <= 3 else hits >= 2


def github_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def readme_signal_terms(readme_text: str | None) -> list[str]:
    if not readme_text:
        return []
    text = readme_text.lower()
    return sorted({keyword for keyword in METRIC_KEYWORDS if keyword in text})


def parse_github_repo(
    repo: dict[str, Any],
    *,
    topics: list[str] | None = None,
    has_release: bool | None = None,
    has_ci: bool | None = None,
    readme_terms: list[str] | None = None,
) -> dict[str, Any]:
    license_info = repo.get("license") or {}
    owner = repo.get("owner") or {}
    return {
        "repo": repo.get("full_name"),
        "url": repo.get("html_url"),
        "description": repo.get("description"),
        "stars": repo.get("stargazers_count") or 0,
        "forks": repo.get("forks_count") or 0,
        "watchers": repo.get("watchers_count") or 0,
        "open_issues": repo.get("open_issues_count") or 0,
        "license": license_info.get("spdx_id"),
        "created_at": repo.get("created_at"),
        "updated_at": repo.get("updated_at"),
        "pushed_at": repo.get("pushed_at"),
        "language": repo.get("language"),
        "archived": bool(repo.get("archived")),
        "owner": owner.get("login"),
        "owner_type": owner.get("type"),
        "topics": topics or [],
        "has_release": bool(has_release),
        "has_ci": bool(has_ci),
        "readme_signal_terms": readme_terms or [],
        "source_status": "ok",
    }


def decode_github_readme(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    content = payload.get("content")
    if not isinstance(content, str):
        return None
    try:
        return base64.b64decode(content.encode("ascii"), validate=False).decode("utf-8", errors="replace")
    except Exception:
        return None


def fetch_github_repo(repo_name: str) -> tuple[dict[str, Any] | None, str]:
    base = f"https://api.github.com/repos/{repo_name}"
    repo, status = request_json(base, headers=github_headers())
    if repo is None:
        return None, status

    topics_payload, _ = request_json(f"{base}/topics", headers=github_headers())
    topics = topics_payload.get("names", []) if isinstance(topics_payload, dict) else []

    releases_payload, releases_status = request_json(f"{base}/releases?per_page=1", headers=github_headers())
    has_release = isinstance(releases_payload, list) and bool(releases_payload) and releases_status == "ok"

    workflows_payload, workflows_status = request_json(f"{base}/contents/.github/workflows", headers=github_headers())
    has_ci = workflows_status == "ok" and isinstance(workflows_payload, list) and bool(workflows_payload)

    readme_payload, _ = request_json(f"{base}/readme", headers=github_headers())
    readme_terms = readme_signal_terms(decode_github_readme(readme_payload))
    return parse_github_repo(repo, topics=topics, has_release=has_release, has_ci=has_ci, readme_terms=readme_terms), "ok"


def search_github_repos(query: str, max_results: int) -> tuple[list[dict[str, Any]], str]:
    params = urllib.parse.urlencode(
        {
            "q": f"{query} in:name,description,readme",
            "sort": "stars",
            "order": "desc",
            "per_page": max(1, min(max_results, 20)),
        }
    )
    payload, status = request_json(f"https://api.github.com/search/repositories?{params}", headers=github_headers())
    if not isinstance(payload, dict):
        return [], status
    results = []
    for item in payload.get("items", []):
        if not is_relevant_to_query(query, item.get("full_name"), item.get("description"), " ".join(item.get("topics") or [])):
            continue
        parsed = parse_github_repo(item)
        results.append(parsed)
        if len(results) >= max_results:
            break
    return results, "ok"


def parse_alphaxiv_html(html: str, arxiv_id: str, url: str) -> dict[str, Any]:
    def number(pattern: str) -> int | None:
        match = re.search(pattern, html)
        return int(match.group(1)) if match else None

    title_match = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else None
    title = title.replace("&amp;", "&") if title else None
    return {
        "arxiv_id": arxiv_id,
        "url": url,
        "title": title,
        "comments": number(r"commentsCount:(\d+)"),
        "totalVotes": number(r"totalVotes:(\d+)"),
        "publicTotalVotes": number(r"publicTotalVotes:(\d+)"),
        "visitsAll": number(r"visitsCount:[^}]*all:(\d+)"),
        "source_status": "ok",
    }


def fetch_alphaxiv(arxiv_id: str) -> tuple[dict[str, Any] | None, str]:
    url = f"https://www.alphaxiv.org/abs/{arxiv_id}"
    html, status = request_text(url)
    if html is None:
        return None, status
    return parse_alphaxiv_html(html, arxiv_id, url), "ok"


def parse_hn_hits(payload: dict[str, Any]) -> list[dict[str, Any]]:
    hits = []
    for item in payload.get("hits", []) or []:
        hits.append(
            {
                "title": item.get("title") or item.get("story_title"),
                "url": item.get("url") or item.get("story_url"),
                "points": item.get("points") or 0,
                "comments": item.get("num_comments") or 0,
                "created_at": item.get("created_at"),
                "objectID": item.get("objectID"),
                "source_status": "ok",
            }
        )
    return hits


def fetch_hackernews(query: str, max_results: int) -> tuple[list[dict[str, Any]], str]:
    params = urllib.parse.urlencode({"query": query, "tags": "story", "hitsPerPage": max(1, min(max_results, 10))})
    payload, status = request_json(f"https://hn.algolia.com/api/v1/search?{params}")
    if not isinstance(payload, dict):
        return [], status
    return parse_hn_hits(payload), "ok"


def fetch_hf_paper(arxiv_id: str) -> tuple[dict[str, Any] | None, str]:
    url = f"https://huggingface.co/papers/{arxiv_id}"
    html, status = request_text(url)
    if html is None:
        return None, status
    title_match = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else None
    return {
        "arxiv_id": arxiv_id,
        "url": url,
        "title": title,
        "exists": "Papers" in html or "Hugging Face" in html,
        "source_status": "ok",
    }, "ok"


def fetch_semantic_scholar_by_arxiv(arxiv_id: str) -> tuple[dict[str, Any] | None, str]:
    fields = "title,citationCount,referenceCount,influentialCitationCount,year,venue,url,externalIds"
    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{urllib.parse.quote(arxiv_id)}?fields={fields}"
    headers = {"Accept": "application/json"}
    key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    if key:
        headers["x-api-key"] = key
    payload, status = request_json(url, headers=headers)
    if not isinstance(payload, dict):
        return None, status
    return {
        "arxiv_id": arxiv_id,
        "title": payload.get("title"),
        "year": payload.get("year"),
        "venue": payload.get("venue"),
        "citations": payload.get("citationCount") or 0,
        "influential_citations": payload.get("influentialCitationCount") or 0,
        "references": payload.get("referenceCount") or 0,
        "url": payload.get("url"),
        "externalIds": payload.get("externalIds") or {},
        "source_status": "ok",
    }, "ok"


def fetch_openalex(query: str, max_results: int) -> tuple[list[dict[str, Any]], str]:
    params = urllib.parse.urlencode({"search": query, "per-page": max(1, min(max_results, 10)), "sort": "relevance_score:desc"})
    email = os.environ.get("OPENALEX_EMAIL", "").strip()
    if email:
        params += "&" + urllib.parse.urlencode({"mailto": email})
    payload, status = request_json(f"https://api.openalex.org/works?{params}")
    if not isinstance(payload, dict):
        return [], status
    results = []
    seen_titles: set[str] = set()
    for work in payload.get("results", []) or []:
        if not is_relevant_to_query(query, work.get("display_name") or work.get("title")):
            continue
        title_key = str(work.get("display_name") or work.get("title") or "").strip().lower()
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        results.append(
            {
                "title": work.get("display_name") or work.get("title"),
                "publication_year": work.get("publication_year"),
                "citations": work.get("cited_by_count") or 0,
                "doi": (work.get("doi") or "").replace("https://doi.org/", "") or None,
                "openalex_id": work.get("id"),
                "url": work.get("id"),
                "source_status": "ok",
            }
        )
    return results, "ok"


def default_manual_signals() -> dict[str, list[dict[str, Any]]]:
    return {"x_posts": [], "reddit_posts": [], "enterprise_adoption": []}


def load_manual_signals(path: Path | None) -> dict[str, list[dict[str, Any]]]:
    manual = default_manual_signals()
    if path is None:
        return manual
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("manual"), dict):
        data = data["manual"]
    if not isinstance(data, dict):
        raise ValueError("manual signals must be a JSON object")
    for key in manual:
        value = data.get(key, [])
        if value is None:
            value = []
        if not isinstance(value, list):
            raise ValueError(f"manual.{key} must be a list")
        manual[key] = [item if isinstance(item, dict) else {"value": item} for item in value]
    return manual


def log_score(value: int | float, divisor: float, cap: float) -> float:
    if value <= 0:
        return 0
    return min(cap, math.log10(value + 1) / divisor * cap)


def score_engineering(github_items: list[dict[str, Any]]) -> int:
    if not github_items:
        return 0
    top = max(github_items, key=lambda item: item.get("stars", 0))
    score = 0.0
    score += log_score(top.get("stars", 0), 5, 40)
    score += log_score(top.get("forks", 0), 4, 15)
    age = days_since(top.get("pushed_at"))
    if age is not None:
        if age <= 30:
            score += 20
        elif age <= 90:
            score += 15
        elif age <= 365:
            score += 8
        else:
            score += 2
    if top.get("license"):
        score += 7
    if top.get("has_release"):
        score += 5
    if top.get("has_ci"):
        score += 5
    if not top.get("archived"):
        score += 3
    return clamp(score)


def combined_text(*groups: Any) -> str:
    chunks: list[str] = []
    for group in groups:
        if isinstance(group, list):
            for item in group:
                if isinstance(item, dict):
                    chunks.extend(str(value) for value in item.values() if value is not None)
        elif isinstance(group, dict):
            chunks.extend(str(value) for value in group.values() if value is not None)
        elif group is not None:
            chunks.append(str(group))
    return " ".join(chunks).lower()


def score_benchmark(sources: dict[str, Any]) -> int:
    text = combined_text(sources.get("github", []), sources.get("hackernews", []), sources.get("manual", {}))
    hits = sum(1 for keyword in METRIC_KEYWORDS if keyword in text)
    hits += sum(len(item.get("readme_signal_terms") or []) for item in sources.get("github", []))
    score = min(80, hits * 18)
    if sources.get("semantic_scholar") or sources.get("openalex"):
        score += 10
    if any((item.get("citations") or 0) >= 10 for item in sources.get("semantic_scholar", []) + sources.get("openalex", [])):
        score += 10
    return clamp(score)


def score_community(sources: dict[str, Any]) -> int:
    score = 0.0
    if sources.get("github"):
        top_stars = max(item.get("stars", 0) for item in sources["github"])
        score += log_score(top_stars, 5, 35)
    for item in sources.get("alphaxiv", []):
        score += log_score(item.get("publicTotalVotes") or 0, 3, 18)
        score += log_score(item.get("visitsAll") or 0, 5, 12)
        score += log_score(item.get("comments") or 0, 2, 8)
    for item in sources.get("hackernews", []):
        score += log_score(item.get("points") or 0, 3, 12)
        score += log_score(item.get("comments") or 0, 3, 8)
    manual = sources.get("manual", {})
    for item in manual.get("x_posts", []):
        score += log_score(int(item.get("likes") or item.get("like_count") or 0), 5, 8)
        score += log_score(int(item.get("reposts") or item.get("retweets") or 0), 4, 4)
    for item in manual.get("reddit_posts", []):
        score += log_score(int(item.get("score") or 0), 4, 8)
        score += log_score(int(item.get("comments") or item.get("num_comments") or 0), 4, 4)
    return clamp(score)


def score_institution(sources: dict[str, Any]) -> int:
    score = 0
    for item in sources.get("github", []):
        owner = str(item.get("owner") or "").lower()
        if item.get("owner_type") == "Organization":
            score += 20
        if owner in KNOWN_INSTITUTION_OWNERS:
            score += 35
    manual = sources.get("manual", {})
    score += min(45, len(manual.get("enterprise_adoption", [])) * 20)
    return clamp(score)


def score_freshness(sources: dict[str, Any]) -> int:
    candidates = []
    for item in sources.get("github", []):
        age = days_since(item.get("pushed_at") or item.get("updated_at"))
        if age is not None:
            candidates.append(age)
    if not candidates:
        return 0
    age = min(candidates)
    if age <= 14:
        return 100
    if age <= 30:
        return 85
    if age <= 90:
        return 65
    if age <= 180:
        return 45
    if age <= 365:
        return 25
    return 10


def compute_scores(sources: dict[str, Any]) -> dict[str, Any]:
    engineering = score_engineering(sources.get("github", []))
    benchmark = score_benchmark(sources)
    community = score_community(sources)
    institution = score_institution(sources)
    freshness = score_freshness(sources)
    raw = (0.30 * engineering) + (0.25 * benchmark) + (0.20 * community) + (0.15 * institution) + (0.10 * freshness)
    hype_risk = "low"
    if community >= 70 and benchmark < 35:
        hype_risk = "high"
    elif community >= 45 and benchmark < 40:
        hype_risk = "medium"
    if engineering >= 65 and benchmark < 25:
        hype_risk = "high"
    penalty = 0
    if hype_risk == "high":
        penalty += 15
    elif hype_risk == "medium":
        penalty += 7
    if not sources.get("github"):
        penalty += 10
    if benchmark < 20:
        penalty += 10
    return {
        "external_signal_score": clamp(raw - penalty),
        "engineering_health": engineering,
        "benchmark_or_metric_signal": benchmark,
        "community_attention": community,
        "institution_or_enterprise_signal": institution,
        "freshness": freshness,
        "hype_risk": hype_risk,
    }


def derive_risk_flags(sources: dict[str, Any], scores: dict[str, Any], source_status: dict[str, str]) -> list[str]:
    flags: list[str] = []
    if not sources.get("github"):
        flags.append("没有发现明确 GitHub 实现信号，idea 可能仍停留在论文或概念层。")
    if scores["community_attention"] >= 60 and scores["benchmark_or_metric_signal"] < 35:
        flags.append("社区热度高于可验证指标信号，存在 hype 先于证据的风险。")
    if scores["benchmark_or_metric_signal"] < 25:
        flags.append("缺少固定预算、leaderboard、trace 或清晰 benchmark 信号。")
    if sources.get("github"):
        top = max(sources["github"], key=lambda item: item.get("stars", 0))
        if not top.get("license"):
            flags.append(f"Top GitHub 项目 {top.get('repo')} 缺少明确 license，复用风险较高。")
        age = days_since(top.get("pushed_at"))
        if age is not None and age > 365:
            flags.append(f"Top GitHub 项目 {top.get('repo')} 超过一年未 push，维护信号弱。")
    if sources.get("github") and not (sources.get("alphaxiv") or sources.get("semantic_scholar") or sources.get("openalex")):
        flags.append("有实现信号但缺少论文社区或学术索引信号，需要确认评价依据。")
    failures = [name for name, status in source_status.items() if status not in {"ok", "skipped"}]
    if len(failures) >= 2:
        flags.append("多个外部来源抓取失败，本次外部信号不完整。")
    return flags


def derive_pitfalls(risk_flags: list[str], scores: dict[str, Any]) -> list[str]:
    pitfalls = []
    if scores["benchmark_or_metric_signal"] < 35:
        pitfalls.append("idea 可能缺少可度量目标，后续容易变成描述性论文或 A+B 包装。")
    if scores["hype_risk"] in {"medium", "high"}:
        pitfalls.append("方向可能热度先于验证，需要先找反例、失败 issue 和独立 benchmark。")
    if scores["engineering_health"] < 35:
        pitfalls.append("工程承载信号弱，后续实验可能会被环境、数据和依赖问题拖住。")
    if any("license" in flag.lower() for flag in risk_flags):
        pitfalls.append("开源复用边界不清，后续方案设计需避免依赖不可复用代码。")
    if not pitfalls:
        pitfalls.append("外部信号未暴露明显硬坑，但仍需用最近工作重叠检查确认不是简单组合。")
    return pitfalls


def derive_prechecks(risk_flags: list[str], scores: dict[str, Any]) -> list[str]:
    prechecks = [
        "列出最近 10 个相邻论文/项目，逐项确认核心差异不是简单 A+B。",
        "寻找固定预算、leaderboard、trace 或公开评测脚本；没有则先设计最小静态指标。",
    ]
    if scores["hype_risk"] in {"medium", "high"}:
        prechecks.append("抽样阅读高热度项目的 issue、HN/alphaXiv 评论和失败报告，优先找负面证据。")
    if scores["engineering_health"] < 50:
        prechecks.append("检查 top repo 是否可安装、是否有 license、是否近期维护；失败则降低工程可行性评分。")
    if any("学术索引" in flag for flag in risk_flags):
        prechecks.append("补做 Semantic Scholar/OpenAlex/arXiv 查新，确认实现热度是否对应真实研究贡献。")
    return prechecks


def build_ledger_markdown(payload: dict[str, Any]) -> str:
    scores = payload["scores"]
    sources = payload["sources"]
    lines = [
        f"# 外部信号账本：{payload['query']}",
        "",
        f"**项目编号**：`{payload['project_id']}`  ",
        f"**想法编号**：`{payload['idea_id']}`  ",
        f"**生成时间**：{payload['created_at']}  ",
        "",
        "## 总体判断",
        "",
        "| 指标 | 分数 / 状态 |",
        "|---|---:|",
        f"| external_signal_score | {scores['external_signal_score']} |",
        f"| engineering_health | {scores['engineering_health']} |",
        f"| benchmark_or_metric_signal | {scores['benchmark_or_metric_signal']} |",
        f"| community_attention | {scores['community_attention']} |",
        f"| institution_or_enterprise_signal | {scores['institution_or_enterprise_signal']} |",
        f"| freshness | {scores['freshness']} |",
        f"| hype_risk | {scores['hype_risk']} |",
        "",
        "**解释**：外部信号是软门控，只影响调研优先级、风险假设和低成本预检，不单独决定 `GO` 或 `NO_GO`。",
        "",
        "## 数据源状态",
        "",
        "| 来源 | 状态 |",
        "|---|---|",
    ]
    for name, status in payload.get("source_status", {}).items():
        lines.append(f"| {name} | {status} |")

    lines.extend(["", "## GitHub 信号", "", "| repo | stars | forks | pushed | license | CI | release |", "|---|---:|---:|---|---|---:|---:|"])
    for item in sources.get("github", []):
        lines.append(
            f"| [{item.get('repo')}]({item.get('url')}) | {item.get('stars', 0)} | {item.get('forks', 0)} | "
            f"{item.get('pushed_at') or ''} | {item.get('license') or ''} | {str(item.get('has_ci')).lower()} | {str(item.get('has_release')).lower()} |"
        )
    if not sources.get("github"):
        lines.append("| 无 | 0 | 0 |  |  | false | false |")

    lines.extend(["", "## 论文社区与学术信号", "", "| 来源 | 标题 | 指标 | 链接 |", "|---|---|---|---|"])
    for item in sources.get("alphaxiv", []):
        metrics = f"votes={item.get('publicTotalVotes')}; comments={item.get('comments')}; visits={item.get('visitsAll')}"
        lines.append(f"| alphaXiv | {item.get('title') or item.get('arxiv_id')} | {metrics} | {item.get('url')} |")
    for item in sources.get("hf_papers", []):
        lines.append(f"| HF Papers | {item.get('title') or item.get('arxiv_id')} | exists={item.get('exists')} | {item.get('url')} |")
    for item in sources.get("semantic_scholar", []):
        metrics = f"citations={item.get('citations')}; influential={item.get('influential_citations')}"
        lines.append(f"| Semantic Scholar | {item.get('title')} | {metrics} | {item.get('url')} |")
    for item in sources.get("openalex", []):
        metrics = f"citations={item.get('citations')}; year={item.get('publication_year')}"
        lines.append(f"| OpenAlex | {item.get('title')} | {metrics} | {item.get('url')} |")

    lines.extend(["", "## 社区讨论", "", "| 来源 | 标题 | 指标 | 链接 |", "|---|---|---|---|"])
    for item in sources.get("hackernews", []):
        metrics = f"points={item.get('points')}; comments={item.get('comments')}"
        lines.append(f"| Hacker News | {item.get('title')} | {metrics} | {item.get('url') or ''} |")

    manual = sources.get("manual", {})
    lines.extend(["", "## 手工补录", "", "| 类型 | 条目数 | 说明 |", "|---|---:|---|"])
    lines.append(f"| X / Twitter | {len(manual.get('x_posts', []))} | 第一版仅手工补录，不自动抓取。 |")
    lines.append(f"| Reddit | {len(manual.get('reddit_posts', []))} | 第一版仅手工补录，不自动抓取。 |")
    lines.append(f"| 企业/机构采用 | {len(manual.get('enterprise_adoption', []))} | 用于补充产业真实需求信号。 |")

    lines.extend(["", "## 风险旗标", ""])
    for flag in payload.get("risk_flags", []):
        lines.append(f"- {flag}")
    if not payload.get("risk_flags"):
        lines.append("- 未发现明确外部信号风险旗标。")

    lines.extend(["", "## 坑位假设", ""])
    for item in payload.get("pitfall_hypotheses", []):
        lines.append(f"- {item}")

    lines.extend(["", "## 推荐低成本预检", ""])
    for item in payload.get("recommended_prechecks", []):
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def collect_sources(
    query: str,
    *,
    arxiv_ids: list[str],
    github_repos: list[str],
    manual: dict[str, list[dict[str, Any]]],
    github_max: int,
    community_max: int,
    offline: bool,
) -> tuple[dict[str, Any], dict[str, str]]:
    sources: dict[str, Any] = {
        "github": [],
        "alphaxiv": [],
        "hf_papers": [],
        "hackernews": [],
        "semantic_scholar": [],
        "openalex": [],
        "manual": manual,
    }
    status = {name: "skipped" for name in ["github", "alphaxiv", "hf_papers", "hackernews", "semantic_scholar", "openalex", "manual"]}
    status["manual"] = "ok"
    if offline:
        return sources, status

    if github_repos:
        repo_statuses = []
        for repo in github_repos:
            item, item_status = fetch_github_repo(repo)
            repo_statuses.append(item_status)
            if item:
                sources["github"].append(item)
        status["github"] = "ok" if sources["github"] else "; ".join(repo_statuses) or "skipped"
    else:
        items, item_status = search_github_repos(query, github_max)
        sources["github"].extend(items)
        status["github"] = item_status

    alpha_statuses = []
    hf_statuses = []
    s2_statuses = []
    for arxiv_id in arxiv_ids:
        alpha_item, alpha_status = fetch_alphaxiv(arxiv_id)
        alpha_statuses.append(alpha_status)
        if alpha_item:
            sources["alphaxiv"].append(alpha_item)
        hf_item, hf_status = fetch_hf_paper(arxiv_id)
        hf_statuses.append(hf_status)
        if hf_item:
            sources["hf_papers"].append(hf_item)
        s2_item, s2_status = fetch_semantic_scholar_by_arxiv(arxiv_id)
        s2_statuses.append(s2_status)
        if s2_item:
            sources["semantic_scholar"].append(s2_item)
    if arxiv_ids:
        status["alphaxiv"] = "ok" if sources["alphaxiv"] else "; ".join(alpha_statuses)
        status["hf_papers"] = "ok" if sources["hf_papers"] else "; ".join(hf_statuses)
        status["semantic_scholar"] = "ok" if sources["semantic_scholar"] else "; ".join(s2_statuses)

    hn_items, hn_status = fetch_hackernews(query, community_max)
    sources["hackernews"].extend(hn_items)
    status["hackernews"] = hn_status

    openalex_items, openalex_status = fetch_openalex(query, community_max)
    sources["openalex"].extend(openalex_items)
    status["openalex"] = openalex_status
    return sources, status


def scout(
    query: str,
    *,
    project: str,
    idea: str,
    root: Path,
    arxiv_ids: list[str],
    github_repos: list[str],
    manual_signals: Path | None,
    github_max: int = 5,
    community_max: int = 5,
    offline: bool = False,
) -> dict[str, Any]:
    manual = load_manual_signals(manual_signals)
    sources, source_status = collect_sources(
        query,
        arxiv_ids=arxiv_ids,
        github_repos=github_repos,
        manual=manual,
        github_max=github_max,
        community_max=community_max,
        offline=offline,
    )
    scores = compute_scores(sources)
    risk_flags = derive_risk_flags(sources, scores, source_status)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "project_id": project,
        "idea_id": idea,
        "query": query,
        "created_at": now_iso(),
        "sources": sources,
        "source_status": source_status,
        "scores": scores,
        "risk_flags": risk_flags,
        "pitfall_hypotheses": derive_pitfalls(risk_flags, scores),
        "recommended_prechecks": derive_prechecks(risk_flags, scores),
    }
    output_dir = root / "projects" / project / "signals" / idea
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "external_signals.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "EXTERNAL_SIGNAL_LEDGER.md").write_text(build_ledger_markdown(payload), encoding="utf-8")
    payload["output_dir"] = str(output_dir)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect external soft-gate signals for early research idea triage.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scout_parser = subparsers.add_parser("scout", help="Collect external signals and write a project-local ledger.")
    scout_parser.add_argument("query", help="Idea or search query to scout.")
    scout_parser.add_argument("--project", required=True, help="Project slug.")
    scout_parser.add_argument("--idea", required=True, help="Idea slug.")
    scout_parser.add_argument("--root", type=Path, default=Path("."), help="Repository root. Defaults to current directory.")
    scout_parser.add_argument("--arxiv-id", action="append", default=[], help="arXiv ID to query on alphaXiv/HF/Semantic Scholar. Can be repeated.")
    scout_parser.add_argument("--github-repo", action="append", default=[], help="GitHub repo owner/name to inspect. Can be repeated.")
    scout_parser.add_argument("--manual-signals", type=Path, help="Manual JSON file for X/Reddit/enterprise signals.")
    scout_parser.add_argument("--github-max", type=int, default=5, help="Max GitHub search results when --github-repo is omitted.")
    scout_parser.add_argument("--community-max", type=int, default=5, help="Max HN/OpenAlex search results.")
    scout_parser.add_argument("--offline", action="store_true", help="Skip network sources; useful for tests or manual-only ledgers.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "scout":
        try:
            payload = scout(
                args.query,
                project=args.project,
                idea=args.idea,
                root=args.root.resolve(),
                arxiv_ids=args.arxiv_id,
                github_repos=args.github_repo,
                manual_signals=args.manual_signals,
                github_max=args.github_max,
                community_max=args.community_max,
                offline=args.offline,
            )
        except Exception as exc:
            print(f"external signal scout failed: {exc}", file=sys.stderr)
            return 2
        print(json.dumps({"output_dir": payload["output_dir"], "scores": payload["scores"]}, ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
