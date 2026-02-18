# seithar-cogdef

**Cognitive Defense Instrumentation System — Seithar Group**

Scanner and inoculation engine for detecting cognitive exploitation in text, URLs, files, and agent skill definitions.

## Quick Start

```bash
# Scan a file for cognitive exploitation vectors
python scanner.py --file suspicious.md

# LLM-enhanced deep analysis (optional)
export ANTHROPIC_API_KEY=your_key
python scanner.py --file suspicious.md --llm

# Batch scan a directory
python scanner.py --batch /path/to/skills/

# Scan a URL
python scanner.py --url https://example.com/article
```

Zero dependencies for local pattern matching. LLM mode optional (Anthropic API).

## Components

| File | Purpose |
|------|---------|
| `scanner.py` | Cognitive threat scanner — pattern matching + LLM analysis + SCT taxonomy mapping |
| `inoculator.py` | Inoculation engine — generates cognitive defense training content |
| `SKILL.md` | OpenClaw agent integration skill definition |

## Taxonomy

Maps findings to **Seithar Cognitive Threat taxonomy** (SCT-001 through SCT-012) and **DISARM framework**.

**Input:** URLs, files, raw text, RSS feeds, directories  
**Output:** Structured threat reports with classification, severity, techniques, defensive recommendations

## Related

- [seithar-research](https://github.com/Mirai8888/seithar-research) — Research publications
- [seithar-intel](https://github.com/Mirai8888/seithar-intel) — Threat intelligence skill
- [HoleSpawn](https://github.com/Mirai8888/HoleSpawn) — Cognitive substrate profiling
- [ThreatMouth](https://github.com/Mirai8888/ThreatMouth) — Threat intelligence bot

---

Seithar Group Research Division | 認知作戦 | [seithar.com](https://seithar.com)
