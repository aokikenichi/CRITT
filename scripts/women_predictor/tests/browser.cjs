// Offline artifact integration test. Launch requires the host's browser permission.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { pathToFileURL } = require("node:url");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "/Users/aoki/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");

const htmlPath = path.resolve(process.env.WOMEN_PREDICTOR_HTML || path.join(__dirname, "../../../japan-women-t20-predictor.html"));
const reports = path.resolve(__dirname, "../reports/wasp");
const html = fs.readFileSync(htmlPath, "utf8");
const scripts = [...html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)];
assert.equal(scripts.length, 3, "one payload plus two inline scripts");
const payload = JSON.parse(scripts[0][2]);
const sandbox = {};
vm.runInNewContext(scripts[1][2], sandbox);
const predictor = sandbox.WASPStandalonePredictor;
const fmt = (value, digits = 1) => value.toLocaleString("ja-JP", { maximumFractionDigits: digits });
const pct = value => value === null ? "—" : (value * 100).toFixed(1) + "%";
const firstInput = { batting_team: "Japan", bowling_team: "Indonesia", runs: 62, wickets: 3,
  completed: { overs: 10, balls: 0 }, quota: { overs: 20, balls: 0 }, venue: null, use_japan_correction: true };
const chaseInput = { chasing_team: "Japan", defending_team: "Indonesia", target: 130, current_score: 76,
  wickets: 4, balls_remaining: 48, target_ball_limit: { overs: 20, balls: 0 }, venue: null, use_japan_correction: true };

assert.equal(payload.metadata.gender, "female");
assert.equal(payload.metadata.team_type, "international");
assert.equal(payload.metadata.match_type, "T20");
assert.equal(payload.japan_matches.length, 45);
assert.equal(Object.keys(payload.replays).length, 45);
assert.ok(!/日本男子|\bMEN'S T20/.test(html));
assert.ok(html.includes("connect-src 'none'"));
assert.ok(payload.metadata.replay_note.includes("未学習試合の性能評価ではありません"));
for (const match of payload.japan_matches) {
  assert.equal(match.gender, "female");
  assert.equal(match.team_type, "international");
  assert.equal(match.match_type, "T20");
  const replay = payload.replays[match.match_id];
  assert.ok(replay.first_innings.length > 0, `first score replay missing: ${match.match_id}`);
  if (!match.first_innings_eligible) assert.ok(replay.first_innings.every(p => p.selected === null));
  if (!match.chase_eligible && (!match.reduced_match_eligible || !payload.reduced_match_enabled)) {
    assert.ok(replay.chase.every(p => p.selected === null));
  }
  if (!match.first_innings_eligible || !match.chase_eligible) assert.ok(match.model_exclusions.length > 0);
}
assert.ok(Object.values(payload.japan_gates).every(gate => !gate.enabled));
assert.equal(payload.reduced_match_enabled, false);
for (const tossWinner of ["Japan", "Indonesia", null]) {
  const input = { ...chaseInput, toss_winner: tossWinner };
  const state = predictor.buildState(input, payload, 2);
  assert.equal(state.batting_team_won_toss, tossWinner === null ? null : tossWinner === "Japan");
  const result = predictor.predictChase(input, payload);
  if (tossWinner === null) {
    assert.equal(result.comparison.selected, result.comparison.global);
    assert.ok(result.warnings.some(text => text.includes("トス結果が不明")));
  }
}

async function settle(page) {
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
}

const routes = ["overview", "first", "chase", "replay", "evaluation"];

async function assertRouteLayout(page, route, viewport) {
  await page.locator(`.page-nav [data-route="${route}"]`).click();
  await settle(page);
  assert.deepEqual(await page.locator('[data-view]:visible').evaluateAll(nodes => nodes.map(node => node.dataset.view)), [route],
    `one visible screen: ${viewport} ${route}`);
  assert.deepEqual(await page.locator('.page-nav [aria-current="page"]').evaluateAll(nodes => nodes.map(node => node.dataset.route)), [route],
    `current navigation tab: ${viewport} ${route}`);
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    `horizontal overflow: ${viewport} ${route}`);
}

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM_EXECUTABLE ||
    "/Users/aoki/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing" });
  try {
    const context = await browser.newContext({ offline: true, viewport: { width: 1280, height: 900 } });
    const page = await context.newPage();
    const errors = [], external = [];
    page.on("pageerror", error => errors.push(error.message));
    page.on("request", request => { if (/^https?:/.test(request.url())) external.push(request.url()); });
    await page.goto(pathToFileURL(htmlPath).href);
    await settle(page);
    assert.ok((await page.locator("#overview-title").textContent()).includes("日本女子代表"));
    assert.equal(await page.locator(".site-global .brand strong").textContent(), "CRITT");
    assert.equal(await page.locator(".site-global .brand").getAttribute("href"), "index.html");
    assert.equal(await page.locator(".page-nav-title").textContent(), "T20 Match Predictor");
    assert.deepEqual(await page.locator(".global-nav a").evaluateAll(nodes => nodes.map(node => [node.textContent.trim(), node.getAttribute("href")])), [
      ["ホーム", "index.html"], ["物語", "index.html#stories"], ["遊ぶ", "index.html#play"],
      ["知る", "index.html#guide"], ["データ分析", "data-analytics.html"], ["CRITTとは", "about.html"]
    ]);
    assert.deepEqual(await page.locator(".page-nav a").evaluateAll(nodes => nodes.map(node => [node.textContent.trim(), node.dataset.route])), [
      ["概要", "overview"], ["先攻予測", "first"], ["追走予測", "chase"], ["リプレイ", "replay"], ["モデル評価", "evaluation"]
    ]);
    assert.equal(await page.locator(".brand-mark, .hero-aside, .site-header > .status-pill").count(), 0);
    assert.deepEqual(await page.locator("#view-overview h2").allTextContents(), [
      "使用データ", "評価スナップショット", "WASPとは？", "使い方"
    ]);
    assert.equal(await page.locator("#overview-gates, #evaluation-gates, .gate-list").count(), 0);
    assert.ok(!(await page.locator("#view-overview h2, #view-evaluation h2").allTextContents()).some(title =>
      title === "機能の有効状態" || title === "補正・短縮戦"));
    const correctionNote = await page.locator("#view-overview #correction-note").textContent();
    for (const phrase of ["強い国・弱い国", "十分な日本女子代表戦", "追加補正", "適用していません"]) {
      assert.ok(correctionNote.includes(phrase), `correction note explains: ${phrase}`);
    }
    assert.deepEqual(await page.locator("#summary-cards .metric-card > span").allTextContents(), [
      "女子T20試合", "deliveries", "収録チーム", "日本女子代表戦"
    ]);
    assert.deepEqual(await page.locator("#summary-cards .metric-card > strong").allTextContents(), ["2,141", "486,540", "90", "45"]);
    const coverageText = await page.locator("#overview-data-text").textContent();
    assert.ok(coverageText.includes(payload.metadata.date_from) && coverageText.includes(payload.metadata.date_to));
    assert.ok(coverageText.includes("453,614") && coverageText.includes("合法球"));
    assert.equal(await page.locator('footer a[href="https://cricsheet.org/"]').count(), 1);
    assert.ok((await page.locator("#data-cutoff").textContent()).includes(payload.metadata.source_cutoff));
    assert.ok((await page.locator("#generated-at").textContent()).startsWith("最終更新"));
    assert.equal(await page.locator("#view-overview #replay-model-note, #view-replay #replay-model-note").count(), 0);
    assert.equal(await page.locator("#view-evaluation #replay-model-note").textContent(), payload.metadata.replay_note);
    assert.deepEqual(await page.locator("#first-form input, #first-form select").evaluateAll(nodes => nodes.map(node => node.name)), [
      "batting_team", "bowling_team", "runs", "wickets", "completed_overs", "completed_balls",
      "quota_overs", "quota_balls", "venue", "use_japan_correction"
    ]);
    assert.deepEqual(await page.locator("#chase-form input, #chase-form select").evaluateAll(nodes => nodes.map(node => node.name)), [
      "chasing_team", "defending_team", "target", "current_score", "wickets", "balls_remaining",
      "limit_overs", "limit_balls", "toss_winner", "venue", "use_japan_correction"
    ]);
    fs.mkdirSync(reports, { recursive: true });
    await page.screenshot({ path: path.join(reports, "browser-overview.png"), fullPage: true });
    await page.locator('nav [data-route="first"]').click();
    await page.locator('#first-form button[type="submit"]').click();
    await page.locator("#first-results:not([hidden])").waitFor();
    assert.equal(await page.locator("#first-selected").textContent(), fmt(predictor.predictFirst(firstInput, payload).comparison.selected));
    await page.locator('nav [data-route="chase"]').click();
    for (const [choice, tossWinner] of [["unknown", null], ["chasing", "Japan"], ["defending", "Indonesia"]]) {
      const expected = pct(predictor.predictChase({ ...chaseInput, toss_winner: tossWinner }, payload).comparison.selected);
      await page.locator('#chase-form select[name="toss_winner"]').selectOption(choice);
      await page.locator('#chase-form button[type="submit"]').click();
      await page.waitForFunction(value => document.querySelector("#chase-selected").textContent === value, expected);
      assert.equal((await page.locator("#chase-warnings").textContent()).includes("トス結果が不明"), choice === "unknown");
    }
    for (const [score, wickets, remaining, expected, note] of [
      [130, 4, 48, "100.0%", "target到達"], [128, 10, 48, "0.0%", "追走失敗"],
      [128, 4, 0, "0.0%", "追走失敗"], [129, 10, 0, "—", "規定tie"]
    ]) {
      await page.locator('#chase-form [name="current_score"]').fill(String(score));
      await page.locator('#chase-form [name="wickets"]').fill(String(wickets));
      await page.locator('#chase-form [name="balls_remaining"]').fill(String(remaining));
      await page.locator('#chase-form button[type="submit"]').click();
      await page.waitForFunction(value => document.querySelector("#chase-selected").textContent === value, expected);
      assert.ok((await page.locator("#chase-terminal").textContent()).includes(note));
      assert.equal(await page.locator("#scenario-content").isVisible(), false);
    }
    await page.locator('nav [data-route="replay"]').click();
    assert.equal(await page.locator(".match-button").count(), 45);
    const included = payload.japan_matches.find(match => match.first_innings_eligible && match.chase_eligible);
    const excluded = payload.japan_matches.filter(match => !match.first_innings_eligible || !match.chase_eligible);
    assert.ok(included);
    assert.ok(excluded.length > 0);
    for (const match of [included, ...excluded]) {
      await page.locator(`[data-match-id="${match.match_id}"]`).click();
      await settle(page);
      assert.ok((await page.locator("#replay-title").textContent()).includes("Japan"));
      const replay = payload.replays[match.match_id];
      const finalScore = replay.first_innings.at(-1).runs_so_far;
      assert.ok((await page.locator("#replay-accessible-summary").textContent()).includes(`最終得点 ${fmt(finalScore, 0)}`));
      const status = await page.locator("#replay-eligibility").textContent();
      if (!match.first_innings_eligible || !match.chase_eligible) {
        assert.ok(status.includes("対象外"));
        assert.equal(await page.locator("#replay-eligibility").isVisible(), true);
      } else {
        assert.equal(await page.locator("#replay-eligibility").isVisible(), false);
      }
      if (!match.first_innings_eligible) assert.equal(await page.locator("#replay-first-chart-title").textContent(), "第1イニング 実得点の推移");
      if (!match.chase_eligible) assert.equal(await page.locator("#replay-chase-chart-title").textContent(), "第2イニング 実得点の推移");
    }
    await page.evaluate(() => window.scrollTo(0, 0));
    await settle(page);
    await page.screenshot({ path: path.join(reports, "browser-replay.png"), fullPage: true });
    await page.locator('nav [data-route="evaluation"]').click();
    const evalText = await page.locator("#evaluation-cards").textContent();
    assert.ok(evalText.includes(fmt(payload.evaluation.first_innings.locked_test.match_macro_mae)));
    assert.ok(evalText.includes(fmt(payload.evaluation.chase.locked_test.match_macro_brier, 3)));
    assert.ok((await page.locator("#candidate-table").textContent()).includes("Model 0"));
    assert.equal(await page.locator("#evaluation-gates").count(), 0);
    for (const route of routes) await assertRouteLayout(page, route, "desktop");
    await page.setViewportSize({ width: 390, height: 844 });
    for (const route of routes) await assertRouteLayout(page, route, "mobile");
    await page.locator('nav [data-route="overview"]').click();
    await page.evaluate(() => window.scrollTo(0, 0));
    await settle(page);
    await page.screenshot({ path: path.join(reports, "browser-mobile.png"), fullPage: true });
    assert.deepEqual(errors, []);
    assert.deepEqual(external, []);
    const result = { html: htmlPath, offline: true, female_replays: 45, excluded_replays_checked: excluded.length,
      first_form_parity: true, published_ui_alignment: true, desktop_routes_checked: 5,
      chase_toss_cases: 3, terminal_cases: 4, mobile_width: 390,
      mobile_routes_checked: 5, page_errors: errors, external_requests: external };
    fs.writeFileSync(path.join(reports, "browser-validation.json"), JSON.stringify(result, null, 2) + "\n");
    console.log(JSON.stringify(result, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
