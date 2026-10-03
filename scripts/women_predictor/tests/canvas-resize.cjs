// Filesystem/VM regression for canvas backing dimensions; no browser is launched.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const sourcePath = path.resolve(process.argv[2] || path.join(__dirname,
  "../src/cricket_japan_bi/wasp/export/web/standalone.js"));
let source = fs.readFileSync(sourcePath, "utf8");
if (sourcePath.endsWith(".html")) {
  const scripts = [...source.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)];
  assert.equal(scripts.length, 3, "standalone HTML has payload, predictor and UI scripts");
  source = scripts[2][1];
}
const initialization = "  initialize();\n})();";
assert.equal(source.split(initialization).length, 2, "one UI initialization entry point");
const testSource = source.replace(initialization,
  "  globalThis.canvasTestHooks = { prepareCanvas, drawReplayFirst, drawReplayChase, drawBarChart };\n})();");

class MockCanvas {
  constructor(height, width = 640) {
    this.attributes = new Map([["width", "300"], ["height", String(height)]]);
    this.dataset = {};
    this.style = {};
    this.hidden = false;
    this.parentElement = { clientWidth: width };
    this.logicalWidth = width;
    this.transforms = [];
    this.clears = [];
    this.context = new Proxy({
      setTransform: (...args) => this.transforms.push(args),
      clearRect: (...args) => this.clears.push(args),
      measureText: text => ({ width: String(text).length * 6 })
    }, {
      get: (target, key) => key in target ? target[key] : () => {}
    });
  }
  // HTMLCanvasElement width/height properties reflect their content attributes.
  get height() { return Number(this.attributes.get("height")); }
  set height(value) { this.attributes.set("height", String(Math.floor(Number(value)))); }
  get width() { return Number(this.attributes.get("width")); }
  set width(value) { this.attributes.set("width", String(Math.floor(Number(value)))); }
  getAttribute(name) { return this.attributes.has(name) ? this.attributes.get(name) : null; }
  setAttribute(name, value) { this.attributes.set(name, String(value)); }
  getBoundingClientRect() {
    return { width: this.logicalWidth, height: parseFloat(this.style.height) || this.height };
  }
  getContext(kind) { assert.equal(kind, "2d"); return this.context; }
}

function createRuntime(ratio) {
  const titles = new Map([
    ["#replay-first-chart-title", { textContent: "" }],
    ["#replay-chase-chart-title", { textContent: "" }]
  ]);
  const sandbox = {
    devicePixelRatio: ratio,
    document: {
      querySelector: selector => selector === "#wasp-standalone-data" ? { textContent: "{}" } : titles.get(selector)
    }
  };
  vm.runInNewContext(testSource, sandbox, { filename: sourcePath });
  return sandbox;
}

function assertStableCanvas(canvas, height, ratio, label) {
  const effectiveRatio = Math.min(ratio || 1, 2);
  assert.equal(canvas.style.height, height + "px", label + ": logical CSS height");
  assert.equal(canvas.height, Math.floor(height * effectiveRatio), label + ": backing height");
  assert.equal(canvas.getAttribute("height"), String(canvas.height), label + ": reflected height attribute");
  assert.equal(canvas.width, Math.floor(canvas.logicalWidth * effectiveRatio), label + ": backing width");
  assert.deepEqual(canvas.transforms.at(-1), [effectiveRatio, 0, 0, effectiveRatio, 0, 0], label + ": pixel ratio transform");
  assert.deepEqual(canvas.clears.at(-1), [0, 0, canvas.logicalWidth, height], label + ": logical clear bounds");
}

const matches = [
  {
    first: [{ legal_balls: 1, runs: 1, selected: 124 }, { legal_balls: 60, runs: 62, selected: 138, event: "four" }],
    chase: [{ legal_balls: 1, runs: 2, selected: .46 }, { legal_balls: 60, runs: 73, selected: .62, event: "wicket" }]
  },
  {
    first: [{ legal_balls: 1, runs: 0, selected: null }, { legal_balls: 120, runs: 93, selected: null }],
    chase: [{ legal_balls: 1, runs: 1, selected: null }, { legal_balls: 80, runs: 67, selected: null }]
  },
  { first: [], chase: [] }
];

let draws = 0;
for (const ratio of [1, 1.5, 2]) {
  const runtime = createRuntime(ratio);
  const preparedCanvas = new MockCanvas(320);
  for (let repeat = 0; repeat < 12; repeat += 1) {
    const prepared = runtime.canvasTestHooks.prepareCanvas(preparedCanvas);
    assert.equal(prepared.height, 320, `DPR ${ratio}, prepare ${repeat}: logical return height`);
    assertStableCanvas(preparedCanvas, 320, ratio, `DPR ${ratio}, prepare ${repeat}`);
    draws += 1;
  }
  const firstCanvas = new MockCanvas(330);
  const chaseCanvas = new MockCanvas(330);
  for (let switchIndex = 0; switchIndex < 18; switchIndex += 1) {
    const match = matches[switchIndex % matches.length];
    runtime.canvasTestHooks.drawReplayFirst(firstCanvas, match.first);
    runtime.canvasTestHooks.drawReplayChase(chaseCanvas, match.chase);
    assertStableCanvas(firstCanvas, 330, ratio, `DPR ${ratio}, Replay first switch ${switchIndex}`);
    assertStableCanvas(chaseCanvas, 330, ratio, `DPR ${ratio}, Replay chase switch ${switchIndex}`);
    draws += 2;
  }
}

const changingRuntime = createRuntime(1);
const changingCanvas = new MockCanvas(330);
for (const ratio of [1, 2, 1.5, 1, 2, 1.5, 2, 1]) {
  changingRuntime.devicePixelRatio = ratio;
  changingCanvas.logicalWidth = ratio === 1 ? 360 : 640;
  for (let repeat = 0; repeat < 3; repeat += 1) {
    changingRuntime.canvasTestHooks.drawReplayChase(changingCanvas, matches[repeat].chase);
    assertStableCanvas(changingCanvas, 330, ratio, `DPR change ${ratio}, draw ${repeat}`);
    draws += 1;
  }
}

// The same preparation path is shared by scenario charts.
const barCanvas = new MockCanvas(320);
for (let repeat = 0; repeat < 6; repeat += 1) {
  changingRuntime.devicePixelRatio = 2;
  changingRuntime.canvasTestHooks.drawBarChart(barCanvas, [{ label: "Single", value: .6 }]);
  assertStableCanvas(barCanvas, 320, 2, `scenario redraw ${repeat}`);
  draws += 1;
}
console.log(JSON.stringify({ source: sourcePath, browser_launched: false, draws, pixel_ratios: [1, 1.5, 2],
  replay_prediction_and_empty_states: true, pixel_ratio_changes: true, stable_canvas_height: true }));
