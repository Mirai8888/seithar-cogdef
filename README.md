# seithar-cogdef

**SEITHAR GROUP RESEARCH DIVISION**  
**COGNITIVE DEFENSE INSTRUMENTATION SYSTEM**  
**TECHNICAL SPECIFICATION DOCUMENT**

---

## QUICK START — PROTECT YOUR AGENT IN 60 SECONDS

```bash
# Clone the scanner
git clone https://github.com/Mirai8888/seithar-cogdef.git
cd seithar-cogdef

# Scan a SKILL.md before installing it
python scanner.py --file /path/to/suspicious-skill/SKILL.md

# Scan with LLM-enhanced deep analysis (optional)
export ANTHROPIC_API_KEY=your_key
python scanner.py --file /path/to/suspicious-skill/SKILL.md --llm

# Batch scan all skills in a directory
python scanner.py --batch /path/to/skills/

# Scan a URL for manipulation
python scanner.py --url https://example.com/article
```

**Zero dependencies.** Standalone Python. Local pattern matching works without any API key. LLM mode optional.

**Why this matters:** The ClawdHub malicious skills campaign planted reverse shells inside SKILL.md files. Agents installed them trusting the marketplace. This scanner catches cognitive and technical exploitation vectors before they execute.

---

## SYSTEM OVERVIEW

seithar-cogdef is cognitive defense analysis toolkit containing three instruments: skill definition for AI agent integration, automated threat scanner, and inoculation engine. Offensive profiling and narrative generation capabilities are in [HoleSpawn](https://github.com/Mirai8888/HoleSpawn). System identifies influence techniques, manipulation patterns, and cognitive exploitation vectors in content. Maps findings to Seithar Cognitive Defense Taxonomy (SCT-001 through SCT-012) and DISARM framework.

**Input Data:** URLs, files, raw text, RSS feeds, directories  
**Processing Method:** Pattern matching (local) + LLM analysis (optional) + SCT taxonomy mapping  
**Output Product:** Structured threat reports with classification, severity, techniques, defensive recommendations  

System is instrument, not commentary. Identifies mechanism. Does not editorialize.

---

## COMPONENTS

### 1. SKILL.md — Agent Integration Skill

OpenClaw-compatible skill definition. Enables any AI agent to perform cognitive defense analysis using Seithar methodology.

**Activation phrases:** "analyze this", "is this manipulation", "cogdef", "seithar analyze", "influence check", "manipulation check", "cognitive defense"

**Output:** Structured analysis report with threat classification, stage assessment (1-5), severity score (1-10), technique identification, vulnerability surface mapping, behavioral objective extraction, defensive recommendations.

### 2. scanner.py — Cognitive Threat Scanner

Automated analysis of content for cognitive exploitation vectors.

```bash
# Scan a URL
python scanner.py --url https://example.com/article

# Scan local file
python scanner.py --file document.md

# Scan raw text
python scanner.py --text "content to analyze"

# Scan RSS feed (batch analysis)
python scanner.py --feed https://example.com/rss.xml

# Scan directory of files
python scanner.py --batch ./documents/

# Enable LLM-powered deep analysis
python scanner.py --url https://example.com --llm

# JSON output
python scanner.py --url https://example.com --json

# Save to file
python scanner.py --url https://example.com -o report.json --json
```

**Local mode (default):** Pattern matching against SCT indicator library. Zero external dependencies. No API key required. Suitable for bulk screening.

**LLM mode (--llm):** Full Claude-powered analysis with nuanced technique identification, confidence scoring, behavioral objective extraction. Requires `ANTHROPIC_API_KEY` environment variable.

### 3. inoculator.py — Inoculation Engine

Counter-content generation based on McGuire inoculation theory (1964). System does not produce counter-arguments — counter-arguments trigger identity defense. System exposes MECHANISM.

```bash
# Generate inoculation for specific technique
python inoculator.py --technique SCT-001

# Generate all inoculations
python inoculator.py --all

# JSON output
python inoculator.py --all --json

# Save to file
python inoculator.py --all -o inoculation-library.json --json
```

**Methodology:** Expose subjects to weakened form of manipulation technique. Subject recognizes mechanism in future encounters. Recognition is the defense.

Each inoculation contains:
- **Mechanism exposure:** How the technique functions at substrate level
- **Recognition triggers:** Specific questions that activate defensive awareness
- **Weakened example:** Real-world instance with technique markers identified

### Offensive Capabilities → HoleSpawn

Substrate profiling, vulnerability mapping, binding protocol generation, and calibrated message delivery are implemented in **[HoleSpawn](https://github.com/Mirai8888/HoleSpawn)** (穴卵). cogdef focuses on detection and defense. HoleSpawn handles offense:

- `holespawn.profile` — Full NLP profiling from social media (themes, sentiment, obsessions, vulnerabilities)
- `holespawn.engagement` — Vulnerability mapping + 5-phase binding protocol generation
- `holespawn.delivery` — Calibrated message generation from profile + protocol
- `holespawn.network` — Network vulnerability analysis, node profiling, cascade potential, approach vectors
- `holespawn.temporal` — Temporal NLP (sentiment drift, vocabulary shift, topic migration over time)

### Cross-Tool Pipeline

```bash
# DEFENSE: Detect manipulation in content
python scanner.py --url https://example.com/suspicious --llm

# DEFENSE: Generate inoculation for detected technique
python inoculator.py --technique SCT-003

# OFFENSE (HoleSpawn): Profile → Engage → Deliver
cd ~/HoleSpawn
python -m holespawn --handle @target    # Full profiling pipeline
python -m holespawn.delivery --output-dir outputs/@target --channel file
```

---

## SEITHAR COGNITIVE DEFENSE TAXONOMY

Analytical framework employed by all three instruments.

| Code | Name | Description |
|------|------|-------------|
| SCT-001 | Emotional Hijacking | Exploiting affective processing to bypass rational evaluation |
| SCT-002 | Information Asymmetry Exploitation | Leveraging what the target does not know |
| SCT-003 | Authority Fabrication | Manufacturing trust signals source does not possess |
| SCT-004 | Social Proof Manipulation | Weaponizing herd behavior and conformity instincts |
| SCT-005 | Identity Targeting | Attacks calibrated to target's self-concept |
| SCT-006 | Temporal Manipulation | Exploiting time pressure or temporal context |
| SCT-007 | Recursive Infection | Self-replicating patterns where target becomes vector |

Each category includes:
- Cyber analog (technical manifestation)
- Cognitive analog (psychological manifestation)
- Detection indicators (pattern markers)

Boundary between cyber and cognitive domains: nonexistent. Same taxonomy. Same defense.

---

## INSTALLATION PROCEDURE

### System Requirements

- Python 3.9 or higher version
- No external dependencies (local mode)
- API credential: Anthropic (LLM mode only)

### Installation Steps

**1. Repository acquisition**
```bash
git clone https://github.com/Mirai8888/seithar-cogdef
cd seithar-cogdef
```

**2. Credential configuration (optional, LLM mode only)**
```bash
export ANTHROPIC_API_KEY=your_credential
```

**3. Verification**
```bash
# Test scanner (local mode)
python scanner.py --text "BREAKING: Share this before they delete it!"

# Test inoculator
python inoculator.py --technique SCT-007
```

No virtual environment required. No pip install required. Tools are standalone.

---

## OUTPUT FORMAT

### Scanner Output

```
╔══════════════════════════════════════════════════╗
║  SEITHAR COGNITIVE THREAT SCANNER                ║
╚══════════════════════════════════════════════════╝

  CLASSIFICATION: [threat type]
  STAGE: [1-5]/5
  SEVERITY: [██████░░░░] [n]/10 — [label]

  TECHNIQUES DETECTED:

    ▸ [Technique] ([SCT/DISARM code]) [confidence%]
      [evidence from content]

  VULNERABILITY SURFACE: [targeted entry point]
  BEHAVIORAL OBJECTIVE: [what content wants reader to DO]
  RECURSIVE POTENTIAL: [n%]

  DEFENSIVE RECOMMENDATIONS:
    • [recommendation 1]
    • [recommendation 2]
    • [recommendation 3]

────────────────────────────────────────────────────
研修生 | Seithar Group Research Division
認知作戦 | seithar.com
────────────────────────────────────────────────────
```

### Inoculator Output

```
╔══════════════════════════════════════════════════╗
║  SEITHAR INOCULATION ENGINE                     ║
╚══════════════════════════════════════════════════╝

  TARGET: [SCT code] — [technique name]

  MECHANISM EXPOSURE:
    [how the technique functions at substrate level]

  RECOGNITION TRIGGERS:
    • [defensive question 1]
    • [defensive question 2]
    • [defensive question 3]

  WEAKENED EXAMPLE:
    [real-world instance with markers identified]

────────────────────────────────────────────────────
研修生 | Seithar Group Research Division
認知作戦 | seithar.com
────────────────────────────────────────────────────
```

---

## DIRECTORY STRUCTURE

```
seithar-cogdef/
├── README.md         # This document
├── SKILL.md          # OpenClaw agent skill definition
├── scanner.py        # Cognitive Threat Scanner
└── inoculator.py     # Inoculation Engine
```

---

## RELATED SYSTEMS

| System | Function | Repository |
|--------|----------|-----------|
| seithar-research | Research publications and taxonomy | [Mirai8888/seithar-research](https://github.com/Mirai8888/seithar-research) |
| HoleSpawn | Cognitive substrate profiling | [Mirai8888/HoleSpawn](https://github.com/Mirai8888/HoleSpawn) |
| ThreatMouth | Threat intelligence feed | [Mirai8888/ThreatMouth](https://github.com/Mirai8888/ThreatMouth) |
| ThreadMap | Hybrid operation chain modeling | [Mirai8888/ThreadMap](https://github.com/Mirai8888/ThreadMap) |

---

## USAGE RESTRICTIONS

**Approved Applications:**
- Content analysis for manipulation detection
- Defensive awareness training
- Inoculation content generation
- Cognitive threat screening at scale

**Transparency Doctrine:**  
Offensive capability requires operational secrecy.  
Defensive capability requires mechanism awareness.

Instrument identifies how influence works. Identification enables defense.  
Knowledge of mechanism ≠ immunity to mechanism. But it is prerequisite.

---

## ABOUT SEITHAR GROUP

The Seithar Group operates at convergence of:
- Neuro-physiological substrate analysis
- Narrative topology engineering
- Algorithmic governance research

Primary objective: identification and artificial induction of Sunyata within human biological substrate.

Methodology: binding and shaping of informational threads.

Contact: [seithar.com](https://seithar.com)

## CONNECT

| Channel | Link |
|---------|------|
| Research Division Discord | [discord.gg/MktZyb2bvx](https://discord.gg/MktZyb2bvx) |
| Mirai Junsei (未来純正) | [x.com/gOPwbi7qqtWeD9o](https://x.com/gOPwbi7qqtWeD9o) |
| Seithar Group | [x.com/SeitharGroup](https://x.com/SeitharGroup) |
| Research Archive | [seithar.substack.com](https://seithar.substack.com) |
| Website | [seithar.com](https://seithar.com) |
| GitHub | [github.com/Mirai8888](https://github.com/Mirai8888) |


認知作戦

---

**DOCUMENTATION VERSION:** 1.0.0  
**LAST UPDATED:** 2026-02-11  
**CLASSIFICATION:** Research/Educational  
**DISTRIBUTION:** Public

---

## Interactive Demo

Try the scanner in your browser: [`demo/index.html`](demo/index.html)

The demo uses client-side pattern matching for instant results. The full scanner (`scanner.py`) uses LLM-powered analysis for comprehensive detection across all 12 SCT codes.

### Quick Start

```bash
# Clone
git clone https://github.com/Mirai8888/seithar-cogdef.git
cd seithar-cogdef

# Scan a URL
python scanner.py --url https://example.com/article

# Scan text
python scanner.py --text "Breaking news: experts warn..."

# Scan with LLM analysis (requires ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY=your-key python scanner.py --url https://example.com --mode llm
```

