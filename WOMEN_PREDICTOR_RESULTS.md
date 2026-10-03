# Japan Women T20 Predictor 実行結果

女子データで監査・学習・候補比較・評価・全期間refit・単一HTML生成を完了。男子版は変更していません。

## 成果物

`japan-women-t20-predictor.html` は外部CSS/JS/API不要で、GitHub Pagesとfile://に対応します。
日本女子45試合のReplayを内包し、通常モデル対象外3試合も実得点と除外理由を表示します。

## データと分割

- Source SHA-256: `acb457e9d1337907e901b4aa08a3a8a1962a7b98b216476ca3236d595bb0f4d9`。
- 全2,141試合。2009-06-18〜2026-09-01。全件female/international/T20。
- Trainは2022年末まで、rolling validationは2023・2024年、locked testは2025年以降。
- 以下はscope別の適格試合数。モデル非適格でも女子source内のmain inningsは既存仕様でcontext更新に使います。

| Scope | Train | Validation | Test | Total |
|---|---:|---:|---:|---:|
| First | 706 | 548 | 685 | 1939 |
| Chase full | 691 | 553 | 681 | 1925 |
| Chase reduced | 16 | 11 | 23 | 50 |

## 選択とlocked test

女子validationからElo K=32を選択しました。
先攻採用は `hgb`、追走採用は `logistic`。採用後のproductionだけ全期間で再学習しています。

| 指標 | Locked test |
|---|---:|
| First match-macro MAE | 16.276419 runs |
| First match-macro RMSE | 20.857602 runs |
| Chase match-macro Brier | 0.090858 |
| Chase match-macro log-loss | 0.283364 |
| Chase ECE | 0.026548 |

Firstは開始・terminalを含み、chase主指標はnonterminal stateを使います。
候補比較と区間校正にはvalidation OOFを用い、上記locked testはproduction refit前のモデルで評価しました。
Replayはproductionの振り返りで、未学習試合の性能評価ではありません。

## First 候補比較 (validation)

Model 0 (stateのみ): 候補内選択 `hgb`。

| Candidate | match_macro_mae | match_macro_rmse |
|---|---:|---:|
| current_run_rate | 20.381050 | 30.716456 |
| resource_12 | 19.981282 | 23.151231 |
| resource_24 | 21.398149 | 24.393456 |
| resource_48 | 23.295360 | 26.349533 |
| resource_96 | 25.430942 | 28.852231 |
| ridge | 17.063224 | 20.969697 |
| tweedie_1.1 | 18.450674 | 23.123171 |
| tweedie_1.5 | 18.715015 | 24.293077 |
| hgb | 15.732000 | 20.099638 |

Model 1 (女子context追加): 候補内選択 `ridge`。 context gate=False。

| Candidate | match_macro_mae | match_macro_rmse |
|---|---:|---:|
| current_run_rate | 20.381050 | 30.716456 |
| resource_12 | 19.981282 | 23.151231 |
| resource_24 | 21.398149 | 24.393456 |
| resource_48 | 23.295360 | 26.349533 |
| resource_96 | 25.430942 | 28.852231 |
| ridge | 16.797717 | 20.396693 |
| tweedie_1.1 | 17.890250 | 22.098080 |
| tweedie_1.5 | 18.095070 | 23.033603 |
| hgb | 18.185463 | 22.613492 |

## Chase 候補比較 (validation)

Model 0 (stateのみ): 候補内選択 `logistic`。

| Candidate | match_macro_brier | match_macro_log_loss | ece |
|---|---:|---:|---:|
| empirical_12 | 0.182932 | 0.547827 | 0.129605 |
| empirical_24 | 0.201401 | 0.590041 | 0.124416 |
| empirical_48 | 0.216338 | 0.623009 | 0.103064 |
| empirical_96 | 0.227295 | 0.646548 | 0.138403 |
| logistic | 0.087665 | 0.280733 | 0.025768 |
| hgb | 0.092009 | 0.281507 | 0.024631 |

Model 1 (女子context追加): 候補内選択 `logistic`。 context gate=True。

| Candidate | match_macro_brier | match_macro_log_loss | ece |
|---|---:|---:|---:|
| empirical_12 | 0.182932 | 0.547827 | 0.129605 |
| empirical_24 | 0.201401 | 0.590041 | 0.124416 |
| empirical_48 | 0.216338 | 0.623009 | 0.103064 |
| empirical_96 | 0.227295 | 0.646548 | 0.138403 |
| logistic | 0.085813 | 0.275723 | 0.012162 |
| hgb | 0.095614 | 0.300647 | 0.028133 |

## Activation gates

| Role | History matches | Enabled | Reason |
|---|---:|---|---|
| japan_batting | 10 | False | insufficient_history |
| japan_bowling | 9 | False | insufficient_history |
| japan_chasing | 9 | False | insufficient_history |
| japan_defending | 10 | False | insufficient_history |

Reduced gate: enabled=False, development matches=27, reason=insufficient_development_matches。
既存の最小件数と性能条件をそのまま適用し、補正・短縮試合機能を強制有効化していません。

## 検証

`scripts/women_predictor/reports/wasp/verification.json`: passed。
全locked-test stateをfrozenモデルで再推論し、保存済み予測と独立match-macro集計の一致を確認。
女子context再計算、Python/JavaScript推論、45 Replayの実得点/state、男子ファイルSHAも検証しました。

初回HTMLのBrowser検証: offline=True、Replay=45、mobile=390px、page errors=0、external requests=0。

## 公開男子版とのUI統一

CRITT共通ナビ、Hero、使用データ説明・4件数カード、WASPとは？、使い方、フッターを公開男子版と同じ内容・順序・配置へ統一しました。
5画面のDOM構成とPC／モバイルCSSを照合し、JavaScriptの件数表示・Replay判定を実行検証しました。
埋め込みpayload、推論runtime、女子の学習・評価artifactは更新前とSHA-256が一致しています。
今回のUI更新後のブラウザ再描画は未検証です。アプリ内ブラウザはfile://の操作を拒否するため、表示中のタブの再読み込みはユーザー操作が必要です。
検証記録: `scripts/women_predictor/reports/wasp/ui-alignment.json`。

## 追加の表示変更

ユーザーの指定により、女子版の概要『機能の有効状態』と評価画面の未適用一覧を削除しました。
概要の注記に、強い国・弱い国との対戦を考慮した追加補正には十分な日本女子代表戦データが必要で、現時点では適用していない旨を記載しました。
表示だけの変更で、補正判定・モデル・評価・Replayのデータは維持しています。男子版は変更していません。

## Replayグラフの高さ修正

Canvasの表示高と画面倍率に合わせた内部ピクセル数を分離し、再描画で高さが増え続ける不具合を修正しました。Replayの表示高は330pxで固定しています。
画面倍率1・1.5・2での反復描画、試合切り替え、幅と倍率の変更をNodeのCanvasモックで検証しました。埋め込みモデルデータ・推論runtime・男子版は変更していません。
検証記録: `scripts/women_predictor/reports/wasp/ui-canvas-resize.json`。ブラウザの再描画確認は未実施です。

再実行手順とライブラリ固定値は `scripts/women_predictor/README.md` と `requirements.txt` を参照してください。

HTMLはCRITTルートへ配置済みです。公開先は https://aokikenichi.github.io/CRITT/japan-women-t20-predictor.html です。
