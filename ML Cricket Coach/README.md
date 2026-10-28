# ML Cricket Coach

Start with **[START_HERE.md](START_HERE.md)** for the complete beginner workflow.

Project folders:

- `data/`: the supplied Excel workbook, preserved unchanged.
- `docs/`: the supplied research proposal.
- `ml/`: completed Python ML and analysis implementation, tests and generated results.
- `backend/`: reserved for the Flask application stage.
- `frontend/`: reserved for the React application stage.

Run order after installing `ml/requirements.txt`:

```bash
python ml/01_prepare_data.py
python ml/02_train_models.py
python ml/03_evaluate_models.py
python ml/04_analyze_player.py --player P001 --format T20 --as-of 2026-10-26
python ml/05_assess_innings.py --runs 44 --balls 50 --format ODI
python -m unittest discover -s ml/tests -v
```

Use your virtual environment's Python. Windows instructions that avoid PowerShell activation issues are in START_HERE.md.

This package assesses completed innings. It does not predict future match scores or dismissal types. The classifier approximates the existing rule-generated performance labels. Pattern analysis and a fixed coaching catalogue provide evidence-linked review candidates and tips. Current-form summaries are descriptive; they are not independently coach-validated labels.

All workbook rows are processed in one table. Existing provenance notes are retained. Internal benchmark results must not be presented as accuracy on 1,000 independent verified real innings.
