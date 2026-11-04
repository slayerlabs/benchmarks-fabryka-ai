"""Central-run chart: one panel per benchmark, Slayer highlighted, best model per benchmark marked."""
import json, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import liczby  # noqa: E402  (verdict of a t from its p: one set of thresholds for the repo)

B = Path(sys.argv[1])  # research/results/central-run
OUT = Path(sys.argv[2])
T = [("T01", "blimp", "BLiMP", "acc"), ("T02", "arc-challenge", "ARC-Challenge", "acc_norm"),
     ("T03", "wikitext-2", "WikiText-2 (byte ppl, lower = better)", "byte_perplexity"),
     ("T04", "multiblimp-pl", "MultiBLiMP-PL", "acc"), ("T44", "pubmedqa", "PubMedQA", "acc"),
     ("T45", "medmcqa", "MedMCQA", "acc"), ("T46", "social-iqa", "Social IQa", "acc")]
M = [("slayer1b-1.06", "Slayer 1B"), ("qwen3.5-0.8b-base", "Qwen3.5 0.8B"), ("lfm2.5-1.2b-base", "LFM2.5 1.2B"),
     ("lfm3-1.7b-base", "LFM3 1.7B"), ("eurollm-1.7b", "EuroLLM 1.7B")]
SLAYER, BEST, REST = "#2a78d6", "#3d3d3a", "#c3c2b7"
INK, MUTED = "#1f1f1e", "#6b6a64"


def klastry_blimp(d, m):
    """Per-paradigm accuracy of model m on BLiMP from the per-pair samples, or None."""
    import gzip
    f = B / d / m / "probki" / "T01_space.jsonl.gz"
    if not f.exists():
        return None
    acc = {}
    with gzip.open(f, "rt") as fh:
        for l in fh:
            r = json.loads(l)
            ll = [x[0] if isinstance(x, list) else x for x in r["filtered_resps"]]
            acc.setdefault(r["doc"]["UID"], []).append(float(max(range(len(ll)), key=ll.__getitem__) == r["target"]))
    return {g: sum(v) / len(v) for g, v in acc.items()}


def rozroznialny(d, i):
    """Is model i separable from Slayer over the paradigms (t over the paradigm differences, df = k - 1)?
    Pairs of one paradigm share a template, so the ±1 SE bars over pairs overstate the resolution."""
    a, b = klastry_blimp(d, M[0][0]), klastry_blimp(d, M[i][0])
    if not a or not b:
        return True
    r = [a[g] - b[g] for g in sorted(set(a) & set(b))]
    k = len(r)
    m = sum(r) / k
    sd = (sum((x - m) ** 2 for x in r) / (k - 1)) ** 0.5
    return liczby.werdykt_t(m / (sd / k ** 0.5), k - 1) != "szum"


def wynik(d, m, k):
    f = B / d / m / "results_rozszerzone.json"
    if not f.exists():
        return None
    o = json.loads(f.read_text())["observations"][0]
    if o["state"] != "ok":
        return None
    v = o["dodatkowe"]["space"][k]
    s = 1 if k == "byte_perplexity" else 100
    return v["value"] * s, v["se"] * s


plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": REST})
fig, axes = plt.subplots(2, 4, figsize=(13, 5.6))
for ax, (tid, d, name, k) in zip(axes.flat, T):
    vals = [wynik(d, m, k) for m, _ in M]
    ok = [(i, v) for i, v in enumerate(vals) if v]
    low = k == "byte_perplexity"
    best = (min if low else max)(ok, key=lambda x: x[1][0])[0]  # Slayer included: when it wins, it is the one marked
    # BLiMP: no "best" when Slayer vs the models is noise over the paradigms (the bars are SE over pairs)
    bez_rankingu = d == "blimp" and not any(rozroznialny(d, i) for i, _ in ok if i)
    if bez_rankingu:
        best = None
    slayer_leads = best == 0
    top = max(v[0] + v[1] for _, v in ok)
    for i, (m, label) in enumerate(M):
        y = len(M) - 1 - i
        v = vals[i]
        if not v:
            ax.text(0, y, "  not measured", va="center", color=MUTED, fontsize=8, style="italic")
            continue
        c = SLAYER if i == 0 else (BEST if i == best else REST)
        ax.barh(y, v[0], height=0.62, color=c, xerr=v[1], ecolor=MUTED, error_kw={"lw": 1, "capsize": 2})
        txt = f"{v[0]:.3f}" if low else f"{v[0]:.1f}"
        ax.text(v[0] + v[1] + top * 0.02, y, txt, va="center", fontsize=8.5, color=INK,
                fontweight="bold" if i in (0, best) else "normal")
    ax.set_yticks(range(len(M)))
    ax.set_yticklabels([l for _, l in M][::-1])
    for i, t in enumerate(ax.get_yticklabels()[::-1]):
        t.set_fontweight("bold" if i in (0, best) else "normal")
    ax.set_xlim(0, top * 1.25)
    ax.set_title(f"{tid} {name}" + ("  ★ best" if slayer_leads else "")
                 + ("\nno ranking: every difference to Slayer is noise over the 67 paradigms" if bez_rankingu else ""),
                 fontsize=9.5 if not bez_rankingu else 8.5,
                 color=SLAYER if slayer_leads else INK, loc="left", fontweight="bold" if slayer_leads else "normal")
    ax.grid(axis="x", color="#e8e7e2", lw=0.6); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=MUTED, length=0)
ax = axes.flat[-1]; ax.axis("off")
for y, (c, t) in enumerate([(SLAYER, "Slayer 1B (ours)"), (BEST, "best other model"), (REST, "other models")]):
    ax.barh(2 - y, 0.12, left=0.02, height=0.5, color=c)
    ax.text(0.18, 2 - y, t, va="center", fontsize=9.5, color=INK)
ax.text(0.02, -0.9, "accuracy in %, error bar = ±1 SE over questions\n(BLiMP: over pairs; over paradigms it is\nseveral times larger)\nfull sets, lm-eval",
        fontsize=8.5, color=MUTED, va="top")
ax.set_xlim(0, 1); ax.set_ylim(-2, 3)
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.text(0.01, 0.045, "Slayer 1B = Slayer 1.06, a checkpoint from about 1/8 of the planned training, without LR annealing "
         "(per the model author, 1 November 2026); the other models are fully trained.", fontsize=8.5, color=MUTED)
fig.text(0.01, 0.01, "LFM2.5: every task from the new environment on Apple M5 Pro (MPS, float32); other models on an RTX 4090 (CUDA).",
         fontsize=8.5, color=MUTED)
fig.savefig(OUT, dpi=150, facecolor="white")
