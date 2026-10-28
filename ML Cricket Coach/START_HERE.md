# Cricket batting analysis ML guide

This project now contains a complete, runnable ML comparison and retrospective player-analysis workflow. The existing `backend/`, `frontend/`, `data/` and `docs/` folders are preserved. All Python implementation files are in `ml/`.

You do not need to paste code from the chat. Extract the ZIP and open the project folder in VS Code. The files already contain the code. If you prefer to keep your existing project folder, copy the entire `ml/` folder and this guide into it, and use the included workbook at `data/Match_Data_Newl.xlsx`. Do not copy `.venv/` or mix outputs from different model runs.

## 1. Understand what the implementation does

The three classifiers are Decision Tree, Random Forest and Logistic Regression. Their target is the existing `Performance_Label`: Poor, Average or Good. They assess an innings whose runs and balls faced are already known. They do not forecast next-match runs or dismissal types.

The complete workflow has three different analytical responsibilities:

| Part | Method | Output |
|---|---|---|
| Completed-innings performance | Trained classifier, compared with the exact existing rubric | Model label and rubric label, both shown |
| Recent form | Descriptive summary of the latest five completed innings in the same format | Label distribution, majority summary, mean runs, weighted strike rate and consistency |
| Areas to review and tips | Recurring dismissal-pattern analysis plus an evidence-linked coaching catalogue | Supported review candidates, counts, record IDs and practice suggestions |

The dataset has no independent technical-weakness labels or coaching-tip targets. Consequently, the code does not pretend to train a supervised technical-coaching model. Pattern analysis and tips complement the classifier. This is a hybrid ML and statistical coaching-support prototype.

Your performance labels were created from runs and strike rate. Therefore a high classification score mainly shows that the model reproduces that rule. It does not prove expert-level coaching or improved batting. The exact rubric is included as a non-ML baseline, so the model comparison is honest about this limitation. Independent coach review would be needed to validate the ratings and the usefulness of advice.

All 1,000 rows are read and processed together. There are no separate original/synthetic input files, and the original workbook is not edited. Its existing provenance notes are retained in the manifest. The notes identify supplied and generated records; treating known generated records as verified real matches would be inaccurate. Results are described as an internal benchmark on the combined dataset.

## 2. Install Python and open the correct folder

Use Python **3.12** for the closest match to the tested environment. Open the folder that directly contains `ml`, `data`, `backend` and `frontend`. In VS Code, select **Terminal > New Terminal**. Do not open a terminal inside `ml/cricket_coach/`.

On Windows, check Python:

```powershell
py -3.12 --version
```

If this command fails, install Python 3.12 and reopen VS Code. The project does not require MySQL, Flask or React to run the ML stage.

## 3. Create an isolated Python environment

Run these commands in the project folder on Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r ml\requirements.txt
```

This guide calls the environment's Python directly. You do not need to activate PowerShell scripts or change your execution policy.

In VS Code, use **Ctrl+Shift+P > Python: Select Interpreter**, then select `.venv\Scripts\python.exe` for editing and debugging.

On macOS/Linux, the equivalent setup is:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r ml/requirements.txt
```

For subsequent commands on macOS/Linux, replace `.\.venv\Scripts\python.exe` with `.venv/bin/python` and use `/` in paths.

## 4. Prepare the dataset

The supplied workbook is already in the correct location:

`data/Match_Data_Newl.xlsx`

Run:

```powershell
.\.venv\Scripts\python.exe ml\01_prepare_data.py
```

This step:

1. Reads `Match_Data`, player names and existing source notes.
2. Checks required columns, numbers, formats, labels, duplicate innings and dismissal status.
3. Recalculates strike rate in a processed copy. It keeps literal `NA` values as categories rather than accidentally treating them as blank values.
4. Parses text dates as day-first and preserves already-stored Excel dates. It logs future dates instead of guessing corrections.
5. Records data-quality observations and keeps the Excel workbook unchanged.
6. Creates one combined processed CSV and two exploratory figures.

Important outputs:

- `ml/outputs/processed/innings.csv`
- `ml/outputs/processed/manifest.json`
- `ml/outputs/reports/data_quality_issues.csv`
- `ml/outputs/reports/figures/label_distribution.png`
- `ml/outputs/reports/figures/runs_and_strike_rate.png`

The issue report includes observations, not only fatal errors. For example, it logs a recalculated strike rate, unknown context or a future recorded date. Resolve source-date problems before relying on chronological form conclusions. A date already stored as an Excel date may have been converted incorrectly before this project; the code cannot reconstruct the intended date without a source.

To use another workbook path, pass it explicitly:

```powershell
.\.venv\Scripts\python.exe ml\01_prepare_data.py --dataset "C:\path\to\your_dataset.xlsx"
```

For player analysis with that workbook, also pass the same `--dataset` option to step 7.

## 5. Train and compare the algorithms on training folds

Run:

```powershell
.\.venv\Scripts\python.exe ml\02_train_models.py
```

The model inputs are `runs`, `balls_faced`, recalculated `strike_rate` and `match_format`. The target is `performance_label`. Player IDs, match IDs, dates, record IDs and grouping information are excluded from model inputs. Dismissal context is reserved for the separate pattern analysis.

The code holds out 20% of related-match groups for final testing. It uses the remaining groups for five-fold cross-validation and a small parameter search. Existing workbook notes identify resampled matches, allowing related records to stay together. All rows are still in one table; this grouping does not create origin-specific datasets. If those notes are unavailable in a future workbook, grouping falls back to Match ID and cannot recover hidden ancestry.

In each fold, the preprocessing learns only from that fold's training records. Numeric values are imputed and scaled, and match format is one-hot encoded. These steps and the classifier are saved together as a scikit-learn Pipeline. The code selects the algorithm with the highest training-only CV macro F1. It does not select a model by its final test score.

This is a retrospective grouped evaluation. It is not a time-based forecast test, not an evaluation on entirely new players, and not an untouched verified-real-world test.

Important outputs:

- `ml/outputs/models/decision_tree.joblib`
- `ml/outputs/models/random_forest.joblib`
- `ml/outputs/models/logistic_regression.joblib`
- `ml/outputs/models/selected_model.joblib`
- `ml/outputs/models/metadata.json`
- `ml/outputs/processed/split_assignments.csv`
- `ml/outputs/reports/cv_comparison.csv`

`selected_model.joblib` is the selected model fitted on the training partition only. The project does not silently refit it on test records. The metadata records versions, feature names, parameters, source hashes and split sizes. Only load trusted artifacts produced by this project; a joblib file can contain executable Python objects.

## 6. Evaluate the locked models

Run:

```powershell
.\.venv\Scripts\python.exe ml\03_evaluate_models.py
```

This evaluates the three saved models on the same held-out records. It adds a training-majority baseline and the exact performance-rubric baseline. You receive accuracy, macro precision, macro recall, macro F1, per-class reports and confusion matrices. Macro averages give every class equal weight.

Read:

- `ml/outputs/reports/RESULTS.md`
- `ml/outputs/reports/model_comparison.csv`
- `ml/outputs/reports/test_predictions.csv`
- `ml/outputs/reports/figures/model_comparison.png`
- `ml/outputs/reports/figures/decision_tree_confusion_matrix.png`
- `ml/outputs/reports/figures/random_forest_confusion_matrix.png`
- `ml/outputs/reports/figures/logistic_regression_confusion_matrix.png`

`selected_model_feature_importance.csv` shows how strongly the selected classifier relies on its scoring inputs. It does not diagnose a technical batting weakness. In this task, dependence on runs and strike rate is expected because the labels came from those inputs.

Use these figures as actual execution evidence in your report, with the label-generation and combined-data limitations clearly stated. Model test scores do not answer whether coaching advice is effective.

After understanding the separate steps, you can rerun preparation, training and evaluation together:

```powershell
.\.venv\Scripts\python.exe ml\run_all.py
```

## 7. Analyze a player's form, recurring patterns and tips

First list the available players and formats:

```powershell
.\.venv\Scripts\python.exe ml\04_analyze_player.py --list-players
```

Then run a player report:

```powershell
.\.venv\Scripts\python.exe ml\04_analyze_player.py --player P001 --format T20 --as-of 2026-10-26
```

Change the player ID and format as needed. A second example is:

```powershell
.\.venv\Scripts\python.exe ml\04_analyze_player.py --player P006 --format ODI --as-of 2026-10-26
```

The as-of date excludes later-dated records. If omitted, it uses today's date in Sri Lanka. Each report includes a warning that source dates must be verified. Form is calculated within a match format; T20, ODI and Test innings are not mixed into one recent-form window.

The recent-form summary uses the latest five eligible innings. It reports a majority of the existing performance labels, or `Mixed` if no label has a majority. With fewer than five innings, it reports `Insufficient history` and does not invent a form label. It also shows model labels separately, mean runs, weighted strike rate and run variability. The form rule itself is descriptive, not a separately trained current-form model.

The pattern engine uses all eligible past innings for that player and format. By default a review candidate must appear in at least three rows, three match IDs, two related-match groups, and 20% of recorded dismissals. These are prototype evidence thresholds, not statistically validated cricket standards. They are settings in `ml/cricket_coach/config.py`.

Each suggestion links to the pattern and exact supporting record IDs. If there is not enough evidence, the system says so. It does not manufacture a personalized technical weakness. Without all the successful deliveries faced, it cannot estimate the risk of getting out to a particular delivery type.

Example outputs:

- `ml/outputs/reports/player_P001_T20.json`: structured results for future Flask use.
- `ml/outputs/reports/player_P001_T20.md`: readable analysis.
- `ml/outputs/reports/figures/player_P001_T20.png`: recent runs and strike rate.

The practice catalogue is in `ml/cricket_coach/coaching_rules.json`. Its suggestions are drafts for coach review. You can edit the text and drills without retraining the classifier.

## 8. Assess one completed innings

Run:

```powershell
.\.venv\Scripts\python.exe ml\05_assess_innings.py --runs 44 --balls 50 --format ODI
```

The output includes the learned `model_label`, the exact `rubric_label`, and whether they agree. This separation is intentional: a learned classifier can differ from the rule it approximates. No future score or dismissal is predicted. A single innings assessment does not establish current form.

## 9. Run the checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s ml\tests -v
```

The checks cover numeric boundaries, zero-ball innings, date interpretation, family grouping, split separation, literal NA values, insufficient history, future-date exclusion, weighted strike rate, traceable tips and safe rejection of invalid records. Integration checks require the model from step 5.

## 10. Where each code file belongs

| File | What you should understand |
|---|---|
| `ml/01_prepare_data.py` | Thin command-line wrapper for dataset preparation. |
| `ml/02_train_models.py` | Starts the three-model comparison. |
| `ml/03_evaluate_models.py` | Creates held-out metrics and figures. |
| `ml/04_analyze_player.py` | Creates a player report, supported patterns and tips. |
| `ml/05_assess_innings.py` | Assesses a completed innings from supplied runs and balls. |
| `ml/cricket_coach/config.py` | Paths, allowed features, labels, evidence settings and limitations. |
| `ml/cricket_coach/data.py` | Workbook loading, validation, date handling and related-match grouping. |
| `ml/cricket_coach/prepare.py` | Processed files, audit metadata and exploratory figures. |
| `ml/cricket_coach/label_rules.py` | The documented rule baseline; it is not ML training. |
| `ml/cricket_coach/pipelines.py` | Preprocessing and the three algorithms' small search grids. |
| `ml/cricket_coach/train.py` | Group splits, cross-validation, parameter selection and saved models. |
| `ml/cricket_coach/evaluate.py` | Accuracy, precision, recall, F1, matrices and interpretation. |
| `ml/cricket_coach/predictor.py` | Loads the saved pipeline once and checks artifact compatibility. |
| `ml/cricket_coach/analysis.py` | Recent form, dismissal-pattern support and evidence-linked tips. |
| `ml/cricket_coach/coaching_rules.json` | Editable practice suggestions, not training labels. |
| `ml/cricket_coach/api.py` | Public functions to reuse in Flask later. |
| `ml/tests/test_workflow.py` | Meaningful boundary and integration checks. |

`X` means input features. `y` means the target label. `fit()` learns from training data. `predict()` classifies a completed record. Cross-validation estimates agreement on different training partitions while selecting settings. The final test partition is used only after selection. A saved Pipeline keeps the preprocessing and classifier together so they use the same transformations during actual assessment.

## 11. Later Flask integration

When you start the application, these functions are already available. From Python run at the project root:

```python
from ml.cricket_coach.api import assess_innings, analyze_player, analyze_history

completed = assess_innings(runs=44, balls_faced=50, match_format="ODI")
player = analyze_player("P001", "T20", as_of="2026-10-26")
```

For a database-backed application, query the authenticated player's innings and pass normalized records to `analyze_history`. Its required field names are documented in that function. It can calculate rule labels for new histories that do not yet have `performance_label`. Do not retrain inside a web request. Validate ownership of player records in the application layer before calling these functions.

## 12. Common problems

| Problem | What to do |
|---|---|
| Python command not found | Install Python 3.12 and reopen the terminal. |
| Cannot find `ml/01_prepare_data.py` | Open the project root containing `ml` and `data`. |
| `ModuleNotFoundError` | Install `ml/requirements.txt` using the same `.venv` Python used to run the scripts. |
| Dataset not found | Keep the filename `data/Match_Data_Newl.xlsx`, or pass `--dataset`. |
| Missing/invalid columns | Restore the exact workbook headers and read the specific error. |
| Processed data changed | Do not edit generated CSVs. Edit the source workbook and rerun steps 4–6. |
| Model version mismatch | Install the pinned requirements or retrain all models in your environment. |
| No player history | Check the player ID, selected format and as-of date. |
| No weakness/tip returned | This can be the correct result when support is insufficient. Do not lower thresholds just to force a tip. |
| Future dates in history | Verify source dates; do not simply swap day and month automatically. |
| JSON and model metadata do not match | Restore matching outputs or rerun the complete workflow. |

## Sources for the implementation choices

- Scikit-learn, avoiding leakage: https://scikit-learn.org/stable/common_pitfalls.html
- Scikit-learn, stratified grouped folds: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html
- Scikit-learn, model persistence and version compatibility: https://scikit-learn.org/stable/model_persistence.html

The source workbook, generated outputs and stored labels remain subject to the limitations above. You can complete the software prototype with this package; claims about independently accurate weakness diagnosis or improved real-world batting need additional validation.
