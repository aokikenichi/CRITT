(function runSixBallsGame() {
  "use strict";

  const cards = window.SixBallsCards;
  const model = window.SixBallsGameModel;

  if (!cards || !model) {
    throw new Error("Game data could not be loaded.");
  }

  const probabilityErrors = cards.validateProbabilityTable();
  if (probabilityErrors.length) {
    throw new Error(`Invalid card probabilities: ${probabilityErrors.join("; ")}`);
  }

  const elements = {
    titleScreen: document.querySelector("#titleScreen"),
    gameScreen: document.querySelector("#gameScreen"),
    startButton: document.querySelector("#startButton"),
    battingOrderInputs: document.querySelectorAll('input[name="battingOrder"]'),
    inningsLabel: document.querySelector("#inningsLabel"),
    matchHeading: document.querySelector("#matchHeading"),
    matchOrder: document.querySelector("#matchOrder"),
    targetBadge: document.querySelector("#targetBadge"),
    targetValue: document.querySelector("#targetValue"),
    playerScoreCard: document.querySelector("#playerScoreCard"),
    cpuScoreCard: document.querySelector("#cpuScoreCard"),
    playerRole: document.querySelector("#playerRole"),
    cpuRole: document.querySelector("#cpuRole"),
    playerScore: document.querySelector("#playerScore"),
    playerWickets: document.querySelector("#playerWickets"),
    cpuScore: document.querySelector("#cpuScore"),
    cpuWickets: document.querySelector("#cpuWickets"),
    choicePanel: document.querySelector("#choicePanel"),
    choiceHeading: document.querySelector("#choiceHeading"),
    choiceHint: document.querySelector("#choiceHint"),
    ballCount: document.querySelector("#ballCount"),
    cardGrid: document.querySelector("#cardGrid"),
    revealPanel: document.querySelector("#revealPanel"),
    playerCardArt: document.querySelector("#playerCardArt"),
    playerCardType: document.querySelector("#playerCardType"),
    playerCardName: document.querySelector("#playerCardName"),
    cpuCardArt: document.querySelector("#cpuCardArt"),
    cpuCardType: document.querySelector("#cpuCardType"),
    cpuCardName: document.querySelector("#cpuCardName"),
    deliveryResult: document.querySelector("#deliveryResult"),
    resultMark: document.querySelector("#resultMark"),
    resultText: document.querySelector("#resultText"),
    continueButton: document.querySelector("#continueButton"),
    playerHistory: document.querySelector("#playerHistory"),
    cpuHistory: document.querySelector("#cpuHistory"),
    inningsModal: document.querySelector("#inningsModal"),
    inningsLead: document.querySelector("#inningsLead"),
    inningsTargetLabel: document.querySelector("#inningsTargetLabel"),
    inningsTarget: document.querySelector("#inningsTarget"),
    inningsSummary: document.querySelector("#inningsSummary"),
    secondInningsButton: document.querySelector("#secondInningsButton"),
    resultModal: document.querySelector("#resultModal"),
    resultKicker: document.querySelector("#resultKicker"),
    resultTitle: document.querySelector("#resultTitle"),
    resultReason: document.querySelector("#resultReason"),
    finalPlayerScore: document.querySelector("#finalPlayerScore"),
    finalCpuScore: document.querySelector("#finalCpuScore"),
    replayButton: document.querySelector("#replayButton"),
    backToTitleButton: document.querySelector("#backToTitleButton"),
    liveRegion: document.querySelector("#liveRegion"),
  };

  const riskLabels = {
    LOW: "低リスク",
    MID: "中リスク",
    HIGH: "高リスク",
  };

  const resultCopy = {
    "0": "得点なし",
    "1": "1点！",
    "2": "2点！",
    "4": "4点！ バウンダリー",
    "6": "6点！ 最大得点",
    W: "ウィケット！ アウト",
  };

  let match = null;

  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function announce(message) {
    elements.liveRegion.textContent = "";
    window.requestAnimationFrame(() => {
      elements.liveRegion.textContent = message;
    });
  }

  function setModalOpen(modal, isOpen, focusTarget) {
    modal.hidden = !isOpen;
    document.body.classList.toggle("modal-open", isOpen);

    if (isOpen) {
      window.requestAnimationFrame(() => focusTarget.focus({ preventScroll: true }));
    }
  }

  function closeModal(modal) {
    modal.hidden = true;
    document.body.classList.remove("modal-open");
  }

  function startMatch() {
    const selectedOrder = Array.from(elements.battingOrderInputs).find((input) => input.checked)?.value || "random";
    const playerBatsFirst = selectedOrder === "first"
      || (selectedOrder === "random" && Math.random() < 0.5);

    match = model.createMatch(playerBatsFirst ? "player" : "cpu");
    closeModal(elements.inningsModal);
    closeModal(elements.resultModal);
    elements.titleScreen.hidden = true;
    elements.gameScreen.hidden = false;
    renderMatch();
    announce(`試合開始。あなたは${playerBatsFirst ? "先攻" : "後攻"}です。`);
    window.scrollTo({ top: 0, behavior: prefersReducedMotion() ? "auto" : "smooth" });
    window.requestAnimationFrame(() => {
      const firstCard = elements.cardGrid.querySelector("button");
      if (firstCard) firstCard.focus({ preventScroll: true });
    });
  }

  function backToTitle() {
    match = null;
    closeModal(elements.inningsModal);
    closeModal(elements.resultModal);
    elements.gameScreen.hidden = true;
    elements.titleScreen.hidden = false;
    window.scrollTo({ top: 0, behavior: prefersReducedMotion() ? "auto" : "smooth" });
    window.requestAnimationFrame(() => elements.startButton.focus({ preventScroll: true }));
  }

  function renderMatch() {
    renderScoreboard();
    renderHistory();
    renderChoice();
  }

  function renderScoreboard() {
    const playerInnings = model.teamInnings(match, "player");
    const cpuInnings = model.teamInnings(match, "cpu");
    const playerBatting = model.isPlayerBatting(match);

    elements.playerScore.textContent = String(playerInnings.score);
    elements.playerWickets.textContent = String(playerInnings.wickets);
    elements.cpuScore.textContent = String(cpuInnings.score);
    elements.cpuWickets.textContent = String(cpuInnings.wickets);

    elements.playerRole.textContent = playerBatting ? "攻撃" : "守備";
    elements.cpuRole.textContent = playerBatting ? "守備" : "攻撃";
    elements.playerScoreCard.classList.toggle("is-active", playerBatting);
    elements.cpuScoreCard.classList.toggle("is-active", !playerBatting);

    elements.inningsLabel.textContent = match.inningsIndex === 0 ? "1ST INNINGS" : "2ND INNINGS";
    elements.matchHeading.textContent = playerBatting ? "あなたの攻撃" : "CPUの攻撃";
    elements.matchOrder.textContent = match.innings[0].teamId === "player" ? "あなたは先攻" : "あなたは後攻";
    elements.targetBadge.hidden = match.inningsIndex === 0;

    if (match.inningsIndex === 1) {
      elements.targetValue.textContent = String(match.target);
    }
  }

  function createCardButton(card, type) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `game-card game-card--${type}`;
    button.dataset.cardId = card.id;
    button.setAttribute("aria-label", `${card.name}。${card.description}`);

    const topLine = document.createElement("span");
    topLine.className = "game-card__topline";

    const typeLabel = document.createElement("span");
    typeLabel.textContent = type === "batting" ? "BATTING" : "BOWLING";

    const risk = document.createElement("span");
    risk.textContent = riskLabels[card.risk];
    risk.className = `risk risk--${card.risk.toLowerCase()}`;

    const name = document.createElement("strong");
    name.className = "game-card__name";
    name.textContent = card.name;

    const art = document.createElement("img");
    art.className = "game-card__art";
    art.src = card.image;
    art.alt = "";
    art.width = 720;
    art.height = 720;
    art.loading = "lazy";
    art.decoding = "async";
    art.draggable = false;

    const shortDescription = document.createElement("span");
    shortDescription.className = "game-card__short";
    shortDescription.textContent = card.shortDescription;

    const description = document.createElement("span");
    description.className = "game-card__description";
    description.textContent = card.description;

    topLine.append(typeLabel, risk);
    button.append(topLine, art, name, shortDescription, description);
    return button;
  }

  function renderChoice() {
    if (match.stage !== "awaiting-card") return;

    const playerBatting = model.isPlayerBatting(match);
    const innings = model.currentInnings(match);
    const availableCards = model.cardsForPlayer(match);
    const cardType = playerBatting ? "batting" : "bowling";

    elements.choicePanel.hidden = false;
    elements.revealPanel.hidden = true;
    elements.choiceHeading.textContent = playerBatting
      ? "バッティングカードを選ぶ"
      : "ボウリングカードを選ぶ";
    elements.choiceHint.textContent = playerBatting
      ? "どう打つか、1枚選択"
      : "どの球を投げるか、1枚選択";
    elements.ballCount.textContent = `第${innings.balls.length + 1}球 / 6球`;

    elements.cardGrid.replaceChildren(
      ...availableCards.map((card) => createCardButton(card, cardType)),
    );
  }

  function renderHistoryList(list, innings, isCurrentInnings) {
    const items = [];

    for (let index = 0; index < model.MAX_BALLS; index += 1) {
      const item = document.createElement("li");
      const delivery = innings.balls[index];
      const ballNumber = document.createElement("span");
      const mark = document.createElement("strong");

      ballNumber.textContent = `${index + 1}`;
      mark.textContent = delivery ? delivery.result : "—";
      item.append(ballNumber, mark);

      if (delivery) {
        item.classList.add("is-played");
        if (delivery.result === "W") item.classList.add("is-wicket");
        if (delivery.result === "4" || delivery.result === "6") item.classList.add("is-boundary");
        item.setAttribute("aria-label", `第${index + 1}球、${resultCopy[delivery.result]}`);
      } else {
        item.setAttribute("aria-label", `第${index + 1}球、未投球`);
      }

      if (isCurrentInnings && match.stage === "awaiting-card" && index === innings.balls.length) {
        item.classList.add("is-next");
        item.setAttribute("aria-current", "step");
      }

      items.push(item);
    }

    list.replaceChildren(...items);
  }

  function renderHistory() {
    const playerInnings = model.teamInnings(match, "player");
    const cpuInnings = model.teamInnings(match, "cpu");
    renderHistoryList(elements.playerHistory, playerInnings, model.currentInnings(match).teamId === "player");
    renderHistoryList(elements.cpuHistory, cpuInnings, model.currentInnings(match).teamId === "cpu");
  }

  function deliveryAnnouncement(delivery) {
    const batter = delivery.playerBatting ? "あなた" : "CPU";
    if (delivery.result === "W") {
      return `${batter}はアウト。`;
    }
    if (delivery.result === "0") {
      return `${batter}は得点なし。`;
    }
    return `${batter}が${delivery.result}点を獲得。`;
  }

  function showReveal(delivery) {
    const playerCard = delivery.playerBatting
      ? cards.getBattingCard(delivery.playerCardId)
      : cards.getBowlingCard(delivery.playerCardId);
    const cpuCard = delivery.playerBatting
      ? cards.getBowlingCard(delivery.cpuCardId)
      : cards.getBattingCard(delivery.cpuCardId);

    elements.choicePanel.hidden = true;
    elements.revealPanel.hidden = false;
    elements.playerCardType.textContent = delivery.playerBatting ? "バッティング" : "ボウリング";
    elements.cpuCardType.textContent = delivery.playerBatting ? "ボウリング" : "バッティング";
    elements.playerCardArt.src = playerCard.image;
    elements.cpuCardArt.src = cpuCard.image;
    elements.playerCardName.textContent = playerCard.name;
    elements.cpuCardName.textContent = cpuCard.name;
    elements.resultMark.textContent = delivery.result;
    elements.resultText.textContent = resultCopy[delivery.result];

    elements.deliveryResult.classList.toggle("is-wicket", delivery.result === "W");
    elements.deliveryResult.classList.toggle(
      "is-boundary",
      delivery.result === "4" || delivery.result === "6",
    );

    if (match.afterReveal === "innings-break") {
      elements.continueButton.textContent = "攻守交代へ";
    } else if (match.afterReveal === "match-over") {
      elements.continueButton.textContent = "試合結果を見る";
    } else {
      elements.continueButton.textContent = "次の球へ";
    }

    renderScoreboard();
    renderHistory();
    announce(`${deliveryAnnouncement(delivery)} ${resultCopy[delivery.result]}`);
    elements.revealPanel.scrollIntoView({
      behavior: prefersReducedMotion() ? "auto" : "smooth",
      block: "start",
    });
    window.requestAnimationFrame(() => elements.continueButton.focus({ preventScroll: true }));
  }

  function showInningsBreak() {
    const playerChasing = match.innings[1].teamId === "player";
    const firstTeamName = match.innings[0].teamId === "player" ? "あなた" : "CPU";

    elements.inningsTarget.textContent = String(match.target);
    elements.inningsLead.textContent = `${firstTeamName}の攻撃が終了しました。`;
    elements.inningsTargetLabel.textContent = playerChasing ? "あなたの目標" : "CPUの目標";
    elements.inningsSummary.textContent = playerChasing
      ? `6球以内に${match.target}点へ到達すれば、あなたの勝利です。`
      : `CPUが${match.target}点に到達する前に、2アウトを取るか6球を投げ切りましょう。`;
    elements.secondInningsButton.textContent = playerChasing ? "後攻で打つ" : "後攻を迎える";
    setModalOpen(elements.inningsModal, true, elements.secondInningsButton);
    announce(`攻守交代。${playerChasing ? "あなた" : "CPU"}の目標は${match.target}点です。`);
  }

  function resultDetails() {
    const player = model.teamInnings(match, "player");
    const cpu = model.teamInnings(match, "cpu");
    const playerChased = match.innings[1].teamId === "player";

    if (match.outcome === "win") {
      const reason = playerChased
        ? `目標の${match.target}点に到達しました。`
        : cpu.wickets >= model.MAX_WICKETS
          ? "CPUを2アウトに抑え、目標点を守りました。"
          : "6球を投げ切り、目標点を守りました。";
      return { kicker: "YOU WIN", title: "勝利！", reason };
    }

    if (match.outcome === "lose") {
      const reason = playerChased
        ? player.wickets >= model.MAX_WICKETS
          ? "2アウトとなり、目標点に届きませんでした。"
          : "6球を終え、目標点に届きませんでした。"
        : `CPUが目標の${match.target}点に到達しました。`;
      return {
        kicker: "CPU WIN",
        title: "敗北",
        reason,
      };
    }

    return {
      kicker: "DRAW",
      title: "引き分け",
      reason: `両チーム${player.score}点。同点で試合終了です。`,
    };
  }

  function showResult() {
    const details = resultDetails();
    elements.resultModal.dataset.outcome = match.outcome;
    elements.resultKicker.textContent = details.kicker;
    elements.resultTitle.textContent = details.title;
    elements.resultReason.textContent = details.reason;
    const playerInnings = model.teamInnings(match, "player");
    const cpuInnings = model.teamInnings(match, "cpu");
    elements.finalPlayerScore.textContent = String(playerInnings.score);
    elements.finalCpuScore.textContent = String(cpuInnings.score);
    setModalOpen(elements.resultModal, true, elements.replayButton);
    announce(`${details.title}。最終得点、あなた${playerInnings.score}点、CPU${cpuInnings.score}点。`);
  }

  function handleCardSelection(event) {
    const button = event.target.closest("button[data-card-id]");
    if (!button || !elements.cardGrid.contains(button) || !match || match.stage !== "awaiting-card") {
      return;
    }

    elements.cardGrid.querySelectorAll("button").forEach((cardButton) => {
      cardButton.disabled = true;
    });

    const delivery = model.playDelivery(match, button.dataset.cardId);
    showReveal(delivery);
  }

  function handleContinue() {
    const nextStage = model.continueAfterReveal(match);

    if (nextStage === "awaiting-card") {
      renderScoreboard();
      renderHistory();
      renderChoice();
      elements.choicePanel.scrollIntoView({
        behavior: prefersReducedMotion() ? "auto" : "smooth",
        block: "start",
      });
      window.requestAnimationFrame(() => {
        const firstCard = elements.cardGrid.querySelector("button");
        if (firstCard) firstCard.focus({ preventScroll: true });
      });
      return;
    }

    if (nextStage === "innings-break") {
      showInningsBreak();
      return;
    }

    showResult();
  }

  function beginSecondInnings() {
    model.startSecondInnings(match);
    closeModal(elements.inningsModal);
    renderMatch();
    window.scrollTo({ top: 0, behavior: prefersReducedMotion() ? "auto" : "smooth" });
    window.requestAnimationFrame(() => {
      const firstCard = elements.cardGrid.querySelector("button");
      if (firstCard) firstCard.focus({ preventScroll: true });
    });
    announce(`後攻開始。あなたは${model.isPlayerBatting(match) ? "バッティング" : "ボウリング"}です。目標は${match.target}点です。`);
  }

  function trapModalFocus(event) {
    if (event.key !== "Tab") return;

    const openModal = !elements.inningsModal.hidden
      ? elements.inningsModal
      : !elements.resultModal.hidden
        ? elements.resultModal
        : null;

    if (!openModal) return;

    const focusable = Array.from(openModal.querySelectorAll("button:not([disabled])"));
    if (!focusable.length) return;

    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  elements.startButton.addEventListener("click", startMatch);
  elements.cardGrid.addEventListener("click", handleCardSelection);
  elements.continueButton.addEventListener("click", handleContinue);
  elements.secondInningsButton.addEventListener("click", beginSecondInnings);
  elements.replayButton.addEventListener("click", startMatch);
  elements.backToTitleButton.addEventListener("click", backToTitle);
  document.addEventListener("keydown", trapModalFocus);

  renderHistoryList(elements.playerHistory, { balls: [] }, false);
  renderHistoryList(elements.cpuHistory, { balls: [] }, false);
})();
