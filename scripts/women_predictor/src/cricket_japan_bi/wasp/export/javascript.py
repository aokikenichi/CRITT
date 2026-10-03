"""Dependency-free browser runtime embedded by the standalone HTML exporter."""

from __future__ import annotations


_BROWSER_RUNTIME = r"""(function (root) {
  "use strict";

  const VERSION = "wasp-standalone-models/1.0";
  const own = (object, key) => Object.prototype.hasOwnProperty.call(object || {}, key);

  function contextOf(context) {
    const result = context && context.inference ? context.inference : context;
    if (!result || result.schema_version !== VERSION) {
      throw new Error("Unsupported standalone WASP model schema");
    }
    return result;
  }

  function pick(object, names, fallback) {
    for (const name of names) {
      if (own(object, name) && object[name] !== null && object[name] !== undefined) {
        return object[name];
      }
    }
    return fallback;
  }

  function quotaBalls(value, fallback) {
    if (value === null || value === undefined) return fallback;
    if (typeof value === "number") return Math.trunc(value);
    if (value.total_balls !== null && value.total_balls !== undefined) {
      return Math.trunc(Number(value.total_balls));
    }
    return Math.trunc(Number(value.overs || 0)) * 6 + Math.trunc(Number(value.balls || 0));
  }

  function completedBalls(input) {
    const structured = pick(input, ["completed", "current", "completed_quota"], null);
    if (structured !== null) return quotaBalls(structured, 0);
    if (input.legal_balls_bowled !== null && input.legal_balls_bowled !== undefined) {
      return Math.trunc(Number(input.legal_balls_bowled));
    }
    return Math.trunc(Number(pick(input, ["completed_overs", "overs"], 0))) * 6 +
      Math.trunc(Number(pick(input, ["completed_balls", "balls"], 0)));
  }

  function phaseAbsolute(balls) {
    return balls < 36 ? "powerplay" : balls < 96 ? "middle" : "death";
  }

  function phaseRelative(balls, limit) {
    const progress = Math.min(1, balls / limit);
    return progress < 0.30 ? "powerplay" : progress < 0.80 ? "middle" : "death";
  }

  function finiteNumber(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number : 0;
  }

  function vector(state, features) {
    return features.map((name) => finiteNumber(state[name]));
  }

  function sigmoid(value) {
    if (value >= 0) {
      const exponential = Math.exp(-value);
      return 1 / (1 + exponential);
    }
    const exponential = Math.exp(value);
    return exponential / (1 + exponential);
  }

  function treeValue(tree, values) {
    let index = 0;
    while (!tree.leaf[index]) {
      const candidate = values[tree.feature[index]];
      const left = Number.isFinite(candidate)
        ? candidate <= tree.threshold[index]
        : Boolean(tree.missing_left[index]);
      index = left ? tree.left[index] : tree.right[index];
    }
    return tree.value[index];
  }

  function hgbValue(spec, values) {
    if (values.length !== spec.n_features) throw new Error("WASP feature-count mismatch");
    let raw = spec.baseline;
    for (const tree of spec.trees) raw += treeValue(tree, values);
    if (spec.inverse_link === "identity") return raw;
    if (spec.inverse_link === "log") return Math.exp(raw);
    if (spec.inverse_link === "logit") return sigmoid(raw);
    throw new Error("Unknown HGB inverse link");
  }

  function estimatorValue(spec, values) {
    if (spec.kind === "hist_gradient_boosting") return hgbValue(spec, values);
    if (spec.kind === "standardized_logistic") {
      if (values.length !== spec.mean.length || values.length !== spec.scale.length ||
          values.length !== spec.coefficient.length) {
        throw new Error("WASP logistic feature-count mismatch");
      }
      let raw = spec.intercept;
      for (let index = 0; index < values.length; index += 1) {
        raw += ((values[index] - spec.mean[index]) / spec.scale[index]) * spec.coefficient[index];
      }
      return sigmoid(raw);
    }
    if (spec.kind === "standardized_linear") {
      if (values.length !== spec.mean.length || values.length !== spec.scale.length ||
          values.length !== spec.coefficient.length) {
        throw new Error("WASP linear feature-count mismatch");
      }
      let raw = spec.intercept;
      for (let index = 0; index < values.length; index += 1) {
        raw += ((values[index] - spec.mean[index]) / spec.scale[index]) * spec.coefficient[index];
      }
      if (spec.inverse_link === "identity") return raw;
      if (spec.inverse_link === "log") return Math.exp(raw);
      throw new Error("Unknown linear inverse link");
    }
    throw new Error("Unsupported standalone estimator");
  }

  function phase(state) {
    return String(state.phase_absolute || state.phase || phaseAbsolute(Number(state.legal_balls_bowled || 0))).toLowerCase();
  }

  function wicketBand(wickets) {
    return wickets >= 8 ? "8-10" : wickets >= 5 ? "5-7" : wickets >= 3 ? "3-4" : "0-2";
  }

  function rrrBand(value) {
    if (value === null || value === undefined || value === "") return "start";
    const rate = Number(value);
    if (!Number.isFinite(rate)) return "15+";
    return rate < 5 ? "<5" : rate < 7 ? "5-7" : rate < 9 ? "7-9" :
      rate < 11 ? "9-11" : rate < 15 ? "11-15" : "15+";
  }

  function tableLookup(level, key) {
    const encoded = JSON.stringify(key);
    for (const entry of level) {
      if (JSON.stringify(entry[0]) === encoded) return [entry[1], entry[2]];
    }
    return null;
  }

  function resourceRemaining(spec, state) {
    if (Number(state.wickets_lost || 0) >= 10 || Number(state.balls_remaining || 0) <= 0) return 0;
    const balls = Math.max(0, Math.trunc(Number(state.balls_remaining || 0)));
    const wickets = Math.max(0, Math.trunc(Number(state.wickets_remaining || 0)));
    const keys = [[], [phase(state), wicketBand(wickets)],
      [Math.floor((balls + 5) / 6), wicketBand(wickets)], [balls, wickets]];
    let prediction = spec.global_mean;
    keys.forEach((key, index) => {
      const found = tableLookup(spec.levels[index], key);
      if (!found || found[1] <= 0) return;
      const observed = found[0] / found[1];
      prediction = index === 0 ? observed :
        (found[1] * observed + spec.pseudo_count * prediction) / (found[1] + spec.pseudo_count);
    });
    return Math.max(0, prediction);
  }

  function hierarchicalProbability(spec, state) {
    const balls = Math.max(0, Math.trunc(Number(state.balls_remaining || 0)));
    const wickets = Math.max(0, Math.trunc(Number(state.wickets_remaining || 0)));
    const section = phase(state);
    const bucket = Math.floor((balls + 5) / 6);
    const keys = [[], [section], [section, bucket], [section, bucket, wickets],
      [section, bucket, wickets, rrrBand(state.required_run_rate)]];
    let prediction = spec.global_probability;
    keys.forEach((key, index) => {
      const found = tableLookup(spec.levels[index], key);
      if (!found || found[1] <= 0) return;
      const observed = found[0] / found[1];
      prediction = index === 0 ? observed :
        (found[1] * observed + spec.pseudo_count * prediction) / (found[1] + spec.pseudo_count);
    });
    return Math.min(1 - 1e-6, Math.max(1e-6, prediction));
  }

  function calibrate(value, calibrator) {
    if (!calibrator) return value;
    const clipped = Math.min(1 - 1e-6, Math.max(1e-6, Number(value)));
    const logit = Math.log(clipped / (1 - clipped));
    return sigmoid(calibrator.slope * logit + calibrator.intercept);
  }

  function firstModelValue(spec, state) {
    const runs = Number(state.runs_so_far || 0);
    if (Number(state.wickets_lost || 0) >= 10 || Number(state.balls_remaining || 0) <= 0) return runs;
    if (spec.kind === "remaining_regressor") {
      const remaining = Math.max(0, estimatorValue(spec.estimator, vector(state, spec.features)));
      return Math.max(runs, runs + remaining);
    }
    if (spec.kind === "current_run_rate") {
      const legal = Number(state.legal_balls_bowled || 0);
      if (!legal) return Math.max(runs, spec.start_score);
      const rate = Number(state.current_run_rate || runs * 6 / legal);
      return Math.max(runs, runs + rate * Number(state.balls_remaining || 0) / 6);
    }
    if (spec.kind === "resource_table") return runs + resourceRemaining(spec, state);
    throw new Error("Unknown first-innings model");
  }

  function chaseModelValue(spec, state) {
    if (spec.kind === "chase_classifier") {
      const raw = estimatorValue(spec.estimator, vector(state, spec.features));
      return Math.min(1, Math.max(0, calibrate(raw, spec.calibrator)));
    }
    if (spec.kind === "hierarchical_probability") return hierarchicalProbability(spec, state);
    throw new Error("Unknown chase model");
  }

  function terminal(score, target, wickets, balls) {
    if (target < 1) throw new Error("target must be at least 1");
    if (score >= target) return ["chase_won", 1];
    if (wickets >= 10 || balls <= 0) {
      if (score === target - 1) return ["tied_regulation", null];
      return ["chase_lost", 0];
    }
    return [null, null];
  }

  function buildState(exported, input, innings) {
    const first = innings === 1;
    const batting = String(pick(input, first ? ["batting_team", "team"] : ["chasing_team", "batting_team"], ""));
    const bowling = String(pick(input, first ? ["bowling_team", "opponent"] : ["defending_team", "bowling_team"], ""));
    const runs = Math.trunc(Number(pick(input, first ? ["runs", "runs_so_far"] : ["current_score", "runs", "runs_so_far"], 0)));
    const wickets = Math.trunc(Number(pick(input, ["wickets", "wickets_lost"], 0)));
    const quotaValue = pick(input, first ? ["quota", "innings_quota", "ball_limit"] : ["target_ball_limit", "quota", "ball_limit"], null);
    const limit = quotaBalls(quotaValue, 120);
    let legal;
    let remaining;
    if (!first && input.balls_remaining !== null && input.balls_remaining !== undefined) {
      remaining = quotaBalls(input.balls_remaining, limit);
      legal = Math.max(0, limit - remaining);
    } else {
      legal = completedBalls(input);
      remaining = Math.max(0, limit - legal);
    }
    const target = first ? null : Math.trunc(Number(pick(input, ["target", "target_runs"], 0)));
    const crr = legal ? runs * 6 / legal : 0;
    const required = target === null ? null : Math.max(0, target - runs);
    const rrr = required === null ? null : required === 0 ? 0 : remaining ? required * 6 / remaining : Infinity;
    const contexts = exported.context || {};
    const globalContext = contexts.global || {};
    const teamContexts = contexts.teams || {};
    const battingContext = own(teamContexts, batting) ? teamContexts[batting] : globalContext;
    const bowlingContext = own(teamContexts, bowling) ? teamContexts[bowling] : globalContext;
    const venue = String(input.venue || "Unknown");
    const venueContext = own(contexts.venues || {}, venue) ? contexts.venues[venue] : globalContext;
    const battingElo = Number(pick(battingContext, ["elo"], pick(globalContext, ["elo"], 1500)));
    const bowlingElo = Number(pick(bowlingContext, ["elo"], pick(globalContext, ["elo"], 1500)));
    const battingForm = Number(pick(battingContext, ["batting_form"], pick(globalContext, ["batting_form"], 0)));
    const opponentForm = Number(pick(bowlingContext, ["batting_form"], pick(globalContext, ["batting_form"], 0)));
    const battingSuppression = Number(pick(battingContext, ["bowling_suppression"], pick(globalContext, ["bowling_suppression"], 0)));
    const opponentSuppression = Number(pick(bowlingContext, ["bowling_suppression"], pick(globalContext, ["bowling_suppression"], 0)));
    const predictionDate = String(pick(input, ["prediction_date", "match_date"], exported.source_cutoff || ""));
    const defaultYear = Number(String(pick(input, ["prediction_date"], "2026")).slice(0, 4) || 2026);
    return {
      match_id: "manual", match_date: predictionDate, innings: innings,
      batting_team: batting, bowling_team: bowling, venue: venue,
      runs_so_far: runs, wickets_lost: wickets, wickets_remaining: Math.max(0, 10 - wickets),
      legal_balls_bowled: legal, balls_remaining: remaining, innings_ball_limit: limit,
      current_run_rate: crr, progress: Math.min(1, legal / limit),
      phase_absolute: phaseAbsolute(legal), phase_relative: phaseRelative(legal, limit),
      is_reduced_match: limit < 120, target: target, runs_required: required,
      required_run_rate: rrr, rrr_minus_crr: rrr === null ? null : rrr - crr,
      batting_team_won_toss: input.toss_winner ? String(input.toss_winner) === batting : null,
      elo_diff: Number(pick(input, ["elo_diff"], battingElo - bowlingElo)),
      batting_form_delta: Number(pick(input, ["batting_form_delta"], battingForm - opponentForm)),
      bowling_suppression_delta: Number(pick(input, ["bowling_suppression_delta"], battingSuppression - opponentSuppression)),
      venue_prior: Number(pick(input, ["venue_prior"], pick(venueContext, ["venue_prior"], pick(globalContext, ["venue_prior"], 0)))),
      venue_sample_count: Number(pick(input, ["venue_sample_count"], pick(venueContext, ["venue_sample_count"], 0))),
      team_cold_start: Number(!own(teamContexts, batting) || Boolean(battingContext.cold_start)),
      opponent_cold_start: Number(!own(teamContexts, bowling) || Boolean(bowlingContext.cold_start)),
      era_trend: Number(pick(input, ["era_trend"], pick(globalContext, ["era_trend"], defaultYear)))
    };
  }

  function intervalValue(interval, state, pointValue) {
    const runs = Number(state.runs_so_far || 0);
    if (Number(state.wickets_lost || 0) >= 10 || Number(state.balls_remaining || 0) <= 0) {
      return {p50: {lower: runs, upper: runs}, p80: {lower: runs, upper: runs}};
    }
    const point = Math.max(runs, Number(pointValue));
    let lower50, upper50, lower80, upper80;
    if (interval.kind === "symmetric_conformal") {
      lower50 = Math.max(runs, point - interval.radius_50);
      upper50 = Math.max(point, point + interval.radius_50);
      lower80 = Math.max(runs, Math.min(lower50, point - interval.radius_80));
      upper80 = Math.max(upper50, point + interval.radius_80);
    } else if (interval.kind === "quantile_conformal") {
      const values = vector(state, interval.features);
      const remaining = ["0.10", "0.25", "0.75", "0.90"]
        .map((key) => Math.max(0, estimatorValue(interval.models[key], values)))
        .sort((a, b) => a - b);
      lower50 = Math.max(runs, Math.min(point, runs + remaining[1] - interval.correction_50));
      upper50 = Math.max(point, runs + remaining[2] + interval.correction_50);
      lower80 = Math.max(runs, Math.min(lower50, runs + remaining[0] - interval.correction_80));
      upper80 = Math.max(upper50, runs + remaining[3] + interval.correction_80);
    } else throw new Error("Unknown interval model");
    return {p50: {lower: lower50, upper: upper50}, p80: {lower: lower80, upper: upper80}};
  }

  function warningList(exported, batting, bowling, venue) {
    const result = [];
    const teams = new Set(exported.known_teams || []);
    const venues = new Set(exported.known_venues || []);
    if (teams.size && !teams.has(batting)) result.push(batting + " は学習時に未収録のためglobal priorへfallbackしました");
    if (teams.size && !teams.has(bowling)) result.push(bowling + " は学習時に未収録のためglobal priorへfallbackしました");
    if (venues.size && !venues.has(venue)) result.push("venue未収録のためglobal venue priorへfallbackしました");
    return result;
  }

  function roleFor(state, innings) {
    if (state.batting_team === "Japan") return innings === 1 ? "japan_batting" : "japan_chasing";
    if (state.bowling_team === "Japan") return innings === 1 ? "japan_bowling" : "japan_defending";
    return null;
  }

  function applyCorrection(value, correction) {
    if (!correction || !correction.enabled) return Number(value);
    if (correction.kind === "score") return Math.max(0, Number(value) + Number(correction.offset || 0));
    return Math.min(1, Math.max(0, calibrate(Number(value), correction.calibrator)));
  }

  function correctionStatus(correction, role, requested, isTerminal) {
    const applicable = Boolean(correction);
    const applied = Boolean(requested && applicable && correction.enabled && !isTerminal);
    let fallback = null;
    if (isTerminal) fallback = "terminal_rule";
    else if (!applied) fallback = correction ? (correction.fallback_reason || "gate_not_passed") :
      (role === null ? "not_a_japan_role" : "correction_unavailable");
    return {requested: requested, applicable: applicable, applied: applied,
      fallback_reason: fallback, match_count: correction ? Number(correction.match_count || 0) : 0,
      ci80: correction && !isTerminal ? correction.ci80 : null,
      ci95: correction && !isTerminal ? correction.ci95 : null};
  }

  function unsupportedReduced() {
    const error = new Error("unsupported_reduced_match");
    error.code = "unsupported_reduced_match";
    throw error;
  }

  function predictFirst(input, context) {
    const exported = contextOf(context);
    const state = buildState(exported, input || {}, 1);
    if (state.is_reduced_match && !exported.reduced_match_enabled) unsupportedReduced();
    const globalValue = firstModelValue(exported.models.first_global, state);
    const teams = new Set(exported.known_teams || []);
    const unknown = teams.size && (!teams.has(state.batting_team) || !teams.has(state.bowling_team));
    const teamValue = unknown ? globalValue : firstModelValue(exported.models.first_team, state);
    const requested = Boolean(pick(input || {}, ["use_japan_correction", "japan_correction"], false));
    const role = roleFor(state, 1);
    const correction = role ? (exported.japan_corrections || {})[role] : null;
    const japanValue = correction ? Math.max(state.runs_so_far, applyCorrection(teamValue, correction)) : teamValue;
    const status = correctionStatus(correction, role, requested, false);
    const selected = status.applied ? japanValue : teamValue;
    return {comparison: {global: globalValue, team_adjusted: teamValue,
      japan_adjusted: japanValue, selected: selected},
      intervals: intervalValue(exported.interval, state, selected), correction: status,
      warnings: warningList(exported, state.batting_team, state.bowling_team, state.venue)};
  }

  function scenarioState(state, runs, wicket) {
    const child = Object.assign({}, state);
    child.runs_so_far = state.runs_so_far + runs;
    child.wickets_lost = state.wickets_lost + Number(wicket);
    child.wickets_remaining = Math.max(0, 10 - child.wickets_lost);
    child.balls_remaining = Math.max(0, state.balls_remaining - 1);
    child.legal_balls_bowled = state.legal_balls_bowled + 1;
    const limit = Math.max(1, Number(state.innings_ball_limit || child.legal_balls_bowled + child.balls_remaining));
    child.current_run_rate = child.legal_balls_bowled ? child.runs_so_far * 6 / child.legal_balls_bowled : 0;
    child.progress = Math.min(1, child.legal_balls_bowled / limit);
    child.phase_absolute = phaseAbsolute(child.legal_balls_bowled);
    child.phase_relative = phaseRelative(child.legal_balls_bowled, limit);
    child.runs_required = Math.max(0, state.target - child.runs_so_far);
    child.required_run_rate = child.runs_required && child.balls_remaining ?
      child.runs_required * 6 / child.balls_remaining : child.runs_required === 0 ? 0 : Infinity;
    child.rrr_minus_crr = child.required_run_rate - child.current_run_rate;
    return child;
  }

  function predictChase(input, context) {
    const exported = contextOf(context);
    const state = buildState(exported, input || {}, 2);
    if (state.is_reduced_match && !exported.reduced_match_enabled) unsupportedReduced();
    const ending = terminal(state.runs_so_far, state.target, state.wickets_lost, state.balls_remaining);
    const requested = Boolean(pick(input || {}, ["use_japan_correction", "japan_correction"], false));
    const role = roleFor(state, 2);
    const correction = role ? (exported.japan_corrections || {})[role] : null;
    const warnings = warningList(exported, state.batting_team, state.bowling_team, state.venue);
    if (ending[0] !== null) {
      return {comparison: {global: ending[1], team_adjusted: ending[1], japan_adjusted: ending[1], selected: ending[1]},
        scenarios: [], terminal: {is_terminal: true, status: ending[0], probability: ending[1]},
        correction: correctionStatus(correction, role, requested, true), warnings: warnings};
    }
    const globalValue = chaseModelValue(exported.models.chase_global, state);
    const unknownToss = ![state.batting_team, state.bowling_team].includes(input.toss_winner);
    if (unknownToss) {
      state.batting_team_won_toss = null;
      warnings.push("トス結果が不明のため、チーム補正モデルではなくglobalモデルを使用しました");
    }
    const teams = new Set(exported.known_teams || []);
    const unknown = teams.size && (!teams.has(state.batting_team) || !teams.has(state.bowling_team));
    const model = unknown || unknownToss ? exported.models.chase_global : exported.models.chase_team;
    const teamValue = unknown || unknownToss ? globalValue : chaseModelValue(model, state);
    const japanValue = correction && !unknownToss ? applyCorrection(teamValue, correction) : teamValue;
    const status = correctionStatus(correction, role, requested, false);
    if (unknownToss && status.applied) {
      status.applied = false;
      status.fallback_reason = "unknown_toss";
      status.ci80 = null;
      status.ci95 = null;
    }
    const selected = status.applied ? japanValue : teamValue;
    const scenarios = [["0 runs", 0, false], ["1 run", 1, false], ["2 runs", 2, false],
      ["3 runs", 3, false], ["4 runs", 4, false], ["6 runs", 6, false], ["wicket", 0, true]]
      .map((item) => {
        const child = scenarioState(state, item[1], item[2]);
        const childEnding = terminal(child.runs_so_far, child.target, child.wickets_lost, child.balls_remaining);
        let probability = childEnding[0] === null ? chaseModelValue(model, child) : childEnding[1];
        if (status.applied && correction && probability !== null) probability = applyCorrection(probability, correction);
        return {label: item[0], runs: item[1], wicket: item[2], win_probability: probability};
      });
    return {comparison: {global: globalValue, team_adjusted: teamValue,
      japan_adjusted: japanValue, selected: selected}, scenarios: scenarios,
      terminal: {is_terminal: false, status: null, probability: null}, correction: status,
      warnings: warnings};
  }

  root.WASPStandalonePredictor = Object.freeze({
    version: VERSION,
    predictFirst: predictFirst,
    predictChase: predictChase,
    buildState: function (input, context, innings) { return buildState(contextOf(context), input || {}, innings); }
  });
})(typeof globalThis !== "undefined" ? globalThis : window);
"""


def browser_runtime_source() -> str:
    """Return JavaScript defining ``globalThis.WASPStandalonePredictor``.

    The source contains no network calls, dynamic imports, ``eval`` or external
    dependencies and is safe to inline in a ``file://`` standalone document.
    """

    return _BROWSER_RUNTIME


__all__ = ["browser_runtime_source"]
