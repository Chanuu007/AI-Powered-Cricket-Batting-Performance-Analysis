"""Example: python ml/04_analyze_player.py --player P001 --format T20 --as-of 2026-10-26"""
import argparse
import json
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from cricket_coach.api import analyze_player
from cricket_coach.config import DATASET, REPORTS, FIGURES
from cricket_coach.data import load_dataset
from cricket_coach.io_utils import write_json, save_figure


def save_player_report(result):
    REPORTS.mkdir(parents=True, exist_ok=True); FIGURES.mkdir(parents=True, exist_ok=True)
    identifier = re.sub(r"[^A-Za-z0-9_-]", "_", result["player_id"])
    stem = f"player_{identifier}_{result['match_format']}"
    write_json(REPORTS / f"{stem}.json", result)
    form = result["current_form"]
    lines = [f"# {result['player_name']} — {result['match_format']} analysis", "",
             f"As of: {result['as_of']}. Eligible recorded innings: {result['eligible_history_innings']}.",
             f"Excluded future-dated rows: {result['excluded_future_date_rows']}. Invalid-date rows: {result['excluded_invalid_date_rows']}.",
             result["date_warning"], "", "## Recent form", "",
             f"Status: {form['status']}. Summary: {form['summary_label'] or 'Not assigned'}.",
             form["method"], f"Label counts: {form['label_counts']}.",
             f"Mean runs: {form['mean_runs']}. Weighted strike rate: {form['weighted_strike_rate']}.",
             f"Model label counts: {form['model_label_counts']}.", "", "## Areas to review", "",
             result["evidence_status"], result["pattern_scope"]]
    for p in result["weakness_review_candidates"][:5]:
        description = ", ".join(f"{k.replace('_',' ')} = {v}" for k, v in p["pattern"].items())
        lines.append(f"- {description}: {p['dismissal_count']} of {p['all_recorded_dismissals']} recorded dismissals; {p['distinct_matches']} match IDs and {p['distinct_related_match_groups']} related-match groups.")
    lines += ["", "## Evidence-linked practice suggestions", ""]
    for rec in result["recommendations"]:
        lines += [f"### {rec['title']}", "", rec["tip"], f"Practice: {rec['practice_drill']}",
                  f"Supporting record IDs: {', '.join(rec['evidence']['evidence_record_ids'])}.", ""]
    if not result["recommendations"]: lines.append(result.get("next_action", "No supported personalized suggestion."))
    lines += ["", "## Interpretation", ""] + [f"- {x}" for x in result["limitations"]]
    (REPORTS / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    recent = result["recent_innings"]
    x = list(range(len(recent)))
    labels = [r["match_date"] for r in recent]
    fig, axes = plt.subplots(2, 1, figsize=(8, 6.5), sharex=True)
    axes[0].bar(x, [r["runs"] for r in recent], color="#305E83"); axes[0].set_ylabel("Runs")
    axes[1].plot(x, [r["strike_rate"] for r in recent], marker="o", color="#4B826E")
    axes[1].set_ylabel("Strike rate"); axes[1].set_xticks(x, labels, rotation=20)
    fig.suptitle(f"{result['player_name']}: recent recorded {result['match_format']} innings")
    fig.tight_layout(); save_figure(fig, FIGURES / f"{stem}.png"); plt.close(fig)
    return REPORTS / f"{stem}.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assess recent form and find supported recurring dismissal patterns.")
    parser.add_argument("--player", help="Player ID, for example P001")
    parser.add_argument("--format", dest="match_format", choices=["T20", "ODI", "Test"])
    parser.add_argument("--as-of", help="YYYY-MM-DD; default is today's date in Sri Lanka")
    parser.add_argument("--recent-window", type=int, default=5)
    parser.add_argument("--dataset", default=DATASET)
    parser.add_argument("--list-players", action="store_true")
    args = parser.parse_args()
    if args.list_players:
        frame, names, _, _ = load_dataset(args.dataset)
        for pid in sorted(frame.player_id.unique()):
            counts = frame[frame.player_id == pid].match_format.value_counts().to_dict()
            print(f"{pid}: {names.get(pid, pid)} — {counts}")
    else:
        if not args.player or not args.match_format: parser.error("Provide --player and --format, or use --list-players.")
        result = analyze_player(args.player, args.match_format, dataset=args.dataset,
                                as_of=args.as_of, recent_window=args.recent_window)
        destination = save_player_report(result)
        print(json.dumps({"player": result["player_name"], "format": result["match_format"],
                          "recent_form": result["current_form"], "patterns": len(result["weakness_review_candidates"]),
                          "recommendations": len(result["recommendations"])}, indent=2))
        print(f"Full report: {destination}")
