#!/usr/bin/env python3
"""Tests for the Seithar Taxonomy Evolution Engine."""

import json
import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

# Ensure taxonomy package is importable
sys.path.insert(0, str(Path(__file__).parent / "taxonomy"))
import evolve


@pytest.fixture(autouse=True)
def isolated_schema(tmp_path, monkeypatch):
    """Use a temporary schema file for each test."""
    src = Path(__file__).parent / "taxonomy" / "schema.json"
    tmp_schema = tmp_path / "schema.json"
    shutil.copy(src, tmp_schema)
    monkeypatch.setattr(evolve, "SCHEMA_PATH", tmp_schema)
    return tmp_schema


class TestPropose:
    def test_creates_candidate_for_novel_technique(self):
        result = evolve.propose_candidate(
            "Quantum entanglement based subliminal neural resonance attack",
            source="fictional-paper-2026",
            evidence="Observed quantum neural coupling in lab setting",
        )
        assert result["action"] == "created_candidate"
        assert result["code_id"].startswith("SCT-")
        # Should be SCT-015 (next after 012)
        assert result["code_id"] == "SCT-015"

        # Verify it exists in schema
        schema = evolve.load_schema()
        assert "SCT-015" in schema["codes"]
        assert schema["codes"]["SCT-015"]["status"] == "candidate"

    def test_duplicate_proposal_accumulates_evidence(self):
        """Proposing something similar to an existing code adds evidence instead."""
        result = evolve.propose_candidate(
            "Emotional hijacking exploits affective processing urgency fear outrage to bypass rational evaluation",
            source="test-paper",
        )
        # Should match SCT-001 (Emotional Hijacking)
        assert result["action"] == "evidence_added"
        assert result["code_id"] == "SCT-001"


class TestEvidence:
    def test_accumulate_evidence(self):
        result = evolve.accumulate_evidence(
            "SCT-001", source="new-paper", description="New evidence of emotional hijacking"
        )
        assert result["action"] == "evidence_added"
        assert result["total_evidence"] == 2  # original + new

    def test_evidence_nonexistent_code(self):
        result = evolve.accumulate_evidence(
            "SCT-999", source="x", description="y"
        )
        assert result["action"] == "error"


class TestPromotion:
    def test_promotion_threshold(self):
        # Create a candidate with 3 independent sources
        evolve.propose_candidate(
            "Completely novel technique with zero similarity to anything existing xyz123",
            source="source-1",
        )
        schema = evolve.load_schema()
        new_id = [k for k, v in schema["codes"].items() if v["status"] == "candidate"][0]

        evolve.accumulate_evidence(new_id, "source-2", "second observation")
        evolve.accumulate_evidence(new_id, "source-3", "third observation")

        promoted = evolve.promote_candidates(min_sources=3)
        assert len(promoted) == 1
        assert promoted[0]["code_id"] == new_id

        schema = evolve.load_schema()
        assert schema["codes"][new_id]["status"] == "confirmed"

    def test_no_promotion_below_threshold(self):
        evolve.propose_candidate(
            "Another totally unique technique abc987 zzz",
            source="only-one-source",
        )
        promoted = evolve.promote_candidates(min_sources=3)
        assert len(promoted) == 0


class TestDeprecation:
    def test_deprecation_flagging(self, isolated_schema):
        # Set a code's last_seen to 200 days ago
        schema = evolve.load_schema()
        old_date = (datetime.now(timezone.utc) - timedelta(days=200)).strftime("%Y-%m-%d")
        schema["codes"]["SCT-008"]["last_seen"] = old_date
        evolve.save_schema(schema)

        flagged = evolve.deprecation_check(days_unseen=180)
        assert any(f["code_id"] == "SCT-008" for f in flagged)

        schema = evolve.load_schema()
        assert schema["codes"]["SCT-008"]["status"] == "deprecated"


class TestPatterns:
    def test_pattern_generation(self):
        patterns = evolve.generate_scanner_patterns("SCT-001")
        assert len(patterns) > 0
        # Each pattern should be a valid regex
        for p in patterns:
            import re
            re.compile(p)

    def test_patterns_nonexistent(self):
        patterns = evolve.generate_scanner_patterns("SCT-999")
        assert patterns == []


class TestScannerLoadsSchema:
    def test_scanner_loads_from_schema(self):
        """Verify scanner.py can load taxonomy from schema.json."""
        # Import scanner -- it should pick up schema.json
        scanner_path = Path(__file__).parent
        sys.path.insert(0, str(scanner_path))
        # Just verify the loading function works
        from scanner import _load_taxonomy_from_schema
        tax = _load_taxonomy_from_schema()
        assert tax is not None
        assert "SCT-001" in tax
        assert "name" in tax["SCT-001"]


class TestExport:
    def test_export_taxonomy(self):
        result = evolve.export_taxonomy()
        assert "codes" in result
        assert "SCT-001" in result["codes"]
