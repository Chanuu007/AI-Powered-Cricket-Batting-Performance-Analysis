"""Load trusted local model artifacts and assess a completed innings."""
import math
from functools import lru_cache
import joblib
import pandas as pd
import sklearn
from .config import MODELS, FEATURES
from .io_utils import read_json, file_hash
from .label_rules import rubric_label


def validate_scoring(runs, balls_faced, match_format):
    for name, value in [("runs", runs), ("balls_faced", balls_faced)]:
        if isinstance(value, bool): raise ValueError(f"{name} must be a whole number, not True/False.")
        try: numeric = float(value)
        except (ValueError, TypeError): raise ValueError(f"{name} must be numeric.") from None
        if not math.isfinite(numeric) or numeric < 0 or not numeric.is_integer():
            raise ValueError(f"{name} must be a nonnegative whole number.")
    fmt = {"T20": "T20", "ODI": "ODI", "TEST": "Test"}.get(str(match_format).strip().upper())
    if fmt is None: raise ValueError("Match format must be T20, ODI or Test.")
    r, b = int(float(runs)), int(float(balls_faced))
    return {"runs": r, "balls_faced": b, "strike_rate": 100.0 * r / b if b else 0.0, "match_format": fmt}


class PerformanceAssessor:
    def __init__(self, model_dir=MODELS):
        from pathlib import Path
        directory = Path(model_dir)
        path = directory / "selected_model.joblib"
        if not path.is_file() or not (directory / "metadata.json").is_file():
            raise FileNotFoundError("No trained model. Run python ml/02_train_models.py first.")
        self.metadata = read_json(directory / "metadata.json")
        expected = self.metadata["dependency_versions"]["scikit-learn"]
        if sklearn.__version__ != expected:
            raise RuntimeError(f"This artifact uses scikit-learn {expected}, but you have {sklearn.__version__}. Install ml/requirements.txt or retrain in your environment.")
        if file_hash(path) != self.metadata["selected_model_sha256"]:
            raise ValueError("Model file does not match its metadata. Retrain or restore the matching artifact.")
        # Only load the trusted model produced by this project, never an unknown uploaded pickle/joblib.
        self.pipeline = joblib.load(path)

    def assess(self, runs, balls_faced, match_format):
        values = validate_scoring(runs, balls_faced, match_format)
        model_label = str(self.pipeline.predict(pd.DataFrame([values])[FEATURES])[0])
        rule = rubric_label(values["runs"], values["balls_faced"], values["match_format"])
        return {"task": "Completed-innings assessment", "inputs": values,
                "model": self.metadata["selected_model"], "model_label": model_label,
                "rubric_label": rule, "model_agrees_with_rubric": model_label == rule,
                "interpretation": "The model approximates the documented performance rubric. This is not a prediction of a future score or dismissal."}


@lru_cache(maxsize=1)
def get_assessor():
    """Load once per process; restart the process after retraining."""
    return PerformanceAssessor()
