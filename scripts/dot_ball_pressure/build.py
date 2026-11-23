#!/usr/bin/env python3
"""Build the CRITT dot-ball experiment from Cricsheet's men's T20I JSON ZIP."""

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import json
from math import sqrt
from pathlib import Path
import re
import shutil
from tempfile import NamedTemporaryFile
from urllib.request import urlopen
from zipfile import ZipFile

SOURCE = "https://cricsheet.org/downloads/t20s_male_json.zip"
LICENSE = "https://opendatacommons.org/licenses/by/1-0/"
ATTRIBUTION = (
    "Contains information from Cricsheet (https://cricsheet.org/downloads/), "
    "which is made available under the ODC Attribution License."
)
ROOT = Path(__file__).resolve().parents[2]
PHASES = ("all", "powerplay", "middle", "death")
STREAKS = ("0", "1", "2", "3", "4", "5+")
BUCKETS = (*STREAKS, "any", "all")
RUNS = ("0", "1", "2", "3", "4", "5", "6", "7+")
METRICS = ("dot", "wicket", "score", "boundary", "escape")
NON_DISMISSALS = {"retired hurt", "retired not out"}
Z95 = 1.959963984540054


@dataclass(frozen=True)
class Delivery:
    phase: str
    runs: int
    legal: bool
    wickets: int
    departure: bool
    boundary: bool

    @property
    def dot(self):
        return self.legal and self.runs == 0

    @property
    def continues(self):
        return self.dot and not self.departure


def read_delivery(over, raw):
    if not 0 <= over < 20:
        raise ValueError(f"Unexpected over number: {over}")
    phase = "powerplay" if over < 6 else "middle" if over < 15 else "death"
    extras = raw.get("extras", {})
    runs = raw["runs"]
    if runs["total"] != runs["batter"] + runs["extras"] or sum(extras.values()) != runs["extras"]:
        raise ValueError(f"Inconsistent runs/extras: {raw}")
    kinds = [w["kind"] for w in raw.get("wickets", [])]
    return Delivery(
        phase, runs["total"], not (extras.get("wides", 0) or extras.get("noballs", 0)),
        sum(kind not in NON_DISMISSALS for kind in kinds), bool(kinds),
        runs["batter"] in (4, 6) and not runs.get("non_boundary", False),
    )


def score_within_two(first, second):
    """Score before a scoreless departure resets the chain, in the same innings."""
    if first.runs > 0:
        return True
    if not first.continues:
        return False
    if second is None:
        return None
    return second.runs > 0


def contexts(innings):
    """One row per recorded delivery, using the state immediately before it."""
    deliveries = [
        read_delivery(over["over"], raw)
        for over in innings.get("overs", [])
        for raw in over["deliveries"]
    ]
    streak = wickets_lost = 0
    for index, ball in enumerate(deliveries):
        second = deliveries[index + 1] if index + 1 < len(deliveries) else None
        yield ball, STREAKS[min(streak, 5)], wickets_lost, score_within_two(ball, second)
        streak = streak + 1 if ball.continues else 0
        wickets_lost += ball.wickets


def count_delivery(counts, ball, escape):
    counts["n"] += 1
    counts["dot"] += ball.dot
    counts["wicket"] += ball.wickets > 0
    counts["score"] += ball.runs > 0
    counts["boundary"] += ball.boundary
    counts["legal"] += ball.legal
    counts["scoreAndWicket"] += ball.runs > 0 and ball.wickets > 0
    counts[f"runs:{ball.runs}"] += 1
    counts["runs:7+"] += ball.runs >= 7
    if escape is not None:
        counts["escapeN"] += 1
        counts["escape"] += escape


def cluster_interval(pairs):
    """95% Wilson-style interval with effective N from match-level residuals."""
    n = sum(total for _, total in pairs)
    y = sum(events for events, _ in pairs)
    matches = len(pairs)
    if matches < 2:
        return [y, None, None]
    rate = y / n
    if y in (0, n):
        # There is no observed variance. Treat each match as one weighted unit.
        effective_n = n * n / sum(total * total for _, total in pairs)
    else:
        variance = matches / (matches - 1) * sum(
            (events - rate * total) ** 2 for events, total in pairs
        ) / n**2
        effective_n = min(n, rate * (1 - rate) / variance) if variance else n
    adjustment = Z95**2 / effective_n
    center = (rate + adjustment / 2) / (1 + adjustment)
    radius = sqrt(adjustment * rate * (1 - rate) + adjustment**2 / 4) / (1 + adjustment)
    return [y, round(max(0.0, center - radius), 7), round(min(1.0, center + radius), 7)]


def summarize(cells, totals):
    escape = [(c["escape"], c["escapeN"]) for c in cells.values() if c["escapeN"]]
    metrics = {
        metric: cluster_interval([(c[metric], c["n"]) for c in cells.values()])
        for metric in METRICS if metric != "escape"
    }
    metrics["escape"] = cluster_interval(escape)
    run_counts = {
        run: cluster_interval([(c[f"runs:{run}"], c["n"]) for c in cells.values()])
        for run in RUNS
    }
    return {
        "n": sum(c["n"] for c in cells.values()), "matches": len(cells),
        "escapeN": sum(total for _, total in escape), "escapeMatches": len(escape),
        "frequency": cluster_interval([
            (cells.get(match, {}).get("n", 0), c["n"]) for match, c in totals.items()
        ]),
        "metrics": metrics,
        "runs": run_counts,
        "scoreAndWicket": sum(c["scoreAndWicket"] for c in cells.values()),
    }


def contrast(cells, terms, metric):
    """Cluster delta-method CI for a linear combination of proportions."""
    influence = defaultdict(float)
    parts = []
    estimate = 0.0
    for sign, key in terms:
        selected = cells[key]
        denominator = "escapeN" if metric == "escape" else "n"
        n = sum(c[denominator] for c in selected.values())
        if not n:
            return None
        y = sum(c[metric] for c in selected.values())
        p = y / n
        estimate += sign * p
        parts.append({"group": key[0], "phase": key[1], "streak": key[2], "events": y, "n": n})
        for match, c in selected.items():
            if c[denominator]:
                influence[match] += sign * (c[metric] - p * c[denominator]) / n
    matches = len(influence)
    if matches < 2:
        return None
    se = sqrt(matches / (matches - 1) * sum(x * x for x in influence.values()))
    return {"metric": metric, "estimate": round(estimate, 7),
            "ci": [round(estimate - Z95 * se, 7), round(estimate + Z95 * se, 7)],
            "matches": matches, "parts": parts}


def long_streak_gap(phase):
    return [(1, ("world", phase, "5+")), (-1, ("world", phase, "0"))]


def build(archive, retrieved, fit_model=True):
    if fit_model:
        from model import fit_wicket_model

    cells = defaultdict(dict)
    listed, played, batting = Counter(), Counter(), Counter()
    dates, versions = [], set()
    audit = Counter()
    sequences = []
    team_dates = defaultdict(list)
    seen = set()
    japan_opponents = Counter()
    japan_batting_opponents = Counter()

    with ZipFile(archive) as source:
        names = sorted(n for n in source.namelist() if n.endswith(".json"))
        readme = source.read("README.txt").decode("utf-8")
        withheld = re.search(r"A further (\d+) matches have been withheld", readme)
        for name in names:
            match = Path(name).stem
            if match in seen:
                raise ValueError(f"Duplicate match: {match}")
            seen.add(match)
            raw = json.loads(source.read(name))
            info = raw["info"]
            if (info["gender"], info["team_type"], info["match_type"]) != ("male", "international", "T20"):
                raise ValueError(f"Unexpected match type in men's T20I archive: {match}")
            if info["balls_per_over"] != 6:
                raise ValueError(f"Unexpected balls per over: {match}")
            audit["nonstandardInfoOvers"] += info["overs"] != 20
            versions.add(raw["meta"]["data_version"])
            match_date = min(info["dates"])
            teams = info["teams"]
            team_a, team_b = teams
            if team_a == team_b:
                raise ValueError(f"Invalid match teams: {match}")
            listed.update(teams)
            if "Japan" in teams:
                japan_opponents.update(team for team in teams if team != "Japan")
            local = defaultdict(Counter)
            batting_teams = set()
            match_model = Counter()
            for innings in raw.get("innings", []):
                if innings.get("super_over"):
                    audit["excludedSuperOvers"] += 1
                    audit["excludedSuperOverDeliveries"] += sum(
                        len(o["deliveries"]) for o in innings.get("overs", [])
                    )
                    continue
                team = innings["team"]
                opponent = team_b if team == team_a else team_a
                if team not in teams:
                    raise ValueError(f"Unexpected batting team: {match}")
                for ball, bucket, wickets_lost, escape in contexts(innings):
                    batting_teams.add(team)
                    count_delivery(local[(team, ball.phase, bucket)], ball, escape)
                    if fit_model:
                        match_model[(team, opponent, ball.phase, wickets_lost, bucket, bool(ball.wickets))] += 1
            if not local:
                continue
            played.update(teams)
            batting.update(batting_teams)
            dates.append(match_date)
            if "Japan" in batting_teams:
                japan_batting_opponents[team_b if team_a == "Japan" else team_a] += 1
            for team in batting_teams:
                team_dates[team].append(match_date)
            for (team, phase, bucket), counts in local.items():
                groups = [f"team:{team}", "world"]
                if team != "Japan":
                    groups.append("world-ex-japan")
                for group in groups:
                    for portion in (phase, "all"):
                        for streak in ((bucket, "all") if bucket == "0" else (bucket, "any", "all")):
                            cells[(group, portion, streak)].setdefault(match, Counter()).update(counts)
            if fit_model:
                sequences.append((match_date[:4], match_model))

    if not dates:
        raise ValueError("No recorded T20I deliveries")
    groups = ["world", "world-ex-japan", *(f"team:{team}" for team in sorted(listed))]
    countries = {
        team: {"archiveMatches": listed[team], "matches": played[team], "battingMatches": batting[team],
               "from": min(team_dates[team], default=None), "to": max(team_dates[team], default=None)}
        for team in sorted(listed)
    }
    contrasts = {
        "worldWicket5Vs0": contrast(cells, long_streak_gap("all"), "wicket"),
        "worldDot5Vs0": contrast(cells, long_streak_gap("all"), "dot"),
        "worldWicket5Vs0ByPhase": {
            phase: contrast(cells, long_streak_gap(phase), "wicket")
            for phase in PHASES[1:]
        },
        "phaseGapContrasts": {
            f"{phase}-vs-{baseline}": {
                metric: contrast(cells, long_streak_gap(phase) +
                                 [(-sign, key) for sign, key in long_streak_gap(baseline)], metric)
                for metric in ("dot", "wicket")
            }
            for phase, baseline in (("middle", "powerplay"), ("death", "powerplay"), ("death", "middle"))
        },
        "japanVsRestAny": {
            metric: contrast(cells, [(1, ("team:Japan", "all", "any")),
                                     (-1, ("world-ex-japan", "all", "any"))], metric)
            for metric in ("wicket", "score", "escape")
        },
    }
    world = cells[("world", "all", "all")]
    exact_runs = Counter()
    for counts in world.values():
        exact_runs.update({k[5:]: v for k, v in counts.items() if k.startswith("runs:") and k[5:].isdigit()})
    return {
        "metadata": {
            "schema": 1, "source": SOURCE, "license": LICENSE, "attribution": ATTRIBUTION,
            "retrieved": retrieved, "sha256": sha256(archive.read_bytes()).hexdigest(),
            "jsonVersions": sorted(versions), "archiveMatches": len(seen), "matches": len(world),
            "from": min(dates), "to": max(dates), "withheldMatches": int(withheld[1]) if withheld else None,
            "deliveries": sum(c["n"] for c in world.values()), "legal": sum(c["legal"] for c in world.values()),
            "excludedSuperOvers": audit["excludedSuperOvers"],
            "excludedSuperOverDeliveries": audit["excludedSuperOverDeliveries"],
            "nonstandardInfoOvers": audit["nonstandardInfoOvers"],
            "minimum": {"n": 100, "matches": 20}, "exactWorldRuns": exact_runs,
            "countries": countries, "japanOpponents": japan_opponents,
            "japanBattingOpponents": japan_batting_opponents,
        },
        "groups": {
            group: {
                phase: {bucket: summarize(cells[(group, phase, bucket)], cells[(group, phase, "all")])
                        for bucket in BUCKETS}
                for phase in PHASES
            }
            for group in groups
        },
        "contrasts": contrasts,
        "adjustedWicket": fit_wicket_model(sequences) if fit_model else None,
    }


def download(archive):
    with urlopen(SOURCE, timeout=90) as response, NamedTemporaryFile(
        dir=archive.parent, delete=False
    ) as temporary:
        try:
            shutil.copyfileobj(response, temporary)
            temporary.flush()
            with ZipFile(temporary.name) as source:
                if source.testzip() is not None:
                    raise ValueError("Corrupt Cricsheet ZIP")
            Path(temporary.name).replace(archive)
        finally:
            Path(temporary.name).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path, help="path to Cricsheet ZIP")
    parser.add_argument("--download", action="store_true", help="fetch the latest official ZIP into --archive")
    parser.add_argument("--retrieved", type=datetime.fromisoformat, help="ZIP retrieval date (YYYY-MM-DD)")
    parser.add_argument("--output", type=Path, default=ROOT / "data/dot-ball-pressure.json")
    parser.add_argument("--descriptive-only", action="store_true", help="skip the optional regression")
    args = parser.parse_args()
    if args.retrieved is None and not args.download:
        parser.error("--retrieved is required when using an existing ZIP")
    if args.download:
        args.archive.parent.mkdir(parents=True, exist_ok=True)
        download(args.archive)
    retrieved = args.retrieved or datetime.now(timezone(timedelta(hours=9)))
    result = build(args.archive, retrieved.date().isoformat(), not args.descriptive_only)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.output.parent, delete=False) as output:
        try:
            json.dump(result, output, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
            output.write("\n")
            output.flush()
            Path(output.name).replace(args.output)
        finally:
            Path(output.name).unlink(missing_ok=True)
    print(f'{result["metadata"]["matches"]:,} matches, {result["metadata"]["deliveries"]:,} deliveries → {args.output}')


if __name__ == "__main__":
    main()
