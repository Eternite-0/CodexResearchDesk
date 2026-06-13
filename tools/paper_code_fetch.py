from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from external_signal_fetch import (
    clamp,
    days_since,
    decode_github_readme,
    github_headers,
    is_relevant_to_query,
    log_score,
    request_json,
    request_text,
    query_tokens,
)


SCHEMA_VERSION = "1.0"

GITHUB_REPO_RE = re.compile(
    r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)",
    flags=re.IGNORECASE,
)

COMING_SOON_PATTERNS = (
    "code coming soon",
    "coming soon",
    "to be released",
    "will be released",
    "will release",
    "stay tuned",
    "under construction",
)

INSTALL_PATTERNS = (
    "pip install",
    "conda env",
    "requirements.txt",
    "environment.yml",
    "pyproject.toml",
    "setup.py",
    "poetry install",
    "uv pip",
)

EVAL_PATTERNS = (
    "evaluate",
    "evaluation",
    "eval.py",
    "benchmark",
    "leaderboard",
    "reproduce",
    "reproduction",
    "test.py",
    "metrics",
)

DATA_PATTERNS = (
    "dataset",
    "datasets",
    "download data",
    "data download",
    "huggingface.co/datasets",
    "kaggle",
)

CHECKPOINT_PATTERNS = (
    "checkpoint",
    "checkpoints",
    "pretrained",
    "pre-trained",
    "weights",
    "model zoo",
    "huggingface.co/",
)

CONFIG_PATTERNS = (
    "config",
    "configs",
    "yaml",
    "hydra",
    "argparse",
)

OFFICIAL_PATTERNS = (
    "official implementation",
    "official code",
    "code for our paper",
    "implementation of our paper",
    "this repository contains the code for",
)

UNOFFICIAL_PATTERNS = (
    "unofficial implementation",
    "unofficial code",
    "reimplementation",
    "re-implementation",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_repo_name(value: str) -> str | None:
    value = value.strip().strip("<>()[]{}.,;:'\"")
    if not value:
        return None
    match = GITHUB_REPO_RE.search(value)
    if match:
        value = match.group(1)
    value = value.removesuffix(".git").strip("/").strip("<>()[]{}.,;:'\"")
    parts = value.split("/")
    if len(parts) < 2:
        return None
    owner = parts[0].strip("<>()[]{}.,;:'\"")
    repo = parts[1].removesuffix(".git").strip("<>()[]{}.,;:'\"")
    if not owner or not repo:
        return None
    return f"{owner}/{repo}"


def md_cell(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).replace("|", "\\|").strip()


def extract_github_repos(text: str | None) -> list[str]:
    if not text:
        return []
    repos: list[str] = []
    seen: set[str] = set()
    for match in GITHUB_REPO_RE.finditer(text):
        repo = normalize_repo_name(match.group(1))
        if repo and repo.lower() not in seen:
            seen.add(repo.lower())
            repos.append(repo)
    return repos


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9]+", " ", value.lower())).strip()


def title_overlap(title: str | None, text: str | None) -> float:
    title_tokens = {token for token in query_tokens(title or "") if len(token) >= 4}
    if not title_tokens:
        return 0.0
    haystack = normalize_text(text)
    hits = sum(1 for token in title_tokens if token in haystack)
    return hits / len(title_tokens)


def contains_any(text: str, patterns: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in patterns)


def analyze_readme(readme_text: str | None, *, arxiv_ids: list[str], paper_title: str | None) -> dict[str, Any]:
    text = readme_text or ""
    lowered = text.lower()
    arxiv_hits = [arxiv_id for arxiv_id in arxiv_ids if arxiv_id.lower() in lowered]
    overlap = title_overlap(paper_title, text)
    has_result_table = bool(re.search(r"\|.+\|.+\|", text)) and contains_any(text, EVAL_PATTERNS)
    return {
        "has_install_instructions": contains_any(text, INSTALL_PATTERNS),
        "has_dataset_instructions": contains_any(text, DATA_PATTERNS),
        "has_checkpoint_or_weights": contains_any(text, CHECKPOINT_PATTERNS),
        "has_evaluation_instructions": contains_any(text, EVAL_PATTERNS),
        "has_config_signal": contains_any(text, CONFIG_PATTERNS),
        "has_result_table": has_result_table,
        "code_coming_soon": contains_any(text, COMING_SOON_PATTERNS),
        "official_claim": contains_any(text, OFFICIAL_PATTERNS),
        "unofficial_claim": contains_any(text, UNOFFICIAL_PATTERNS),
        "arxiv_id_hits": arxiv_hits,
        "title_token_overlap": round(overlap, 3),
        "github_links": extract_github_repos(text),
    }


def analyze_root_contents(contents: Any) -> dict[str, Any]:
    names: set[str] = set()
    if isinstance(contents, list):
        for item in contents:
            if isinstance(item, dict) and item.get("name"):
                names.add(str(item["name"]).lower())
    joined = " ".join(sorted(names))
    return {
        "has_requirements_file": bool({"requirements.txt", "environment.yml", "environment.yaml", "pyproject.toml", "setup.py"} & names),
        "has_license_file": any(name.startswith("license") for name in names),
        "has_config_dir": bool({"configs", "config", "conf"} & names),
        "has_script_or_eval_path": bool({"scripts", "eval", "evaluation", "benchmarks", "benchmark", "tests", "test"} & names)
        or any("eval" in name or "benchmark" in name for name in names),
        "has_data_path": bool({"data", "datasets", "dataset"} & names),
        "has_examples_or_notebooks": bool({"examples", "notebooks", "demo", "demos"} & names),
        "root_names": sorted(names),
        "root_text": joined,
    }


def parse_github_repo_detail(
    repo: dict[str, Any],
    *,
    readme_text: str | None,
    root_contents: Any,
    topics: list[str] | None,
    has_release: bool,
    has_ci: bool,
    arxiv_ids: list[str],
    paper_title: str | None,
    discovered_via: list[str] | None = None,
) -> dict[str, Any]:
    owner = repo.get("owner") or {}
    license_info = repo.get("license") or {}
    readme_signals = analyze_readme(readme_text, arxiv_ids=arxiv_ids, paper_title=paper_title)
    root_signals = analyze_root_contents(root_contents)
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
        "default_branch": repo.get("default_branch"),
        "language": repo.get("language"),
        "archived": bool(repo.get("archived")),
        "owner": owner.get("login"),
        "owner_type": owner.get("type"),
        "topics": topics or [],
        "has_release": bool(has_release),
        "has_ci": bool(has_ci),
        "readme_signals": readme_signals,
        "root_signals": root_signals,
        "discovered_via": discovered_via or [],
        "source_status": "ok",
    }


def fetch_github_repo_detail(
    repo_name: str,
    *,
    arxiv_ids: list[str],
    paper_title: str | None,
    discovered_via: list[str] | None = None,
) -> tuple[dict[str, Any] | None, str]:
    base = f"https://api.github.com/repos/{repo_name}"
    repo, status = request_json(base, headers=github_headers())
    if not isinstance(repo, dict):
        fallback = build_github_repo_fallback(
            repo_name,
            arxiv_ids=arxiv_ids,
            paper_title=paper_title,
            discovered_via=discovered_via,
            original_status=status,
        )
        return fallback, f"fallback_after_{status}" if fallback else status

    topics_payload, _ = request_json(f"{base}/topics", headers=github_headers())
    topics = topics_payload.get("names", []) if isinstance(topics_payload, dict) else []

    releases_payload, releases_status = request_json(f"{base}/releases?per_page=1", headers=github_headers())
    has_release = isinstance(releases_payload, list) and bool(releases_payload) and releases_status == "ok"

    workflows_payload, workflows_status = request_json(f"{base}/contents/.github/workflows", headers=github_headers())
    has_ci = workflows_status == "ok" and isinstance(workflows_payload, list) and bool(workflows_payload)

    readme_payload, _ = request_json(f"{base}/readme", headers=github_headers())
    readme_text = decode_github_readme(readme_payload)

    root_contents, _ = request_json(f"{base}/contents", headers=github_headers())
    return (
        parse_github_repo_detail(
            repo,
            readme_text=readme_text,
            root_contents=root_contents,
            topics=topics,
            has_release=has_release,
            has_ci=has_ci,
            arxiv_ids=arxiv_ids,
            paper_title=paper_title,
            discovered_via=discovered_via,
        ),
        "ok",
    )


def fetch_raw_readme(repo_name: str) -> tuple[str | None, str]:
    owner_repo = normalize_repo_name(repo_name)
    if not owner_repo:
        return None, "invalid_repo"
    statuses = []
    for ref in ("HEAD", "main", "master"):
        for filename in ("README.md", "README.rst", "readme.md", "Readme.md"):
            url = f"https://raw.githubusercontent.com/{owner_repo}/{ref}/{filename}"
            text, status = request_text(url)
            statuses.append(status)
            if text:
                return text, "ok"
    return None, "; ".join(statuses)


def build_github_repo_fallback(
    repo_name: str,
    *,
    arxiv_ids: list[str],
    paper_title: str | None,
    discovered_via: list[str] | None,
    original_status: str,
) -> dict[str, Any] | None:
    normalized = normalize_repo_name(repo_name)
    if not normalized:
        return None
    readme_text, readme_status = fetch_raw_readme(normalized)
    owner = normalized.split("/", 1)[0]
    repo = {
        "full_name": normalized,
        "html_url": f"https://github.com/{normalized}",
        "description": None,
        "stargazers_count": 0,
        "forks_count": 0,
        "watchers_count": 0,
        "open_issues_count": 0,
        "license": None,
        "created_at": None,
        "updated_at": None,
        "pushed_at": None,
        "default_branch": None,
        "language": None,
        "archived": False,
        "owner": {"login": owner, "type": None},
    }
    parsed = parse_github_repo_detail(
        repo,
        readme_text=readme_text,
        root_contents=[],
        topics=[],
        has_release=False,
        has_ci=False,
        arxiv_ids=arxiv_ids,
        paper_title=paper_title,
        discovered_via=discovered_via,
    )
    parsed["source_status"] = f"fallback_after_{original_status}; raw_readme={readme_status}"
    return parsed


def parse_papers_with_code_papers(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        rows = payload.get("results") or []
    elif isinstance(payload, list):
        rows = payload
    else:
        rows = []
    papers = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        papers.append(
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "arxiv_id": item.get("arxiv_id"),
                "url": item.get("url_abs") or item.get("url"),
                "paper_url": item.get("paper_url"),
                "proceeding": item.get("proceeding"),
                "published": item.get("published"),
                "source_status": "ok",
            }
        )
    return papers


def parse_papers_with_code_repositories(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        rows = payload.get("results") or []
    elif isinstance(payload, list):
        rows = payload
    else:
        rows = []
    repositories = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        url = item.get("url") or item.get("github_url") or item.get("repository_url")
        repo_names = extract_github_repos(str(url or ""))
        repositories.append(
            {
                "name": item.get("name") or item.get("full_name") or (repo_names[0] if repo_names else None),
                "url": url,
                "repo": repo_names[0] if repo_names else normalize_repo_name(str(item.get("name") or "")),
                "framework": item.get("framework"),
                "is_official": item.get("is_official"),
                "stars": item.get("stars"),
                "source_status": "ok",
            }
        )
    return repositories


def fetch_papers_with_code(query: str, *, arxiv_ids: list[str], paper_title: str | None, max_results: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    params_list = []
    for arxiv_id in arxiv_ids:
        params_list.append({"arxiv_id": arxiv_id})
    if paper_title or query:
        params_list.append({"q": paper_title or query})

    papers: list[dict[str, Any]] = []
    repos: list[dict[str, Any]] = []
    statuses: list[str] = []
    seen_papers: set[str] = set()
    seen_repos: set[str] = set()
    for params in params_list:
        params["page_size"] = str(max(1, min(max_results, 10)))
        payload, status = request_json(f"https://paperswithcode.com/api/v1/papers/?{urllib.parse.urlencode(params)}")
        statuses.append(status)
        for paper in parse_papers_with_code_papers(payload):
            paper_key = str(paper.get("id") or paper.get("title") or "").lower()
            if paper_key and paper_key not in seen_papers:
                seen_papers.add(paper_key)
                papers.append(paper)
            paper_id = paper.get("id")
            if not paper_id:
                continue
            repo_payload, repo_status = request_json(f"https://paperswithcode.com/api/v1/papers/{urllib.parse.quote(str(paper_id))}/repositories/")
            statuses.append(repo_status)
            for repo in parse_papers_with_code_repositories(repo_payload):
                repo_key = str(repo.get("repo") or repo.get("url") or repo.get("name") or "").lower()
                if repo_key and repo_key not in seen_repos:
                    seen_repos.add(repo_key)
                    repos.append(repo)
    status = "ok" if papers or repos else "; ".join(statuses) or "skipped"
    return papers, repos, status


def parse_arxiv_abs_html(html: str, arxiv_id: str, url: str) -> dict[str, Any]:
    title = None
    title_match = re.search(r'<h1 class="title[^"]*">\s*<span[^>]*>Title:</span>\s*(.*?)</h1>', html, flags=re.DOTALL | re.IGNORECASE)
    if title_match:
        title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", title_match.group(1))).strip()
    if not title:
        title_tag = re.search(r"<title>(.*?)</title>", html, flags=re.DOTALL | re.IGNORECASE)
        title = re.sub(r"\s+", " ", title_tag.group(1)).strip() if title_tag else None
    return {
        "arxiv_id": arxiv_id,
        "url": url,
        "title": title,
        "github_repos": extract_github_repos(html),
        "source_status": "ok",
    }


def fetch_arxiv_abs(arxiv_id: str) -> tuple[dict[str, Any] | None, str]:
    url = f"https://arxiv.org/abs/{urllib.parse.quote(arxiv_id)}"
    html, status = request_text(url)
    if html is None:
        return None, status
    return parse_arxiv_abs_html(html, arxiv_id, url), "ok"


def fetch_alphaxiv_links(arxiv_id: str) -> tuple[dict[str, Any] | None, str]:
    url = f"https://www.alphaxiv.org/abs/{urllib.parse.quote(arxiv_id)}"
    html, status = request_text(url)
    if html is None:
        return None, status
    title_match = re.search(r"<title>(.*?)</title>", html, flags=re.DOTALL | re.IGNORECASE)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else None
    return {
        "arxiv_id": arxiv_id,
        "url": url,
        "title": title,
        "github_repos": extract_github_repos(html),
        "source_status": "ok",
    }, "ok"


def fetch_semantic_scholar_meta(arxiv_id: str) -> tuple[dict[str, Any] | None, str]:
    fields = "title,year,venue,url,externalIds"
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
        "url": payload.get("url"),
        "externalIds": payload.get("externalIds") or {},
        "source_status": "ok",
    }, "ok"


def search_github_repos_for_paper(query: str, *, paper_title: str | None, arxiv_ids: list[str], max_results: int) -> tuple[list[str], str]:
    search_terms = []
    search_terms.extend(arxiv_ids)
    if paper_title:
        search_terms.append(paper_title)
    if query and query not in search_terms:
        search_terms.append(query)

    repos: list[str] = []
    seen: set[str] = set()
    statuses: list[str] = []
    for term in search_terms:
        params = urllib.parse.urlencode(
            {
                "q": f"{term} in:name,description,readme",
                "sort": "stars",
                "order": "desc",
                "per_page": max(1, min(max_results, 10)),
            }
        )
        payload, status = request_json(f"https://api.github.com/search/repositories?{params}", headers=github_headers())
        statuses.append(status)
        if not isinstance(payload, dict):
            continue
        for item in payload.get("items", []) or []:
            repo = normalize_repo_name(str(item.get("full_name") or ""))
            if not repo or repo.lower() in seen:
                continue
            if paper_title and is_relevant_to_query(paper_title, item.get("full_name"), item.get("description")):
                seen.add(repo.lower())
                repos.append(repo)
            elif arxiv_ids:
                seen.add(repo.lower())
                repos.append(repo)
            elif is_relevant_to_query(query, item.get("full_name"), item.get("description")):
                seen.add(repo.lower())
                repos.append(repo)
            if len(repos) >= max_results:
                return repos, "ok"
    return repos, "ok" if repos else "; ".join(statuses) or "skipped"


def load_manual_code(path: Path | None) -> dict[str, list[dict[str, Any]]]:
    manual = {"repositories": []}
    if path is None:
        return manual
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("manual"), dict):
        data = data["manual"]
    if not isinstance(data, dict):
        raise ValueError("manual code signals must be a JSON object")
    repositories = data.get("repositories", [])
    if repositories is None:
        repositories = []
    if not isinstance(repositories, list):
        raise ValueError("manual.repositories must be a list")
    manual["repositories"] = [item if isinstance(item, dict) else {"url": item} for item in repositories]
    return manual


def repository_trace_score(repo: dict[str, Any]) -> int:
    readme = repo.get("readme_signals") or {}
    score = 0.0
    if readme.get("arxiv_id_hits"):
        score += 35
    score += min(25, float(readme.get("title_token_overlap") or 0) * 35)
    if readme.get("official_claim"):
        score += 20
    if readme.get("unofficial_claim"):
        score -= 10
    if any(source in repo.get("discovered_via", []) for source in ("papers_with_code", "arxiv", "alphaxiv", "manual", "explicit")):
        score += 15
    return clamp(score)


def repository_artifact_score(repo: dict[str, Any]) -> int:
    readme = repo.get("readme_signals") or {}
    root = repo.get("root_signals") or {}
    score = 0
    if readme.get("code_coming_soon"):
        return 5
    if readme.get("has_install_instructions") or root.get("has_requirements_file"):
        score += 20
    if readme.get("has_evaluation_instructions") or root.get("has_script_or_eval_path"):
        score += 25
    if readme.get("has_dataset_instructions") or root.get("has_data_path"):
        score += 15
    if readme.get("has_checkpoint_or_weights"):
        score += 15
    if readme.get("has_config_signal") or root.get("has_config_dir"):
        score += 10
    if readme.get("has_result_table"):
        score += 10
    if root.get("has_examples_or_notebooks"):
        score += 5
    return clamp(score)


def repository_maintenance_score(repo: dict[str, Any]) -> int:
    score = 0.0
    score += log_score(repo.get("stars", 0), 5, 25)
    score += log_score(repo.get("forks", 0), 4, 10)
    age = days_since(repo.get("pushed_at"))
    if age is not None:
        if age <= 30:
            score += 30
        elif age <= 90:
            score += 22
        elif age <= 365:
            score += 12
        else:
            score += 3
    if repo.get("license"):
        score += 10
    if repo.get("has_ci"):
        score += 10
    if repo.get("has_release"):
        score += 8
    if not repo.get("archived"):
        score += 7
    return clamp(score)


def repository_evaluation_score(repo: dict[str, Any]) -> int:
    readme = repo.get("readme_signals") or {}
    root = repo.get("root_signals") or {}
    score = 80 if readme.get("has_evaluation_instructions") or root.get("has_script_or_eval_path") else 25
    if readme.get("has_result_table"):
        score += 15
    if readme.get("code_coming_soon"):
        score = min(score, 20)
    return clamp(score)


def best_repo(repos: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not repos:
        return None
    return max(
        repos,
        key=lambda repo: (
            repository_trace_score(repo),
            repository_artifact_score(repo),
            repository_maintenance_score(repo),
            repo.get("stars", 0),
        ),
    )


def compute_scores(repositories: list[dict[str, Any]]) -> dict[str, Any]:
    repo = best_repo(repositories)
    if not repo:
        return {
            "paper_code_trace_score": 0,
            "paper_repo_traceability": 0,
            "code_availability": 0,
            "artifact_completeness": 0,
            "maintenance_health": 0,
            "license_clarity": 0,
            "evaluation_readiness": 0,
            "code_availability_risk": "high",
        }

    trace = repository_trace_score(repo)
    artifact = repository_artifact_score(repo)
    maintenance = repository_maintenance_score(repo)
    readme = repo.get("readme_signals") or {}
    root = repo.get("root_signals") or {}
    license_score = 100 if repo.get("license") or root.get("has_license_file") else 20
    eval_score = repository_evaluation_score(repo)
    code_availability = artifact
    if readme.get("code_coming_soon"):
        code_availability = 5

    raw = (0.35 * trace) + (0.20 * code_availability) + (0.15 * artifact) + (0.15 * maintenance) + (0.10 * eval_score) + (0.05 * license_score)
    penalty = 0
    if trace < 30:
        penalty += 12
    if code_availability < 35:
        penalty += 15
    if eval_score < 50:
        penalty += 8
    if license_score < 50:
        penalty += 5
    score = clamp(raw - penalty)
    if readme.get("code_coming_soon") or trace < 25 or code_availability < 25:
        risk = "high"
    elif score < 60 or eval_score < 60 or license_score < 60:
        risk = "medium"
    else:
        risk = "low"

    return {
        "paper_code_trace_score": score,
        "paper_repo_traceability": trace,
        "code_availability": code_availability,
        "artifact_completeness": artifact,
        "maintenance_health": maintenance,
        "license_clarity": license_score,
        "evaluation_readiness": eval_score,
        "code_availability_risk": risk,
    }


def derive_risk_flags(repositories: list[dict[str, Any]], sources: dict[str, Any], source_status: dict[str, str], scores: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    if not repositories:
        flags.append("没有发现可检查的 GitHub 代码库；当前只能把论文当作概念或静态文献处理。")
        return flags

    repo = best_repo(repositories)
    assert repo is not None
    readme = repo.get("readme_signals") or {}
    root = repo.get("root_signals") or {}
    if scores["paper_repo_traceability"] < 35:
        flags.append(f"最佳候选代码库 {repo.get('repo')} 与论文标题或 arXiv ID 的追踪关系弱，可能不是官方实现。")
    if readme.get("code_coming_soon"):
        flags.append(f"候选代码库 {repo.get('repo')} 出现 code coming soon / 未发布代码信号。")
    license_unconfirmed = not repo.get("license") and not root.get("has_license_file")
    if license_unconfirmed and str(repo.get("source_status") or "").startswith("fallback"):
        flags.append(f"候选代码库 {repo.get('repo')} 因 GitHub API 限流等原因未能确认 license，复用边界需要后续核验。")
    elif license_unconfirmed:
        flags.append(f"候选代码库 {repo.get('repo')} 缺少明确 license，复用边界不清。")
    age = days_since(repo.get("pushed_at"))
    if age is not None and age > 365:
        flags.append(f"候选代码库 {repo.get('repo')} 超过一年未 push，后续静态检查可能被依赖老化拖住。")
    if not (readme.get("has_install_instructions") or root.get("has_requirements_file")):
        flags.append(f"候选代码库 {repo.get('repo')} 缺少清晰安装入口。")
    if not (readme.get("has_evaluation_instructions") or root.get("has_script_or_eval_path")):
        flags.append(f"候选代码库 {repo.get('repo')} 缺少 evaluation / benchmark 脚本信号。")
    if not (readme.get("has_dataset_instructions") or root.get("has_data_path")):
        flags.append(f"候选代码库 {repo.get('repo')} 缺少数据获取说明。")
    if not readme.get("has_checkpoint_or_weights"):
        flags.append(f"候选代码库 {repo.get('repo')} 未发现公开 checkpoint / pretrained weights 信号。")
    if readme.get("unofficial_claim") and not readme.get("official_claim"):
        flags.append(f"候选代码库 {repo.get('repo')} 声明为 unofficial / reimplementation，不能直接代表论文作者实现。")
    if not sources.get("papers_with_code") and not any(item.get("github_repos") for item in sources.get("arxiv", []) + sources.get("alphaxiv", [])):
        flags.append("Papers with Code、arXiv、alphaXiv 未提供明确代码入口，需要手工核验作者主页或论文附录。")
    failures = [name for name, status in source_status.items() if status not in {"ok", "skipped"}]
    if len(failures) >= 2:
        flags.append("多个论文到代码来源抓取失败，本次代码追踪不完整。")
    return flags


def derive_traceability_hypotheses(risk_flags: list[str], scores: dict[str, Any]) -> list[str]:
    hypotheses = []
    if scores["paper_repo_traceability"] < 35:
        hypotheses.append("这篇论文可能没有稳定官方代码，或公开仓库与论文主张没有直接绑定。")
    if scores["evaluation_readiness"] < 50:
        hypotheses.append("即使代码存在，也可能缺少最低成本静态评价入口，后续复现负责人会先卡在脚本和指标定义上。")
    if scores["artifact_completeness"] < 45:
        hypotheses.append("代码库可能只展示核心模块，缺数据、权重或配置，无法支撑前期可做性判断。")
    if scores["code_availability_risk"] == "low":
        hypotheses.append("代码追踪信号较完整，下一步适合做只读静态审计，而不是立即跑实验。")
    if any("license" in flag.lower() for flag in risk_flags):
        hypotheses.append("即使 idea 可做，也应避免把不可复用代码作为方案依赖。")
    return hypotheses


def derive_prechecks(repositories: list[dict[str, Any]], scores: dict[str, Any]) -> list[str]:
    prechecks = [
        "确认论文页面、Papers with Code、README、arXiv ID 是否指向同一代码库；不一致时优先找作者官方链接。",
        "只读检查 README、requirements、configs、scripts、data/checkpoint 链接，判断复现负责人是否有明确入口。",
        "对照论文结果表和代码库 result table / benchmark script，确认指标名称、数据集和设置是否一致。",
    ]
    if scores["paper_repo_traceability"] < 45:
        prechecks.append("手工核验作者主页、项目页、论文附录和 issue，确认是否存在隐藏或迁移后的官方仓库。")
    if scores["evaluation_readiness"] < 60:
        prechecks.append("先要求找到 eval 命令或 benchmark 配置；找不到则把 idea 降级为高风险，不进入实验计划。")
    if scores["code_availability_risk"] != "low":
        prechecks.append("抽样阅读 open issues 和最近 commits，优先寻找安装失败、数据缺失、结果对不上等负面证据。")
    if repositories:
        prechecks.append("保留最佳候选仓库的 commit 时间、license 和 README 命中证据，写入 Decision Memo。")
    return prechecks


def collect_sources(
    query: str,
    *,
    arxiv_ids: list[str],
    github_repos: list[str],
    paper_title: str | None,
    manual: dict[str, list[dict[str, Any]]],
    github_max: int,
    offline: bool,
) -> tuple[dict[str, Any], dict[str, str], list[dict[str, Any]]]:
    sources: dict[str, Any] = {
        "papers_with_code": [],
        "arxiv": [],
        "alphaxiv": [],
        "semantic_scholar": [],
        "github": [],
        "manual": manual,
    }
    status = {name: "skipped" for name in sources}
    status["manual"] = "ok"

    repo_sources: dict[str, set[str]] = {}

    def add_repo(repo_name: str | None, source: str) -> None:
        normalized = normalize_repo_name(repo_name or "")
        if not normalized:
            return
        repo_sources.setdefault(normalized, set()).add(source)

    for repo in github_repos:
        add_repo(repo, "explicit")
    for item in manual.get("repositories", []):
        add_repo(str(item.get("repo") or item.get("url") or ""), "manual")

    if offline:
        return sources, status, []

    papers, pwc_repos, pwc_status = fetch_papers_with_code(query, arxiv_ids=arxiv_ids, paper_title=paper_title, max_results=github_max)
    sources["papers_with_code"] = papers
    status["papers_with_code"] = pwc_status
    for repo in pwc_repos:
        add_repo(str(repo.get("repo") or repo.get("url") or repo.get("name") or ""), "papers_with_code")

    arxiv_statuses: list[str] = []
    alphaxiv_statuses: list[str] = []
    s2_statuses: list[str] = []
    inferred_title = paper_title
    for arxiv_id in arxiv_ids:
        arxiv_item, arxiv_status = fetch_arxiv_abs(arxiv_id)
        arxiv_statuses.append(arxiv_status)
        if arxiv_item:
            sources["arxiv"].append(arxiv_item)
            inferred_title = inferred_title or arxiv_item.get("title")
            for repo in arxiv_item.get("github_repos", []):
                add_repo(repo, "arxiv")
        alphaxiv_item, alphaxiv_status = fetch_alphaxiv_links(arxiv_id)
        alphaxiv_statuses.append(alphaxiv_status)
        if alphaxiv_item:
            sources["alphaxiv"].append(alphaxiv_item)
            for repo in alphaxiv_item.get("github_repos", []):
                add_repo(repo, "alphaxiv")
        s2_item, s2_status = fetch_semantic_scholar_meta(arxiv_id)
        s2_statuses.append(s2_status)
        if s2_item:
            sources["semantic_scholar"].append(s2_item)
            inferred_title = inferred_title or s2_item.get("title")
    if arxiv_ids:
        status["arxiv"] = "ok" if sources["arxiv"] else "; ".join(arxiv_statuses)
        status["alphaxiv"] = "ok" if sources["alphaxiv"] else "; ".join(alphaxiv_statuses)
        status["semantic_scholar"] = "ok" if sources["semantic_scholar"] else "; ".join(s2_statuses)

    searched_repos, search_status = search_github_repos_for_paper(query, paper_title=inferred_title, arxiv_ids=arxiv_ids, max_results=github_max)
    for repo in searched_repos:
        add_repo(repo, "github_search")

    github_statuses: list[str] = [search_status]
    for repo_name, discovered_via in list(repo_sources.items())[: max(github_max, len(github_repos))]:
        item, item_status = fetch_github_repo_detail(
            repo_name,
            arxiv_ids=arxiv_ids,
            paper_title=inferred_title,
            discovered_via=sorted(discovered_via),
        )
        github_statuses.append(item_status)
        if not item:
            continue
        if "github_search" not in discovered_via or is_relevant_to_query(query, item.get("repo"), item.get("description")) or repository_trace_score(item) > 0:
            sources["github"].append(item)
    if sources["github"]:
        warnings = [item for item in github_statuses if item and item != "ok"]
        status["github"] = "ok" if not warnings else "ok_with_warnings: " + "; ".join(warnings[:4])
    else:
        status["github"] = "; ".join(github_statuses) or "skipped"
    return sources, status, sources["github"]


def build_ledger_markdown(payload: dict[str, Any]) -> str:
    scores = payload["scores"]
    sources = payload["sources"]
    repos = payload.get("candidate_repositories", [])
    lines = [
        f"# 论文到代码库追踪账本：{payload['query']}",
        "",
        f"**项目编号**：`{payload['project_id']}`  ",
        f"**想法编号**：`{payload['idea_id']}`  ",
        f"**生成时间**：{payload['created_at']}  ",
        "",
        "## 总体判断",
        "",
        "| 指标 | 分数 / 状态 |",
        "|---|---:|",
        f"| paper_code_trace_score | {scores['paper_code_trace_score']} |",
        f"| paper_repo_traceability | {scores['paper_repo_traceability']} |",
        f"| code_availability | {scores['code_availability']} |",
        f"| artifact_completeness | {scores['artifact_completeness']} |",
        f"| maintenance_health | {scores['maintenance_health']} |",
        f"| license_clarity | {scores['license_clarity']} |",
        f"| evaluation_readiness | {scores['evaluation_readiness']} |",
        f"| code_availability_risk | {scores['code_availability_risk']} |",
        "",
        "**解释**：论文到代码库追踪是前期调研的软门控。它只判断代码是否可追踪、可静态审计、是否暴露后续复现风险，不要求现在复现论文。",
        "",
        "## 数据源状态",
        "",
        "| 来源 | 状态 |",
        "|---|---|",
    ]
    for name, status in payload.get("source_status", {}).items():
        lines.append(f"| {name} | {status} |")

    lines.extend(["", "## 候选代码库", "", "| repo | 来源 | stars | pushed | license | trace | artifacts | eval | 风险线索 |", "|---|---|---:|---|---|---:|---:|---:|---|"])
    for repo in repos:
        readme = repo.get("readme_signals") or {}
        risk_hint = []
        if readme.get("code_coming_soon"):
            risk_hint.append("code coming soon")
        if readme.get("unofficial_claim"):
            risk_hint.append("unofficial")
        if not repo.get("license"):
            if str(repo.get("source_status") or "").startswith("fallback"):
                risk_hint.append("license unconfirmed")
            else:
                risk_hint.append("no license")
        lines.append(
            f"| [{md_cell(repo.get('repo'))}]({repo.get('url')}) | {md_cell(', '.join(repo.get('discovered_via') or []))} | "
            f"{repo.get('stars', 0)} | {repo.get('pushed_at') or ''} | {repo.get('license') or ''} | "
            f"{repository_trace_score(repo)} | {repository_artifact_score(repo)} | {repository_evaluation_score(repo)} | {md_cell(', '.join(risk_hint) or '无')} |"
        )
    if not repos:
        lines.append("| 无 |  | 0 |  |  | 0 | 0 | 0 | 未发现代码库 |")

    lines.extend(["", "## 论文来源链接", "", "| 来源 | 标题 / 条目 | 代码线索 | 链接 |", "|---|---|---|---|"])
    for item in sources.get("papers_with_code", []):
        lines.append(f"| Papers with Code | {md_cell(item.get('title') or item.get('id'))} | API paper match | {item.get('url') or ''} |")
    for item in sources.get("arxiv", []):
        lines.append(f"| arXiv | {md_cell(item.get('title') or item.get('arxiv_id'))} | {md_cell(', '.join(item.get('github_repos') or []) or '无')} | {item.get('url')} |")
    for item in sources.get("alphaxiv", []):
        lines.append(f"| alphaXiv | {md_cell(item.get('title') or item.get('arxiv_id'))} | {md_cell(', '.join(item.get('github_repos') or []) or '无')} | {item.get('url')} |")
    for item in sources.get("semantic_scholar", []):
        lines.append(f"| Semantic Scholar | {md_cell(item.get('title') or item.get('arxiv_id'))} | metadata | {item.get('url') or ''} |")

    lines.extend(["", "## 风险旗标", ""])
    for flag in payload.get("risk_flags", []):
        lines.append(f"- {flag}")
    if not payload.get("risk_flags"):
        lines.append("- 未发现明确论文到代码库追踪风险旗标。")

    lines.extend(["", "## 追踪假设", ""])
    for item in payload.get("traceability_hypotheses", []):
        lines.append(f"- {item}")

    lines.extend(["", "## 推荐低成本预检", ""])
    for item in payload.get("recommended_prechecks", []):
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def scout(
    query: str,
    *,
    project: str,
    idea: str,
    root: Path,
    arxiv_ids: list[str],
    github_repos: list[str],
    paper_title: str | None,
    manual_code: Path | None,
    github_max: int = 5,
    offline: bool = False,
) -> dict[str, Any]:
    manual = load_manual_code(manual_code)
    sources, source_status, repositories = collect_sources(
        query,
        arxiv_ids=arxiv_ids,
        github_repos=github_repos,
        paper_title=paper_title,
        manual=manual,
        github_max=github_max,
        offline=offline,
    )
    scores = compute_scores(repositories)
    risk_flags = derive_risk_flags(repositories, sources, source_status, scores)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "project_id": project,
        "idea_id": idea,
        "query": query,
        "paper_title": paper_title,
        "arxiv_ids": arxiv_ids,
        "created_at": now_iso(),
        "sources": sources,
        "source_status": source_status,
        "candidate_repositories": repositories,
        "scores": scores,
        "risk_flags": risk_flags,
        "traceability_hypotheses": derive_traceability_hypotheses(risk_flags, scores),
        "recommended_prechecks": derive_prechecks(repositories, scores),
    }
    output_dir = root / "projects" / project / "signals" / idea
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "paper_code.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "PAPER_CODE_LEDGER.md").write_text(build_ledger_markdown(payload), encoding="utf-8")
    payload["output_dir"] = str(output_dir)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trace a paper to code repositories for pre-experiment due diligence.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scout_parser = subparsers.add_parser("scout", help="Collect paper-to-code signals and write a project-local ledger.")
    scout_parser.add_argument("query", help="Paper title, idea, or search query.")
    scout_parser.add_argument("--project", required=True, help="Project slug.")
    scout_parser.add_argument("--idea", required=True, help="Idea slug.")
    scout_parser.add_argument("--root", type=Path, default=Path("."), help="Repository root. Defaults to current directory.")
    scout_parser.add_argument("--arxiv-id", action="append", default=[], help="arXiv ID to inspect. Can be repeated.")
    scout_parser.add_argument("--paper-title", help="Exact paper title when known.")
    scout_parser.add_argument("--github-repo", action="append", default=[], help="Known GitHub repo owner/name or URL. Can be repeated.")
    scout_parser.add_argument("--manual-code", type=Path, help="Manual JSON file with repositories to inspect.")
    scout_parser.add_argument("--github-max", type=int, default=5, help="Max GitHub candidates to inspect.")
    scout_parser.add_argument("--offline", action="store_true", help="Skip network sources; useful for tests.")
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
                paper_title=args.paper_title,
                manual_code=args.manual_code,
                github_max=args.github_max,
                offline=args.offline,
            )
        except Exception as exc:
            print(f"paper code scout failed: {exc}", file=sys.stderr)
            return 2
        print(json.dumps({"output_dir": payload["output_dir"], "scores": payload["scores"]}, ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
