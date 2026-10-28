# Evaluation results

Selected by training-only CV: **random_forest**.
Training rows: 764. Held-out rows: 236. Related-match groups do not overlap.

| Model | Accuracy | Macro precision | Macro recall | Macro F1 |
|---|---:|---:|---:|---:|
| decision_tree | 0.9746 | 0.9710 | 0.9765 | 0.9733 |
| random_forest | 0.9534 | 0.9498 | 0.9601 | 0.9516 |
| logistic_regression | 0.9237 | 0.9230 | 0.9330 | 0.9214 |
| majority_baseline | 0.3475 | 0.1158 | 0.3333 | 0.1719 |
| exact_rubric_baseline | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

The exact rubric needs no training. Strong ML scores here do not prove independent coaching ability.
Feature importance explains the performance-label classifier; it is not a technical weakness explanation.

## Limits of the experiment

- Retrospective assessment of completed innings; no next-match forecasting.
- Performance_Label is a researcher-defined rubric, not independent coach ground truth.
- Classification scores measure agreement with that rubric, not coaching effectiveness.
- The workbook records supplied and generated innings. All rows are processed together; scores are an internal mixed-data benchmark, not verified-real-world accuracy.
- Dismissal-only context lacks successful deliveries faced; patterns are review candidates, not per-ball dismissal risks or proven technical faults.
- Practice tips are evidence-linked suggestions from a fixed rule catalogue, not learned or coach-validated prescriptions.
