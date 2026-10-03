# Japan Women T20 predictor pipeline

女子T20Iのみで男子と同じWASP-style分析手順を再実行する独立snapshotです。
男子のコード・学習済み値は実行時に参照しません。設計は
[`../../WOMEN_PREDICTOR_PLAN.md`](../../WOMEN_PREDICTOR_PLAN.md) を参照してください。

## 再実行

Python 3.12を推奨します。必要ライブラリは `requirements.txt` に固定しました。
CRITTルートから実行してください。

```sh
python scripts/build_japan_women_predictor.py --source /path/to/t20s_female_csv2.zip
```

このworkspaceの既存環境を利用する場合:

```sh
../cricket-japan-bi/.venv-wasp/bin/python scripts/build_japan_women_predictor.py --source /Users/aoki/Downloads/t20s_female_csv2.zip
```

ZIPはSHA-256固定、全試合のfemale/international/T20 metadataを事前検証します。
新しいCricsheet releaseを使う場合は、source監査・SHA・設計・期待cohortを更新してください。
`--from-stage train` などで完了済み工程を再利用できます。

## 出力

- `../../japan-women-t20-predictor.html`: 外部依存のない単一HTML。
- `data/processed/wasp/`: audit、Parquet、DuckDB、chronology、OOF/test予測。
- `artifacts/wasp/frozen_test/`: 2024年末まででfitした評価用bundle。
- `artifacts/wasp/`: 全期間でrefitしたproduction bundle。
- `reports/wasp/`: 候補比較、locked test指標、再計算verification。
- `provenance.json`: 原男子sourceのhash、参照元、変更していないことの検証用記録。

ZIP、Parquet、joblibはGit対象外です。公開には最終HTMLだけで足ります。
Replayは全期間productionモデルの振り返りです。評価画面はfrozenモデルのlocked testを示します。
日本補正と短縮試合は元のactivation gateを満たす場合だけ有効になります。

## 検証

```sh
cd scripts/women_predictor
PYTHONPATH=src python -m pytest tests
PYTHONPATH=src python verify_results.py --node /path/to/node
```

browser検証用 `tests/browser.cjs` はNodeとPlaywrightを使います。
`PLAYWRIGHT_MODULE` と `CHROMIUM_EXECUTABLE` で既存runtimeを指定できます。

`verify_results.py` の男子版保存チェックは、`provenance.json` に記録した元workspaceの
男子ファイルを参照します。別環境ではこの元ファイル一式も必要です。
女子の学習・HTML出力には男子ファイルを使わず、`--through-stage export` まで実行できます。

Canvasの高さの回帰テストはブラウザを使わず実行できます。

```sh
node tests/canvas-resize.cjs
node tests/canvas-resize.cjs ../../japan-women-t20-predictor.html
```

## ソースの差分方針

`src/cricket_japan_bi/wasp`、CSV2 parser、`scripts/` は添付男子パイプラインの独立コピー。
学習・モデル選択・評価・chronologyの数式と固定policyを維持し、dataのgender判定、
source cohort事前検証、女子UI/metadata/Replay表示を変更しています。
