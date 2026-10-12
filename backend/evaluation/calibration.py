"""
Confidence Quality and Calibration Module (Step 4.7)
Computes reliability diagram bins, Expected Calibration Error (ECE),
and accuracy by evidence assessment tier for human-labelled decisions.
"""
from typing import Dict, Any, List, Optional, Tuple


def compute_calibration(
    labelled_items: List[Dict[str, Any]],
    num_bins: int = 5,
    min_labels_for_ece: int = 100
) -> Dict[str, Any]:
    """
    Computes calibration metrics for labelled decision items.

    Each item in labelled_items should have:
      - 'confidence': float in [0.0, 1.0]
      - 'correct': bool (True or False), or None
      - Optional 'evidence_assessment': str ('strong', 'moderate', 'weak', 'unsupported')

    Requirements per Step 4.7:
      - Compute accuracy by heuristic-score bucket (5 equal-width bins).
      - Compute accuracy by evidence_assessment label.
      - Report whether higher scores are really more accurate (monotonicity check).
      - Compute reliability table and ECE ONLY IF there are >= 100 labelled predictions;
        otherwise report 'not enough labels for calibration' and 'not measured'.
    """
    # 1. Filter items with valid human boolean labels
    valid_items = [
        it for it in labelled_items
        if it.get("correct") is not None and isinstance(it.get("correct"), (bool, int))
    ]
    total_valid = len(valid_items)

    # 2. Compute accuracy by evidence_assessment label (regardless of sample size)
    assessment_groups: Dict[str, Dict[str, Any]] = {}
    for it in valid_items:
        tier = it.get("evidence_assessment") or "unspecified"
        conf = float(it.get("confidence", 0.0))
        is_corr = bool(it.get("correct"))

        if tier not in assessment_groups:
            assessment_groups[tier] = {
                "total": 0,
                "correct": 0,
                "confidence_sum": 0.0
            }
        assessment_groups[tier]["total"] += 1
        if is_corr:
            assessment_groups[tier]["correct"] += 1
        assessment_groups[tier]["confidence_sum"] += conf

    assessment_accuracy: Dict[str, Dict[str, Any]] = {}
    for tier, data in assessment_groups.items():
        tot = data["total"]
        corr = data["correct"]
        acc = round((corr / tot) * 100, 1) if tot > 0 else 0.0
        avg_c = round((data["confidence_sum"] / tot), 3) if tot > 0 else 0.0
        assessment_accuracy[tier] = {
            "total": tot,
            "correct": corr,
            "accuracy_pct": acc,
            "avg_confidence": avg_c
        }

    # 3. Guard against small sample sizes per Step 4.7 (>= 100 labels required)
    if total_valid < min_labels_for_ece:
        return {
            "status": "not measured",
            "reason": "not enough labels for calibration",
            "labeled_count": total_valid,
            "min_required": min_labels_for_ece,
            "calibrated": False,
            "ece": None,
            "ece_pct": None,
            "reliability_table": [],
            "assessment_accuracy": assessment_accuracy,
            "monotonic_confidence": None,
            "higher_scores_more_accurate": None
        }

    # 4. Construct Bins (Equal-width [0.0, 1.0])
    bin_width = 1.0 / num_bins
    bins: List[Dict[str, Any]] = []
    for b in range(num_bins):
        low = round(b * bin_width, 4)
        high = round((b + 1) * bin_width, 4)
        bins.append({
            "bin_index": b,
            "range": f"[{low:.1f}, {high:.1f})" if b < num_bins - 1 else f"[{low:.1f}, {high:.1f}]",
            "low": low,
            "high": high,
            "items": []
        })

    for it in valid_items:
        conf = max(0.0, min(1.0, float(it.get("confidence", 0.0))))
        assigned = False
        for b_idx, b in enumerate(bins):
            if b_idx == num_bins - 1:
                # Include upper boundary in last bin
                if b["low"] <= conf <= b["high"]:
                    b["items"].append(it)
                    assigned = True
                    break
            else:
                if b["low"] <= conf < b["high"]:
                    b["items"].append(it)
                    assigned = True
                    break
        if not assigned:
            bins[-1]["items"].append(it)

    # 5. Compute Reliability Table and ECE
    reliability_table = []
    ece_weighted_sum = 0.0
    non_empty_accuracies = []

    for b in bins:
        count = len(b["items"])
        if count == 0:
            reliability_table.append({
                "bin_index": b["bin_index"],
                "range": b["range"],
                "count": 0,
                "accuracy": 0.0,
                "avg_confidence": round((b["low"] + b["high"]) / 2, 3),
                "calibration_error": 0.0
            })
            continue

        corr_count = sum(1 for item in b["items"] if bool(item.get("correct")))
        acc = corr_count / count
        avg_conf = sum(float(item.get("confidence", 0.0)) for item in b["items"]) / count
        cal_err = abs(acc - avg_conf)

        ece_weighted_sum += (count / total_valid) * cal_err
        non_empty_accuracies.append((avg_conf, acc))

        reliability_table.append({
            "bin_index": b["bin_index"],
            "range": b["range"],
            "count": count,
            "accuracy": round(acc, 4),
            "avg_confidence": round(avg_conf, 4),
            "calibration_error": round(cal_err, 4)
        })

    ece = round(ece_weighted_sum, 4)
    ece_pct = round(ece * 100, 2)

    # 6. Monotonicity Analysis: Check if higher confidence corresponds to higher accuracy
    monotonic = True
    if len(non_empty_accuracies) >= 2:
        for i in range(len(non_empty_accuracies) - 1):
            if non_empty_accuracies[i + 1][1] < non_empty_accuracies[i][1]:
                monotonic = False
                break
    else:
        monotonic = False

    is_calibrated = (ece <= 0.10) and monotonic

    return {
        "status": "measured",
        "reason": None,
        "labeled_count": total_valid,
        "min_required": min_labels_for_ece,
        "calibrated": is_calibrated,
        "ece": ece,
        "ece_pct": ece_pct,
        "reliability_table": reliability_table,
        "assessment_accuracy": assessment_accuracy,
        "monotonic_confidence": monotonic,
        "higher_scores_more_accurate": "yes" if monotonic else "no"
    }


def format_calibration_markdown(result: Dict[str, Any]) -> str:
    """Formats calibration evaluation results into clean Markdown."""
    lines = []
    lines.append("### Confidence Quality and Calibration (Step 4.7)")
    lines.append("")

    if result.get("status") != "measured":
        cnt = result.get("labeled_count", 0)
        req = result.get("min_required", 100)
        lines.append(f"> **Status**: *not measured* ({result.get('reason', 'not enough labels for calibration')}).")
        lines.append(f"> Labelled predictions: **{cnt}** / {req} required for calibration. Heuristic scores remain explicitly marked as **uncalibrated** in UI and API.")
        lines.append("")
        if result.get("assessment_accuracy"):
            lines.append("#### Accuracy by Evidence Assessment Tier (Preliminary):")
            lines.append("")
            lines.append("| Evidence Tier | Labelled Samples | Correct | Accuracy | Avg Confidence |")
            lines.append("|---|:---:|:---:|:---:|:---:|")
            for tier, d in result["assessment_accuracy"].items():
                lines.append(f"| `{tier}` | {d['total']} | {d['correct']} | {d['accuracy_pct']}% | {d['avg_confidence']:.2f} |")
            lines.append("")
        return "\n".join(lines)

    lines.append(f"- **Total Labelled Predictions**: {result.get('labeled_count')}")
    lines.append(f"- **Expected Calibration Error (ECE)**: **{result.get('ece_pct')}%** (ECE = {result.get('ece')})")
    lines.append(f"- **Monotonic Confidence**: {result.get('higher_scores_more_accurate')} (Higher confidence implies higher accuracy: {result.get('higher_scores_more_accurate')})")
    lines.append(f"- **Calibrated Status**: {'Calibrated' if result.get('calibrated') else 'Uncalibrated'}")
    lines.append("")
    lines.append("#### Reliability Table (5 Equal-Width Bins):")
    lines.append("")
    lines.append("| Bin Range | Samples | Avg Confidence | Empirical Accuracy | Calibration Error |")
    lines.append("|---|:---:|:---:|:---:|:---:|")
    for b in result.get("reliability_table", []):
        lines.append(f"| `{b['range']}` | {b['count']} | {b['avg_confidence']:.3f} | {b['accuracy']:.3f} | {b['calibration_error']:.3f} |")
    lines.append("")

    if result.get("assessment_accuracy"):
        lines.append("#### Accuracy by Evidence Assessment Tier:")
        lines.append("")
        lines.append("| Evidence Tier | Labelled Samples | Correct | Accuracy | Avg Confidence |")
        lines.append("|---|:---:|:---:|:---:|:---:|")
        for tier, d in result["assessment_accuracy"].items():
            lines.append(f"| `{tier}` | {d['total']} | {d['correct']} | {d['accuracy_pct']}% | {d['avg_confidence']:.2f} |")
        lines.append("")

    return "\n".join(lines)
