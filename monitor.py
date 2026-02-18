#!/usr/bin/env python3
"""
Seithar Group -- GitHub Monitoring Hooks

Checks stars/forks/clones on all Mirai8888 repos and searches for
mentions of "seithar" or "SCT-" in recent GitHub code search.
Outputs a markdown summary report.
"""

import json
import os
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import quote

# ── Config ─────────────────────────────────────────────────────────────────
GITHUB_PAT = os.environ.get("GITHUB_PAT", "")
OWNER = "Mirai8888"
REPOS = [
    "HoleSpawn",
    "ThreatMouth",
    "seithar",
    "seithar-cogdef",
    "seithar-intel",
    "seithar-autoprompt",
]
SEARCH_TERMS = ["seithar", "SCT-"]


def _api(path: str) -> dict | list | None:
    """Call GitHub API with PAT auth."""
    url = f"https://api.github.com{path}"
    req = Request(url)
    req.add_header("Authorization", f"Bearer {GITHUB_PAT}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        return {"error": e.code, "reason": str(e.reason), "url": url}
    except Exception as e:
        return {"error": str(e)}


def get_repo_stats() -> list[dict]:
    """Get stars, forks, watchers for each repo."""
    results = []
    for repo in REPOS:
        data = _api(f"/repos/{OWNER}/{repo}")
        if isinstance(data, dict) and "error" not in data:
            results.append({
                "repo": repo,
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "watchers": data.get("subscribers_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "updated": data.get("updated_at", ""),
            })
        else:
            results.append({"repo": repo, "error": data})
    return results


def get_clone_traffic(repo: str) -> dict | None:
    """Get clone traffic (requires push access)."""
    data = _api(f"/repos/{OWNER}/{repo}/traffic/clones")
    if isinstance(data, dict) and "error" not in data:
        return {"total": data.get("count", 0), "unique": data.get("uniques", 0)}
    return None


def search_mentions(term: str) -> dict:
    """Search GitHub code for mentions (excluding our own org)."""
    query = quote(f"{term} -user:{OWNER}")
    data = _api(f"/search/code?q={query}&per_page=5")
    if isinstance(data, dict) and "error" not in data:
        return {
            "term": term,
            "total_count": data.get("total_count", 0),
            "items": [
                {
                    "repo": item.get("repository", {}).get("full_name", ""),
                    "path": item.get("path", ""),
                    "url": item.get("html_url", ""),
                }
                for item in data.get("items", [])[:5]
            ],
        }
    return {"term": term, "total_count": 0, "error": data}


def generate_report() -> str:
    """Generate full markdown monitoring report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Seithar Monitoring Report",
        f"**Generated:** {now}",
        f"**Owner:** {OWNER}",
        "",
        "## Repository Stats",
        "",
        "| Repo | ⭐ Stars | 🍴 Forks | 👀 Watchers | Issues | Last Updated |",
        "|------|---------|---------|------------|--------|-------------|",
    ]

    stats = get_repo_stats()
    for s in stats:
        if "error" in s:
            lines.append(f"| {s['repo']} | ❌ Error | | | | |")
        else:
            lines.append(
                f"| {s['repo']} | {s['stars']} | {s['forks']} | {s['watchers']} "
                f"| {s['open_issues']} | {s['updated'][:10]} |"
            )

    lines.extend(["", "## Clone Traffic (14-day)", ""])
    for repo in REPOS:
        clones = get_clone_traffic(repo)
        if clones:
            lines.append(f"- **{repo}**: {clones['total']} clones ({clones['unique']} unique)")
        else:
            lines.append(f"- **{repo}**: N/A (insufficient permissions or no data)")

    lines.extend(["", "## External Mentions", ""])
    for term in SEARCH_TERMS:
        result = search_mentions(term)
        lines.append(f"### \"{term}\"")
        lines.append(f"Total results (excluding {OWNER}): {result.get('total_count', 0)}")
        if result.get("items"):
            for item in result["items"]:
                lines.append(f"- [{item['repo']}]({item['url']}) — `{item['path']}`")
        elif result.get("error"):
            lines.append(f"- ⚠️ Search error: {result['error']}")
        else:
            lines.append("- No external mentions found")
        lines.append("")

    lines.extend(["---", f"*Report generated by seithar-cogdef/monitor.py*"])
    return "\n".join(lines)


if __name__ == "__main__":
    report = generate_report()
    print(report)
