# Contributing to Seithar Cognitive Defense

The Seithar Group welcomes contributions to our cognitive defense instrumentation.

## Architecture

```
seithar-cogdef/
├── scanner.py          # Cognitive Threat Scanner — pattern + LLM analysis
├── inoculator.py       # Inoculation Engine — counter-narrative generation
├── SKILL.md            # OpenClaw agent skill definition
├── demo/               # Interactive web demo (client-side)
│   └── index.html      # Browser-based pattern matching demo
├── pyproject.toml      # Python packaging (pip-installable)
└── README.md           # Documentation
```

## SCT Taxonomy

All contributions should align with the Seithar Cognitive Defense Taxonomy:

| Code | Name | Description |
|------|------|-------------|
| SCT-001 | Narrative Capture | External narrative replaces analytical framework |
| SCT-002 | Emotional Substrate Priming | Emotional manipulation increases receptivity |
| SCT-003 | Frequency Lock | Repeated exposure synchronizes cognitive baseline |
| SCT-004 | Social Proof Fabrication | Manufactured consensus |
| SCT-005 | Identity Anchor | Self-concept bound to external entity |
| SCT-006 | Authority Hijack | Credentials bypass critical evaluation |
| SCT-007 | Recursive Infection | Captured substrate propagates voluntarily |
| SCT-008 | Temporal Manipulation | Memory/expectation exploited |
| SCT-009 | Semantic Manipulation | Language constrains thought |
| SCT-010 | Algorithmic Amplification | Platform systems weaponized |
| SCT-011 | Platform Complicity | Economic incentives against defense |
| SCT-012 | LLM-Mediated Operations | AI mediates influence at scale |

## Ways to Contribute

### Improve Pattern Detection
The scanner's local mode uses regex patterns. More patterns = better detection without API costs.
- Add patterns to `SCT_PATTERNS` in `scanner.py`
- Test against real-world examples
- Avoid false positives on legitimate content

### Add New Content Sources
The scanner supports URLs, files, text, RSS, and batch modes. Additional input sources welcome:
- Social media API integrations
- Email inbox scanning
- Browser extension
- Chat platform integration

### Improve the Demo
`demo/index.html` is a standalone client-side demo. Enhancements welcome:
- Additional example texts
- Better pattern matching
- Visualization of detection results
- Multi-language support

### Research
- Document new cognitive exploitation techniques
- Map techniques to existing SCT codes or propose new ones
- Write case studies analyzing real-world influence operations
- Cross-reference with DISARM, MITRE ATT&CK, or other frameworks

## Code Style
- Python 3.8+ compatible
- No external dependencies for core functionality
- Optional dependencies clearly marked
- Clear docstrings on all public functions
- SCT codes referenced where applicable

## Submitting
1. Fork the repository
2. Create a feature branch
3. Write clear commit messages
4. Open a pull request with description of changes

## Contact
- GitHub Issues: https://github.com/Mirai8888/seithar-cogdef/issues
- Discord: https://discord.gg/MktZyb2bvx
- Website: https://seithar.com

────────────────────────────────────────────────────
Seithar Group — Intelligence and Research Division
認知作戦 | seithar.com
────────────────────────────────────────────────────
