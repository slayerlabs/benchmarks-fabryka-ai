"""Jedno źródło liczb dla raportów: wyniki/LICZBY.json + wyniki/LICZBY.md z surowych wyników.

Czyta wyniki/raport_formatu.json, wygaszanie/wyniki/porownanie.json, wygaszanie/wyniki/heldout_*.json
i raporty benchmarków z BENCHMARKI (osobna pula wartości, bez porównań).
Każde porównanie dostaje różnicę, SE różnicy, z = różnica / SE i werdykt (|z| >= 3 „pewne”,
2-3 „prawdopodobne”, < 2 „szum”). SE parowane (to samo pytanie / to samo okno, dwa modele) jest
tylko tam, gdzie surowe wyniki per pytanie istnieją: wygaszanie (bootstrap z porownaj.py na plikach
z pelne_wyniki.tgz) i 1.00 -> 1.06 z test5 analizy formatu. Slayer vs Pythia nie ma wyników per
pytanie Pythii w repo, więc SE jest niezależne (hypot), czyli ostrożne.

Uruchom: python narzedzia/liczby.py   (bez argumentów; nadpisuje wyniki/LICZBY.json i LICZBY.md)
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
}
METRYKI = ("acc", "acc_norm", "bpb", "pmi")

# Benchmarki z własnym raportem wyników. Ich liczby trafiają do osobnej puli, sprawdzanej tylko w
# plikach z `pliki` i w liniach, które nazywają benchmark. `skala` 100 = raporty piszą wartości w %.
# GOTCHA: grupy (wg_*) i metryki poboczne pominięte: z nimi 90% liczb 40,0-80,0 pasowało do czegoś
# i bramka nie łapała pomyłek; raporty cytują je tylko jako liczby całkowite, których strażnik nie czyta.
BENCHMARKI = {
    "ewok": {"zrodlo": "wyniki_ewok/raport_ewok.json", "aliasy": ["EWoK"],
             "pliki": ["ewok_pl/", "wyniki_ewok/"], "skala": 100,
             "pomin": ("protokol", "do_przegladu", "n", "wg_Domain", "wg_ConceptA", "wg_ContextType",
                       "wg_ContextDiff", "wg_TargetDiff", "wg_flaga",
                       "kontekst_staly", "kontekst_staly_pmi", "staly_target", "margines")},
}


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
    """{nazwa: opis z BENCHMARKI + spłaszczone wartości jej raportu}."""
    out = {}
    for nazwa, b in BENCHMARKI.items():
        wartosci = {}
        splaszcz(json.loads((korzen / b["zrodlo"]).read_text()), nazwa, wartosci, b["pomin"])
        out[nazwa] = {k: v for k, v in b.items() if k != "pomin"} | {"wartosci": wartosci}
    return out


def zbuduj(korzen=KORZEN):
    raport = json.loads((korzen / "wyniki/raport_formatu.json").read_text())
    por = json.loads((korzen / "wygaszanie/wyniki/porownanie.json").read_text())
    wartosci = {}
    splaszcz(raport, "raport_formatu", wartosci)
    splaszcz(por, "porownanie", wartosci)
    heldouty = sorted((korzen / "wygaszanie/wyniki").glob("heldout_*.json"))
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
    zrodla = ["wyniki/raport_formatu.json", "wygaszanie/wyniki/porownanie.json"] + \
             [str(p.relative_to(korzen)) for p in heldouty]
    return {"zrodla": zrodla + [b["zrodlo"] for b in BENCHMARKI.values()],
            "benchmarki": benchmarki(korzen),
            "werdykt": {"pewne": f"|z| >= {PROG_PEWNE}", "prawdopodobne": f"{PROG_PRAWDOPODOBNE} <= |z| < {PROG_PEWNE}",
                        "szum": f"|z| < {PROG_PRAWDOPODOBNE}",
                        "uwaga": "werdykt główny z SE parowanego, gdy jest; inaczej z niezależnego (ostrożnego)"},
            "aliasy": ALIASY, "wartosci": wartosci, "porownania": porownania}


def pl(x, cyfr=4):
    if x is None:
        return "—"
    return f"{x:.{cyfr}f}".replace(".", ",").replace("-", "−")


def markdown(liczby):
    w = ["# Liczby raportów (wygenerowane, nie edytuj ręcznie)", "",
         "Źródło: `python narzedzia/liczby.py` z " + ", ".join(f"`{z}`" for z in liczby["zrodla"]) + ".",
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
    (KORZEN / "wyniki/LICZBY.json").write_text(json.dumps(liczby, ensure_ascii=False, indent=1) + "\n")
    (KORZEN / "wyniki/LICZBY.md").write_text(markdown(liczby))
    bench = ", ".join(f"{n}: {len(b['wartosci'])}" for n, b in liczby["benchmarki"].items())
    print(f"wyniki/LICZBY.json: {len(liczby['wartosci'])} wartości, {len(liczby['porownania'])} porównań; "
          f"benchmarki: {bench}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
