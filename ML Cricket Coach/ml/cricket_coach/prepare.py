"""Step 1: validate and document one combined input dataset."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from .config import DATASET, PROCESSED, REPORTS, FIGURES, LABELS
from .data import load_dataset
from .io_utils import file_hash, write_json, read_json, save_figure
from .label_rules import RUBRIC_DESCRIPTION


def prepare_dataset(dataset=DATASET):
    frame, players, meta, issues = load_dataset(dataset)
    for directory in (PROCESSED, REPORTS, FIGURES): directory.mkdir(parents=True, exist_ok=True)
    output = PROCESSED / "innings.csv"
    frame.to_csv(output, index=False, date_format="%Y-%m-%d")
    meta["prepared_data_sha256"] = file_hash(output)
    meta["processing_version"] = "1.0.0"
    meta["rubric"] = RUBRIC_DESCRIPTION
    meta["quality_issue_count"] = len(issues)
    write_json(PROCESSED / "manifest.json", meta)
    write_json(PROCESSED / "players.json", players)
    issues.to_csv(REPORTS / "data_quality_issues.csv", index=False)
    counts = frame.performance_label.value_counts().reindex(LABELS, fill_value=0)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(counts.index, counts.values, color=["#C76B58", "#C7A24B", "#4B826E"])
    ax.bar_label(bars, padding=4)
    ax.set(title="Existing rule-based innings labels", ylabel="Number of innings")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); save_figure(fig, FIGURES / "label_distribution.png"); plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, fmt in zip(axes, ["T20", "ODI", "Test"]):
        part = frame[frame.match_format == fmt]
        ax.scatter(part.runs, part.strike_rate, alpha=0.45, s=14, color="#305E83")
        ax.set(title=fmt, xlabel="Runs", ylabel="Strike rate")
    fig.suptitle("Completed innings in the combined dataset")
    fig.tight_layout(); save_figure(fig, FIGURES / "runs_and_strike_rate.png"); plt.close(fig)
    print(f"Prepared {len(frame)} innings, {meta['matches']} match IDs, {meta['split_groups']} related-match groups.")
    print(f"Quality observations: {len(issues)}. Read ml/outputs/reports/data_quality_issues.csv.")
    print("The source workbook was not edited. All rows remain together in processed/innings.csv.")
    return meta


def load_prepared():
    manifest_path = PROCESSED / "manifest.json"
    csv_path = PROCESSED / "innings.csv"
    if not manifest_path.is_file() or not csv_path.is_file():
        raise FileNotFoundError("Run python ml/01_prepare_data.py first.")
    meta = read_json(manifest_path)
    if file_hash(csv_path) != meta["prepared_data_sha256"]:
        raise ValueError("Processed data changed after preparation. Run step 1 again; do not edit the CSV manually.")
    frame = pd.read_csv(csv_path, keep_default_na=False,
                        dtype={"player_id": str, "match_id": str, "split_group": str})
    frame["match_date"] = pd.to_datetime(frame["match_date"], format="%Y-%m-%d", errors="coerce")
    if len(frame) != meta["rows"]: raise ValueError("Prepared row count differs from manifest.")
    return frame, meta
