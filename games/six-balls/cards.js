/*
 * LAST OVER：SIX BALLS - card data and result probabilities
 *
 * Tuning guide:
 * - PROBABILITY_TABLE contains every batting × bowling combination.
 * - Each row uses the result keys "0", "1", "2", "4", "6", and "W".
 * - The six values in each row must add up to 100.
 * - W means a wicket (out); the number keys mean runs (points).
 * - Current target: roughly 7–8 runs per innings when both sides choose at random.
 */
(function exposeCardRules(scope) {
  "use strict";

  const RESULTS = ["0", "1", "2", "4", "6", "W"];

  const BATTING_CARDS = [
    {
      id: "defend",
      name: "守る",
      image: "./assets/cards/batting-defend.jpg",
      shortDescription: "アウトを避ける",
      description: "得点は控えめ。ウィケットになりにくい安全な一手。",
      risk: "LOW",
    },
    {
      id: "drive",
      name: "ドライブ",
      image: "./assets/cards/batting-drive.jpg",
      shortDescription: "まっすぐ打つ",
      description: "得点と安全性のバランスがよい基本のショット。",
      risk: "MID",
    },
    {
      id: "pull",
      name: "プル",
      image: "./assets/cards/batting-pull.jpg",
      shortDescription: "横へ強く打つ",
      description: "バウンサーや遅い球から大きな得点を狙いやすい。",
      risk: "MID",
    },
    {
      id: "sweep",
      name: "スイープ",
      image: "./assets/cards/batting-sweep.jpg",
      shortDescription: "低く払い打つ",
      description: "スピンに強い。速い球にはタイミングを合わせにくい。",
      risk: "MID",
    },
    {
      id: "big-swing",
      name: "大振り",
      image: "./assets/cards/batting-big-swing.jpg",
      shortDescription: "一発を狙う",
      description: "4点・6点の好機が増える一方、アウトの危険も大きい。",
      risk: "HIGH",
    },
  ];

  const BOWLING_CARDS = [
    {
      id: "fast",
      name: "速球",
      image: "./assets/cards/bowling-fast.jpg",
      shortDescription: "速さで勝負",
      description: "力強い基本球。どの打ち方にも安定して対抗する。",
      risk: "MID",
    },
    {
      id: "yorker",
      name: "ヨーカー",
      image: "./assets/cards/bowling-yorker.jpg",
      shortDescription: "足元を狙う",
      description: "打者の足元へ投げる球。大振りや横のショットを崩しやすい。",
      risk: "LOW",
    },
    {
      id: "bouncer",
      name: "バウンサー",
      image: "./assets/cards/bowling-bouncer.jpg",
      shortDescription: "高く跳ねさせる",
      description: "高く弾む球。守りやスイープを抑えるが、プルには注意。",
      risk: "MID",
    },
    {
      id: "spin",
      name: "スピン",
      image: "./assets/cards/bowling-spin.jpg",
      shortDescription: "変化で惑わす",
      description: "曲がる球でタイミングを外す。スイープには読まれやすい。",
      risk: "MID",
    },
    {
      id: "slow",
      name: "スローボール",
      image: "./assets/cards/bowling-slow.jpg",
      shortDescription: "速度を落とす",
      description: "遅い球でタイミングを外す。見抜かれると長打になりやすい。",
      risk: "HIGH",
    },
  ];

  const PROBABILITY_TABLE = {
    defend: {
      fast: { "0": 44, "1": 26, "2": 16, "4": 5, "6": 1, W: 8 },
      yorker: { "0": 52, "1": 22, "2": 12, "4": 3, "6": 1, W: 10 },
      bouncer: { "0": 48, "1": 26, "2": 12, "4": 3, "6": 1, W: 10 },
      spin: { "0": 37, "1": 30, "2": 20, "4": 5, "6": 1, W: 7 },
      slow: { "0": 33, "1": 32, "2": 22, "4": 7, "6": 1, W: 5 },
    },
    drive: {
      fast: { "0": 28, "1": 21, "2": 18, "4": 16, "6": 3, W: 14 },
      yorker: { "0": 33, "1": 18, "2": 16, "4": 13, "6": 3, W: 17 },
      bouncer: { "0": 37, "1": 16, "2": 14, "4": 11, "6": 4, W: 18 },
      spin: { "0": 27, "1": 20, "2": 22, "4": 18, "6": 4, W: 9 },
      slow: { "0": 27, "1": 22, "2": 20, "4": 18, "6": 5, W: 8 },
    },
    pull: {
      fast: { "0": 33, "1": 18, "2": 12, "4": 18, "6": 5, W: 14 },
      yorker: { "0": 43, "1": 14, "2": 10, "4": 11, "6": 3, W: 19 },
      bouncer: { "0": 30, "1": 17, "2": 14, "4": 20, "6": 8, W: 11 },
      spin: { "0": 37, "1": 16, "2": 16, "4": 12, "6": 4, W: 15 },
      slow: { "0": 31, "1": 18, "2": 15, "4": 19, "6": 8, W: 9 },
    },
    sweep: {
      fast: { "0": 39, "1": 18, "2": 14, "4": 12, "6": 3, W: 14 },
      yorker: { "0": 43, "1": 17, "2": 12, "4": 10, "6": 2, W: 16 },
      bouncer: { "0": 43, "1": 16, "2": 12, "4": 10, "6": 3, W: 16 },
      spin: { "0": 27, "1": 19, "2": 22, "4": 19, "6": 5, W: 8 },
      slow: { "0": 31, "1": 20, "2": 21, "4": 16, "6": 4, W: 8 },
    },
    "big-swing": {
      fast: { "0": 33, "1": 13, "2": 8, "4": 16, "6": 11, W: 19 },
      yorker: { "0": 36, "1": 11, "2": 7, "4": 13, "6": 9, W: 24 },
      bouncer: { "0": 34, "1": 11, "2": 8, "4": 14, "6": 10, W: 23 },
      spin: { "0": 32, "1": 13, "2": 10, "4": 16, "6": 12, W: 17 },
      slow: { "0": 31, "1": 14, "2": 10, "4": 16, "6": 13, W: 16 },
    },
  };

  function getCard(cards, id) {
    return cards.find((card) => card.id === id) || null;
  }

  function getBattingCard(id) {
    return getCard(BATTING_CARDS, id);
  }

  function getBowlingCard(id) {
    return getCard(BOWLING_CARDS, id);
  }

  function getProbabilities(battingId, bowlingId) {
    const battingRow = PROBABILITY_TABLE[battingId];
    return battingRow ? battingRow[bowlingId] || null : null;
  }

  function drawResult(battingId, bowlingId, randomValue) {
    const probabilities = getProbabilities(battingId, bowlingId);

    if (!probabilities) {
      throw new Error(`Unknown card combination: ${battingId} × ${bowlingId}`);
    }

    const rawRandom = randomValue === undefined ? Math.random() : Number(randomValue);
    const safeRandom = Number.isFinite(rawRandom) ? Math.min(Math.max(rawRandom, 0), 0.999999999) : 0;
    const roll = safeRandom * 100;
    let boundary = 0;

    for (const result of RESULTS) {
      boundary += probabilities[result];
      if (roll < boundary) {
        return result;
      }
    }

    return RESULTS[RESULTS.length - 1];
  }

  function validateProbabilityTable() {
    const errors = [];

    for (const battingCard of BATTING_CARDS) {
      for (const bowlingCard of BOWLING_CARDS) {
        const probabilities = getProbabilities(battingCard.id, bowlingCard.id);

        if (!probabilities) {
          errors.push(`${battingCard.id} × ${bowlingCard.id}: missing row`);
          continue;
        }

        const resultKeys = Object.keys(probabilities);
        if (resultKeys.length !== RESULTS.length || RESULTS.some((result) => !resultKeys.includes(result))) {
          errors.push(`${battingCard.id} × ${bowlingCard.id}: invalid result keys`);
        }

        for (const result of RESULTS) {
          const weight = probabilities[result];
          if (!Number.isFinite(weight) || weight < 0) {
            errors.push(`${battingCard.id} × ${bowlingCard.id}: invalid ${result} weight`);
          }
        }

        const total = RESULTS.reduce((sum, result) => sum + (Number(probabilities[result]) || 0), 0);
        if (total !== 100) {
          errors.push(`${battingCard.id} × ${bowlingCard.id}: total is ${total}, expected 100`);
        }
      }
    }

    return errors;
  }

  const api = Object.freeze({
    RESULTS: Object.freeze([...RESULTS]),
    BATTING_CARDS: Object.freeze(BATTING_CARDS.map((card) => Object.freeze({ ...card }))),
    BOWLING_CARDS: Object.freeze(BOWLING_CARDS.map((card) => Object.freeze({ ...card }))),
    PROBABILITY_TABLE,
    getBattingCard,
    getBowlingCard,
    getProbabilities,
    drawResult,
    validateProbabilityTable,
  });

  scope.SixBallsCards = api;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
