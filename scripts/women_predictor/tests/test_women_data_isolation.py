"""Source isolation and preserved cricket-state/split behavior for women."""

from __future__ import annotations

import csv
import importlib.util
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from cricket_japan_bi.csv2_parser import iter_csv2_matches
from cricket_japan_bi.wasp.data.audit import (
    AuditInvariantError,
    audit_csv2_archive,
    validate_womens_t20i_archive,
)
from cricket_japan_bi.wasp.data.normalize import _prepare_match, _write_match_rows, prepare_dataset
from cricket_japan_bi.wasp.data.rules import (
    chase_terminal_status,
    counts_as_team_wicket,
    phase_absolute,
    phase_relative,
    split_for_date,
)
from cricket_japan_bi.wasp.evaluation.splits import rolling_origin_folds


def info_text(match_id: str = "4242", **overrides: str) -> str:
    cohort = {"gender": "female", "team_type": "international", "match_type": "T20"}
    cohort.update(overrides)
    rows = [
        "version,2.3.0", "info,balls_per_over,6", "info,team,Japan",
        "info,team,Example XI", "info,season,2025", "info,date,2025/02/01",
        "info,match_id," + match_id, "info,overs,20", "info,toss_winner,Japan",
        "info,toss_decision,bat", "info,winner,Example XI",
        "info,target_overs,2,20", "info,target_runs,2,8",
        "info,player,Japan,A", "info,player,Japan,B",
        "info,player,Example XI,C", "info,player,Example XI,D",
        "info,registry,people,A,aaaaaaaa", "info,registry,people,B,bbbbbbbb",
        "info,registry,people,C,cccccccc", "info,registry,people,D,dddddddd",
    ]
    rows.extend("info,{},{}".format(key, value) for key, value in cohort.items() if value is not None)
    return "\n".join(rows) + "\n"


def ball_text(match_id: str = "4242") -> str:
    columns = (
        "match_id", "season", "start_date", "venue", "innings", "ball", "actual_delivery",
        "batting_team", "bowling_team", "striker", "non_striker", "bowler",
        "runs_off_bat", "extras", "wides", "noballs", "wicket_type", "player_dismissed",
        "other_wicket_type", "other_player_dismissed",
    )
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    deliveries = [
        {"ball": "0.1", "actual_delivery": "0.1", "runs_off_bat": 1, "extras": 0},
        {"ball": "0.2", "actual_delivery": "0.1", "runs_off_bat": 0, "extras": 1, "wides": 1},
        {"ball": "0.3", "actual_delivery": "0.1", "runs_off_bat": 4, "extras": 1, "noballs": 1},
        {"ball": "0.4", "actual_delivery": "0.2", "runs_off_bat": 0, "extras": 0,
         "wicket_type": "caught", "player_dismissed": "A",
         "other_wicket_type": "retired hurt", "other_player_dismissed": "B"},
        {"innings": 2, "ball": "0.1", "actual_delivery": "0.1", "runs_off_bat": 8, "extras": 0,
         "batting_team": "Example XI", "bowling_team": "Japan", "striker": "C",
         "non_striker": "D", "bowler": "B"},
    ]
    for delivery in deliveries:
        row = {"match_id": match_id, "season": "2025", "start_date": "2025-02-01",
               "venue": "Tokyo", "innings": 1, "batting_team": "Japan",
               "bowling_team": "Example XI", "striker": "A", "non_striker": "B", "bowler": "C"}
        row.update(delivery)
        writer.writerow(row)
    return buffer.getvalue()


class WomenDataIsolationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)

    def archive(self, name: str = "source", **overrides: str) -> Path:
        path = self.root / (name + ".zip")
        with zipfile.ZipFile(path, "w") as output:
            output.writestr("4242_info.csv", info_text(**overrides))
            output.writestr("4242.csv", ball_text())
        return path

    def test_female_archive_accepted_and_audited(self) -> None:
        archive = self.archive()
        self.assertEqual(validate_womens_t20i_archive(archive), 1)
        report = audit_csv2_archive(archive)
        self.assertEqual(report.counts["matches"], 1)
        self.assertEqual(report.counts["deliveries"], 5)
        self.assertEqual(report.counts["legal_balls"], 3)
        self.assertEqual(report.counts["team_wicket_events"], 1)
        self.assertEqual(report.counts["non_team_wicket_events"], 1)
        self.assertEqual(report.to_dict()["source_cohort"], {
            "gender": "female", "team_type": "international", "match_type": "T20",
            "validated_matches": 1, "mixed_cohort_allowed": False,
        })
        self.assertEqual(next(iter_csv2_matches(archive)).metadata.gender, "female")

    def test_wrong_or_missing_cohort_rejected_before_outputs(self) -> None:
        invalid = [
            {"gender": "male"}, {"team_type": "club"}, {"match_type": "ODI"},
            {"gender": None}, {"team_type": None}, {"match_type": None},
            {"gender": ""}, {"team_type": ""}, {"match_type": ""},
        ]
        for index, overrides in enumerate(invalid):
            with self.subTest(overrides=overrides):
                archive = self.archive(str(index), **overrides)
                output = self.root / ("output-" + str(index))
                with self.assertRaises(AuditInvariantError):
                    audit_csv2_archive(archive, output_json=output / "audit.json")
                self.assertFalse(output.exists())
                with self.assertRaises(AuditInvariantError):
                    prepare_dataset(archive, output, create_duckdb=False)
                self.assertFalse(output.exists())

    def test_mixed_archive_rejects_male_before_delivery_scan(self) -> None:
        archive = self.archive()
        with zipfile.ZipFile(archive, "a") as output:
            output.writestr("9999_info.csv", info_text("9999", gender="male"))
            # A metadata violation must be diagnosed before reading this invalid ball file.
            output.writestr("9999.csv", "invalid delivery data\n")
        with self.assertRaisesRegex(AuditInvariantError, "match 9999 has gender='male'"):
            audit_csv2_archive(archive)

    def test_hash_mismatch_rejected_before_outputs(self) -> None:
        output = self.root / "hash-output"
        with self.assertRaisesRegex(AuditInvariantError, "SHA-256 mismatch"):
            prepare_dataset(self.archive(), output, expected_sha256="0" * 64)
        self.assertFalse(output.exists())

    def test_exact_normalized_states_preserve_physical_delivery_semantics(self) -> None:
        class MemoryWriters:
            def __init__(self) -> None:
                self.rows = {}

            def append(self, table, row) -> None:
                self.rows.setdefault(table, []).append(row)

        match = next(iter_csv2_matches(self.archive()))
        summaries, exclusions, flags = _prepare_match(match)
        writers = MemoryWriters()
        _write_match_rows(writers, match, summaries, exclusions, flags)
        states = writers.rows["states"]
        self.assertEqual(len(states), 7)
        first = [row for row in states if row["innings"] == 1]
        golden = [
            (0, 0, 0, 0, "start", None),
            (1, 1, 0, 1, "delivery", None),
            (2, 2, 0, 1, "wide", None),
            (3, 7, 0, 1, "no_ball", None),
            (4, 7, 1, 2, "wicket", "innings_complete"),
        ]
        actual = [(row["state_sequence"], row["runs_so_far"], row["wickets_lost"],
                   row["legal_balls_bowled"], row["previous_event"], row["terminal_status"])
                  for row in first]
        self.assertEqual(actual, golden)
        self.assertTrue(all(row["first_innings_eligible"] for row in first))
        self.assertTrue(all(row["split"] == "test" for row in first))
        self.assertAlmostEqual(sum(row["sample_weight"] for row in first), 1.0)
        chase = [row for row in states if row["innings"] == 2]
        self.assertEqual([(row["runs_so_far"], row["legal_balls_bowled"], row["terminal_status"],
                           row["terminal_probability"]) for row in chase],
                         [(0, 0, None, None), (8, 1, "chase_won", 1.0)])
        self.assertTrue(all(row["chase_eligible"] for row in chase))

    @unittest.skipUnless(importlib.util.find_spec("pyarrow") is not None, "PyArrow required")
    def test_prepared_parquet_contains_female_states_and_context(self) -> None:
        import pyarrow.parquet as parquet

        manifest = prepare_dataset(self.archive(), self.root / "valid-output", create_duckdb=False)
        self.assertEqual(manifest["row_counts"]["states"], 7)
        self.assertEqual(manifest["row_counts"]["model_ready_states"], 7)
        matches = parquet.read_table(manifest["paths"]["matches"]).to_pylist()
        self.assertEqual([(row["gender"], row["team_type"], row["match_type"]) for row in matches],
                         [("female", "international", "T20")])
        states = parquet.read_table(manifest["paths"]["model_ready_states"]).to_pylist()
        self.assertTrue(all(row["pre_match_elo"] == 1500.0 for row in states))
        self.assertEqual(states[3]["runs_so_far"], 7)
        self.assertEqual(states[3]["legal_balls_bowled"], 1)

    def test_split_phase_and_terminal_boundaries_preserved(self) -> None:
        self.assertEqual([split_for_date(value) for value in (
            "2009/06/18", "2022/12/31", "2023/01/01", "2024/12/31", "2025/01/01")],
            ["train", "train", "validation", "validation", "test"])
        self.assertEqual([phase_absolute(ball) for ball in (0, 35, 36, 95, 96, 120)],
                         ["powerplay", "powerplay", "middle", "middle", "death", "death"])
        self.assertEqual(phase_relative(36, 120), "middle")
        self.assertEqual(phase_relative(96, 120), "death")
        self.assertFalse(counts_as_team_wicket("retired hurt"))
        self.assertTrue(counts_as_team_wicket("retired out"))
        self.assertEqual(chase_terminal_status(8, 10, 0, 8), "chase_won")
        self.assertEqual(chase_terminal_status(7, 10, 0, 8), "tied_regulation")
        records = [{"match_id": match, "match_date": date} for match, date in (
            ("old", "2022-12-31"), ("val23", "2023-01-01"),
            ("val23", "2023-01-01"), ("val24", "2024-12-31"), ("locked", "2025-01-01"))]
        folds = rolling_origin_folds(records)
        self.assertEqual(folds[0].train_match_ids, ("old",))
        self.assertEqual(folds[0].validation_indices, (1, 2))
        self.assertEqual(folds[1].train_match_ids, ("old", "val23"))
        self.assertEqual(folds[1].validation_match_ids, ("val24",))
        self.assertTrue(all("locked" not in fold.train_match_ids + fold.validation_match_ids for fold in folds))


if __name__ == "__main__":
    unittest.main()
