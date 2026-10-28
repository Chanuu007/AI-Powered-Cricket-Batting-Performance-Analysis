"""Public Python functions for the command line now and Flask integration later."""
from .config import DATASET
from .data import load_dataset
from .analysis import analyze_history
from .predictor import get_assessor


def assess_innings(runs, balls_faced, match_format):
    return get_assessor().assess(runs, balls_faced, match_format)


def analyze_player(player_id, match_format, dataset=DATASET, as_of=None, recent_window=5):
    history, names, _, _ = load_dataset(dataset)
    return analyze_history(history, player_id, match_format, as_of=as_of,
                           recent_window=recent_window, player_name=names.get(str(player_id)))


__all__ = ["assess_innings", "analyze_player", "analyze_history"]
