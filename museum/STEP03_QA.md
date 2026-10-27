# 工程③ QA記録

実施日：2026-10-28（Asia/Tokyo）。公開先ではなくローカルHTTPサーバーで確認。ファイルを直接開く `file://` テストではない。

## 実施済み：実ブラウザ（Codex内ブラウザ / IAB）

以下はCodex内ブラウザでUIを操作して確認した項目。専用CLIテストの成功結果と混同しない。

| 確認項目 | 結果 | 確認内容 |
|---|---|---|
| 入口・作品一覧 | PASS | 入口表示と一覧から009へ移動。`/CRITT/museum/`のサブパスを実ブラウザで検証 |
| 009の作品表示 | PASS | iframe内Canvas描画を目視確認 |
| 作品解説・Esc・フォーカス | PASS | 解説表示後Escで閉じ、起動ボタンへフォーカス復帰 |
| 作品間ナビゲーション | PASS | 009の「次の作品」から010へ移動、Canvas描画を目視確認 |
| 010のUI表示復帰 | PASS | 共通「UIを隠す」→Escで復帰、`#hide-ui`へフォーカス |
| 010のAuto/一時停止 | PASS | 共通Autoと作品内部AUTOが同期、共通一時停止で作品内部に「再開」表示、Canvasへフォーカス |
| 010の言葉入力画面 | PASS | 「言葉を残す」でinputへフォーカス、Shift+Tabで送信ボタンへ循環、Escで閉じ起動ボタンへ復帰 |
| 狭い表示幅 | PASS | 340×698の入口・009・010に加え、390×844で009・010を確認。両作品ともページ幅390px、viewport幅390px、作品iframe高さ658.3125px。横はみ出しなし。実機スマートフォンの検証ではない |
| デスクトップ表示 | PASS | 1440×1000で009・010を描画し、作品と共通UIを操作 |
| 009の場面切替 | PASS | 「宙吊り」「落ちない一球」「地面」の3場面へ順に切替 |
| 009の重力・軽量表示 | PASS | 0Gへ切替し無重力表示、「高密度」を軽量表示へ切替 |
| 009のManual移動 | PASS | Wキー約1.5秒でマップ位置が4.16667%から18.7007%へ移動 |
| 009のAuto・一時停止・次の場 | PASS | 共通Autoから一時停止で共通/作品双方に「再開」表示、「次の場へ」を操作 |
| 009の制作途中の参考画像 | PASS | 3点の自然寸法1440×810を確認。未承認素材と明記、Escで閉じる |
| 010の境界横断 | PASS | Wキー約2.8秒で「3 CROSSINGS」、入口リセット後0 |
| 010の言葉を残す | PASS | 「QA確認用の境界」を入力し、成功toastを確認。作品内だけの一時保持で外部送信なし |
| 010の内部UI切替 | PASS | Hキーで作品内部UIを隠し、「UI表示」ボタンで復帰 |
| 010のドラッグ操作 | PASS | PCの作品画面中央をドラッグし、光の輪・展示空間が横へ移る視点変化を目視確認 |
| 009の狭い幅での移動UI | 部分確認 | 390pxで画面下の矢印を確認し、前進ボタンを1秒押下。実機タッチによる移動量の測定は未実施 |
| 001〜008の詳細ページ | PASS | `/CRITT/museum/`配下で全8件を開き、原本未取得/未収録、鑑賞モードなしを確認 |
| 不正ID | PASS | `999`、空、`9`、`009&id=010`の重複、`<script>`で同じサブパスの一覧へ復帰 |
| 原画ゼロの本番作品 | PASS | 正式原画ゼロと無効ボタンを確認。009の候補画像を正式原画に登録していない |
| 原画ビューアfixtureの登録判定 | PASS | 390×844と1440×1000。候補のみは拒否、approved2点＋candidate1点で表示件数2点 |
| 原画ビューアfixtureの画像と倍率 | PASS | 自然寸法1600×900、100%で1600×900、拡大125%、フィット、縮小、0キーのフィットを確認。PCフィット時1125×633で読込成功 |
| 原画ビューアfixtureの切替 | PASS | 右キーで2/2の縦長画像へ、前へで1/2へ復帰 |
| 原画ビューアfixtureの終了 | PASS | Escで閉じて起動ボタンへフォーカス復帰、閉じるボタンも動作 |
| 原画ビューアfixtureの読込失敗 | PASS | 非画像txtに対して読込失敗を明示 |

不正IDの最初のsnapshotでは画面遷移待ちのタイミングが不安定だったため、一覧の見出しが表示されるまで待って999を再確認しPASS。表示タイミングの問題と実装の失敗を区別した。

確認画像：`qa-results/desktop-009.png`、`desktop-010.png`、`mobile-009.png`、`mobile-010.png`。原画ビューアのテスト専用画像は `mobile-viewer-fixture.png`、`desktop-viewer-fixture.png` であり、作品原画の収録証拠ではない。010ドラッグ操作後・009モバイル表示時に取得したブラウザerror/warnログは0件。全通信の網羅的な監査を実施したという意味ではない。

## 実施済み：静的・ソース確認

- `node --check museum/tests/browser-qa.cjs`：PASS。
- `node --check museum/js/museum-shell.js` / `original-viewer.js`：PASS。
- `python3 museum/tests/validate-assets.py`：PASS。同梱5資産のSHA-256／サイズ、009・010のバイト一致、10件の台帳・原画ゼロ・未収録8件を検査。詳細は `source-backups/PRESERVATION.json`。
- 共通HTML3ページのID重複なし、静的参照先の相対パスとファイル存在を検査：PASS。
- `git diff --cached --check -- museum ':!museum/source-backups'`：実装ファイルの空白検査。受領バックアップのCRLFとMarkdown改行用末尾スペースは原本保全のため変更せず、この検査から除外。
- 009/010には `#manual` / `#auto` / `#pause` が実装されており、共通シェルはこれらを同一オリジンDOMの`click()`で接続する。
- 009はJPEGをHTMLへ埋込み、010はCanvasで描画。両作品とも外部ライブラリ、外部画像URL、fetch/XHR、postMessage、storage利用はない。
- 本番 `artworks.json` の正式原画は全作品ゼロ。009の候補画像・010の表示プレビューを原画に登録していない。
- `prefers-reduced-motion`対応は両原本内にある。ただし009/010とも利用者が開始したAutoは移動する。010の静止モードはカメラ移動全体の停止ではない。

## テスト専用原画fixture

`tests/viewer-fixture.html` は機能確認専用。横1600×900、縦900×1600の単純SVG図形を使う。いずれも作品原画ではなく、正式台帳に登録されていない。fixture内だけでapproved2点とcandidate1点を渡し、表示件数2点となることを確認した。候補のみの拒否と非画像ファイルの読込失敗も確認した。正式採用原画による検証とは区別する。

## 実ブラウザ自動テストの実行制約

`tests/browser-qa.cjs` は再実行用のPlaywrightテスト。今回、CLIによる自動テスト本体は未実施。

1. 標準起動：bundled Playwrightが要求するChromium 1234がローカルに存在せず失敗。
2. キャッシュ済みChromium 1208を明示：sandbox内でSIGABRT/EPERMとなり起動失敗。
3. sandbox外起動の承認要求：中断され、起動成功は未確認。
4. 代替のCodex内ブラウザ（IAB）を使用し、上表のUI操作で確認した。

上記は自動テスト環境の制約であり、作品の動作成功や失敗を示す証拠ではない。自動テストがPASSしたとは報告しない。

再実行例（リポジトリルート、ローカルHTTP起動後）：

```sh
/Users/aoki/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node museum/tests/browser-qa.cjs
```

環境に合わせ `PLAYWRIGHT_MODULE`、`CHROMIUM_PATH`、`MUSEUM_QA_ORIGIN` を指定可能。実行すると `qa-results/browser-qa.json` とスクリーンショットを保存する。fixture原画はPlaywrightの応答差替え内だけで使用し、本番JSONを変更しない。

## 未実施・未検証

- 実機iOS Safari・Android Chrome、Firefox、Safari、スクリーンリーダー。
- 実機タッチ移動、coarse pointerの操作ボタン、原画ビューアの実機2本指ピンチ。
- `prefers-reduced-motion`の実ブラウザ設定による確認（ソース確認のみ実施）。
- 長時間・低性能端末・メモリ負荷。
- 009の旧v3.3、010の旧v3.4との比較（原本未取得）。
- 001〜008の描画・操作（原本未取得）。
- 正式採用原画による表示（正式原画ゼロ。機能テスト用図形と区別）。
- GitHub Pagesの公開URLでの確認（本番公開を行わない指示のため）。

## 公開・既存ページ

本工程でmainへのマージ、本番公開、既存トップの変更は行わない。ローカルサブパスの動作確認と、本番での動作確認は区別する。
