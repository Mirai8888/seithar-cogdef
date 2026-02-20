"""Tests for the Seithar Inoculation Engine."""

import pytest
from inoculator import INOCULATIONS, generate_inoculation, format_inoculation


# ---------------------------------------------------------------------------
# Template completeness
# ---------------------------------------------------------------------------

SCT_CODES = [f"SCT-{i:03d}" for i in range(1, 13)]


@pytest.mark.parametrize("code", SCT_CODES)
def test_inoculation_template_exists(code):
    assert code in INOCULATIONS


@pytest.mark.parametrize("code", SCT_CODES)
def test_template_has_required_fields(code):
    inoc = INOCULATIONS[code]
    for key in ("name", "mechanism_exposure", "recognition_triggers", "weakened_example"):
        assert key in inoc, f"{code} missing {key}"


@pytest.mark.parametrize("code", SCT_CODES)
def test_mechanism_exposure_nonempty(code):
    assert len(INOCULATIONS[code]["mechanism_exposure"]) > 50


@pytest.mark.parametrize("code", SCT_CODES)
def test_recognition_triggers_nonempty(code):
    triggers = INOCULATIONS[code]["recognition_triggers"]
    assert isinstance(triggers, list)
    assert len(triggers) >= 2, f"{code} needs at least 2 recognition triggers"


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def test_generate_valid_code():
    result = generate_inoculation("SCT-001")
    assert "error" not in result
    assert result["sct_code"] == "SCT-001"
    assert "mechanism_exposure" in result
    assert "_metadata" in result
    assert result["_metadata"]["generator"].startswith("SeitharSIE")


def test_generate_invalid_code():
    result = generate_inoculation("SCT-999")
    assert "error" in result


def test_generate_all_codes():
    for code in SCT_CODES:
        result = generate_inoculation(code)
        assert "error" not in result, f"Failed for {code}: {result}"


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def test_format_valid():
    inoc = generate_inoculation("SCT-001")
    text = format_inoculation(inoc)
    assert "SEITHAR INOCULATION ENGINE" in text
    assert "SCT-001" in text
    assert "MECHANISM EXPOSURE" in text
    assert "RECOGNITION TRIGGERS" in text


def test_format_error():
    text = format_inoculation({"error": "test error"})
    assert "ERROR" in text


def test_format_contains_all_triggers():
    inoc = generate_inoculation("SCT-003")
    text = format_inoculation(inoc)
    for trigger in inoc["recognition_triggers"]:
        assert trigger in text


# ---------------------------------------------------------------------------
# Cross-validation: names should be unique
# ---------------------------------------------------------------------------

def test_unique_technique_names():
    names = [INOCULATIONS[c]["name"] for c in SCT_CODES]
    assert len(names) == len(set(names)), "Duplicate technique names found"
