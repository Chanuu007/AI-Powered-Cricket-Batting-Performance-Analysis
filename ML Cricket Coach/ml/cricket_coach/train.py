"""Step 2: tune on training folds only, select by CV macro F1, save pipelines."""
from datetime import datetime, timezone
import platform
import importlib.metadata
import shutil
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, make_scorer
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold, GridSearchCV
from .config import FEATURES, TARGET, MODELS, REPORTS, PROCESSED, RANDOM_SEED, LABELS, LIMITATIONS
from .io_utils import write_json, file_hash
from .pipelines import candidates, make_pipeline
from .prepare import load_prepared


def create_splits(frame):
    groups = frame.split_group
    if groups.nunique() < 8:
        raise ValueError("At least eight independent match/family groups are needed for this experiment.")
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=RANDOM_SEED)
    train_index, test_index = next(splitter.split(frame[FEATURES], frame[TARGET], groups))
    train, test = frame.iloc[train_index].copy(), frame.iloc[test_index].copy()
    if set(train[TARGET]) != set(LABELS): raise ValueError("Training partition lacks a performance class.")
    if set(train.split_group) & set(test.split_group): raise AssertionError("Group overlap.")
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    folds = list(cv.split(train[FEATURES], train[TARGET], groups=train.split_group))
    for fit, validate in folds:
        if set(train.iloc[fit].split_group) & set(train.iloc[validate].split_group):
            raise AssertionError("Cross-validation group overlap.")
        if set(train.iloc[fit][TARGET]) != set(LABELS):
            raise ValueError("A training fold lacks a class. More independent examples are needed.")
    return train, test, folds


def train_models():
    frame, prepared = load_prepared()
    train, test, folds = create_splits(frame)
    MODELS.mkdir(parents=True, exist_ok=True); REPORTS.mkdir(parents=True, exist_ok=True)
    assignment = frame[["record_id", "player_id", "match_id", "split_group", TARGET]].copy()
    assignment["partition"] = np.where(assignment.record_id.isin(test.record_id), "test", "train")
    assignment.to_csv(PROCESSED / "split_assignments.csv", index=False)
    cv_rows, best_parameters = [], {}
    scorer = make_scorer(f1_score, labels=LABELS, average="macro", zero_division=0, pos_label=None)
    for name, (classifier, parameters) in candidates().items():
        print(f"Training {name.replace('_', ' ')} ...", flush=True)
        search = GridSearchCV(make_pipeline(classifier), parameters, scoring=scorer,
                              cv=folds, refit=True, n_jobs=1, return_train_score=False,
                              error_score="raise")
        search.fit(train[FEATURES], train[TARGET])
        cv_rows.append({"model": name, "cv_macro_f1": float(search.best_score_),
                        "cv_std": float(search.cv_results_["std_test_score"][search.best_index_])})
        best_parameters[name] = search.best_params_
        pd.DataFrame(search.cv_results_).to_csv(REPORTS / f"{name}_cv_search.csv", index=False)
        joblib.dump(search.best_estimator_, MODELS / f"{name}.joblib")
        print(f"  training-fold CV macro F1: {search.best_score_:.4f}", flush=True)
    comparison = pd.DataFrame(cv_rows).sort_values(["cv_macro_f1", "model"], ascending=[False, True])
    comparison.to_csv(REPORTS / "cv_comparison.csv", index=False)
    selected = comparison.iloc[0]["model"]
    shutil.copyfile(MODELS / f"{selected}.joblib", MODELS / "selected_model.joblib")
    versions = {x: importlib.metadata.version(x) for x in
                ["pandas", "numpy", "scikit-learn", "scipy", "joblib", "openpyxl", "matplotlib"]}
    meta = {
        "trained_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
        "dependency_versions": versions, "dataset_sha256": prepared["dataset_sha256"],
        "prepared_data_sha256": prepared["prepared_data_sha256"],
        "split_assignments_sha256": file_hash(PROCESSED / "split_assignments.csv"),
        "features": FEATURES, "target": TARGET, "labels": LABELS,
        "task": "Post-match classification of the existing rule-based innings performance label",
        "selected_model": selected, "selection_criterion": "Highest training-only 5-fold grouped CV macro F1; alphabetical model name breaks exact ties.",
        "test_used_for_selection": False, "fit_scope": "Training partition only; no silent refit on test records.",
        "train_rows": len(train), "test_rows": len(test),
        "train_groups": train.split_group.nunique(), "test_groups": test.split_group.nunique(),
        "train_class_counts": train[TARGET].value_counts().to_dict(),
        "test_class_counts": test[TARGET].value_counts().to_dict(),
        "split_method": "GroupShuffleSplit, 20% of match-family groups held out, seed 42; not a temporal or new-player generalization experiment.",
        "cv_folds": 5, "best_parameters": best_parameters,
        "selected_model_sha256": file_hash(MODELS / "selected_model.joblib"),
        "all_model_sha256": {name: file_hash(MODELS / f"{name}.joblib") for name in candidates()},
        "limitations": LIMITATIONS,
    }
    write_json(MODELS / "metadata.json", meta)
    (REPORTS / "requirements_tested.txt").write_text("\n".join(f"{k}=={v}" for k, v in versions.items()) + "\n", encoding="utf-8")
    print(f"Selected by CV: {selected}. Held-out test records have not been used for fitting or selection.")
    return meta
