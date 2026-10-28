"""Run from the project folder: python ml/01_prepare_data.py"""
import argparse
from pathlib import Path
from cricket_coach.config import DATASET
from cricket_coach.prepare import prepare_dataset


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate the workbook and prepare one combined dataset.")
    parser.add_argument("--dataset", type=Path, default=DATASET)
    args = parser.parse_args()
    prepare_dataset(args.dataset)
