"use strict";

const Wasp = (() => {
  const green = "#0b6b4f";
  const lime = "#b8d35b";
  const orange = "#e46d3c";
  const blue = "#31688e";
  const layout = {
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
    font: {family: "Inter, Noto Sans JP, sans-serif", color: "#405248"},
    margin: {l: 52, r: 24, t: 24, b: 48},
    xaxis: {gridcolor: "#e3e5de", zeroline: false},
    yaxis: {gridcolor: "#e3e5de", zeroline: false},
    legend: {orientation: "h", y: 1.12}
  };
  const config = {displayModeBar: false, responsive: true};

  const qs = (selector, root = document) => root.querySelector(selector);
  const qsa = (selector, root = document) => [...root.querySelectorAll(selector)];
  const number = value => {
    if (value === null || value === undefined || (typeof value === "string" && value.trim() === "")) return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  };
  const fmt = (value, digits = 1) => number(value) === null ? "—" : Number(value).toLocaleString("ja-JP", {maximumFractionDigits: digits});
  const pct = value => {
    const n = number(value);
    if (n === null) return "—";
    return `${(n <= 1 ? n * 100 : n).toFixed(1)}%`;
  };
  const probability = value => {
    const n = number(value);
    if (n === null) return null;
    return Math.max(0, Math.min(1, n > 1 ? n / 100 : n));
  };
  const escapeHtml = value => String(value ?? "").replace(/[&<>'"]/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"})[char]);
  const matchTeams = item => (item.teams || [item.team_1 ?? item.team1, item.team_2 ?? item.team2]).filter(Boolean);

  function evaluationParts(data = {}) {
    const locked = data.locked_test || {};
    const looksFirst = Object.prototype.hasOwnProperty.call(locked, "match_macro_mae") || Object.prototype.hasOwnProperty.call(locked, "mae");
    const looksChase = Object.prototype.hasOwnProperty.call(locked, "match_macro_brier") || Object.prototype.hasOwnProperty.call(locked, "brier");
    return {
      first: data.first_innings || (looksFirst ? data : {}),
      chase: data.chase || (looksChase ? data : {})
    };
  }

  async function api(path, options = {}) {
    const response = await fetch(path, {headers: {"Accept": "application/json", ...(options.body ? {"Content-Type": "application/json"} : {})}, ...options});
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = payload.error || {};
      const wrapped = new Error(error.message || `HTTP ${response.status}`);
      wrapped.code = error.code || "http_error";
      wrapped.details = error.details;
      throw wrapped;
    }
    return Object.prototype.hasOwnProperty.call(payload, "data") ? payload.data : payload;
  }

  function alertError(error) {
    const target = qs("#global-alert");
    if (!target) return;
    target.hidden = false;
    target.textContent = `${error.message || "処理できませんでした。"}${error.details ? ` (${error.details})` : ""}`;
    target.scrollIntoView({behavior: "smooth", block: "nearest"});
  }

  function clearAlert() {
    const target = qs("#global-alert");
    if (target) target.hidden = true;
  }

  async function checkHealth() {
    const badge = qs("#service-status");
    try {
      const response = await fetch("/api/health");
      const health = await response.json();
      if (health.ready) {
        badge.textContent = "モデル準備完了";
        badge.className = "status-pill status-ok";
      } else {
        badge.textContent = "モデル未準備";
        badge.className = "status-pill status-error";
      }
    } catch (_) {
      badge.textContent = "API接続なし";
      badge.className = "status-pill status-error";
    }
  }

  function plot(target, traces, extraLayout = {}) {
    if (!target) return;
    if (!window.Plotly) {
      target.innerHTML = '<p class="empty-state">グラフライブラリを読み込めませんでした。</p>';
      return;
    }
    // Plotly.react appends its container when the target currently contains a
    // hand-written empty state. Remove that placeholder so it is not exposed
    // alongside the rendered chart (visually or to assistive technology).
    qsa(":scope > .empty-state", target).forEach(node => node.remove());
    window.Plotly.react(target, traces, {...layout, ...extraLayout}, config);
  }

  function metricCard(label, value, note = "") {
    return `<article class="metric-card"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small></article>`;
  }

  async function dashboard() {
    try {
      const [metadata, evaluation] = await Promise.all([api("/api/metadata"), api("/api/evaluation")]);
      const counts = metadata.counts || metadata.audit || {};
      const models = metadata.models || metadata.selected_models || {};
      const parts = evaluationParts(evaluation);
      const firstMetrics = parts.first.locked_test || {};
      const chaseMetrics = parts.chase.locked_test || {};
      qs("#summary-cards").innerHTML = [
        metricCard("収録試合", fmt(counts.matches ?? metadata.match_count, 0), metadata.period || "CSV2監査済み"),
        metricCard("日本戦", fmt(counts.japan_matches ?? metadata.japan_match_count, 0), "男子T20"),
        metricCard("採用先攻モデル", models.first_innings_team?.name || models.first_innings_team || models.first_innings?.name || models.first_innings || "—", "validation選択"),
        metricCard("採用追走モデル", models.chase_team?.name || models.chase_team || models.chase?.name || models.chase || "—", "validation選択")
      ].join("");
      const hash = metadata.source_sha256 || metadata.source?.sha256;
      qs("#source-hash").textContent = hash ? `source ${hash.slice(0, 12)}…` : "source —";
      const metrics = evaluation.summary || evaluation.metrics || {};
      qs("#dashboard-evaluation").className = "";
      qs("#dashboard-evaluation").innerHTML = `<div class="comparison-grid">
        <div class="comparison-item"><span>先攻 MAE</span><strong>${fmt(metrics.first_mae ?? firstMetrics.match_macro_mae ?? firstMetrics.mae)}</strong></div>
        <div class="comparison-item"><span>追走 Brier</span><strong>${fmt(metrics.chase_brier ?? chaseMetrics.match_macro_brier ?? chaseMetrics.brier, 3)}</strong></div>
        <div class="comparison-item"><span>追走 ECE</span><strong>${fmt(metrics.chase_ece ?? chaseMetrics.ece, 3)}</strong></div>
      </div>`;
      const exclusions = metadata.exclusions || counts.exclusions || {};
      const items = Array.isArray(exclusions) ? exclusions : Object.entries(exclusions).map(([reason, count]) => ({reason, count}));
      qs("#exclusions").className = "";
      qs("#exclusions").innerHTML = items.length ? `<ul class="plain-list">${items.slice(0, 7).map(item => `<li>${escapeHtml(item.reason || item.name)}: ${fmt(item.count, 0)}試合</li>`).join("")}</ul>` : '<p class="muted">除外内訳はアーティファクトにありません。</p>';
    } catch (error) { alertError(error); }
  }

  function comparisonHtml(values, formatter) {
    const labels = {global: "全体", team_adjusted: "チーム補正", japan_adjusted: "日本補正", model_0: "Model 0", model_1: "Model 1", model_2: "Model 2"};
    return Object.entries(values || {}).filter(([key]) => key !== "selected").slice(0, 3).map(([key, value]) => `<div class="comparison-item"><span>${labels[key] || escapeHtml(key)}</span><strong>${formatter(value)}</strong></div>`).join("");
  }

  function correctionHtml(correction = {}) {
    if (!correction.requested) return "日本向け補正はリクエストされていません。";
    if (correction.applied) return `日本向け補正を適用（gate対象 ${fmt(correction.match_count, 0)}試合）。`;
    return `日本向け補正は未適用です。${escapeHtml(correction.fallback_reason || "gateまたは標本数の条件を満たしていません。")}`;
  }

  function firstIntervals(data) {
    const intervals = data.intervals || {};
    const p50 = intervals.p50 || intervals["50"] || {lower: data.lower_50, upper: data.upper_50};
    const p80 = intervals.p80 || intervals["80"] || {lower: data.lower_80, upper: data.upper_80};
    return {p50, p80};
  }

  function renderFirstHistory() {
    const target = qs("#first-history-chart");
    if (!target) return;
    const history = JSON.parse(localStorage.getItem("wasp-first-history") || "[]");
    if (!history.length) {
      target.innerHTML = '<p class="empty-state">このブラウザでの送信履歴はまだありません。</p>';
      return;
    }
    plot(target, [
      {x: history.map(item => item.balls), y: history.map(item => item.selected), type: "scatter", mode: "lines+markers", name: "最終得点推定", line: {color: green, width: 3}},
      {x: history.map(item => item.balls), y: history.map(item => item.current), type: "scatter", mode: "lines+markers", name: "現在得点", line: {color: orange, dash: "dot"}}
    ], {xaxis: {...layout.xaxis, title: "完了合法球"}, yaxis: {...layout.yaxis, title: "得点"}});
  }

  function firstInnings() {
    renderFirstHistory();
    qs("#clear-first-history")?.addEventListener("click", () => { localStorage.removeItem("wasp-first-history"); renderFirstHistory(); });
    qs("#first-innings-form")?.addEventListener("submit", async event => {
      event.preventDefault(); clearAlert();
      const form = new FormData(event.currentTarget);
      const payload = {
        batting_team: form.get("batting_team"), bowling_team: form.get("bowling_team"),
        runs: Number(form.get("runs")), wickets: Number(form.get("wickets")),
        completed: {overs: Number(form.get("completed_overs")), balls: Number(form.get("completed_balls"))},
        quota: {overs: Number(form.get("quota_overs")), balls: Number(form.get("quota_balls"))},
        venue: form.get("venue") || null, use_japan_correction: form.has("use_japan_correction")
      };
      try {
        const data = await api("/api/predict/first-innings", {method: "POST", body: JSON.stringify(payload)});
        const comparison = data.comparison || {};
        const selected = comparison.selected ?? data.selected ?? data.predicted_score;
        const intervals = firstIntervals(data);
        qs("#first-empty").hidden = true; qs("#first-results").hidden = false;
        qs("#first-selected").textContent = fmt(selected);
        qs("#first-interval").textContent = `50% ${fmt(intervals.p50?.lower)}–${fmt(intervals.p50?.upper)} ／ 80% ${fmt(intervals.p80?.lower)}–${fmt(intervals.p80?.upper)}`;
        qs("#first-comparison").innerHTML = comparisonHtml(comparison, value => fmt(value));
        qs("#first-correction").textContent = correctionHtml(data.correction);
        const history = JSON.parse(localStorage.getItem("wasp-first-history") || "[]");
        history.push({balls: payload.completed.overs * 6 + payload.completed.balls, current: payload.runs, selected: number(selected)});
        localStorage.setItem("wasp-first-history", JSON.stringify(history.slice(-40)));
        renderFirstHistory();
      } catch (error) { alertError(error); }
    });
  }

  function chase() {
    qs("#chase-form")?.addEventListener("submit", async event => {
      event.preventDefault(); clearAlert();
      const form = new FormData(event.currentTarget);
      const payload = {
        chasing_team: form.get("chasing_team"), defending_team: form.get("defending_team"),
        target: Number(form.get("target")), current_score: Number(form.get("current_score")),
        wickets: Number(form.get("wickets")), balls_remaining: Number(form.get("balls_remaining")),
        target_ball_limit: {overs: Number(form.get("limit_overs")), balls: Number(form.get("limit_balls"))},
        venue: form.get("venue") || null, use_japan_correction: form.has("use_japan_correction")
      };
      try {
        const tossChoice = form.get("toss_winner");
        payload.toss_winner = tossChoice === "chasing" ? payload.chasing_team : tossChoice === "defending" ? payload.defending_team : null;
        const data = await api("/api/predict/chase", {method: "POST", body: JSON.stringify(payload)});
        const comparison = data.comparison || {};
        const selected = comparison.selected ?? data.selected ?? data.win_probability;
        const selectedProbability = probability(selected);
        qs("#chase-empty").hidden = true; qs("#chase-results").hidden = false;
        qs("#chase-selected").textContent = pct(selectedProbability);
        qs("#chase-ring").style.setProperty("--probability", selectedProbability === null ? 0 : selectedProbability * 100);
        qs("#chase-ring").classList.toggle("is-unavailable", selectedProbability === null);
        qs("#chase-comparison").innerHTML = comparisonHtml(comparison, pct);
        qs("#chase-correction").textContent = correctionHtml(data.correction);
        qs("#chase-warnings").innerHTML = (data.warnings || []).map(warning => `<li>${escapeHtml(warning)}</li>`).join("");
        const terminal = data.terminal || {};
        if (terminal.is_terminal) {
          qs("#chase-terminal").hidden = false;
          qs("#chase-terminal").textContent = terminal.status === "tied_regulation" ? "規定tieのため、v1の二値確率は返しません。" : `終端状態: ${terminal.status || "確定"}`;
        } else qs("#chase-terminal").hidden = true;
        const scenarios = data.scenarios || [];
        plot(qs("#scenario-chart"), [{x: scenarios.map(item => item.label || (item.wicket ? "wicket" : `${item.runs} runs`)), y: scenarios.map(item => probability(item.win_probability ?? item.probability)), type: "bar", marker: {color: scenarios.map(item => item.wicket ? orange : green)}, hovertemplate: "%{x}<br>%{y:.1%}<extra></extra>"}], {yaxis: {...layout.yaxis, title: "追走成功推定", tickformat: ".0%", range: [0,1]}});
      } catch (error) { alertError(error); }
    });
  }

  let replayCursor = null;
  const replayEvents = [
    {event: "wicket", label: "wicket", symbol: "circle", color: orange},
    {event: "four", label: "Four", symbol: "diamond", color: lime},
    {event: "six", label: "Six", symbol: "hexagon", color: green}
  ];
  const replayEvent = item => String(item.event || item.previous_event || item.previous_event_type || "").toLowerCase();
  const replayBall = item => item.legal_balls_bowled ?? item.legal_balls ?? item.ball;
  function replayEventTrace(points, definition, yValue) {
    const selected = points.filter(item => replayEvent(item) === definition.event);
    return {
      x: selected.map(replayBall), y: selected.map(yValue), type: "scatter", mode: "markers",
      name: definition.label, showlegend: false,
      marker: {symbol: definition.symbol, color: definition.color, size: 10, line: {color: "#ffffff", width: 1}},
      hovertemplate: `${definition.label}<br>合法球 %{x}<extra></extra>`
    };
  }

  async function loadMatches(append = false) {
    const params = new URLSearchParams({limit: "25", japan_only: String(qs("#replay-japan-only").checked)});
    if (qs("#replay-from-date").value) params.set("from_date", qs("#replay-from-date").value);
    if (qs("#replay-to-date").value) params.set("to_date", qs("#replay-to-date").value);
    if (append && replayCursor) params.set("cursor", replayCursor);
    try {
      const data = await api(`/api/matches?${params}`);
      const items = Array.isArray(data) ? data : (data.items || data.matches || []);
      replayCursor = data.next_cursor || null;
      const html = items.map(item => `<button class="match-button" data-match-id="${escapeHtml(item.match_id || item.id)}"><strong>${escapeHtml(matchTeams(item).join(" vs "))}</strong><span>${escapeHtml(item.date || item.match_date || "")} · ${escapeHtml(item.venue || "会場不明")}</span></button>`).join("");
      const list = qs("#match-list");
      list.innerHTML = append ? list.innerHTML + html : (html || '<p class="empty-state">条件に合う試合はありません。</p>');
      qs("#replay-more").hidden = !replayCursor;
    } catch (error) { alertError(error); }
  }

  async function loadReplay(matchId, button) {
    qsa(".match-button").forEach(element => element.removeAttribute("aria-current"));
    button?.setAttribute("aria-current", "true");
    try {
      const data = await api(`/api/matches/${encodeURIComponent(matchId)}`);
      qs("#replay-empty").hidden = true; qs("#replay-detail").hidden = false;
      qs("#replay-title").textContent = matchTeams(data).join(" vs ");
      qs("#replay-date").textContent = `${data.date || data.match_date || ""} · ${data.venue || ""}`;
      qs("#replay-result").textContent = data.result || data.winner || "結果不明";
      const replay = data.replay || data;
      const points = replay.points || [];
      const first = replay.first_innings || points.filter(item => Number(item.innings) === 1);
      const chase = replay.chase || replay.second_innings || points.filter(item => Number(item.innings) === 2);
      plot(qs("#replay-first-chart"), [
        {x: first.map(replayBall), y: first.map(item => item.selected ?? item.predicted_final_score ?? item.predicted_score), type: "scatter", mode: "lines", name: "推定最終得点", line: {color: green, width: 3}},
        {x: first.map(replayBall), y: first.map(item => item.runs_so_far ?? item.runs ?? item.score), type: "scatter", mode: "lines", name: "実得点", line: {color: orange}},
        ...replayEvents.map(definition => replayEventTrace(first, definition, item => item.runs_so_far ?? item.runs ?? item.score))
      ], {xaxis: {...layout.xaxis, title: "完了合法球"}, yaxis: {...layout.yaxis, title: "得点"}});
      plot(qs("#replay-chase-chart"), [
        {x: chase.map(replayBall), y: chase.map(item => probability(item.selected ?? item.win_probability)), type: "scatter", mode: "lines", fill: "tozeroy", name: "追走成功推定", line: {color: blue, width: 3}},
        ...replayEvents.map(definition => replayEventTrace(chase, definition, item => probability(item.selected ?? item.win_probability)))
      ], {xaxis: {...layout.xaxis, title: "完了合法球"}, yaxis: {...layout.yaxis, title: "確率", tickformat: ".0%", range: [0,1]}});
    } catch (error) { alertError(error); }
  }

  function replay() {
    qs("#replay-search")?.addEventListener("click", () => { replayCursor = null; loadMatches(); });
    qs("#replay-more")?.addEventListener("click", () => loadMatches(true));
    qs("#match-list")?.addEventListener("click", event => { const button = event.target.closest(".match-button"); if (button) loadReplay(button.dataset.matchId, button); });
    loadMatches();
  }

  function filteredEvaluationSlices(data) {
    const rows = [];
    const visit = (value, path = []) => {
      if (!value || typeof value !== "object" || Array.isArray(value)) return;
      const metric = value.match_macro_mae ?? value.match_macro_brier ?? value.mae ?? value.brier;
      if (number(metric) !== null) {
        rows.push({phase: path.join(" / ") || "filtered", value: number(metric), match_count: value.matches ?? value.match_count ?? value.n});
        return;
      }
      Object.entries(value).forEach(([key, child]) => visit(child, [...path, key]));
    };
    visit(data.filtered || {});
    return rows;
  }

  function renderEvaluation(data, modelInfo) {
    const parts = evaluationParts(data);
    const firstMetrics = parts.first.locked_test || {};
    const chaseMetrics = parts.chase.locked_test || {};
    const summary = data.summary || data.metrics || {};
    qs("#evaluation-cards").innerHTML = [
      metricCard("第1 innings MAE", fmt(summary.first_mae ?? firstMetrics.match_macro_mae ?? firstMetrics.mae), "match-macro"),
      metricCard("第1 innings RMSE", fmt(summary.first_rmse ?? firstMetrics.match_macro_rmse ?? firstMetrics.rmse), "locked test"),
      metricCard("追走 Brier", fmt(summary.chase_brier ?? chaseMetrics.match_macro_brier ?? chaseMetrics.brier, 3), "低いほど良い"),
      metricCard("追走 ECE", fmt(summary.chase_ece ?? chaseMetrics.ece, 3), "equal-mass 10 bins")
    ].join("");
    const calibration = data.calibration || chaseMetrics.calibration_curve || [];
    plot(qs("#calibration-chart"), [
      {x: [0,1], y: [0,1], type: "scatter", mode: "lines", name: "完全校正", line: {color: "#9aa49d", dash: "dash"}},
      {x: calibration.map(item => item.predicted ?? item.mean_probability), y: calibration.map(item => item.observed ?? item.observed_rate ?? item.event_rate), type: "scatter", mode: "lines+markers", name: "採用モデル", line: {color: green, width: 3}}
    ], {xaxis: {...layout.xaxis, title: "推定確率", tickformat: ".0%", range: [0,1]}, yaxis: {...layout.yaxis, title: "実測率", tickformat: ".0%", range: [0,1]}});
    const filteredPhases = filteredEvaluationSlices(data);
    const rawPhases = data.by_phase || parts.chase.by_phase || parts.chase.by_slice?.phase_absolute || parts.first.by_phase || parts.first.by_slice?.phase_absolute || [];
    const phases = filteredPhases.length ? filteredPhases : (Array.isArray(rawPhases) ? rawPhases : Object.entries(rawPhases).map(([phase, values]) => ({phase, ...values})));
    plot(qs("#phase-chart"), [{x: phases.map(item => item.phase), y: phases.map(item => item.value ?? item.match_macro_mae ?? item.match_macro_brier ?? item.mae ?? item.brier), type: "bar", marker: {color: [lime, green, orange]}, customdata: phases.map(item => item.match_count ?? item.matches ?? item.n), hovertemplate: "%{x}<br>指標 %{y:.3f}<br>試合 %{customdata}<extra></extra>"}], {yaxis: {...layout.yaxis, title: "主指標"}});
    const candidates = data.candidates || [
      ...(parts.first.candidates_model_0 || parts.first.selection_model_0?.candidates || []).map(item => ({...item, variant: "第1 innings Model 0"})),
      ...(parts.first.candidates_model_1 || parts.first.selection_model_1?.candidates || []).map(item => ({...item, variant: "第1 innings Model 1"})),
      ...(parts.chase.candidates_model_0 || parts.chase.selection_model_0?.candidates || []).map(item => ({...item, variant: "追走 Model 0"})),
      ...(parts.chase.candidates_model_1 || parts.chase.selection_model_1?.candidates || []).map(item => ({...item, variant: "追走 Model 1"}))
    ];
    qs("#candidate-table").innerHTML = candidates.length ? `<table><thead><tr><th>候補</th><th>対象</th><th>主指標</th><th>判断</th></tr></thead><tbody>${candidates.map(item => `<tr><td>${escapeHtml(item.name || item.model)}</td><td>${escapeHtml(item.variant || item.scope || "—")}</td><td>${fmt(item.primary_metric ?? item.match_macro_mae ?? item.match_macro_brier ?? item.value, 3)}</td><td>${escapeHtml(item.reason || (item.selected ? "採用" : "比較"))}</td></tr>`).join("")}</tbody></table>` : '<p class="empty-state">候補モデルの内訳はありません。</p>';
    const limitations = modelInfo.limitations || data.limitations || [];
    qs("#model-limitations").innerHTML = limitations.length ? limitations.map(item => `<li>${escapeHtml(item)}</li>`).join("") : "<li>D/L・DLS、規定tie、Super Overはv1安定版の学習対象外です。</li><li>日本向け補正は役割別gateによりfallbackする場合があります。</li><li>収録範囲外のチーム・会場ではglobal priorへ戻ります。</li>";
  }

  async function loadEvaluation() {
    clearAlert();
    const params = new URLSearchParams();
    [["model", "#evaluation-model"], ["scope", "#evaluation-scope"], ["phase", "#evaluation-phase"]].forEach(([key, selector]) => { const value = qs(selector).value; if (value) params.set(key, value); });
    try {
      const [data, modelInfo] = await Promise.all([api(`/api/evaluation?${params}`), api("/api/model-info")]);
      renderEvaluation(data, modelInfo);
    } catch (error) { alertError(error); }
  }

  function evaluation() { qs("#evaluation-apply")?.addEventListener("click", loadEvaluation); loadEvaluation(); }

  function init() {
    checkHealth();
    ({dashboard, "first-innings": firstInnings, chase, replay, evaluation}[document.body.dataset.page] || (() => {}))();
  }
  return {init};
})();

document.addEventListener("DOMContentLoaded", Wasp.init);
