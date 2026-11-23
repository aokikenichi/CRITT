"use strict";

const streaks = ["0", "1", "2", "3", "4", "5+"];
const runBins = ["0", "1", "2", "3", "4", "5", "6", "7+"];
const labels = {
  dot: "次球もドット", wicket: "次球でアウト", score: "次球で得点",
  boundary: "次球でバウンダリー", escape: "2球以内に得点",
};
const phases = { all: "全体", powerplay: "Powerplay", middle: "Middle", death: "Death" };
const priority = {
  Japan: "日本", India: "インド", Australia: "オーストラリア", Nepal: "ネパール",
  Afghanistan: "アフガニスタン",
};
const state = { phase: "all", streak: "3" };
const number = new Intl.NumberFormat("ja-JP");
const $ = (id) => document.getElementById(id);
const fmt = (n) => number.format(n);
const percent = (rate) => (rate * 100).toFixed(1) + "%";
const share = (events, n) => n ? percent(events / n) : "—";
const interval = ([, low, high]) => low === null ? "—" : percent(low) + "〜" + percent(high);
const points = (rate) => (rate > 0 ? "+" : rate < 0 ? "−" : "") + (Math.abs(rate) * 100).toFixed(2);
const balls = (key) => ({ any: "1球以上", "5+": "5球以上" }[key] || key + "球");
const runLabel = (key) => key === "7+" ? "7点以上" : key + "点";
const teamName = (key) => priority[key] || key;
const distinctTeams = Object.keys(priority);
const escapeHTML = (value) => String(value).replace(/[&<>"']/g, (c) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
}[c]));

let data;
const sample = (group, bucket) => data.groups[group]?.[state.phase][bucket];

function shortSample(n, matches) {
  return n < data.metadata.minimum.n || matches < data.metadata.minimum.matches;
}

function row(label, values, n, matches) {
  return `<tr><th scope="row">${label}</th><td>${share(values[0], n)}</td>
    <td>${fmt(values[0])} / ${fmt(n)}</td><td>${interval(values)}</td><td>${fmt(matches)}</td></tr>`;
}

function resultsTable(caption, rows) {
  return `<div class="table-wrap"><table><caption>${caption}</caption>
    <thead><tr><th scope="col">結果</th><th scope="col">割合</th><th scope="col">件数 / 投球</th>
      <th scope="col">95%区間</th><th scope="col">試合</th></tr></thead><tbody>${rows.join("")}</tbody></table></div>`;
}

function bar(values, n, max = 1) {
  const [events, lo, hi] = values;
  const width = (x) => (Math.min(x / max, 1) * 100).toFixed(3) + "%";
  const errorBar = lo === null ? "" :
    `<i class="interval" style="--low:${width(lo)};--span:${width(Math.min(hi, max) - lo)}"></i>`;
  return `<div class="track" aria-hidden="true"><i class="bar" style="--bar:${width(n ? events / n : 0)}"></i>${errorBar}</div>`;
}

function wicketScale(cells) {
  const high = Math.max(.10, ...cells.filter(Boolean).map((cell) =>
    cell.metrics.wicket[2] ?? (cell.n ? cell.metrics.wicket[0] / cell.n : 0)));
  return Math.min(1, Math.ceil(high * 20) / 20);
}

function axis(max) {
  return `<div class="axis" aria-hidden="true"><span>0%</span><span>${Math.round(max * 100)}%</span></div>`;
}

function renderNext() {
  const c = sample("world", state.streak);
  const length = parseInt(state.streak, 10);
  $("past-balls").innerHTML = Array.from({ length: 5 }, (_, i) =>
    i >= 5 - length ? '<span class="ball">·</span>' : '<span class="ball empty"></span>').join("");
  $("next-sample").textContent = `${phases[state.phase]}・直前 ${balls(state.streak)} ／ ${fmt(c.n)}投球・${fmt(c.matches)}試合`;

  const cards = [["wicket", "アウト"], ["score", "得点"], ["boundary", "バウンダリー"], ["escape", "2球以内に脱出"]];
  $("next-metrics").innerHTML = cards.map(([metric, label]) => {
    const n = metric === "escape" ? c.escapeN : c.n;
    return `<div class="metric ${metric}"><strong>${share(c.metrics[metric][0], n)}</strong><span>${label}</span></div>`;
  }).join("");

  $("run-bars").innerHTML = '<ul class="run-grid" aria-label="チーム得点の分布">' + runBins.map((key) => {
    const n = c.runs[key][0];
    return `<li><b>${share(n, c.n)}</b><span class="run-track" aria-hidden="true">
      <i style="--bar:${c.n ? n / c.n * 100 : 0}%"></i></span><span>${runLabel(key)}</span></li>`;
  }).join("") + "</ul>";
  const metrics = Object.entries(labels).map(([metric, label]) =>
    row(label, c.metrics[metric], metric === "escape" ? c.escapeN : c.n, metric === "escape" ? c.escapeMatches : c.matches));
  $("next-details").innerHTML = resultsTable("次球と脱出の割合", metrics) +
    `<p class="note">得点とアウトが同時に起きた投球は ${fmt(c.scoreAndWicket)}球。</p>`;
  $("run-details").innerHTML = resultsTable("チーム得点の分布",
    runBins.map((key) => row(runLabel(key), c.runs[key], c.n, c.matches)));
}

function renderWorld() {
  const cells = streaks.map((key) => sample("world", key));
  const first = cells[0], last = cells.at(-1);
  const gap = state.phase === "all" ? data.contrasts.worldWicket5Vs0 : data.contrasts.worldWicket5Vs0ByPhase[state.phase];
  const range = gap ? ` アウト率の差の95%区間は ${gap.ci.map(points).join("〜")} ポイント。` : "";
  $("world-reading").textContent = `${phases[state.phase]}で0球と5球以上を比べると、次球もドットになる割合は ${share(first.metrics.dot[0], first.n)} から ${share(last.metrics.dot[0], last.n)}、アウト率は ${share(first.metrics.wicket[0], first.n)} から ${share(last.metrics.wicket[0], last.n)}。${range}`;
  $("world-trends").innerHTML = ["dot", "score", "wicket"].map((metric) => {
    const scale = metric === "wicket" ? wicketScale(cells) : 1;
    return `<section class="trend ${metric}"><h3>${labels[metric]}</h3>${axis(scale)}<ol>` +
      cells.map((c, i) => {
        const key = streaks[i], values = c.metrics[metric];
        return `<li class="trend-row${state.streak === key ? " selected" : ""}">
          <span>${key === "5+" ? "5+球" : balls(key)}</span>${bar(values, c.n, scale)}<b>${share(values[0], c.n)}</b>
          <small>${fmt(values[0])} / ${fmt(c.n)}球 · 区間 ${interval(values)}</small></li>`;
      }).join("") + "</ol></section>";
  }).join("");
}

function comparisonMeasure(group, key, metric) {
  const c = sample(group, key);
  if (!c) return { values: [0, null, null], n: 0, matches: 0 };
  if (metric === "frequency") {
    const base = sample(group, "all");
    return { values: c.frequency, n: base.n, matches: base.matches };
  }
  if (metric === "escape") return { values: c.metrics.escape, n: c.escapeN, matches: c.escapeMatches };
  return { values: c.metrics[metric], n: c.n, matches: c.matches };
}

function renderComparison(id, groups, names, key) {
  const context = groups.map((group) => sample(group, key));
  const header = names.map((name, i) => {
    const c = context[i];
    const coverage = data.metadata.countries[groups[i].slice(5)];
    const date = coverage?.from ? ` ／ 打撃記録 ${coverage.from.slice(0, 4)}〜${coverage.to.slice(0, 4)}年` : "";
    const recordedMatches = coverage ? ` ／ 収録 ${fmt(coverage.archiveMatches)}試合` : "";
    const status = c?.n ? `${fmt(c.n)}投球・${fmt(c.matches)}試合${shortSample(c.n, c.matches) ? "（参考値）" : ""}`
      : coverage || c ? "この条件の投球なし" : "収録データなし";
    return `<div class="series-${i === 0 ? "a" : "b"}"><strong>${escapeHTML(name)}</strong>
      <span>${status}${recordedMatches}${date}</span></div>`;
  }).join("");
  const measurements = [
    ["frequency", key === "0" ? "直前0球の割合" : key === "any" ? "連鎖の発生頻度" : balls(key) + "の連鎖の頻度"],
    ["wicket", "次球でアウト"], ["score", "次球で得点"], ["escape", "2球以内に得点して脱出"],
  ];
  const cards = measurements.map(([metric, label]) => {
    const scale = metric === "wicket" ? wicketScale(context) : 1;
    const measures = groups.map((group, i) => {
      const { values, n, matches } = comparisonMeasure(group, key, metric);
      const stats = n ? `${fmt(values[0])} / ${fmt(n)}球` : "対象投球なし";
      const caution = n && shortSample(n, matches) ? ' <span class="sample-warning">参考値</span>' : "";
      return `<div class="compare-measure series-${i === 0 ? "a" : "b"}">
        <div class="measure-value"><strong>${escapeHTML(names[i])}</strong><b>${share(values[0], n)}</b>
        <small>${stats} · 区間 ${interval(values)}${caution}</small></div>${bar(values, n, scale)}</div>`;
    }).join("");
    return `<section class="compare-metric"><h3>${label}</h3>${axis(scale)}${measures}</section>`;
  }).join("");
  $(id).innerHTML = `<div class="comparison-header">${header}</div><p class="note">${phases[state.phase]} ／ 直前 ${balls(key)}。
    頻度の分母はその局面の全投球です。</p><div class="compare-grid">${cards}</div>`;
}

function renderComparisons() {
  const key = $("compare-streak").value === "any" ? "any" : state.streak;
  const a = $("team-a").value, b = $("team-b").value;
  renderComparison("country-chart", [`team:${a}`, `team:${b}`], [teamName(a), teamName(b)], key);
  const exclude = $("exclude-japan").checked;
  renderComparison("japan-chart", ["team:Japan", exclude ? "world-ex-japan" : "world"],
    ["日本", exclude ? "世界（日本の打撃を除く）" : "世界全体"], key);
}

function renderAdjusted() {
  const model = data.adjustedWicket;
  if (!model) return;
  const rows = streaks.filter((key) => model.oddsRatios[key]).map((key) => {
    const estimate = model.oddsRatios[key];
    const ci = estimate.ci ? estimate.ci.map((v) => v.toFixed(3)).join("〜") : "基準";
    const raw = data.groups.world.all[key];
    return `<tr><th scope="row">${balls(key)}</th><td>${estimate.oddsRatio.toFixed(3)}</td>
      <td>${ci}</td><td>${fmt(raw.metrics.wicket[0])} / ${fmt(raw.n)}</td></tr>`;
  });
  $("adjusted").innerHTML = `<div class="table-wrap"><table>
    <caption>調整後のオッズ比（全局面・${fmt(model.n)}投球・${fmt(model.matches)}試合）</caption>
    <thead><tr><th scope="col">直前の連続数</th><th scope="col">オッズ比</th>
      <th scope="col">95%区間</th><th scope="col">アウト / 投球</th></tr></thead><tbody>${rows.join("")}</tbody></table></div>`;
  $("adjusted-section").hidden = false;
}

function renderCoverage() {
  const m = data.metadata;
  $("coverage").innerHTML = `<span>${fmt(m.matches)}試合 ／ ${fmt(m.deliveries)}投球 ／</span>
    <span>${escapeHTML(m.from + "〜" + m.to)}</span>`;
  $("coverage").hidden = false;
  const withheld = m.withheldMatches === null ? "" : ` 配布元は別途${fmt(m.withheldMatches)}試合を非提供としています。`;
  $("source-details").textContent = `Cricsheet公式JSON ${m.jsonVersions.join(" / ")}（${m.retrieved}取得）。
    収録${fmt(m.archiveMatches)}試合のうち、通常イニングに記録投球のある${fmt(m.matches)}試合を集計しました。
    ${fmt(m.deliveries)}投球のうち合法球は${fmt(m.legal)}球。
    ${fmt(m.excludedSuperOvers)}スーパーオーバー、${fmt(m.excludedSuperOverDeliveries)}投球を除外しています。${withheld}`;
  const japan = m.countries.Japan;
  $("japan-context").textContent = japan?.battingMatches
    ? `日本は収録${fmt(japan.archiveMatches)}試合のうち${fmt(japan.battingMatches)}試合で打撃記録があり、対象期間は${japan.from}〜${japan.to}です。`
    : "日本の打撃記録がありません。";
  const rows = Object.entries(m.countries).map(([team, c]) =>
    `<tr><th scope="row">${escapeHTML(teamName(team))}</th><td>${fmt(c.archiveMatches)}</td><td>${fmt(c.matches)}</td>
    <td>${fmt(c.battingMatches)}</td><td>${c.from ? escapeHTML(c.from + "〜" + c.to) : "—"}</td></tr>`);
  $("teams-coverage").innerHTML = `<div class="table-wrap"><table>
    <caption>Cricsheet収録の${fmt(rows.length)}チーム</caption><thead><tr><th scope="col">打撃側</th>
    <th scope="col">収録</th><th scope="col">分析対象</th><th scope="col">打撃記録あり</th>
    <th scope="col">打撃記録の期間</th></tr></thead><tbody>${rows.join("")}</tbody></table></div>`;
  $("coverage-table").hidden = false;
}

function selectButtons(id, dataKey, update) {
  const control = $(id);
  control.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    state[dataKey] = button.dataset[dataKey];
    for (const option of control.querySelectorAll("button")) {
      option.setAttribute("aria-pressed", String(option === button));
    }
    update();
  });
}

async function loadData() {
  if (location.protocol === "file:") {
    // Browsers block fetch() from a local file, but allow adjacent classic scripts.
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "data/dot-ball-pressure-local.js";
      script.onload = () => {
        resolve(globalThis.crittDotBallPressureData);
        delete globalThis.crittDotBallPressureData;
      };
      script.onerror = () => reject(new Error("Local data script could not be loaded"));
      document.head.append(script);
    });
  }
  const response = await fetch("data/dot-ball-pressure.json");
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

async function start() {
  const status = $("load-status");
  status.hidden = false;
  try {
    data = await loadData();
    if (data?.metadata?.schema !== 1) throw new Error("Unsupported data schema");

    const listed = Object.keys(data.metadata.countries);
    const teams = [...distinctTeams, ...listed.filter((team) => !distinctTeams.includes(team))];
    for (const id of ["team-a", "team-b"]) {
      const select = $(id);
      select.replaceChildren(...teams.map((team) =>
        new Option(teamName(team) + (listed.includes(team) ? "" : "（収録なし）"), team)));
    }
    $("team-a").value = "Japan";
    $("team-b").value = "India";
    renderCoverage();
    renderAdjusted();
    const render = () => { renderNext(); renderWorld(); renderComparisons(); };
    render();
    selectButtons("phases", "phase", render);
    selectButtons("streaks", "streak", render);
    for (const id of ["team-a", "team-b", "compare-streak", "exclude-japan"]) {
      $(id).addEventListener("change", renderComparisons);
    }
    $("explore").hidden = false;
    status.hidden = true;
  } catch (error) {
    status.textContent = location.protocol === "file:"
      ? "集計を読み込めませんでした。HTMLと一緒に data フォルダーを配置し、開き直してください。"
      : "集計を読み込めませんでした。ページの再読み込みをお試しください。";
    console.error(error);
  }
}

start();
