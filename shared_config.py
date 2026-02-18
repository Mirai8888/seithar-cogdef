"""
Seithar Group -- Shared Configuration Module

Cross-repo integration: common paths, constants, and taxonomy import helpers.
All Seithar ecosystem repos should reference this module for shared config.
"""

import os
import sys
import importlib
from pathlib import Path

# ── Version ────────────────────────────────────────────────────────────────
SEITHAR_VERSION = "0.3.0"
SCT_VERSION = "2.0"

# ── Repo Locations ─────────────────────────────────────────────────────────
HOME = Path.home()

REPO_PATHS = {
    "holespawn":        HOME / "HoleSpawn",
    "threatmouth":      HOME / "ThreatMouth",
    "seithar":          HOME / "seithar",
    "seithar-cogdef":   HOME / "seithar-cogdef",
    "seithar-intel":    HOME / "seithar-intel",
    "seithar-autoprompt": HOME / "seithar-autoprompt",
    "seithar-research": HOME / "seithar-research",
}

# ── Common Paths ───────────────────────────────────────────────────────────
OUTPUT_DIR = HOME / "seithar-research" / "output"
DATA_DIR = HOME / "seithar-research" / "data"
TAXONOMY_FILENAME = "taxonomy.py"
TAXONOMY_JSON_FILENAME = "taxonomy.json"

# ── API Endpoints & Constants ──────────────────────────────────────────────
GITHUB_OWNER = "Mirai8888"
GITHUB_API_BASE = "https://api.github.com"
GITHUB_REPOS = [
    "HoleSpawn",
    "ThreatMouth",
    "seithar",
    "seithar-cogdef",
    "seithar-intel",
    "seithar-autoprompt",
]

# ── Taxonomy Import Helpers ────────────────────────────────────────────────

def get_taxonomy_module(repo_name: str = "seithar-cogdef"):
    """
    Import and return the taxonomy module from a given repo.
    seithar-cogdef is the canonical source of truth.
    """
    repo_path = REPO_PATHS.get(repo_name)
    if repo_path is None:
        raise ValueError(f"Unknown repo: {repo_name}")
    repo_str = str(repo_path)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)
    return importlib.import_module("taxonomy")


def get_all_sct_codes() -> list[str]:
    """Return all SCT codes from canonical taxonomy."""
    tax = get_taxonomy_module()
    return tax.all_codes()


def get_sct_entry(code: str) -> dict | None:
    """Look up a single SCT entry from canonical taxonomy."""
    tax = get_taxonomy_module()
    return tax.get_code(code)


def resolve_repo_path(repo_name: str) -> Path:
    """Resolve a repo name to its filesystem path."""
    p = REPO_PATHS.get(repo_name)
    if p is None:
        raise ValueError(f"Unknown repo: {repo_name}. Known: {list(REPO_PATHS.keys())}")
    return p


def ensure_output_dir() -> Path:
    """Create and return the shared output directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR
