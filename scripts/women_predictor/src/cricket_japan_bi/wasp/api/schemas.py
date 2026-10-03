"""Public request and response schemas for the WASP-style HTTP API."""

from __future__ import annotations

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    """Base model that rejects misspelled or unsupported request fields."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class BallQuota(StrictModel):
    """An over/ball pair. The ball component is base six, never decimal."""

    overs: int = Field(ge=0, examples=[20])
    balls: int = Field(default=0, ge=0, le=5, examples=[0])

    @property
    def total_balls(self) -> int:
        return self.overs * 6 + self.balls

    @model_validator(mode="after")
    def validate_t20_limit(self) -> "BallQuota":
        if self.total_balls > 120:
            raise ValueError("a T20 ball quota cannot exceed 120 legal balls")
        return self


class FirstInningsRequest(StrictModel):
    batting_team: str = Field(min_length=1, max_length=120)
    bowling_team: str = Field(min_length=1, max_length=120)
    runs: int = Field(ge=0)
    wickets: int = Field(ge=0, le=10)
    completed: BallQuota
    quota: BallQuota = Field(default_factory=lambda: BallQuota(overs=20))
    venue: str | None = Field(default=None, max_length=240)
    toss_winner: str | None = Field(default=None, max_length=120)
    toss_decision: Literal["bat", "field"] | None = None
    use_japan_correction: bool = True

    @field_validator("venue", "toss_winner", mode="after")
    @classmethod
    def empty_optional_strings_are_none(cls, value: str | None) -> str | None:
        return value or None

    @model_validator(mode="after")
    def validate_state(self) -> "FirstInningsRequest":
        if self.batting_team.casefold() == self.bowling_team.casefold():
            raise ValueError("batting_team and bowling_team must be different")
        if self.quota.total_balls == 0:
            raise ValueError("quota must contain at least one ball")
        if self.completed.total_balls > self.quota.total_balls:
            raise ValueError("completed balls cannot exceed the innings quota")
        if self.toss_winner and self.toss_winner.casefold() not in {
            self.batting_team.casefold(),
            self.bowling_team.casefold(),
        }:
            raise ValueError("toss_winner must be one of the two teams")
        return self


class ChaseRequest(StrictModel):
    chasing_team: str = Field(min_length=1, max_length=120)
    defending_team: str = Field(min_length=1, max_length=120)
    target: int = Field(ge=1)
    current_score: int = Field(ge=0)
    wickets: int = Field(ge=0, le=10)
    target_ball_limit: BallQuota = Field(default_factory=lambda: BallQuota(overs=20))
    balls_remaining: int = Field(ge=0)
    venue: str | None = Field(default=None, max_length=240)
    toss_winner: str | None = Field(default=None, max_length=120)
    toss_decision: Literal["bat", "field"] | None = None
    use_japan_correction: bool = True

    @field_validator("venue", "toss_winner", mode="after")
    @classmethod
    def empty_optional_strings_are_none(cls, value: str | None) -> str | None:
        return value or None

    @model_validator(mode="after")
    def validate_state(self) -> "ChaseRequest":
        if self.chasing_team.casefold() == self.defending_team.casefold():
            raise ValueError("chasing_team and defending_team must be different")
        limit = self.target_ball_limit.total_balls
        if limit == 0:
            raise ValueError("target_ball_limit must contain at least one ball")
        if self.balls_remaining > limit:
            raise ValueError("balls_remaining cannot exceed target_ball_limit")
        if self.toss_winner and self.toss_winner.casefold() not in {
            self.chasing_team.casefold(),
            self.defending_team.casefold(),
        }:
            raise ValueError("toss_winner must be one of the two teams")
        return self


class ScorePredictionComparison(StrictModel):
    global_: float = Field(alias="global")
    team_adjusted: float
    japan_adjusted: float
    selected: float

    model_config = ConfigDict(
        extra="forbid", str_strip_whitespace=True, populate_by_name=True
    )


class ProbabilityPredictionComparison(StrictModel):
    global_: float | None = Field(default=None, alias="global")
    team_adjusted: float | None = None
    japan_adjusted: float | None = None
    selected: float | None = None

    model_config = ConfigDict(
        extra="forbid", str_strip_whitespace=True, populate_by_name=True
    )


class CorrectionStatus(StrictModel):
    requested: bool
    applicable: bool
    applied: bool
    fallback_reason: str | None = None
    match_count: int = Field(default=0, ge=0)
    ci80: tuple[float, float] | None = None
    ci95: tuple[float, float] | None = None


class IntervalBounds(StrictModel):
    lower: float
    upper: float


class PredictionIntervals(StrictModel):
    p50: IntervalBounds
    p80: IntervalBounds


class NextBallScenario(StrictModel):
    label: str
    runs: int = Field(ge=0)
    wicket: bool
    win_probability: float | None = Field(default=None, ge=0.0, le=1.0)


class ChaseTerminal(StrictModel):
    is_terminal: bool
    status: str | None = None
    probability: float | None = Field(default=None, ge=0.0, le=1.0)


class FirstInningsPrediction(StrictModel):
    comparison: ScorePredictionComparison
    intervals: PredictionIntervals
    correction: CorrectionStatus
    warnings: list[str] = Field(default_factory=list)


class ChasePrediction(StrictModel):
    comparison: ProbabilityPredictionComparison
    scenarios: list[NextBallScenario]
    terminal: ChaseTerminal
    correction: CorrectionStatus
    warnings: list[str] = Field(default_factory=list)


class MetadataPayload(StrictModel):
    product: str
    official_wasp_reproduction: bool
    source_sha256: str
    source_cutoff: str | None = None
    schema_version: str
    created_at: str
    bundle_role: str
    evaluation_role: str
    match_count: int = Field(ge=0)
    japan_match_count: int = Field(ge=0)
    date_from: str | None = None
    date_to: str | None = None
    selected_models: dict[str, str]
    reduced_match_enabled: bool
    counts: dict[str, int] = Field(default_factory=dict)
    row_counts: dict[str, int] = Field(default_factory=dict)
    exclusions: dict[str, int] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)


class ModelInfoPayload(StrictModel):
    schema_version: str
    bundle_role: str
    evaluation_role: str
    selected_models: dict[str, str]
    feature_schema: dict[str, list[str]]
    split: dict[str, Any] = Field(default_factory=dict)
    library_versions: dict[str, str] = Field(default_factory=dict)
    japan_gates: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)


DataT = TypeVar("DataT")


class ApiDataResponse(StrictModel, Generic[DataT]):
    data: DataT


class HealthResponse(StrictModel):
    status: Literal["ok", "degraded"]
    ready: bool
    service: str = "wasp-style"
    schema_version: str = "1.0"
    detail: str | None = None


class ApiErrorBody(StrictModel):
    code: str
    message: str
    details: Any | None = None


class ApiErrorResponse(StrictModel):
    error: ApiErrorBody
