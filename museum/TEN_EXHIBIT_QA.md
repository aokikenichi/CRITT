# 10作品連続回遊 α版 — QA記録

2026-11-01。原本基準 `40e96c2`。IABの実ブラウザでPC1440×900、モバイル390×844を検証。物理iOS／Androidではない。

## 結果

- 原本：**10/10 PASS**（hash・bytes一致）。抽出画像**88/88**が元HTML内の実バイトと一致。原本と旧入口13ファイルを基準コミットと照合して保全。
- **10作品 × 2画面サイズ × 3視点 = 60枚**の描画証跡。解説・資料ビューア20件を確認。
- PC・モバイル各々で、館内Autoの001→010・全30視点と出口に到達。ページ遷移・作品起動なし。
- PCで全10作品の作品Autoを再実行。キー入力でのAuto中断、横移動、前進、ドラッグを確認。
- 002は全記録でfigureMode A・5レイヤー。C/B人体メッシュは未使用。
- 解説／資料の間に移動キーを押してもカメラを維持。閉じると起点ボタンへフォーカス復帰。
- 画像の4倍拡大・全体表示・別画像選択を確認。010は画像未収録と原本の来歴を表示。
- 修正後の最終consoleはerror/warn **0件**。

## 作品別の証跡

各3視点は技法や主題に対応し、近接・側面・内外／背面を含む。実ブラウザの画面であり、展示素材に転用していない。fpsは停止点での短い計測値で、機材全般の性能保証ではない。

| ID | PC 3視点 | モバイル 3視点 | 共通UI | Manual横移動 | fps（PC / mobile） |
| --- | --- | --- | --- | --- | --- |
| 001 | [1](qa/ten-exhibits/pc-001-1.jpg) / [2](qa/ten-exhibits/pc-001-2.jpg) / [3](qa/ten-exhibits/pc-001-3.jpg) | [1](qa/ten-exhibits/mobile-001-1.jpg) / [2](qa/ten-exhibits/mobile-001-2.jpg) / [3](qa/ten-exhibits/mobile-001-3.jpg) | [PC](qa/ten-exhibits/pc-001-ui.json) / [mobile](qa/ten-exhibits/mobile-001-ui.json) | [1.26m](qa/ten-exhibits/pc-001-manual.json) | 60-60 / 60-60 |
| 002 | [1](qa/ten-exhibits/pc-002-1.jpg) / [2](qa/ten-exhibits/pc-002-2.jpg) / [3](qa/ten-exhibits/pc-002-3.jpg) | [1](qa/ten-exhibits/mobile-002-1.jpg) / [2](qa/ten-exhibits/mobile-002-2.jpg) / [3](qa/ten-exhibits/mobile-002-3.jpg) | [PC](qa/ten-exhibits/pc-002-ui.json) / [mobile](qa/ten-exhibits/mobile-002-ui.json) | [1.26m](qa/ten-exhibits/pc-002-manual.json) | 60-60 / 60-60 |
| 003 | [1](qa/ten-exhibits/pc-003-1.jpg) / [2](qa/ten-exhibits/pc-003-2.jpg) / [3](qa/ten-exhibits/pc-003-3.jpg) | [1](qa/ten-exhibits/mobile-003-1.jpg) / [2](qa/ten-exhibits/mobile-003-2.jpg) / [3](qa/ten-exhibits/mobile-003-3.jpg) | [PC](qa/ten-exhibits/pc-003-ui.json) / [mobile](qa/ten-exhibits/mobile-003-ui.json) | [1.261m](qa/ten-exhibits/pc-003-manual.json) | 60-60 / 60-60 |
| 004 | [1](qa/ten-exhibits/pc-004-1.jpg) / [2](qa/ten-exhibits/pc-004-2.jpg) / [3](qa/ten-exhibits/pc-004-3.jpg) | [1](qa/ten-exhibits/mobile-004-1.jpg) / [2](qa/ten-exhibits/mobile-004-2.jpg) / [3](qa/ten-exhibits/mobile-004-3.jpg) | [PC](qa/ten-exhibits/pc-004-ui.json) / [mobile](qa/ten-exhibits/mobile-004-ui.json) | [1.264m](qa/ten-exhibits/pc-004-manual.json) | 60-60 / 60-60 |
| 005 | [1](qa/ten-exhibits/pc-005-1.jpg) / [2](qa/ten-exhibits/pc-005-2.jpg) / [3](qa/ten-exhibits/pc-005-3.jpg) | [1](qa/ten-exhibits/mobile-005-1.jpg) / [2](qa/ten-exhibits/mobile-005-2.jpg) / [3](qa/ten-exhibits/mobile-005-3.jpg) | [PC](qa/ten-exhibits/pc-005-ui.json) / [mobile](qa/ten-exhibits/mobile-005-ui.json) | [1.324m](qa/ten-exhibits/pc-005-manual.json) | 60-60 / 60-60 |
| 006 | [1](qa/ten-exhibits/pc-006-1.jpg) / [2](qa/ten-exhibits/pc-006-2.jpg) / [3](qa/ten-exhibits/pc-006-3.jpg) | [1](qa/ten-exhibits/mobile-006-1.jpg) / [2](qa/ten-exhibits/mobile-006-2.jpg) / [3](qa/ten-exhibits/mobile-006-3.jpg) | [PC](qa/ten-exhibits/pc-006-ui.json) / [mobile](qa/ten-exhibits/mobile-006-ui.json) | [1.322m](qa/ten-exhibits/pc-006-manual.json) | 60-60 / 60-60 |
| 007 | [1](qa/ten-exhibits/pc-007-1.jpg) / [2](qa/ten-exhibits/pc-007-2.jpg) / [3](qa/ten-exhibits/pc-007-3.jpg) | [1](qa/ten-exhibits/mobile-007-1.jpg) / [2](qa/ten-exhibits/mobile-007-2.jpg) / [3](qa/ten-exhibits/mobile-007-3.jpg) | [PC](qa/ten-exhibits/pc-007-ui.json) / [mobile](qa/ten-exhibits/mobile-007-ui.json) | [1.26m](qa/ten-exhibits/pc-007-manual.json) | 60-60 / 60-60 |
| 008 | [1](qa/ten-exhibits/pc-008-1.jpg) / [2](qa/ten-exhibits/pc-008-2.jpg) / [3](qa/ten-exhibits/pc-008-3.jpg) | [1](qa/ten-exhibits/mobile-008-1.jpg) / [2](qa/ten-exhibits/mobile-008-2.jpg) / [3](qa/ten-exhibits/mobile-008-3.jpg) | [PC](qa/ten-exhibits/pc-008-ui.json) / [mobile](qa/ten-exhibits/mobile-008-ui.json) | [1.264m](qa/ten-exhibits/pc-008-manual.json) | 39-60 / 60-60 |
| 009 | [1](qa/ten-exhibits/pc-009-1.jpg) / [2](qa/ten-exhibits/pc-009-2.jpg) / [3](qa/ten-exhibits/pc-009-3.jpg) | [1](qa/ten-exhibits/mobile-009-1.jpg) / [2](qa/ten-exhibits/mobile-009-2.jpg) / [3](qa/ten-exhibits/mobile-009-3.jpg) | [PC](qa/ten-exhibits/pc-009-ui.json) / [mobile](qa/ten-exhibits/mobile-009-ui.json) | [1.263m](qa/ten-exhibits/pc-009-manual.json) | 60-60 / 60-60 |
| 010 | [1](qa/ten-exhibits/pc-010-1.jpg) / [2](qa/ten-exhibits/pc-010-2.jpg) / [3](qa/ten-exhibits/pc-010-3.jpg) | [1](qa/ten-exhibits/mobile-010-1.jpg) / [2](qa/ten-exhibits/mobile-010-2.jpg) / [3](qa/ten-exhibits/mobile-010-3.jpg) | [PC](qa/ten-exhibits/pc-010-ui.json) / [mobile](qa/ten-exhibits/mobile-010-ui.json) | [1.264m](qa/ten-exhibits/pc-010-manual.json) | 60-60 / 44-60 |

## 回遊・固有設定

- 館内Auto：[PCログ](qa/ten-exhibits/pc-full-tour.json)、[モバイルログ](qa/ten-exhibits/mobile-full-tour.json)。各視点でPauseして証跡を採取し、次の見どころで進行。通常時は6秒の鑑賞時間。
- PC全回遊の後に009の縮尺と010の発光を調整。最終PC版では各作品Auto全3視点とManualを再検証。モバイル全回遊は調整後。008の後続データUI修正は追加のモバイル検証で確認。
- 003：[4材質](qa/ten-exhibits/pc-003-settings.json)。三角形数44,370 / 97,614 / 88,740 / 559,062。初回の診断ラベルはD固定だったが、現行コードは選択材質も返す。
- 005：[関係の光ON](qa/ten-exhibits/pc-005-settings.json)。006：[位置反応OFF](qa/ten-exhibits/pc-006-settings.json)とONへの復帰。
- 008：[3表現・アウト抽出](qa/ten-exhibits/pc-008-settings.json)。初期は創作120球。JSON検査は検証専用の架空データを使い、[第1イニング2球→第2イニング1球](qa/ten-exhibits/mobile-008-inning-recheck.json)を確認。実試合の収録を意味しない。
- 008：[非該当ZIPの0/6表示](qa/ten-exhibits/mobile-008-zip.jpg)。一致試合が無い場合の選択欄は未確認／未収録として無効化。実試合の陽性照合・専用試合Autoの実データE2Eは未検証。
- 009：[1G・¼G・0G・−1G・位置依存](qa/ten-exhibits/pc-009-settings.json)。元の浮遊式と17島・12球・9バット・28岩を確認。
- 010：[横断2回・残像2本、静止・言葉1件、リセット](qa/ten-exhibits/mobile-010-settings.json)。
- [画像4倍拡大・別画像](qa/ten-exhibits/mobile-viewer.json)。

## 修正した問題

1. 先読みで009の補助関数 `clamp` が未分離のため停止。関数を分離し、4重力状態の検査を追加。修正後の回遊エラーなし。
2. 009の仮設置0.62倍では目線高に合わず、白球が島に隠れやすかった。0.41倍にして元の床と目線の関係を維持。最終画面で白球を確認。
3. 010の輪を細いWebGL線だけで表示していたため、元の発光の幅が不足。元の曲線を3層の発光形状に変更。
4. 第2イニング切替直後に200ms周期の診断が旧状態を返した。状態を待って再採取し、inning=1・1球を確認。

## 再現チェック

リポジトリルートで実行する。

```sh
python3 museum/tests/verify-ten-exhibit-sources.py
python3 museum/tests/verify-ten-exhibit-derived.py
node --test museum/tests/ten-exhibit-model.test.mjs
python3 museum/tests/summarize-ten-exhibit-qa.py
```

Node v24.22.1（この環境ではCodex同梱ランタイム）を使用。モデル検査6件PASS：30視点の連続経路、衝突、009重力、010境界、008創作120球とJSON第2イニングなど。抽出スクリプトは原本HTMLを書き換えない。

[未達・制約](TEN_EXHIBIT_UNRESOLVED.md)のとおり、実データZIPと実機端末は未確認。main・既存PR・原本HTMLは変更せず、本番公開もしない。
