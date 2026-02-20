# MISSION.md — seithar-cogdef

**Status:** Operational  
**Last Updated:** 2026-02-20  
**Tests:** 72 passing (inoculator + scanner + evolve)

## Purpose
Detect and classify cognitive exploitation in content. Defensive instrumentation.
- Scanner: Pattern-based detection of manipulation techniques (crescendo, emotional hijacking, etc.)
- Inoculator: Generate exposure-based inoculation content per SCT code
- Monitor: Cognitive landscape monitoring

## Recent (2026-02-20)
- All 72 tests passing
- Scanner v2 with recursive infection detection
- Inoculator covers all 12 SCT codes
- Note: tests live in repo root (test_*.py), not tests/ directory
