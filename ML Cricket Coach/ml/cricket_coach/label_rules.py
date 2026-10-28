"""The existing label rubric, used as an explicit non-ML reference baseline."""
from .config import SUPPORTED_FORMATS


def rubric_label(runs, balls_faced, match_format):
    """Describe a completed innings. These thresholds are project assumptions."""
    if match_format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format {match_format!r}; use T20, ODI or Test.")
    if runs < 0 or balls_faced < 0:
        raise ValueError("Runs and balls faced cannot be negative.")
    strike_rate = 100.0 * runs / balls_faced if balls_faced else 0.0
    if match_format == "T20":
        if runs < 15: return "Poor"
        if runs >= 30 and strike_rate >= 120: return "Good"
        return "Average"
    if runs < 20: return "Poor"
    if runs >= 50 and (match_format == "Test" or strike_rate >= 80): return "Good"
    return "Average"


RUBRIC_DESCRIPTION = {
    "version": "1.0", "target": "completed-innings performance",
    "T20": "Poor: runs < 15; Good: runs >= 30 and SR >= 120; Average: otherwise.",
    "ODI": "Poor: runs < 20; Good: runs >= 50 and SR >= 80; Average: otherwise.",
    "Test": "Poor: runs < 20; Good: runs >= 50; Average: otherwise. SR is not used.",
    "zero_balls": "SR is encoded as 0; a zero-run run-out receives Poor as a scoring outcome, not a technical judgment.",
}
