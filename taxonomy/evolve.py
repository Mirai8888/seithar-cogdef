#!/usr/bin/env python3
"""
Seithar Taxonomy Evolution Engine

Proposes, accumulates evidence for, promotes, and deprecates SCT codes.
No external dependencies beyond Python stdlib.

Usage:
    python evolve.py propose "description" --source "paper-name"
    python evolve.py evidence SCT-013 --source "paper" --desc "details"
    python evolve.py promote --min-sources 3
    python evolve.py deprecate --days 180
    python evolve.py patterns SCT-001
    python evolve.py export
"""

import argparse
import json
import math
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.json"


def load_schema() -> dict:
    """Load the taxonomy schema from disk."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_schema(schema: dict) -> None:
    """Save the taxonomy schema to disk."""
    schema["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(SCHEMA_PATH, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
        f.write("\n")


def tokenize(text: str) -> list:
    """Simple whitespace + punctuation tokenizer, lowercased."""
    return re.findall(r"[a-z0-9]+", text.lower())


def tf_idf_vector(tokens: list, idf: dict) -> dict:
    """Compute TF-IDF vector for a token list."""
    tf = Counter(tokens)
    total = len(tokens) if tokens else 1
    return {t: (tf[t] / total) * idf.get(t, 1.0) for t in tf}


def cosine_sim(vec_a: dict, vec_b: dict) -> float:
    """Cosine similarity between two sparse vectors."""
    common = set(vec_a) & set(vec_b)
    if not common:
        return 0.0
    dot = sum(vec_a[k] * vec_b[k] for k in common)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def keyword_overlap(keywords_a: list, text_b_tokens: set) -> float:
    """Fraction of keywords from A found in B's tokens."""
    if not keywords_a:
        return 0.0
    hits = sum(1 for kw in keywords_a if kw.lower() in text_b_tokens)
    return hits / len(keywords_a)


def build_idf(schema: dict) -> dict:
    """Build IDF from all embedding texts in the taxonomy."""
    docs = []
    for code_data in schema["codes"].values():
        tokens = set(tokenize(code_data.get("embedding_text", "")))
        docs.append(tokens)
    n = len(docs) if docs else 1
    all_tokens = set()
    for d in docs:
        all_tokens.update(d)
    idf = {}
    for t in all_tokens:
        df = sum(1 for d in docs if t in d)
        idf[t] = math.log((n + 1) / (df + 1)) + 1
    return idf


def next_code_id(schema: dict) -> str:
    """Generate the next SCT code ID."""
    existing = []
    for code_id in schema["codes"]:
        match = re.match(r"SCT-(\d+)", code_id)
        if match:
            existing.append(int(match.group(1)))
    next_num = max(existing) + 1 if existing else 1
    return f"SCT-{next_num:03d}"


def find_best_match(description: str, schema: dict) -> tuple:
    """
    Find the best matching existing code for a description.
    Returns (code_id, similarity_score) or (None, 0.0).
    """
    idf = build_idf(schema)
    desc_tokens = tokenize(description)
    desc_vec = tf_idf_vector(desc_tokens, idf)
    desc_token_set = set(desc_tokens)

    best_id = None
    best_score = 0.0

    for code_id, code_data in schema["codes"].items():
        emb_tokens = tokenize(code_data.get("embedding_text", ""))
        emb_vec = tf_idf_vector(emb_tokens, idf)
        cos = cosine_sim(desc_vec, emb_vec)
        kw_score = keyword_overlap(code_data.get("keywords", []), desc_token_set)
        # Weighted combination: 60% TF-IDF cosine, 40% keyword overlap
        combined = 0.6 * cos + 0.4 * kw_score
        if combined > best_score:
            best_score = combined
            best_id = code_id

    return best_id, best_score


def propose_candidate(
    technique_description: str,
    source: str,
    evidence: str = "",
    threshold: float = 0.35,
) -> dict:
    """
    Check if a technique matches an existing code. If similarity is below
    threshold, create a new candidate code. Otherwise accumulate evidence
    on the matching code.

    Returns dict with action taken and details.
    """
    schema = load_schema()
    best_id, score = find_best_match(technique_description, schema)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if score >= threshold and best_id:
        # Matches existing code -- accumulate evidence
        return accumulate_evidence(
            best_id, source, evidence or technique_description, _schema=schema
        )

    # Create new candidate
    new_id = next_code_id(schema)
    # Extract keywords: most frequent non-stopword tokens
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "shall", "can",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "and",
        "but", "or", "nor", "not", "so", "yet", "both", "either",
        "neither", "each", "every", "all", "any", "few", "more",
        "most", "other", "some", "such", "no", "only", "own", "same",
        "than", "too", "very", "just", "that", "this", "it", "its",
        "they", "their", "them", "we", "our", "us", "he", "she",
        "his", "her", "him", "who", "which", "what", "when", "where",
        "how", "why", "if", "then", "about", "up", "out", "also",
    }
    tokens = tokenize(technique_description)
    filtered = [t for t in tokens if t not in stopwords and len(t) > 2]
    freq = Counter(filtered)
    keywords = [w for w, _ in freq.most_common(10)]

    # Generate a short name from the description
    name_words = technique_description.split()[:5]
    name = " ".join(name_words)
    if len(name_words) < len(technique_description.split()):
        name += "..."

    schema["codes"][new_id] = {
        "id": new_id,
        "name": name,
        "description": technique_description,
        "keywords": keywords,
        "embedding_text": technique_description,
        "evidence": [
            {"source": source, "description": evidence or technique_description, "date": today}
        ],
        "status": "candidate",
        "created": today,
        "last_seen": today,
    }
    save_schema(schema)
    return {
        "action": "created_candidate",
        "code_id": new_id,
        "name": name,
        "best_match": best_id,
        "best_match_score": round(score, 3),
    }


def accumulate_evidence(
    code_id: str, source: str, description: str, _schema: dict = None
) -> dict:
    """Add evidence to an existing code."""
    schema = _schema or load_schema()
    if code_id not in schema["codes"]:
        return {"action": "error", "message": f"Code {code_id} not found"}

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    code = schema["codes"][code_id]
    code["evidence"].append(
        {"source": source, "description": description, "date": today}
    )
    code["last_seen"] = today
    save_schema(schema)
    return {
        "action": "evidence_added",
        "code_id": code_id,
        "total_evidence": len(code["evidence"]),
    }


def promote_candidates(min_sources: int = 3) -> list:
    """Promote candidate codes with enough independent sources to confirmed."""
    schema = load_schema()
    promoted = []
    for code_id, code in schema["codes"].items():
        if code["status"] != "candidate":
            continue
        unique_sources = set(e["source"] for e in code["evidence"])
        if len(unique_sources) >= min_sources:
            code["status"] = "confirmed"
            promoted.append({"code_id": code_id, "sources": len(unique_sources)})
    if promoted:
        save_schema(schema)
    return promoted


def deprecation_check(days_unseen: int = 180) -> list:
    """Flag codes not seen in the wild for review."""
    schema = load_schema()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_unseen)).strftime("%Y-%m-%d")
    flagged = []
    for code_id, code in schema["codes"].items():
        if code["status"] == "deprecated":
            continue
        if code.get("last_seen", "2000-01-01") < cutoff:
            code["status"] = "deprecated"
            flagged.append({"code_id": code_id, "last_seen": code.get("last_seen")})
    if flagged:
        save_schema(schema)
    return flagged


def generate_scanner_patterns(code_id: str) -> list:
    """
    Extract regex patterns from the evidence corpus for a given code.
    Returns a list of pattern strings suitable for scanner.py.
    """
    schema = load_schema()
    if code_id not in schema["codes"]:
        return []

    code = schema["codes"][code_id]
    keywords = code.get("keywords", [])
    patterns = []

    for kw in keywords:
        # Escape regex special chars, allow word boundary matching
        escaped = re.escape(kw)
        patterns.append(rf"\b{escaped}\b")

    return patterns


def export_taxonomy() -> dict:
    """Return the full current taxonomy as a dict."""
    return load_schema()


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="Seithar Taxonomy Evolution Engine",
        epilog="Seithar Group | seithar.com",
    )
    sub = parser.add_subparsers(dest="command", help="Command to run")

    # propose
    p_propose = sub.add_parser("propose", help="Propose a new technique")
    p_propose.add_argument("description", help="Technique description")
    p_propose.add_argument("--source", required=True, help="Source reference")
    p_propose.add_argument("--evidence", default="", help="Additional evidence text")
    p_propose.add_argument(
        "--threshold", type=float, default=0.35, help="Similarity threshold"
    )

    # evidence
    p_evidence = sub.add_parser("evidence", help="Add evidence to existing code")
    p_evidence.add_argument("code_id", help="SCT code ID")
    p_evidence.add_argument("--source", required=True, help="Source reference")
    p_evidence.add_argument("--desc", required=True, help="Evidence description")

    # promote
    p_promote = sub.add_parser("promote", help="Promote candidates with enough sources")
    p_promote.add_argument(
        "--min-sources", type=int, default=3, help="Min independent sources"
    )

    # deprecate
    p_deprecate = sub.add_parser("deprecate", help="Flag stale codes for review")
    p_deprecate.add_argument(
        "--days", type=int, default=180, help="Days unseen threshold"
    )

    # patterns
    p_patterns = sub.add_parser("patterns", help="Generate scanner patterns for a code")
    p_patterns.add_argument("code_id", help="SCT code ID")

    # export
    sub.add_parser("export", help="Export full taxonomy as JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "propose":
        result = propose_candidate(
            args.description, args.source, args.evidence, args.threshold
        )
        print(json.dumps(result, indent=2))

    elif args.command == "evidence":
        result = accumulate_evidence(args.code_id, args.source, args.desc)
        print(json.dumps(result, indent=2))

    elif args.command == "promote":
        result = promote_candidates(args.min_sources)
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No candidates met promotion threshold.")

    elif args.command == "deprecate":
        result = deprecation_check(args.days)
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No codes flagged for deprecation.")

    elif args.command == "patterns":
        result = generate_scanner_patterns(args.code_id)
        print(json.dumps(result, indent=2))

    elif args.command == "export":
        result = export_taxonomy()
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
