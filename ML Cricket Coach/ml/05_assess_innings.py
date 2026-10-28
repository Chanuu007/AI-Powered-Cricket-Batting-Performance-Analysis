"""Example: python ml/05_assess_innings.py --runs 44 --balls 50 --format ODI"""
import argparse
import json
from cricket_coach.api import assess_innings

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify a completed innings, not a future innings.")
    parser.add_argument("--runs", type=int, required=True)
    parser.add_argument("--balls", type=int, required=True)
    parser.add_argument("--format", dest="match_format", choices=["T20", "ODI", "Test"], required=True)
    args = parser.parse_args()
    print(json.dumps(assess_innings(args.runs, args.balls, args.match_format), indent=2))
