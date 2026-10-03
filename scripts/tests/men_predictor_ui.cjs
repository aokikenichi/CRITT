// Standalone men's UI regression using files and VM only; no browser/network access.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const htmlPath = path.resolve(process.argv[2] || path.join(__dirname, "../../japan-t20-predictor.html"));
const baselinePath = process.argv[3] && path.resolve(process.argv[3]);
function readArtifact(filePath) {
  const html = fs.readFileSync(filePath, "utf8");
  const scripts = [...html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)];
  assert.equal(scripts.length, 3, "one payload, predictor and UI script");
  return { html, scripts, payload: JSON.parse(scripts[0][2]), markup: html.slice(0, scripts[0].index) };
}
const artifact = readArtifact(htmlPath);
const { scripts, payload, markup } = artifact;
const appSource = scripts[2][2];
for (const id of ["overview-gates", "evaluation-gates"]) {
  assert.ok(!new RegExp(`id=["']${id}["']`).test(markup), `removed panel: ${id}`);
  assert.ok(!appSource.includes(`#${id}`), `no UI reference to removed panel: ${id}`);
}
assert.ok(!/class=["'][^"']*\bgate-list\b/.test(markup), "gate lists removed");
assert.ok(!/renderGates\s*\(/.test(appSource), "gate renderer and calls removed");
const headings = [...markup.matchAll(/<h2\b[^>]*>([\s\S]*?)<\/h2>/g)].map(match => match[1].replace(/<[^>]+>/g, "").trim());
assert.ok(!headings.includes("機能の有効状態"), "Top inactive-state heading removed");
assert.ok(!headings.includes("補正・短縮戦"), "evaluation inactive-state heading removed");
assert.ok(headings.includes("評価スナップショット") && headings.includes("候補モデル"), "evaluation content retained");
const note = markup.match(/<([a-z][a-z0-9]*)\b[^>]*\bid=["']correction-note["'][^>]*>([\s\S]*?)<\/\1>/i);
assert.ok(note, "correction note is present");
const noteText = note[2].replace(/<[^>]+>/g, "").trim();
for (const phrase of ["強い国・弱い国", "相手の実力差", "追加補正", "過去試合のデータ量", "検証での精度改善", "十分でない", "適用していません"]) {
  assert.ok(noteText.includes(phrase), `correction note explains: ${phrase}`);
}
assert.ok(!noteText.includes("日本女子"), "men's note names the correct team");
assert.equal(payload.reduced_match_enabled, false, "shortened-match gate remains disabled");
assert.ok(Object.values(payload.japan_gates).every(gate => !gate.enabled), "Japan role gates remain disabled");
assert.ok(Object.values(payload.japan_gates).some(gate => gate.fallback_reason === "insufficient_history"), "history shortage retained");
assert.ok(Object.values(payload.japan_gates).some(gate => gate.fallback_reason === "activation_gate_failed"), "failed validation improvement retained");

const initialization = "  initialize();\n})();";
assert.equal(appSource.split(initialization).length, 2, "one initialization entry point");
const instrumented = appSource.replace(initialization,
  "  globalThis.menUiTestHooks = { renderOverview, renderEvaluation, ensureReducedSupported };\n})();");

function createRuntime(runtimePayload = payload) {
  const permitted = ["#summary-cards", "#overview-evaluation", "#evaluation-cards", "#phase-table", "#candidate-table", "#model-limitations"];
  const nodes = new Map(permitted.map(selector => [selector, { innerHTML: "", textContent: "" }]));
  const requested = [];
  const sandbox = {
    document: {
      querySelector(selector) {
        requested.push(selector);
        if (selector === "#wasp-standalone-data") return { textContent: JSON.stringify(runtimePayload) };
        assert.ok(nodes.has(selector), `unexpected or removed DOM reference: ${selector}`);
        return nodes.get(selector);
      }
    }
  };
  vm.runInNewContext(scripts[1][2], sandbox, { filename: htmlPath + ":predictor" });
  vm.runInNewContext(instrumented, sandbox, { filename: htmlPath + ":ui" });
  return { sandbox, nodes, requested };
}

const runtime = createRuntime();
const predictor = runtime.sandbox.WASPStandalonePredictor;
assert.equal(typeof predictor, "object", "predictor runtime retained");
assert.ok(Object.isFrozen(predictor), "predictor public interface remains frozen");
for (const method of ["predictFirst", "predictChase", "buildState"]) {
  assert.equal(typeof predictor[method], "function", `predictor method retained: ${method}`);
}
runtime.sandbox.menUiTestHooks.renderOverview();
runtime.sandbox.menUiTestHooks.renderEvaluation();
for (const selector of ["#summary-cards", "#overview-evaluation", "#evaluation-cards", "#phase-table", "#candidate-table", "#model-limitations"]) {
  assert.ok(runtime.nodes.get(selector).innerHTML.length > 0, `rendered retained content: ${selector}`);
}
assert.ok(runtime.nodes.get("#summary-cards").innerHTML.includes("男子T20試合"), "men's data labels retained");
assert.ok(runtime.nodes.get("#candidate-table").innerHTML.includes("Model 0"), "candidate comparison retained");
assert.ok(!/Japan correction\b/i.test(runtime.nodes.get("#model-limitations").innerHTML), "duplicate gate limitation removed from rendered list");
assert.ok(!runtime.requested.some(selector => selector.includes("-gates")), "renders avoid removed gate elements");
assert.doesNotThrow(() => runtime.sandbox.menUiTestHooks.ensureReducedSupported(120), "20-over input remains available");
assert.throws(() => runtime.sandbox.menUiTestHooks.ensureReducedSupported(90),
  error => error.code === "unsupported_reduced_match", "shortened input remains blocked by data gate");
const enabledRuntime = createRuntime({ ...payload, reduced_match_enabled: true });
assert.doesNotThrow(() => enabledRuntime.sandbox.menUiTestHooks.ensureReducedSupported(90), "enabled shortened-match data gate remains respected");

if (baselinePath) {
  const baseline = readArtifact(baselinePath);
  assert.equal(scripts[0][2], baseline.scripts[0][2], "raw model/evaluation/replay payload unchanged");
  assert.equal(scripts[1][2], baseline.scripts[1][2], "predictor runtime unchanged");
}
console.log(JSON.stringify({ html: htmlPath, browser_launched: false, gate_panels_removed: true,
  accurate_correction_note: true, retained_panels_rendered: 6, reduced_match_guard_preserved: true,
  predictor_methods: ["predictFirst", "predictChase", "buildState"],
  model_content_sha256: payload.metadata.model_content_sha256, baseline_compared: Boolean(baselinePath) }));
