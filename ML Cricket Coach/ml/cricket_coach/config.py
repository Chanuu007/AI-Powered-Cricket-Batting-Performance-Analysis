"""One place for paths, field names and reproducible experiment settings."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = PROJECT_ROOT / "ml"
DATASET = PROJECT_ROOT / "data" / "Match_Data_Newl.xlsx"
OUTPUTS = ML_ROOT / "outputs"
PROCESSED = OUTPUTS / "processed"
REPORTS = OUTPUTS / "reports"
FIGURES = REPORTS / "figures"
MODELS = OUTPUTS / "models"
RANDOM_SEED = 42
LABELS = ["Poor", "Average", "Good"]
NUMERIC_FEATURES = ["runs", "balls_faced", "strike_rate"]
CATEGORICAL_FEATURES = ["match_format"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET = "performance_label"
CONTEXT = ["bowling_length", "bowling_line", "shot_type", "bowler_type"]
SUPPORTED_FORMATS = ["T20", "ODI", "Test"]
MIN_PATTERN_ROWS = 3
MIN_PATTERN_MATCHES = 3
MIN_PATTERN_FAMILIES = 2
MIN_PATTERN_SHARE = 0.20

COLUMN_MAP = {
    "Player ID": "player_id", "Match ID": "match_id", "Match Date": "match_date",
    "Innings Number": "innings_number", "Runs": "runs", "Balls Faced": "balls_faced",
    "Strike Rate": "strike_rate", "Out / Not Out": "out_status",
    "Dismissal Type": "dismissal_type", "Bowling Length": "bowling_length",
    "Bowling Line": "bowling_line", "Shot Type": "shot_type",
    "Bowler Type": "bowler_type", "Match Format": "match_format",
    "Performance_Label": "performance_label",
}

LIMITATIONS = [
    "Retrospective assessment of completed innings; no next-match forecasting.",
    "Performance_Label is a researcher-defined rubric, not independent coach ground truth.",
    "Classification scores measure agreement with that rubric, not coaching effectiveness.",
    "The workbook records supplied and generated innings. All rows are processed together; scores are an internal mixed-data benchmark, not verified-real-world accuracy.",
    "Dismissal-only context lacks successful deliveries faced; patterns are review candidates, not per-ball dismissal risks or proven technical faults.",
    "Practice tips are evidence-linked suggestions from a fixed rule catalogue, not learned or coach-validated prescriptions.",
]
