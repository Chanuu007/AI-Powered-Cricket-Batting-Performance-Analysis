"""Optional shortcut for steps 1, 2 and 3: python ml/run_all.py"""
import argparse
from pathlib import Path
from cricket_coach.config import DATASET
from cricket_coach.prepare import prepare_dataset
from cricket_coach.train import train_models
from cricket_coach.evaluate import evaluate_models

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare, train and evaluate the complete ML comparison.")
    parser.add_argument("--dataset", type=Path, default=DATASET)
    args = parser.parse_args()
    prepare_dataset(args.dataset)
    train_models()
    evaluate_models()
    print("Finished. Next run ml/04_analyze_player.py for a player analysis.")
