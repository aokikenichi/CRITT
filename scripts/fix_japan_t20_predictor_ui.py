"""Apply the reviewed display fixes to an exported men's predictor HTML.

Preserves the embedded model payload and prediction runtime byte-for-byte.
Run again after exporting the men's page from its original model pipeline.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

NOTE = (
    "強い国・弱い国との対戦では、相手の実力差を考慮した追加補正が必要です。"
    "日本代表向けの追加補正は、過去試合のデータ量や検証での精度改善が十分でないため、"
    "現在は適用していません。"
)


def replace_once(text, old, new):
    if text.count(old) == 1:
        return text.replace(old, new, 1)
    if old not in text and new in text:
        return text
    raise ValueError(f"Unexpected exported UI structure: {old[:80]!r}")


def patch(text):
    scripts_before = re.findall(r"<script[^>]*>([\s\S]*?)</script>", text)
    if len(scripts_before) != 3:
        raise ValueError("Expected one payload and two inline JavaScript blocks")
    payload = json.loads(scripts_before[0])
    gender = payload.get("metadata", {}).get("gender")
    # Older men's exports omit gender metadata; their document header identifies the cohort.
    if gender not in (None, "male") or "日本男子代表" not in text.split("</head>", 1)[0]:
        raise ValueError("This patch is only for the men's predictor")

    text = replace_once(text, '''      <div class="two-column">
        <article class="panel">
          <div class="panel-heading"><p class="eyebrow">LOCKED TEST</p><h2>評価スナップショット</h2></div>
          <div id="overview-evaluation"></div>
        </article>
        <article class="panel">
          <div class="panel-heading"><p class="eyebrow">ACTIVATION GATES</p><h2>機能の有効状態</h2></div>
          <div id="overview-gates" class="gate-list"></div>
        </article>
      </div>''', '''      <article class="panel">
        <div class="panel-heading"><p class="eyebrow">LOCKED TEST</p><h2>評価スナップショット</h2></div>
        <div id="overview-evaluation"></div>
      </article>''')
    text = replace_once(text, '''      <div class="two-column">
        <article class="panel"><div class="panel-heading"><p class="eyebrow">SELECTION</p><h2>候補モデル</h2></div><div id="candidate-table" class="table-wrap"></div></article>
        <article class="panel"><div class="panel-heading"><p class="eyebrow">ACTIVATION GATES</p><h2>補正・短縮戦</h2></div><div id="evaluation-gates" class="gate-list"></div></article>
      </div>''', '''      <article class="panel"><div class="panel-heading"><p class="eyebrow">SELECTION</p><h2>候補モデル</h2></div><div id="candidate-table" class="table-wrap"></div></article>''')
    text = replace_once(text,
        '<aside class="notice-panel"><strong>読み方</strong><p>得点と確率は事実・公式値ではなく、収録試合に基づく推定です。日本補正は役割別gateを通過した場合だけ適用されます。</p></aside>',
        '<aside class="notice-panel"><strong>注記</strong><p>得点と確率は事実・公式値ではなく、収録試合に基づく推定です。<span id="correction-note">' + NOTE + '</span></p></aside>')
    text = replace_once(text, "指標・標本数・gate状態を表示します。", "指標と標本数を表示します。")
    text = replace_once(text,
        "世界の男子T20データで学習したモデルを日本代表戦にも適用し、日本向け補正は十分な検証結果が得られた役割についてのみ適用します。",
        "世界の男子T20データで学習したモデルを日本代表戦にも適用します。")
    for selector in ["overview-gates", "evaluation-gates"]:
        text = text.replace(f'    renderGates(q("#{selector}"), data.gates);\n', "")
    text = re.sub(r"\n  function renderGates\(target, gates\) \{[\s\S]*?(?=\n  function renderFirstHistory\()", "\n", text, count=1)
    text = replace_once(text,
        '    const limitations = data.metadata.limitations || data.evaluation.limitations || [',
        '    const limitations = (data.metadata.limitations || data.evaluation.limitations || [')
    text = text.replace('      "日本向け補正は役割別gateによりfallbackする場合があります。",\n', "")
    text = replace_once(text,
        '    ];\n    q("#model-limitations").innerHTML = limitations.map',
        '    ]).filter(function (item) { return !/^Japan correction\\b/i.test(String(item)); });\n    q("#model-limitations").innerHTML = limitations.map')
    text = replace_once(text,
        '  const ROUTES = new Set(["overview", "first", "chase", "replay", "evaluation"]);\n',
        '  const ROUTES = new Set(["overview", "first", "chase", "replay", "evaluation"]);\n  const canvasDisplayHeights = new WeakMap();\n') if "const canvasDisplayHeights" not in text else text
    text = replace_once(text,
        '    const height = Number(canvas.getAttribute("height")) || 320;',
        '    // Keep CSS height separate from the pixel buffer, whose height attribute changes on every draw.\n'
        '    if (!canvasDisplayHeights.has(canvas)) {\n'
        '      canvasDisplayHeights.set(canvas, Number(canvas.getAttribute("height")) || 320);\n'
        '    }\n'
        '    const height = canvasDisplayHeights.get(canvas);')
    scripts_after = re.findall(r"<script[^>]*>([\s\S]*?)</script>", text)
    if scripts_before[:2] != scripts_after[:2]:
        raise ValueError("Model payload or prediction runtime changed")
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", nargs="?", type=Path,
                        default=Path(__file__).resolve().parents[1] / "japan-t20-predictor.html")
    args = parser.parse_args()
    original = args.html.read_text()
    updated = patch(original)
    if updated != original:
        args.html.write_text(updated)
    print(json.dumps({"html": str(args.html), "changed": updated != original,
                      "model_payload_and_runtime_unchanged": True,
                      "sha256": hashlib.sha256(updated.encode()).hexdigest()}))


if __name__ == "__main__":
    main()
