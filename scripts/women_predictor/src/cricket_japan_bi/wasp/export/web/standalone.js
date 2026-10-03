"use strict";

(function () {
  const COLORS = {
    green: "#0b6b4f", lime: "#bed85c", orange: "#e46d3c",
    blue: "#31688e", muted: "#68746c", grid: "#dfe3dc", ink: "#24332b"
  };
  const ROUTES = new Set(["overview", "first", "chase", "replay", "evaluation"]);
  const canvasDisplayHeights = new WeakMap();
  const q = (selector, root) => (root || document).querySelector(selector);
  const qa = (selector, root) => Array.from((root || document).querySelectorAll(selector));
  const rawData = readEmbeddedData();
  const predictor = globalThis.WASPStandalonePredictor;
  const data = normalizePayload(rawData);
  let selectedMatchId = null;
  let lastFirstHistory = readHistory();
  let lastScenarios = [];

  function readEmbeddedData() {
    try {
      const node = q("#wasp-standalone-data");
      const parsed = JSON.parse(node ? node.textContent : "{}");
      return parsed && typeof parsed === "object" ? parsed : {};
    } catch (error) {
      setTimeout(function () { showError("埋め込みデータを読み込めませんでした。", error.message); }, 0);
      return {};
    }
  }

  function normalizePayload(raw) {
    const metadata = raw.metadata || raw.model_metadata || {};
    const evaluation = raw.evaluation || raw.metrics || {};
    const matches = Array.isArray(raw.japan_matches) ? raw.japan_matches :
      (Array.isArray(raw.matches) ? raw.matches : []);
    const contexts = raw.contexts || raw.context || {};
    const models = metadata.selected_models || (raw.model_info && raw.model_info.selected_models) ||
      raw.display_models || metadata.models || raw.models || {};
    const teams = unique((raw.known_teams || (raw.options && raw.options.teams) || []).concat(
      matches.reduce(function (all, match) { return all.concat(matchTeams(match)); }, [])
    )).sort(localeCompare);
    const venues = unique((raw.known_venues || (raw.options && raw.options.venues) || []).concat(
      matches.map(function (match) { return match.venue; }).filter(Boolean)
    )).sort(localeCompare);
    return {
      raw: raw, metadata: metadata, evaluation: evaluation, matches: matches,
      replays: raw.replays || {}, contexts: contexts, models: models,
      teams: teams, venues: venues, gates: normalizeGates(raw, evaluation)
    };
  }

  function normalizeGates(raw, evaluation) {
    const labels = {
      batting: "日本の打撃", japan_batting: "日本の打撃",
      bowling: "日本のボウリング", japan_bowling: "日本のボウリング",
      chasing: "日本の追走", japan_chasing: "日本の追走",
      defending: "日本の守備", japan_defending: "日本の守備"
    };
    let source = raw.japan_gates || (raw.gates && raw.gates.japan) ||
      (evaluation.japan && evaluation.japan.gates) || {};
    const gates = [];
    if (Array.isArray(source)) {
      source.forEach(function (gate, index) {
        const key = gate.role || gate.name || String(index);
        gates.push(normalizeGate(key, gate, labels[key]));
      });
    } else if (source && typeof source === "object") {
      Object.keys(source).forEach(function (key) {
        gates.push(normalizeGate(key, source[key], labels[key]));
      });
    }
    const reducedSource = raw.reduced_match_gate || (raw.gates && raw.gates.reduced) ||
      evaluation.reduced_gate || raw.reduced_match_enabled;
    if (reducedSource !== undefined) {
      gates.push(normalizeGate("reduced", reducedSource, "短縮戦の手動予測"));
    }
    return gates;
  }

  function normalizeGate(key, value, fallbackLabel) {
    const gate = value && typeof value === "object" ? value : { enabled: Boolean(value) };
    const enabled = Boolean(gate.enabled ?? gate.applied ?? gate.passed ?? gate.pass ?? gate.active);
    return {
      key: key,
      label: gate.label || fallbackLabel || key,
      enabled: enabled,
      reason: gateReason(gate.reason || gate.fallback_reason || gate.status_reason, enabled),
      historyCount: number(gate.history_match_count ?? gate.history_matches ?? gate.match_count),
      gateCount: number(gate.gate_match_count ?? gate.activation_match_count ?? (gate.gate_details && gate.gate_details.gate_matches)),
      raw: gate
    };
  }

  function gateReason(reason, enabled) {
    const translations = {
      activation_gate_failed: "activation期間で精度改善を確認できませんでした。",
      insufficient_history: "補正の学習に必要な過去試合数が不足しています。",
      insufficient_gate_matches: "activation判定に必要な試合数が不足しています。",
      insufficient_first_innings_reduced_cohort: "信頼できる短縮第1イニングの検証試合が不足しています。",
      validation_gate_failed: "validation期間で安定した精度改善を確認できませんでした。"
    };
    if (!reason) return enabled ? "有効化条件を満たしています。" : "有効化条件を満たしていません。";
    return translations[reason] || String(reason).replace(/_/g, " ");
  }

  function initialize() {
    populateOptions();
    renderOverview();
    renderEvaluation();
    bindRouting();
    bindFirstForm();
    bindChaseForm();
    bindReplay();
    renderFirstHistory();
    renderReplayList();
    const generated = data.metadata.generated_at || rawData.generated_at;
    q("#generated-at").textContent = generated ? "最終更新 " + formatDateTime(generated) : "オフライン書き出し";
    q("#data-cutoff").textContent = data.metadata.source_cutoff || data.metadata.date_to || "—";
    if (data.metadata.replay_note) q("#replay-model-note").textContent = data.metadata.replay_note;
    if (!predictor || typeof predictor.predictFirst !== "function" || typeof predictor.predictChase !== "function") {
      showError("予測モデルを読み込めませんでした。", "このHTMLを書き出し直してください。");
      qa("form button[type='submit']").forEach(function (button) { button.disabled = true; });
    }
    window.addEventListener("resize", debounce(redrawVisibleCharts, 120));
    showRoute(routeFromHash(), false);
  }

  function bindRouting() {
    window.addEventListener("hashchange", function () { showRoute(routeFromHash(), true); });
    qa("[data-route]").forEach(function (link) {
      link.addEventListener("click", function (event) {
        const route = link.dataset.route;
        if (!ROUTES.has(route)) return;
        if (routeFromHash() === route) {
          event.preventDefault();
          showRoute(route, true);
        }
      });
    });
  }

  function routeFromHash() {
    const route = location.hash.replace(/^#/, "");
    return ROUTES.has(route) ? route : "overview";
  }

  function showRoute(route, focusMain) {
    clearError();
    qa("[data-view]").forEach(function (section) { section.hidden = section.dataset.view !== route; });
    qa("nav [data-route]").forEach(function (link) {
      if (link.dataset.route === route) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
    document.title = routeTitle(route) + " | Japan Women T20 WASP-style Lab";
    if (focusMain) q("#main-content").focus({ preventScroll: true });
    requestAnimationFrame(function () {
      if (route === "first") renderFirstHistory();
      if (route === "chase" && lastScenarios.length) renderScenarios(lastScenarios);
      if (route === "replay" && selectedMatchId) renderReplay(selectedMatchId);
      if (route === "evaluation") drawEvaluationCharts();
    });
  }

  function routeTitle(route) {
    return { overview: "概要", first: "第1イニング予測", chase: "追走予測", replay: "試合リプレイ", evaluation: "モデル評価" }[route];
  }

  function populateOptions() {
    q("#team-options").innerHTML = data.teams.map(function (team) { return "<option value=\"" + escAttr(team) + "\"></option>"; }).join("");
    q("#venue-options").innerHTML = data.venues.map(function (venue) { return "<option value=\"" + escAttr(venue) + "\"></option>"; }).join("");
  }

  function renderOverview() {
    const metadata = data.metadata;
    const counts = metadata.counts || metadata.audit || {};
    const evaluation = evaluationParts(data.evaluation);
    const firstMetrics = evaluation.first.locked_test || {};
    const chaseMetrics = evaluation.chase.locked_test || {};
    const matchCount = counts.matches ?? metadata.match_count ?? rawData.match_count;
    const japanCount = counts.japan_matches ?? metadata.japan_match_count ?? data.matches.length;
    const deliveryCount = counts.deliveries ?? (metadata.row_counts && metadata.row_counts.deliveries);
    const legalBallCount = counts.legal_balls;
    const teamCount = counts.teams ?? data.teams.length;
    q("#overview-data-text").textContent = "Cricsheetが公開する女子T20 Internationalのball-by-ballデータを使用しています。収録期間は" +
      (metadata.period || "—") + "。" + fmt(matchCount, 0) + "試合、" + fmt(deliveryCount, 0) +
      " deliveries（うち" + fmt(legalBallCount, 0) + "合法球）、" + fmt(teamCount, 0) +
      "チームを含み、このうち日本女子代表戦は" + fmt(japanCount, 0) + "試合です。";
    q("#summary-cards").innerHTML = [
      metricCard("女子T20試合", fmt(matchCount, 0), metadata.period || ""),
      metricCard("deliveries", fmt(deliveryCount, 0), "ball-by-ball"),
      metricCard("収録チーム", fmt(teamCount, 0), "女子T20"),
      metricCard("日本女子代表戦", fmt(japanCount, 0), "収録試合")
    ].join("");
    const summary = data.evaluation.summary || {};
    q("#overview-evaluation").innerHTML = '<div class="comparison-grid">' +
      comparisonItem("先攻 MAE", fmt(summary.first_mae ?? firstMetrics.match_macro_mae ?? firstMetrics.mae)) +
      comparisonItem("追走 Brier", fmt(summary.chase_brier ?? chaseMetrics.match_macro_brier ?? chaseMetrics.brier, 3)) +
      comparisonItem("追走 ECE", fmt(summary.chase_ece ?? chaseMetrics.ece, 3)) + "</div>";
  }

  function bindFirstForm() {
    q("#first-form").addEventListener("submit", async function (event) {
      event.preventDefault();
      clearError();
      markFormValid(event.currentTarget);
      try {
        const input = readFirstInput(event.currentTarget);
        const warnings = categoryWarnings(input.batting_team, input.bowling_team, input.venue);
        const result = await callPredictor("predictFirst", input, "first_innings");
        renderFirstResult(result, warnings);
        const comparison = result.comparison || {};
        const selected = predictionValue(comparison.selected ?? result.selected ?? result.predicted_score ?? result.predicted_final_score);
        lastFirstHistory.push({ balls: quotaToBalls(input.completed), current: input.runs, selected: selected, at: Date.now() });
        lastFirstHistory = lastFirstHistory.slice(-40);
        writeHistory(lastFirstHistory);
        renderFirstHistory();
      } catch (error) { handleFormError(event.currentTarget, error); }
    });
    q("#clear-first-history").addEventListener("click", function () {
      lastFirstHistory = [];
      writeHistory(lastFirstHistory);
      renderFirstHistory();
    });
  }

  function readFirstInput(form) {
    const values = new FormData(form);
    const input = {
      batting_team: textValue(values, "batting_team"),
      bowling_team: textValue(values, "bowling_team"),
      runs: integerValue(values, "runs"), wickets: integerValue(values, "wickets"),
      completed: { overs: integerValue(values, "completed_overs"), balls: integerValue(values, "completed_balls") },
      quota: { overs: integerValue(values, "quota_overs"), balls: integerValue(values, "quota_balls") },
      venue: optionalText(values, "venue"), use_japan_correction: values.has("use_japan_correction")
    };
    requireTeams(input.batting_team, input.bowling_team, "batting_team", "bowling_team");
    requireRange(input.runs, 0, Number.MAX_SAFE_INTEGER, "runs", "現在得点");
    requireRange(input.wickets, 0, 10, "wickets", "wicket");
    validateQuota(input.completed, "completed", "完了した合法球");
    validateQuota(input.quota, "quota", "イニングquota");
    const completedBalls = quotaToBalls(input.completed);
    const quotaBalls = quotaToBalls(input.quota);
    if (quotaBalls < 1 || quotaBalls > 120) throw validationError("quota_overs", "quotaは1〜120合法球で入力してください。");
    if (completedBalls > quotaBalls) throw validationError("completed_overs", "完了合法球はquotaを超えられません。");
    ensureReducedSupported(quotaBalls);
    return input;
  }

  function renderFirstResult(result, categoryNotices) {
    const comparison = result.comparison || {};
    const selected = predictionValue(comparison.selected ?? result.selected ?? result.predicted_score ?? result.predicted_final_score);
    if (number(selected) === null) throw new Error("モデルが最終得点を返しませんでした。");
    const intervals = firstIntervals(result);
    q("#first-empty").hidden = true;
    q("#first-results").hidden = false;
    q("#first-selected").textContent = fmt(selected);
    q("#first-interval").textContent = "50% " + intervalText(intervals.p50) + " ／ 80% " + intervalText(intervals.p80);
    q("#first-comparison").innerHTML = comparisonHtml(comparison, fmt, firstComparisonLabels());
    q("#first-correction").textContent = correctionText(result.correction || result.correction_status);
    renderWarnings(q("#first-warnings"), Array.isArray(result.warnings) && result.warnings.length ? result.warnings : categoryNotices);
  }

  function bindChaseForm() {
    q("#chase-form").addEventListener("submit", async function (event) {
      event.preventDefault();
      clearError();
      markFormValid(event.currentTarget);
      try {
        const input = readChaseInput(event.currentTarget);
        const warnings = categoryWarnings(input.chasing_team, input.defending_team, input.venue);
        const result = await callPredictor("predictChase", input, "chase");
        renderChaseResult(result, warnings, input);
        const terminal = terminalState(result, input);
        if (!terminal.is_terminal) {
          lastScenarios = await resolveScenarios(result, input);
          renderScenarios(lastScenarios);
        } else {
          lastScenarios = [];
          q("#scenario-empty").hidden = false;
          q("#scenario-empty").textContent = "終端状態のため次球シナリオはありません。";
          q("#scenario-content").hidden = true;
        }
      } catch (error) { handleFormError(event.currentTarget, error); }
    });
  }

  function readChaseInput(form) {
    const values = new FormData(form);
    const input = {
      chasing_team: textValue(values, "chasing_team"),
      defending_team: textValue(values, "defending_team"),
      target: integerValue(values, "target"), current_score: integerValue(values, "current_score"),
      wickets: integerValue(values, "wickets"), balls_remaining: integerValue(values, "balls_remaining"),
      target_ball_limit: { overs: integerValue(values, "limit_overs"), balls: integerValue(values, "limit_balls") },
      venue: optionalText(values, "venue"), use_japan_correction: values.has("use_japan_correction")
    };
    requireTeams(input.chasing_team, input.defending_team, "chasing_team", "defending_team");
    const tossChoice = values.get("toss_winner");
    input.toss_winner = tossChoice === "chasing" ? input.chasing_team : tossChoice === "defending" ? input.defending_team : null;
    requireRange(input.target, 1, Number.MAX_SAFE_INTEGER, "target", "target");
    requireRange(input.current_score, 0, Number.MAX_SAFE_INTEGER, "current_score", "現在得点");
    requireRange(input.wickets, 0, 10, "wickets", "wicket");
    validateQuota(input.target_ball_limit, "limit", "target制限球数");
    const limit = quotaToBalls(input.target_ball_limit);
    if (limit < 1 || limit > 120) throw validationError("limit_overs", "target制限球数は1〜120合法球で入力してください。");
    requireRange(input.balls_remaining, 0, limit, "balls_remaining", "残り合法球");
    ensureReducedSupported(limit);
    return input;
  }

  function renderChaseResult(result, categoryNotices, input) {
    const comparison = result.comparison || {};
    const terminal = terminalState(result, input);
    let selected = probability(comparison.selected ?? result.selected ?? result.win_probability ?? terminal.probability);
    if (terminal.status === "tied_regulation") selected = null;
    q("#chase-empty").hidden = true;
    q("#chase-results").hidden = false;
    q("#chase-selected").textContent = pct(selected);
    q("#chase-ring").style.setProperty("--probability", selected === null ? 0 : selected * 100);
    q("#chase-ring").classList.toggle("is-unavailable", selected === null);
    q("#chase-comparison").innerHTML = comparisonHtml(comparison, pct, input.toss_winner ? {} : { team_adjusted: "チーム補正（未使用）" });
    q("#chase-correction").textContent = correctionText(result.correction || result.correction_status);
    q("#chase-terminal").hidden = !terminal.is_terminal;
    q("#chase-terminal").textContent = terminalText(terminal);
    renderWarnings(q("#chase-warnings"), Array.isArray(result.warnings) && result.warnings.length ? result.warnings : categoryNotices);
  }

  async function resolveScenarios(result, input) {
    if (Array.isArray(result.scenarios) && result.scenarios.length) return result.scenarios;
    if (typeof predictor.predictNextBallScenarios === "function") {
      const response = await Promise.resolve(predictor.predictNextBallScenarios(input, rawData, contextFor("chase")));
      return Array.isArray(response) ? response : (response.scenarios || []);
    }
    const definitions = [
      { label: "0 run", runs: 0 }, { label: "1 run", runs: 1 }, { label: "2 runs", runs: 2 },
      { label: "3 runs", runs: 3 }, { label: "Four", runs: 4 }, { label: "Six", runs: 6 },
      { label: "0 + wicket", runs: 0, wicket: true }
    ];
    return Promise.all(definitions.map(async function (definition) {
      const state = Object.assign({}, input, {
        current_score: input.current_score + definition.runs,
        wickets: Math.min(10, input.wickets + (definition.wicket ? 1 : 0)),
        balls_remaining: Math.max(0, input.balls_remaining - 1),
        include_scenarios: false
      });
      const scenarioResult = await callPredictor("predictChase", state, "chase");
      const comparison = scenarioResult.comparison || {};
      const terminal = terminalState(scenarioResult, state);
      return Object.assign({}, definition, {
        win_probability: comparison.selected ?? scenarioResult.selected ?? scenarioResult.win_probability ?? terminal.probability,
        terminal: terminal
      });
    }));
  }

  function renderScenarios(scenarios) {
    q("#scenario-empty").hidden = true;
    q("#scenario-content").hidden = false;
    const normalized = scenarios.map(function (item, index) {
      return {
        label: item.label || (item.wicket ? "0 + wicket" : String(item.runs ?? index) + " runs"),
        value: probability(item.win_probability ?? item.probability ?? item.selected),
        wicket: Boolean(item.wicket)
      };
    });
    drawBarChart(q("#scenario-chart"), normalized);
    q("#scenario-table").innerHTML = '<table><caption>各シナリオは次の1合法球が終わった直後の推定です。</caption><thead><tr><th>次球結果</th><th class="numeric">追走成功推定</th></tr></thead><tbody>' +
      normalized.map(function (item) { return "<tr><td>" + esc(item.label) + "</td><td class=\"numeric\">" + pct(item.value) + "</td></tr>"; }).join("") +
      "</tbody></table>";
  }

  function terminalState(result, input) {
    const provided = result.terminal || {};
    if (provided.is_terminal || result.terminal_status) {
      const status = provided.status || result.terminal_status;
      return { is_terminal: true, status: status, probability: probability(provided.probability ?? result.win_probability) };
    }
    if (input.current_score >= input.target) return { is_terminal: true, status: "chase_won", probability: 1 };
    if (input.wickets >= 10 || input.balls_remaining <= 0) {
      if (input.current_score === input.target - 1) return { is_terminal: true, status: "tied_regulation", probability: null };
      return { is_terminal: true, status: "chase_lost", probability: 0 };
    }
    return { is_terminal: false, status: null, probability: null };
  }

  function terminalText(terminal) {
    if (!terminal.is_terminal) return "";
    if (terminal.status === "tied_regulation") return "規定tieのため、v1の二値確率は返しません。";
    if (["chase_won", "won", "win", "target_reached"].includes(terminal.status)) return "target到達：追走成功が確定した終端状態です。";
    if (["chase_lost", "lost", "loss", "all_out", "balls_exhausted"].includes(terminal.status)) return "追走失敗が確定した終端状態です。";
    return "終端状態：" + String(terminal.status || "確定");
  }

  function callPredictor(method, input, contextName) {
    if (!predictor || typeof predictor[method] !== "function") return Promise.reject(new Error("予測モデルが利用できません。"));
    return Promise.resolve(predictor[method](input, rawData, contextFor(contextName))).then(function (result) {
      if (!result || typeof result !== "object") throw new Error("予測結果の形式が正しくありません。");
      return result;
    });
  }

  function contextFor(name) {
    return data.contexts[name] || data.contexts[name === "first_innings" ? "first" : name] || data.contexts;
  }

  function bindReplay() {
    ["#replay-query", "#replay-from-date", "#replay-to-date", "#replay-japan-only"].forEach(function (selector) {
      q(selector).addEventListener(selector === "#replay-query" ? "input" : "change", renderReplayList);
    });
    q("#match-list").addEventListener("click", function (event) {
      const button = event.target.closest(".match-button");
      if (!button) return;
      selectedMatchId = button.dataset.matchId;
      renderReplay(selectedMatchId);
      qa(".match-button", q("#match-list")).forEach(function (item) {
        if (item.dataset.matchId === selectedMatchId) item.setAttribute("aria-current", "true");
        else item.removeAttribute("aria-current");
      });
    });
  }

  function renderReplayList() {
    const query = q("#replay-query").value.trim().toLocaleLowerCase("ja-JP");
    const fromDate = q("#replay-from-date").value;
    const toDate = q("#replay-to-date").value;
    const japanOnly = q("#replay-japan-only").checked;
    const filtered = data.matches.filter(function (match) {
      const teams = matchTeams(match);
      const haystack = teams.concat([match.venue, match.date, match.match_date, match.result, match.winner]).filter(Boolean).join(" ").toLocaleLowerCase("ja-JP");
      const date = String(match.date || match.match_date || "").slice(0, 10);
      const isJapan = match.is_japan !== undefined ? Boolean(match.is_japan) : teams.some(function (team) { return normalizeName(team) === "japan"; });
      return (!query || haystack.includes(query)) && (!fromDate || date >= fromDate) && (!toDate || date <= toDate) && (!japanOnly || isJapan);
    }).sort(function (left, right) { return String(right.date || right.match_date || "").localeCompare(String(left.date || left.match_date || "")); });
    q("#match-count").textContent = fmt(filtered.length, 0) + "試合";
    q("#match-list").innerHTML = filtered.length ? filtered.map(function (match, index) {
      const id = String(match.match_id ?? match.id ?? index);
      const teams = matchTeams(match);
      const current = id === selectedMatchId ? ' aria-current="true"' : "";
      return '<button class="match-button" type="button" data-match-id="' + escAttr(id) + '"' + current + '><strong>' +
        esc(teams.length ? teams.join(" vs ") : "対戦カード不明") + "</strong><span>" +
        esc(String(match.date || match.match_date || "日付不明").slice(0, 10)) + " · " + esc(match.venue || "会場不明") +
        "</span>" + ((match.first_innings_eligible === false || match.chase_eligible === false) ?
          "<span>" + esc(replayEligibilityLabel(match)) + "</span>" : "") + "</button>";
    }).join("") : '<p class="empty-state">条件に合う試合はありません。</p>';
    if (selectedMatchId && !filtered.some(function (match, index) { return String(match.match_id ?? match.id ?? index) === selectedMatchId; })) {
      selectedMatchId = null;
      q("#replay-empty").hidden = false;
      q("#replay-detail").hidden = true;
    }
  }

  function renderReplay(matchId) {
    const match = data.matches.find(function (item, index) { return String(item.match_id ?? item.id ?? index) === String(matchId); });
    if (!match) return;
    let replay = data.replays[String(matchId)] || match.replay || match;
    if (replay && replay.data && typeof replay.data === "object") replay = replay.data;
    const teams = matchTeams(match).length ? matchTeams(match) : matchTeams(replay);
    const replayBody = replay.replay || replay;
    const allPoints = Array.isArray(replayBody.points) ? replayBody.points : [];
    const first = pointArray(replayBody.first_innings || replayBody.first || (replayBody.innings && (replayBody.innings[0] || replayBody.innings["1"]))) ||
      allPoints.filter(function (point) { return Number(point.innings) === 1; });
    const chase = pointArray(replayBody.chase || replayBody.second_innings || (replayBody.innings && (replayBody.innings[1] || replayBody.innings["2"]))) ||
      allPoints.filter(function (point) { return Number(point.innings) === 2; });
    q("#replay-empty").hidden = true;
    q("#replay-detail").hidden = false;
    q("#replay-title").textContent = teams.length ? teams.join(" vs ") : "対戦カード不明";
    q("#replay-date").textContent = String(match.date || match.match_date || replay.date || replay.match_date || "").slice(0, 10);
    q("#replay-venue").textContent = match.venue || replay.venue || "会場不明";
    q("#replay-result").textContent = resultText(match.result || replay.result, match.winner || replay.winner);
    renderReplayEligibility(match);
    drawReplayFirst(q("#replay-first-chart"), first);
    drawReplayChase(q("#replay-chase-chart"), chase);
    const lastFirst = first[first.length - 1] || {};
    const lastChase = chase[chase.length - 1] || {};
    q("#replay-accessible-summary").textContent = "第1イニング " + first.length + "状態、最終得点 " + fmt(pointScore(lastFirst), 0) +
      "。第2イニング " + chase.length + "状態、最終得点 " + fmt(pointScore(lastChase), 0) +
      "、最終追走成功推定 " + pct(pointProbability(lastChase)) + "。" + replayEligibilityLabel(match);
  }

  function replayEligibilityLabel(match) {
    if (match.first_innings_eligible === true && match.chase_eligible === true) return "通常モデル対象";
    if (match.first_innings_eligible === false || match.chase_eligible === false) return "通常モデルの対象外を含む";
    return "対象判定情報なし";
  }

  function renderReplayEligibility(match) {
    const target = q("#replay-eligibility");
    target.replaceChildren();
    target.hidden = match.first_innings_eligible !== false && match.chase_eligible !== false;
    if (target.hidden) return;
    const heading = document.createElement("strong");
    heading.textContent = "学習・評価対象の判定";
    target.appendChild(heading);
    const body = document.createElement("div");
    target.appendChild(body);
    const exclusions = Array.isArray(match.model_exclusions) ? match.model_exclusions : [];
    [
      { scope: "first_innings", field: "first_innings_eligible", label: "第1イニング" },
      { scope: "chase_full_20", field: "chase_eligible", label: "第2イニング" }
    ].forEach(function (entry) {
      const eligible = match[entry.field];
      const reasons = exclusions.filter(function (item) { return item.model_scope === entry.scope; });
      const reasonText = reasons.map(function (item) { return replayExclusionReason(item.reason); }).join("、");
      const text = document.createElement("p");
      if (eligible === true) {
        text.textContent = entry.label + "：通常モデルの学習・評価対象です。";
      } else if (eligible === false) {
        const reducedSupported = entry.scope === "chase_full_20" && match.reduced_match_eligible === true && rawData.reduced_match_enabled === true;
        text.textContent = entry.label + "：通常モデル対象外" + (reasonText ? "（" + reasonText + "）" : "") + "。" +
          (reducedSupported ? "有効化済みの短縮戦モデルによる推定を表示します。" : "推定を表示せず、実得点とイベントを表示します。") +
          (entry.scope === "chase_full_20" && match.reduced_match_eligible === true && !reducedSupported ? "短縮戦のactivation gateは無効です。" : "");
      } else {
        text.textContent = entry.label + "：対象判定情報がありません。";
      }
      body.appendChild(text);
    });
  }

  function replayExclusionReason(reason) {
    const labels = {
      dls: "D/L・DLS", awarded: "awarded", no_result: "no result", super_over: "Super Over",
      tie: "規定tie", bowl_out: "bowl-out", reduced_target: "120球未満のtarget",
      nonstandard_scheduled_quota: "標準20 over・6球以外のquota",
      missing_first_innings: "第1イニング未収録", not_two_main_innings: "通常の2イニングが未収録",
      missing_target: "target不明", suspected_revised_target: "改定targetの疑い",
      unknown_dismissal_kind: "dismissal種別不明", overlong_innings: "quotaを超過したイニング",
      unknown_first_innings_end: "第1イニング終了理由不明", unknown_chase_end: "追走終了理由不明"
    };
    return labels[reason] || String(reason || "対象条件外").replace(/_/g, " ");
  }

  function pointArray(value) {
    if (Array.isArray(value)) return value;
    if (value && Array.isArray(value.points)) return value.points;
    return null;
  }

  function drawReplayFirst(canvas, points) {
    const hasPrediction = points.some(function (point) { return pointFirstPrediction(point) !== null; });
    q("#replay-first-chart-title").textContent = hasPrediction ? "第1イニング 最終得点推定" : "第1イニング 実得点の推移";
    canvas.setAttribute("aria-label", hasPrediction ? "第1イニングの得点と最終得点推定" : "第1イニングの実得点。予測は対象外のため非表示");
    if (!points.length) { drawEmptyCanvas(canvas, "第1イニングのリプレイデータがありません。"); return; }
    const series = [
      { name: "推定最終得点", color: COLORS.green, width: 3, values: points.map(function (item) { return xy(pointBall(item), pointFirstPrediction(item)); }) },
      { name: "実得点", color: COLORS.orange, width: 2, values: points.map(function (item) { return xy(pointBall(item), pointScore(item)); }) }
    ];
    drawLineChart(canvas, series, { xLabel: "完了合法球", yLabel: "得点", yMin: 0, events: pointEvents(points, false) });
  }

  function drawReplayChase(canvas, points) {
    const hasPrediction = points.some(function (point) { return pointProbability(point) !== null; });
    q("#replay-chase-chart-title").textContent = hasPrediction ? "第2イニング 追走成功確率" : "第2イニング 実得点の推移";
    canvas.setAttribute("aria-label", hasPrediction ? "第2イニングの追走成功推定" : "第2イニングの実得点。予測は対象外のため非表示");
    if (!points.length) { drawEmptyCanvas(canvas, "第2イニングのリプレイデータがありません。"); return; }
    if (!hasPrediction) {
      drawLineChart(canvas, [{ name: "実得点", color: COLORS.orange, width: 2, values: points.map(function (item) { return xy(pointBall(item), pointScore(item)); }) }],
        { xLabel: "完了合法球", yLabel: "得点", yMin: 0, events: pointEvents(points, false) });
      return;
    }
    const series = [{ name: "追走成功推定", color: COLORS.blue, width: 3, values: points.map(function (item) { return xy(pointBall(item), pointProbability(item)); }) }];
    drawLineChart(canvas, series, { xLabel: "完了合法球", yLabel: "確率", yMin: 0, yMax: 1, percent: true, events: pointEvents(points, true) });
  }

  function pointEvents(points, probabilityAxis) {
    return points.map(function (point) {
      const event = String(point.event || point.previous_event || point.previous_event_type || "").toLowerCase();
      let kind = null;
      if (event.includes("wicket")) kind = "wicket";
      else if (event.includes("six")) kind = "six";
      else if (event.includes("four")) kind = "four";
      if (!kind) return null;
      return { x: pointBall(point), y: probabilityAxis ? pointProbability(point) : pointScore(point), kind: kind };
    }).filter(Boolean);
  }

  function pointBall(item) { return number(item.legal_balls_bowled ?? item.legal_balls ?? item.ball ?? item.state_sequence); }
  function pointScore(item) { return number(item.runs_so_far ?? item.runs ?? item.score ?? item.current_score); }
  function pointFirstPrediction(item) { return number(item.selected ?? item.predicted_final_score ?? item.predicted_score ?? item.point_estimate); }
  function pointProbability(item) { return probability(item.selected ?? item.win_probability ?? item.probability); }

  function renderEvaluation() {
    const parts = evaluationParts(data.evaluation);
    const firstMetrics = parts.first.locked_test || {};
    const chaseMetrics = parts.chase.locked_test || {};
    const summary = data.evaluation.summary || {};
    q("#evaluation-cards").innerHTML = [
      metricCard("第1 innings MAE", fmt(summary.first_mae ?? firstMetrics.match_macro_mae ?? firstMetrics.mae), "match-macro"),
      metricCard("第1 innings RMSE", fmt(summary.first_rmse ?? firstMetrics.match_macro_rmse ?? firstMetrics.rmse), "locked test"),
      metricCard("追走 Brier", fmt(summary.chase_brier ?? chaseMetrics.match_macro_brier ?? chaseMetrics.brier, 3), "低いほど良い"),
      metricCard("追走 ECE", fmt(summary.chase_ece ?? chaseMetrics.ece, 3), "equal-mass 10 bins")
    ].join("");
    renderPhaseTable(parts);
    renderCandidateTable(parts);
    const limitations = data.metadata.limitations || data.evaluation.limitations || [
      "D/L・DLS、規定tie、Super Overはv1安定版の学習対象外です。",
      "収録範囲外のチーム・会場ではglobal priorへ戻ります。",
      "このHTMLは学習を行いません。モデル更新時はPythonから再書き出しが必要です。"
    ];
    // The plain-language overview note replaces the repeated inactive status.
    const visibleLimitations = limitations.filter(function (item) {
      return !/^Japan correction\b/.test(String(item));
    });
    q("#model-limitations").innerHTML = visibleLimitations.map(function (item) { return "<li>" + esc(item) + "</li>"; }).join("");
  }

  function evaluationParts(evaluation) {
    const locked = evaluation.locked_test || {};
    const looksFirst = Object.prototype.hasOwnProperty.call(locked, "match_macro_mae") || Object.prototype.hasOwnProperty.call(locked, "mae");
    const looksChase = Object.prototype.hasOwnProperty.call(locked, "match_macro_brier") || Object.prototype.hasOwnProperty.call(locked, "brier");
    return {
      first: evaluation.first_innings || evaluation.first || (looksFirst ? evaluation : {}),
      chase: evaluation.chase || (looksChase ? evaluation : {})
    };
  }

  function renderPhaseTable(parts) {
    let rows = [];
    const combined = data.evaluation.by_phase;
    if (combined) {
      rows = phaseRows(combined, "全体");
    } else {
      const first = (parts.first.by_slice && parts.first.by_slice.phase_absolute) || parts.first.by_phase || [];
      const chase = (parts.chase.by_slice && parts.chase.by_slice.phase_absolute) || parts.chase.by_phase || [];
      rows = phaseRows(first, "第1 innings").concat(phaseRows(chase, "追走"));
    }
    q("#phase-table").innerHTML = rows.length ? '<table><thead><tr><th>対象</th><th>phase</th><th>指標</th><th class="numeric">値</th><th class="numeric">試合</th></tr></thead><tbody>' +
      rows.map(function (item) {
        const value = item.value ?? item.match_macro_mae ?? item.match_macro_brier ?? item.mae ?? item.brier;
        const metric = item.metric || (item.match_macro_mae !== undefined || item.mae !== undefined ? "MAE" : "Brier");
        return "<tr><td>" + esc(item.scope || "—") + "</td><td>" + esc(item.label || item.phase || item.name || "—") + "</td><td>" + esc(metric) + "</td><td class=\"numeric\">" + fmt(value, 3) + "</td><td class=\"numeric\">" + fmt(item.match_count ?? item.matches ?? item.n, 0) + "</td></tr>";
      }).join("") + "</tbody></table>" : '<p class="empty-state">局面別指標はありません。</p>';
  }

  function phaseRows(raw, scope) {
    if (Array.isArray(raw)) return raw.map(function (item) { return Object.assign({ scope: scope }, item); });
    if (!raw || typeof raw !== "object") return [];
    return Object.keys(raw).map(function (phase) {
      return Object.assign({ scope: scope, phase: phase }, raw[phase]);
    });
  }

  function renderCandidateTable(parts) {
    let candidates = data.evaluation.candidates || [];
    if (!candidates.length) {
      candidates = [].concat(
        candidateRows(parts.first.candidates_model_0 || (parts.first.selection_model_0 && parts.first.selection_model_0.candidates), "第1 innings Model 0"),
        candidateRows(parts.first.candidates_model_1 || (parts.first.selection_model_1 && parts.first.selection_model_1.candidates), "第1 innings Model 1"),
        candidateRows(parts.chase.candidates_model_0 || (parts.chase.selection_model_0 && parts.chase.selection_model_0.candidates), "追走 Model 0"),
        candidateRows(parts.chase.candidates_model_1 || (parts.chase.selection_model_1 && parts.chase.selection_model_1.candidates), "追走 Model 1")
      );
    }
    q("#candidate-table").innerHTML = candidates.length ? '<table><thead><tr><th>候補</th><th>対象</th><th class="numeric">主指標</th><th>判断</th></tr></thead><tbody>' +
      candidates.map(function (item) {
        return "<tr><td>" + esc(item.name || item.model || "—") + "</td><td>" + esc(item.variant || item.scope || "—") + "</td><td class=\"numeric\">" +
          fmt(item.primary_metric ?? item.match_macro_mae ?? item.match_macro_brier ?? item.value, 3) + "</td><td>" + esc(item.reason || (item.selected ? "採用" : "比較")) + "</td></tr>";
      }).join("") + "</tbody></table>" : '<p class="empty-state">候補モデルの内訳はありません。</p>';
  }

  function candidateRows(rows, variant) {
    return (Array.isArray(rows) ? rows : []).map(function (row) { return Object.assign({ variant: variant }, row); });
  }

  function drawEvaluationCharts() {
    const parts = evaluationParts(data.evaluation);
    const locked = parts.chase.locked_test || {};
    let calibration = data.evaluation.calibration || locked.calibration_curve || parts.chase.calibration || [];
    if (!Array.isArray(calibration)) calibration = calibration.bins || [];
    const observed = calibration.map(function (item) {
      return xy(probability(item.predicted ?? item.mean_probability ?? item.predicted_probability), probability(item.observed ?? item.observed_rate ?? item.event_rate));
    }).filter(validPoint);
    drawLineChart(q("#calibration-chart"), [
      { name: "完全校正", color: COLORS.muted, dash: true, width: 1.5, values: [xy(0, 0), xy(1, 1)] },
      { name: "採用モデル", color: COLORS.green, width: 3, points: true, values: observed }
    ], { xLabel: "推定確率", yLabel: "実測率", xMin: 0, xMax: 1, yMin: 0, yMax: 1, percent: true });
    q("#calibration-table").innerHTML = calibration.length ? "確率校正 " + calibration.map(function (item) {
      return pct(item.predicted ?? item.mean_probability) + "で実測" + pct(item.observed ?? item.observed_rate ?? item.event_rate);
    }).join("、") : "確率校正データはありません。";
  }

  function renderFirstHistory() {
    const canvas = q("#first-history-chart");
    const empty = q("#first-history-empty");
    if (!lastFirstHistory.length) {
      canvas.hidden = true;
      empty.hidden = false;
      q("#first-history-table").textContent = "予測履歴はありません。";
      return;
    }
    canvas.hidden = false;
    empty.hidden = true;
    drawLineChart(canvas, [
      { name: "最終得点推定", color: COLORS.green, width: 3, points: true, values: lastFirstHistory.map(function (item) { return xy(item.balls, item.selected); }) },
      { name: "現在得点", color: COLORS.orange, width: 2, points: true, values: lastFirstHistory.map(function (item) { return xy(item.balls, item.current); }) }
    ], { xLabel: "完了合法球", yLabel: "得点", yMin: 0 });
    q("#first-history-table").textContent = lastFirstHistory.map(function (item) {
      return item.balls + "合法球で現在" + fmt(item.current, 0) + "点、最終得点推定" + fmt(item.selected) + "。";
    }).join(" ");
  }

  function drawLineChart(canvas, inputSeries, options) {
    const series = inputSeries.map(function (item) {
      return Object.assign({}, item, { values: (item.values || []).filter(validPoint) });
    }).filter(function (item) { return item.values.length; });
    if (!series.length) { drawEmptyCanvas(canvas, "表示できるデータがありません。"); return; }
    const prepared = prepareCanvas(canvas);
    if (!prepared) return;
    const ctx = prepared.ctx;
    const width = prepared.width;
    const height = prepared.height;
    const margin = { left: 58, right: 20, top: 48, bottom: 52 };
    const plotWidth = Math.max(10, width - margin.left - margin.right);
    const plotHeight = Math.max(10, height - margin.top - margin.bottom);
    const all = series.reduce(function (points, item) { return points.concat(item.values); }, []);
    const xValues = all.map(function (point) { return point.x; });
    const yValues = all.map(function (point) { return point.y; });
    let xMin = number(options.xMin) ?? Math.min.apply(null, xValues);
    let xMax = number(options.xMax) ?? Math.max.apply(null, xValues);
    let yMin = number(options.yMin) ?? Math.min.apply(null, yValues);
    let yMax = number(options.yMax) ?? Math.max.apply(null, yValues);
    if (xMin === xMax) { xMin -= .5; xMax += .5; }
    if (yMin === yMax) { yMin = Math.max(0, yMin - 1); yMax += 1; }
    if (options.yMax === undefined) yMax += Math.max((yMax - yMin) * .08, options.percent ? .02 : 1);
    const xScale = function (value) { return margin.left + ((value - xMin) / (xMax - xMin)) * plotWidth; };
    const yScale = function (value) { return margin.top + plotHeight - ((value - yMin) / (yMax - yMin)) * plotHeight; };
    drawAxes(ctx, width, height, margin, xMin, xMax, yMin, yMax, options);
    let legendX = margin.left;
    series.forEach(function (item) {
      ctx.save();
      ctx.strokeStyle = item.color || COLORS.green;
      ctx.fillStyle = item.color || COLORS.green;
      ctx.lineWidth = item.width || 2;
      if (item.dash) ctx.setLineDash([6, 5]);
      ctx.beginPath();
      item.values.forEach(function (point, index) {
        const px = xScale(point.x), py = yScale(point.y);
        if (index === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      });
      ctx.stroke();
      ctx.setLineDash([]);
      if (item.points) item.values.forEach(function (point) { drawCircle(ctx, xScale(point.x), yScale(point.y), 3.5, item.color || COLORS.green); });
      ctx.fillStyle = item.color || COLORS.green;
      ctx.fillRect(legendX, 17, 17, 3);
      ctx.fillStyle = COLORS.ink;
      ctx.font = "12px system-ui, sans-serif";
      ctx.fillText(item.name || "系列", legendX + 23, 22);
      legendX += 33 + ctx.measureText(item.name || "系列").width;
      ctx.restore();
    });
    (options.events || []).filter(validPoint).forEach(function (event) {
      const color = event.kind === "wicket" ? COLORS.orange : (event.kind === "four" ? COLORS.lime : COLORS.green);
      drawCircle(ctx, xScale(event.x), yScale(event.y), 5, color, "#ffffff");
    });
  }

  function drawAxes(ctx, width, height, margin, xMin, xMax, yMin, yMax, options) {
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    ctx.save();
    ctx.font = "11px system-ui, sans-serif";
    ctx.textBaseline = "middle";
    for (let index = 0; index <= 5; index += 1) {
      const ratio = index / 5;
      const y = margin.top + plotHeight - ratio * plotHeight;
      const value = yMin + ratio * (yMax - yMin);
      ctx.strokeStyle = COLORS.grid;
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(margin.left, y); ctx.lineTo(width - margin.right, y); ctx.stroke();
      ctx.fillStyle = COLORS.muted;
      ctx.textAlign = "right";
      ctx.fillText(options.percent ? Math.round(value * 100) + "%" : compactNumber(value), margin.left - 8, y);
    }
    for (let index = 0; index <= 4; index += 1) {
      const ratio = index / 4;
      const x = margin.left + ratio * plotWidth;
      const value = xMin + ratio * (xMax - xMin);
      ctx.fillStyle = COLORS.muted;
      ctx.textAlign = "center";
      ctx.fillText(options.xPercent ? Math.round(value * 100) + "%" : compactNumber(value), x, height - margin.bottom + 18);
    }
    ctx.fillStyle = COLORS.muted;
    ctx.font = "12px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(options.xLabel || "", margin.left + plotWidth / 2, height - 10);
    ctx.save();
    ctx.translate(14, margin.top + plotHeight / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(options.yLabel || "", 0, 0);
    ctx.restore();
    ctx.restore();
  }

  function drawBarChart(canvas, values) {
    const prepared = prepareCanvas(canvas);
    if (!prepared) return;
    const ctx = prepared.ctx, width = prepared.width, height = prepared.height;
    const margin = { left: 54, right: 16, top: 24, bottom: 66 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    for (let index = 0; index <= 4; index += 1) {
      const y = margin.top + plotHeight - (index / 4) * plotHeight;
      ctx.strokeStyle = COLORS.grid; ctx.beginPath(); ctx.moveTo(margin.left, y); ctx.lineTo(width - margin.right, y); ctx.stroke();
      ctx.fillStyle = COLORS.muted; ctx.font = "11px system-ui, sans-serif"; ctx.textAlign = "right"; ctx.textBaseline = "middle";
      ctx.fillText(index * 25 + "%", margin.left - 7, y);
    }
    const slot = plotWidth / Math.max(1, values.length);
    const barWidth = Math.min(54, slot * .68);
    values.forEach(function (item, index) {
      const value = item.value === null ? 0 : item.value;
      const x = margin.left + slot * index + (slot - barWidth) / 2;
      const barHeight = value * plotHeight;
      ctx.fillStyle = item.wicket ? COLORS.orange : COLORS.green;
      ctx.fillRect(x, margin.top + plotHeight - barHeight, barWidth, barHeight);
      ctx.fillStyle = COLORS.ink; ctx.textAlign = "center"; ctx.textBaseline = "top"; ctx.font = "11px system-ui, sans-serif";
      ctx.fillText(item.value === null ? "—" : Math.round(value * 100) + "%", x + barWidth / 2, margin.top + plotHeight - barHeight - 17);
      ctx.save();
      ctx.translate(x + barWidth / 2, height - margin.bottom + 10);
      if (slot < 68) ctx.rotate(-Math.PI / 7);
      ctx.fillText(shortLabel(item.label, 13), 0, 0);
      ctx.restore();
    });
  }

  function prepareCanvas(canvas) {
    if (!canvas || canvas.hidden) return null;
    const width = Math.max(280, Math.floor(canvas.getBoundingClientRect().width || canvas.parentElement.clientWidth || 600));
    // Keep CSS height separate from the pixel buffer, whose height attribute changes on every draw.
    if (!canvasDisplayHeights.has(canvas)) {
      canvasDisplayHeights.set(canvas, Number(canvas.getAttribute("height")) || 320);
    }
    const height = canvasDisplayHeights.get(canvas);
    const ratio = Math.min(globalThis.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(width * ratio);
    canvas.height = Math.floor(height * ratio);
    canvas.style.height = height + "px";
    const ctx = canvas.getContext("2d");
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, width, height);
    return { ctx: ctx, width: width, height: height };
  }

  function drawEmptyCanvas(canvas, message) {
    const prepared = prepareCanvas(canvas);
    if (!prepared) return;
    prepared.ctx.fillStyle = COLORS.muted;
    prepared.ctx.font = "13px system-ui, sans-serif";
    prepared.ctx.textAlign = "center";
    prepared.ctx.textBaseline = "middle";
    prepared.ctx.fillText(message, prepared.width / 2, prepared.height / 2);
  }

  function drawCircle(ctx, x, y, radius, fill, stroke) {
    ctx.beginPath(); ctx.arc(x, y, radius, 0, Math.PI * 2); ctx.fillStyle = fill; ctx.fill();
    if (stroke) { ctx.lineWidth = 1.5; ctx.strokeStyle = stroke; ctx.stroke(); }
  }

  function redrawVisibleCharts() {
    const route = routeFromHash();
    if (route === "first") renderFirstHistory();
    if (route === "chase" && lastScenarios.length) renderScenarios(lastScenarios);
    if (route === "replay" && selectedMatchId) renderReplay(selectedMatchId);
    if (route === "evaluation") drawEvaluationCharts();
  }

  function readHistory() {
    try {
      const stored = globalThis.localStorage && globalThis.localStorage.getItem("wasp-women-standalone-first-history");
      const parsed = stored ? JSON.parse(stored) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch (_) {
      return Array.isArray(globalThis.__waspHistoryFallback) ? globalThis.__waspHistoryFallback : [];
    }
  }

  function writeHistory(history) {
    globalThis.__waspHistoryFallback = history.slice();
    try {
      if (globalThis.localStorage) globalThis.localStorage.setItem("wasp-women-standalone-first-history", JSON.stringify(history));
    } catch (_) { /* Private/file modes may reject localStorage; memory fallback remains active. */ }
  }

  function firstIntervals(result) {
    const intervals = result.intervals || {};
    return {
      p50: intervals.p50 || intervals["50"] || { lower: result.lower_50, upper: result.upper_50 },
      p80: intervals.p80 || intervals["80"] || { lower: result.lower_80, upper: result.upper_80 }
    };
  }

  function intervalText(interval) {
    if (!interval) return "—";
    const lower = interval.lower ?? interval.low ?? interval[0];
    const upper = interval.upper ?? interval.high ?? interval[1];
    return fmt(lower) + "–" + fmt(upper);
  }

  function correctionText(correction) {
    if (!correction || !correction.requested) return "日本向け補正はリクエストされていません。";
    if (correction.applied) {
      const count = number(correction.match_count ?? correction.gate_match_count);
      return "日本向け補正を適用しました。" + (count === null ? "" : " gate対象 " + fmt(count, 0) + "試合。");
    }
    return "日本向け補正は未適用です。" + gateReason(correction.fallback_reason || correction.reason, false);
  }

  function firstComparisonLabels() {
    const first = evaluationParts(data.evaluation).first || {};
    const model1 = first.selection_model_1 || {};
    return model1.model_1_gate_passed === false ? { team_adjusted: "チーム情報モデル（不採用）" } : {};
  }

  function comparisonHtml(comparison, formatter, labelOverrides) {
    const labels = Object.assign({ global: "全体", team_adjusted: "チーム補正", japan_adjusted: "日本補正", model_0: "Model 0", model_1: "Model 1", model_2: "Model 2" }, labelOverrides || {});
    return Object.keys(comparison || {}).filter(function (key) { return key !== "selected"; }).slice(0, 3).map(function (key) {
      return comparisonItem(labels[key] || key, formatter(predictionValue(comparison[key])));
    }).join("");
  }

  function comparisonItem(label, value) { return '<div class="comparison-item"><span>' + esc(label) + "</span><strong>" + esc(value) + "</strong></div>"; }
  function metricCard(label, value, note) { return '<article class="metric-card"><span>' + esc(label) + "</span><strong>" + esc(value) + "</strong><small>" + esc(note || "") + "</small></article>"; }

  function categoryWarnings(teamOne, teamTwo, venue) {
    const warnings = [];
    if (data.teams.length && !data.teams.includes(teamOne)) warnings.push(teamOne + "は学習済みteam一覧にないためglobal fallbackを使います。");
    if (data.teams.length && !data.teams.includes(teamTwo)) warnings.push(teamTwo + "は学習済みteam一覧にないためglobal fallbackを使います。");
    if (venue && data.venues.length && !data.venues.includes(venue)) warnings.push(venue + "は学習済み会場一覧にないためglobal priorを使います。");
    return warnings;
  }

  function renderWarnings(target, warnings) {
    target.innerHTML = unique((warnings || []).map(function (warning) {
      return typeof warning === "string" ? warning : (warning.message || warning.code || String(warning));
    })).map(function (warning) { return "<li>" + esc(warning) + "</li>"; }).join("");
  }

  function ensureReducedSupported(limit) {
    if (limit === 120) return;
    let enabled = rawData.reduced_match_enabled;
    if (enabled && typeof enabled === "object") enabled = enabled.enabled ?? enabled.passed ?? enabled.active;
    const gate = data.gates.find(function (item) { return item.key === "reduced"; });
    if (!Boolean(enabled ?? (gate && gate.enabled))) {
      const error = validationError(null, "短縮戦は有効化gateを通過していないため、このHTMLでは手動予測できません。");
      error.code = "unsupported_reduced_match";
      throw error;
    }
  }

  function validateQuota(value, prefix, label) {
    const overField = prefix + "_overs";
    const ballField = prefix + "_balls";
    requireRange(value.overs, 0, 20, overField, label + "のover");
    requireRange(value.balls, 0, 5, ballField, label + "のball");
  }

  function requireTeams(first, second, firstField, secondField) {
    if (!first) throw validationError(firstField, "チーム名を入力してください。");
    if (!second) throw validationError(secondField, "チーム名を入力してください。");
    if (normalizeName(first) === normalizeName(second)) throw validationError(secondField, "同じチーム同士は指定できません。");
  }

  function requireRange(value, min, max, field, label) {
    if (!Number.isInteger(value) || value < min || value > max) throw validationError(field, label + "は" + min + "〜" + max + "の整数で入力してください。");
  }

  function validationError(field, message) {
    const error = new Error(message);
    error.code = "validation_error";
    error.field = field;
    return error;
  }

  function handleFormError(form, error) {
    if (error.field) {
      const field = form.elements.namedItem(error.field);
      if (field) { field.setAttribute("aria-invalid", "true"); field.focus(); }
    }
    showError(error.message || "入力を確認してください。", error.code && error.code !== "validation_error" ? error.code : "");
  }

  function markFormValid(form) { qa("[aria-invalid='true']", form).forEach(function (field) { field.removeAttribute("aria-invalid"); }); }

  function showError(message, detail) {
    const alert = q("#global-alert");
    if (!alert) return;
    alert.hidden = false;
    alert.textContent = message + (detail ? "（" + detail + "）" : "");
    alert.scrollIntoView({ block: "nearest" });
  }

  function clearError() { const alert = q("#global-alert"); if (alert) alert.hidden = true; }

  function textValue(formData, name) { return String(formData.get(name) || "").trim(); }
  function optionalText(formData, name) { const value = textValue(formData, name); return value || null; }
  function integerValue(formData, name) { const value = Number(formData.get(name)); return Number.isInteger(value) ? value : NaN; }
  function quotaToBalls(quota) { return quota.overs * 6 + quota.balls; }

  function predictionValue(value) {
    if (value && typeof value === "object") return value.value ?? value.prediction ?? value.predicted_score ?? value.win_probability ?? value.probability;
    return value;
  }

  function probability(value) {
    const parsed = number(predictionValue(value));
    if (parsed === null) return null;
    return Math.max(0, Math.min(1, parsed > 1 ? parsed / 100 : parsed));
  }

  function number(value) {
    if (value === null || value === undefined || value === "") return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function fmt(value, digits) {
    const parsed = number(predictionValue(value));
    if (parsed === null) return "—";
    return parsed.toLocaleString("ja-JP", { maximumFractionDigits: digits === undefined ? 1 : digits });
  }

  function pct(value) {
    const parsed = probability(value);
    return parsed === null ? "—" : (parsed * 100).toFixed(1) + "%";
  }

  function compactNumber(value) {
    if (!Number.isFinite(value)) return "—";
    const rounded = Math.abs(value) >= 10 ? Math.round(value) : Math.round(value * 10) / 10;
    return String(rounded);
  }

  function xy(x, y) { return { x: number(x), y: number(y) }; }
  function validPoint(point) { return point && point.x !== null && point.y !== null && Number.isFinite(point.x) && Number.isFinite(point.y); }
  function shortLabel(value, max) { const text = String(value || ""); return text.length > max ? text.slice(0, max - 1) + "…" : text; }
  function normalizeName(value) { return String(value || "").trim().toLocaleLowerCase("en-US"); }
  function unique(values) { return Array.from(new Set(values.filter(function (value) { return value !== null && value !== undefined && value !== ""; }))); }
  function localeCompare(left, right) { return String(left).localeCompare(String(right), "en"); }

  function matchTeams(match) {
    if (!match || typeof match !== "object") return [];
    const teams = Array.isArray(match.teams) ? match.teams : [match.team_1 ?? match.team1 ?? match.batting_team, match.team_2 ?? match.team2 ?? match.bowling_team];
    return teams.filter(Boolean).map(String);
  }

  function modelName(value) {
    if (!value) return "—";
    if (typeof value === "string") return value;
    return value.name || value.model || value.model_name || "—";
  }

  function resultText(result, winner) {
    if (typeof result === "string" && result) return result;
    if (result && typeof result === "object") return result.text || result.description || result.outcome || (result.winner ? result.winner + " 勝利" : "結果収録済み");
    return winner ? String(winner) + " 勝利" : "結果不明";
  }

  function formatDateTime(value) {
    const parsed = new Date(value);
    if (Number.isNaN(parsed.valueOf())) return String(value);
    return parsed.toLocaleString("ja-JP", { dateStyle: "medium", timeStyle: "short" });
  }

  function esc(value) {
    return String(value ?? "").replace(/[&<>'\"]/g, function (character) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '\"': "&quot;" }[character];
    });
  }

  function escAttr(value) { return esc(value).replace(/`/g, "&#96;"); }

  function debounce(callback, wait) {
    let timer = null;
    return function () {
      const args = arguments;
      clearTimeout(timer);
      timer = setTimeout(function () { callback.apply(null, args); }, wait);
    };
  }

  initialize();
})();
