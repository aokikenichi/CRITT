# Standalone web export contract

`builder.render_standalone_html(payload, predictor_javascript)` replaces the
four source placeholders below and returns one UTF-8 HTML document. The result
has no HTTP, CDN, font, image, worker, iframe, or WebSocket dependency and is
intended to be opened through `file://`.

| Placeholder | Embedded value |
|---|---|
| `<!--__WASP_STYLE__-->` | `standalone.css` |
| `<!--__WASP_PAYLOAD__-->` | script-safe compact JSON |
| `<!--__WASP_PREDICTOR__-->` | supplied predictor runtime |
| `<!--__WASP_APP__-->` | `standalone.js` |

The builder rejects a closing `</script>` token in JavaScript assets and
serializes the JSON with `<`, `>`, and `&` escaped. NaN and Infinity are not
accepted in the payload.

## Predictor API

The injected JavaScript must define:

```js
globalThis.WASPStandalonePredictor = {
  predictFirst(input, fullPayload, optionalNamedContext) { /* result */ },
  predictChase(input, fullPayload, optionalNamedContext) { /* result */ },
  // Optional. A chase result may instead contain `scenarios` directly.
  predictNextBallScenarios(input, fullPayload, optionalNamedContext) { /* rows */ }
};
```

Functions may return either an object or a Promise. `fullPayload` is the exact
top-level export payload; the production runtime reads its `inference` member.
The third argument is respectively `payload.contexts.first_innings` and
`payload.contexts.chase` when supplied, and exists only for alternative runtime
implementations.

First-innings input:

```json
{
  "batting_team": "Japan",
  "bowling_team": "Indonesia",
  "runs": 62,
  "wickets": 3,
  "completed": {"overs": 10, "balls": 0},
  "quota": {"overs": 20, "balls": 0},
  "venue": null,
  "use_japan_correction": true
}
```

First-innings result uses the API response subset:

```json
{
  "comparison": {
    "global": 131.2,
    "team_adjusted": 136.4,
    "japan_adjusted": 136.4,
    "selected": 136.4
  },
  "intervals": {
    "p50": {"lower": 124.0, "upper": 149.0},
    "p80": {"lower": 110.0, "upper": 166.0}
  },
  "correction": {
    "requested": true,
    "applied": false,
    "fallback_reason": "activation_gate_failed",
    "match_count": 22
  },
  "warnings": []
}
```

Chase input:

`toss_winner` is the current chasing/defending team name, or `null` for unknown.
The form defaults to unknown and resolves its relative choice at submission.
Unknown toss uses the global model for the prediction and all next-ball
scenarios, with a warning; it must not enter the team model as a zero-valued
feature. Japan corrections fitted on team-model residuals are not applied to
this fallback. Stored replays retain their original prematch toss context.

```json
{
  "chasing_team": "Japan",
  "defending_team": "Indonesia",
  "toss_winner": "Japan",
  "target": 130,
  "current_score": 76,
  "wickets": 4,
  "balls_remaining": 48,
  "target_ball_limit": {"overs": 20, "balls": 0},
  "venue": null,
  "use_japan_correction": true
}
```

Chase result uses `comparison`, `correction`, and `warnings` as above, plus:

```json
{
  "comparison": {"global": 0.59, "team_adjusted": 0.80, "selected": 0.80},
  "terminal": {"is_terminal": false, "status": null},
  "scenarios": [
    {"label": "0 run", "runs": 0, "wicket": false, "win_probability": 0.74}
  ]
}
```

For a regulation tie, `terminal.status` is `tied_regulation` and the selected
probability is `null`. Terminal wins and losses use probabilities 1 and 0.

## Payload members

The UI accepts these top-level members. All except `inference` may be omitted;
the affected panel then shows a Japanese empty state.

```text
metadata          source hash, generation time, counts, period, limitations
known_teams       string[] used by datalists and cold-start notices
known_venues      string[] used by datalists and cold-start notices
japan_matches     compact match[] used by the offline replay browser
replays           object keyed by match_id
evaluation        locked-test summary, calibration, slices, candidates
japan_gates       object keyed by batting/bowling/chasing/defending
reduced_match_gate object, or reduced_match_enabled boolean
contexts          optional named contexts passed as the third predictor argument
models            selected model metadata for overview cards
inference         exported numeric runtime context used by the predictor
```

A compact `japan_matches` object supports:

```json
{
  "match_id": "1333932",
  "date": "2022-10-10",
  "teams": ["Japan", "Indonesia"],
  "venue": "Sano International Cricket Ground",
  "winner": "Japan",
  "result": "Japan won by ...",
  "is_japan": true
}
```

Each `replays[match_id]` supports either `first_innings` and `chase` arrays or a
single `points` array with `innings: 1|2`. Point objects use this subset:

```text
legal_balls_bowled
runs_so_far
predicted_final_score   (or selected for innings 1)
win_probability         (or selected for innings 2)
event                   "wicket" | "four" | "six" | another event
```

The reader also accepts `{data: ...}` and `{replay: ...}` wrappers to remain
compatible with saved API responses.
