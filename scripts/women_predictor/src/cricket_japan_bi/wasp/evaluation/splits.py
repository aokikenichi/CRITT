"""Fixed locked test and rolling-origin split definitions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, Iterator, List, Mapping, Sequence, Tuple


TRAIN_END = date(2022, 12, 31)
VALIDATION_END = date(2024, 12, 31)


def _date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def assign_split(value: Any) -> str:
    match_date = _date(value)
    if match_date <= TRAIN_END:
        return "train"
    if match_date <= VALIDATION_END:
        return "validation"
    return "test"


@dataclass(frozen=True)
class RollingFold:
    validation_year: int
    train_indices: Tuple[int, ...]
    validation_indices: Tuple[int, ...]
    train_match_ids: Tuple[str, ...]
    validation_match_ids: Tuple[str, ...]


def rolling_origin_folds(
    records: Sequence[Mapping[str, Any]],
    *,
    validation_years: Sequence[int] = (2023, 2024),
) -> List[RollingFold]:
    """Make year folds while keeping every state from a match together."""

    match_date = {}
    for row in records:
        match_id = str(row.get("match_id") or "")
        value = _date(row.get("match_date") or row.get("date"))
        previous = match_date.setdefault(match_id, value)
        if previous != value:
            raise ValueError("match {} appears with multiple dates".format(match_id))
    folds: List[RollingFold] = []
    for year in validation_years:
        train_ids = {match_id for match_id, value in match_date.items() if value.year < year}
        validation_ids = {match_id for match_id, value in match_date.items() if value.year == year}
        if not train_ids or not validation_ids:
            continue
        train_indices = tuple(
            index for index, row in enumerate(records) if str(row.get("match_id") or "") in train_ids
        )
        validation_indices = tuple(
            index
            for index, row in enumerate(records)
            if str(row.get("match_id") or "") in validation_ids
        )
        folds.append(
            RollingFold(
                validation_year=year,
                train_indices=train_indices,
                validation_indices=validation_indices,
                train_match_ids=tuple(sorted(train_ids)),
                validation_match_ids=tuple(sorted(validation_ids)),
            )
        )
    return folds


def split_records(records: Iterable[Mapping[str, Any]]) -> Mapping[str, List[Mapping[str, Any]]]:
    result = {"train": [], "validation": [], "test": []}
    seen = {}
    for row in records:
        match_id = str(row.get("match_id") or "")
        split = str(row.get("split") or assign_split(row.get("match_date") or row.get("date")))
        previous = seen.setdefault(match_id, split)
        if previous != split:
            raise ValueError("match {} spans multiple splits".format(match_id))
        result[split].append(row)
    return result
