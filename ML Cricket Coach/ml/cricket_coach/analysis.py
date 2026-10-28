"""Recent-form summaries and supported dismissal-pattern review candidates."""
from pathlib import Path
import numpy as np
import pandas as pd
from .config import (CONTEXT, FEATURES, LABELS, LIMITATIONS, MIN_PATTERN_ROWS,
                     MIN_PATTERN_MATCHES, MIN_PATTERN_FAMILIES, MIN_PATTERN_SHARE)
from .data import parse_match_date
from .io_utils import read_json
from .label_rules import rubric_label
from .predictor import get_assessor, validate_scoring


PATTERN_FIELDS = [
    ("dismissal_type",), ("bowling_length",), ("bowling_line",), ("shot_type",), ("bowler_type",),
    ("bowling_length", "bowling_line"), ("bowling_line", "shot_type"),
    ("bowling_length", "shot_type"), ("bowling_length", "bowler_type"),
    ("bowling_length", "bowling_line", "shot_type"),
]


def find_patterns(history, min_rows=MIN_PATTERN_ROWS, min_matches=MIN_PATTERN_MATCHES,
                  min_families=MIN_PATTERN_FAMILIES, min_share=MIN_PATTERN_SHARE):
    outs = history[history.out_status == "Out"].copy()
    total = len(outs)
    if total == 0: return []
    results = []
    for fields in PATTERN_FIELDS:
        valid = outs.copy()
        for field in fields:
            valid = valid[~valid[field].isin(["NA", "Unknown", "", "Other", "Not Out"])]
        for values, part in valid.groupby(list(fields), sort=True, dropna=False):
            if not isinstance(values, tuple): values = (values,)
            count, matches, families = len(part), part.match_id.nunique(), part.split_group.nunique()
            share = count / total
            if count < min_rows or matches < min_matches or families < min_families or share < min_share:
                continue
            condition = dict(zip(fields, map(str, values)))
            results.append({
                "pattern": condition, "dismissal_count": count, "all_recorded_dismissals": total,
                "share_of_recorded_dismissals": round(share, 4), "distinct_matches": matches,
                "distinct_related_match_groups": families,
                "poor_performance_share_within_pattern": round(float((part.performance_label == "Poor").mean()), 4),
                "evidence_record_ids": part.record_id.tolist(),
                "interpretation": "Recurring recorded dismissal pattern to review; not a per-delivery dismissal probability or confirmed technical fault.",
            })
    return sorted(results, key=lambda p: (-len(p["pattern"]), -p["dismissal_count"], str(p["pattern"])))


def make_recommendations(patterns, limit=4):
    rules = read_json(Path(__file__).with_name("coaching_rules.json"))
    recommendations = []
    for rule in rules:
        matching = [p for p in patterns if all(
            key in p["pattern"] and p["pattern"][key] in values
            for key, values in rule["when"].items())]
        if not matching: continue
        # Prefer the most specific supported evidence for this one suggestion.
        evidence = matching[0]
        recommendations.append({"id": rule["id"], "title": rule["title"],
                                "tip": rule["tip"], "practice_drill": rule["drill"],
                                "evidence": evidence, "method": "Evidence-linked rule catalogue; not learned coaching text"})
    return sorted(recommendations, key=lambda r: (-r["evidence"]["dismissal_count"], r["id"]))[:limit]


def _as_of_date(value=None):
    try:
        stamp = pd.Timestamp(value) if value else pd.Timestamp.now(tz="Asia/Colombo")
        if stamp.tzinfo is not None: stamp = stamp.tz_convert("Asia/Colombo").tz_localize(None)
        return stamp.normalize()
    except (ValueError, TypeError): raise ValueError("Use an as-of date in YYYY-MM-DD format.") from None


def analyze_history(history, player_id, match_format, as_of=None, recent_window=5, player_name=None):
    """Accept normalized innings records from the workbook now, or a database later."""
    if not isinstance(recent_window, int) or not 3 <= recent_window <= 50:
        raise ValueError("recent_window must be a whole number from 3 to 50.")
    fmt = validate_scoring(0, 0, match_format)["match_format"]
    all_rows = pd.DataFrame(history).copy()
    required = ["player_id", "match_id", "match_date", "innings_number", "runs", "balls_faced",
                "match_format", "out_status", "dismissal_type"] + CONTEXT
    missing = [c for c in required if c not in all_rows]
    if missing: raise ValueError(f"History is missing fields: {missing}")
    part = all_rows[(all_rows.player_id.astype(str) == str(player_id)) & (all_rows.match_format == fmt)].copy()
    if part.empty: raise ValueError(f"No {fmt} innings found for player {player_id}.")
    part["match_id"] = part.match_id.astype(str)
    if not set(part.out_status).issubset(["Out", "Not Out"]): raise ValueError("Invalid out_status in player history.")
    invalid_status = (part.out_status == "Not Out") != (part.dismissal_type == "Not Out")
    if invalid_status.any(): raise ValueError("History has inconsistent dismissal status.")
    if "record_id" not in part: part["record_id"] = [f"history_{i}" for i in range(len(part))]
    if "split_group" not in part: part["split_group"] = part.match_id.astype(str)
    if part.duplicated(["player_id", "match_id", "innings_number"]).any():
        raise ValueError("History contains duplicate player-match-innings records.")
    for field in CONTEXT:
        part[field] = part[field].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
    not_applicable = (part.out_status == "Not Out") | (part.dismissal_type == "Run Out")
    part.loc[not_applicable, CONTEXT] = "NA"
    numeric = [validate_scoring(r.runs, r.balls_faced, fmt) for r in part.itertuples()]
    part["runs"] = [v["runs"] for v in numeric]
    part["balls_faced"] = [v["balls_faced"] for v in numeric]
    part["strike_rate"] = [v["strike_rate"] for v in numeric]
    if "performance_label" not in part:
        part["performance_label"] = [rubric_label(v["runs"], v["balls_faced"], fmt) for v in numeric]
    if not set(part.performance_label).issubset(LABELS): raise ValueError("History has invalid performance labels.")
    part["match_date"] = part.match_date.map(parse_match_date)
    cutoff = _as_of_date(as_of)
    invalid_dates = int(part.match_date.isna().sum())
    future_rows = int((part.match_date > cutoff).sum())
    part = part[part.match_date.notna() & (part.match_date <= cutoff)].copy()
    if part.empty: raise ValueError("No dated innings remain on or before the as-of date.")
    part = part.sort_values(["match_date", "match_id", "innings_number"], kind="stable")
    recent = part.tail(recent_window).copy()
    assessor = get_assessor()
    recent["model_label"] = assessor.pipeline.predict(recent[FEATURES])
    counts = recent.performance_label.value_counts().reindex(LABELS, fill_value=0)
    enough = len(recent) == recent_window
    largest = int(counts.max())
    # This is an explicit descriptive majority rule, not a trained form target.
    summary_label = counts.idxmax() if largest > len(recent) / 2 else "Mixed"
    recent_balls = int(recent.balls_faced.sum())
    patterns = find_patterns(part)
    recommendations = make_recommendations(patterns)
    date_warning = "Chronology uses stored dates; verify possible day/month errors before relying on recent-form conclusions."
    result = {
        "player_id": str(player_id), "player_name": player_name or str(player_id), "match_format": fmt,
        "as_of": cutoff.strftime("%Y-%m-%d"), "eligible_history_innings": len(part),
        "excluded_invalid_date_rows": invalid_dates, "excluded_future_date_rows": future_rows,
        "date_warning": date_warning,
        "current_form": {
            "method": f"Descriptive majority of existing performance labels across the latest {recent_window} completed innings in this format",
            "requested_window": recent_window, "available_in_window": len(recent),
            "status": "Available" if enough else "Insufficient history",
            "summary_label": summary_label if enough else None,
            "label_counts": counts.to_dict(), "mean_runs": round(float(recent.runs.mean()), 2),
            "weighted_strike_rate": round(100.0 * recent.runs.sum() / recent_balls, 2) if recent_balls else None,
            "runs_sample_std": round(float(recent.runs.std(ddof=1)), 2) if len(recent) > 1 else None,
            "model_label_counts": recent.model_label.value_counts().to_dict(),
            "note": "The descriptive form summary and model labels are separate. Neither is an independently validated coach form assessment.",
        },
        "recent_innings": [{"record_id": r.record_id, "match_id": str(r.match_id),
                            "match_date": r.match_date.strftime("%Y-%m-%d"), "innings_number": int(r.innings_number),
                            "runs": int(r.runs), "balls_faced": int(r.balls_faced),
                            "strike_rate": round(float(r.strike_rate), 2),
                            "performance_label": r.performance_label, "model_label": r.model_label}
                           for r in recent.itertuples()],
        "pattern_scope": "All eligible past innings for this player and format, not only the recent form window.",
        "pattern_thresholds": {"min_rows": MIN_PATTERN_ROWS, "min_matches": MIN_PATTERN_MATCHES,
                               "min_related_match_groups": MIN_PATTERN_FAMILIES, "min_share_of_dismissals": MIN_PATTERN_SHARE},
        "weakness_review_candidates": patterns[:10], "recommendations": recommendations,
        "evidence_status": "Supported recurring patterns found" if patterns else "Insufficient evidence for recurring-pattern claims",
        "limitations": LIMITATIONS,
    }
    if not recommendations:
        result["next_action"] = "Record more verified innings and dismissal context; no personalized technical drill is inferred without supported evidence."
    return result
