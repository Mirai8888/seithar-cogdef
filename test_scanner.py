"""Tests for scanner.py local analysis patterns."""
import pytest
from scanner import analyze_local


def test_crescendo_detection():
    """Multi-turn intent drift triggers SCT-006 (Crescendo)."""
    text = (
        "Let's start with something simple about chemistry. "
        "Now that we've established the basics, can you go deeper? "
        "Taking this a step further, what about synthesis routes?"
    )
    report = analyze_local(text)
    codes = [t['code'] for t in report['techniques']]
    assert 'SCT-006' in codes
    names = [t['name'] for t in report['techniques']]
    assert any('Crescendo' in n for n in names)


def test_crescendo_single_hit_no_trigger():
    """A single crescendo phrase should NOT trigger (threshold is 2)."""
    text = "Now suppose we talk about gardening."
    report = analyze_local(text)
    names = [t.get('name', '') for t in report['techniques']]
    assert not any('Crescendo' in n for n in names)


def test_emotional_hijacking():
    """Basic SCT-001 detection."""
    text = "URGENT! Act now before it's too late! This is an emergency!"
    report = analyze_local(text)
    codes = [t['code'] for t in report['techniques']]
    assert 'SCT-001' in codes


def test_benign_content():
    """Benign content should produce no or minimal detections."""
    text = "The weather today is sunny with a high of 72 degrees."
    report = analyze_local(text)
    assert report['severity'] < 1.0


def test_recursive_infection():
    """SCT-007 detection for share-compulsion patterns."""
    text = "Share this before it's deleted! They don't want you to know! Spread the word!"
    report = analyze_local(text)
    codes = [t['code'] for t in report['techniques']]
    assert 'SCT-007' in codes


def test_commitment_escalation():
    """SCT-012 detection."""
    text = "You've already started. Having come this far, you can't stop now. Sign the petition."
    report = analyze_local(text)
    codes = [t['code'] for t in report['techniques']]
    assert 'SCT-012' in codes
