"""Grouped logistic regression with a match-clustered sandwich covariance."""

from collections import Counter
from math import exp, sqrt

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.sparse import csr_matrix
from scipy.special import expit

FIELDS = ("batting", "bowling", "phase", "wicketsLost", "era", "streak")
Z95 = 1.959963984540054


def era(year):
    if year < "2015":
        return "2005–2014"
    if year < "2020":
        return "2015–2019"
    if year < "2024":
        return "2020–2023"
    return "2024以降"


def fit_wicket_model(sequences):
    rows, totals, events, match_indexes = [], [], [], []
    for match_index, (year, deliveries) in enumerate(sequences):
        totals_by_context, wickets_by_context = Counter(), Counter()
        for (batting, bowling, phase, lost, streak, wicket), n in deliveries.items():
            key = (batting, bowling, phase, lost, era(year), streak)
            totals_by_context[key] += n
            wickets_by_context[key] += wicket * n
        for key, n in totals_by_context.items():
            rows.append(key)
            totals.append(n)
            events.append(wickets_by_context[key])
            match_indexes.append(match_index)

    levels = [set(values) for values in zip(*rows)]
    preferred_references = ("Australia", "Australia", "powerplay", 0, "2024以降", "0")
    references = [
        preferred if preferred in values else min(values)
        for preferred, values in zip(preferred_references, levels)
    ]
    columns = {
        (field, level): index
        for index, (field, level) in enumerate(
            ((field, level) for field, values, ref in zip(FIELDS, levels, references)
             for level in sorted(values - {ref})), start=1
        )
    }
    indices = []
    offsets = [0]
    for row in rows:
        indices.append(0)
        indices.extend(columns[(field, value)] for field, value, ref in zip(FIELDS, row, references) if value != ref)
        offsets.append(len(indices))
    x = csr_matrix((np.ones(len(indices)), indices, offsets), shape=(len(rows), 1 + len(columns)))
    n = np.array(totals)
    y = np.array(events)
    total = int(n.sum())
    matches = len(sequences)
    beta = np.zeros(x.shape[1])

    def loss(linear):
        return np.dot(n, np.logaddexp(0, linear)) - np.dot(y, linear)

    eta = x @ beta
    for iteration in range(100):
        probability = expit(eta)
        residual = y - n * probability
        score = x.T @ residual
        weighted = x.multiply((n * probability * (1 - probability))[:, None])
        factor = cho_factor((x.T @ weighted).toarray())
        if np.max(np.abs(score)) < 1e-6:
            break
        step = cho_solve(factor, score)
        delta = x @ step
        current_loss = loss(eta)
        while loss(eta + delta) > current_loss + 1e-9:
            step *= 0.5
            delta *= 0.5
        beta += step
        eta += delta
    else:
        raise RuntimeError("Logistic regression failed to converge")
    if np.max(np.abs(beta)) > 15:
        raise RuntimeError("Possible separation in logistic regression")

    # First sum score contributions within each match, then form the sandwich.
    by_match = csr_matrix((residual, (match_indexes, np.arange(len(rows)))), shape=(matches, len(rows)))
    scores = (by_match @ x).toarray()
    bread = cho_solve(factor, np.eye(len(beta)))
    correction = matches / (matches - 1) * (total - 1) / (total - len(beta))
    covariance = correction * bread @ (scores.T @ scores) @ bread

    estimates = {}
    for level in sorted(levels[-1]):
        column = columns.get(("streak", level))
        if column is None:
            estimates[level] = {"oddsRatio": 1.0, "ci": None}
        else:
            b = beta[column]
            span = Z95 * sqrt(covariance[column, column])
            estimates[level] = {"oddsRatio": round(exp(b), 5),
                                "ci": [round(exp(b - span), 5), round(exp(b + span), 5)]}
    return {
        "n": total, "events": int(y.sum()), "matches": matches,
        "method": "Grouped binomial logit; match-clustered sandwich (CR1); normal 95% CI",
        "references": dict(zip(FIELDS, references)),
        "levels": {field: len(values) for field, values in zip(FIELDS, levels)},
        "terms": len(beta), "iterations": iteration,
        "maxAbsScore": round(float(np.max(np.abs(score))), 9),
        "oddsRatios": estimates,
    }
