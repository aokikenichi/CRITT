# Japan Women T20 Predictor 差分設計

作成日: 2026-10-03 (Asia/Tokyo)。実装・学習前の設計。

## 1. 男子版の解析と変更範囲

現行公開 `japan-t20-predictor.html` を取得し、添付スクリプトの実体である
`cricket-japan-bi/src/cricket_japan_bi/wasp` とローカル男子HTMLを照合した。
公開版とローカル版の inference / evaluation / japan_gates / replays は一致する。
男子の採用モデルは first=HGB、chase=context logistic、Elo K=32。
これらの採用結果・パラメータ・評価値は女子へ転用しない。

男子のソース、設定、processed、artifacts、reports、HTMLは変更しない。
CRITT の `scripts/women_predictor/` にパイプラインを独立して保存する。
依存する CSV2 parser と WASP 実装、5本のCLIを同梱し、入力からHTMLまで再実行可能にする。
既存 CRITT の未コミット変更にも触れない。

## 2. 入力と女性コホートの保証

- 入力: `/Users/aoki/Downloads/t20s_female_csv2.zip`。
- SHA-256: `acb457e9d1337907e901b4aa08a3a8a1962a7b98b216476ca3236d595bb0f4d9`。
- 全2,141試合。2009-06-18〜2026-09-01。日本女子45試合。
- `gender=female`, `team_type=international`, `match_type=T20` を取込前に検証し、
  異なるメタデータの混入は停止させる。モデル対象外にするだけでは、
  chronology・選択肢・Replayへの混入を防げないためである。
- `build_t20_women.py` の CSV2 metadata の扱いを参照する。ただし同ファイルの
  `START=2022-10-10`、選手分析、比較率の計算は今回の学習に使用しない。
  男子WASPの既存CSV2 parserを使って全期間を読み込む。
- 同梱実装の2か所の `male` eligibility 判定を `female` に変更する。
  固定SHAとcohort検証を両方実施し、男子データを一切読み込まない。

## 3. 除外条件・state・時系列

男子の実際のscope別条件を維持する。firstはDLS、awarded、no result、super over、
非標準20x6 quota、unknown dismissal/end、120球超過などを除外する。
chaseは加えてregulation tie/bowl-out、非確定target、改定target疑いなどを除外する。
firstに通常tie/bowl-outの明示除外がない既存仕様も維持する。
通常targetの安全な再構築(first score+1/120球)も同じ条件でのみ許可する。

stateはinnings開始と各physical delivery後を作る。wide/no-ballは合法球に数えず、
retired hurt等はteam wicketに数えない。firstはterminalを含み、chaseの主評価はterminalを除く。
各matchで含まれるstate数に応じた `1/N` sample weight を再計算する。

分割は固定: train=2022-12-31以前、rolling validation=2023年・2024年、locked test=2025年以降。
2023foldは2022年以前、2024foldは2023年以前で学習し、候補モデルは2024年末まででrefitする。
選択・frozen test評価を完了後、productionモデルだけ全期間で再学習する。
全期間学習と未学習testによる評価は別artifactとして保存する。

## 4. 女子だけでのcontext再計算

Elo初期1500、K候補16/24/32を女子validationのprematch Brierで再選択する。
batting form / bowling suppression は365日半減期、8innings prior、venueは20innings prior。
global score初期150は既存の固定policy定数で、男子観測データではない。
前日までの情報だけでsnapshotを作り、同日試合はまとめて更新する。
chronology更新はモデル適格性と別で、女子sourceのmain inningsを男子と同じ方法で利用する。

## 5. 候補モデルと採用規則

state-only(Model 0)とcontext追加(Model 1)の両方を女子で比較する。

First: CRR、resource tables(pseudo count=12/24/48/96)、Ridge(alpha=10)、
Tweedie(power=1.1/1.5, alpha=1)、Poisson HGB(lr=.06, iterations=250, L2=2)。
主指標はmatch-macro MAE。最良の1%以内ならresource→ridge→tweedie→HGB→CRRの
簡潔性順。context採用はmacro MAEの厳密改善と各phaseの悪化5%以内が必要。

Chase: empirical tables(12/24/48/96)、logistic(C=.2)、log-loss HGB＋OOF Platt校正。
主指標はmatch-macro Brier。log-loss/ECE guardとBrier差.002以内の簡潔性規則を維持する。
contextはmacro Brier改善、log-loss悪化1%以内、ECE悪化.02以内で採用する。

50/80%区間は女子のrolling quantile models＋validation校正で再学習する。
validation校正に使ったOOF上の結果と、未使用locked testの結果を区別して報告する。

## 6. Japan-specific correction / reduced gate

日本女子のみ、batting/bowling/chasing/defendingの4roleを再評価する。
historyは2023–24 OOFのみ。最低12history matches、2025年gate最低8matches、
500回match bootstrap、80/95%CI、MAE/RMSEまたはBrier/log-loss/ECEとcoverage guardを維持する。
chaseはhistory/gateとも3勝3敗以上が必要。2026年はauditのみ。
女子のhistoryはrole別10/9/9/10試合なので、全4roleは既存基準で無効になる見込み。
gateを緩めたり、有効化を強制したりしない。

reducedもdevelopment最低50matches、full悪化1%以内、reduced validation改善の既存gateを維持。
女子reduced developmentは27試合の見込みで無効。該当Replayは実際のscoreを表示し、
通常モデル予測不能の理由を示す。

## 7. HTML / Replay / 評価表示

最終成果物: CRITTルートの `japan-women-t20-predictor.html`。
既存UIと推論runtimeを再利用し、女子で学習したモデル・特徴量・評価・日本女子45試合を埋め込む。
CSS/JS/model/replayはすべて内包し、GitHub Pagesでもfile://でも外部通信なしで動作する。
性別・期間・SHA・candidate比較・match-macro評価・無効gate理由を表示する。
Replayは全期間production refitの振り返りであり、未学習test性能の証拠として扱わない。
通常対象外の日本3試合もscore Replayを保存し、適格性/予測不能理由を注記する。

## 8. 実行・検証・納品

1. この設計を保存してから独立パイプラインと女性configを作成する。
2. SHA/cohort監査→prepare→train→frozen評価再計算→standalone exportを実行する。
3. 女子cohort、分割、state/target、女性context、gate、Python/JS推論の一致を検証する。
4. オフラインbrowserでfirst/chase/Replay/evaluation、端末state、未知toss、モバイルを確認する。
5. 男子ソース・成果物のSHAが開始時と同じことを確認する。
6. 実測結果を `WOMEN_PREDICTOR_RESULTS.md` と機械可読reportに保存する。
   入力ZIP・Parquet・joblibはローカル再現用とし、公開HTMLには含めない。

GitHubへpushする指示は今回含まれていないため、配置可能なHTMLと再現手順をローカルで完成する。

実行完了: [WOMEN_PREDICTOR_RESULTS.md](WOMEN_PREDICTOR_RESULTS.md) に女子の実測結果と検証記録を保存した。

UI追加対応 (2026-10-03): ユーザーの指定に従い、公開男子版のCRITT共通ナビ・Top内容・配置・全5画面のCSSへ統一した。
女子payloadと学習・評価結果は変更せず、女子固有の詳細説明は評価画面、対象外のReplay注意は該当試合のみで表示する。
