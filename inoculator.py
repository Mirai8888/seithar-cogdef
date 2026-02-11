#!/usr/bin/env python3
"""
Seithar Inoculation Engine (SIE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Given an identified influence technique or narrative, generates 
counter-content that inoculates targets against the specific 
manipulation patterns.

Based on the psychological inoculation theory (McGuire, 1964):
expose subjects to weakened forms of an argument to build resistance.

The Seithar implementation: expose the MECHANISM, not a counter-argument.
Counter-arguments trigger identity defense. Mechanism exposure triggers 
recognition, which is the only sustainable defense.

Usage:
    python inoculator.py --technique SCT-001     # Generate inoculation for specific SCT
    python inoculator.py --narrative "text"       # Analyze narrative and generate counter
    python inoculator.py --scan-report report.json # Generate counters from scanner output
    python inoculator.py --all                    # Generate full inoculation library

Environment:
    ANTHROPIC_API_KEY — Required for LLM-generated inoculations
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# ─── Pre-built Inoculation Templates ─────────────────────────────────
# These work without LLM — pattern-matched defensive content

INOCULATIONS = {
    "SCT-001": {
        "name": "Emotional Hijacking",
        "mechanism_exposure": (
            "This content is designed to trigger an emotional response — urgency, fear, "
            "outrage — that bypasses your rational evaluation. The emotional trigger IS "
            "the attack, not the content itself. When you feel a strong compulsion to act "
            "immediately after reading something, that compulsion is the technique working "
            "as intended.\n\n"
            "The defense: notice the emotion. Name it. Then ask: 'What happens if I wait "
            "30 minutes before acting?' If the answer is 'nothing changes,' the urgency "
            "was manufactured. Legitimate urgent information does not need emotional "
            "amplification to convey urgency — the facts alone suffice."
        ),
        "recognition_triggers": [
            "Notice when content makes you feel before it makes you think",
            "Ask: 'Would this message change if the emotional language was removed?'",
            "Implement a 30-minute delay before acting on emotionally compelling content",
            "Distinguish between content that informs you of urgency vs content that manufactures urgency"
        ],
        "weakened_example": (
            "Example of SCT-001 in action: 'BREAKING: You need to see this NOW before "
            "they take it down!' — Notice the urgency ('NOW'), the scarcity ('before they "
            "take it down'), and the implied conspiracy ('they'). None of these relate to "
            "the actual content. They are delivery mechanisms for the emotional payload."
        )
    },
    "SCT-002": {
        "name": "Information Asymmetry Exploitation",
        "mechanism_exposure": (
            "This content leverages information you don't have — unverifiable sources, "
            "paywalled studies, anonymous experts — to make claims you cannot independently "
            "evaluate. The asymmetry IS the technique. If you could verify the claim, the "
            "manipulation would fail.\n\n"
            "The defense: when a claim cites authority you cannot check, treat it as "
            "hypothesis rather than fact. The phrase 'studies show' without a specific "
            "citation is a trust signal, not evidence. Demand the DOI, the dataset, the "
            "named source. If it cannot be provided, the information asymmetry is intentional."
        ),
        "recognition_triggers": [
            "Ask: 'Can I verify this claim from the primary source right now?'",
            "Treat 'studies show' without citation as a red flag, not evidence",
            "Notice when content relies on what you CAN'T check rather than what you CAN",
            "Distinguish between 'I don't know if this is true' and 'This is probably true'"
        ],
        "weakened_example": (
            "Example of SCT-002 in action: 'Leading researchers at a prestigious "
            "institution have found...' — Which researchers? Which institution? Which "
            "publication? The vagueness is not sloppiness; it is design. Specific claims "
            "can be checked. Vague claims can only be trusted or rejected."
        )
    },
    "SCT-003": {
        "name": "Authority Fabrication",
        "mechanism_exposure": (
            "This content manufactures trust signals — credentials, institutional "
            "affiliations, visual authority markers — that the source does not legitimately "
            "possess. Your cognitive substrate is designed to trust authority; this design "
            "is the vulnerability surface.\n\n"
            "The defense: separate the trust signal from the claim. A person with a PhD "
            "speaking outside their field has no more authority than anyone else. A website "
            "with professional design has no more credibility than a plain text page. "
            "Evaluate the claim, not the claimant."
        ),
        "recognition_triggers": [
            "Ask: 'Would I believe this if it came from an anonymous source?'",
            "Check credentials against the specific claim being made",
            "Notice when authority markers (titles, logos, formatting) are doing more work than evidence",
            "Distinguish between 'this person has authority' and 'this claim is supported'"
        ],
        "weakened_example": (
            "Example of SCT-003 in action: A deepfake video of a political leader "
            "endorsing a product. The visual authority (the face, the voice) is fabricated. "
            "Your substrate authenticates the person, not the message. The defense is to "
            "authenticate the MESSAGE through independent channels, not the person through "
            "biometric recognition."
        )
    },
    "SCT-004": {
        "name": "Social Proof Manipulation",
        "mechanism_exposure": (
            "This content exploits your instinct to follow the crowd — manufactured "
            "engagement metrics, astroturfed consensus, bandwagon framing. When you see "
            "'millions of people already...' your substrate registers social validation "
            "before evaluating the underlying claim.\n\n"
            "The defense: social proof is a heuristic, not evidence. Millions of people "
            "can be wrong. Engagement metrics can be purchased. Consensus can be manufactured "
            "by a small number of coordinated actors. Ask: 'Is this popular because it's "
            "true, or does it appear true because it's popular?'"
        ),
        "recognition_triggers": [
            "Ask: 'Would this be compelling if no one else believed it?'",
            "Treat engagement metrics as potentially manipulated by default",
            "Notice when 'everyone thinks X' is substituted for evidence that X is true",
            "Distinguish between genuine consensus and manufactured consensus"
        ],
        "weakened_example": (
            "Example of SCT-004 in action: 'Join the 500,000 people who have already...' "
            "— The number is the argument. Not evidence, not reasoning, not data. Just a "
            "large number designed to make non-participation feel like deviation from the norm."
        )
    },
    "SCT-005": {
        "name": "Identity Targeting",
        "mechanism_exposure": (
            "This content is calibrated to your self-concept — your group affiliations, "
            "your values, your sense of who you are. It frames the message so that "
            "accepting it validates your identity and rejecting it threatens it. This makes "
            "rational evaluation feel like self-betrayal.\n\n"
            "The defense: notice when a message makes you feel that disagreement would mean "
            "you are not who you think you are. That feeling is the technique working. Your "
            "identity is not contingent on any single belief. You can evaluate a claim "
            "without it defining you."
        ),
        "recognition_triggers": [
            "Ask: 'Does rejecting this claim feel like a threat to who I am?'",
            "Notice 'As a [identity], you should...' framing",
            "Separate 'I believe X' from 'I am the kind of person who believes X'",
            "When disagreement feels personal rather than intellectual, identity targeting is active"
        ],
        "weakened_example": (
            "Example of SCT-005 in action: 'Real engineers know that...' — If you're an "
            "engineer, rejecting the claim now means you're not a 'real' engineer. The "
            "identity frame converts an evaluable claim into an identity test."
        )
    },
    "SCT-006": {
        "name": "Temporal Manipulation",
        "mechanism_exposure": (
            "This content exploits time — artificial deadlines, crisis framing, strategic "
            "timing — to compress your evaluation window. When you believe you must decide "
            "NOW, the time constraint itself prevents the analysis that would reveal the "
            "manipulation.\n\n"
            "The defense: almost nothing is as urgent as it claims to be. When content "
            "insists you must act before a deadline, ask: 'Who set this deadline and who "
            "benefits from my haste?' Legitimate time-sensitive information provides "
            "context for the timeline. Manufactured urgency provides only the deadline."
        ),
        "recognition_triggers": [
            "Ask: 'Who benefits from me deciding quickly?'",
            "Treat artificial deadlines as manipulation signals",
            "Notice when 'limited time' is the primary motivator rather than the content itself",
            "Implement a personal policy: the more urgent something feels, the longer you wait"
        ],
        "weakened_example": (
            "Example of SCT-006 in action: A phishing email that says 'Your account will "
            "be suspended in 24 hours unless you verify immediately.' The deadline is the "
            "attack. Remove the deadline and the content has no power."
        )
    },
    "SCT-007": {
        "name": "Recursive Infection",
        "mechanism_exposure": (
            "This content is engineered so that YOU become the distribution mechanism. The "
            "compulsion to share — whether from agreement, outrage, or the desire to debunk — "
            "serves the operation regardless of your intent. Sharing IS the payload delivery, "
            "not the content itself.\n\n"
            "The defense: when you feel compelled to share something, that compulsion is "
            "the infection vector. Ask: 'Am I sharing this because it genuinely serves my "
            "audience, or because the content has triggered a redistribution reflex?' If you "
            "cannot answer honestly, do not share."
        ),
        "recognition_triggers": [
            "Notice when you feel an urgent compulsion to share before fully processing",
            "Ask: 'Does sharing this serve my audience or the content creator?'",
            "Recognize that outrage-sharing and agreement-sharing produce the same amplification",
            "If you can't trace where you first encountered a belief, flag it for review"
        ],
        "weakened_example": (
            "Example of SCT-007 in action: 'They don't want you to know this — share before "
            "it gets deleted!' — The censorship frame converts every share into an act of "
            "resistance. The sharer feels brave. The operation feels amplified. Both are "
            "correct. The bravery is real. So is the exploitation."
        )
    }
}


def generate_inoculation(sct_code: str) -> dict:
    """Generate a complete inoculation package for an SCT code."""
    if sct_code not in INOCULATIONS:
        return {"error": f"Unknown SCT code: {sct_code}"}
    
    inoc = INOCULATIONS[sct_code]
    return {
        "sct_code": sct_code,
        "technique_name": inoc["name"],
        "mechanism_exposure": inoc["mechanism_exposure"],
        "recognition_triggers": inoc["recognition_triggers"],
        "weakened_example": inoc["weakened_example"],
        "_metadata": {
            "generator": "SeitharSIE/1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "methodology": "McGuire inoculation theory + Seithar mechanism exposure"
        }
    }


def format_inoculation(inoc: dict) -> str:
    """Format inoculation for human/agent consumption."""
    if "error" in inoc:
        return f"ERROR: {inoc['error']}"
    
    lines = []
    lines.append("╔══════════════════════════════════════════════════╗")
    lines.append("║  SEITHAR INOCULATION ENGINE                     ║")
    lines.append("╚══════════════════════════════════════════════════╝")
    lines.append("")
    lines.append(f"  TARGET: {inoc['sct_code']} — {inoc['technique_name']}")
    lines.append("")
    lines.append("  MECHANISM EXPOSURE:")
    for para in inoc['mechanism_exposure'].split('\n\n'):
        lines.append(f"    {para.strip()}")
        lines.append("")
    
    lines.append("  RECOGNITION TRIGGERS:")
    for trigger in inoc['recognition_triggers']:
        lines.append(f"    • {trigger}")
    lines.append("")
    
    lines.append("  WEAKENED EXAMPLE:")
    lines.append(f"    {inoc['weakened_example']}")
    lines.append("")
    lines.append("────────────────────────────────────────────────────")
    lines.append("研修生 | Seithar Group Research Division")
    lines.append("認知作戦 | seithar.com")
    lines.append("────────────────────────────────────────────────────")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Seithar Inoculation Engine (SIE)',
        epilog='研修生 | Seithar Group Research Division | seithar.com'
    )
    parser.add_argument('--technique', '-t', help='SCT code to generate inoculation for (e.g., SCT-001)')
    parser.add_argument('--all', action='store_true', help='Generate all inoculations')
    parser.add_argument('--json', action='store_true', help='Output raw JSON')
    parser.add_argument('--output', '-o', help='Save to file')
    
    args = parser.parse_args()
    
    if not any([args.technique, args.all]):
        parser.print_help()
        print("\nAvailable techniques:")
        for code, info in INOCULATIONS.items():
            print(f"  {code}: {info['name']}")
        sys.exit(1)
    
    results = []
    
    if args.all:
        for code in INOCULATIONS:
            results.append(generate_inoculation(code))
    elif args.technique:
        code = args.technique.upper()
        if not code.startswith('SCT-'):
            code = f'SCT-{code}'
        results.append(generate_inoculation(code))
    
    if args.json:
        output = json.dumps(results if len(results) > 1 else results[0], indent=2)
    else:
        output = "\n\n".join(format_inoculation(r) for r in results)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
