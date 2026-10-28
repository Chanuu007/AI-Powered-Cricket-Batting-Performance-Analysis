# ML execution record

Validated on 26 October 2026 with Python 3.12.

All 22 unit and integration checks passed. The preparation, training, evaluation, single-innings CLI and player-analysis CLIs were executed successfully.

Training partition: 764 rows in 20 related-match groups. Held-out partition: 236 rows in 5 groups.
Selected by training-only cross-validation: random_forest. No selection was made using the final test scores.

| Model | Test accuracy | Test macro F1 |
|---|---:|---:|
| decision_tree | 0.9746 | 0.9733 |
| random_forest | 0.9534 | 0.9516 |
| logistic_regression | 0.9237 | 0.9214 |
| majority_baseline | 0.3475 | 0.1719 |
| exact_rubric_baseline | 1.0000 | 1.0000 |

Random Forest was selected by cross-validation. Decision Tree happened to score higher on this held-out test partition; selection was not changed after seeing the test results.

The exact rubric reproduces its own generated labels perfectly. These results measure agreement with existing rule-based labels in a combined dataset; they do not establish independently accurate coaching.

Example player reports were generated for P001/T20 and P006/ODI as of 2026-10-26. The CLI was also exercised on a 44-runs, 50-balls ODI innings.

All generated PNG files were checked for valid image data. The source workbook and proposal remain byte-for-byte unchanged.

The trained artifacts are provided for immediate experimentation. Install the pinned requirements before loading them. You can reproduce the training using the numbered scripts.

A separate independent coach-reviewed evaluation is still required for claims about actual weakness diagnosis and recommendation usefulness.
