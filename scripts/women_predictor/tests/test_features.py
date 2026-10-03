from __future__ import annotations

import pytest

from cricket_japan_bi.wasp.features.chronology import (
    build_prematch_features,
    select_elo_k,
)
from cricket_japan_bi.wasp.features.datasets import build_first_innings_dataset
from cricket_japan_bi.wasp.features.states import (
    build_innings_states,
    chase_terminal,
    counts_as_team_wicket,
)


def test_delivery_after_states_count_only_legal_balls_and_team_wickets():
    deliveries = [
        {
            "source_sequence": 1,
            "total_runs": 1,
            "wides": 1,
            "legal_ball": False,
            "team_wickets": 0,
        },
        {
            "source_sequence": 2,
            "total_runs": 2,
            "noballs": 1,
            "legal_ball": False,
            "team_wickets": 0,
        },
        {
            "source_sequence": 3,
            "total_runs": 0,
            "legal_ball": True,
            "wickets": [{"kind": "retired hurt"}, {"kind": "run out"}],
        },
    ]
    innings = {
        "match_id": "fixture",
        "innings": 1,
        "batting_team": "Japan",
        "bowling_team": "World XI",
        "innings_ball_limit": 120,
        "final_runs": 3,
        "final_wickets": 1,
    }
    states = build_innings_states(
        deliveries,
        innings,
        {"match_id": "fixture", "match_date": "2025-01-01", "venue": "Ground"},
    )
    assert len(states) == 4
    assert states[0]["previous_event_type"] == "innings_start"
    assert states[1]["legal_balls_bowled"] == 0
    assert states[2]["legal_balls_bowled"] == 0
    assert states[3]["legal_balls_bowled"] == 1
    assert states[3]["wickets_lost"] == 1
    assert states[3]["previous_event_type"] == "wicket"


def test_unknown_dismissal_is_not_silently_guessed():
    assert counts_as_team_wicket("retired hurt") is False
    assert counts_as_team_wicket("retired out") is True
    with pytest.raises(ValueError, match="unknown dismissal"):
        counts_as_team_wicket("experimental kind")


def test_regulation_tie_has_no_binary_probability():
    assert chase_terminal(score=80, target=80, wickets_lost=3, balls_remaining=2) == (
        "chase_won",
        1.0,
    )
    assert chase_terminal(score=79, target=80, wickets_lost=10, balls_remaining=0) == (
        "tied_regulation",
        None,
    )
    assert chase_terminal(score=78, target=80, wickets_lost=10, balls_remaining=1) == (
        "chase_lost",
        0.0,
    )


def test_same_day_elo_snapshots_are_batch_updated():
    matches = [
        {
            "match_id": "one",
            "match_date": "2024-01-01",
            "team_1": "A",
            "team_2": "B",
            "winner": "A",
        },
        {
            "match_id": "two",
            "match_date": "2024-01-01",
            "team_1": "A",
            "team_2": "C",
            "winner": "A",
        },
        {
            "match_id": "three",
            "match_date": "2024-01-02",
            "team_1": "A",
            "team_2": "B",
            "winner": "B",
        },
    ]
    snapshots = build_prematch_features(matches)
    by_key = {(row["match_id"], row["team"]): row for row in snapshots}
    assert by_key[("one", "A")]["pre_match_elo"] == 1500.0
    assert by_key[("two", "A")]["pre_match_elo"] == 1500.0
    assert by_key[("three", "A")]["pre_match_elo"] > 1500.0


def test_super_over_and_bowl_out_are_half_score_for_elo():
    matches = [
        {
            "match_id": "seed",
            "match_date": "2022-01-01",
            "team_1": "A",
            "team_2": "B",
            "winner": "A",
        },
        {
            "match_id": "super",
            "match_date": "2023-01-01",
            "team_1": "A",
            "team_2": "B",
            "winner": "A",
            "has_super_over": True,
        },
        {
            "match_id": "bowl",
            "match_date": "2023-01-02",
            "team_1": "A",
            "team_2": "B",
            "winner": "B",
            "has_bowl_out": True,
        },
        {
            "match_id": "nr",
            "match_date": "2023-01-03",
            "team_1": "A",
            "team_2": "B",
            "result": "no result",
        },
    ]
    snapshots = build_prematch_features(matches)
    by_key = {(row["match_id"], row["team"]): row for row in snapshots}
    assert by_key[("bowl", "A")]["pre_match_elo"] < by_key[("super", "A")]["pre_match_elo"]
    # The half-score can reduce a previously favoured team's rating, but NR does not.
    assert by_key[("nr", "A")]["pre_match_elo"] < by_key[("bowl", "A")]["pre_match_elo"]
    selection = select_elo_k(matches)
    assert selection.selected_k in {16.0, 24.0, 32.0}


def test_state_weights_sum_to_one_per_match():
    states = [
        {
            "match_id": "m1",
            "innings": 1,
            "runs_so_far": value,
            "final_score": 10,
            "first_innings_eligible": True,
            "is_reduced_match": False,
        }
        for value in (0, 1, 2)
    ]
    dataset = build_first_innings_dataset(states)
    assert sum(row["sample_weight"] for row in dataset) == pytest.approx(1.0)
