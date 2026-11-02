"""BLiMP over checkpoints and weight averaging: report and chart generated from results/LICZBY.json only.

  python tools/liczby.py && python benchmarks/blimp/checkpoints.py raport
  -> benchmarks/blimp/results/CHECKPOINTS.md, benchmarks/blimp/results/blimp_curve.svg

`pliki(liczby, checkpoints_json)` is pure; tools/sprawdz_raporty.py (gate g) fails when a file on disk differs
from it by one byte. Numbers come from LICZBY.json; verdict words and yes/no flags from checkpoints.json.
"""
import json
import math
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sprawdz_raporty.py loads this file by path
from blimp_raport import SIATKA, TEKST, TEKST2, TLO, WERDYKT_EN, f, pkt

P = "blimp_krzywa"
WERDYKT_TEZY = {"potwierdzone": "CONFIRMED", "obalone": "REFUTED", "nierozstrzygniete": "NOT DETERMINED",
                "nieustalone": "NOT DETERMINED (a control failed)"}
ZASTRZEZENIA = {
    "bez_ostatniego_punktu_brak_wzrostu": "without step 13848 the slope does not rise",
    "trend_nieodroznialny_od_wahan_miedzy_checkpointami":
        "with the SE from the residuals of the checkpoint accuracies around the line, the trend cannot be told apart "
        "from the swings between checkpoints"}
KONTROLE_EN = {"urzadzenie": "device (CUDA vs MPS)", "gpu": "same model on different GPUs", "konwersja": "conversion",
               "sha_ckpt": "checkpoint SHA-256", "heldout_1.06": "held-out loss of Slayer 1.06 reproduced",
               "val_sha": "held-out set SHA-256", "odniesienia": "annealing references round to the protocol values",
               "sklad_srednich": "composition of the averages"}
# public_note of the training run (W&B-style run.json of SlayerLab/Slayer1B corpus 7150-13848), quoted
RESTART = "4x L40S to 10080 (10020+ a replica); 8x L40S from 10090, adopted at 10010"
KOLOR, KOLOR_SR, KOLOR_PY = "#2a78d6", "#1b9e77", "#eb6834"


AMENDMENT_2 = "(amendment 2: measured after avg3/avg5 BLiMP was read; not a protocol result)"


def etykieta(e):
    return f"{e} {AMENDMENT_2}" if e == "avg10" else e


def wer(x):
    return WERDYKT_EN.get(x, x)


def tak(x):
    return "yes" if x else "no"


def wykres_krzywej(punkty, pythia, srednie):
    """Accuracy per checkpoint (dot + CI95 whiskers) on bn tokens, Pythia-1B line, averages as diamonds at 1.06."""
    szer, wys, lewy, prawy, gora, dol = 900, 460, 80, 40, 60, 60
    xs = [p["mld"] for p in punkty]
    ys = [v for p in punkty for v in p["ci"]] + [pythia] + [s["acc"] for s in srednie]
    y0 = math.floor(min(ys) * 100 - 1) / 100
    y1 = math.ceil(max(ys) * 100 + 1) / 100
    x1 = math.ceil(max(xs) + 1)

    def X(v):
        return lewy + v / x1 * (szer - lewy - prawy)

    def Y(v):
        return gora + (y1 - v) / (y1 - y0) * (wys - gora - dol)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{szer}" height="{wys}" viewBox="0 0 {szer} {wys}" '
         f'font-family="system-ui, sans-serif" font-size="12">', f'<rect width="{szer}" height="{wys}" fill="{TLO}"/>',
         f'<text x="{lewy}" y="24" font-size="15" fill="{TEKST}">BLiMP accuracy over training (n = 67 000 pairs per point, CI95)</text>',
         f'<text x="{lewy}" y="42" fill="{TEKST2}">x: billions of training tokens (step x 2^20); open circles: side-branch ends</text>']
    k = 0.0
    while k <= y1 + 1e-9:
        if k >= y0 - 1e-9:
            s.append(f'<line x1="{lewy}" x2="{szer - prawy}" y1="{Y(k):.1f}" y2="{Y(k):.1f}" stroke="{SIATKA}"/>')
            s.append(f'<text x="{lewy - 8}" y="{Y(k) + 4:.1f}" text-anchor="end" fill="{TEKST2}">{k:.2f}</text>')
        k = round(k + 0.01, 2)
    for t in range(0, int(x1) + 1, 2):
        s.append(f'<text x="{X(t):.1f}" y="{wys - dol + 18}" text-anchor="middle" fill="{TEKST2}">{t}</text>')
    s.append(f'<line x1="{lewy}" x2="{szer - prawy}" y1="{Y(pythia):.1f}" y2="{Y(pythia):.1f}" stroke="{KOLOR_PY}" '
             f'stroke-dasharray="6 4" stroke-width="1.5"/>')
    s.append(f'<text x="{szer - prawy}" y="{Y(pythia) - 6:.1f}" text-anchor="end" fill="{KOLOR_PY}">Pythia-1B {pythia:.4f}</text>')
    gl = [p for p in punkty if p["glowny"]]
    s.append('<polyline fill="none" stroke="%s" stroke-width="1.5" points="%s"/>' % (
        KOLOR, " ".join(f"{X(p['mld']):.1f},{Y(p['acc']):.1f}" for p in gl)))
    for p in punkty:
        x = X(p["mld"])
        s.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{Y(p["ci"][0]):.1f}" y2="{Y(p["ci"][1]):.1f}" stroke="{KOLOR}" stroke-width="1.5"/>')
        wyp = KOLOR if p["glowny"] else TLO
        s.append(f'<circle cx="{x:.1f}" cy="{Y(p["acc"]):.1f}" r="4.5" fill="{wyp}" stroke="{KOLOR}" stroke-width="2"/>')
        s.append(f'<text x="{x:.1f}" y="{Y(p["ci"][0]) + 16:.1f}" text-anchor="middle" fill="{TEKST2}" font-size="10">{p["krok"]}</text>')
    for i, sr in enumerate(srednie):
        x, y = X(sr["mld"]) + 10 + 9 * i, Y(sr["acc"])
        s.append(f'<path d="M{x:.1f},{y - 5:.1f} L{x + 5:.1f},{y:.1f} L{x:.1f},{y + 5:.1f} L{x - 5:.1f},{y:.1f} Z" fill="{KOLOR_SR}"/>')
    if srednie:
        s.append(f'<text x="{szer - prawy}" y="{wys - 12}" text-anchor="end" fill="{KOLOR_SR}">diamonds right of 13848: '
                 f'{escape(", ".join(sr["nazwa"] for sr in srednie))} (weight averages)</text>')
    s.append("</svg>")
    return "\n".join(s) + "\n"


def pliki(liczby, kr):
    w = liczby["wartosci"]
    por = {p["id"]: p for p in liczby["porownania"]}

    def W(*k):
        return w.get("/".join([P, *map(str, k)]))

    def zt(pp, pk):
        """'+1.78 pts (z = 12.03, t = 3.18)' from the pair and the clustered comparison."""
        return f"{pkt(pp['roznica'])} (z = {f(pp['z'], 2)}" + (f", t = {f(pk['z'], 2)})" if pk else ")")

    def krok(a, b):
        return (por.get(f"k{b}_vs_k{a}/blimp_krzywa_krok/acc"), por.get(f"k{b}_vs_k{a}/blimp_krzywa_krok_klastr/acc"))

    punkty = []
    for i, pt in enumerate(kr["punkty"]):
        punkty.append({"i": i, "etykieta": pt["etykieta"], "repo": pt["repo"], "krok": pt["krok"], "glowny": pt["glowny_bieg"],
                       "mld": W("punkty", i, "mld"), "acc": W("punkty", i, "acc"), "se": W("punkty", i, "se"),
                       "ci": (W("punkty", i, "ci95", 0), W("punkty", i, "ci95", 1)), "n": W("punkty", i, "n"),
                       "luka": por[f"{pt['etykieta']}_vs_pythia/blimp_krzywa_luka/acc"]})
    pythia = W("pythia_acc")
    L = ["# BLiMP over training checkpoints and weight averaging: Slayer 1B", "",
         "Generated by `python benchmarks/blimp/checkpoints.py raport` from `results/LICZBY.json`; do not edit by hand.",
         "Protocol and thresholds (written and committed before the measurement): "
         "[`CHECKPOINTS_THRESHOLDS.md`](CHECKPOINTS_THRESHOLDS.md). Scoring as [`BLIMP.md`](BLIMP.md).", ""]

    # ---- question 1
    if "nachylenie" in kr:
        n = kr["nachylenie"]
        nk = por.get("krzywa/blimp_krzywa_nachylenie_klastr/acc")
        L += ["## Question 1: does the gap to Pythia-1B shrink over the final run?", ""]
        k_10_13, k_7_13, k_7_10, k_8_13 = krok(10010, 13848), krok(7150, 13848), krok(7150, 10010), krok(8600, 13848)
        if all(k_[0] for k_ in (k_10_13, k_7_13, k_7_10, k_8_13)):
            L += [f"**What the data show: step 13848 is closer to Pythia-1B than 10010, {zt(*k_10_13)}, and than 7150, "
                  f"{zt(*k_7_13)}. Between 7150 and 10010 the gap does not shrink: {zt(*k_7_10)}. The rise falls in the "
                  f"only interval that contains a restart of the run, and a trend cannot be told apart from the swings "
                  f"between checkpoints.** Step 10010 is a local dip: from 8600 the change is {zt(*k_8_13)}.", ""]
        pr = por.get("krzywa/blimp_krzywa_nachylenie_reszty/acc")
        if n["werdykt_luki"] == "potwierdzone" and n.get("zastrzezenia") and pr:
            L += [f"**Protocol rule: met ({WERDYKT_TEZY['potwierdzone']} on pair and paradigm SE at fixed checkpoints). "
                  f"Shrinking of the gap with tokens: not determined** - the rule does not include checkpoint-to-checkpoint "
                  f"noise (SE from residuals {pkt(pr['se_parowane'])}, p = {f(pr['p_t'], 2)}) and the rise sits in the "
                  "restart interval.", ""]
        else:
            L += [f"**Protocol verdict: {WERDYKT_TEZY[n['werdykt_luki']]}.**", ""]
        L += [f"The protocol rule (slope over 7150, 8600, 10010, 13848 > 0, certain or probable in both SEs): slope "
              f"{pkt(W('nachylenie', 'nachylenie'))} per billion tokens, pair-bootstrap SE {pkt(W('nachylenie', 'se'))}, "
              f"CI95 {pkt(W('nachylenie', 'ci95', 0))} to {pkt(W('nachylenie', 'ci95', 1))}, z = {f(W('nachylenie', 'z'), 2)} "
              f"({wer(n['werdykt'])}); over the 67 paradigms "
              + (f"t = {f(W('nachylenie', 't'), 2)}, df = {n['df']}, p = {f(W('nachylenie', 'p_klastr'), 4)} "
                 f"({wer(n['werdykt_klastr'])})." if nk else "no variance (no clustered verdict).")
              + f" Gap at 13848: {pkt(punkty[-1]['luka']['roznica'])}, SE {pkt(punkty[-1]['luka']['se'])}.", ""]
        if n.get("zastrzezenia"):
            L += ["Caveat (robustness checks added after the measurement, not protocol rules):", ""]
            b3 = kr.get("nachylenie_bez_ostatniego")
            pb, pbk = por.get("krzywa/blimp_krzywa_nachylenie_bez_ostatniego/acc"), por.get(
                "krzywa/blimp_krzywa_nachylenie_bez_ostatniego_klastr/acc")
            if b3 and pb:
                L += [f"- Without 13848 (slope over {', '.join(map(str, b3['kroki']))}): {pkt(pb['roznica'])} per billion "
                      f"tokens, z = {f(pb['z'], 2)} ({wer(pb['werdykt'])}), "
                      + (f"t = {f(pbk['z'], 2)} ({wer(pbk['werdykt'])})." if pbk else "no clustered verdict.")]
            pr = por.get("krzywa/blimp_krzywa_nachylenie_reszty/acc")
            if pr:
                L += [f"- SE from the residuals of the four checkpoint accuracies around the line: {pkt(pr['se_parowane'])}, "
                      f"t = {f(pr['z'], 2)}, df = {pr['df']}, p = {f(pr['p_t'], 2)} ({wer(pr['werdykt'])}). The pair-bootstrap "
                      "SE measures only the sampling noise of the pairs at fixed checkpoints, not how much a checkpoint "
                      "moves away from the line."]
            L += [f"- Between 10010 and 13848 the run was restarted on other hardware; the run's public note says: "
                  f"\"{RESTART}\". The rise falls in this interval, so it cannot be attributed to the extra tokens alone. "
                  "Next step that would separate a jump from a trend: BLiMP of step 11450 (8x L40S, after the restart). "
                  "The same note says that packs 4-7 of the training data (used from v1.04 on) exclude leak-scan "
                  "documents; which packs each interval saw is not checked here.",
                  "- In short: " + "; ".join(ZASTRZEZENIA[z] for z in n["zastrzezenia"]) + ".", ""]
        L += ["Refutation condition (protocol): the pair-level CI95 of the slope contains 0 or lies below 0. No "
              "extrapolation of the slope is reported: four points with this caveat give no basis for one.", ""]

    # ---- question 2 headline
    ho = kr.get("heldout", {})
    if ho.get("werdykt_substytut"):
        L += ["## Question 2: weight averaging vs LR annealing", ""]
        s = ho.get("srednie", {})
        q2 = [e for e in ("avg3", "avg5") if e in s]
        czesci = []
        for e in q2:
            pp = por[f"{e}_vs_1.06/heldout_srednia/loss"]
            czesci.append(f"{e} {f(pp['roznica'], 4)} nat, SE {f(pp['se'], 4)}, z = {f(pp['z'], 2)}, share "
                          f"{f(W('heldout', 'srednie', e, 'udzial_wygaszania'), 3)}")
        L += [f"**Protocol verdict on avg3 and avg5 (amendment 1): {WERDYKT_TEZY[ho['werdykt_substytut']]}**, the held-out "
              f"loss gain of averaging is at least half the gain of annealing ({'; '.join(czesci)}).", ""]
        if "avg10" in s and "vs_wygaszanie" in s["avg10"]:
            pa = por["avg10_vs_A/heldout_srednia_vs_wygaszanie/loss"]
            L += [f"Reading: on the held-out loss, the mean of the last 10 checkpoints gains about as much as the 150-step "
                  f"annealing: avg10 - annealed arm = {f(pa['roznica'], 4)} nat, SE {f(pa['se'], 4)}, z = {f(pa['z'], 2)} "
                  f"({wer(pa['werdykt'])}); annealed - constant-LR arm = {f(W('heldout', 'wygaszanie_vs_staly'), 4)} nat. "
                  "The gain is spread differently over the data components (table below), and BLiMP of the annealed model, "
                  "as well as avg10 on the other tests of the annealing run, are not measured, so this is a statement about "
                  "the held-out loss only, not that averaging replaces annealing.", ""]

    # ---- controls
    L += ["## Controls", ""]
    ku = kr.get("kontrola_urzadzenia")
    if ku:
        L += [f"- Device: Slayer 1.06 on CUDA (step 13848, converted trainer checkpoint) vs the MPS run of BLIMP.md: "
              f"{W('kontrola_urzadzenia', 'zmienione_pary')} of 67 000 pairs change outcome (limit 30: "
              f"{'pass' if ku['w_progu'] else 'FAIL'}), max |log-likelihood difference| {W('kontrola_urzadzenia', 'max_abs_ll'):.1e}."]
    for g in kr.get("kontrola_gpu", []):
        L += [f"- Same model on two GPU types ({g['model']}, {escape(g['a'])} vs {escape(g['b'])}): "
              f"{g['zmienione_pary']} pairs change outcome (limit 30: {'pass' if g['w_progu'] else 'FAIL'})."]
    if kr.get("konwersja_13848_max_abs") is not None:
        L += [f"- Conversion: `ckpt_13848.pt` vs the published Slayer 1.06 weights, max |difference| = {kr['konwersja_13848_max_abs']:g}."]
    if kr.get("sha_ckpt_zgodne") is not None:
        L += [f"- Every downloaded checkpoint matches the SHA-256 (LFS id) of the HF listing: {tak(kr['sha_ckpt_zgodne'])}."]
    for e, r in kr.get("srednie", {}).items():
        if r.get("kroki"):
            L += [f"- {e}: built from steps {', '.join(map(str, r['kroki']))} (read from the checkpoint files by "
                  f"`average_weights.py`); as the protocol prescribes: {tak(r['sklad_zgodny_z_protokolem'])}; every one of those "
                  f"checkpoints passed the SHA check: {tak(r['sha_ckpt_zgodne'])}; `model.safetensors` SHA-256 "
                  f"`{r['sha256_safetensors'][:16]}...`. Source: {escape(r['zrodlo'])}."]
        else:
            L += [f"- {e}: composition not recorded, not verified."]
    k = kr.get("kontrole")
    if k:
        zle = sorted({n for q in ("q1", "q2") for n, v in k[q].items() if v is not True})
        L += ["- Controls that block a verdict when they fail or are missing: "
              + (", ".join(KONTROLE_EN[n] for n in zle) + " NOT passed, verdicts set to not determined." if zle
                 else "all passed.")]
    L += [""]

    # ---- curve table
    L += ["## Accuracy per checkpoint", "",
          "Overall accuracy over 67 paradigms (n = 67 000 pairs), SE stratified by paradigm, bootstrap CI95. "
          f"Gap = checkpoint - Pythia-1B ({f(pythia, 4)}) on the same pairs, paired SE. Chance = 0.5. "
          "Points of side branches (1430, 2860) are not on the final run.", "",
          "| checkpoint | repo | final run | bn tokens | accuracy | SE | CI95 | gap to Pythia | SE | z | verdict |",
          "|---:|---|---|---:|---:|---:|---|---:|---:|---:|---|"]
    for p in punkty:
        r = p["luka"]
        L.append(f"| {p['krok']} | v{p['repo'].split('-')[1]} | {tak(p['glowny'])} | {f(p['mld'], 2)} | {f(p['acc'], 4)} | "
                 f"{f(p['se'], 4)} | {f(p['ci'][0], 4)}-{f(p['ci'][1], 4)} | {pkt(r['roznica'])} | {pkt(r['se'])} | "
                 f"z = {f(r['z'], 2)} | {wer(r['werdykt'])} |")
    L += ["", "![BLiMP over checkpoints](blimp_curve.svg)", ""]

    # ---- steps
    if "kroki" in kr:
        L += ["## Changes between checkpoints of the final run", "",
              "Later - earlier on the same pairs, every pair of the four points. Pairs: paired SE stratified by paradigm, "
              "verdict from |z|. Paradigms: t over the 67 paradigm differences, df = 66, verdict from p.", "",
              "| from | to | difference | SE pairs | z pairs | verdict pairs | t paradigms | p paradigms | verdict paradigms |",
              "|---:|---:|---:|---:|---:|---|---:|---:|---|"]
        for r in kr["kroki"]:
            pp, pk = krok(r["od"], r["do"])
            L.append(f"| {r['od']} | {r['do']} | {pkt(pp['roznica'])} | {pkt(pp['se'])} | z = {f(pp['z'], 2)} | {wer(pp['werdykt'])} | "
                     + (f"t = {f(pk['z'], 2)} | {f(pk['p_t'], 4)} | {wer(pk['werdykt'])} |" if pk else "- | - | - |"))
        L += [""]
        for i, r in enumerate(kr["kroki"]):
            if (r["od"], r["do"]) != (10010, 13848):
                continue
            wk = r["wklad_paradygmatow"]
            L += [f"Where the 10010 -> 13848 change sits: five paradigms carry {pkt(W('kroki', i, 'wklad_paradygmatow', 'suma_top'))} "
                  f"of the {pkt(W('kroki', i, 'roznica'))} (each paradigm weighs 1/67): "
                  + ", ".join(f"{t['grupa'].replace('_', ' ')} {pkt(W('kroki', i, 'wklad_paradygmatow', 'top', j, 'wklad'))}"
                              for j, t in enumerate(wk["top"]))
                  + f". Without them the change is {pkt(W('kroki', i, 'wklad_paradygmatow', 'bez_top'))}.", ""]

    # ---- phenomena
    if "nachylenie_zjawiska" in kr:
        L += ["## Which phenomena grow (slope over the final run)", "",
              "Slope per billion tokens of the phenomenon's accuracy. Pairs: pair-bootstrap SE, z, Holm over 12 phenomena "
              "at the 'probable' level (p <= 0.0455). Paradigms: t over the phenomenon's paradigm slopes, df = k - 1; "
              "fewer than 3 paradigms: undetermined. 'Grows' = slope > 0, Holm-significant on pairs and certain or probable "
              "on paradigms. The caveat of question 1 applies to every row.", "",
              "| phenomenon | paradigms | slope | SE pairs | z pairs | verdict pairs | Holm | t paradigms | df | verdict paradigms | grows (protocol rule) |",
              "|---|---:|---:|---:|---:|---|---|---:|---:|---|---|"]
        for z, r in kr["nachylenie_zjawiska"].items():
            pp = por[f"krzywa/blimp_krzywa_nachylenie_{z}/acc"]
            pk = por.get(f"krzywa/blimp_krzywa_nachylenie_klastr_{z}/acc")
            wk = wer(r["werdykt_klastr"] if r["k"] >= 3 else "nierozstrzygalne")
            L.append(f"| {z.replace('_', ' ')} | {r['k']} | {pkt(pp['roznica'])} | {pkt(pp['se'])} | z = {f(pp['z'], 2)} | "
                     f"{wer(pp['werdykt'])} | {tak(r['holm'])} | " + (f"t = {f(pk['z'], 2)}" if pk else "-")
                     + f" | {r['df']} | {wk} | {tak(r['rosnie'])} |")
        L += [""]
        for z, r in kr["nachylenie_zjawiska"].items():
            prz = por.get(f"krzywa/blimp_krzywa_nachylenie_reszty_{z}/acc")
            if not (r["rosnie"] and prz and r.get("kroki_sasiednie")):
                continue
            i_max = max(range(len(r["kroki_sasiednie"])), key=lambda i: r["kroki_sasiednie"][i]["roznica"])
            km = r["kroki_sasiednie"][i_max]
            sciezka = f"nachylenie_zjawiska/{z}/kroki_sasiednie/{i_max}/roznica"
            L += [f"{z.replace('_', ' ')} grows by the protocol rule, but with the SE from the residuals of its checkpoint "
                  f"accuracies the slope is {wer(prz['werdykt'])} (t = {f(prz['z'], 2)}, df = {prz['df']}, "
                  f"p = {f(prz['p_t'], 2)}), and the largest change between adjacent points is {km['od']} -> {km['do']}: "
                  f"{pkt(W(*sciezka.split('/')))}"
                  + (" (v1.03 -> v1.04)." if (km["od"], km["do"]) == (7150, 8600) else "."), ""]
    if "nachylenie_ln_D" in kr:
        n = kr["nachylenie_ln_D"]
        pk = por.get("krzywa/blimp_krzywa_nachylenie_lnD_klastr/acc")
        L += ["## Whole curve (descriptive)", "",
              f"OLS on ln(tokens) over all {len(punkty)} points, side branches included (no lineage, so no verdict on the "
              f"run): {pkt(W('nachylenie_ln_D', 'nachylenie'))} per unit of ln D, pair-bootstrap SE "
              f"{pkt(W('nachylenie_ln_D', 'se'))}, z = {f(W('nachylenie_ln_D', 'z'), 2)}; over the 67 paradigms "
              + (f"t = {f(pk['z'], 2)}, df = {pk['df']}, p = {f(pk['p_t'], 4)} ({wer(pk['werdykt'])})." if pk else
                 "no clustered value.") + " Points of side branches and of the final run differ in more than tokens, so "
              "this is context, not a scaling law.", ""]

    # ---- averaging
    if kr.get("srednie"):
        L += ["## Weight averaging vs Slayer 1.06", "",
              "Uniform mean of the last K trainer checkpoints of the Slayer 1.06 run (constant LR 6e-4), BLiMP paired against "
              "the CUDA run of step 13848 (= Slayer 1.06). The protocol expected no BLiMP change; a certain difference is "
              "reported, not claimed.", "",
              "| model | K | steps | accuracy | difference | SE pairs | z pairs | verdict pairs | t paradigms | verdict paradigms |",
              "|---|---:|---|---:|---:|---:|---:|---|---:|---|"]
        for e, r in kr["srednie"].items():
            pp = por[f"{e}_vs_k13848/blimp_srednia/acc"]
            pk = por.get(f"{e}_vs_k13848/blimp_srednia_klastr/acc")
            kroki = f"{r['kroki'][0]}-{r['kroki'][-1]}" if r.get("kroki") else "not recorded"
            L.append(f"| {etykieta(e)} | {len(r['kroki']) if r.get('kroki') else '-'} | {kroki} | {f(W('srednie', e, 'acc'), 4)} | "
                     f"{pkt(pp['roznica'])} | {pkt(pp['se'])} | z = {f(pp['z'], 2)} | {wer(pp['werdykt'])} | "
                     + (f"t = {f(pk['z'], 2)} | {wer(pk['werdykt'])} |" if pk else "- | - |"))
        L += [""]
        sr = list(kr["srednie"])
        zj = list(next(iter(kr["srednie"].values()))["blimp_zjawiska"])
        n_ist = sum(r["holm"] for e in sr for r in kr["srednie"][e]["blimp_zjawiska"].values())
        spadki = [(e, z) for e in sr for z, r in kr["srednie"][e]["blimp_zjawiska"].items()
                  if r["holm"] and r["roznica"] < 0]
        L += [f"Per phenomenon (protocol question 2): average - Slayer 1.06 on the same pairs, paired SE, Holm over "
              f"{len(zj)} phenomena x {len(sr)} averages at the 'probable' level. Holm-significant: {n_ist} of "
              f"{len(zj) * len(sr)}, of them {len(spadki)} decreases"
              + (" (" + ", ".join(f"{z.replace('_', ' ')} in {e}" for e, z in spadki) + ")" if spadki else "")
              + ". Averaging does not move BLiMP evenly: some phenomena fall while the overall accuracy rises. "
              "Paradigms: t over the phenomenon's paradigm differences, df = k - 1; fewer than 3 paradigms: undetermined.", "",
              "| phenomenon | average | paradigms | difference | SE pairs | z pairs | verdict pairs | Holm | t paradigms | verdict paradigms |",
              "|---|---|---:|---:|---:|---:|---|---|---:|---|"]
        for z in zj:
            for e in sr:
                r = kr["srednie"][e]["blimp_zjawiska"][z]
                pp = por[f"{e}_vs_k13848/blimp_srednia_{z}/acc"]
                pk = por.get(f"{e}_vs_k13848/blimp_srednia_klastr_{z}/acc")
                k_ = r.get("k")
                wk = wer(r.get("werdykt_klastr") if (k_ or 0) >= 3 else "nierozstrzygalne")
                L.append(f"| {z.replace('_', ' ')} | {etykieta(e)} | {k_ if k_ is not None else '-'} | {pkt(pp['roznica'])} | {pkt(pp['se'])} | "
                         f"z = {f(pp['z'], 2)} | {wer(pp['werdykt'])} | {tak(r['holm'])} | "
                         + (f"t = {f(pk['z'], 2)}" if pk else "-") + f" | {wk} |")
        L += [""]
        if ho:
            L += [f"Held-out loss (nat/token, {W('heldout', 'n_okien')} windows of 4096 tokens of the annealing run, "
                  f"`slayer-1b/wygaszanie/heldout.py`). Control: our Slayer 1.06 loss {f(W('heldout', 'loss_1.06'), 5)} vs "
                  f"{f(W('heldout', 'odniesienie_wygaszania'), 5)} in the annealing run "
                  f"({'pass' if ho['kontrola_1.06'] else 'FAIL'}); `val.bin` identical by SHA-256: "
                  f"{tak(ho.get('val_sha256_zgodne'))}. References read from `slayer-1b/wygaszanie/wyniki/heldout_*.json` on the same "
                  f"windows: annealed arm A - Slayer 1.06 = {f(W('heldout', 'wygaszanie_vs_1.06'), 4)} nat, A - constant-LR "
                  f"arm B = {f(W('heldout', 'wygaszanie_vs_staly'), 4)} nat.", "",
                  "| model | loss | difference to Slayer 1.06 | SE (paired windows) | z | verdict | share of A - Slayer 1.06 | "
                  "share of A - B | helps (protocol) | difference to A | SE | z | verdict |",
                  "|---|---:|---:|---:|---:|---|---:|---:|---|---:|---:|---:|---|"]
            for e, r in ho.get("srednie", {}).items():
                pp = por[f"{e}_vs_1.06/heldout_srednia/loss"]
                pa = por.get(f"{e}_vs_A/heldout_srednia_vs_wygaszanie/loss")
                L.append(f"| {e} | {f(W('heldout', 'srednie', e, 'loss'), 5)} | {f(pp['roznica'], 5)} | {f(pp['se'], 5)} | "
                         f"z = {f(pp['z'], 2)} | {wer(pp['werdykt'])} | {f(W('heldout', 'srednie', e, 'udzial_wygaszania'), 3)} | "
                         f"{f(W('heldout', 'srednie', e, 'udzial_vs_staly'), 3)} | {tak(r['pomaga'])} | "
                         + (f"{f(pa['roznica'], 5)} | {f(pa['se'], 5)} | z = {f(pa['z'], 2)} | {wer(pa['werdykt'])} |" if pa
                            else "- | - | - | - |"))
            if ho.get("komponenty"):
                kom = ho["komponenty"]
                modele = [m for m in ("A", "B", *ho.get("srednie", {})) if m in kom]
                nazwy = {"A": "annealed A", "B": "constant-LR B"}
                L += ["", "Per data component (mean over the component's windows of model - Slayer 1.06, nat/token):", "",
                      "| component | windows | " + " | ".join(nazwy.get(m, m) for m in modele) + " |",
                      "|---|---:|" + "---:|" * len(modele)]
                for c in kom["A"]:
                    L.append(f"| {c} | {kom['A'][c]['n_okien']} | "
                             + " | ".join(f(W("heldout", "komponenty", m, c, "roznica"), 4) for m in modele) + " |")
            L += ["", "The share is difference / (A - Slayer 1.06); the protocol rule is share >= 0.5 with |z| >= 3. Bits per token = "
                  "nat / ln 2 (field `roznica_bity_na_token`); bits per byte are not reported because the byte length of the "
                  "held-out windows was not saved.", ""]

    # ---- deviations and reproduction
    przerw = kr.get("przerwane", [])
    opis = ", ".join(f"{r['krok']} on {escape(r['gpu'])} at {r['pary']} of {r['wszystkie']} pairs "
                     f"({f(W('przerwane', i, 'udzial') * 100, 1)}%)" for i, r in enumerate(przerw))
    L += ["## Deviations and limits", "",
          "- Scope cut (protocol amendment 1, before any accuracy was read): the curve uses the checkpoints whose BLiMP run "
          "had finished at that moment. "
          + (f"Runs stopped part-way, read from the instance logs `results/checkpoints/points_*.log`: {opis}; " if przerw else "")
          + "12870 was not downloaded. None of them is reported. The primary slope stands on four points "
          "(7150, 8600, 10010, 13848).",
          "- The held-out windows come from pack-07 (web) and the shared files (core, legal, en) of the training "
          "dataset; which of these documents the training run had already seen is not known (`slayer-1b/wygaszanie/PROGI.md`), so "
          "part of the held-out loss may be measured on seen text, for averages and annealing alike.",
          "- avg10 (protocol amendment 2): the decision to build it was taken at 14:10 UTC, after the BLiMP results of avg3 "
          "and avg5 against Slayer 1.06 had been read (both certain on pairs) and before any held-out loss was computed. "
          "Its thresholds are the ones of the protocol. The question 2 verdict rests on avg3 and avg5.",
          "- The question 1 verdict follows the protocol rule; the caveat above comes from checks chosen after the results "
          "were seen (verification of task #52) and is reported as such.",
          "- A certain slope or difference is not its cause. For the averages, an obvious alternative reading is that "
          "averaging acts like a short LR decay (smaller effective step noise), which is what annealing does too.",
          "- Batch 64 with right padding on CUDA in float32 with TF32 off (protocol of BLIMP.md: batch 64 on MPS).",
          "- All checkpoints were scored on CUDA GPUs (vast.ai), Pythia-1B on Apple MPS (BLIMP.md). The device control above "
          "bounds the effect on the gap.",
          "- Tokens per step are taken as 2^20 for every version (batch 256 x block 4096); the checkpoints do not record it.",
          "- 1430 and 2860 are ends of side branches (the next version restarted from an earlier step), so they are not points "
          "of the final run and are kept out of the primary slope.",
          "- Weight averages are built from trainer checkpoints in float64 and stored in float32; no other change to the model. "
          "The composition of avg5 and avg10 comes from the stdout of `average_weights.py` copied from the session transcript, "
          "because those two runs did not write the instance log.",
          "- Contamination is not scanned (no access to the training corpus).", "",
          "## How to reproduce", "",
          "The commands that were run, with the paths of the current layout (code in `/workspace/kod` = `research/`; "
          "the run itself used the older layout `research/slayer-1b`, see `RECIPE.md`; each instance first ran "
          "`przygotuj` with a time limit for its own safety destroy):", "", "```bash",
          "# L40S: calibration job, then curve points (11450 stopped by the scope cut, 12870 never reached)",
          "bash benchmarks/blimp/checkpoints_instance.sh przygotuj 9000 && bash benchmarks/blimp/checkpoints_instance.sh kalibracja",
          "bash benchmarks/blimp/checkpoints_instance.sh punkty \"1.03:7150 1.04:8600 1.04:10010 1.04:11450 1.05:12870\"",
          "# A100: calibration job, then curve points (5720 stopped by the scope cut)",
          "bash benchmarks/blimp/checkpoints_instance.sh przygotuj 9000 && bash benchmarks/blimp/checkpoints_instance.sh kalibracja",
          "bash benchmarks/blimp/checkpoints_instance.sh punkty \"1.00:1430 1.01:2860 1.02:5720\"",
          "# RTX 4090: calibration job (k13848, avg3); the 'srednie' stage was started and stopped by the scope cut,",
          "# then avg5, held-out and avg10 by hand:",
          "bash benchmarks/blimp/checkpoints_instance.sh przygotuj 8000 && bash benchmarks/blimp/checkpoints_instance.sh kalibracja",
          "source benchmarks/blimp/checkpoints_instance.sh _funkcje",
          "python benchmarks/blimp/average_weights.py --wzor /workspace/m106 --wyjscie /workspace --zapisz 5 \\",
          "  /workspace/ckpt/ckpt_{13848,13800,13750,13700,13650}.pt",
          "blimp avg5 /workspace/avg5",
          "bash benchmarks/blimp/checkpoints_instance.sh heldout \"m106 avg3 avg5\"",
          "python benchmarks/blimp/download_checkpoint.py SlayerLab/Slayer1B-1.06-checkpoints 13400 /workspace/ckpt --log /workspace/czasy.jsonl",
          "python benchmarks/blimp/average_weights.py --wzor /workspace/m106 --wyjscie /workspace --zapisz 10 \\",
          "  /workspace/ckpt/ckpt_{13848,13800,13750,13700,13650,13600,13550,13500,13450,13400}.pt",
          "blimp avg10 /workspace/avg10",
          "python slayer-1b/wygaszanie/heldout.py --model /workspace/avg10 --dane /workspace/dane --wyjscie /workspace/wyniki/heldout_avg10.json",
          "# locally: per-pair files in benchmarks/blimp/results/checkpoints/<label>.jsonl.gz, held-out losses heldout_<model>.json",
          "BLIMP_DIR=<snapshot> python benchmarks/blimp/checkpoints.py zbierz [--gpu <dir with <gpu>/<label>.jsonl.gz>]",
          "python tools/liczby.py && python benchmarks/blimp/checkpoints.py raport && python tools/sprawdz_raporty.py",
          "```", ""]
    srednie_w = [{"nazwa": e, "acc": W("srednie", e, "acc"), "mld": punkty[-1]["mld"]} for e in kr.get("srednie", {})]
    return {"CHECKPOINTS.md": "\n".join(L), "blimp_curve.svg": wykres_krzywej(punkty, pythia, srednie_w)}


def raport(sciezka_liczb, katalog):
    katalog = Path(katalog)
    liczby = json.loads(Path(sciezka_liczb).read_text())
    kr = json.loads((katalog / "checkpoints.json").read_text())
    for nazwa, tresc in pliki(liczby, kr).items():
        (katalog / nazwa).write_text(tresc)
    print(f"{katalog / 'CHECKPOINTS.md'}, blimp_curve.svg")
