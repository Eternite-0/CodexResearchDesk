from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from external_signal_fetch import (
    compute_scores,
    derive_risk_flags,
    load_manual_signals,
    parse_alphaxiv_html,
    parse_github_repo,
    parse_hn_hits,
    is_relevant_to_query,
)


class ExternalSignalFetchTests(unittest.TestCase):
    def test_parse_github_repo_and_engineering_score(self) -> None:
        repo = parse_github_repo(
            {
                "full_name": "demo/research",
                "html_url": "https://github.com/demo/research",
                "description": "A benchmark with fixed budget traces",
                "stargazers_count": 1200,
                "forks_count": 110,
                "watchers_count": 1200,
                "open_issues_count": 7,
                "license": {"spdx_id": "MIT"},
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-06-01T00:00:00Z",
                "pushed_at": "2026-06-01T00:00:00Z",
                "language": "Python",
                "archived": False,
                "owner": {"login": "microsoft", "type": "Organization"},
            },
            topics=["benchmark"],
            has_release=True,
            has_ci=True,
        )
        scores = compute_scores(
            {
                "github": [repo],
                "alphaxiv": [],
                "hf_papers": [],
                "hackernews": [],
                "semantic_scholar": [],
                "openalex": [],
                "manual": {"x_posts": [], "reddit_posts": [], "enterprise_adoption": []},
            }
        )
        self.assertEqual(repo["license"], "MIT")
        self.assertGreater(scores["engineering_health"], 60)
        self.assertGreater(scores["institution_or_enterprise_signal"], 40)

    def test_readme_signal_terms_raise_benchmark_score(self) -> None:
        repo = parse_github_repo(
            {
                "full_name": "demo/bench",
                "html_url": "https://github.com/demo/bench",
                "description": "Autonomous research system",
                "stargazers_count": 10,
                "forks_count": 1,
                "license": {"spdx_id": "MIT"},
                "pushed_at": "2026-06-01T00:00:00Z",
                "archived": False,
                "owner": {"login": "demo", "type": "User"},
            },
            readme_terms=["benchmark", "leaderboard", "trace"],
        )
        scores = compute_scores(
            {
                "github": [repo],
                "alphaxiv": [],
                "hf_papers": [],
                "hackernews": [],
                "semantic_scholar": [],
                "openalex": [],
                "manual": {"x_posts": [], "reddit_posts": [], "enterprise_adoption": []},
            }
        )
        self.assertGreaterEqual(scores["benchmark_or_metric_signal"], 50)

    def test_parse_alphaxiv_html(self) -> None:
        html = "<title>Demo Paper | alphaXiv</title> metrics:$R[1]={commentsCount:2,totalVotes:9,publicTotalVotes:42,visitsCount:$R[2]={last24Hours:1,all:1234}}"
        parsed = parse_alphaxiv_html(html, "2601.00001", "https://www.alphaxiv.org/abs/2601.00001")
        self.assertEqual(parsed["comments"], 2)
        self.assertEqual(parsed["publicTotalVotes"], 42)
        self.assertEqual(parsed["visitsAll"], 1234)

    def test_parse_hn_hits(self) -> None:
        hits = parse_hn_hits({"hits": [{"title": "Show HN: Research agent", "points": 21, "num_comments": 4, "url": "https://x.test"}]})
        self.assertEqual(hits[0]["points"], 21)
        self.assertEqual(hits[0]["comments"], 4)

    def test_relevance_filter_expands_sae_and_moe(self) -> None:
        self.assertTrue(is_relevant_to_query("SAE features explain MoE routing", "Scaling sparse autoencoders for expert routing"))
        self.assertFalse(is_relevant_to_query("SAE features explain MoE routing", "CeO2 catalytic materials survey"))

    def test_manual_json_merge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manual.json"
            path.write_text(
                json.dumps(
                    {
                        "x_posts": [{"url": "https://x.test", "likes": 100}],
                        "reddit_posts": [{"url": "https://reddit.test", "score": 50}],
                        "enterprise_adoption": [{"organization": "DemoCorp", "evidence": "uses benchmark"}],
                    }
                ),
                encoding="utf-8",
            )
            manual = load_manual_signals(path)
            self.assertEqual(len(manual["x_posts"]), 1)
            self.assertEqual(len(manual["enterprise_adoption"]), 1)

    def test_hype_risk_and_flags(self) -> None:
        sources = {
            "github": [
                {
                    "repo": "demo/hot",
                    "stars": 50000,
                    "forks": 1000,
                    "pushed_at": "2026-06-01T00:00:00Z",
                    "license": None,
                    "has_release": False,
                    "has_ci": False,
                    "archived": False,
                    "description": "cool autonomous research",
                }
            ],
            "alphaxiv": [{"publicTotalVotes": 300, "comments": 5, "visitsAll": 5000}],
            "hf_papers": [],
            "hackernews": [{"points": 300, "comments": 120}],
            "semantic_scholar": [],
            "openalex": [],
            "manual": {"x_posts": [], "reddit_posts": [], "enterprise_adoption": []},
        }
        scores = compute_scores(sources)
        flags = derive_risk_flags(sources, scores, {"github": "ok", "alphaxiv": "ok"})
        self.assertEqual(scores["hype_risk"], "high")
        self.assertTrue(any("hype" in flag for flag in flags))

    def test_cli_offline_writes_project_local_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cmd = [
                sys.executable,
                str(ROOT / "tools" / "external_signal_fetch.py"),
                "scout",
                "SAE features explain MoE routing",
                "--project",
                "demo-project",
                "--idea",
                "demo-idea",
                "--root",
                str(root),
                "--offline",
            ]
            result = subprocess.run(cmd, check=True, text=True, capture_output=True)
            self.assertIn("external_signal_score", result.stdout)
            output = root / "projects" / "demo-project" / "signals" / "demo-idea"
            self.assertTrue((output / "external_signals.json").exists())
            self.assertTrue((output / "EXTERNAL_SIGNAL_LEDGER.md").exists())


if __name__ == "__main__":
    unittest.main()
