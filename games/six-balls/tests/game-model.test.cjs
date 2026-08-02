const test = require("node:test");
const assert = require("node:assert/strict");

const cards = require("../cards.js");
const model = require("../game-model.js");

function playFirstInningsBall(match, result) {
  model.playDelivery(match, "drive", { cpuCardId: "fast", result });
  return model.continueAfterReveal(match);
}

function playSecondInningsBall(match, result) {
  model.playDelivery(match, "fast", { cpuCardId: "drive", result });
  return model.continueAfterReveal(match);
}

test("all 25 card combinations have complete 100-point probability rows", () => {
  assert.deepEqual(cards.validateProbabilityTable(), []);

  for (const battingCard of cards.BATTING_CARDS) {
    for (const bowlingCard of cards.BOWLING_CARDS) {
      const row = cards.getProbabilities(battingCard.id, bowlingCard.id);
      assert.deepEqual(Object.keys(row), ["0", "1", "2", "4", "6", "W"]);
      assert.equal(Object.values(row).reduce((sum, weight) => sum + weight, 0), 100);
    }
  }
});

test("the prototype stays in the intended 7–8 run balance band", () => {
  let expectedRunsPerBall = 0;

  for (const battingCard of cards.BATTING_CARDS) {
    for (const bowlingCard of cards.BOWLING_CARDS) {
      const row = cards.getProbabilities(battingCard.id, bowlingCard.id);
      expectedRunsPerBall += (row["1"] + row["2"] * 2 + row["4"] * 4 + row["6"] * 6) / 100 / 25;
    }
  }

  assert.ok(expectedRunsPerBall >= 1.2 && expectedRunsPerBall <= 1.4);

  const defendWicketRate = cards.BOWLING_CARDS.reduce(
    (sum, bowlingCard) => sum + cards.getProbabilities("defend", bowlingCard.id).W / 5,
    0,
  );
  assert.ok(defendWicketRate <= 9);
});

test("the first innings ends after six balls and sets target to score plus one", () => {
  const match = model.createMatch();

  for (let ball = 0; ball < 5; ball += 1) {
    assert.equal(playFirstInningsBall(match, "1"), "awaiting-card");
  }

  assert.equal(playFirstInningsBall(match, "1"), "innings-break");
  assert.equal(match.innings[0].score, 6);
  assert.equal(match.innings[0].balls.length, 6);
  assert.equal(match.target, 7);
});

test("two wickets end an innings early", () => {
  const match = model.createMatch();

  assert.equal(playFirstInningsBall(match, "W"), "awaiting-card");
  assert.equal(playFirstInningsBall(match, "W"), "innings-break");
  assert.equal(match.innings[0].wickets, 2);
  assert.equal(match.innings[0].balls.length, 2);
  assert.equal(match.target, 1);
});

test("the player can bowl first and bat in the chase", () => {
  const match = model.createMatch("cpu");

  assert.equal(match.innings[0].teamId, "cpu");
  assert.equal(match.innings[1].teamId, "player");
  assert.equal(model.isPlayerBatting(match), false);
  assert.equal(model.cardsForPlayer(match), cards.BOWLING_CARDS);

  for (let ball = 0; ball < 6; ball += 1) {
    model.playDelivery(match, "fast", { cpuCardId: "drive", result: ball === 0 ? "1" : "0" });
    model.continueAfterReveal(match);
  }

  model.startSecondInnings(match);
  assert.equal(model.isPlayerBatting(match), true);
  assert.equal(model.cardsForPlayer(match), cards.BATTING_CARDS);

  model.playDelivery(match, "drive", { cpuCardId: "fast", result: "2" });
  assert.equal(model.continueAfterReveal(match), "match-over");
  assert.equal(match.outcome, "win");
});

test("the chase ends immediately when the CPU reaches the winning target", () => {
  const match = model.createMatch();

  playFirstInningsBall(match, "1");
  for (let ball = 1; ball < 6; ball += 1) {
    playFirstInningsBall(match, "0");
  }

  model.startSecondInnings(match);
  assert.equal(playSecondInningsBall(match, "2"), "match-over");
  assert.equal(match.innings[1].balls.length, 1);
  assert.equal(match.outcome, "lose");
});

test("equal scores after the second innings produce a draw", () => {
  const match = model.createMatch();

  playFirstInningsBall(match, "2");
  for (let ball = 1; ball < 6; ball += 1) {
    playFirstInningsBall(match, "0");
  }

  model.startSecondInnings(match);
  playSecondInningsBall(match, "2");
  for (let ball = 1; ball < 6; ball += 1) {
    playSecondInningsBall(match, "0");
  }

  assert.equal(match.innings[1].score, 2);
  assert.equal(match.outcome, "draw");
});
