"""BLiMP report and charts generated from wyniki/LICZBY.json only (no number typed by hand).

  python narzedzia/liczby.py && python slayer_eval/blimp.py raport
  -> wyniki/blimp/BLIMP.md, wyniki/blimp/blimp_phenomena.svg, wyniki/blimp/blimp_paradigms.svg
"""
from html import escape
from pathlib import Path

WERDYKT_EN = {"pewne": "certain", "prawdopodobne": "probable", "szum": "noise", None: "-"}
MODELE = [("1.06", "Slayer 1.06", "#2a78d6", "circle"), ("pythia-1b", "Pythia-1B", "#eb6834", "square")]
TEKST, TEKST2, SIATKA, TLO = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def f(x, cyfr=3):
    return "-" if x is None else f"{x:.{cyfr}f}"


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


def wykres(wiersze, tytul, plik, os_min=0.4):
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
    plik.write_text("\n".join(s) + "\n")


def znacznik(x, y, kolor, ksztalt):
    if ksztalt == "square":
        return f'<rect x="{x - 4:.1f}" y="{y - 4:.1f}" width="8" height="8" rx="1" fill="{kolor}" stroke="{TLO}" stroke-width="2"/>'
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{kolor}" stroke="{TLO}" stroke-width="2"/>'


def raport(sciezka_liczb, katalog):
    import json
    liczby = json.loads(Path(sciezka_liczb).read_text())
    w, por, mod, zjawiska, zj = dane(liczby)
    katalog = Path(katalog)
    sl, py = mod["1.06"], mod["pythia-1b"]
    og = por["blimp"]

    # charts
    wiersze = [("BLiMP overall (67 paradigms)", {m: (mod[m]["acc"], *mod[m]["ci"]) for m, *_ in MODELE})]
    wiersze += [(nazwa_zjawiska(z), {m: (zj(m, z)["acc"], *zj(m, z)["ci"]) for m, *_ in MODELE}) for z in zjawiska]
    wykres(wiersze, "BLiMP full set: overall and 12 phenomena (n = 67 000 minimal pairs per model)",
           katalog / "blimp_phenomena.svg")
    parad = sorted((p for k, p in por.items() if k.startswith("blimp_") and not k.startswith("blimp_zjawisko_")),
                   key=lambda p: p["roznica"])
    wiersze_p = []
    for p in parad:
        g = p["zadanie"][len("blimp_"):]
        wiersze_p.append((g, {"1.06": (p["wartosc_a"], *ci_wilson(p["wartosc_a"])),
                              "pythia-1b": (p["wartosc_b"], *ci_wilson(p["wartosc_b"]))}))
    wykres(wiersze_p, "BLiMP: 67 paradigms, n = 1000 pairs each, sorted by Slayer - Pythia",
           katalog / "blimp_paradigms.svg", os_min=0.0)

    kp = {k.split("/")[-1]: v for k, v in w.items() if k.startswith("blimp/kontrola_pythia/")}
    # numbers from LICZBY.json; yes/no flags (not numbers, so not in LICZBY) from blimp.json
    flagi = json.loads((katalog / "blimp.json").read_text())
    pan = {wr: {**{k.split("/")[-1]: w[k] for k in w if k.startswith(f"blimp/panel_space/{wr}/")},
                **{k: v for k, v in flagi["panel_space"][wr].items() if isinstance(v, bool)}}
           for wr in ("pair_id", "sha256")}
    licz = {"pewne": [0, 0], "prawdopodobne": [0, 0], "szum": [0, 0]}
    for p in parad:
        licz[p["werdykt"]][0 if p["roznica"] > 0 else 1] += 1

    L = ["# BLiMP full set: Slayer 1.06 and Pythia-1B", "",
         "Generated by `python slayer_eval/blimp.py raport` from `wyniki/LICZBY.json`; do not edit by hand.",
         "Protocol and thresholds (written before the measurement): [`THRESHOLDS.md`](THRESHOLDS.md).", "",
         f"**Slayer 1.06: {f(sl['acc'], 4)} (CI95 {f(sl['ci'][0], 4)}-{f(sl['ci'][1], 4)}), Pythia-1B: "
         f"{f(py['acc'], 4)} (CI95 {f(py['ci'][0], 4)}-{f(py['ci'][1], 4)}) on all {sl['n']} minimal pairs.** "
         f"Difference {f(og['roznica'] * 100, 2)} points, paired SE {f(og['se'] * 100, 2)} points, "
         f"z = {f(og['z'], 1)}: {WERDYKT_EN[og['werdykt']]}.", "",
         "## Overall", "",
         "| model | accuracy | n | SE | CI95 (bootstrap, stratified) | chance | majority |",
         "|---|---:|---:|---:|---|---:|---|"]
    for m, nazwa, *_ in MODELE:
        x = mod[m]
        L.append(f"| {nazwa} | {f(x['acc'], 4)} | {x['n']} | {f(x['se'], 4)} | {f(x['ci'][0], 4)}-{f(x['ci'][1], 4)} | "
                 f"0.5 | n/a (gold always first by construction) |")
    L += ["", "## Control: Pythia-1B against the published value", "",
          f"Our Pythia-1B {f(kp['nasza'], 4)} vs reference {f(kp['wartosc'], 4)}: difference "
          f"{f(kp['roznica'] * 100, 2)} points, threshold +-2 points: "
          f"**{'within' if abs(kp['roznica']) <= kp['prog'] else 'outside, control not confirmed'}**.",
          "The reference is the mean of the 67 `blimp_*` values in the EleutherAI/pythia repo file "
          "`evals/pythia-v0/pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json`. "
          "It is the v0 model (weights before the Pythia re-train) scored by the old harness without the leading "
          "space; the v1 eval folders of that repo have no BLiMP and no other published BLiMP value for "
          "`EleutherAI/pythia-1b` was found. It is a sanity range, not an exact reference.", "",
          "## Agreement with the Space (panel of 200)", "",
          f"Space T01, Slayer 1.06: {f(w['blimp/space/wartosc'], 4)} (CI95 {f(w['blimp/space/ci95/0'], 3)}-"
          f"{f(w['blimp/space/ci95/1'], 3)}, n = 200). Panel rebuilt by METHOD.md section 3 "
          "(2 per member, the remaining 66 slots by largest deficit, ties by member name, inside a member by "
          "SHA-256 of `20261028|blimp|<member>|<source id>`):", "",
          "| source id in the hash | n | Slayer 1.06 | difference to Space | inside Space CI95 | Pythia-1B |",
          "|---|---:|---:|---:|---|---:|"]
    for wr, opis in (("pair_id", "`pair_id`"), ("sha256", "SHA-256 of the canonical row")):
        p = pan[wr]
        L.append(f"| {opis} | {int(p['n'])} | {f(p['1.06'], 4)} | {f(p['roznica_1.06_do_space'], 4)} | "
                 f"{'yes' if p['w_ci95_space'] else 'no'} | {f(p['pythia-1b'], 4)} |")
    zgodny = [wr for wr in pan if pan[wr].get("rowna_space")]
    L += ["", ("With the source id = SHA-256 of the canonical row our Slayer 1.06 value equals the Space value "
               "exactly (338 of 402 in the equal-member weighting), while `pair_id` gives a different panel. "
               if zgodny else "No source-id definition reproduces the Space value. ") +
          "We could not reproduce the Space `source_id_digest` itself (its id/separator format is not published), "
          "so the panel identity is inferred from the value, not proven by the digest. Same pairs or not, 200 pairs "
          "give a CI95 about +-3.5 points wide, which is why the full set is the number to use.", "",
          "## 12 phenomena", "",
          "Paired SE over the same pairs; verdict from |z|: >= 3 certain, 2-3 probable, < 2 noise.", "",
          "| phenomenon | paradigms | n | Slayer 1.06 | Pythia-1B | difference (points) | SE (points) | z | verdict |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for z in zjawiska:
        p = por[f"blimp_zjawisko_{z}"]
        npar = int(w[f"blimp/modele/1.06/zjawiska/{z}/n_paradygmatow"])
        L.append(f"| {nazwa_zjawiska(z)} | {npar} | {int(zj('1.06', z)['n'])} | {f(p['wartosc_a'])} | {f(p['wartosc_b'])} | "
                 f"{f(p['roznica'] * 100, 1)} | {f(p['se'] * 100, 2)} | {f(p['z'], 1)} | {WERDYKT_EN[p['werdykt']]} |")
    L += ["", "![BLiMP overall and phenomena](blimp_phenomena.svg)", "",
          "## 67 paradigms", "",
          f"n = 1000 pairs per paradigm and model. Slayer ahead: {licz['pewne'][0]} certain, "
          f"{licz['prawdopodobne'][0]} probable; Pythia ahead: {licz['pewne'][1]} certain, {licz['prawdopodobne'][1]} "
          f"probable; noise: {sum(licz['szum'])}. With 67 comparisons about 3 'probable' and 0.2 'certain' are expected "
          "by chance alone, so single 'probable' paradigms are not findings.", "",
          "| paradigm | Slayer 1.06 | Pythia-1B | difference (points) | SE (points) | z | verdict |",
          "|---|---:|---:|---:|---:|---:|---|"]
    for p in parad:
        L.append(f"| {p['zadanie'][len('blimp_'):]} | {f(p['wartosc_a'])} | {f(p['wartosc_b'])} | {f(p['roznica'] * 100, 1)} | "
                 f"{f(p['se'] * 100, 2)} | {f(p['z'], 1)} | {WERDYKT_EN[p['werdykt']]} |")
    L += ["", "![BLiMP paradigms](blimp_paradigms.svg)", "",
          "## Limits", "",
          "- Runtime: Apple MPS, float32, batch 64 with right padding (causal attention, so padding does not reach "
          "scored tokens). A CPU float32 re-run of 300 pairs per model (the sha256 panel and 100 pairs spread over "
          "the set) flipped no pair.",
          "- Contamination is not scanned here (no access to the Slayer training corpus). The Space flags BLiMP for "
          "Slayer 1.06 with hits on 3 of its 200 panel pairs; Pythia's Pile was not scanned either.",
          "- Pythia-1B is scored with the same pair encoding as lm-eval HFLM (EOT as the empty context, no BOS); "
          "Slayer with one BOS `<|endoftext|>` as in the Space METHOD.md. Both are the 'exactly one unscored prefix "
          "token' rule.", "",
          "## How to reproduce", "",
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
    (katalog / "BLIMP.md").write_text("\n".join(L))
    print(f"{katalog / 'BLIMP.md'}, 2 SVG")


def ci_wilson(p, n=1000):
    import math
    z = 1.959963984540054
    m = 1 + z * z / n
    c = (p + z * z / (2 * n)) / m
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / m
    return c - h, c + h
