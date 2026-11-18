"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from scipy.stats import bootstrap

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    buckets = {(POS, POS): "tp", ("PASS", POS): "fp",
               (POS, "PASS"): "fn", ("PASS", "PASS"): "tn"}
    counts = dict.fromkeys(buckets.values(), 0)
    for actual, predicted in zip(human, judge, strict=True):
        bucket = buckets.get((actual, predicted))
        if bucket is None:
            raise ValueError("judge calibration labels must be PASS or FAIL")
        counts[bucket] += 1
    return counts


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    cm = confusion(human, judge)
    tp = cm["tp"]
    predicted_fail = tp + cm["fp"]
    actual_fail = tp + cm["fn"]
    return (tp / predicted_fail if predicted_fail else 0.0,
            tp / actual_fail if actual_fail else 0.0)


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined."""
    cm = confusion(human, judge)
    tp, fp, fn, tn = (cm[key] for key in ("tp", "fp", "fn", "tn"))
    total = tp + fp + fn + tn
    # Express observed and chance agreement over the same denominator, total².
    observed = (tp + tn) * total
    chance = (tp + fn) * (tp + fp) + (tn + fp) * (tn + fn)
    if chance == total * total:
        raise ValueError("Cohen's kappa is undefined")
    return (observed - chance) / (total * total - chance)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    denominator = sensitivity + specificity - 1
    if denominator == 0:
        raise ValueError("Rogan-Gladen correction is undefined")
    corrected = (observed_rate + specificity - 1) / denominator
    return min(1.0, max(0.0, corrected))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    if len(a) and np.array_equal(a, b):
        return 0.0, 0.0, 0.0

    def mean_difference(x, y, axis=0):
        return np.mean(x, axis=axis) - np.mean(y, axis=axis)

    interval = bootstrap(
        (a, b), mean_difference, paired=True, method="percentile",
        n_resamples=n_resamples, confidence_level=confidence, rng=np.random.default_rng(rng),
    ).confidence_interval
    return float(mean_difference(a, b)), float(interval.low), float(interval.high)


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    # TODO M6
    raise NotImplementedError


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    # TODO M6
    raise NotImplementedError
