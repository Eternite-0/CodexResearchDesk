from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import paper_code_fetch as pcf
from paper_code_fetch import (
    analyze_readme,
    build_github_repo_fallback,
    compute_scores,
    extract_github_repos,
    normalize_repo_name,
    parse_github_repo_detail,
    parse_papers_with_code_papers,
    parse_papers_with_code_repositories,
)


class PaperCodeFetchTests(unittest.TestCase):
    def test_extract_and_normalize_github_repos(self) -> None:
        text = "Code: https://github.com/demo/research-code/tree/main and https://github.com/demo/research-code.git."
        self.assertEqual(normalize_repo_name("https://github.com/demo/research-code/tree/main"), "demo/research-code")
        self.assertEqual(normalize_repo_name("https://github.com/demo/research-code."), "demo/research-code")
        self.assertEqual(extract_github_repos(text), ["demo/research-code"])

    def test_parse_papers_with_code_payloads(self) -> None:
        papers = parse_papers_with_code_papers(
            {
                "results": [
                    {
                        "id": "demo-paper",
                        "title": "Demo Paper",
                        "arxiv_id": "2601.00001",
                        "url_abs": "https://paperswithcode.com/paper/demo-paper",
                    }
                ]
            }
        )
        repos = parse_papers_with_code_repositories(
            {
                "results": [
                    {
                        "name": "demo/research-code",
                        "url": "https://github.com/demo/research-code",
                        "is_official": True,
                    }
                ]
            }
        )
        self.assertEqual(papers[0]["id"], "demo-paper")
        self.assertEqual(repos[0]["repo"], "demo/research-code")

    def test_analyze_readme_detects_trace_and_artifacts(self) -> None:
        readme = """
        # Official implementation of Demo Paper
        arXiv:2601.00001
        pip install -r requirements.txt
        Download dataset from Hugging Face. Pretrained checkpoints are available.
        Run python eval.py for evaluation and benchmark metrics.
        | method | score |
        |---|---:|
        | ours | 90 |
        """
        signals = analyze_readme(readme, arxiv_ids=["2601.00001"], paper_title="Demo Paper")
        self.assertTrue(signals["official_claim"])
        self.assertEqual(signals["arxiv_id_hits"], ["2601.00001"])
        self.assertTrue(signals["has_install_instructions"])
        self.assertTrue(signals["has_evaluation_instructions"])
        self.assertTrue(signals["has_result_table"])

    def test_compute_scores_for_traceable_repo(self) -> None:
        repo = parse_github_repo_detail(
            {
                "full_name": "demo/research-code",
                "html_url": "https://github.com/demo/research-code",
                "description": "Official implementation of Demo Paper",
                "stargazers_count": 400,
                "forks_count": 40,
                "open_issues_count": 3,
                "license": {"spdx_id": "MIT"},
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-06-01T00:00:00Z",
                "pushed_at": "2026-06-01T00:00:00Z",
                "default_branch": "main",
                "language": "Python",
                "archived": False,
                "owner": {"login": "demo", "type": "Organization"},
            },
            readme_text=(
                "Official implementation of Demo Paper arXiv:2601.00001. "
                "pip install -r requirements.txt. Download dataset. "
                "Pretrained checkpoints. Run eval.py for benchmark metrics. "
                "| method | score |\n|---|---:|\n| ours | 90 |"
            ),
            root_contents=[
                {"name": "requirements.txt"},
                {"name": "configs"},
                {"name": "scripts"},
                {"name": "LICENSE"},
            ],
            topics=["benchmark"],
            has_release=True,
            has_ci=True,
            arxiv_ids=["2601.00001"],
            paper_title="Demo Paper",
            discovered_via=["papers_with_code"],
        )
        scores = compute_scores([repo])
        self.assertGreaterEqual(scores["paper_code_trace_score"], 70)
        self.assertEqual(scores["code_availability_risk"], "low")

    def test_code_coming_soon_is_high_risk(self) -> None:
        repo = parse_github_repo_detail(
            {
                "full_name": "demo/placeholder",
                "html_url": "https://github.com/demo/placeholder",
                "description": "Demo Paper",
                "stargazers_count": 10,
                "forks_count": 0,
                "license": None,
                "pushed_at": "2026-06-01T00:00:00Z",
                "archived": False,
                "owner": {"login": "demo", "type": "User"},
            },
            readme_text="Demo Paper. Code coming soon.",
            root_contents=[],
            topics=[],
            has_release=False,
            has_ci=False,
            arxiv_ids=["2601.00001"],
            paper_title="Demo Paper",
            discovered_via=["github_search"],
        )
        scores = compute_scores([repo])
        self.assertEqual(scores["code_availability_risk"], "high")
        self.assertLess(scores["code_availability"], 10)

    def test_github_api_fallback_keeps_repo_trace(self) -> None:
        original_request_text = pcf.request_text

        def fake_request_text(url: str, **kwargs):
            if "README.md" in url:
                return "Official implementation of Demo Paper arXiv:2601.00001. Run eval.py.", "ok"
            return None, "http_404"

        pcf.request_text = fake_request_text
        try:
            repo = build_github_repo_fallback(
                "demo/research-code",
                arxiv_ids=["2601.00001"],
                paper_title="Demo Paper",
                discovered_via=["arxiv", "explicit"],
                original_status="http_403",
            )
        finally:
            pcf.request_text = original_request_text
        self.assertIsNotNone(repo)
        assert repo is not None
        self.assertEqual(repo["repo"], "demo/research-code")
        self.assertIn("fallback_after_http_403", repo["source_status"])
        self.assertGreaterEqual(compute_scores([repo])["paper_repo_traceability"], 60)

    def test_cli_offline_writes_project_local_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cmd = [
                sys.executable,
                str(ROOT / "tools" / "paper_code_fetch.py"),
                "scout",
                "Demo Paper",
                "--project",
                "demo-project",
                "--idea",
                "demo-idea",
                "--root",
                str(root),
                "--offline",
            ]
            result = subprocess.run(cmd, check=True, text=True, capture_output=True)
            self.assertIn("paper_code_trace_score", result.stdout)
            output = root / "projects" / "demo-project" / "signals" / "demo-idea"
            self.assertTrue((output / "paper_code.json").exists())
            self.assertTrue((output / "PAPER_CODE_LEDGER.md").exists())
            data = json.loads((output / "paper_code.json").read_text(encoding="utf-8"))
            self.assertEqual(data["scores"]["code_availability_risk"], "high")


if __name__ == "__main__":
    unittest.main()
