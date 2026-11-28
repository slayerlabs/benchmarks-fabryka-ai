"""Per-question scores, uncertainty, baselines, and the comparison with the baseline b.

Ported from research/common/metryki.py and research/tools/statystyka.py with the same arithmetic, seeds, and
thresholds, so the same per-question results give the same numbers. Verdicts use English names for the research
pipeline's terms: `strong` (pewne, |z| >= 3), `probable` (prawdopodobne, 2 <= |z| < 3), `noise` (szum), and
`inconclusive` (nierozstrzygalne). `tests/test_runner.py` compares every function with the research code.
"""

import math
from collections import Counter
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np

SEED = 20261028
REPLICATES = 10000
LN2 = math.log(2)
STRONG, PROBABLE = 3.0, 2.0
P_STRONG = math.erfc(STRONG / math.sqrt(2))
P_PROBABLE = math.erfc(PROBABLE / math.sqrt(2))
INCONCLUSIVE = "inconclusive"
MIN_CLUSTERS = 3

Summary = dict[str, Any]


# --- one question ---


def gold_index(target: Any, continuations: Sequence[str]) -> int:
    """lm-eval records the target as an index or as the text of an option (PubMedQA: "yes"/"no"/"maybe")."""
    try:
        return int(target)
    except (TypeError, ValueError):
        options = [c.strip() for c in continuations]
        if len(options) > 1 and len(set(options)) == 1:
            raise ValueError("multi-context task: the target is the shared continuation; pass the gold index") from None
        return options.index(str(target).strip())


def argmax(values: Sequence[float]) -> int:
    return max(range(len(values)), key=lambda i: values[i])


def multiple_choice_outcome(sample: dict[str, Any], gold: int | None = None) -> dict[str, Any]:
    """acc, acc_norm, and the bits per byte of the correct option for one lm-eval multiple-choice sample.

    acc_norm as in lm-eval: the log-likelihood divided by the option's length in characters (without the delimiter).
    Bits per byte of the correct option: -loglik / (ln 2 * bytes of the continuation with its delimiter).
    """
    lls = [float(r[0]) for r in sample["filtered_resps"]]
    continuations = [a[1] for a in sample["arguments"][: len(lls)]]
    if gold is None:
        gold = gold_index(sample["target"], continuations)
    lengths = [max(len(c.lstrip(" ")), 1) for c in continuations]
    pred = argmax(lls)
    pred_norm = argmax([ll / n for ll, n in zip(lls, lengths, strict=True)])
    return {
        "k": len(lls),
        "gold": gold,
        "pred_acc": pred,
        "pred_acc_norm": pred_norm,
        "acc": float(pred == gold),
        "acc_norm": float(pred_norm == gold),
        "bpb_correct": -lls[gold] / (LN2 * max(len(continuations[gold].encode("utf-8")), 1)),
        "loglikelihoods": lls,
    }


# --- uncertainty ---


def mean_with_uncertainty(values: Sequence[float], seed: int = SEED, replicates: int = REPLICATES) -> Summary:
    """Mean, n, SE (sample standard deviation / sqrt(n)), and a 95% percentile-bootstrap interval."""
    x = np.asarray(values, dtype=float)
    n = len(x)
    if n == 0:
        return {"value": None, "n": 0, "se": None, "ci95": None}
    se = float(x.std(ddof=1) / math.sqrt(n)) if n > 1 else None
    idx = np.random.default_rng(seed).integers(0, n, size=(replicates, n))
    lo, hi = np.percentile(x[idx].mean(axis=1), [2.5, 97.5])
    return {"value": float(x.mean()), "n": n, "se": se, "ci95": [float(lo), float(hi)], "se_method": "per question"}


def clustered_mean(
    values: Sequence[float], clusters: Sequence[Any], seed: int = SEED, replicates: int = REPLICATES
) -> Summary:
    """Mean over questions that come in clusters: SE over clusters (with t at df = k - 1), and a 95% bootstrap
    interval that resamples whole clusters. The per-question SE is kept as `se_per_question`, for information."""
    x = np.asarray(values, dtype=float)
    if len(x) != len(clusters):
        raise ValueError("values and clusters must have the same length")
    r = se_clustered([float(v) for v in x], list(clusters))
    groups = list(_groups(clusters).values())
    sums = np.array([x[g].sum() for g in groups])
    counts = np.array([len(g) for g in groups], dtype=float)
    idx = np.random.default_rng(seed).integers(0, len(groups), size=(replicates, len(groups)))
    lo, hi = np.percentile(sums[idx].sum(axis=1) / counts[idx].sum(axis=1), [2.5, 97.5])
    return {
        "value": float(x.mean()),
        "n": len(x),
        "se": r["se"],
        "ci95": [float(lo), float(hi)],
        "se_per_question": float(x.std(ddof=1) / math.sqrt(len(x))) if len(x) > 1 else None,
        "k": r["k"],
        "df": r["df"],
        "se_method": "clustered",
    }


def _groups(clusters: Sequence[Any]) -> dict[Any, list[int]]:
    groups: dict[Any, list[int]] = {}
    for i, c in enumerate(clusters):
        groups.setdefault(c, []).append(i)
    return groups


def perplexity(
    logliks: Sequence[float],
    words: Sequence[float],
    nbytes: Sequence[float],
    seed: int = SEED,
    replicates: int = REPLICATES,
) -> dict[str, Summary]:
    """Word and byte perplexity and bits per byte of a document stream; SE and 95% interval from a bootstrap over
    documents."""
    ll, w, b = (np.asarray(v, dtype=float) for v in (logliks, words, nbytes))
    n = len(ll)

    def measures(ll_: Any, w_: Any, b_: Any) -> dict[str, Any]:
        return {
            "word_perplexity": np.exp(-ll_.sum(-1) / w_.sum(-1)),
            "byte_perplexity": np.exp(-ll_.sum(-1) / b_.sum(-1)),
            "bits_per_byte": -ll_.sum(-1) / (LN2 * b_.sum(-1)),
        }

    point = measures(ll, w, b)
    idx = np.random.default_rng(seed).integers(0, n, size=(replicates, n))
    boot = measures(ll[idx], w[idx], b[idx])
    out = {}
    for name, v in point.items():
        lo, hi = np.percentile(boot[name], [2.5, 97.5])
        out[name] = {
            "value": float(v),
            "n": n,
            "se": float(boot[name].std(ddof=1)),
            "ci95": [float(lo), float(hi)],
            "se_method": "bootstrap over documents",
        }
    return out


# --- clusters ---


def winogrande_pairs(docs: Sequence[dict[str, Any]]) -> list[int]:
    """Adjacent WinoGrande rows with the same option set are twin sentences and share a cluster
    (research/studies/2026-10-lm-eval-benchmarks/benchmarks/winogrande/przelicz.py `klastry_z_opcji`). Documents
    in split order."""
    options = [(d["option1"], d["option2"]) for d in docs]
    ids: list[int] = []
    i = c = 0
    while i < len(options):
        if i + 1 < len(options) and set(options[i]) == set(options[i + 1]):
            ids += [c, c]
            i += 2
        else:
            ids.append(c)
            i += 1
        c += 1
    return ids


WSC273_SCHEMA_THRESHOLD = 0.6


def wsc273_schemas(docs: Sequence[dict[str, Any]], threshold: float = WSC273_SCHEMA_THRESHOLD) -> list[int]:
    """WSC273 has no schema ID: a document belongs to the previous one's schema when the Jaccard similarity of
    their words is at least `threshold`
    (research/studies/2026-10-lm-eval-benchmarks/benchmarks/wsc273/wsc273.py `schematy`). Documents in split order."""

    def words(text: str) -> set[str]:
        return set(text.lower().replace(".", " ").replace(",", " ").split())

    out, g = [], 0
    for i, d in enumerate(docs):
        if i:
            a, b = words(d["text"]), words(docs[i - 1]["text"])
            if len(a & b) / len(a | b) < threshold:
                g += 1
        out.append(g)
    return out


CLUSTER_RULES: dict[str, Callable[[Sequence[dict[str, Any]]], list[int]]] = {
    "winogrande-pairs": winogrande_pairs,
    "wsc273-schemas": wsc273_schemas,
}


# --- baselines ---


def choice_baselines(outcomes: Sequence[dict[str, Any]], fixed_classes: bool, key: str) -> dict[str, Any]:
    """Random baseline (mean 1/k), majority baseline (the most common correct position), and the share of the most
    common prediction of metric `key`, in the fields of the results contract's `reference`."""
    n = len(outcomes)
    chance = sum(1 / o["k"] for o in outcomes) / n
    if not fixed_classes:
        return {
            "chance_value": chance,
            "majority_value": None,
            "majority_prediction_share": None,
            "constant_prediction": None,
        }
    gold = Counter(o["gold"] for o in outcomes)
    share = Counter(o[f"pred_{key}"] for o in outcomes).most_common(1)[0][1] / n
    return {
        "chance_value": chance,
        "majority_value": gold.most_common(1)[0][1] / n,
        "majority_prediction_share": share,
        "constant_prediction": share == 1.0,
    }


def cloze_baseline(targets: Sequence[str]) -> dict[str, Any]:
    """Cloze test: the share of the most common target word (research/common/ewaluuj.py `bazy_proby`, `cloze`)."""
    counts = Counter(str(t).strip() for t in targets)
    return {
        "chance_value": 0.0,
        "majority_value": counts.most_common(1)[0][1] / len(targets),
        "majority_prediction_share": None,
        "constant_prediction": None,
    }


# --- verdicts (research/tools/statystyka.py) ---


def verdict(z: float | None) -> str | None:
    if z is None or math.isnan(z):
        return None
    a = abs(z)
    return "strong" if a >= STRONG else "probable" if a >= PROBABLE else "noise"


def p_normal(z: float | None) -> float | None:
    return None if z is None else math.erfc(abs(z) / math.sqrt(2))


def verdict_p(p: float | None) -> str:
    if p is None:
        return INCONCLUSIVE
    return "strong" if p <= P_STRONG else "probable" if p <= P_PROBABLE else "noise"


def _beta_cf(a: float, b: float, x: float) -> float:
    """Continued fraction of the incomplete beta function (Numerical Recipes, betacf)."""
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > 1e-300 else 1e-300)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        for aa in (m * (b - m) * x / ((qam + m2) * (a + m2)), -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))):
            d = 1 + aa * d
            d = 1 / (d if abs(d) > 1e-300 else 1e-300)
            c = 1 + aa / c
            c = c if abs(c) > 1e-300 else 1e-300
            h *= d * c
        if abs(d * c - 1) < 1e-14:
            break
    return h


def p_t(t: float, df: float) -> float:
    """Two-sided p of Student's t with df degrees of freedom."""
    if t == 0:
        return 1.0
    x = df / (df + t * t)
    if x <= 0:
        return 0.0
    a, b = df / 2, 0.5
    ln = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    if x < (a + 1) / (a + b + 2):
        return math.exp(ln) * _beta_cf(a, b, x) / a
    return 1.0 - math.exp(ln) * _beta_cf(b, a, 1 - x) / b


def verdict_t(t: float, df: float) -> str:
    return verdict_p(p_t(t, df))


def clustered_weighted(groups: Sequence[tuple[int, float]]) -> dict[str, Any]:
    """groups: [(n, mean within the cluster)]. Weighted mean and SE over clusters, t at df = k - 1."""
    total, k = sum(n for n, _ in groups), len(groups)
    m = sum(n * d for n, d in groups) / total
    if k < 2:
        return {"difference": m, "se": None, "t": None, "df": k - 1, "p_t": None, "verdict": INCONCLUSIVE, "k": k}
    se = math.sqrt(sum((n * (d - m)) ** 2 for n, d in groups) * k / (k - 1)) / total
    if se == 0:
        return {
            "difference": m,
            "se": se,
            "t": None,
            "df": k - 1,
            "p_t": None,
            "verdict": INCONCLUSIVE if k < MIN_CLUSTERS else None,
            "k": k,
        }
    t = m / se
    p = p_t(t, k - 1)
    return {
        "difference": m,
        "se": se,
        "t": t,
        "df": k - 1,
        "p_t": p,
        "verdict": INCONCLUSIVE if k < MIN_CLUSTERS else verdict_p(p),
        "k": k,
    }


def se_clustered(values: Sequence[float], clusters: Sequence[Any], b: float = 0.0) -> dict[str, Any]:
    """SE over clusters of the mean of `values` minus `b`."""
    if len(values) != len(clusters) or not values:
        raise ValueError("values and clusters must have the same, non-zero length")
    sums: dict[Any, float] = {}
    counts: dict[Any, int] = {}
    for x, c in zip(values, clusters, strict=True):
        sums[c] = sums.get(c, 0.0) + x
        counts[c] = counts.get(c, 0) + 1
    r = clustered_weighted([(counts[c], sums[c] / counts[c] - b) for c in sorted(sums, key=str)])
    r.update({"n": len(values), "mean": r["difference"] + b, "b": b})
    return r


def against_constant(
    results: Sequence[float], golds: Sequence[Any], clusters: Sequence[Any] | None = None
) -> dict[str, Any]:
    """The model against a constant predictor that always picks the most common correct option (ties: the smallest
    label), paired per question: d_i = x_i - c_i. SE of the paired differences, or over clusters with t."""
    n = len(results)
    if n != len(golds) or n < 2:
        raise ValueError("results and golds must have the same length, at least 2")
    counts: dict[Any, int] = {}
    for g in golds:
        counts[g] = counts.get(g, 0) + 1
    constant = min(counts, key=lambda g: (-counts[g], g))
    c = [1.0 if g == constant else 0.0 for g in golds]
    d = [x - y for x, y in zip(results, c, strict=True)]
    out: dict[str, Any] = {"n": n, "constant": constant, "b": sum(c) / n, "score": sum(results) / n}
    if clusters is not None:
        r = se_clustered(d, clusters)
        out.update(
            {
                "difference": r["difference"],
                "se": r["se"],
                "t": r["t"],
                "df": r["df"],
                "p": r["p_t"],
                "verdict": r["verdict"] or INCONCLUSIVE,
                "k": r["k"],
                "method": "clustered",
            }
        )
        return out
    m = sum(d) / n
    se = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1) / n)
    z = m / se if se > 0 else None
    out.update(
        {
            "difference": m,
            "se": se,
            "z": z,
            "p": p_normal(z),
            "verdict": verdict(z) or INCONCLUSIVE,
            "method": "paired",
        }
    )
    return out


def against_baseline(
    results: Sequence[float],
    golds: Sequence[Any],
    main: Summary,
    baselines: dict[str, Any],
    clusters: Sequence[Any] | None = None,
) -> dict[str, Any]:
    """The score against b, the higher of the random baseline and the constant answer (research/common/ewaluuj.py
    `wobec_b`). A constant answer above random is compared paired per question; otherwise z = (score - b) / SE."""
    chance, majority = baselines.get("chance_value"), baselines.get("majority_value")
    if len(results) < 2:
        return {"b": max(chance or 0.0, majority or 0.0), "verdict": INCONCLUSIVE}
    if majority is not None and chance is not None and majority > chance:
        r = against_constant(results, golds, clusters)
        return {
            "b": r["b"],
            "baseline": "constant answer",
            **{k: r.get(k) for k in ("difference", "se", "z", "t", "df")},
            "verdict": r["verdict"],
            "method": r["method"],
        }
    assert chance is not None
    difference, se = main["value"] - chance, main["se"]
    out: dict[str, Any] = {"b": chance, "baseline": "random", "difference": difference, "se": se}
    if not se:
        return {**out, "verdict": INCONCLUSIVE}
    if main.get("se_method") == "clustered":
        t = difference / se
        return {
            **out,
            "t": t,
            "df": main["df"],
            "method": "clustered",
            "verdict": verdict_t(t, main["df"]) if main["k"] >= MIN_CLUSTERS else INCONCLUSIVE,
        }
    return {**out, "z": difference / se, "verdict": verdict(difference / se), "method": "per question"}
