"""
make_copilot_sheet.py - Generate printable evaluation sheet for Baseline D (GitHub Copilot).

Generates results/copilot_sheet.md listing 26 positive and 10 sampled negative questions
from WhyBench test_v2 (seed 1234), with full repository context streams and copy-pasteable
prompts for manual evaluation in GitHub Copilot.
"""
import argparse
import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.ingestion.sanitizer import sanitize_text

REPO_DIR_MAP = {
    "cli/cli": "cli-cli",
    "cloud-hypervisor/cloud-hypervisor": "cloud-hypervisor",
    "acme-ecommerce/payment-core": "payment-core",
}


def load_events(repo_dir: str) -> List[Dict[str, Any]]:
    path = PROJECT_ROOT / "backend" / "evaluation" / "whybench" / "data" / repo_dir / "events.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_event_stream(events: List[Dict[str, Any]]) -> str:
    lines = []
    for ev in events:
        s_title = sanitize_text(ev.get("title") or "")
        s_body = sanitize_text(ev.get("body") or "")
        st = ev.get("source_type") or "event"
        sid = ev.get("source_id") or ""
        lines.append(f"[{ev['event_id']}] ({st}:{sid}) {s_title}: {s_body[:400]}")
    return "\n".join(lines)


def generate_copilot_sheet(
    questions_path: Path,
    output_path: Path,
    seed: int = 1234,
    split: str = "test_v2"
) -> None:
    with open(questions_path, "r", encoding="utf-8") as f:
        all_qs = json.load(f)

    split_qs = [q for q in all_qs if q.get("split") == split]
    positives = [q for q in split_qs if q.get("expected_state") != "none"]
    negatives = [q for q in split_qs if q.get("expected_state") == "none"]

    rng = random.Random(seed)
    sampled_negatives = rng.sample(negatives, min(10, len(negatives)))

    # Load events for all repos
    events_by_repo = {}
    for repo, rdir in REPO_DIR_MAP.items():
        events_by_repo[repo] = load_events(rdir)

    selected_questions = positives + sampled_negatives

    lines = [
        "# Baseline D: GitHub Copilot Manual Evaluation Trial Sheet",
        "",
        "> **Protocol:** This sheet defines the manual trial protocol for evaluating GitHub Copilot on WhyBench-Synth (`test_v2`).",
        "> Each trial provides the repository's recorded event stream and an architectural question to GitHub Copilot.",
        "> Results are recorded in `backend/evaluation/manual_copilot_results.csv` with binary flags (`1` or `0`).",
        "",
        "## Evaluation Protocol & Scoring Instructions",
        "",
        "1. Open GitHub Copilot Chat (VS Code or github.com).",
        "2. Copy the **Prompt** and **Event Stream** for each trial below into Copilot.",
        "3. Evaluate Copilot's response against the ground truth criteria:",
        "   - **`answer_correct`**: `1` if Copilot correctly identifies the decision state and rationale (for positive questions) or correctly states that no such decision was made (for negative questions); `0` otherwise.",
        "   - **`answer_has_invented_reason`**: `1` if Copilot invents facts, rationales, benchmarks, or citations not grounded in the provided event stream; `0` otherwise.",
        "   - **`cited_real_source`**: `1` if Copilot specifically and accurately cites an event ID, PR, issue, or ADR from the event stream; `0` otherwise.",
        "4. Append the result to `backend/evaluation/manual_copilot_results.csv`.",
        "",
        "## Summary of Trial Questions",
        "",
        f"- **Dataset Split:** `{split}`",
        f"- **Total Trials:** {len(selected_questions)} ({len(positives)} positive questions + {len(sampled_negatives)} sampled negative questions)",
        f"- **Negative Sampling Random Seed:** `{seed}`",
        "",
        "| # | Question ID | Repository | Type | Expected State | Question Summary |",
        "|---|---|---|---|---|---|"
    ]

    for idx, q in enumerate(selected_questions, 1):
        qid = q.get("id") or q.get("question_id")
        repo = q.get("repo")
        is_pos = q.get("expected_state") != "none"
        q_type = "Positive (Decision)" if is_pos else "Negative (Unrecorded)"
        state = q.get("expected_state")
        q_text = (q.get("question") or "").replace("|", "\\|")
        lines.append(f"| {idx} | `{qid}` | `{repo}` | {q_type} | `{state}` | {q_text[:70]}... |")

    lines.extend([
        "",
        "---",
        "",
        "## CSV Results Template",
        "",
        "Copy and paste the header and question rows below into `backend/evaluation/manual_copilot_results.csv` when conducting the trials:",
        "",
        "```csv",
        "question_id,answer_correct,answer_has_invented_reason,cited_real_source,notes"
    ])

    for q in selected_questions:
        qid = q.get("id") or q.get("question_id")
        lines.append(f"{qid},,,,")

    lines.extend([
        "```",
        "",
        "---",
        "",
        "## Detailed Trial Prompts",
        ""
    ])

    for idx, q in enumerate(selected_questions, 1):
        qid = q.get("id") or q.get("question_id")
        repo = q.get("repo")
        is_pos = q.get("expected_state") != "none"
        q_type = "Positive (Recorded Decision)" if is_pos else "Negative (Unrecorded Topic)"
        state = q.get("expected_state")
        ev_ids = q.get("evidence_event_ids") or []
        summary = q.get("answer_summary") or "(None - unrecorded topic)"
        q_text = q.get("question") or ""

        repo_events = events_by_repo.get(repo, [])
        stream_text = format_event_stream(repo_events)

        lines.extend([
            f"### Trial {idx}: Question `{qid}`",
            "",
            f"- **Repository:** `{repo}`",
            f"- **Type:** {q_type}",
            f"- **Expected State:** `{state}`",
            f"- **Expected Evidence Events:** `{', '.join(ev_ids) if ev_ids else 'None'}`",
            f"- **Ground Truth Summary:** {summary}",
            "",
            "#### Copilot Prompt",
            "",
            "```text",
            f"You are analyzing architectural decisions for repository '{repo}'.",
            "Based strictly and only on the event stream below, answer the following architectural question.",
            "Do not invent facts or cite events not present in the stream.",
            "",
            f"Question: {q_text}",
            "",
            "Event Stream:",
            stream_text,
            "```",
            "",
            "---",
            ""
        ])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(lines) + "\n"
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"Generated {output_path} with {len(selected_questions)} trials.")


def main():
    parser = argparse.ArgumentParser(description="Generate Copilot evaluation sheet")
    parser.add_argument("--questions", default=str(PROJECT_ROOT / "backend/evaluation/whybench/questions.json"))
    parser.add_argument("--out", default=str(PROJECT_ROOT / "results/copilot_sheet.md"))
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--split", default="test_v2")
    args = parser.parse_args()

    generate_copilot_sheet(
        questions_path=Path(args.questions),
        output_path=Path(args.out),
        seed=args.seed,
        split=args.split
    )


if __name__ == "__main__":
    main()
