/* Pure match state for LAST OVER：SIX BALLS. */
(function exposeGameModel(scope) {
  "use strict";

  const rules = scope.SixBallsCards || (typeof require === "function" ? require("./cards.js") : null);

  if (!rules) {
    throw new Error("SixBallsCards must be loaded before game-model.js");
  }

  const MAX_BALLS = 6;
  const MAX_WICKETS = 2;

  function createInnings(teamId) {
    return {
      teamId,
      score: 0,
      wickets: 0,
      balls: [],
    };
  }

  function createMatch(firstBattingTeamId) {
    const firstTeamId = firstBattingTeamId || "player";

    if (firstTeamId !== "player" && firstTeamId !== "cpu") {
      throw new Error(`Invalid first batting team: ${firstTeamId}`);
    }

    const secondTeamId = firstTeamId === "player" ? "cpu" : "player";

    return {
      inningsIndex: 0,
      innings: [createInnings(firstTeamId), createInnings(secondTeamId)],
      target: null,
      stage: "awaiting-card",
      afterReveal: null,
      lastDelivery: null,
      outcome: null,
    };
  }

  function currentInnings(state) {
    return state.innings[state.inningsIndex];
  }

  function teamInnings(state, teamId) {
    return state.innings.find((innings) => innings.teamId === teamId) || null;
  }

  function isPlayerBatting(state) {
    return currentInnings(state).teamId === "player";
  }

  function cardsForPlayer(state) {
    return isPlayerBatting(state) ? rules.BATTING_CARDS : rules.BOWLING_CARDS;
  }

  function randomCard(cards, randomValue) {
    const rawRandom = randomValue === undefined ? Math.random() : Number(randomValue);
    const safeRandom = Number.isFinite(rawRandom) ? Math.min(Math.max(rawRandom, 0), 0.999999999) : 0;
    return cards[Math.floor(safeRandom * cards.length)];
  }

  function isInningsComplete(innings) {
    return innings.balls.length >= MAX_BALLS || innings.wickets >= MAX_WICKETS;
  }

  function playDelivery(state, playerCardId, options) {
    if (!state || state.stage !== "awaiting-card") {
      throw new Error("A delivery can only be played while awaiting a card.");
    }

    const config = options || {};
    const playerBatting = isPlayerBatting(state);
    const playerCards = cardsForPlayer(state);
    const playerCard = playerCards.find((card) => card.id === playerCardId);

    if (!playerCard) {
      throw new Error(`Invalid player card for this innings: ${playerCardId}`);
    }

    const cpuCards = playerBatting ? rules.BOWLING_CARDS : rules.BATTING_CARDS;
    const cpuCard = config.cpuCardId
      ? cpuCards.find((card) => card.id === config.cpuCardId)
      : randomCard(cpuCards, config.cpuRandom);

    if (!cpuCard) {
      throw new Error(`Invalid CPU card for this innings: ${config.cpuCardId}`);
    }

    const battingId = playerBatting ? playerCard.id : cpuCard.id;
    const bowlingId = playerBatting ? cpuCard.id : playerCard.id;
    const result = config.result || rules.drawResult(battingId, bowlingId, config.resultRandom);

    if (!rules.RESULTS.includes(String(result))) {
      throw new Error(`Invalid delivery result: ${result}`);
    }

    const innings = currentInnings(state);
    const delivery = {
      ball: innings.balls.length + 1,
      result: String(result),
      battingId,
      bowlingId,
      playerCardId: playerCard.id,
      cpuCardId: cpuCard.id,
      playerBatting,
    };

    innings.balls.push(delivery);

    if (delivery.result === "W") {
      innings.wickets += 1;
    } else {
      innings.score += Number(delivery.result);
    }

    let afterReveal = "awaiting-card";

    if (state.inningsIndex === 0 && isInningsComplete(innings)) {
      state.target = innings.score + 1;
      afterReveal = "innings-break";
    }

    if (state.inningsIndex === 1) {
      const targetReached = innings.score >= state.target;
      if (targetReached || isInningsComplete(innings)) {
        afterReveal = "match-over";
      }
    }

    state.lastDelivery = delivery;
    state.stage = "reveal";
    state.afterReveal = afterReveal;

    return delivery;
  }

  function determineOutcome(state) {
    const playerScore = teamInnings(state, "player").score;
    const cpuScore = teamInnings(state, "cpu").score;

    if (playerScore > cpuScore) {
      return "win";
    }

    if (playerScore < cpuScore) {
      return "lose";
    }

    return "draw";
  }

  function continueAfterReveal(state) {
    if (!state || state.stage !== "reveal") {
      throw new Error("There is no revealed delivery to continue from.");
    }

    state.stage = state.afterReveal;
    state.afterReveal = null;

    if (state.stage === "match-over") {
      state.outcome = determineOutcome(state);
    }

    return state.stage;
  }

  function startSecondInnings(state) {
    if (!state || state.stage !== "innings-break") {
      throw new Error("The second innings can only start after the innings break.");
    }

    state.inningsIndex = 1;
    state.stage = "awaiting-card";
    state.lastDelivery = null;
    return state;
  }

  const api = Object.freeze({
    MAX_BALLS,
    MAX_WICKETS,
    createMatch,
    currentInnings,
    teamInnings,
    isPlayerBatting,
    cardsForPlayer,
    isInningsComplete,
    playDelivery,
    continueAfterReveal,
    startSecondInnings,
    determineOutcome,
  });

  scope.SixBallsGameModel = api;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
