"""Write the human-readable result using saved audit/evaluation evidence."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent


def main():
    manifest = json.loads((ROOT / "artifacts/wasp/manifest.json").read_text())
    evaluation = json.loads((ROOT / "reports/wasp/evaluation.json").read_text())
    verification = json.loads((ROOT / "reports/wasp/verification.json").read_text())
    assert verification["status"] == "passed"
    matches = pd.read_parquet(ROOT / "data/processed/wasp/matches.parquet")
    first, chase = evaluation["first_innings"], evaluation["chase"]
    lines = ["# Japan Women T20 Predictor 実行結果", "",
             "女子データで監査・学習・候補比較・評価・全期間refit・単一HTML生成を完了。男子版は変更していません。", "",
             "## 成果物", "", "`japan-women-t20-predictor.html` は外部CSS/JS/API不要で、GitHub Pagesとfile://に対応します。",
             "日本女子45試合のReplayを内包し、通常モデル対象外3試合も実得点と除外理由を表示します。", "",
             "## データと分割", "", f"- Source SHA-256: `{manifest['source_sha256']}`。",
             f"- 全{len(matches):,}試合。{matches.match_date.min()}〜{matches.match_date.max()}。全件female/international/T20。",
             "- Trainは2022年末まで、rolling validationは2023・2024年、locked testは2025年以降。",
             "- 以下はscope別の適格試合数。モデル非適格でも女子source内のmain inningsは既存仕様でcontext更新に使います。", "",
             "| Scope | Train | Validation | Test | Total |", "|---|---:|---:|---:|---:|"]
    for title, field in [("First", "first_innings_eligible"), ("Chase full", "chase_eligible"), ("Chase reduced", "reduced_match_eligible")]:
        group = matches[matches[field]]
        lines.append(f"| {title} | " + " | ".join(str(int(group.split.eq(s).sum())) for s in ["train", "validation", "test"]) + f" | {len(group)} |")
    lines += ["", "## 選択とlocked test", "",
              f"女子validationからElo K={manifest['selected_models']['elo_k']}を選択しました。",
              f"先攻採用は `{first['selected']}`、追走採用は `{chase['selected']}`。採用後のproductionだけ全期間で再学習しています。", "",
              "| 指標 | Locked test |", "|---|---:|",
              f"| First match-macro MAE | {first['locked_test']['match_macro_mae']:.6f} runs |",
              f"| First match-macro RMSE | {first['locked_test']['match_macro_rmse']:.6f} runs |",
              f"| Chase match-macro Brier | {chase['locked_test']['match_macro_brier']:.6f} |",
              f"| Chase match-macro log-loss | {chase['locked_test']['match_macro_log_loss']:.6f} |",
              f"| Chase ECE | {chase['locked_test']['ece']:.6f} |", "",
              "Firstは開始・terminalを含み、chase主指標はnonterminal stateを使います。",
              "候補比較と区間校正にはvalidation OOFを用い、上記locked testはproduction refit前のモデルで評価しました。",
              "Replayはproductionの振り返りで、未学習試合の性能評価ではありません。", ""]
    for title, task, columns in [("First", first, ["match_macro_mae", "match_macro_rmse"]),
                                  ("Chase", chase, ["match_macro_brier", "match_macro_log_loss", "ece"])]:
        lines += [f"## {title} 候補比較 (validation)", ""]
        for scope in ["selection_model_0", "selection_model_1"]:
            selection = task[scope]
            label = "Model 0 (stateのみ)" if scope == "selection_model_0" else "Model 1 (女子context追加)"
            gate_note = "" if scope == "selection_model_0" else f" context gate={selection['model_1_gate_passed']}。"
            lines += [f"{label}: 候補内選択 `{selection['selected']}`。{gate_note}", "",
                      "| Candidate | " + " | ".join(columns) + " |", "|---|" + "---:|" * len(columns)]
            for candidate in selection["candidates"]:
                lines.append("| " + candidate["name"] + " | " + " | ".join(f"{candidate[c]:.6f}" for c in columns) + " |")
            lines.append("")
    lines += ["## Activation gates", "", "| Role | History matches | Enabled | Reason |", "|---|---:|---|---|"]
    for role, gate in manifest["japan_gates"].items():
        lines.append(f"| {role} | {gate['match_count']} | {gate['enabled']} | {gate['fallback_reason']} |")
    reduced = evaluation["reduced_match_gate"]
    lines += ["", f"Reduced gate: enabled={reduced['enabled']}, development matches={reduced['development_matches']}, reason={reduced['reason']}。",
              "既存の最小件数と性能条件をそのまま適用し、補正・短縮試合機能を強制有効化していません。", "",
              "## 検証", "", "`scripts/women_predictor/reports/wasp/verification.json`: passed。",
              "全locked-test stateをfrozenモデルで再推論し、保存済み予測と独立match-macro集計の一致を確認。",
              "女子context再計算、Python/JavaScript推論、45 Replayの実得点/state、男子ファイルSHAも検証しました。"]
    browser = ROOT / "reports/wasp/browser-validation.json"
    if browser.exists():
        data = json.loads(browser.read_text())
        lines += ["", f"初回HTMLのBrowser検証: offline={data['offline']}、Replay={data['female_replays']}、mobile={data['mobile_width']}px、page errors={len(data['page_errors'])}、external requests={len(data['external_requests'])}。"]
    alignment = ROOT / "reports/wasp/ui-alignment.json"
    if alignment.exists():
        lines += ["", "## 公開男子版とのUI統一", "",
                  "CRITT共通ナビ、Hero、使用データ説明・4件数カード、WASPとは？、使い方、フッターを公開男子版と同じ内容・順序・配置へ統一しました。",
                  "5画面のDOM構成とPC／モバイルCSSを照合し、JavaScriptの件数表示・Replay判定を実行検証しました。",
                  "埋め込みpayload、推論runtime、女子の学習・評価artifactは更新前とSHA-256が一致しています。",
                  "今回のUI更新後のブラウザ再描画は未検証です。アプリ内ブラウザはfile://の操作を拒否するため、表示中のタブの再読み込みはユーザー操作が必要です。",
                  "検証記録: `scripts/women_predictor/reports/wasp/ui-alignment.json`。"]
    gate_note = ROOT / "reports/wasp/ui-gate-note.json"
    if gate_note.exists():
        lines += ["", "## 追加の表示変更", "",
                  "ユーザーの指定により、女子版の概要『機能の有効状態』と評価画面の未適用一覧を削除しました。",
                  "概要の注記に、強い国・弱い国との対戦を考慮した追加補正には十分な日本女子代表戦データが必要で、現時点では適用していない旨を記載しました。",
                  "表示だけの変更で、補正判定・モデル・評価・Replayのデータは維持しています。男子版は変更していません。"]
    canvas_resize = ROOT / "reports/wasp/ui-canvas-resize.json"
    if canvas_resize.exists():
        lines += ["", "## Replayグラフの高さ修正", "",
                  "Canvasの表示高と画面倍率に合わせた内部ピクセル数を分離し、再描画で高さが増え続ける不具合を修正しました。Replayの表示高は330pxで固定しています。",
                  "画面倍率1・1.5・2での反復描画、試合切り替え、幅と倍率の変更をNodeのCanvasモックで検証しました。埋め込みモデルデータ・推論runtime・男子版は変更していません。",
                  "検証記録: `scripts/women_predictor/reports/wasp/ui-canvas-resize.json`。ブラウザの再描画確認は未実施です。"]
    lines += ["", "再実行手順とライブラリ固定値は `scripts/women_predictor/README.md` と `requirements.txt` を参照してください。", "",
              "HTMLはCRITTルートへ配置済みです。公開先は https://aokikenichi.github.io/CRITT/japan-women-t20-predictor.html です。", ""]
    destination = ROOT.parents[1] / "WOMEN_PREDICTOR_RESULTS.md"
    destination.write_text("\n".join(lines))
    print(json.dumps({"results": str(destination)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
