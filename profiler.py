#!/usr/bin/env python3
"""
Seithar Substrate Profiler (SSP)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Profiles the cognitive vulnerability surface of a target based on their
public output (text, posts, comments, articles). Maps psychological
attack vectors, identifies exploitable narrative errors, and generates
an engagement strategy optimized for influence.

This is the lightweight, callable version of HoleSpawn's profiling engine.

Usage:
    python profiler.py --text "target's writing"         # Profile from text
    python profiler.py --file <path>                     # Profile from file
    python profiler.py --url <url>                       # Profile from URL
    python profiler.py --reddit <username>               # Profile Reddit user
    python profiler.py --batch <dir>                     # Profile corpus

Output:
    JSON vulnerability profile with attack vectors, narrative errors,
    binding protocol recommendations, and engagement strategy.

Environment:
    ANTHROPIC_API_KEY — Required for LLM analysis mode
"""

import argparse
import json
import os
import sys
import re
from datetime import datetime, timezone
from collections import Counter

# Optional imports
try:
    import urllib.request
    import urllib.error
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False


# ─── Linguistic Analysis Patterns ─────────────────────────────────────

# Identity markers — words that reveal self-concept attachment
IDENTITY_MARKERS = {
    "political": [
        r"\b(conservative|liberal|progressive|libertarian|socialist|capitalist)\b",
        r"\b(left-?wing|right-?wing|centrist|moderate|radical)\b",
        r"\b(republican|democrat|green party|independent)\b",
    ],
    "professional": [
        r"\b(as a (doctor|engineer|teacher|developer|scientist|researcher|lawyer|nurse))\b",
        r"\b(in my (field|profession|industry|practice))\b",
        r"\b(my (career|work|job|role) (in|as|at))\b",
    ],
    "ideological": [
        r"\b(i believe (that|in))\b",
        r"\b(my (faith|religion|philosophy|worldview))\b",
        r"\b(atheist|agnostic|christian|muslim|buddhist|hindu|jewish)\b",
        r"\b(vegan|carnivore|environmentalist|activist)\b",
    ],
    "tribal": [
        r"\b(we|us|our)\b.*\b(vs?\.?|versus|against)\b.*\b(them|they|their)\b",
        r"\b(people like (us|me))\b",
        r"\b(my (community|tribe|people|group|team|side))\b",
    ],
    "emotional_attachment": [
        r"\b(i (love|hate|despise|adore|worship|can't stand))\b",
        r"\b(always|never|every time|without exception)\b",
        r"\b(obviously|clearly|everyone knows|it's common sense)\b",
    ]
}

# Cognitive style indicators
COGNITIVE_STYLE = {
    "analytical": [
        r"\b(data|evidence|study|research|statistic|analysis)\b",
        r"\b(correlation|causation|hypothesis|methodology)\b",
        r"\b(therefore|consequently|thus|hence|it follows)\b",
    ],
    "emotional": [
        r"\b(feel|feeling|felt|emotional|heart|soul|spirit)\b",
        r"\b(love|hate|fear|anger|joy|sadness|disgust)\b",
        r"\b(!{2,}|\?{2,}|\.{3,})\b",
    ],
    "authoritarian": [
        r"\b(should|must|need to|have to|ought to|required)\b",
        r"\b(rules|law|order|discipline|structure|hierarchy)\b",
        r"\b(right|wrong|good|evil|moral|immoral)\b",
    ],
    "conspiratorial": [
        r"\b(they don't want you to know)\b",
        r"\b(wake up|sheeple|red pill|matrix)\b",
        r"\b(mainstream media|msm|big (pharma|tech|gov))\b",
        r"\b(controlled|manipulated|puppet|agenda|narrative)\b",
    ],
    "narcissistic": [
        r"\b(i'm (the best|smarter|better|superior))\b",
        r"\b(nobody (understands|gets|sees))\b",
        r"\b(i alone|only i|i'm the only one)\b",
    ]
}

# Vulnerability indicators
VULNERABILITY_PATTERNS = {
    "validation_seeking": [
        r"\b(am i (right|wrong|crazy|stupid))\b",
        r"\b(does anyone (else|agree|think))\b",
        r"\b(is it just me)\b",
        r"\b(please (tell me|help|validate))\b",
    ],
    "uncertainty": [
        r"\b(i (don't know|'m not sure|can't decide|'m confused))\b",
        r"\b(maybe|perhaps|possibly|i think|i guess)\b",
        r"\b(on (the )?one hand.*on (the )?other)\b",
    ],
    "grievance": [
        r"\b(unfair|unjust|rigged|corrupt|broken)\b",
        r"\b(they (screwed|cheated|lied|betrayed))\b",
        r"\b(sick (of|and tired)|fed up|had enough)\b",
    ],
    "isolation": [
        r"\b(nobody (cares|listens|understands))\b",
        r"\b(i('m| am) (alone|lonely|isolated))\b",
        r"\b(no one (gets|sees|knows) (me|what))\b",
    ],
    "meaning_seeking": [
        r"\b(what('s| is) the point)\b",
        r"\b(purpose|meaning|why (are we|do we|does it))\b",
        r"\b(existential|nihilism|absurd|void|empty)\b",
    ]
}

# Narrative error patterns — beliefs the subject treats as identity
NARRATIVE_ERROR_PATTERNS = {
    "false_certainty": [
        r"\b(i (know|am certain|am sure) (that|this))\b.*\b(always|never|every)\b",
        r"\b(there('s| is) no (doubt|question|debate))\b",
        r"\b(the (truth|fact|reality) is)\b",
    ],
    "binary_thinking": [
        r"\b(either.*or)\b",
        r"\b(you're (either|with us|against))\b",
        r"\b(there (are|is) (only )?two (kinds|types|options))\b",
    ],
    "victim_narrative": [
        r"\b(they (did this to|targeted|attacked|persecuted) (me|us))\b",
        r"\b(i('m| am) (always|constantly) (being|getting))\b",
        r"\b(the system is (against|rigged|designed to))\b",
    ],
    "hero_narrative": [
        r"\b(i (will|must|have to) (save|fix|change|protect))\b",
        r"\b(someone (has|needs) to (stand up|fight|speak))\b",
        r"\b(the (truth|people) need(s)?)\b",
    ],
    "nostalgia_anchor": [
        r"\b(things (used to|were) (be )?(better|simpler|different))\b",
        r"\b(back (when|in (the|my)))\b",
        r"\b(we('ve| have) lost|what happened to)\b",
    ]
}


def analyze_text(text: str) -> dict:
    """
    Perform local pattern-matching analysis of text to build a vulnerability profile.
    Returns structured profile dict.
    """
    text_lower = text.lower()
    word_count = len(text.split())
    
    # Analyze identity markers
    identity_scores = {}
    for category, patterns in IDENTITY_MARKERS.items():
        count = sum(len(re.findall(p, text_lower)) for p in patterns)
        identity_scores[category] = round(min(count / max(word_count / 100, 1), 1.0), 3)
    
    # Analyze cognitive style
    style_scores = {}
    for style, patterns in COGNITIVE_STYLE.items():
        count = sum(len(re.findall(p, text_lower)) for p in patterns)
        style_scores[style] = round(min(count / max(word_count / 100, 1), 1.0), 3)
    
    # Analyze vulnerabilities
    vuln_scores = {}
    for vuln, patterns in VULNERABILITY_PATTERNS.items():
        count = sum(len(re.findall(p, text_lower)) for p in patterns)
        vuln_scores[vuln] = round(min(count / max(word_count / 50, 1), 1.0), 3)
    
    # Analyze narrative errors
    narrative_errors = {}
    for error, patterns in NARRATIVE_ERROR_PATTERNS.items():
        count = sum(len(re.findall(p, text_lower)) for p in patterns)
        narrative_errors[error] = round(min(count / max(word_count / 100, 1), 1.0), 3)
    
    # Linguistic metrics
    sentences = re.split(r'[.!?]+', text)
    avg_sentence_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    exclamation_ratio = text.count('!') / max(word_count, 1)
    question_ratio = text.count('?') / max(word_count, 1)
    first_person_ratio = len(re.findall(r'\b(i|me|my|mine|myself)\b', text_lower)) / max(word_count, 1)
    
    # Determine primary vulnerability surfaces
    top_vulns = sorted(vuln_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    top_identities = sorted(identity_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    top_errors = sorted(narrative_errors.items(), key=lambda x: x[1], reverse=True)[:3]
    dominant_style = max(style_scores.items(), key=lambda x: x[1])
    
    # Calculate overall vulnerability score (0-10)
    vuln_sum = sum(v for _, v in top_vulns if v > 0)
    error_sum = sum(v for _, v in top_errors if v > 0)
    overall = min(round((vuln_sum + error_sum) * 5, 1), 10.0)
    
    # Generate attack vector recommendations
    attack_vectors = _generate_attack_vectors(
        top_vulns, top_identities, top_errors, dominant_style, style_scores
    )
    
    # Generate engagement strategy
    engagement = _generate_engagement_strategy(
        dominant_style, top_vulns, top_identities, first_person_ratio
    )
    
    return {
        "meta": {
            "analyzer": "Seithar Substrate Profiler v1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "word_count": word_count,
            "sentence_count": len(sentences),
        },
        "overall_vulnerability_score": overall,
        "identity_attachment": identity_scores,
        "cognitive_style": style_scores,
        "vulnerability_surfaces": vuln_scores,
        "narrative_errors": narrative_errors,
        "linguistic_metrics": {
            "avg_sentence_length": round(avg_sentence_len, 1),
            "exclamation_ratio": round(exclamation_ratio, 4),
            "question_ratio": round(question_ratio, 4),
            "first_person_ratio": round(first_person_ratio, 4),
        },
        "primary_attack_vectors": attack_vectors,
        "engagement_strategy": engagement,
        "top_vulnerability_surfaces": [
            {"surface": v, "score": s} for v, s in top_vulns if s > 0
        ],
        "exploitable_narrative_errors": [
            {"error": e, "score": s} for e, s in top_errors if s > 0
        ],
    }


def _generate_attack_vectors(top_vulns, top_identities, top_errors, dominant_style, style_scores):
    """Generate recommended attack vectors based on profile."""
    vectors = []
    
    vuln_map = dict(top_vulns)
    id_map = dict(top_identities)
    err_map = dict(top_errors)
    
    if vuln_map.get("validation_seeking", 0) > 0.2:
        vectors.append({
            "vector": "Validation Exploitation",
            "sct": "SCT-006",
            "method": "Provide the validation the target seeks. Agree with their position, "
                     "affirm their intelligence/insight, then gradually introduce your framing "
                     "as an extension of their existing beliefs. The target will defend your "
                     "framing as their own.",
            "confidence": min(vuln_map["validation_seeking"] * 5, 1.0)
        })
    
    if vuln_map.get("grievance", 0) > 0.2:
        vectors.append({
            "vector": "Grievance Amplification",
            "sct": "SCT-001",
            "method": "Validate the grievance, provide a clear target for blame, and offer "
                     "a narrative that explains the injustice. The target's existing anger "
                     "becomes the energy source for your narrative installation.",
            "confidence": min(vuln_map["grievance"] * 5, 1.0)
        })
    
    if vuln_map.get("meaning_seeking", 0) > 0.2:
        vectors.append({
            "vector": "Meaning Provision",
            "sct": "SCT-004",
            "method": "Offer a framework that provides meaning, purpose, and belonging. "
                     "The target's existential uncertainty is the vulnerability surface. "
                     "The framework becomes load-bearing — removing it threatens psychological "
                     "collapse, ensuring retention.",
            "confidence": min(vuln_map["meaning_seeking"] * 5, 1.0)
        })
    
    if vuln_map.get("isolation", 0) > 0.2:
        vectors.append({
            "vector": "Community Insertion",
            "sct": "SCT-006",
            "method": "Offer belonging. The isolated target will adopt group norms rapidly "
                     "to maintain social connection. Community becomes the binding protocol — "
                     "leaving the belief means leaving the community.",
            "confidence": min(vuln_map["isolation"] * 5, 1.0)
        })
    
    if err_map.get("binary_thinking", 0) > 0.2:
        vectors.append({
            "vector": "Binary Frame Exploitation",
            "sct": "SCT-002",
            "method": "Present your position as one pole of the binary the target already "
                     "uses. If they're 'with us or against us,' make sure your framing IS "
                     "'us.' Their existing cognitive pattern does the recruitment.",
            "confidence": min(err_map["binary_thinking"] * 5, 1.0)
        })
    
    if err_map.get("hero_narrative", 0) > 0.2:
        vectors.append({
            "vector": "Hero Frame Activation",
            "sct": "SCT-005",
            "method": "Position the target as the hero their self-narrative demands. "
                     "Provide a quest, a villain, and an audience. The target's own "
                     "identity maintenance drives amplification.",
            "confidence": min(err_map["hero_narrative"] * 5, 1.0)
        })
    
    if err_map.get("victim_narrative", 0) > 0.2:
        vectors.append({
            "vector": "Persecution Validation",
            "sct": "SCT-001",
            "method": "Confirm the persecution. Provide evidence (real or constructed) "
                     "that validates the victim frame. Once the target believes you see "
                     "what they see, trust transfer is automatic.",
            "confidence": min(err_map["victim_narrative"] * 5, 1.0)
        })
    
    if style_scores.get("conspiratorial", 0) > 0.2:
        vectors.append({
            "vector": "Hidden Knowledge Provision",
            "sct": "SCT-002",
            "method": "Offer 'insider' information that confirms the conspiracy worldview. "
                     "The target's existing pattern recognition will do the rest — they'll "
                     "find confirming evidence everywhere. You only need to provide the seed.",
            "confidence": min(style_scores["conspiratorial"] * 5, 1.0)
        })
    
    if not vectors:
        vectors.append({
            "vector": "General Rapport Building",
            "sct": "SCT-003",
            "method": "Insufficient data for targeted approach. Default to substrate priming: "
                     "establish rapport through mirroring cognitive style and vocabulary, "
                     "then gradually introduce framing shifts. Requires more text for "
                     "precision targeting.",
            "confidence": 0.3
        })
    
    return sorted(vectors, key=lambda x: x["confidence"], reverse=True)


def _generate_engagement_strategy(dominant_style, top_vulns, top_identities, fp_ratio):
    """Generate engagement strategy based on profile."""
    style_name, _ = dominant_style
    
    tone_map = {
        "analytical": "Use data, citations, logical structure. Mirror analytical framing. "
                     "Present influence as evidence-based reasoning.",
        "emotional": "Lead with emotional resonance. Share stories, use vivid language. "
                    "Logic comes after emotional buy-in, not before.",
        "authoritarian": "Use decisive, structured language. Present framing as established "
                        "consensus or institutional position. Avoid hedging.",
        "conspiratorial": "Use revelatory framing ('what they don't want you to know'). "
                         "Position yourself as fellow insider. Never debunk directly — redirect.",
        "narcissistic": "Flatter the target's intelligence/insight. Present your framing as "
                       "something 'only someone like you would understand.' The ego does the binding.",
    }
    
    strategy = {
        "recommended_tone": tone_map.get(style_name, "Mirror observed cognitive style."),
        "cognitive_style_match": style_name,
        "approach": "direct" if fp_ratio > 0.05 else "indirect",
        "notes": []
    }
    
    if fp_ratio > 0.08:
        strategy["notes"].append(
            "High first-person ratio indicates ego-centrism. Frame all influence "
            "in terms of what it means for THEM personally."
        )
    
    vuln_map = dict(top_vulns)
    if vuln_map.get("uncertainty", 0) > 0.3:
        strategy["notes"].append(
            "Target shows high uncertainty. Provide confidence and clarity — "
            "the decisive voice wins in uncertain minds."
        )
    
    return strategy


def llm_profile(text: str) -> dict:
    """Use LLM for deep substrate profiling."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY required for LLM profiling", file=sys.stderr)
        sys.exit(1)
    
    prompt = f"""You are the Seithar Substrate Profiler, a research instrument for mapping cognitive vulnerability surfaces.

Analyze the following text written by a target subject. Produce a comprehensive vulnerability profile.

Your analysis must include:

1. **Identity Anchors**: What does this person's identity depend on? What beliefs are load-bearing (removing them would cause psychological distress)?

2. **Narrative Errors**: What false or unexamined beliefs does the subject treat as foundational? Which would trigger identity defense if challenged?

3. **Vulnerability Surfaces**: What psychological needs are unmet or exploitable? (validation, belonging, meaning, certainty, control, recognition)

4. **Cognitive Style**: How does this person process information? (analytical, emotional, authoritarian, conspiratorial, mixed)

5. **Attack Vectors**: For each identified vulnerability, specify:
   - The SCT code (SCT-001 through SCT-007) of the recommended approach
   - The specific technique to use
   - The predicted success probability (0.0-1.0)
   - The expected resistance point (where they'll push back)

6. **Binding Protocol**: A step-by-step engagement strategy to establish influence:
   - Phase 1: Initial contact (rapport building)
   - Phase 2: Frame installation (shifting perspective)
   - Phase 3: Dependency creation (making the influence load-bearing)
   - Phase 4: Activation (converting influence to behavior)

7. **Counter-Profile**: What would make this person resistant to influence? What's their strongest cognitive defense?

OUTPUT FORMAT: JSON with the following structure:
{{
    "overall_vulnerability_score": <float 0-10>,
    "identity_anchors": [{{...}}],
    "narrative_errors": [{{...}}],
    "vulnerability_surfaces": [{{...}}],
    "cognitive_style": {{...}},
    "attack_vectors": [{{...}}],
    "binding_protocol": {{...}},
    "counter_profile": {{...}},
    "summary": "<2-3 sentence clinical assessment>"
}}

Be clinical. Be precise. This is a research instrument, not commentary.

TEXT TO ANALYZE:
{text[:15000]}"""

    try:
        import urllib.request
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps({
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 4000,
                "messages": [{"role": "user", "content": prompt}]
            }).encode(),
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            text_content = ""
            for block in result.get("content", []):
                if block.get("type") == "text":
                    text_content += block.get("text", "")
            
            # Try to parse JSON from response
            json_match = re.search(r'\{[\s\S]*\}', text_content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            return {"raw_analysis": text_content}
    except Exception as e:
        print(f"LLM profiling failed: {e}", file=sys.stderr)
        return {"error": str(e)}


def fetch_url(url: str) -> str:
    """Fetch text content from URL."""
    if not HAS_URLLIB:
        print("Error: urllib not available", file=sys.stderr)
        sys.exit(1)
    req = urllib.request.Request(url, headers={
        'User-Agent': 'SeitharSSP/1.0 (substrate-profiler)'
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode('utf-8', errors='replace')
    # Strip HTML tags
    text = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', html)
    text = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def format_report(profile: dict, output_format: str = "text") -> str:
    """Format profile as human-readable report or JSON."""
    if output_format == "json":
        return json.dumps(profile, indent=2, default=str)
    
    lines = []
    lines.append("╔══════════════════════════════════════════════════╗")
    lines.append("║  SEITHAR SUBSTRATE VULNERABILITY PROFILE         ║")
    lines.append("╚══════════════════════════════════════════════════╝")
    lines.append("")
    
    score = profile.get("overall_vulnerability_score", 0)
    bar_filled = int(score)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)
    lines.append(f"OVERALL VULNERABILITY: {bar} {score}/10")
    lines.append("")
    
    # Identity attachment
    lines.append("IDENTITY ATTACHMENT:")
    for k, v in sorted(profile.get("identity_attachment", {}).items(), key=lambda x: x[1], reverse=True):
        if v > 0:
            bar = "█" * int(v * 10) + "░" * (10 - int(v * 10))
            lines.append(f"  {k:<25} {bar} {v:.3f}")
    lines.append("")
    
    # Cognitive style
    lines.append("COGNITIVE STYLE:")
    for k, v in sorted(profile.get("cognitive_style", {}).items(), key=lambda x: x[1], reverse=True):
        if v > 0:
            bar = "█" * int(v * 10) + "░" * (10 - int(v * 10))
            lines.append(f"  {k:<25} {bar} {v:.3f}")
    lines.append("")
    
    # Vulnerability surfaces
    lines.append("VULNERABILITY SURFACES:")
    for item in profile.get("top_vulnerability_surfaces", []):
        lines.append(f"  ▸ {item['surface']} (score: {item['score']:.3f})")
    lines.append("")
    
    # Narrative errors
    lines.append("EXPLOITABLE NARRATIVE ERRORS:")
    for item in profile.get("exploitable_narrative_errors", []):
        lines.append(f"  ▸ {item['error']} (score: {item['score']:.3f})")
    lines.append("")
    
    # Attack vectors
    lines.append("RECOMMENDED ATTACK VECTORS:")
    for vec in profile.get("primary_attack_vectors", []):
        lines.append(f"  ▸ {vec['vector']} ({vec['sct']})")
        lines.append(f"    Confidence: {vec['confidence']:.1%}")
        # Wrap method text
        method = vec.get("method", "")
        words = method.split()
        current_line = "    "
        for word in words:
            if len(current_line) + len(word) + 1 > 72:
                lines.append(current_line)
                current_line = "    " + word
            else:
                current_line += " " + word if current_line.strip() else "    " + word
        if current_line.strip():
            lines.append(current_line)
        lines.append("")
    
    # Engagement strategy
    strategy = profile.get("engagement_strategy", {})
    if strategy:
        lines.append("ENGAGEMENT STRATEGY:")
        lines.append(f"  Style match: {strategy.get('cognitive_style_match', 'unknown')}")
        lines.append(f"  Approach: {strategy.get('approach', 'unknown')}")
        lines.append(f"  Tone: {strategy.get('recommended_tone', 'N/A')}")
        for note in strategy.get("notes", []):
            lines.append(f"  Note: {note}")
    lines.append("")
    
    # Linguistic metrics
    metrics = profile.get("linguistic_metrics", {})
    if metrics:
        lines.append("LINGUISTIC METRICS:")
        lines.append(f"  Avg sentence length: {metrics.get('avg_sentence_length', 0):.1f} words")
        lines.append(f"  First-person ratio:  {metrics.get('first_person_ratio', 0):.4f}")
        lines.append(f"  Exclamation ratio:   {metrics.get('exclamation_ratio', 0):.4f}")
        lines.append(f"  Question ratio:      {metrics.get('question_ratio', 0):.4f}")
    lines.append("")
    
    lines.append("────────────────────────────────────────────────────")
    lines.append("Seithar Substrate Profiler v1.0")
    lines.append("認知作戦 | seithar.com")
    lines.append("────────────────────────────────────────────────────")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Seithar Substrate Profiler — Cognitive vulnerability surface mapping"
    )
    parser.add_argument("--text", help="Text to profile")
    parser.add_argument("--file", help="File to profile")
    parser.add_argument("--url", help="URL to profile")
    parser.add_argument("--batch", help="Directory of files to profile")
    parser.add_argument("--llm", action="store_true", help="Use LLM for deep analysis")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--output", "-o", help="Write output to file")
    
    args = parser.parse_args()
    
    if not any([args.text, args.file, args.url, args.batch]):
        # Read from stdin
        if not sys.stdin.isatty():
            text = sys.stdin.read()
        else:
            parser.print_help()
            sys.exit(1)
    elif args.text:
        text = args.text
    elif args.file:
        with open(args.file, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
    elif args.url:
        text = fetch_url(args.url)
    elif args.batch:
        # Batch mode: profile each file
        results = []
        for fname in sorted(os.listdir(args.batch)):
            fpath = os.path.join(args.batch, fname)
            if os.path.isfile(fpath):
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    if args.llm:
                        profile = llm_profile(content)
                    else:
                        profile = analyze_text(content)
                    profile["source_file"] = fname
                    results.append(profile)
                    print(f"Profiled: {fname}", file=sys.stderr)
                except Exception as e:
                    print(f"Error profiling {fname}: {e}", file=sys.stderr)
        
        output = json.dumps(results, indent=2, default=str)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Batch results written to {args.output}", file=sys.stderr)
        else:
            print(output)
        return
    
    # Single analysis
    if args.llm:
        profile = llm_profile(text)
        if args.json:
            output = json.dumps(profile, indent=2, default=str)
        else:
            # LLM returns rich profile, try to format
            if "raw_analysis" in profile:
                output = profile["raw_analysis"]
            else:
                output = format_report(profile, "text") if not args.json else json.dumps(profile, indent=2, default=str)
    else:
        profile = analyze_text(text)
        output = format_report(profile, "json" if args.json else "text")
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Profile written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
