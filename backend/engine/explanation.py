"""
Evidence-Grounded Explanation Generator (Section 9 & Step 3.3)
Synthesizes verified explanations with claim-level passage citations,
deterministic evidence assessment, sentence-level support validation,
and explicit abstention when evidence is insufficient.
"""
from typing import Dict, Any, List, Optional, Tuple, Set
import re
from backend.db import Database


STOP_WORDS = {
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


def extract_content_tokens(text: str) -> List[str]:
    """Tokenizes text into content words (length > 3, not in stopwords) per METRICS.md Section 6."""
    if not text:
        return []
    tokens = re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 3]


def split_into_sentences(text: str) -> List[str]:
    """Splits explanation text into distinct sentences."""
    if not text:
        return []
    sentences = []
    for chunk in re.split(r"(?<=[.!?])\s+|\n+", text):
        clean = chunk.strip()
        if clean and len(clean) > 3:
            sentences.append(clean)
    return sentences


def verify_sentence_support(
    text: str,
    evidence_items: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[str], float]:
    """
    Sentence-level support check (Step 3.3 & METRICS.md Section 6):
    - Splits text into sentences.
    - Each sentence is checked against evidence items.
    - Supported if >= 50% content words appear in evidence passage (or event title + body).
    - Unsupported sentences are flagged.
    Returns: (statements, unsupported_sentences, claim_support_rate)
    """
    sentences = split_into_sentences(text)
    if not sentences:
        return [], [], 1.0

    statements: List[Dict[str, Any]] = []
    unsupported: List[str] = []
    supported_count = 0

    evidence_corpus = []
    for ev in evidence_items:
        passage = ev.get("relevant_passage") or ""
        title = ev.get("title") or ""
        corpus_text = f"{title} {passage}".strip()
        corpus_tokens = set(extract_content_tokens(corpus_text))
        evidence_corpus.append({
            "event_id": ev.get("event_id"),
            "passage": passage,
            "source_link": ev.get("source_link"),
            "tokens": corpus_tokens
        })

    for s in sentences:
        s_tokens = extract_content_tokens(s)
        if not s_tokens:
            statements.append({
                "text": s,
                "supported": True,
                "passage": None,
                "source_link": None,
                "event_id": None,
                "flagged_unsupported": False
            })
            supported_count += 1
            continue

        best_match = None
        best_overlap_ratio = 0.0

        for ec in evidence_corpus:
            if not ec["tokens"]:
                continue
            inter = set(s_tokens) & ec["tokens"]
            ratio = len(inter) / len(s_tokens)
            if ratio > best_overlap_ratio:
                best_overlap_ratio = ratio
                best_match = ec

        if best_overlap_ratio >= 0.50 and best_match:
            statements.append({
                "text": s,
                "supported": True,
                "passage": best_match["passage"] or None,
                "source_link": best_match["source_link"] or None,
                "event_id": best_match["event_id"] or None,
                "overlap_ratio": round(best_overlap_ratio, 2),
                "flagged_unsupported": False
            })
            supported_count += 1
        else:
            statements.append({
                "text": s,
                "supported": False,
                "passage": best_match["passage"] if best_match else None,
                "source_link": best_match["source_link"] if best_match else None,
                "event_id": best_match["event_id"] if best_match else None,
                "overlap_ratio": round(best_overlap_ratio, 2),
                "flagged_unsupported": True
            })
            unsupported.append(s)

    rate = round(supported_count / len(sentences), 2)
    return statements, unsupported, rate


def build_decision_evidence_block(db: Database, dec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds the Step 3.3 per-decision structure:
    - decision, lifecycle_state, needs_review, evidence_assessment.label
    - direct_support[], indirect_support[], missing_corroboration[], conflicting_evidence[]
    - per evidence item: source_link, url_format_ok, relevant_passage, author, date, relation, source_group
    """
    from backend.engine.evidence import assess
    dec_id = dec["decision_id"]

    assessment = assess(dec, db=db)

    claim_ev_rows = db.get_all_claim_evidence_for_decision(dec_id)
    trail = db.query_full_evidence_trail(dec_id)
    ev_events = {ev["event_id"]: ev for ev in trail.get("evidence_events", [])}

    direct_support: List[Dict[str, Any]] = []
    indirect_support: List[Dict[str, Any]] = []

    for ce in claim_ev_rows:
        ev_id = ce.get("event_id")
        ev_info = ev_events.get(ev_id, {})
        source_url = ce.get("source_url") or ev_info.get("source_url", "")
        url_format_ok = bool(source_url and source_url.startswith(("http://", "https://")))

        item = {
            "event_id": ev_id,
            "source_link": source_url,
            "url_format_ok": url_format_ok,
            "relevant_passage": ce.get("passage_text"),
            "passage_start": ce.get("passage_start"),
            "passage_end": ce.get("passage_end"),
            "author": ce.get("author") or ev_info.get("author", "unknown"),
            "date": ce.get("ts") or ev_info.get("ts", ""),
            "relation": ce.get("relation", "direct"),
            "source_group": ce.get("source_group", ""),
            "title": ce.get("event_title") or ev_info.get("title", ""),
            "source_type": ce.get("source_type") or ev_info.get("source_type", "")
        }

        if item["relation"] == "direct":
            direct_support.append(item)
        elif item["relation"] == "indirect":
            indirect_support.append(item)

    # Fallback to assessment items if DB claim_evidence was not pre-saved
    if not direct_support and not indirect_support:
        for d in assessment.get("direct_support", []):
            eid = d.get("event_id")
            ev_info = ev_events.get(eid, {})
            surl = ev_info.get("source_url", "")
            direct_support.append({
                "event_id": eid,
                "source_link": surl,
                "url_format_ok": bool(surl.startswith(("http://", "https://"))),
                "relevant_passage": d.get("passage_text"),
                "passage_start": d.get("passage_start"),
                "passage_end": d.get("passage_end"),
                "author": ev_info.get("author", "unknown"),
                "date": ev_info.get("ts", ""),
                "relation": "direct",
                "source_group": d.get("source_group", ""),
                "title": ev_info.get("title", ""),
                "source_type": ev_info.get("source_type", "")
            })
        for ind in assessment.get("indirect_support", []):
            eid = ind.get("event_id")
            ev_info = ev_events.get(eid, {})
            surl = ev_info.get("source_url", "")
            indirect_support.append({
                "event_id": eid,
                "source_link": surl,
                "url_format_ok": bool(surl.startswith(("http://", "https://"))),
                "relevant_passage": ind.get("passage_text"),
                "passage_start": ind.get("passage_start"),
                "passage_end": ind.get("passage_end"),
                "author": ev_info.get("author", "unknown"),
                "date": ev_info.get("ts", ""),
                "relation": "indirect",
                "source_group": ind.get("source_group", ""),
                "title": ev_info.get("title", ""),
                "source_type": ev_info.get("source_type", "")
            })

    needs_review = bool(
        dec.get("review_status") == "pending_review" or
        assessment["label"] in ("weak", "insufficient", "contradicted") or
        dec.get("confidence", 1.0) < 0.90
    )

    return {
        "decision": {
            "decision_id": dec_id,
            "title": dec.get("title", ""),
            "rationale": dec.get("rationale", ""),
            "made_by": dec.get("made_by", ""),
            "made_at": dec.get("made_at", ""),
            "repo": dec.get("repo", "")
        },
        "decision_id": dec_id,
        "title": dec.get("title", ""),
        "rationale": dec.get("rationale", ""),
        "made_by": dec.get("made_by", ""),
        "made_at": dec.get("made_at", ""),
        "lifecycle_state": dec.get("state", "proposed"),
        "state": dec.get("state", "proposed"),
        "needs_review": needs_review,
        "evidence_assessment": {
            "label": assessment["label"]
        },
        "direct_support": direct_support,
        "indirect_support": indirect_support,
        "missing_corroboration": assessment.get("missing_corroboration", []),
        "conflicting_evidence": assessment.get("conflicting_evidence", [])
    }


class ExplanationGenerator:
    def __init__(self, db: Database):
        self.db = db

    def explain_artifact(self, canonical_path: str) -> Dict[str, Any]:
        """
        Generates Step 3.3 evidence-grounded explanation for why an artifact looks the way it does.
        Includes per-decision evidence breakdown, passage citations, sentence support verification,
        and abstention when evidence is insufficient.
        """
        chain = self.db.query_decision_chain_for_artifact(canonical_path)

        if not chain:
            return {
                "artifact": canonical_path,
                "status": "not_found",
                "explanation": f"No recorded architectural decisions found for artifact '{canonical_path}' in project history.",
                "citations": [],
                "chain": [],
                "statements": [],
                "unsupported_sentences": [],
                "claim_support_rate": 0.0
            }

        decision_blocks: List[Dict[str, Any]] = []
        citations: List[Dict[str, Any]] = []

        for idx, dec in enumerate(chain, 1):
            block = build_decision_evidence_block(self.db, dec)
            block["step_number"] = idx
            state_badge = f"[{dec['state'].upper()}]"
            block["summary"] = f"{state_badge} {dec['title']} (by {dec.get('made_by')} on {dec.get('made_at', '')[:10]})"
            decision_blocks.append(block)

            for d_item in block["direct_support"]:
                citations.append({
                    "source_type": d_item["source_type"],
                    "source_id": d_item["event_id"],
                    "source_url": d_item["source_link"],
                    "title": d_item["title"],
                    "author": d_item["author"],
                    "timestamp": d_item["date"],
                    "passage": d_item["relevant_passage"],
                    "relation": "direct"
                })

        # Latest active decision
        active_decisions = [d for d in chain if d["state"] == "accepted"]
        current_active = active_decisions[-1] if active_decisions else chain[-1]
        active_block = [b for b in decision_blocks if b["decision"]["decision_id"] == current_active["decision_id"]][0]

        # Step 3.2 Abstention rule: abstain if evidence assessment is insufficient and no stronger source exists
        active_assessment = active_block["evidence_assessment"]["label"]
        has_stronger = any(b["evidence_assessment"]["label"] in ("strong", "moderate", "weak") for b in decision_blocks)

        if active_assessment == "insufficient" and not has_stronger:
            msg = f"Insufficient evidence recorded to explain design decisions governing artifact '{canonical_path}'."
            return {
                "artifact": canonical_path,
                "status": "insufficient_evidence",
                "message": msg,
                "explanation": msg,
                "decision": active_block["decision"],
                "current_decision": current_active["title"],
                "current_state": current_active["state"],
                "lifecycle_state": current_active["state"],
                "needs_review": active_block["needs_review"],
                "evidence_assessment": active_block["evidence_assessment"],
                "direct_support": active_block["direct_support"],
                "indirect_support": active_block["indirect_support"],
                "missing_corroboration": active_block["missing_corroboration"],
                "conflicting_evidence": active_block["conflicting_evidence"],
                "citations": citations,
                "chain": decision_blocks,
                "statements": [],
                "unsupported_sentences": [],
                "claim_support_rate": 0.0
            }

        # Synthesize answer text
        overall_text = f"Artifact '{canonical_path}' is governed primarily by accepted decision '{current_active['title']}', established by {current_active['made_by']} on {current_active['made_at'][:10]}.\n\n"
        overall_text += f"Key Rationale: {current_active['rationale']}\n\n"
        if len(chain) > 1:
            overall_text += f"Evolutionary History: This artifact progressed through {len(chain)} recorded decision milestones, including prior iterations or superseded proposals."

        # Collect all evidence items from active decision for sentence support checking
        all_active_evidence = active_block["direct_support"] + active_block["indirect_support"]
        statements, unsupported, support_rate = verify_sentence_support(overall_text, all_active_evidence)

        return {
            "artifact": canonical_path,
            "status": "grounded",
            "decision": active_block["decision"],
            "current_decision": current_active["title"],
            "current_state": current_active["state"],
            "lifecycle_state": current_active["state"],
            "needs_review": active_block["needs_review"],
            "evidence_assessment": active_block["evidence_assessment"],
            "direct_support": active_block["direct_support"],
            "indirect_support": active_block["indirect_support"],
            "missing_corroboration": active_block["missing_corroboration"],
            "conflicting_evidence": active_block["conflicting_evidence"],
            "explanation": overall_text,
            "statements": statements,
            "unsupported_sentences": unsupported,
            "claim_support_rate": support_rate,
            "citations": citations,
            "chain": decision_blocks
        }

    def explain_decision(self, decision_id: str) -> Dict[str, Any]:
        """
        Explains a specific decision with Step 3.3 evidence payload structure.
        Abstains if evidence is insufficient.
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decisions WHERE decision_id = ?", (decision_id,))
            row = cursor.fetchone()
            if not row:
                return {
                    "decision_id": decision_id,
                    "status": "not_found",
                    "explanation": f"Decision '{decision_id}' not found in project history.",
                    "citations": [],
                    "statements": [],
                    "unsupported_sentences": [],
                    "claim_support_rate": 0.0
                }
            dec = dict(row)

        block = build_decision_evidence_block(self.db, dec)
        ea_label = block["evidence_assessment"]["label"]

        if ea_label == "insufficient":
            msg = f"Insufficient evidence recorded for decision '{dec.get('title')}' ({decision_id})."
            return {
                "decision": block["decision"],
                "decision_id": decision_id,
                "status": "insufficient_evidence",
                "message": msg,
                "explanation": msg,
                "current_decision": dec["title"],
                "current_state": dec["state"],
                "lifecycle_state": dec["state"],
                "needs_review": block["needs_review"],
                "evidence_assessment": block["evidence_assessment"],
                "direct_support": block["direct_support"],
                "indirect_support": block["indirect_support"],
                "missing_corroboration": block["missing_corroboration"],
                "conflicting_evidence": block["conflicting_evidence"],
                "citations": [],
                "statements": [],
                "unsupported_sentences": [],
                "claim_support_rate": 0.0
            }

        # Grounded explanation text
        explanation_text = f"Decision '{dec['title']}' ({dec['state']}) established by {dec.get('made_by')} on {dec.get('made_at', '')[:10]}.\n"
        explanation_text += f"Key Rationale: {dec.get('rationale', '')}"

        all_evidence = block["direct_support"] + block["indirect_support"]
        statements, unsupported, support_rate = verify_sentence_support(explanation_text, all_evidence)

        citations = [
            {
                "source_type": it.get("source_type"),
                "source_id": it.get("event_id"),
                "source_url": it.get("source_link"),
                "title": it.get("title"),
                "author": it.get("author"),
                "timestamp": it.get("date"),
                "passage": it.get("relevant_passage"),
                "relation": it.get("relation")
            }
            for it in block["direct_support"]
        ]

        return {
            "decision": block["decision"],
            "decision_id": decision_id,
            "status": "grounded",
            "current_decision": dec["title"],
            "current_state": dec["state"],
            "lifecycle_state": dec["state"],
            "needs_review": block["needs_review"],
            "evidence_assessment": block["evidence_assessment"],
            "direct_support": block["direct_support"],
            "indirect_support": block["indirect_support"],
            "missing_corroboration": block["missing_corroboration"],
            "conflicting_evidence": block["conflicting_evidence"],
            "explanation": explanation_text,
            "statements": statements,
            "unsupported_sentences": unsupported,
            "claim_support_rate": support_rate,
            "citations": citations
        }
