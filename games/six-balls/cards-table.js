(function renderCardProbabilityTables() {
  "use strict";

  const cards = window.SixBallsCards;
  const summaryBody = document.querySelector("#battingSummaryBody");
  const matchupBody = document.querySelector("#matchupTableBody");

  if (!cards || !summaryBody || !matchupBody) {
    throw new Error("Card data or table containers could not be loaded.");
  }

  const validationErrors = cards.validateProbabilityTable();
  if (validationErrors.length) {
    throw new Error(`Invalid card probabilities: ${validationErrors.join("; ")}`);
  }

  const runResults = ["1", "2", "4", "6"];

  function expectedRuns(row) {
    return runResults.reduce((sum, result) => sum + Number(result) * row[result], 0) / 100;
  }

  function averageForBattingCard(battingCard) {
    return cards.BOWLING_CARDS.reduce(
      (sum, bowlingCard) => sum + expectedRuns(cards.getProbabilities(battingCard.id, bowlingCard.id)),
      0,
    ) / cards.BOWLING_CARDS.length;
  }

  function averagePercentageForBattingCard(battingCard, resultKeys) {
    return cards.BOWLING_CARDS.reduce((sum, bowlingCard) => {
      const row = cards.getProbabilities(battingCard.id, bowlingCard.id);
      return sum + resultKeys.reduce((rowSum, result) => rowSum + row[result], 0);
    }, 0) / cards.BOWLING_CARDS.length;
  }

  function makeCell(tagName, value, className) {
    const cell = document.createElement(tagName);
    cell.textContent = value;
    if (className) cell.className = className;
    return cell;
  }

  function renderSummary() {
    const rows = cards.BATTING_CARDS.map((battingCard) => {
      const row = document.createElement("tr");
      const heading = makeCell("th", battingCard.name, "summary-table__card");
      heading.scope = "row";

      row.append(
        heading,
        makeCell("td", battingCard.shortDescription),
        makeCell("td", `${averageForBattingCard(battingCard).toFixed(2)}点`, "number-cell"),
        makeCell("td", `${averagePercentageForBattingCard(battingCard, ["4", "6"]).toFixed(1)}%`, "number-cell is-boundary"),
        makeCell("td", `${averagePercentageForBattingCard(battingCard, ["W"]).toFixed(1)}%`, "number-cell is-wicket"),
      );
      return row;
    });

    summaryBody.replaceChildren(...rows);
  }

  function renderMatchupTable() {
    const rows = [];

    for (const battingCard of cards.BATTING_CARDS) {
      for (const bowlingCard of cards.BOWLING_CARDS) {
        const probabilities = cards.getProbabilities(battingCard.id, bowlingCard.id);
        const row = document.createElement("tr");
        row.classList.add("matchup-table__row");
        row.dataset.batting = battingCard.id;
        row.dataset.bowling = bowlingCard.id;

        if (bowlingCard.id === cards.BOWLING_CARDS[0].id) {
          row.classList.add("is-first-in-group");
        }

        const battingHeading = makeCell("th", battingCard.name, "matchup-table__batting");
        battingHeading.scope = "row";
        const bowlingCell = makeCell("td", bowlingCard.name, "matchup-table__bowling");

        row.append(battingHeading, bowlingCell);

        for (const result of cards.RESULTS) {
          const className = result === "W"
            ? "number-cell is-wicket"
            : result === "4" || result === "6"
              ? "number-cell is-boundary"
              : "number-cell";
          row.append(makeCell("td", `${probabilities[result]}%`, className));
        }

        row.append(makeCell("td", `${expectedRuns(probabilities).toFixed(2)}点`, "number-cell matchup-table__expected"));
        rows.push(row);
      }
    }

    matchupBody.replaceChildren(...rows);
  }

  renderSummary();
  renderMatchupTable();
})();
