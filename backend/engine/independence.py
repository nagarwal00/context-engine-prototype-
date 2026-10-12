"""
Context Intelligence Framework - Source Independence and Claim Evidence
Implements Step 3.1 of ANTIGRAVITY_HANDOFF_V2.md:
- Pure function `independence_key(event, all_events=None) -> str`
- Passage extraction: `extract_best_passage(claim_text, event_text, threshold=0.25)`
- Claim extraction & evidence linking
- Support for duplicate-copy (>80% token overlap), same-thread, ADR+PR, commit+PR, and Slack
"""
import re
from typing import List, Dict, Any, Optional, Tuple, Sequence, Set
from backend.models import DecisionClaim, ClaimEvidence, Decision, Event


STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does",
    "doesn't", "doing", "don't", "down", "during", "each", "few", "for", "from", "further",
    "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll",
    "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how",
    "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll",
    "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the",
    "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they",
    "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've",
    "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't",
    "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
}

CONTRADICTION_CUES = {
    "reject", "rejected", "rejection", "unsuitable", "flawed", "failed",
    "bottleneck", "bottlenecks", "reverted", "dropped", "cannot", "do not use", "don't use",
    "instead of", "too slow", "too complex", "not recommended", "abandoned",
    "deprecated", "flaw", "anti-pattern", "vulnerability"
}


def normalize_text(text: str) -> str:
    """Normalizes text for duplicate and exact body detection."""
    if not text:
        return ""
    text_clean = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(text_clean.split())


def tokenize_content_words(text: str) -> List[str]:
    """Extracts non-stop content tokens from text."""
    if not text:
        return []
    tokens = re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def get_sentence_spans(text: str) -> List[Tuple[str, int, int]]:
    """
    Extracts sentence segments from text with exact character start/end offsets.
    Guarantees text[start:end] == sentence_text.
    """
    if not text:
        return []
    spans: List[Tuple[str, int, int]] = []
    pattern = re.compile(r"([^\n.!?]+(?:[\.!?]+|\n+|$))")
    for m in pattern.finditer(text):
        raw = m.group(0)
        s_text = raw.strip()
        if s_text:
            lead = len(raw) - len(raw.lstrip())
            start = m.start() + lead
            end = start + len(s_text)
            spans.append((s_text, start, end))

    if not spans and text.strip():
        s_text = text.strip()
        start = text.find(s_text)
        spans.append((s_text, start, start + len(s_text)))
    return spans


def extract_best_passage(
    claim_text: str,
    event_text: str,
    threshold: float = 0.25
) -> Tuple[Optional[str], Optional[int], Optional[int], str]:
    """
    Passage extraction (Step 3.1):
    For a claim and event text, picks best-matching sentence by content-word overlap.
    Returns: (passage_text, start_offset, end_offset, relation)
    - If overlap >= threshold: returns passage with exact character offsets and 'direct' or 'contradicting' relation.
    - If overlap < threshold: returns (None, None, None, 'indirect').
    """
    if not claim_text or not event_text:
        return None, None, None, "indirect"

    claim_tokens = set(tokenize_content_words(claim_text))
    if not claim_tokens:
        return None, None, None, "indirect"

    spans = get_sentence_spans(event_text)
    if not spans:
        return None, None, None, "indirect"

    best_score = 0.0
    best_span: Optional[Tuple[str, int, int]] = None

    for s_text, start, end in spans:
        s_tokens = set(tokenize_content_words(s_text))
        if not s_tokens:
            continue
        inter = claim_tokens & s_tokens
        if not inter:
            continue

        jaccard = len(inter) / len(claim_tokens | s_tokens)
        containment = len(inter) / min(len(claim_tokens), len(s_tokens))
        claim_coverage = len(inter) / len(claim_tokens)

        score = max(jaccard, claim_coverage, containment)
        if score > best_score:
            best_score = score
            best_span = (s_text, start, end)

    if best_score < threshold or best_span is None:
        return None, None, None, "indirect"

    passage_text, start_idx, end_idx = best_span

    # Check for contradiction cues
    passage_lower = passage_text.lower()
    claim_lower = claim_text.lower()

    has_contradiction = False
    for cue in CONTRADICTION_CUES:
        if cue in passage_lower and cue not in claim_lower:
            has_contradiction = True
            break

    relation = "contradicting" if has_contradiction else "direct"
    return passage_text, start_idx, end_idx, relation


def _get_field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _base_independence_key(event: Any) -> str:
    """Computes structural source independence key for a single event without cross-event copy check."""
    source_type = _get_field(event, "source_type", "")
    source_id = str(_get_field(event, "source_id", ""))
    repo = _get_field(event, "repo", "") or "unknown"
    source_url = _get_field(event, "source_url", "")
    title = _get_field(event, "title", "") or ""
    body = _get_field(event, "body", "") or ""
    raw_meta = _get_field(event, "raw_metadata", {}) or {}
    parent_ids = _get_field(event, "parent_event_ids", []) or []

    # 1. Same issue/PR thread: the issue/PR itself, comments, review comments
    if source_type in ("github_issue", "github_pr", "pr_review_comment", "issue_comment", "pr_comment"):
        thread_num = None
        if "pr_number" in raw_meta:
            thread_num = raw_meta["pr_number"]
        elif "issue_number" in raw_meta:
            thread_num = raw_meta["issue_number"]
        elif "number" in raw_meta:
            thread_num = raw_meta["number"]

        if not thread_num and source_url:
            m = re.search(r"/(?:issues|pull)/(\d+)", source_url)
            if m:
                thread_num = int(m.group(1))

        if not thread_num and source_type in ("github_issue", "github_pr") and source_id.isdigit():
            thread_num = int(source_id)

        if not thread_num and title:
            m = re.search(r"(?:PR\s*#|#)(\d+)", title)
            if m:
                thread_num = int(m.group(1))

        if not thread_num and parent_ids:
            for pid in parent_ids:
                m = re.search(r"(?:evt_pr|evt_issue)_[^_]+_(\d+)", pid)
                if m:
                    thread_num = int(m.group(1))
                    break

        if thread_num is not None:
            return f"thread:{repo}#{thread_num}"

    # 2. Git commit: PR if known, else commit:<sha>
    if source_type == "git_commit":
        pr_num = None
        if "pr_number" in raw_meta:
            pr_num = raw_meta["pr_number"]
        elif "pr" in raw_meta:
            pr_num = raw_meta["pr"]

        if not pr_num:
            m = re.search(r"(?:Merge pull request #|pull/|\(#|PR\s*#)(\d+)", f"{title} {body}")
            if m:
                pr_num = int(m.group(1))

        if pr_num is not None:
            return f"thread:{repo}#{pr_num}"

        sha = source_id.split("@")[0].strip() if "@" in source_id else source_id
        return f"commit:{sha}"

    # 3. ADR / doc file: one group per file path; different revisions map to same group
    if source_type in ("adr", "doc"):
        file_path = raw_meta.get("file_path") or source_id
        norm_path = str(file_path).replace("\\", "/").strip("/.")
        return f"doc:{repo}:{norm_path}"

    # 4. Slack: one group per thread
    if source_type in ("slack", "slack_message"):
        channel = raw_meta.get("slack_channel") or raw_meta.get("channel", "general")
        thread_ts = raw_meta.get("thread_ts") or raw_meta.get("slack_ts") or raw_meta.get("ts") or source_id
        return f"slack:{repo}:{channel}#{thread_ts}"

    # Fallback default group
    return f"{source_type}:{repo}:{source_id}"


def independence_key(event: Any, all_events: Optional[Sequence[Any]] = None) -> str:
    """
    Pure function implementing Step 3.1 source independence rules:
    - Same issue/PR thread -> thread:<repo>#<number>
    - Commit and PR containing it -> thread:<repo>#<number> (else commit:<sha>)
    - ADR/doc file -> doc:<repo>:<path>
    - Duplicate copy/quote (>80% token overlap or identical normalised body) -> maps to original event's group
    - Slack -> slack:<repo>:<channel>#<thread_ts>
    - Different authors alone do not make two sources independent.
    """
    event_id = _get_field(event, "event_id", "")
    curr_body = _get_field(event, "body", "") or ""
    curr_norm = normalize_text(curr_body)
    curr_tokens = set(tokenize_content_words(curr_body))

    # Check for duplicate/copy against prior events in all_events
    if all_events and curr_body.strip():
        curr_idx = None
        try:
            curr_idx = list(all_events).index(event)
        except (ValueError, TypeError):
            pass

        curr_ts = _get_field(event, "timestamp", "") or _get_field(event, "ts", "")

        for idx, other in enumerate(all_events):
            other_id = _get_field(other, "event_id", "")
            if other_id and other_id == event_id:
                continue
            if other is event:
                continue

            # Prioritization: the copy maps to the original event (which precedes it in sequence or timestamp)
            other_ts = _get_field(other, "timestamp", "") or _get_field(other, "ts", "")
            if curr_idx is not None and idx > curr_idx:
                if not (other_ts and curr_ts and other_ts < curr_ts):
                    continue
            elif curr_ts and other_ts and curr_ts < other_ts:
                continue

            other_body = _get_field(other, "body", "") or ""
            if not other_body.strip():
                continue

            other_norm = normalize_text(other_body)
            # Rule: identical normalised body (min 10 chars)
            if len(curr_norm) >= 10 and curr_norm == other_norm:
                return _base_independence_key(other)

            # Rule: body containing > 80% of another event's tokens
            other_tokens = set(tokenize_content_words(other_body))
            if len(other_tokens) >= 5 and len(curr_tokens) >= 5:
                inter_len = len(curr_tokens & other_tokens)
                overlap_other = inter_len / len(other_tokens)
                overlap_curr = inter_len / len(curr_tokens)
                if overlap_other > 0.8 or overlap_curr > 0.8:
                    return _base_independence_key(other)

    # Check if a commit is contained in a known PR event
    source_type = _get_field(event, "source_type", "")
    source_id = str(_get_field(event, "source_id", ""))
    repo = _get_field(event, "repo", "") or "unknown"
    if source_type == "git_commit" and all_events and source_id:
        for other in all_events:
            other_type = _get_field(other, "source_type", "")
            if other_type in ("github_pr", "pr_review_comment"):
                other_meta = _get_field(other, "raw_metadata", {}) or {}
                commit_shas = other_meta.get("commit_shas", [])
                short_sha = source_id[:8]
                other_body = _get_field(other, "body", "") or ""
                if source_id in commit_shas or any(c.startswith(short_sha) for c in commit_shas) or short_sha in other_body:
                    pr_num = other_meta.get("pr_number") or _get_field(other, "source_id", "")
                    if pr_num:
                        return f"thread:{repo}#{pr_num}"

    return _base_independence_key(event)


def extract_claims_from_decision(decision: Any) -> List[DecisionClaim]:
    """
    Extracts atomic claims from a Decision:
    - Rationale claim (claim_type='rationale')
    - Alternatives considered claims (claim_type='alternative_rejected')
    """
    claims: List[DecisionClaim] = []
    dec_id = _get_field(decision, "decision_id", "")
    rationale = _get_field(decision, "rationale", "")

    if rationale and rationale.strip():
        claims.append(DecisionClaim(
            claim_id=f"clm_{dec_id}_rationale",
            decision_id=dec_id,
            claim_type="rationale",
            text=rationale.strip()
        ))

    alts = _get_field(decision, "alternatives_considered", []) or []
    for idx, alt in enumerate(alts):
        desc = alt.get("description", "").strip() if isinstance(alt, dict) else getattr(alt, "description", "").strip()
        reason = alt.get("rejection_reason", "").strip() if isinstance(alt, dict) else getattr(alt, "rejection_reason", "").strip()
        if desc:
            claim_text = f"Alternative rejected: {desc}."
            if reason:
                claim_text += f" Reason: {reason}"
            claims.append(DecisionClaim(
                claim_id=f"clm_{dec_id}_alt_{idx}",
                decision_id=dec_id,
                claim_type="alternative_rejected",
                text=claim_text
            ))

    return claims


def link_claim_to_event(
    claim: DecisionClaim,
    event: Any,
    all_events: Optional[Sequence[Any]] = None,
    threshold: float = 0.25
) -> ClaimEvidence:
    """
    Links a DecisionClaim to an Event, computing source group, passage, offsets, and relation.
    """
    source_group = independence_key(event, all_events=all_events)
    title = _get_field(event, "title", "") or ""
    body = _get_field(event, "body", "") or ""
    full_text = f"{title}\n{body}".strip() if title else body

    p_text, start_idx, end_idx, relation = extract_best_passage(
        claim_text=claim.text,
        event_text=full_text,
        threshold=threshold
    )

    ev_id = _get_field(event, "event_id", "")
    return ClaimEvidence(
        claim_id=claim.claim_id,
        event_id=ev_id,
        relation=relation,
        passage_text=p_text,
        passage_start=start_idx,
        passage_end=end_idx,
        source_group=source_group
    )


def calculate_independent_sources(claim_evidences: Sequence[Any]) -> Set[str]:
    """Returns the set of unique independent source groups from a collection of ClaimEvidence."""
    groups: Set[str] = set()
    for ce in claim_evidences:
        sg = _get_field(ce, "source_group", "")
        if sg:
            groups.add(sg)
    return groups


def get_independent_source_count(claim_evidences: Sequence[Any]) -> int:
    """Returns the count of independent source groups."""
    return len(calculate_independent_sources(claim_evidences))


def count_independent_sources(events: Sequence[Any], all_events: Optional[Sequence[Any]] = None) -> int:
    """Computes the count of unique independent source groups for a list of events."""
    groups = {independence_key(e, all_events=all_events) for e in events}
    return len(groups)

