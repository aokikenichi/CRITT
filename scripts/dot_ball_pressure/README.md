# ドットボールの連鎖を再集計する

ディレクトリはリポジトリのルートから指定する。Python 3.9以降で実行できる。信頼区間付きの記述集計は標準ライブラリで動作する。調整ロジスティック回帰には NumPy と SciPy が必要（初回集計は NumPy 1.26.4、SciPy 1.11.4）。

```bash
python3 -m pip install -r scripts/dot_ball_pressure/requirements.txt
python3 scripts/dot_ball_pressure/build.py --download --archive /tmp/critt-t20s_male_json.zip
python3 -m unittest discover -s scripts/dot_ball_pressure -v
```

`--download` は公式の男子T20I ZIPを指定パスに保存し、日本時間の当日を取得日として記録する。保存したZIPで再生成するときは実際の取得日を指定する。

```bash
python3 scripts/dot_ball_pressure/build.py \
  --archive /tmp/critt-t20s_male_json.zip --retrieved 2026-11-23
```

今回のZIPのSHA-256は `102586ea122793aafc645e05d6a598b9fff0746935e39b77f2d6f153bc385086`。取得日とハッシュは出力にも記録する。公開ZIPは更新されるため、同一結果の再現には取得済みの同一ZIPを使う。回帰を省く確認用の実行では `--descriptive-only --output /tmp/critt-dot-ball-descriptive.json` を追加する。既定の出力先では `data/dot-ball-pressure.json` と、同じ集計を含むローカル閲覧用の `data/dot-ball-pressure-local.js` を生成する。

## 集計と確認

1. 同一イニングの記録順で投球を読み、投球直前の連鎖数と失ウィケット数を求める。合法のチーム0点球をドットとし、ワイド・ノーボールやアウト・退場で連鎖をリセットする。
2. 世界、打撃側の国、日本の打撃を除く世界について、局面別の記述集計と試合単位の信頼区間を生成する。回帰の調整項、脱出の定義、収録上の例外は [RESULTS.md](RESULTS.md) に記載。
3. 自動テストは小さなZIPでの手計算照合、境界条件、回帰とクラスタ区間の照合、公開用JSONの不変条件とローカル閲覧用データとの一致を検証する。
4. `dot-ball-pressure.html` をブラウザーで直接開く。ローカル閲覧には、HTMLと同じ階層にリポジトリの `assets` と `data` が必要。0球〜5球以上、各局面、2ヵ国、日本を除く世界、スマートフォン幅での表示を確認する。

GitHub Pagesと同じHTTP経由の読み込みは、静的サーバーで確認できる。

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

ブラウザーで `http://127.0.0.1:8000/dot-ball-pressure.html` を開く。集計JSONは同じオリジンから取得する。GitHub Pagesでもリポジトリ内の相対パスで動作する。

### JSONの読み方

- `metadata` に分析範囲、試合・投球数、各国の収録試合数、取得日とSHA-256が入る。
- `groups` は世界・日本の打撃を除く世界・国別、続いて投球の局面、直前の連鎖数で参照する。`any` は1球以上、`all` は全条件。
- 各セルの `n` と `matches` は投球・試合数。割合を表す配列は `[分子, 95%区間の下限, 95%区間の上限]`。区間は 0〜1、算出不能は `null`。発生頻度の分母は同じ集計対象・局面の `all.n`、脱出率は `escapeN`、他の結果はセルの `n`。
- `contrasts` は指定した条件の割合の差と試合単位の区間。`adjustedWicket` は調整後のオッズ比、モデルの分析対象と診断情報。

## 更新とサイトへの反映

新しいZIPで再生成したら試合期間と試合数、国名、対象外投球、主要指標・区間の変化を確認する。本文・表の数値は分析レポートも更新し、テストとブラウザー確認を通す。元ZIPは配布元から取得し、PRには集計済みJSON、ローカル閲覧用データと変更したコード・文書を含める。

実験室の `data-analytics.html#lab` に新規ページへのカードを追加するPRでレビューする。マージ後、GitHub Pages上の新規ページ・JSONと実験室からのリンクを確認する。トップページのWhat's Newと `history.html` への掲載は公開確認後の別変更とする。

集計JSONには ODC Attribution License 1.0 を適用する。配布元のZIPには元データのライセンス全文が同梱されている。

Contains information from [Cricsheet](https://cricsheet.org/downloads/), which is made available under the [ODC Attribution License](https://opendatacommons.org/licenses/by/1-0/). CRITTで集計・可視化。
