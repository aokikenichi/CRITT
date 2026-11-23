import json
from collections import Counter
from importlib.util import find_spec
from math import exp
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from build import BUCKETS, JSON_OUTPUT, LOCAL_OUTPUT, PHASES, STREAKS, build, cluster_interval, contexts


def delivery(batter=0, *, extras=None, wickets=(), non_boundary=False):
    extras = extras or {}
    total = sum(extras.values())
    return {
        "runs": {"batter": batter, "extras": total, "total": batter + total, "non_boundary": non_boundary},
        "extras": extras,
        "wickets": [{"kind": kind} for kind in wickets],
    }


def innings(team, *overs, **fields):
    return {"team": team, "overs": [{"over": i, "deliveries": ds} for i, ds in overs], **fields}


class DeliveryTests(unittest.TestCase):
    def test_hand_calculated_sequence(self):
        example = innings(
            "Japan",
            (5, [delivery(), delivery()]),
            (6, [
                delivery(extras={"wides": 1}, wickets=("stumped",)),
                delivery(),
                delivery(4, extras={"noballs": 1}),
                delivery(extras={"legbyes": 1}),
                delivery(4, non_boundary=True),
                delivery(wickets=("bowled",)),
                delivery(wickets=("retired hurt",)),
                delivery(2, wickets=("run out", "retired not out")),
                *[delivery() for _ in range(7)],
            ]),
        )
        rows = list(contexts(example))
        self.assertEqual([s for _, s, _, _ in rows],
                         ["0", "1", "2", "0", "1", "0", "0", "0", "0", "0", "0", "1", "2", "3", "4", "5+", "5+"])
        self.assertEqual([i for i, (ball, _, _, _) in enumerate(rows) if not ball.legal], [2, 4])
        self.assertEqual([i for i, (ball, _, _, _) in enumerate(rows) if ball.wickets], [2, 7, 9])
        self.assertEqual([i for i, (ball, _, _, _) in enumerate(rows) if ball.boundary], [4])
        self.assertEqual([i for i, (ball, _, _, _) in enumerate(rows) if ball.runs and ball.wickets], [2, 9])
        self.assertEqual([i for i, (ball, _, _, _) in enumerate(rows) if ball.dot],
                         [0, 1, 3, 7, 8, 10, 11, 12, 13, 14, 15, 16])
        self.assertEqual([e for _, _, _, e in rows],
                         [False, True, True, True, True, True, True, False, False, True,
                          False, False, False, False, False, False, None])
        self.assertEqual([lost for _, _, lost, _ in rows[:11]], [0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 3])
        self.assertEqual([b.phase for b, _, _, _ in rows[:3]], ["powerplay", "powerplay", "middle"])
        scoreless_wicket, scoring_wicket = list(contexts(innings(
            "Japan", (14, [delivery(wickets=("retired out",))]),
            (15, [delivery(1, wickets=("run out",))]),
        )))
        self.assertEqual([scoreless_wicket[0].phase, scoring_wicket[0].phase], ["middle", "death"])
        self.assertEqual([scoreless_wicket[-1], scoring_wicket[-1]], [False, True])
        self.assertEqual(scoring_wicket[2], 1)
        other = list(contexts(innings("India", (0, [delivery(extras={"byes": 1, "penalty": 5})]))))
        self.assertEqual(other[0][1:], ("0", 0, True))
        self.assertTrue(other[0][0].legal)
        self.assertFalse(other[0][0].boundary)

    def test_archive_aggregation_and_hand_calculated_rate(self):
        first = innings("Japan", (5, [delivery(), delivery()]),
                        (6, [delivery(extras={"wides": 1}, wickets=("stumped",)), delivery()]))
        second = innings("India", (0, [delivery(), delivery(6), delivery()]))
        third = innings("Japan", (0, [delivery(), delivery(), delivery(4)]))
        super_over = innings("India", (0, [delivery(6)]), super_over=True)

        def match(*parts):
            return {"meta": {"data_version": "1.3.0"},
                    "info": {"gender": "male", "team_type": "international", "match_type": "T20",
                             "balls_per_over": 6, "overs": 20, "dates": ["2022-01-01"],
                             "teams": ["Japan", "India"]}, "innings": parts}

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.zip"
            with ZipFile(path, "w") as archive:
                archive.writestr("README.txt", "A further 2 matches have been withheld")
                archive.writestr("1.json", json.dumps(match(first, second, super_over)))
                archive.writestr("2.json", json.dumps(match(third)))
            result = build(path, "2026-11-23", fit_model=False)

        m, groups = result["metadata"], result["groups"]
        self.assertEqual((m["matches"], m["deliveries"], m["legal"], m["withheldMatches"]), (2, 10, 9, 2))
        self.assertEqual((m["excludedSuperOvers"], m["excludedSuperOverDeliveries"]), (1, 1))
        self.assertEqual((m["countries"]["India"]["matches"], m["countries"]["India"]["battingMatches"]), (2, 1))
        two = groups["world"]["all"]["2"]
        self.assertEqual((two["n"], two["matches"], two["escapeN"], two["scoreAndWicket"]), (2, 2, 2, 1))
        self.assertEqual(two["metrics"]["wicket"][0] / two["n"], 0.5)
        self.assertEqual(two["metrics"]["score"][0] / two["n"], 1)
        self.assertEqual(two["metrics"]["escape"][0] / two["escapeN"], 1)
        self.assertEqual(two["frequency"][0] / groups["world"]["all"]["all"]["n"], 0.2)
        self.assertEqual(groups["world"]["middle"]["2"]["metrics"]["wicket"], [1, None, None])
        self.assertEqual(groups["world-ex-japan"]["all"]["all"]["n"], 3)
        self.assertEqual(groups["world-ex-japan"]["all"]["all"]["escapeN"], 2)
        self.assertEqual(m["exactWorldRuns"], {"0": 7, "1": 1, "4": 1, "6": 1})

    def test_cluster_interval_handles_dependence_and_boundary(self):
        mixed = cluster_interval([(5, 10), (5, 10)])
        clustered = cluster_interval([(0, 10), (10, 10)])
        self.assertLess(clustered[1], mixed[1])
        self.assertGreater(clustered[2], mixed[2])
        self.assertEqual(cluster_interval([]), [0, None, None])
        self.assertEqual(cluster_interval([(0, 2)])[1:], [None, None])
        self.assertGreater(cluster_interval([(0, 2), (0, 3)])[2], 0)


class ArtifactTests(unittest.TestCase):
    def test_local_browser_data_matches_release_json(self):
        release = JSON_OUTPUT.read_text(encoding="utf-8").rstrip("\n")
        local = LOCAL_OUTPUT.read_text(encoding="utf-8")
        self.assertTrue(local == f"globalThis.crittDotBallPressureData = {release};\n",
                        "Local browser data must match the release JSON")

    def test_release_aggregate_invariants(self):
        data = json.loads(JSON_OUTPUT.read_text(encoding="utf-8"))
        groups = data["groups"]
        teams = [g for g in groups if g.startswith("team:")]
        self.assertEqual(len(teams), len(data["metadata"]["countries"]))
        self.assertEqual(groups["world"]["all"]["all"]["n"], data["metadata"]["deliveries"])
        for group, phases in groups.items():
            self.assertEqual(
                phases["all"]["all"]["n"], sum(phases[p]["all"]["n"] for p in PHASES[1:]), group
            )
            for phase, cells in phases.items():
                self.assertEqual(cells["all"]["n"], sum(cells[k]["n"] for k in STREAKS), (group, phase))
                self.assertEqual(cells["any"]["n"], sum(cells[k]["n"] for k in STREAKS[1:]), (group, phase))
                for c in cells.values():
                    n, metric = c["n"], c["metrics"]
                    self.assertEqual(sum(v[0] for v in c["runs"].values()), n)
                    self.assertEqual(metric["score"][0] + c["runs"]["0"][0], n)
                    self.assertLessEqual(metric["boundary"][0], metric["score"][0])
                    self.assertLessEqual(c["scoreAndWicket"], min(metric["wicket"][0], metric["score"][0]))
                    self.assertLessEqual(metric["score"][0], metric["escape"][0])
                    self.assertLessEqual(metric["escape"][0], c["escapeN"])
                    self.assertLessEqual(c["escapeN"], n)
        for phase in PHASES:
            for bucket in BUCKETS:
                select = lambda group: groups[group][phase][bucket]
                world = select("world")
                self.assertEqual(world["n"], sum(select(g)["n"] for g in teams))
                rest, japan = select("world-ex-japan"), select("team:Japan")
                for metric in world["metrics"]:
                    self.assertEqual(world["metrics"][metric][0],
                                     rest["metrics"][metric][0] + japan["metrics"][metric][0])
        model = data["adjustedWicket"]
        if model:
            self.assertEqual(model["n"], data["metadata"]["deliveries"])
            self.assertEqual(model["events"], groups["world"]["all"]["all"]["metrics"]["wicket"][0])


@unittest.skipUnless(find_spec("scipy") and find_spec("numpy"), "Optional model dependencies unavailable")
class ModelTests(unittest.TestCase):
    def test_grouped_logit_and_cluster_covariance_against_manual_solution(self):
        from model import fit_wicket_model

        sequences = []
        first, second = [2, 3, 1, 2], [3, 4, 6, 3]
        influences = []
        for a, b in zip(first, second):
            row = Counter()
            for streak, events in [("0", a), ("1", b)]:
                context = ("Japan", "India", "middle", 0, streak)
                row[(*context, True)] = events
                row[(*context, False)] = 20 - events
            sequences.append(("2025", row))
            influences.append((b - 4) / (80 * .2 * .8) - (a - 2) / (80 * .1 * .9))

        result = fit_wicket_model(sequences)
        estimate = result["oddsRatios"]["1"]
        self.assertEqual((result["n"], result["matches"], result["events"]), (160, 4, 24))
        self.assertAlmostEqual(estimate["oddsRatio"], 2.25, places=5)
        span = 1.959963984540054 * (4 / 3 * 159 / 158 * sum(x*x for x in influences)) ** .5
        self.assertAlmostEqual(estimate["ci"][0], 2.25 * exp(-span), places=5)
        self.assertAlmostEqual(estimate["ci"][1], 2.25 * exp(span), places=5)


if __name__ == "__main__":
    unittest.main()
