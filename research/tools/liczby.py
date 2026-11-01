"""Jedno źródło liczb dla raportów: results/LICZBY.json + results/LICZBY.md z surowych wyników.

Czyta analyses/answer-format/results/raport_formatu.json, slayer-1b/wygaszanie/wyniki/{porownanie,heldout_*}.json
i benchmarks/*/results/*.json (osobna pula wartości per benchmark, bez porównań).
Każde porównanie dostaje różnicę, SE różnicy, z = różnica / SE i werdykt (|z| >= 3 „pewne”,
2-3 „prawdopodobne”, < 2 „szum”). SE parowane (to samo pytanie / to samo okno, dwa modele) jest
tylko tam, gdzie surowe wyniki per pytanie istnieją: wygaszanie (bootstrap z porownaj.py na plikach
z pelne_wyniki.tgz) i 1.00 -> 1.06 z test5 analizy formatu. Slayer vs Pythia nie ma wyników per
pytanie Pythii w repo, więc SE jest niezależne (hypot), czyli ostrożne.

Uruchom: python tools/liczby.py   (bez argumentów; nadpisuje results/LICZBY.json i LICZBY.md)
"""
import json
import math
import sys
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent

PROG_PEWNE = 3.0
PROG_PRAWDOPODOBNE = 2.0
SILA = {"szum": 0, "prawdopodobne": 1, "pewne": 2}

# nazwy testów, pod którymi dokumenty je przywołują (do dopasowania słów werdyktu w sprawdz_raporty.py)
ALIASY = {
    "arc_e": ["ARC-E", "ARC Easy"],
    "arc_c": ["ARC-C"],
    "med": ["MedMCQA"],
    "siqa": ["SIQA", "Social IQa"],
    "belebele": ["Belebele"],
    "mmlu": ["MMLU"],
    "multiblimp": ["MultiBLiMP"],
    "pubmedqa": ["PubMedQA"],
    "blimp": ["BLiMP"],
}
METRYKI = ("acc", "acc_norm", "bpb", "pmi")
# tests whose numbers count only in a line that names the test (sprawdz_raporty.zbiory)
TYLKO_Z_NAZWA = ["blimp"]

# Każdy benchmarks/<nazwa>/results/*.json (bez podkatalogów per model) to osobna pula wartości,
# sprawdzana tylko w plikach benchmarks/<nazwa>/ i w liniach, które nazywają benchmark (aliasy).
# USTAWIENIA nadpisują domyślne: aliasy [nazwa], skala 1, pomin (). `skala` 100 = raporty piszą w %.
# GOTCHA: grupy (wg_*) i metryki poboczne EWoK pominięte: z nimi 90% liczb 40,0-80,0 pasowało do
# czegoś i bramka nie łapała pomyłek; raporty cytują je tylko jako liczby całkowite (strażnik ich nie czyta).
USTAWIENIA_BENCHMARKOW = {
    "ewok-pl": {"aliasy": ["EWoK"], "skala": 100,
                "pomin": ["protokol", "do_przegladu", "n", "wg_Domain", "wg_ConceptA", "wg_ContextType",
                          "wg_ContextDiff", "wg_TargetDiff", "wg_flaga",
                          "kontekst_staly", "kontekst_staly_pmi", "staly_target", "margines"]},
    # BLiMP: comparisons with SE and verdicts come from porownania_blimp (test "blimp"); the pool adds the
    # remaining values of blimp.json and kontrola_forward.json. Reports write 0.792 and "-2.87 pts".
    "blimp": {"aliasy": ["BLiMP"], "skala": 1,
              "pomin": ["porownanie", "okna", "per_grupa", "per_grupa_acc_norm", "paradygmaty", "pair_id", "sha256"]},
    # WikiText-2: denominator diagnosis (bajty.json, mianownik.json); the perplexities themselves live in the
    # global values (wygaszanie, raport_formatu), so `with_global` lets the benchmark files use them too.
    "wikitext-2": {"aliasy": ["WikiText"], "skala": 100, "with_global": True,
                   "pomin": ["per_doc_bajty_page_detok"]},
}
WYGASZANIE = "slayer-1b/wygaszanie/wyniki"
BLIMP = "benchmarks/blimp/results/blimp.json"
KRZYWA = "benchmarks/blimp/results/checkpoints.json"  # BLiMP over checkpoints and weight averaging
FORMAT = "analyses/answer-format/results/raport_formatu.json"
PIQA = "benchmarks/piqa/results/piqa.json"


def werdykt(z):
    """Werdykt z |z|: >= 3 pewne, 2-3 prawdopodobne, < 2 szum; None, gdy z nieznane."""
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return None
    a = abs(z)
    if a >= PROG_PEWNE:
        return "pewne"
    if a >= PROG_PRAWDOPODOBNE:
        return "prawdopodobne"
    return "szum"


def se_niezalezne(se_a, se_b):
    """SE różnicy dwóch niezależnych pomiarów (ostrożne, gdy pomiary są w parach)."""
    return math.hypot(se_a, se_b)


def rodzina_testu(zadanie):
    """'siqa_cloze' -> 'siqa', 'arc_c_mc_5shot' -> 'arc_c', 'multiblimp' -> 'multiblimp'."""
    for klucz in sorted(ALIASY, key=len, reverse=True):
        if zadanie == klucz or zadanie.startswith(klucz + "_"):
            return klucz
    return zadanie


def porownanie(pid, rodzina, zadanie, metryka, a, b, wa, sa, wb, sb, se_par=None, zrodlo_par=None, roznica=None):
    """Różnica a − b z SE niezależnym i (gdy jest) parowanym; werdykt główny z parowanego."""
    d = (wa - wb) if roznica is None else roznica
    p = {"id": pid, "rodzina": rodzina, "test": rodzina_testu(zadanie), "zadanie": zadanie,
         "metryka": metryka, "a": a, "b": b, "wartosc_a": wa, "se_a": sa, "wartosc_b": wb, "se_b": sb,
         "roznica": d, "roznica_pkt": d * 100}
    if sa is not None and sb is not None:
        s = se_niezalezne(sa, sb)
        p["se_niezalezne"] = s
        p["z_niezalezne"] = d / s if s > 0 else None
        p["werdykt_niezalezne"] = werdykt(p["z_niezalezne"])
    if se_par is not None:
        p["se_parowane"] = se_par
        p["z_parowane"] = d / se_par if se_par > 0 else None
        p["werdykt_parowane"] = werdykt(p["z_parowane"])
        p["zrodlo_parowania"] = zrodlo_par
        p["werdykt"], p["z"], p["se"] = p["werdykt_parowane"], p["z_parowane"], se_par
    else:
        p["werdykt"], p["z"], p["se"] = p.get("werdykt_niezalezne"), p.get("z_niezalezne"), p.get("se_niezalezne")
        p["adnotacja"] = "SE niezależne (hypot), ostrożne: brak wyników per pytanie obu modeli"
    return p


def splaszcz(obiekt, prefiks, wynik, pomin=("okna", "per_grupa", "per_grupa_acc_norm")):
    """Wszystkie liczby z drzewa JSON jako {ścieżka: wartość}; okna heldoutu i wyniki per przedmiot
    MMLU / grupa MultiBLiMP pominięte (raporty ich nie cytują, a 1450 wartości rozmywa dopasowanie)."""
    if isinstance(obiekt, bool):
        return
    if isinstance(obiekt, (int, float)):
        if not (isinstance(obiekt, float) and math.isnan(obiekt)):
            wynik[prefiks] = obiekt
        return
    if isinstance(obiekt, dict):
        for k, v in obiekt.items():
            if k in pomin:
                continue
            splaszcz(v, f"{prefiks}/{k}" if prefiks else str(k), wynik, pomin)
    elif isinstance(obiekt, list):
        for i, v in enumerate(obiekt):
            splaszcz(v, f"{prefiks}/{i}", wynik, pomin)


def udzialy_liter(zest, wynik):
    """Udział każdej litery w wyborach i w poprawnych odpowiedziach (dokumenty podają je w %)."""
    for model, testy in zest.items():
        for zadanie, t in testy.items():
            n = t.get("n")
            for pole in ("wybory_acc", "poprawne"):
                if n and isinstance(t.get(pole), dict):
                    for litera, ile in t[pole].items():
                        wynik[f"pochodne/udzial_{pole}/{model}/{zadanie}/{litera}"] = ile / n


def porownania_formatu(raport):
    zest = raport["zestawienie"]
    out = []
    # Slayer 1.06 vs Pythia-1B, każdy wspólny test i metryka
    for zadanie in sorted(set(zest["1.06"]) & set(zest["pythia-1b"])):
        for m in METRYKI:
            x, y = zest["1.06"][zadanie].get(m), zest["pythia-1b"][zadanie].get(m)
            if isinstance(x, dict) and isinstance(y, dict):
                out.append(porownanie(f"slayer_vs_pythia/{zadanie}/{m}", "slayer_vs_pythia", zadanie, m,
                                      "1.06", "pythia-1b", x["wartosc"], x["se"], y["wartosc"], y["se"]))
    # postęp wersji Slayera na ARC-C (niezależne SE; parowane dla 1.00 -> 1.06 z test5)
    t5 = raport.get("test5", {})
    par = {"acc_norm": t5.get("se_delta_acc_norm")}
    for a, b in (("1.06", "1.00"), ("1.06", "1.03"), ("1.03", "1.00")):
        for zadanie in sorted(set(zest[a]) & set(zest[b])):
            for m in METRYKI:
                x, y = zest[a][zadanie].get(m), zest[b][zadanie].get(m)
                if not (isinstance(x, dict) and isinstance(y, dict)):
                    continue
                se_p = par.get(m) if (a, b, zadanie) == ("1.06", "1.00", "arc_c_cloze") else None
                out.append(porownanie(f"wersje/{b}->{a}/{zadanie}/{m}", "wersje", zadanie, m, a, b,
                                      x["wartosc"], x["se"], y["wartosc"], y["se"], se_par=se_p,
                                      zrodlo_par="test5 analizy formatu (parowane po pytaniach)" if se_p else None))
    if t5:
        w = t5["wersje"]
        out.append(porownanie("wersje/1.00->1.06/arc_c_cloze/bpb_poprawnej", "wersje", "arc_c_cloze",
                              "bpb_poprawnej", "1.06", "1.00", w["1.06"]["bpb_poprawnej"], w["1.06"]["se"],
                              w["1.00"]["bpb_poprawnej"], w["1.00"]["se"], se_par=t5["se_delta_bpb"],
                              zrodlo_par="test5 analizy formatu (parowane po pytaniach)", roznica=t5["delta_bpb"]))
        out.append(porownanie("wersje/1.00->1.06/arc_c_cloze/margines_bpb", "wersje", "arc_c_cloze",
                              "margines_bpb", "1.06", "1.00", w["1.06"]["margines_bpb"], w["1.06"]["se_margines"],
                              w["1.00"]["margines_bpb"], w["1.00"]["se_margines"], se_par=t5["se_delta_margines"],
                              zrodlo_par="test5 analizy formatu (parowane po pytaniach)", roznica=t5["delta_margines"]))
    return out


def porownania_wygaszania(por):
    out = []
    zrodlo = "bootstrap po pytaniach, porownaj.py na pelne_wyniki.tgz"
    for zadanie, z in sorted(por["zadania"].items()):
        for m, r in z["metryki"].items():
            for a, b, kd, ks in (("A", "B", "delta_A_B", "se_delta_A_B"), ("A", "1.06", "delta_A_baza", "se_delta_A_baza"),
                                 ("B", "1.06", "delta_B_baza", "se_delta_B_baza")):
                out.append(porownanie(f"wygaszanie/{a}-{b}/{zadanie}/{m}", "wygaszanie", zadanie, m, a, b,
                                      r[a]["wartosc"], r[a]["se"], r[b]["wartosc"], r[b]["se"],
                                      se_par=r[ks], zrodlo_par=zrodlo, roznica=r[kd]))
    h = por["heldout"]
    zrodlo_h = "parowane po 1027 oknach heldoutu (porownaj.py)"
    out.append(porownanie("wygaszanie/A-B/heldout/loss", "wygaszanie", "heldout", "loss", "A", "B",
                          h["loss"]["A"], h["se"]["A"], h["loss"]["B"], h["se"]["B"],
                          se_par=h["se_delta_A_B"], zrodlo_par=zrodlo_h, roznica=h["delta_A_B"]))
    for x, klucz in (("A", "delta_A_baza"), ("B", "delta_B_baza")):
        d, s = h[klucz]
        out.append(porownanie(f"wygaszanie/{x}-1.06/heldout/loss", "wygaszanie", "heldout", "loss", x, "1.06",
                              h["loss"][x], h["se"][x], h["loss"]["1.06"], h["se"]["1.06"],
                              se_par=s, zrodlo_par=zrodlo_h, roznica=d))
    for a, b in (("1.06", "13800"), ("1.03", "1.06")):
        out.append(porownanie(f"wygaszanie/{a}-{b}/heldout/loss", "wygaszanie", "heldout", "loss", a, b,
                              h["loss"][a], h["se"][a], h["loss"][b], h["se"][b]))
    # różnice per komponent bez SE (brak per-okno SE komponentów): wartość bez werdyktu
    for x in ("A", "B"):
        for k in h["per_komponent"]["A"]:
            out.append(porownanie(f"wygaszanie/{x}-1.06/heldout_{k}/loss", "wygaszanie", "heldout", f"loss_{k}", x, "1.06",
                                  h["per_komponent"][x][k], None, h["per_komponent"]["1.06"][k], None))
    for k in h["per_komponent"]["A"]:
        out.append(porownanie(f"wygaszanie/A-B/heldout_{k}/loss", "wygaszanie", "heldout", f"loss_{k}", "A", "B",
                              h["per_komponent"]["A"][k], None, h["per_komponent"]["B"][k], None))
    return out


def benchmarki(korzen=KORZEN):
    """{nazwa: {zrodla, aliasy, pliki, skala, wartosci}} z benchmarks/<nazwa>/results/*.json."""
    out = {}
    for katalog in sorted((korzen / "benchmarks").iterdir()):
        raporty = sorted((katalog / "results").glob("*.json")) if katalog.is_dir() else []
        if not raporty:
            continue
        nazwa = katalog.name
        u = USTAWIENIA_BENCHMARKOW.get(nazwa, {})
        wartosci = {}
        for p in raporty:
            splaszcz(json.loads(p.read_text()), f"{nazwa}/{p.stem}", wartosci, tuple(u.get("pomin", ())))
        out[nazwa] = {"zrodla": [p.relative_to(korzen).as_posix() for p in raporty], "aliasy": u.get("aliasy", [nazwa]),
                      "pliki": [f"benchmarks/{nazwa}/"], "skala": u.get("skala", 1),
                      "with_global": u.get("with_global", False), "wartosci": wartosci}
    return out


def porownania_blimp(bl):
    """BLiMP full set, Slayer 1.06 vs Pythia-1B on the same 67 000 pairs: overall, 12 phenomena,
    67 paradigms; SE paired by pair (benchmarks/blimp/blimp.py porownanie_parowane)."""
    por, mod = bl["porownanie"], bl["modele"]
    a, b = por["a"], por["b"]
    zrodlo = "paired by minimal pair (benchmarks/blimp/blimp.py)"
    out = []

    def dodaj(zadanie, wa, sa, wb, sb, r):
        out.append(porownanie(f"slayer_vs_pythia/{zadanie}/acc", "slayer_vs_pythia", zadanie, "acc", a, b,
                              wa, sa, wb, sb, se_par=r["se"], zrodlo_par=zrodlo, roznica=r["roznica"]))

    dodaj("blimp", mod[a]["acc"], mod[a]["se"], mod[b]["acc"], mod[b]["se"], por["ogolem"])
    for z, r in por["zjawiska"].items():
        x, y = mod[a]["zjawiska"][z], mod[b]["zjawiska"][z]
        dodaj(f"blimp_zjawisko_{z}", x["acc"], x["se"], y["acc"], y["se"], r)
    for g, r in por["paradygmaty"].items():
        x, y = mod[a]["paradygmaty"][g], mod[b]["paradygmaty"][g]
        dodaj(f"blimp_{g}", x["acc"], x["se"], y["acc"], y["se"], r)
    an = bl.get("analiza")
    if not an:
        return out
    # paradigms as clusters: SE over the 67 paradigm differences (generalisation to paradigms)
    gen = an["generalizacja"]
    def klastr(p, df, p_t, wer):
        # a clustered t is read through the t distribution (df = k - 1), not as a z
        p.update({"df": df, "p_t": p_t, "werdykt": wer, "werdykt_parowane": wer})
        out.append(p)

    klastr(porownanie("slayer_vs_pythia/blimp_klastrowane/acc", "slayer_vs_pythia", "blimp_klastrowane", "acc", a, b,
                      None, None, None, None, se_par=gen["se_klastrowe"],
                      zrodlo_par=f"clustered by paradigm (k = {gen['k']})", roznica=gen["roznica"]),
           gen["df"], gen["p_t"], gen["werdykt_klastrowy"])
    b2 = gen["bez_2_najgorszych"]
    klastr(porownanie("slayer_vs_pythia/blimp_klastrowane_bez_2/acc", "slayer_vs_pythia", "blimp_klastrowane_bez_2",
                      "acc", a, b, None, None, None, None, se_par=b2["se"],
                      zrodlo_par="clustered by paradigm, 2 lowest paradigms dropped", roznica=b2["roznica"]),
           b2["df"], b2["p_t"], b2["werdykt"])
    for z, r in an["zjawiska_klastrowe"].items():
        klastr(porownanie(f"slayer_vs_pythia/blimp_zjawisko_klastr_{z}/acc", "slayer_vs_pythia", f"blimp_zjawisko_klastr_{z}",
                          "acc", a, b, None, None, None, None, se_par=r["se"],
                          zrodlo_par=f"clustered by paradigm (k = {r['k']})", roznica=r["roznica"]),
               r["df"], r["p_t"], r["werdykt"])  # k < 3: "nierozstrzygalne", whatever t says
    worek = an["ten_sam_worek_slow"]
    for df, strony in worek.get("wrazliwosc", {}).items():  # three readings of "same words"
        for s, r in strony.items():
            out.append(porownanie(f"slayer_vs_pythia/blimp_worek_{df}_{s}/acc", "slayer_vs_pythia",
                                  f"blimp_worek_{df}_{s}", "acc", a, b, None, None, None, None, se_par=r["se"],
                                  zrodlo_par="paired by minimal pair, stratified by paradigm", roznica=r["roznica"]))
    for nazwa, r in (("blimp_ten_sam_worek_slow_klastr", worek["tak"]), ("blimp_inny_worek_slow_klastr", worek["nie"])):
        klastr(porownanie(f"slayer_vs_pythia/{nazwa}/acc", "slayer_vs_pythia", nazwa, "acc", a, b, None, None, None, None,
                          se_par=r["se_paradygmatow"], zrodlo_par=f"clustered by paradigm (k = {r['k_paradygmatow']})",
                          roznica=r["srednia_paradygmatow"]),
               r["df_paradygmatow"], r["p_t_paradygmatow"], r["werdykt_paradygmatow"])
    for nazwa, r in (("blimp_na_token", an["na_token"]),
                     ("blimp_ta_sama_tokenizacja", an["tokenizacja"]["ta_sama_roznica_tokenow"]),
                     ("blimp_rozna_tokenizacja", an["tokenizacja"]["rozna_roznica_tokenow"]),
                     ("blimp_ten_sam_worek_slow", worek["tak"]),
                     ("blimp_inny_worek_slow", worek["nie"])):
        out.append(porownanie(f"slayer_vs_pythia/{nazwa}/acc", "slayer_vs_pythia", nazwa, "acc", a, b, None, None, None, None,
                              se_par=r["se"], zrodlo_par="paired by minimal pair, stratified by paradigm", roznica=r["roznica"]))
    return out


def porownania_krzywej(kr):
    """BLiMP over checkpoints and weight averages (benchmarks/blimp/checkpoints.py, CHECKPOINTS_THRESHOLDS.md):
    gap of every checkpoint to Pythia-1B, slopes, step changes, averages vs 1.06; pair SE and clustered t."""
    out = []
    par = "paired by minimal pair, stratified by paradigm"

    def dodaj(pid, rodzina, zadanie, a, b, r, metryka="acc", se_key="se", zrodlo=par):
        out.append(porownanie(pid, rodzina, zadanie, metryka, a, b, None, None, None, None,
                              se_par=r[se_key], zrodlo_par=zrodlo, roznica=r.get("roznica", r.get("nachylenie"))))

    def klastr(pid, rodzina, zadanie, a, b, r):
        if r.get("se_klastr") is None:
            return
        p = porownanie(pid, rodzina, zadanie, "acc", a, b, None, None, None, None, se_par=r["se_klastr"],
                       zrodlo_par=f"clustered by paradigm (k = {r['k']})", roznica=r.get("roznica", r.get("nachylenie")))
        w = r["werdykt_klastr"]
        p.update({"df": r["df"], "p_t": r["p_klastr"], "werdykt": w, "werdykt_parowane": w})
        out.append(p)

    for pt in kr.get("punkty", []):
        e = pt["etykieta"]
        dodaj(f"{e}_vs_pythia/blimp_krzywa_luka/acc", "slayer_ckpt_vs_pythia", f"blimp_krzywa_luka_{e}", e, "pythia-1b",
              pt["luka_pythia"])
    if "nachylenie" in kr:
        n = kr["nachylenie"]
        dodaj("krzywa/blimp_krzywa_nachylenie/acc", "slayer_krzywa", "blimp_krzywa_nachylenie", "slope", "0", n,
              metryka="acc_per_bn_tokens", zrodlo="bootstrap of pairs within paradigms, shared across checkpoints")
        klastr("krzywa/blimp_krzywa_nachylenie_klastr/acc", "slayer_krzywa", "blimp_krzywa_nachylenie_klastr", "slope", "0", n)
        for z, r in kr["nachylenie_zjawiska"].items():
            dodaj(f"krzywa/blimp_krzywa_nachylenie_{z}/acc", "slayer_krzywa", f"blimp_krzywa_nachylenie_{z}", "slope", "0", r,
                  metryka="acc_per_bn_tokens", zrodlo="bootstrap of pairs within paradigms, shared across checkpoints")
            klastr(f"krzywa/blimp_krzywa_nachylenie_klastr_{z}/acc", "slayer_krzywa", f"blimp_krzywa_nachylenie_klastr_{z}",
                   "slope", "0", r)
        for r in kr["kroki"]:
            a, b = f"k{r['do']}", f"k{r['od']}"
            dodaj(f"{a}_vs_{b}/blimp_krzywa_krok/acc", "slayer_krzywa", f"blimp_krzywa_krok_{r['od']}_{r['do']}", a, b, r)
            klastr(f"{a}_vs_{b}/blimp_krzywa_krok_klastr/acc", "slayer_krzywa", f"blimp_krzywa_krok_klastr_{r['od']}_{r['do']}",
                   a, b, r)
    if "nachylenie_bez_ostatniego" in kr:
        n = kr["nachylenie_bez_ostatniego"]
        dodaj("krzywa/blimp_krzywa_nachylenie_bez_ostatniego/acc", "slayer_krzywa", "blimp_krzywa_nachylenie_bez_ostatniego",
              "slope", "0", n, metryka="acc_per_bn_tokens", zrodlo="bootstrap of pairs within paradigms, shared across checkpoints")
        klastr("krzywa/blimp_krzywa_nachylenie_bez_ostatniego_klastr/acc", "slayer_krzywa",
               "blimp_krzywa_nachylenie_bez_ostatniego_klastr", "slope", "0", n)

    def reszty(pid, zadanie, n):
        if not n or n.get("se_reszty") is None:
            return
        p = porownanie(pid, "slayer_krzywa", zadanie, "acc_per_bn_tokens", "slope", "0", None, None, None, None,
                       se_par=n["se_reszty"],
                       zrodlo_par=f"residuals of the checkpoint accuracies around the line (df = {n['df']})",
                       roznica=n["nachylenie"])
        p.update({"df": n["df"], "p_t": n["p"], "werdykt": n["werdykt"], "werdykt_parowane": n["werdykt"]})
        out.append(p)

    reszty("krzywa/blimp_krzywa_nachylenie_reszty/acc", "blimp_krzywa_nachylenie_reszty", kr.get("nachylenie_reszty"))
    for z, r in kr.get("nachylenie_zjawiska", {}).items():
        reszty(f"krzywa/blimp_krzywa_nachylenie_reszty_{z}/acc", f"blimp_krzywa_nachylenie_reszty_{z}", r.get("reszty"))
    if "nachylenie_ln_D" in kr:
        n = kr["nachylenie_ln_D"]
        dodaj("krzywa/blimp_krzywa_nachylenie_lnD/acc", "slayer_krzywa", "blimp_krzywa_nachylenie_lnD", "slope", "0", n,
              metryka="acc_per_ln_tokens", zrodlo="bootstrap of pairs within paradigms, shared across checkpoints")
        klastr("krzywa/blimp_krzywa_nachylenie_lnD_klastr/acc", "slayer_krzywa", "blimp_krzywa_nachylenie_lnD_klastr",
               "slope", "0", n)
    for e, r in kr.get("srednie", {}).items():
        dodaj(f"{e}_vs_k13848/blimp_srednia/acc", "srednia_vs_1.06", f"blimp_srednia_{e}", e, "k13848", r["blimp"])
        klastr(f"{e}_vs_k13848/blimp_srednia_klastr/acc", "srednia_vs_1.06", f"blimp_srednia_klastr_{e}", e, "k13848", r["blimp"])
        for z, rz in r["blimp_zjawiska"].items():
            dodaj(f"{e}_vs_k13848/blimp_srednia_{z}/acc", "srednia_vs_1.06", f"blimp_srednia_{e}_{z}", e, "k13848", rz)
            if "se_klastr" in rz:
                klastr(f"{e}_vs_k13848/blimp_srednia_klastr_{z}/acc", "srednia_vs_1.06", f"blimp_srednia_klastr_{e}_{z}",
                       e, "k13848", rz)
    for e, r in kr.get("heldout", {}).get("srednie", {}).items():
        dodaj(f"{e}_vs_1.06/heldout_srednia/loss", "srednia_vs_1.06", f"heldout_srednia_{e}", e, "1.06", r, metryka="loss",
              zrodlo="paired by held-out window")
        if "vs_wygaszanie" in r:
            dodaj(f"{e}_vs_A/heldout_srednia_vs_wygaszanie/loss", "srednia_vs_wygaszanie", f"heldout_srednia_vs_A_{e}", e,
                  "A", r["vs_wygaszanie"], metryka="loss", zrodlo="paired by held-out window")
    return out


def raporty_krzywej(kr):
    """Metadata of CHECKPOINTS.md for the gates of sprawdz_raporty.py: generated report (g), clustered verdicts (d),
    phenomena with < 3 paradigms undetermined in the clustered column (e)."""
    if "nachylenie" not in kr:
        return []
    return [{"plik": "benchmarks/blimp/results/CHECKPOINTS.md", "test": "blimp", "wieloparadygmatowy": True,
             "k_paradygmatow": 0, "porownanie_klastrowe": "krzywa/blimp_krzywa_nachylenie_klastr/acc", "holm": {},
             "grupy": [{"nazwa": z, "etykieta": z.replace("_", " "), "k": r["k"],
                        "werdykt": r["werdykt_klastr"] if r["k"] >= 3 else "nierozstrzygalne"}
                       for z, r in kr["nachylenie_zjawiska"].items()],
             "kolumna_werdyktu_klastrowego": "verdict paradigms",
             "generator": {"modul": "benchmarks/blimp/checkpoints_report.py", "funkcja": "pliki",
                           "wejscie": KRZYWA, "komenda": "python benchmarks/blimp/checkpoints.py raport"}}]


def raporty_blimp(bl):
    """Metadata of the BLiMP report for the gates of sprawdz_raporty.py (bramki_raportu)."""
    an = bl.get("analiza")
    if not an:
        return []
    return [{"plik": "benchmarks/blimp/results/BLIMP.md", "test": "blimp", "wieloparadygmatowy": True,
             "k_paradygmatow": an["generalizacja"]["k"],
             "porownanie_klastrowe": "slayer_vs_pythia/blimp_klastrowane/acc",
             "holm": {g: r["holm"] for g, r in an["paradygmaty_dodatkowe"].items()},
             "grupy": [{"nazwa": z, "etykieta": z.replace("_", " "), "k": r["k"], "werdykt": r["werdykt"]}
                       for z, r in an["zjawiska_klastrowe"].items()],
             # the k < 3 rule binds only the paradigm-level (clustered) column of a group row; the pair-level
             # verdict next to it is a claim about the pairs, valid at any k
             "kolumna_werdyktu_klastrowego": "verdict paradigms",
             # the report must equal, byte for byte, what this generator writes from LICZBY.json + blimp.json
             "generator": {"modul": "benchmarks/blimp/blimp_raport.py", "funkcja": "pliki",
                           "wejscie": BLIMP, "komenda": "python benchmarks/blimp/blimp.py raport"},
             "tokenizery": bl.get("tokenizery_sha256", {}),
             "porownanie_na_token": "slayer_vs_pythia/blimp_na_token/acc"}]


def raporty_piqa(korzen):
    """PIQA.md for gate (g): the report must equal what benchmarks/piqa/piqa.py renders from piqa.json."""
    if not (korzen / PIQA).exists():
        return []
    return [{"plik": "benchmarks/piqa/results/PIQA.md", "test": "piqa", "wieloparadygmatowy": False, "grupy": [],
             "generator": {"modul": "benchmarks/piqa/piqa.py", "funkcja": "pliki", "wejscie": PIQA,
                           "komenda": "python benchmarks/piqa/piqa.py report"}}]


def zbuduj(korzen=KORZEN):
    raport = json.loads((korzen / FORMAT).read_text())
    por = json.loads((korzen / WYGASZANIE / "porownanie.json").read_text())
    wartosci = {}
    splaszcz(raport, "raport_formatu", wartosci)
    splaszcz(por, "porownanie", wartosci)
    heldouty = sorted((korzen / WYGASZANIE).glob("heldout_*.json"))
    for p in heldouty:
        splaszcz(json.loads(p.read_text()), p.stem, wartosci)
    udzialy_liter(raport["zestawienie"], wartosci)
    wk = raport.get("slayer_wikitext_kontrola", {})
    if "byte_perplexity" in wk and "space_1.06_byte_ppl" in wk:
        wartosci["pochodne/wikitext_nasz_do_space"] = wk["byte_perplexity"] / wk["space_1.06_byte_ppl"] - 1
    h = por["heldout"]
    wartosci["pochodne/3xZ1_103_106"] = 3 * h["Z1_103_106"]
    wartosci["pochodne/3xZ2_13800_13848"] = 3 * h["Z2_13800_13848"]
    porownania = porownania_formatu(raport) + porownania_wygaszania(por)
    zrodla = [FORMAT, f"{WYGASZANIE}/porownanie.json"] + \
             [p.relative_to(korzen).as_posix() for p in heldouty]
    plik_blimp = korzen / BLIMP
    raporty = []  # reports with metadata for the gates of sprawdz_raporty.py (older reports have none)
    if plik_blimp.exists():
        bl = json.loads(plik_blimp.read_text())
        # per-paradigm values live in `porownania` (with SE and verdict), not twice in `wartosci`
        splaszcz({k: v for k, v in bl.items() if k != "porownanie"}, "blimp", wartosci,
                 pomin=("okna", "per_grupa", "per_grupa_acc_norm", "paradygmaty"))
        porownania += porownania_blimp(bl)
        raporty += raporty_blimp(bl)
    plik_krzywej = korzen / KRZYWA
    if plik_krzywej.exists():
        kr = json.loads(plik_krzywej.read_text())
        splaszcz(kr, "blimp_krzywa", wartosci, pomin=("paradygmaty",))
        porownania += porownania_krzywej(kr)
        raporty += raporty_krzywej(kr)
    raporty += raporty_piqa(korzen)
    bench = benchmarki(korzen)
    return {"zrodla": zrodla + [z for b in bench.values() for z in b["zrodla"]],
            "benchmarki": bench, "raporty": raporty,
            "werdykt": {"pewne": f"|z| >= {PROG_PEWNE}", "prawdopodobne": f"{PROG_PRAWDOPODOBNE} <= |z| < {PROG_PEWNE}",
                        "szum": f"|z| < {PROG_PRAWDOPODOBNE}",
                        "uwaga": "werdykt główny z SE parowanego, gdy jest; inaczej z niezależnego (ostrożnego)"},
            "aliasy": ALIASY, "tylko_z_nazwa": TYLKO_Z_NAZWA, "wartosci": wartosci, "porownania": porownania}


def pl(x, cyfr=4):
    if x is None:
        return "—"
    return f"{x:.{cyfr}f}".replace(".", ",").replace("-", "−")


def markdown(liczby):
    w = ["# Liczby raportów (wygenerowane, nie edytuj ręcznie)", "",
         "Źródło: `python tools/liczby.py` z " + ", ".join(f"`{z}`" for z in liczby["zrodla"]) + ".",
         "Werdykt z |z|: ≥ 3 pewne, 2–3 prawdopodobne, < 2 szum. SE parowane tylko tam, gdzie są wyniki per pytanie;",
         "Slayer vs Pythia ma SE niezależne (hypot), czyli ostrożne.", ""]
    grupy = [("Slayer 1.06 vs Pythia-1B", "slayer_vs_pythia"), ("Wersje Slayera", "wersje"), ("Wygaszanie LR", "wygaszanie")]
    for tytul, rodzina in grupy:
        w += [f"## {tytul}", "",
              "| porównanie | a | b | różnica (pkt) | SE niezal. | z niezal. | SE parow. | z parow. | werdykt |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---|"]
        for p in liczby["porownania"]:
            if p["rodzina"] != rodzina:
                continue
            w.append(f"| {p['id'].split('/', 1)[1]} | {pl(p['wartosc_a'])} | {pl(p['wartosc_b'])} | "
                     f"{pl(p['roznica'])} ({pl(p['roznica_pkt'], 1)}) | {pl(p.get('se_niezalezne'))} | "
                     f"{pl(p.get('z_niezalezne'), 1)} | {pl(p.get('se_parowane'))} | {pl(p.get('z_parowane'), 1)} | "
                     f"{p.get('werdykt') or '—'} |")
        w.append("")
    return "\n".join(w)


def main(argv=None):
    liczby = zbuduj()
    (KORZEN / "results/LICZBY.json").write_text(json.dumps(liczby, ensure_ascii=False, indent=1) + "\n")
    (KORZEN / "results/LICZBY.md").write_text(markdown(liczby))
    bench = ", ".join(f"{n}: {len(b['wartosci'])}" for n, b in liczby["benchmarki"].items())
    print(f"results/LICZBY.json: {len(liczby['wartosci'])} wartości, {len(liczby['porownania'])} porównań; "
          f"benchmarki: {bench}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
