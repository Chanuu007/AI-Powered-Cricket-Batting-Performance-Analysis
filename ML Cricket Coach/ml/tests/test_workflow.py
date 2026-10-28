"""Boundary and integrity checks; run with Python's built-in unittest."""
import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cricket_coach.config import DATASET, MODELS, FEATURES
from cricket_coach.data import load_dataset, family_root, parse_match_date
from cricket_coach.label_rules import rubric_label
from cricket_coach.predictor import validate_scoring, get_assessor
from cricket_coach.analysis import analyze_history, find_patterns
from cricket_coach.train import create_splits


def history_fixture(n=5):
    return pd.DataFrame([{
        "player_id": "NEW_PLAYER", "match_id": str(i), "match_date": f"2026-01-{i+1:02d}",
        "innings_number": 1, "runs": 40, "balls_faced": 30, "match_format": "T20",
        "out_status": "Not Out", "dismissal_type": "Not Out", "bowling_length": "NA",
        "bowling_line": "NA", "shot_type": "NA", "bowler_type": "NA",
        "record_id": f"test_{i}", "split_group": f"family_{i}",
    } for i in range(n)])


class InputTests(unittest.TestCase):
    def test_invalid_numeric_inputs_rejected(self):
        for value in [-1, 2.5, float("nan"), float("inf"), True, "bad"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_scoring(value, 20, "T20")

    def test_zero_ball_runout_outcome(self):
        self.assertEqual(validate_scoring(0, 0, "ODI")["strike_rate"], 0)
        self.assertEqual(rubric_label(0, 0, "ODI"), "Poor")

    def test_format_normalization_and_rejection(self):
        self.assertEqual(validate_scoring(50, 150, "test")["match_format"], "Test")
        with self.assertRaises(ValueError): validate_scoring(30, 20, "T10")

    def test_performance_rubric_uses_exact_rate(self):
        self.assertEqual(rubric_label(30, 25, "T20"), "Good")
        self.assertEqual(rubric_label(30, 26, "T20"), "Average")
        self.assertEqual(rubric_label(50, 200, "Test"), "Good")

    def test_dates_preserved_and_invalid_dates_unavailable(self):
        self.assertEqual(parse_match_date("03/07/2026"), pd.Timestamp("2026-07-03"))
        self.assertEqual(parse_match_date(pd.Timestamp("2026-03-07")), pd.Timestamp("2026-03-07"))
        self.assertTrue(pd.isna(parse_match_date("not a date")))
        self.assertTrue(pd.isna(parse_match_date(pd.NaT)))

    def test_family_ancestry_and_cycles(self):
        self.assertEqual(family_root("3", {"3": "2", "2": "1"}), "1")
        with self.assertRaises(ValueError): family_root("1", {"1": "2", "2": "1"})


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame, cls.players, cls.meta, cls.issues = load_dataset(DATASET)

    def test_all_input_rows_are_kept_together(self):
        self.assertEqual(len(self.frame), 1000)
        self.assertEqual(self.frame.record_id.nunique(), 1000)
        self.assertEqual(self.meta["split_groups"], 25)

    def test_provenance_notes_are_retained(self):
        self.assertTrue(any("synthetic" in n["text"].lower() for n in self.meta["source_notes"]))

    def test_literal_na_not_treated_as_missing(self):
        self.assertFalse(self.frame.bowler_type.isna().any())
        self.assertTrue((self.frame.bowler_type == "NA").any())

    def test_data_quality_discrepancy_is_logged(self):
        self.assertTrue(((self.issues.record_id == "row_139") & (self.issues.field == "strike_rate")).any())

    def test_related_matches_do_not_cross_any_split(self):
        train, test, folds = create_splits(self.frame)
        self.assertFalse(set(train.split_group) & set(test.split_group))
        self.assertEqual(len(train) + len(test), 1000)
        for fit, validate in folds:
            self.assertFalse(set(train.iloc[fit].split_group) & set(train.iloc[validate].split_group))

    def test_identifiers_and_target_are_not_model_features(self):
        self.assertFalse(set(FEATURES) & {"player_id", "match_id", "record_id", "split_group", "performance_label", "match_date"})


@unittest.skipUnless((MODELS / "selected_model.joblib").is_file(), "Train the model before integration tests.")
class AnalysisTests(unittest.TestCase):
    def test_new_player_does_not_need_to_be_in_training(self):
        report = analyze_history(history_fixture(), "NEW_PLAYER", "T20", as_of="2026-10-26")
        self.assertEqual(report["current_form"]["summary_label"], "Good")
        self.assertEqual(len(report["recent_innings"]), 5)

    def test_not_out_history_creates_no_dismissal_weakness(self):
        report = analyze_history(history_fixture(), "NEW_PLAYER", "T20", as_of="2026-10-26")
        self.assertEqual(report["weakness_review_candidates"], [])
        self.assertEqual(report["recommendations"], [])

    def test_fewer_than_five_innings_does_not_force_form_label(self):
        report = analyze_history(history_fixture(2), "NEW_PLAYER", "T20", as_of="2026-10-26")
        self.assertEqual(report["current_form"]["status"], "Insufficient history")
        self.assertIsNone(report["current_form"]["summary_label"])

    def test_future_and_invalid_dates_are_excluded(self):
        history = history_fixture(7)
        history.loc[5, "match_date"] = "2027-01-01"
        history.loc[6, "match_date"] = "bad"
        report = analyze_history(history, "NEW_PLAYER", "T20", as_of="2026-10-26")
        self.assertEqual(report["excluded_future_date_rows"], 1)
        self.assertEqual(report["excluded_invalid_date_rows"], 1)
        self.assertEqual(report["eligible_history_innings"], 5)

    def test_weighted_rate_not_mean_of_rates(self):
        history = history_fixture(2)
        history["runs"] = [30, 30]; history["balls_faced"] = [10, 30]
        report = analyze_history(history, "NEW_PLAYER", "T20", as_of="2026-10-26")
        self.assertEqual(report["current_form"]["weighted_strike_rate"], 150)

    def test_related_repetitions_are_not_independent_pattern_support(self):
        history = history_fixture(5)
        history["out_status"] = "Out"; history["dismissal_type"] = "Caught"
        history["bowling_length"] = "Short"; history["performance_label"] = "Poor"
        history["split_group"] = "family_one"
        self.assertEqual(find_patterns(history), [])

    def test_supported_tips_include_traceable_evidence(self):
        history = history_fixture(5)
        history["out_status"] = "Out"; history["dismissal_type"] = "Caught"
        history["bowling_length"] = "Short"; history["bowling_line"] = "Outside Off"
        history["shot_type"] = "Pull"; history["bowler_type"] = "Right-arm Fast"
        report = analyze_history(history, "NEW_PLAYER", "T20", as_of="2026-10-26")
        self.assertTrue(report["recommendations"])
        for recommendation in report["recommendations"]:
            evidence = recommendation["evidence"]
            self.assertEqual(evidence["dismissal_count"], len(evidence["evidence_record_ids"]))
            self.assertTrue(set(evidence["evidence_record_ids"]).issubset(history.record_id))

    def test_duplicate_history_rejected(self):
        history = history_fixture()
        history.loc[1, "match_id"] = history.loc[0, "match_id"]
        with self.assertRaises(ValueError):
            analyze_history(history, "NEW_PLAYER", "T20", as_of="2026-10-26")

    def test_unknown_player_returns_clear_error(self):
        with self.assertRaisesRegex(ValueError, "No T20 innings"):
            analyze_history(history_fixture(), "MISSING", "T20", as_of="2026-10-26")

    def test_loaded_assessor_returns_both_model_and_reference(self):
        result = get_assessor().assess(44, 50, "ODI")
        self.assertEqual(result["rubric_label"], "Average")
        self.assertIn(result["model_label"], ["Poor", "Average", "Good"])


if __name__ == "__main__":
    unittest.main()
