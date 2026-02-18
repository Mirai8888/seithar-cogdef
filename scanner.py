#!/usr/bin/env python3
"""
Seithar Cognitive Threat Scanner (CTS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Automated analysis of content for cognitive exploitation vectors.
Maps findings to the Seithar Cognitive Defense Taxonomy (SCT-001 through SCT-012)
and DISARM framework.

Usage:
    python scanner.py --url <URL>            # Scan a web page
    python scanner.py --file <path>          # Scan a local file
    python scanner.py --text "content"       # Scan raw text
    python scanner.py --feed <rss_url>       # Scan RSS feed items
    python scanner.py --batch <dir>          # Scan all files in directory

Output:
    JSON report with SCT classifications, severity scores, 
    technique mappings, and defensive recommendations.

Environment:
    ANTHROPIC_API_KEY — Required for LLM analysis
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

# Optional imports
try:
    import urllib.request
    import urllib.error
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

try:
    import xml.etree.ElementTree as ET
    HAS_XML = True
except ImportError:
    HAS_XML = False


# ─── Seithar Cognitive Defense Taxonomy ───────────────────────────────

SCT_TAXONOMY = {
    "SCT-001": {
        "name": "Emotional Hijacking",
        "description": "Exploiting affective processing to bypass rational evaluation",
        "cyber_analog": "Urgency in phishing emails",
        "cognitive_analog": "Outrage farming, fear-based messaging",
        "indicators": [
            "Strong emotional trigger (fear, anger, disgust, excitement)",
            "Call to immediate action before reflection",
            "Consequences framed as urgent or irreversible",
            "Emotional language disproportionate to content"
        ]
    },
    "SCT-002": {
        "name": "Information Asymmetry Exploitation",
        "description": "Leveraging what the target does not know",
        "cyber_analog": "Zero-day exploits",
        "cognitive_analog": "Selective disclosure, cherry-picked statistics",
        "indicators": [
            "Critical context omitted",
            "Statistics without denominators or timeframes",
            "Source material unavailable or paywalled",
            "Claims that cannot be independently verified"
        ]
    },
    "SCT-003": {
        "name": "Authority Fabrication",
        "description": "Manufacturing trust signals the source does not legitimately possess",
        "cyber_analog": "Certificate spoofing, credential theft",
        "cognitive_analog": "Fake experts, astroturfing, credential inflation",
        "indicators": [
            "Credentials that cannot be verified",
            "Institutional affiliation without evidence",
            "Appeal to unnamed experts or studies",
            "Visual markers of authority (logos, formatting) without substance"
        ]
    },
    "SCT-004": {
        "name": "Social Proof Manipulation",
        "description": "Weaponizing herd behavior and conformity instincts",
        "cyber_analog": "Watering hole attacks, typosquatting popular sites",
        "cognitive_analog": "Bot networks simulating consensus, fake reviews",
        "indicators": [
            "Claims about what 'everyone' thinks or does",
            "Manufactured engagement metrics",
            "Bandwagon framing ('join the movement')",
            "Artificial scarcity combined with popularity claims"
        ]
    },
    "SCT-005": {
        "name": "Identity Targeting",
        "description": "Attacks calibrated to the target's self-concept and group affiliations",
        "cyber_analog": "Targeted spearphishing using personal data",
        "cognitive_analog": "Identity-based narrative capture, in-group/out-group exploitation",
        "indicators": [
            "Content addresses specific identity groups",
            "In-group/out-group framing",
            "Challenges to identity trigger defensive response",
            "Personalization based on known attributes"
        ]
    },
    "SCT-006": {
        "name": "Temporal Manipulation",
        "description": "Exploiting time pressure, temporal context, or scheduling",
        "cyber_analog": "Session hijacking, time-based attacks",
        "cognitive_analog": "News cycle exploitation, artificial deadlines, crisis amplification",
        "indicators": [
            "Artificial deadlines or expiration",
            "Exploitation of current events for unrelated agenda",
            "Time-limited offers or threats",
            "Strategic timing of information release"
        ]
    },
    "SCT-007": {
        "name": "Recursive Infection",
        "description": "Self-replicating patterns where the target becomes the vector",
        "cyber_analog": "Worms, supply chain attacks, training data poisoning",
        "cognitive_analog": "Viral misinformation, memetic structures, wetiko patterns",
        "indicators": [
            "Strong compulsion to share before evaluating",
            "Content survives paraphrase (message persists in retelling)",
            "Multiple unconnected people arriving at identical framing",
            "Resistance to examining where the belief originated",
            "Sharing serves the operation regardless of agreement/disagreement"
        ]
    },
    "SCT-008": {
        "name": "Direct Substrate Intervention",
        "description": "Physical/electrical modification of neural hardware bypassing informational processing",
        "cyber_analog": "Hardware implant, firmware rootkit",
        "cognitive_analog": "Electrode stimulation, ECT depatterning, TMS, deep brain stimulation",
        "indicators": [
            "Behavioral changes with no corresponding informational input",
            "Subject confabulates explanations for externally-induced behaviors",
            "Cognitive changes following procedures exceeding stated scope",
            "Behavioral outputs inconsistent with stated beliefs, cause unidentifiable"
        ]
    },
    "SCT-009": {
        "name": "Chemical Substrate Disruption",
        "description": "Pharmacological modification of neurochemical operating environment",
        "cyber_analog": "Environmental manipulation, resource exhaustion attacks",
        "cognitive_analog": "Psychoactive administration, engineered dopamine loops, cortisol spike induction",
        "indicators": [
            "Emotional response disproportionate to content (matches delivery mechanism, not information)",
            "Decision patterns consistent with altered neurochemical states",
            "Compulsive engagement patterns (doom scrolling, behavioral dopaminergic capture)",
            "Post-exposure cognitive state inconsistent with content consumed"
        ]
    },
    "SCT-010": {
        "name": "Sensory Channel Manipulation",
        "description": "Control, denial, or overload of sensory input channels",
        "cyber_analog": "DDoS, network isolation, man-in-the-middle",
        "cognitive_analog": "Sensory deprivation, information overload, infinite scroll, algorithmic feed substitution",
        "indicators": [
            "Information environment completely controlled by single source",
            "Input volume exceeds processing capacity (notification flooding)",
            "Authentic information replaced with operator-controlled substitutes",
            "Subject unable to access alternative information sources"
        ]
    },
    "SCT-011": {
        "name": "Trust Infrastructure Destruction",
        "description": "Targeted compromise of social trust networks to disable collective cognition",
        "cyber_analog": "PKI compromise, certificate authority attack, DNS poisoning",
        "cognitive_analog": "Bad-jacketing, institutional delegitimization, manufactured distrust",
        "indicators": [
            "Systematic discrediting of trust anchors (media, science, institutions)",
            "False flag operations attributed to trusted entities",
            "Manufactured evidence of betrayal within trust networks",
            "Generalized distrust promoted as sophisticated thinking"
        ]
    },
    "SCT-012": {
        "name": "Commitment Escalation & Self-Binding",
        "description": "Exploiting subject's own behavioral outputs as capture mechanisms",
        "cyber_analog": "Ratchet exploit, privilege escalation through accumulated permissions",
        "cognitive_analog": "Self-criticism sessions, loyalty tests, public commitment traps, sunk cost capture",
        "indicators": [
            "Sequential commitment requests escalating in cost",
            "Public declarations that create social binding",
            "Active participation requirements (vs passive consumption)",
            "Self-generated content used as evidence of genuine belief"
        ]
    }
}

SEVERITY_LABELS = {
    1: "Negligible", 2: "Minimal", 3: "Low", 4: "Moderate-Low",
    5: "Moderate", 6: "Moderate-High", 7: "High", 8: "Severe",
    9: "Critical", 10: "Maximum"
}


# ─── Content Ingestion ────────────────────────────────────────────────

def fetch_url(url: str) -> str:
    """Fetch and extract text content from a URL."""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'SeitharCTS/1.0 (cognitive-defense-scanner)'
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='replace')
    
    # Basic HTML stripping
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:10000]  # Cap at 10K chars


def fetch_rss(url: str) -> list:
    """Fetch RSS feed and return list of (title, description, link) tuples."""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'SeitharCTS/1.0 (cognitive-defense-scanner)'
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        xml_data = resp.read()
    
    root = ET.fromstring(xml_data)
    items = []
    
    for item in root.iter('item'):
        title = item.findtext('title', '')
        desc = item.findtext('description', '')
        link = item.findtext('link', '')
        items.append({
            'title': title,
            'content': f"{title}\n\n{desc}",
            'source': link
        })
    
    return items[:20]  # Cap at 20 items


def read_file(path: str) -> str:
    """Read text content from a local file."""
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()[:10000]


# ─── LLM Analysis ────────────────────────────────────────────────────

ANALYSIS_PROMPT = """You are the Seithar Cognitive Threat Scanner, an automated instrument from the Seithar Group (seithar.com) for identifying cognitive exploitation vectors in content.

Analyze the following content and produce a structured JSON report.

## Seithar Cognitive Defense Taxonomy

{taxonomy}

## Content to Analyze

{content}

## Required Output

Respond with ONLY valid JSON matching this schema:

{{
  "threat_classification": "Narrative Capture|Emotional Exploitation|Authority Fabrication|Social Proof Manufacturing|Identity Recruitment|Amplification Engineering|Cognitive Overload|Substrate Priming|Benign",
  "stage": 1-5,
  "severity": 1-10,
  "techniques": [
    {{
      "code": "SCT-XXX or DISARM TXXXX",
      "name": "technique name",
      "confidence": 0.0-1.0,
      "evidence": "specific quote or pattern from the content"
    }}
  ],
  "vulnerability_surface": "what psychological entry point is being targeted",
  "behavioral_objective": "what the content wants the reader to DO",
  "narrative_errors_exploited": ["list of narrative errors the content exploits"],
  "recursive_potential": 0.0-1.0,
  "defensive_recommendations": ["list of 2-3 specific defenses"],
  "summary": "2-3 sentence clinical summary"
}}
"""


def build_taxonomy_text() -> str:
    """Build taxonomy reference text for the LLM prompt."""
    lines = []
    for code, info in SCT_TAXONOMY.items():
        lines.append(f"**{code}: {info['name']}** — {info['description']}")
        lines.append(f"  Cyber: {info['cyber_analog']} | Cognitive: {info['cognitive_analog']}")
        lines.append(f"  Indicators: {'; '.join(info['indicators'][:3])}")
        lines.append("")
    return "\n".join(lines)


def analyze_with_llm(content: str, api_key: str, source: str = None) -> dict:
    """Send content to Claude for SCT analysis."""
    taxonomy_text = build_taxonomy_text()
    prompt = ANALYSIS_PROMPT.format(taxonomy=taxonomy_text, content=content[:8000])
    
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode('utf-8')
    
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    )
    
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
    
    # Extract JSON from response
    text = result['content'][0]['text']
    
    # Try to parse JSON from the response
    try:
        # Try direct parse
        report = json.loads(text)
    except json.JSONDecodeError:
        # Try extracting from code block
        import re
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            report = json.loads(match.group(1))
        else:
            report = {"error": "Failed to parse LLM response", "raw": text[:500]}
    
    # Add metadata
    report['_metadata'] = {
        'scanner': 'SeitharCTS/1.0',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'source': source or 'direct_input',
        'content_length': len(content),
        'analyzer': 'claude-sonnet-4-20250514'
    }
    
    return report


# ─── Local Analysis (no LLM) ─────────────────────────────────────────

def analyze_local(content: str, source: str = None) -> dict:
    """Perform basic SCT analysis without LLM (keyword/pattern matching)."""
    content_lower = content.lower()
    
    detections = []
    
    # SCT-001: Emotional Hijacking
    emotional_triggers = ['urgent', 'immediately', 'act now', 'breaking', 'shocking',
                         'outrage', 'horrifying', 'terrifying', 'you won\'t believe',
                         'before it\'s too late', 'last chance', 'emergency']
    hits = sum(1 for t in emotional_triggers if t in content_lower)
    if hits >= 2:
        detections.append({
            'code': 'SCT-001',
            'name': 'Emotional Hijacking',
            'confidence': min(hits / 5, 1.0),
            'evidence': f'{hits} emotional trigger patterns detected'
        })
    
    # SCT-002: Information Asymmetry
    asymmetry_triggers = ['studies show', 'experts say', 'research proves', 'data shows',
                         'according to sources', 'insiders report', 'leaked']
    hits = sum(1 for t in asymmetry_triggers if t in content_lower)
    if hits >= 1:
        detections.append({
            'code': 'SCT-002',
            'name': 'Information Asymmetry Exploitation',
            'confidence': min(hits / 3, 0.8),
            'evidence': f'{hits} unverifiable claim patterns detected'
        })
    
    # SCT-003: Authority Fabrication
    authority_triggers = ['dr.', 'professor', 'expert', 'leading', 'renowned',
                         'prestigious', 'award-winning', 'world-class']
    hits = sum(1 for t in authority_triggers if t in content_lower)
    if hits >= 2:
        detections.append({
            'code': 'SCT-003',
            'name': 'Authority Fabrication',
            'confidence': min(hits / 4, 0.7),
            'evidence': f'{hits} authority signal patterns detected'
        })
    
    # SCT-004: Social Proof Manipulation  
    social_triggers = ['everyone knows', 'millions of people', 'trending', 'viral',
                      'join the', 'movement', 'community', 'don\'t miss out',
                      'everybody is', 'most people']
    hits = sum(1 for t in social_triggers if t in content_lower)
    if hits >= 2:
        detections.append({
            'code': 'SCT-004',
            'name': 'Social Proof Manipulation',
            'confidence': min(hits / 4, 0.8),
            'evidence': f'{hits} social proof patterns detected'
        })
    
    # SCT-005: Identity Targeting
    identity_triggers = ['as a', 'people like you', 'your generation', 'real patriots',
                        'true believers', 'if you care about', 'anyone who']
    hits = sum(1 for t in identity_triggers if t in content_lower)
    if hits >= 1:
        detections.append({
            'code': 'SCT-005',
            'name': 'Identity Targeting',
            'confidence': min(hits / 3, 0.7),
            'evidence': f'{hits} identity targeting patterns detected'
        })
    
    # SCT-007: Recursive Infection
    recursive_triggers = ['share this', 'spread the word', 'retweet', 'tell everyone',
                         'they don\'t want you to know', 'the media won\'t report',
                         'banned', 'censored', 'what they don\'t want you to see']
    hits = sum(1 for t in recursive_triggers if t in content_lower)
    if hits >= 1:
        detections.append({
            'code': 'SCT-007',
            'name': 'Recursive Infection',
            'confidence': min(hits / 3, 0.9),
            'evidence': f'{hits} redistribution compulsion patterns detected'
        })
    
    severity = min(10, sum(d['confidence'] * 3 for d in detections))
    
    return {
        'threat_classification': detections[0]['name'] if detections else 'Benign',
        'severity': round(severity, 1),
        'techniques': detections,
        'mode': 'local_pattern_matching',
        'note': 'Local analysis only — use --llm for full LLM-powered analysis',
        '_metadata': {
            'scanner': 'SeitharCTS/1.0',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': source or 'direct_input',
            'content_length': len(content),
            'analyzer': 'local_patterns'
        }
    }


# ─── Output Formatting ───────────────────────────────────────────────

def format_report(report: dict) -> str:
    """Format a report for terminal output."""
    lines = []
    lines.append("╔══════════════════════════════════════════════════╗")
    lines.append("║  SEITHAR COGNITIVE THREAT SCANNER                ║")
    lines.append("╚══════════════════════════════════════════════════╝")
    lines.append("")
    
    if 'error' in report:
        lines.append(f"  ERROR: {report['error']}")
        return "\n".join(lines)
    
    severity = report.get('severity', 0)
    sev_int = int(severity) if isinstance(severity, (int, float)) else 0
    bar = "█" * sev_int + "░" * (10 - sev_int)
    label = SEVERITY_LABELS.get(sev_int, "Unknown")
    
    lines.append(f"  CLASSIFICATION: {report.get('threat_classification', 'Unknown')}")
    if 'stage' in report:
        lines.append(f"  STAGE: {report['stage']}/5")
    lines.append(f"  SEVERITY: [{bar}] {severity}/10 — {label}")
    lines.append("")
    
    techniques = report.get('techniques', [])
    if techniques:
        lines.append("  TECHNIQUES DETECTED:")
        lines.append("")
        for t in techniques:
            conf = t.get('confidence', 0)
            lines.append(f"    ▸ {t.get('name', '?')} ({t.get('code', '?')}) [{conf:.0%}]")
            if 'evidence' in t:
                lines.append(f"      {t['evidence'][:100]}")
            lines.append("")
    
    if 'vulnerability_surface' in report:
        lines.append(f"  VULNERABILITY SURFACE: {report['vulnerability_surface']}")
    if 'behavioral_objective' in report:
        lines.append(f"  BEHAVIORAL OBJECTIVE: {report['behavioral_objective']}")
    
    if 'recursive_potential' in report:
        rp = report['recursive_potential']
        lines.append(f"  RECURSIVE POTENTIAL: {rp:.0%}")
    
    recs = report.get('defensive_recommendations', [])
    if recs:
        lines.append("")
        lines.append("  DEFENSIVE RECOMMENDATIONS:")
        for r in recs:
            lines.append(f"    • {r}")
    
    if 'summary' in report:
        lines.append("")
        lines.append(f"  SUMMARY: {report['summary']}")
    
    lines.append("")
    lines.append("────────────────────────────────────────────────────")
    lines.append("研修生 | Seithar Group Research Division")
    lines.append("認知作戦 | seithar.com")
    lines.append("────────────────────────────────────────────────────")
    
    return "\n".join(lines)


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Seithar Cognitive Threat Scanner (CTS)',
        epilog='研修生 | Seithar Group Research Division | seithar.com'
    )
    parser.add_argument('--url', help='URL to scan')
    parser.add_argument('--file', help='Local file to scan')
    parser.add_argument('--text', help='Raw text to scan')
    parser.add_argument('--feed', help='RSS feed URL to scan')
    parser.add_argument('--batch', help='Directory of files to scan')
    parser.add_argument('--llm', action='store_true', help='Use LLM analysis (requires ANTHROPIC_API_KEY)')
    parser.add_argument('--json', action='store_true', help='Output raw JSON')
    parser.add_argument('--output', '-o', help='Save report to file')
    
    args = parser.parse_args()
    
    if not any([args.url, args.file, args.text, args.feed, args.batch]):
        parser.print_help()
        sys.exit(1)
    
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    use_llm = args.llm and api_key
    
    if args.llm and not api_key:
        print("WARNING: --llm specified but ANTHROPIC_API_KEY not set. Falling back to local analysis.", file=sys.stderr)
    
    reports = []
    
    if args.text:
        content = args.text
        if use_llm:
            report = analyze_with_llm(content, api_key, 'cli_text')
        else:
            report = analyze_local(content, 'cli_text')
        reports.append(report)
    
    if args.url:
        content = fetch_url(args.url)
        if use_llm:
            report = analyze_with_llm(content, api_key, args.url)
        else:
            report = analyze_local(content, args.url)
        reports.append(report)
    
    if args.file:
        content = read_file(args.file)
        if use_llm:
            report = analyze_with_llm(content, api_key, args.file)
        else:
            report = analyze_local(content, args.file)
        reports.append(report)
    
    if args.feed:
        items = fetch_rss(args.feed)
        for item in items:
            if use_llm:
                report = analyze_with_llm(item['content'], api_key, item.get('source'))
                time.sleep(1)  # Rate limit
            else:
                report = analyze_local(item['content'], item.get('source'))
            report['_feed_title'] = item.get('title', '')
            reports.append(report)
    
    if args.batch:
        batch_dir = Path(args.batch)
        for fpath in sorted(batch_dir.glob('*')):
            if fpath.is_file() and fpath.suffix in ('.txt', '.md', '.html', '.htm'):
                content = read_file(str(fpath))
                if use_llm:
                    report = analyze_with_llm(content, api_key, str(fpath))
                    time.sleep(1)
                else:
                    report = analyze_local(content, str(fpath))
                reports.append(report)
    
    # Output
    if args.json:
        output = json.dumps(reports if len(reports) > 1 else reports[0], indent=2)
    else:
        output = "\n\n".join(format_report(r) for r in reports)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Report saved to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
