"""Step 3: evaluate the locked models and two honest baselines on held-out rows."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import joblib
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import (accuracy_score, precision_recall_fscore_support,
                             classification_report, confusion_matrix, ConfusionMatrixDisplay,
                             make_scorer, f1_score)
from .config import FEATURES, TARGET, LABELS, MODELS, REPORTS, FIGURES, PROCESSED
from .io_utils import read_json, write_json, file_hash, save_figure
from .label_rules import rubric_label
from .prepare import load_prepared


def metric_row(name, actual, predicted):
    precision, recall, f1, _ = precision_recall_fscore_support(
        actual, predicted, labels=LABELS, average="macro", zero_division=0)
    return {"model": name, "accuracy": accuracy_score(actual, predicted),
            "macro_precision": precision, "macro_recall": recall, "macro_f1": f1}


def evaluate_models():
    frame, prepared = load_prepared()
    meta_path = MODELS / "metadata.json"
    if not meta_path.is_file(): raise FileNotFoundError("Run python ml/02_train_models.py first.")
    meta = read_json(meta_path)
    if meta["prepared_data_sha256"] != prepared["prepared_data_sha256"]:
        raise ValueError("Training used a different processed dataset. Rerun steps 2 and 3.")
    split_path = PROCESSED / "split_assignments.csv"
    if file_hash(split_path) != meta["split_assignments_sha256"]:
        raise ValueError("Split assignments changed after training.")
    splits = pd.read_csv(split_path, dtype=str)
    test = frame[frame.record_id.isin(splits.loc[splits.partition == "test", "record_id"])].copy()
    train = frame[frame.record_id.isin(splits.loc[splits.partition == "train", "record_id"])].copy()
    if set(train.split_group) & set(test.split_group): raise AssertionError("Group leakage.")
    actual = test[TARGET]; rows = []
    prediction_table = test[["record_id", "player_id", "match_id", "match_format", TARGET]].copy()
    for name in meta["best_parameters"]:
        model_path = MODELS / f"{name}.joblib"
        if file_hash(model_path) != meta["all_model_sha256"][name]:
            raise ValueError(f"Saved model changed: {name}. Rerun training.")
        model = joblib.load(model_path)
        predicted = model.predict(test[FEATURES])
        rows.append(metric_row(name, actual, predicted)); prediction_table[name] = predicted
        report = classification_report(actual, predicted, labels=LABELS, output_dict=True, zero_division=0)
        write_json(REPORTS / f"{name}_classification_report.json", report)
        matrix = confusion_matrix(actual, predicted, labels=LABELS)
        pd.DataFrame(matrix, index=LABELS, columns=LABELS).to_csv(REPORTS / f"{name}_confusion_matrix.csv")
        fig, ax = plt.subplots(figsize=(6, 5))
        ConfusionMatrixDisplay(matrix, display_labels=LABELS).plot(ax=ax, cmap="Blues", colorbar=False)
        ax.set_title(f"{name.replace('_', ' ').title()}\nAgreement with rule-based labels")
        fig.tight_layout(); save_figure(fig, FIGURES / f"{name}_confusion_matrix.png"); plt.close(fig)
    majority = train[TARGET].value_counts().idxmax()
    rows.append(metric_row("majority_baseline", actual, [majority] * len(test)))
    rubric = test.apply(lambda r: rubric_label(r.runs, r.balls_faced, r.match_format), axis=1)
    rows.append(metric_row("exact_rubric_baseline", actual, rubric))
    prediction_table["exact_rubric_baseline"] = rubric
    comparison = pd.DataFrame(rows)
    comparison.to_csv(REPORTS / "model_comparison.csv", index=False)
    prediction_table.to_csv(REPORTS / "test_predictions.csv", index=False)
    selected = joblib.load(MODELS / "selected_model.joblib")
    # These values describe dependence on scoring inputs, not causes of dismissals.
    scorer = make_scorer(f1_score, average="macro", labels=LABELS, zero_division=0, pos_label=None)
    importance = permutation_importance(selected, test[FEATURES], actual, scoring=scorer,
                                       n_repeats=10, random_state=42, n_jobs=1)
    imp = pd.DataFrame({"feature": FEATURES, "mean_f1_drop": importance.importances_mean,
                        "std_f1_drop": importance.importances_std}).sort_values("mean_f1_drop", ascending=False)
    imp.to_csv(REPORTS / "selected_model_feature_importance.csv", index=False)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    bars = ax.bar(comparison.model.str.replace("_", " "), comparison.macro_f1, color="#305E83")
    ax.bar_label(bars, fmt="%.3f", padding=3); ax.set_ylim(0, 1.1)
    ax.tick_params(axis="x", labelrotation=22)
    ax.set(ylabel="Macro F1", title="Held-out agreement with the existing performance rubric")
    fig.tight_layout(); save_figure(fig, FIGURES / "model_comparison.png"); plt.close(fig)
    output = {"selected_model": meta["selected_model"], "selected_before_test": True,
              "test_rows": len(test), "metrics": rows,
              "interpretation": "Scores measure reproduction of rule-based labels in this combined dataset. The exact rubric is the relevant non-ML baseline.",
              "limitations": meta["limitations"]}
    write_json(REPORTS / "evaluation_summary.json", output)
    lines = ["# Evaluation results", "", f"Selected by training-only CV: **{meta['selected_model']}**.",
             f"Training rows: {len(train)}. Held-out rows: {len(test)}. Related-match groups do not overlap.", "",
             "| Model | Accuracy | Macro precision | Macro recall | Macro F1 |",
             "|---|---:|---:|---:|---:|"]
    lines += [f"| {r['model']} | {r['accuracy']:.4f} | {r['macro_precision']:.4f} | {r['macro_recall']:.4f} | {r['macro_f1']:.4f} |" for r in rows]
    lines += ["", "The exact rubric needs no training. Strong ML scores here do not prove independent coaching ability.",
              "Feature importance explains the performance-label classifier; it is not a technical weakness explanation.",
              "", "## Limits of the experiment", ""] + [f"- {x}" for x in meta["limitations"]]
    (REPORTS / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(comparison.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("Read ml/outputs/reports/RESULTS.md before describing these results in your report.")
    return output
