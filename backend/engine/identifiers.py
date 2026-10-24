"""
Generic Identifier & Concept Extraction Engine (Step 3.2b)
Extracts identifier candidates, module references, and concepts from decision text
without hardcoding domain scenario vocabulary.
"""
import os
import re
from typing import List, Set, Optional

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me",
    "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
    "other", "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so", "some",
    "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these",
    "they", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "we",
    "were", "what", "when", "where", "which", "while", "who", "whom", "why", "with", "would", "you",
    "your", "yours", "yourself", "yourselves",
    # Common meta terms
    "rejected", "alternative", "decision", "architecture", "system", "module", "service", "approach",
    "causes", "causing", "instead", "rather", "without", "because", "causes", "reason"
}

KEYWORDS = {
    "true", "false", "none", "self", "this", "return", "import", "class", "def", "function",
    "const", "let", "var", "public", "private", "protected", "if", "else", "for", "while"
}


def is_module_like(token: str) -> bool:
    """Returns True if token looks like an importable module or package name."""
    if not token or len(token) < 2:
        return False
    if token.lower() in KEYWORDS or token.lower() in STOP_WORDS:
        return False
    # Valid Python/JS/Go identifier or dotted path
    return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]+)*$", token))


def extract_identifiers(text: str) -> Set[str]:
    """
    Extracts identifier and concept candidates from free text:
    - Backticked spans: `token`
    - import X / from X import patterns
    - require("X") patterns
    - use X patterns
    - snake_case tokens with _ (length >= 5)
    - CamelCase tokens
    - Dotted module names
    - Hyphenated concept tokens with - (length >= 5)
    """
    if not text:
        return set()

    candidates: Set[str] = set()

    # 1. Backticked spans
    backticked = re.findall(r"`([^`\n]+)`", text)
    for b in backticked:
        cleaned = b.strip()
        if cleaned and len(cleaned) >= 2 and cleaned.lower() not in STOP_WORDS:
            candidates.add(cleaned)

    # 2. import X / from X import
    imports = re.findall(r"\bimport\s+([a-zA-Z_][a-zA-Z0-9_\.]*)", text)
    from_imports = re.findall(r"\bfrom\s+([a-zA-Z_][a-zA-Z0-9_\.]*)\s+import", text)
    for imp in imports + from_imports:
        if imp.lower() not in STOP_WORDS and imp.lower() not in KEYWORDS:
            candidates.add(imp)

    # 3. require("X")
    requires = re.findall(r"\brequire\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", text)
    for req in requires:
        cleaned = req.strip()
        if cleaned and cleaned.lower() not in STOP_WORDS:
            candidates.add(cleaned)

    # 4. use X patterns
    uses = re.findall(r"\buse\s+([a-zA-Z_][a-zA-Z0-9_\.]*)", text, re.IGNORECASE)
    for u in uses:
        if u.lower() not in STOP_WORDS and u.lower() not in KEYWORDS and len(u) >= 3:
            candidates.add(u)

    # 5. snake_case tokens (length >= 5)
    snake_tokens = re.findall(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b", text)
    for s in snake_tokens:
        if len(s) >= 5 and s.lower() not in STOP_WORDS:
            candidates.add(s)

    # 6. CamelCase tokens
    camel_tokens = re.findall(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+\b", text)
    for c in camel_tokens:
        if c.lower() not in STOP_WORDS:
            candidates.add(c)

    # 7. Dotted module names
    dotted_tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]+)+\b", text)
    for d in dotted_tokens:
        if d.lower() not in STOP_WORDS:
            candidates.add(d)

    # 8. Hyphenated concept tokens with - (length >= 5)
    hyphen_tokens = re.findall(r"\b[a-zA-Z][a-zA-Z0-9]*(?:-[a-zA-Z0-9]+)+\b", text)
    for h in hyphen_tokens:
        if len(h) >= 5 and h.lower() not in STOP_WORDS:
            candidates.add(h)

    return candidates


def extract_concept_tokens(description: str, rejection_reason: str = "", accepted_text: str = "") -> Set[str]:
    """
    Extracts distinctive concept tokens for a rejected idea or alternative:
    Includes all extract_identifiers candidates PLUS non-stopword tokens (length >= 5)
    appearing in the rejected description that do not appear in the accepted decision text.
    """
    text = description or ""
    concepts = set(extract_identifiers(text))

    acc_lower = (accepted_text or "").lower()
    acc_words = set(re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", acc_lower))

    # Single-word content tokens (length >= 5, alphabetic) from description
    for word in re.findall(r"\b[a-zA-Z]{5,}\b", text):
        w_lower = word.lower()
        if w_lower not in STOP_WORDS and w_lower not in KEYWORDS and w_lower not in acc_words:
            concepts.add(w_lower)

    return concepts



def derive_paths_from_artifacts(artifacts: Optional[List[str]]) -> List[str]:
    """
    Derives glob path patterns from a decision's affected entities (directory + extension).
    Falls back to ['**/*'] if artifacts are missing or empty.
    """
    if not artifacts:
        return ["**/*"]

    paths = []
    for art in artifacts:
        if not art:
            continue
        clean_art = art.split("::")[0].replace("\\", "/")
        directory = os.path.dirname(clean_art)
        _, ext = os.path.splitext(clean_art)

        if directory and ext:
            paths.append(f"{directory}/**/*{ext}")
            paths.append(f"{directory}/*{ext}")
        elif directory:
            paths.append(f"{directory}/**/*")
        elif ext:
            paths.append(f"**/*{ext}")
        else:
            paths.append(clean_art)

        base = os.path.basename(clean_art)
        if base:
            paths.append(f"**/{base}")

    seen = set()
    deduped = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            deduped.append(p)
    return deduped if deduped else ["**/*"]


def extract_require_import_modules(text: str) -> List[str]:
    """
    Extracts module names that must be imported, exclusively from explicit backticked phrases
    such as 'must use `X`' or 'requires `X`'.
    """
    if not text:
        return []
    matches = re.findall(r"(?:must\s+use|must\s+adopt|require(?:s)?)\s+`([^`]+)`", text, re.IGNORECASE)
    results = []
    for m in matches:
        cleaned = m.strip()
        if is_module_like(cleaned):
            results.append(cleaned)
    return results
