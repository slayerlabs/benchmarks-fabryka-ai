"""BLiMP report and charts generated from wyniki/LICZBY.json only (no number typed by hand).

  python narzedzia/liczby.py && python slayer_eval/blimp.py raport
  -> wyniki/blimp/BLIMP.md, wyniki/blimp/blimp_phenomena.svg, wyniki/blimp/blimp_paradigms.svg

`pliki(liczby, blimp_json)` is pure (returns {file name: text}); narzedzia/sprawdz_raporty.py calls it and
fails when a file on disk differs from it by one byte, so the report cannot be edited by hand.
"""
import json
import math
from html import escape
from pathlib import Path

WERDYKT_EN = {"pewne": "certain", "prawdopodobne": "probable", "szum": "noise", "nierozstrzygalne": "undetermined",
              None: "-"}
MODELE = [("1.06", "Slayer 1.06", "#2a78d6", "circle"), ("pythia-1b", "Pythia-1B", "#eb6834", "square")]
TEKST, TEKST2, SIATKA, TLO = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
EKSPL = "*[Added after the measurement: exploratory, not in THRESHOLDS.md.]*"


def f(x, cyfr=3):
    return "-" if x is None else f"{x:.{cyfr}f}"


def zakres(lo, hi, cyfr):
    """'lo-hi', or one value when both print the same."""
    a, b = f(lo, cyfr), f(hi, cyfr)
    return a if a == b else f"{a}-{b}"


def pkt(x, cyfr=2):
    return "-" if x is None else f"{x * 100:.{cyfr}f} pts"


def nazwa_zjawiska(z):
    return z.replace("_", " ")


def dane(liczby):
    w = liczby["wartosci"]
    por = {p["zadanie"]: p for p in liczby["porownania"]
           if p["rodzina"] == "slayer_vs_pythia" and p["test"] == "blimp"}

    def model(m):
        return {"acc": w[f"blimp/modele/{m}/acc"], "se": w[f"blimp/modele/{m}/se"], "n": w[f"blimp/modele/{m}/n"],
                "ci": (w[f"blimp/modele/{m}/ci95/0"], w[f"blimp/modele/{m}/ci95/1"])}

    zjawiska = sorted({k.split("/")[4] for k in w if k.startswith("blimp/modele/1.06/zjawiska/")})

    def zj(m, z):
        p = f"blimp/modele/{m}/zjawiska/{z}"
        return {"acc": w[f"{p}/acc"], "ci": (w[f"{p}/ci95/0"], w[f"{p}/ci95/1"]), "n": w[f"{p}/n"]}

    return w, por, {m: model(m) for m, *_ in MODELE}, zjawiska, zj


def wykres(wiersze, tytul, os_min=0.4):
    """Dot + CI95 whiskers per model, one row per item, chance line at 0.5. wiersze: [(label, {m: (acc, lo, hi)})]."""
    lewy, prawy, gora, wys_w = 330, 40, 70, 22
    szer = 900
    wys = gora + len(wiersze) * wys_w + 50
    x0, x1 = lewy, szer - prawy

    def X(v):
        return x0 + (max(v, os_min) - os_min) / (1 - os_min) * (x1 - x0)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{szer}" height="{wys}" viewBox="0 0 {szer} {wys}" '
         f'font-family="Helvetica, Arial, sans-serif" role="img" aria-label="{escape(tytul)}">',
         f'<rect width="{szer}" height="{wys}" fill="{TLO}"/>',
         f'<text x="20" y="28" font-size="16" fill="{TEKST}">{escape(tytul)}</text>']
    lx = 20
    for m, nazwa, kolor, ksztalt in MODELE:
        s.append(znacznik(lx + 6, 50, kolor, ksztalt))
        s.append(f'<text x="{lx + 16}" y="54" font-size="12" fill="{TEKST2}">{escape(nazwa)} (dot = accuracy, whiskers = CI95)</text>')
        lx += 400
    for k in range(int(os_min * 10), 11):
        v = k / 10
        s.append(f'<line x1="{X(v):.1f}" y1="{gora - 8}" x2="{X(v):.1f}" y2="{wys - 40}" stroke="{SIATKA}" stroke-width="1"/>')
        s.append(f'<text x="{X(v):.1f}" y="{wys - 24}" font-size="11" fill="{TEKST2}" text-anchor="middle">{v:.1f}</text>')
    s.append(f'<line x1="{X(0.5):.1f}" y1="{gora - 8}" x2="{X(0.5):.1f}" y2="{wys - 40}" stroke="{TEKST2}" '
             f'stroke-width="1.5" stroke-dasharray="4 3"/>')
    s.append(f'<text x="{X(0.5) + 4:.1f}" y="{wys - 44}" font-size="11" fill="{TEKST2}">chance 0.5</text>')
    s.append(f'<text x="{(x0 + x1) / 2:.1f}" y="{wys - 8}" font-size="11" fill="{TEKST2}" text-anchor="middle">accuracy</text>')
    for i, (etykieta, wart) in enumerate(wiersze):
        y = gora + i * wys_w + wys_w / 2
        s.append(f'<text x="{lewy - 10}" y="{y + 4:.1f}" font-size="12" fill="{TEKST}" text-anchor="end">{escape(etykieta)}</text>')
        for j, (m, nazwa, kolor, ksztalt) in enumerate(MODELE):
            acc, lo, hi = wart[m]
            yy = y + (j - 0.5) * 7
            opis = f"{etykieta}, {nazwa}: {acc:.3f} (CI95 {lo:.3f}-{hi:.3f})"
            s.append(f'<g><title>{escape(opis)}</title>'
                     f'<line x1="{X(lo):.1f}" y1="{yy:.1f}" x2="{X(hi):.1f}" y2="{yy:.1f}" stroke="{kolor}" stroke-width="2" stroke-linecap="round"/>'
                     f'{znacznik(X(acc), yy, kolor, ksztalt)}</g>')
    s.append("</svg>")
    return "\n".join(s) + "\n"


def znacznik(x, y, kolor, ksztalt):
    if ksztalt == "square":
        return f'<rect x="{x - 4:.1f}" y="{y - 4:.1f}" width="8" height="8" rx="1" fill="{kolor}" stroke="{TLO}" stroke-width="2"/>'
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{kolor}" stroke="{TLO}" stroke-width="2"/>'


def raport(sciezka_liczb, katalog):
    katalog = Path(katalog)
    liczby = json.loads(Path(sciezka_liczb).read_text())
    bl = json.loads((katalog / "blimp.json").read_text())
    for nazwa, tresc in pliki(liczby, bl).items():
        (katalog / nazwa).write_text(tresc)
    print(f"{katalog / 'BLIMP.md'}, 2 SVG")


def pliki(liczby, bl):
    """{file name: text} of the report and both charts. Numbers from LICZBY.json; yes/no flags and names
    (not numbers, so not in LICZBY) from blimp.json."""
    w, por, mod, zjawiska, zj = dane(liczby)
    an = bl["analiza"]
    sl, py = mod["1.06"], mod["pythia-1b"]
    og, kl, kl2, tok = por["blimp"], por["blimp_klastrowane"], por["blimp_klastrowane_bez_2"], por["blimp_na_token"]
    gen = "blimp/analiza/generalizacja"
    pd_ = {g: {k.split("/")[-1]: w[k] for k in w if k.startswith(f"blimp/analiza/paradygmaty_dodatkowe/{g}/")}
           for g in bl["porownanie"]["paradygmaty"]}
    out = {}

    # charts
    wiersze = [("BLiMP overall (67 paradigms)", {m: (mod[m]["acc"], *mod[m]["ci"]) for m, *_ in MODELE})]
    wiersze += [(nazwa_zjawiska(z), {m: (zj(m, z)["acc"], *zj(m, z)["ci"]) for m, *_ in MODELE}) for z in zjawiska]
    out["blimp_phenomena.svg"] = wykres(
        wiersze, "BLiMP full set: overall and 12 phenomena (n = 67 000 minimal pairs per model)")
    parad = sorted((por[f"blimp_{g}"] for g in bl["porownanie"]["paradygmaty"]), key=lambda p: p["roznica"])
    out["blimp_paradigms.svg"] = wykres(
        [(p["zadanie"][len("blimp_"):], {"1.06": (p["wartosc_a"], *ci_wilson(p["wartosc_a"])),
                                         "pythia-1b": (p["wartosc_b"], *ci_wilson(p["wartosc_b"]))}) for p in parad],
        "BLiMP: 67 paradigms, n = 1000 pairs each, sorted by Slayer - Pythia", os_min=0.0)

    kp = {k.split("/")[-1]: v for k, v in w.items() if k.startswith("blimp/kontrola_pythia/")}
    pan = {wr: {**{k.split("/")[-1]: w[k] for k in w if k.startswith(f"blimp/panel_space/{wr}/")},
                **{k: v for k, v in bl["panel_space"][wr].items() if isinstance(v, bool)}}
           for wr in ("pair_id", "sha256")}
    licz = {"pewne": [0, 0], "prawdopodobne": [0, 0], "szum": [0, 0]}
    for p in parad:
        licz[p["werdykt"]][0 if p["roznica"] > 0 else 1] += 1
    nie_holm = [p["zadanie"][len("blimp_"):] for p in parad
                if p["werdykt"] == "pewne" and not an["paradygmaty_dodatkowe"][p["zadanie"][len("blimp_"):]]["holm"]]
    znak = an["generalizacja"]["znak"]

    L = ["# BLiMP full set: Slayer 1.06 and Pythia-1B", "",
         "Generated by `python slayer_eval/blimp.py raport` from `wyniki/LICZBY.json`; do not edit by hand.",
         "Protocol and thresholds (written before the measurement): [`THRESHOLDS.md`](THRESHOLDS.md).", "",
         f"**Slayer 1.06: {f(sl['acc'], 4)} (CI95 {f(sl['ci'][0], 4)}-{f(sl['ci'][1], 4)}), Pythia-1B: "
         f"{f(py['acc'], 4)} (CI95 {f(py['ci'][0], 4)}-{f(py['ci'][1], 4)}) on all {sl['n']} minimal pairs.**", "",
         f"- **On these 67 000 pairs:** difference {pkt(og['roznica'])}, paired SE {pkt(og['se'])}, "
         f"z = {f(og['z'], 2)}: {WERDYKT_EN[og['werdykt']]}. This says the gap is real for these pairs. "
         "This is the comparison THRESHOLDS.md fixed before the measurement.",
         f"- **Generalised to paradigms** (the 67 paradigms as clusters, since pairs of one paradigm share a "
         f"template): SE {pkt(kl['se'])}, t = {f(kl['z'], 2)}, df = {kl['df']}, p = {f(kl['p_t'], 4)} from the t "
         f"distribution: {WERDYKT_EN[kl['werdykt']]}; bootstrap over paradigms "
         f"CI95 {pkt(w[gen + '/ci95_bootstrap_paradygmatow/0'])} to {pkt(w[gen + '/ci95_bootstrap_paradygmatow/1'])}; "
         f"Pythia ahead in {znak['b_lepszy']} of {an['generalizacja']['k']} paradigms (exact sign test, p < 10^-7). "
         f"Sensitivity: without the 2 paradigms with the largest gap t = {f(kl2['z'], 2)}, df = {kl2['df']}, "
         f"p = {f(kl2['p_t'], 4)} ({WERDYKT_EN[kl2['werdykt']]}), so the paradigm-level verdict rests partly on a "
         f"few paradigms. {EKSPL}",
         f"- **Per token** (log-likelihood divided by the number of tokens, since the tokenizers differ): difference "
         f"{pkt(tok['roznica'])}, SE {pkt(tok['se'])}, z = {f(tok['z'], 2)}: {WERDYKT_EN[tok['werdykt']]}. {EKSPL}", "",
         "THRESHOLDS.md fixed, before any result was seen: the pair-level comparison and its verdicts (overall, "
         "phenomena, paradigms), the Pythia control and the Space panel check. Everything marked *added after the "
         "measurement* was added after the results were seen, partly at reviewers' request: paradigms as clusters "
         "(read through the t distribution), the k < 3 rule, the Holm correction, per-token scores, the "
         "tokenization and same-words splits, and the random-panel analysis of the Space panel. Read those as "
         "exploratory. Verdict thresholds everywhere are those of THRESHOLDS.md: |z| >= 3 certain, 2-3 probable, "
         f"< 2 noise; a t with df = k - 1 is held to the same two-sided p (<= {f(w['blimp/analiza/progi_p/pewne'], 4)} "
         f"certain, <= {f(w['blimp/analiza/progi_p/prawdopodobne'], 4)} probable).", "",
         "## Overall", "",
         "| model | accuracy | n | SE | CI95 (bootstrap, stratified) | chance | majority |",
         "|---|---:|---:|---:|---|---:|---|"]
    for m, nazwa, *_ in MODELE:
        x = mod[m]
        L.append(f"| {nazwa} | {f(x['acc'], 4)} | {x['n']} | {f(x['se'], 4)} | {f(x['ci'][0], 4)}-{f(x['ci'][1], 4)} | "
                 f"0.5 | n/a (gold always first by construction) |")
    L += ["", "## Control: Pythia-1B against the published value", "",
          f"Our Pythia-1B {f(kp['nasza'], 4)} vs reference {f(kp['wartosc'], 4)}: difference "
          f"{pkt(kp['roznica'])}, threshold +-2 points: "
          f"**{'within' if abs(kp['roznica']) <= kp['prog'] else 'outside, control not confirmed'}**.",
          "The reference is the mean of the 67 `blimp_*` values in the EleutherAI/pythia repo file "
          "`evals/pythia-v0/pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json`. "
          "It is the v0 model (weights before the Pythia re-train) scored by the old harness without the leading "
          "space; the v1 eval folders of that repo have no BLiMP and no other published BLiMP value for "
          "`EleutherAI/pythia-1b` was found. It is a sanity range, not an exact reference.", ""]
    L += sekcja_space(w, pan, sl)
    L += ["## 12 phenomena", "",
          "Two verdicts per phenomenon. *Pairs* (fixed in THRESHOLDS.md): paired SE over the pairs of the "
          "phenomenon, verdict from |z| (is the gap real on these pairs); it applies at any number of paradigms. "
          "*Paradigms*: SE over the paradigm differences of the phenomenon, t = mean / SE with df = k - 1, verdict "
          "from the p of the t distribution (would it hold for other paradigms of the phenomenon); with fewer than "
          f"3 paradigms this column gives no verdict (undetermined). The paradigm columns: {EKSPL}", "",
          "| phenomenon | paradigms | n | Slayer 1.06 | Pythia-1B | difference | SE pairs | z pairs | verdict pairs "
          "| SE paradigms | t paradigms | df | p paradigms | verdict paradigms |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---|"]
    for z in zjawiska:
        p, pk = por[f"blimp_zjawisko_{z}"], por[f"blimp_zjawisko_klastr_{z}"]
        k = an["zjawiska_klastrowe"][z]["k"]
        wer_k = "undetermined (k < 3)" if k < 3 else WERDYKT_EN[pk["werdykt"]]
        L.append(f"| {nazwa_zjawiska(z)} | {k} | {int(zj('1.06', z)['n'])} | {f(p['wartosc_a'])} | {f(p['wartosc_b'])} | "
                 f"{pkt(p['roznica'], 1)} | {pkt(p['se'])} | z = {f(p['z'], 2)} | {WERDYKT_EN[p['werdykt']]} | "
                 f"{pkt(pk['se'])} | t = {f(pk['z'], 2)} | {pk['df']} | {f(pk['p_t'], 4)} | {wer_k} |")
    odwr = an["przewagi_a_odwrocone_na_token"]
    L += ["", "![BLiMP overall and phenomena](blimp_phenomena.svg)", "",
          "## 67 paradigms", "",
          f"n = 1000 pairs per paradigm and model. On pairs: Slayer ahead {licz['pewne'][0]} certain, "
          f"{licz['prawdopodobne'][0]} probable; Pythia ahead {licz['pewne'][1]} certain, {licz['prawdopodobne'][1]} "
          f"probable; noise {sum(licz['szum'])}. With 67 comparisons a Holm correction (family-wise 5%) keeps "
          f"{an['holm_odrzucone']} differences; the 'certain' rows marked `certain, not Holm` "
          f"({', '.join(nie_holm)}) do not survive it. Holm, per token and same tokenization: {EKSPL}", "",
          f"The order of the gaps depends on the measure: Spearman rank correlation between the summed and the "
          f"per-token differences is {f(w['blimp/analiza/spearman_suma_na_token'], 2)}. "
          f"{len(odwr)} of the {an['przewagi_a_pewne']} certain Slayer advantages reverses per token: "
          + ", ".join(f"{g} ({pkt(por['blimp_' + g]['roznica'], 1)} summed, {pkt(pd_[g]['roznica_na_token'], 1)} "
                      "per token)" for g in odwr)
          + f". Another example: tough_vs_raising_1 is "
          f"{pkt(por['blimp_tough_vs_raising_1']['roznica'], 1)} summed, "
          f"{pkt(pd_['tough_vs_raising_1']['roznica_na_token'], 1)} per token, and "
          f"{pkt(pd_['tough_vs_raising_1']['roznica_ta_sama_tokenizacja'], 1)} on the pairs where both tokenizers "
          "give the same token difference between good and bad sentence. Read the ranking as 'where the gap is "
          "large under summed log-likelihood', not as a ranking of syntactic weaknesses.", "",
          "| paradigm | Slayer 1.06 | Pythia-1B | difference | SE | z | verdict | per token | same tokenization (n) |",
          "|---|---:|---:|---:|---:|---:|---|---:|---|"]
    for p in parad:
        g = p["zadanie"][len("blimp_"):]
        d = pd_[g]
        wer = WERDYKT_EN[p["werdykt"]]
        if p["werdykt"] == "pewne" and g in nie_holm:
            wer = "certain, not Holm"
        L.append(f"| {g} | {f(p['wartosc_a'])} | {f(p['wartosc_b'])} | {pkt(p['roznica'], 1)} | {pkt(p['se'])} | "
                 f"z = {f(p['z'], 2)} | {wer} | {pkt(d['roznica_na_token'], 1)} | "
                 f"{pkt(d.get('roznica_ta_sama_tokenizacja'), 1)} ({int(d['n_ta_sama_tokenizacja'])}) |")
    L += ["", "![BLiMP paradigms](blimp_paradigms.svg)", ""]
    L += sekcja_tokenizacji(w, por)
    L += sekcja_odstepstw(w, bl)
    L += ["## How to reproduce", "",
          "```bash",
          "# data: nyu-mll/blimp @ 877fba0801ffb7cbd8c39c1ff314a46f053f6036 (67 parquet files) in BLIMP_DIR or the HF cache",
          "BLIMP_DIR=<snapshot> python slayer_eval/hipoteza_formatu.py licz --model <slayer-1.06 dir> --zadania blimp \\",
          "  --wyjscie <out>/1.06 --device mps --batch 64",
          "BLIMP_DIR=<snapshot> python slayer_eval/hipoteza_formatu.py licz --model <pythia-1b dir> --zadania blimp \\",
          "  --wyjscie <out>/pythia-1b --device mps --batch 64",
          "BLIMP_DIR=<snapshot> python slayer_eval/blimp.py zbierz --wyniki <out>",
          "python narzedzia/liczby.py && python slayer_eval/blimp.py raport && python narzedzia/sprawdz_raporty.py",
          "```", "",
          "Per-pair log-likelihoods (ids and numbers only, no sentences): `wyniki/blimp/raw/<model>.jsonl.gz`;",
          "without weights, `BLIMP_DIR=<snapshot> python slayer_eval/blimp.py zbierz --wyniki wyniki/blimp/raw` "
          "rebuilds `blimp.json` from them.", ""]
    out["BLIMP.md"] = "\n".join(L)
    return out


def sekcja_space(w, pan, sl):
    ps = pan["sha256"]
    sp = "blimp/space"
    return ["## Agreement with the Space (panel of 200)", "",
            f"Space T01, Slayer 1.06: {f(w[sp + '/wartosc'], 4)} (CI95 {f(w[sp + '/ci95/0'], 3)}-"
            f"{f(w[sp + '/ci95/1'], 3)}, n = 200). Panel rebuilt by METHOD.md section 3 "
            "(2 per member, the remaining 66 slots by largest deficit, ties by member name, inside a member by "
            "SHA-256 of `20261028|blimp|<member>|<source id>`):", "",
            "| source id in the hash | n | Slayer 1.06 | difference to Space | inside Space CI95 | Pythia-1B |",
            "|---|---:|---:|---:|---|---:|"] + [
        f"| {opis} | {int(pan[wr]['n'])} | {f(pan[wr]['1.06'], 4)} | {f(pan[wr]['roznica_1.06_do_space'], 4)} | "
        f"{'yes' if pan[wr]['w_ci95_space'] else 'no'} | {f(pan[wr]['pythia-1b'], 4)} |"
        for wr, opis in (("pair_id", "`pair_id`"), ("sha256", "SHA-256 of the canonical row"))] + [
        "", "**Verdict by THRESHOLDS.md: panel not identical (not reproduced).** The Space `source_id_digest` is "
        "not reproduced by any id/separator/order format we tried. METHOD.md section 3 names the document's native "
        "id as the source id; for BLiMP that is `pair_id`, and that panel gives a value outside the Space CI95.", "",
        f"The rest of this section: {EKSPL}", "",
        "The SHA-256-of-the-row panel was added as a second reading, not as the protocol. Its Slayer 1.06 value "
        f"is the same as the Space value to all printed digits (difference {f(ps['roznica_1.06_do_space'], 4)}). "
        "Among random panels with the same per-member sizes drawn from Slayer's own per-pair results, a share of "
        f"{f(ps['p_rownej_wartosci_losowo'], 4)} gives exactly this value (20 000 draws, seed 20261028); corrected "
        f"for the two source-id readings we tried, {f(ps['p_rownej_wartosci_skorygowane_2_warianty'], 3)}. So the "
        "Space most likely hashes the canonical row and this is probably its panel; that is an inference from one "
        "value, not proof.", "",
        "The panel is a lucky one for both models: only "
        f"{f(ps['udzial_paneli_nie_nizszych_1.06'] * 100, 1)}% of random panels give Slayer this value or higher, and "
        f"{f(ps['udzial_paneli_nie_nizszych_pythia-1b'] * 100, 1)}% for Pythia. The full-set value "
        f"{f(sl['acc'], 4)} lies outside the Space CI95. The Space CI95 is narrower than the spread of random "
        f"panels of this allocation (ratio {f(w[sp + '/stosunek_rozrzutu_paneli_do_ci_space'], 2)}), so it "
        "understates the panel-to-panel uncertainty (inference: the Space bootstrap resamples the 200 chosen pairs, "
        "not the choice of pairs). Use the full set.", ""]


def sekcja_tokenizacji(w, por):
    an = "blimp/analiza/tokenizacja"
    wr = "blimp/analiza/ten_sam_worek_slow"
    ts, tr = por["blimp_ta_sama_tokenizacja"], por["blimp_rozna_tokenizacja"]
    lt, ln = por["blimp_ten_sam_worek_slow"], por["blimp_inny_worek_slow"]
    return ["## What the gap measures: tokenizer and vocabulary", "", EKSPL, "",
            f"- Slayer's tokenizer cuts these English sentences into {f(w[an + '/stosunek_tokenow_a_do_b'], 2)}x as many "
            "tokens as Pythia's.",
            "- Accuracy depends on the token-length difference within a pair. On the "
            f"{int(w[an + '/ta_sama_roznica_tokenow/n'])} pairs where both tokenizers give the same token "
            f"difference between good and bad sentence the gap is {pkt(ts['roznica'])} (SE {pkt(ts['se'])}, "
            f"z = {f(ts['z'], 2)}); on the {int(w[an + '/rozna_roznica_tokenow/n'])} other pairs {pkt(tr['roznica'])} "
            f"(SE {pkt(tr['se'])}, z = {f(tr['z'], 2)}). About {pkt(-w[an + '/czesc_luki_od_tokenizacji'])} of the "
            f"overall gap goes with the tokenizer difference.",
            f"- On the {int(w[wr + '/tak/n'])} pairs ({int(w[wr + '/tak/k_paradygmatow'])} paradigms) whose good and bad "
            f"sentence use the same words, as a multiset, and differ only in word order, the gap is "
            f"{pkt(lt['roznica'])} (SE {pkt(lt['se'])}, z = {f(lt['z'], 2)}: {WERDYKT_EN[lt['werdykt']]}; over "
            f"paradigms t = {f(w[wr + '/tak/t_paradygmatow'], 2)}). On the {int(w[wr + '/nie/n'])} other pairs "
            f"({int(w[wr + '/nie/k_paradygmatow'])} paradigms), where the sentences differ in a word or its form, "
            f"{pkt(ln['roznica'])} (SE {pkt(ln['se'])}, z = {f(ln['z'], 2)}: {WERDYKT_EN[ln['werdykt']]}; over "
            f"paradigms t = {f(w[wr + '/nie/t_paradygmatow'], 2)}). On the word-order pairs the paradigm differences "
            f"are large in both directions (mean |d| {pkt(w[wr + '/tak/srednia_abs_paradygmatow'], 1)} vs "
            f"{pkt(w[wr + '/nie/srednia_abs_paradygmatow'], 1)}) and cancel out; Pythia's steady advantage is where "
            "the sentences differ in a word or its form. A paradigm with pairs of both kinds is counted on both "
            "sides. This is a correlation over paradigm types, not a controlled experiment.",
            f"- The BLiMP flag `lexically_identical` does not mark this split: {int(w[wr + '/flaga_bez_tego_samego_worka'])} "
            f"of its {int(w[wr + '/flaga_lexically_identical_paradygmaty'])} paradigms have pairs with different word "
            "forms (e.g. sketch / sketches in determiner_noun_agreement_1), so the split is made on the words of each "
            "pair.", ""]


def sekcja_odstepstw(w, bl):
    kf = "blimp/kontrola_forward"
    return ["## Deviations from METHOD.md and limits", "",
            "- **Batch and device:** METHOD.md runs batch 1; we ran batch 64 with right padding on Apple MPS "
            "(causal attention, so padding does not reach scored tokens). MPS and CPU log-likelihoods differ by float "
            "noise, so only pairs whose two sentences score almost the same can flip: "
            f"{int(w['blimp/modele/1.06/pary_bliskie_remisu'])} for Slayer and "
            f"{int(w['blimp/modele/pythia-1b/pary_bliskie_remisu'])} for Pythia (of 67 000) are closer than that "
            "noise, which bounds the effect. Our CPU re-run of 300 pairs per model flipped none; an independent CPU "
            "check of 52 pairs flipped one per model.",
            "- **Slayer forward is a re-implementation** (`slayer_model.py`), not the harness forward. The METHOD.md "
            "runtime calibration (bitwise-equal logits, per-token difference bound) was not done. Against the "
            "official `load_slayer.py` model from the HF repo (CPU, batch 1) on the "
            f"{int(w[kf + '/zdania'])} sentences of the sha256 panel: mean |difference| "
            f"{zakres(w[kf + '/srednia_abs_roznica_ll/0'], w[kf + '/srednia_abs_roznica_ll/1'], 5)} and max "
            f"{zakres(w[kf + '/max_abs_roznica_ll/0'], w[kf + '/max_abs_roznica_ll/1'], 5)} in summed "
            f"log-likelihood per sentence, {int(w[kf + '/przestawione_pary'])} pairs changed their outcome in any "
            f"of the {len([k for k in w if k.startswith(kf + '/przebiegi/') and k.endswith('/watki_cpu')])} runs. The "
            "max is given as a range because it is float32 rounding and moves in its second digit with the "
            "number of CPU threads, with whether the unscored last token is fed, and with summing the token "
            "log-probs in float32 or float64 (the runs and versions are in `kontrola_forward.json`). The "
            "independent check's max, which differed from our earlier single value, is reproduced to all digits "
            "by one of these runs (all CPU threads, last token fed, float64 sum).",
            f"- {int(w['blimp/zbior/pary_identyczne'])} pairs of the dataset have identical good and bad sentences "
            "(passive_1, principle_A_case_2). lm-eval scores them as a tie, which counts as correct; we decide them "
            "from the text the same way, so batch noise cannot turn them into errors.",
            "- Contamination is not scanned here (no access to the Slayer training corpus). The Space flags BLiMP for "
            "Slayer 1.06 with hits on 3 of its 200 panel pairs; Pythia's Pile was not scanned either.",
            "- Pythia-1B uses the lm-eval HFLM pair encoding (the empty context is the tokenizer's BOS, else EOS; for "
            "Pythia both are `<|endoftext|>`); Slayer one BOS `<|endoftext|>` as in the Space METHOD.md: the "
            "'exactly one unscored prefix token' rule.", ""]


def ci_wilson(p, n=1000):
    z = 1.959963984540054
    m = 1 + z * z / n
    c = (p + z * z / (2 * n)) / m
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / m
    return c - h, c + h
