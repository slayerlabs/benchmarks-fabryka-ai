"""WSC273 (T14): the Space protocol through lm-eval, plus the control model.

Subcommands: `panel` freezes the sample, `evaluate` runs one model, `report` builds results/wsc273.json.
Rules and thresholds: PROTOCOL-space.md.
"""
import argparse
import gzip
import hashlib
import itertools
import json
import os
import pathlib
import statistics
import sys

KATALOG = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(KATALOG.parents[1] / "common"))
sys.path.insert(0, str(KATALOG.parents[1] / "tools"))
from statystyka import p_z, po_holmie, se_k, werdykt, wobec_stalej  # noqa: E402

from metryki import bazy_mc, ranking_panel, srednia_z_niepewnoscia  # noqa: E402

ZADANIE = "wsc273"
ZADANIA = KATALOG / "lm_eval_tasks"
PANEL = KATALOG / "panel200.json"
WYNIKI = KATALOG / "results"
RAPORT = WYNIKI / "wsc273.json"
ROZMIAR_PANELU = 200
LICZBA_DOK = 273
PROG_ZGODNOSCI = 1e-3
MODELE = {"slayer-1.06": "slayer", "bloom-560m": "hf"}
KONTROLA = {"model": "bigscience/bloom-560m", "wartosc": 0.6666666666666666, "se": 0.028583097523751506, "n": 273}
PROG_KONTROLI = (0.6095, 0.7238)
POLA_TRESCI = ("text", "pronoun", "pronoun_loc", "options", "label")


def kanoniczny(doc):
    return json.dumps(doc, sort_keys=True, ensure_ascii=False)


def id_dokumentu(doc):
    return hashlib.sha256(kanoniczny(doc).encode("utf-8")).hexdigest()


def tozsamosci(dokumenty):
    """Document ids in input order; byte-identical documents get an ordinal (METHOD section 3)."""
    widziane, wynik = {}, []
    for doc in dokumenty:
        baza = id_dokumentu(doc)
        ile = widziane.get(baza, 0)
        widziane[baza] = ile + 1
        wynik.append(baza if ile == 0 else f"{baza}#{ile}")
    return wynik


def zadanie():
    # lm-eval 0.4.9.1 loses the `task` key when tasks come as a dict (common/ewaluuj.py does the same).
    from lm_eval.tasks import TaskManager, get_task_dict
    obiekt = get_task_dict([ZADANIE], TaskManager(include_path=str(ZADANIA), include_defaults=False))[ZADANIE]
    obiekt.config.task = ZADANIE
    return obiekt


def dokumenty_surowe(obiekt):
    """Rows before process_docs, for the sensitivity variant of the document identity."""
    return [dict(d) for d in obiekt.dataset["test"]]


def dokumenty(obiekt):
    return [dict(d) for d in obiekt.test_docs()]


def panel_z(identyfikatory, rozmiar=ROZMIAR_PANELU):
    return ranking_panel(ZADANIE, ZADANIE, identyfikatory, n=rozmiar)


def cmd_panel(_):
    docs = dokumenty(zadanie())
    assert len(docs) == LICZBA_DOK, len(docs)
    ids = tozsamosci(docs)
    PANEL.write_text(json.dumps({
        "benchmark_id": ZADANIE, "member_task": ZADANIE,
        "tozsamosc": "sha256(json.dumps(doc po process_docs, sort_keys=True, ensure_ascii=False))",
        "n_splitu": len(ids), "indeksy": panel_z(ids),
        "sha256_listy_id": hashlib.sha256("\n".join(ids).encode()).hexdigest(),
    }, indent=1) + "\n", encoding="utf-8", newline="\n")


def najdluzsze_zadanie(obiekt, tok):
    """Longest context + continuation in tokens; the protocol allows no truncation."""
    return max(len(tok(r.args[0] + r.args[1])["input_ids"]) for r in obiekt.instances)


def wiersze(zadane):
    wynik = []
    for s in zadane:
        logliki = [float(r[0]) for r in s["filtered_resps"]]
        wynik.append({"k": s["doc_id"], "id": id_dokumentu(s["doc"]), "gold": int(s["doc"]["label"]), "logliki": logliki,
                      "pred": max(range(len(logliki)), key=logliki.__getitem__), "acc": float(s["acc"])})
    return sorted(wynik, key=lambda w: w["k"])


def cmd_evaluate(a):
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    from lm_eval import simple_evaluate
    if MODELE[a.model] == "slayer":
        import slayer_lm
        lm = slayer_lm.SlayerLM(pretrained=a.model_path, dtype="float32", batch_size=1, device=a.device)
    else:
        from lm_eval.models.huggingface import HFLM
        lm = HFLM(pretrained=a.model_path, revision=None, dtype="float32", batch_size=1, device=a.device)
    obiekt = zadanie()
    indeksy = json.loads(PANEL.read_text(encoding="utf-8"))["indeksy"]
    if a.limit:
        probka = {ZADANIE: list(range(a.limit))}
    else:
        probka = {ZADANIE: indeksy} if a.sample == "panel200" else None
    wynik = simple_evaluate(model=lm, tasks=[obiekt], samples=probka, log_samples=True, bootstrap_iters=0,
                            random_seed=0, numpy_random_seed=1234, torch_random_seed=1234, fewshot_random_seed=1234)
    najdluzszy = najdluzsze_zadanie(obiekt, lm.tokenizer)
    assert najdluzszy <= lm.max_length, (najdluzszy, lm.max_length)
    probki = wynik["samples"][ZADANIE]
    if a.limit:
        print(json.dumps(probki[0]["arguments"], ensure_ascii=False)[:600])
        print(json.dumps(wiersze(probki)[:3]))
    else:
        cel = WYNIKI / a.model / f"{a.sample}.jsonl.gz"
        cel.parent.mkdir(parents=True, exist_ok=True)
        tresc = "".join(json.dumps(w, sort_keys=True) + "\n" for w in wiersze(probki)).encode()
        with open(cel, "wb") as surowy, gzip.GzipFile(filename="", mode="wb", fileobj=surowy, mtime=0) as gz:
            gz.write(tresc)
    print(json.dumps({"model": a.model, "sample": a.sample, "acc": wynik["results"][ZADANIE]["acc,none"],
                      "n": len(probki), "najdluzszy_kontekst": najdluzszy}))


def czytaj(model, probka):
    with gzip.open(WYNIKI / model / f"{probka}.jsonl.gz", "rt", encoding="utf-8") as f:
        return [json.loads(l) for l in f]


def podsumuj(oceny, klasy_splitu):
    wiersz = srednia_z_niepewnoscia([o["acc"] for o in oceny])
    wiersz["bazy"] = bazy_mc([{"k": 2, "gold": o["gold"], "pred_acc": o["pred"]} for o in oceny], klasy_stale=True)
    wiersz["baza_wiekszosciowa_split"] = max(klasy_splitu) / sum(klasy_splitu)
    return wiersz


def porownanie(wartosc, se, baza):
    z = (wartosc - baza) / se
    return {"roznica": wartosc - baza, "se": se, "z": z, "werdykt": werdykt(z)}


def wobec_wiekszosciowej(oceny):
    """Both predictors answer the same questions, so the SE of the difference is paired (tools/statystyka.py)."""
    r = wobec_stalej([o["acc"] for o in oceny], [o["gold"] for o in oceny])
    return {"roznica": r["roznica"], "se": r["se"], "z": r["z"], "werdykt": r["werdykt"]}


PROG_SCHEMATU = 0.6  # Jaccard słów sąsiednich zdań; 0,5 i 0,7 dają ten sam werdykt (README)


def _slowa(tekst):
    return set(tekst.lower().replace(".", " ").replace(",", " ").split())


def schematy(dokumenty, prog=PROG_SCHEMATU):
    """Id schematu dla każdego dokumentu. WSC273 nie ma id schematu, a schematy nie zawsze są parami
    (George, wiersze 252-254, ma 3 zdania; Madonna, 267-270, 4), więc k // 2 je rozjeżdża. Zdania jednego
    schematu stoją kolejno i różnią się jednym-dwoma słowami: kolejny dokument należy do schematu poprzedniego,
    gdy Jaccard ich słów >= prog."""
    out, g = [], 0
    for i, d in enumerate(dokumenty):
        if i:
            a, b = _slowa(d["text"]), _slowa(dokumenty[i - 1]["text"])
            if len(a & b) / len(a | b) < prog:
                g += 1
        out.append(g)
    return out


def po_schematach(oceny, grupy, baza):
    """Model minus baza z SE K po schematach (grupy[k] = id schematu wiersza k), t przy df = schematy − 1
    (tools/statystyka.py se_k). Stała odpowiedź trafia w schemacie o przeciwnych odpowiedziach mniej więcej raz
    na parę, więc wariancja różnicy siedzi w schematach, a SE po pytaniach ją zawyża. `baza(o)` to trafienie
    bazy na pytaniu o."""
    r = se_k([o["acc"] - baza(o) for o in oceny], [grupy[o["k"]] for o in oceny])
    rozmiary = {}
    for o in oceny:
        rozmiary[grupy[o["k"]]] = rozmiary.get(grupy[o["k"]], 0) + 1
    licz = {}
    for v in rozmiary.values():
        licz[str(v)] = licz.get(str(v), 0) + 1
    return {"roznica": r["roznica"], "se": r["se"], "t": r["t"], "df": r["df"], "p": r["p_t"],
            "werdykt": r["werdykt"], "schematy": r["k"], "rozmiary_schematow": dict(sorted(licz.items()))}


def holm_bazy(raport):
    """Holm na sześciu wierszach tabeli „Slayer 1.06 wobec baz” (rodzina = ta tabela); p z z, a po schematach z t."""
    p, s = raport["slayer_panel200"], raport["slayer_pelny"]
    wiersze = [("panel200", "losowa", p_z(p["wobec_losowej"]["z"])),
               ("panel200", "wiekszosciowa", p_z(p["wobec_wiekszosciowej"]["z"])),
               ("pelny", "losowa", p_z(s["wobec_losowej"]["z"])),
               ("pelny", "wiekszosciowa", p_z(s["wobec_wiekszosciowej"]["z"])),
               ("pelny_po_schematach", "losowa", s["wobec_losowej_po_schematach"]["p"]),
               ("pelny_po_schematach", "wiekszosciowa", s["wobec_wiekszosciowej_po_schematach"]["p"])]
    return [{"probka": a, "baza": b, **h} for (a, b, _), h in zip(wiersze, po_holmie([x for *_, x in wiersze]))]


def po_schematach_pelny(pelny, docs, wynik_pelny):
    """Odczyt po schematach (wiążący, typ `mc +klastry`) wobec obu baz, plus wrażliwość na próg grupowania."""
    klasa = max((0, 1), key=lambda i: sum(x["gold"] == i for x in pelny))
    losowa = lambda o: wynik_pelny["bazy"]["chance_value"]  # noqa: E731
    wieksz = lambda o: float(o["gold"] == klasa)  # noqa: E731
    grupy = schematy(docs)
    return {"wobec_losowej_po_schematach": po_schematach(pelny, grupy, losowa),
            "wobec_wiekszosciowej_po_schematach": po_schematach(pelny, grupy, wieksz),
            "po_schematach_wrazliwosc_progu": {
                str(p): {"schematy": max(g) + 1, "t_losowa": po_schematach(pelny, g, losowa)["t"],
                         "t_wiekszosciowa": po_schematach(pelny, g, wieksz)["t"]}
                for p in (0.5, 0.7) for g in [schematy(docs, p)]}}


def pola(dokumenty, klucze):
    return [{k: d[k] for k in klucze} for d in dokumenty]


def bez_sortowania(dokumenty):
    return [hashlib.sha256(json.dumps(d, ensure_ascii=False).encode("utf-8")).hexdigest() for d in dokumenty]


def warianty(pelne, surowe, przetworzone):
    """Slayer on the samples from each document identity, as subsets of the full run."""
    wynik = {}
    for nazwa, ids in {"indeks_wiersza": [str(i) for i in range(len(pelne))],
                       "przed_process_docs": tozsamosci(surowe),
                       "po_process_docs": tozsamosci(przetworzone),
                       "przed_process_docs_bez_sort_keys": bez_sortowania(surowe),
                       "po_process_docs_bez_sort_keys": bez_sortowania(przetworzone),
                       "pola_tresci": tozsamosci(pola(przetworzone, POLA_TRESCI))}.items():
        wiersz = srednia_z_niepewnoscia([pelne[i]["acc"] for i in panel_z(ids)])
        wynik[nazwa] = {k: wiersz[k] for k in ("value", "n", "se")}
    return wynik


def podzbiory_pol(pelne, przetworzone):
    """Sample value for every strict subset of the fields that keeps `text` and `options`."""
    reszta = [k for k in przetworzone[0] if k not in ("text", "options")]
    kombinacje = [("text", "options", *c) for r in range(len(reszta)) for c in itertools.combinations(reszta, r)]
    wartosci = [statistics.fmean(pelne[i]["acc"] for i in panel_z(tozsamosci(pola(przetworzone, k))))
                for k in kombinacje]
    return {"n": len(wartosci), "min": min(wartosci), "mediana": statistics.median(wartosci), "max": max(wartosci)}


def sd_podproby(pelne, n=ROZMIAR_PANELU):
    """SD of the mean of a random n-of-N subsample of a fixed run: what drawing another sample costs by itself."""
    return (statistics.variance(w["acc"] for w in pelne) / n * (1 - n / len(pelne))) ** 0.5


def cmd_report(_):
    obiekt = zadanie()
    docs = dokumenty(obiekt)
    panel = json.loads(PANEL.read_text(encoding="utf-8"))["indeksy"]
    assert panel == panel_z(tozsamosci(docs))
    klasy = [sum(int(d["label"]) == i for d in docs) for i in (0, 1)]
    pelny = czytaj("slayer-1.06", "full")
    probka = czytaj("slayer-1.06", "panel200")
    kontrola = czytaj("bloom-560m", "full")
    assert [w["k"] for w in probka] == sorted(panel)
    roznica = max(abs(a - b) for w in probka for a, b in zip(w["logliki"], pelny[w["k"]]["logliki"]))
    rozne_acc = sum(w["acc"] != pelny[w["k"]]["acc"] for w in probka)
    assert roznica <= PROG_ZGODNOSCI and rozne_acc == 0, (roznica, rozne_acc)
    wynik_kontroli = srednia_z_niepewnoscia([w["acc"] for w in kontrola])
    assert PROG_KONTROLI[0] <= wynik_kontroli["value"] <= PROG_KONTROLI[1], wynik_kontroli
    wynik_pelny, wynik_panel = podsumuj(pelny, klasy), podsumuj(probka, klasy)
    wobec_baz = lambda w, oceny: {"wobec_losowej": porownanie(w["value"], w["se"], w["bazy"]["chance_value"]),
                                  "wobec_wiekszosciowej": wobec_wiekszosciowej(oceny)}
    warianty_wyniku = warianty(pelny, dokumenty_surowe(obiekt), docs)
    wartosci_wariantow = [w["value"] for w in warianty_wyniku.values()]
    raport = {
        "kontrola":{**wynik_kontroli, "opublikowana": KONTROLA["wartosc"], "se_opublikowane": KONTROLA["se"],
                     "porownanie": porownanie(wynik_kontroli["value"], KONTROLA["se"], KONTROLA["wartosc"])},
        "slayer_panel200": {**wynik_panel, **wobec_baz(wynik_panel, probka)},
        "slayer_pelny": {**wynik_pelny, **wobec_baz(wynik_pelny, pelny),
                         # panel 200 has whole and broken schemas, so only the full split gets the schema reading
                         **po_schematach_pelny(pelny, docs, wynik_pelny)},
        "zgodnosc_panel_pelny": {"max_roznica_loglik": roznica, "rozne_acc": rozne_acc},
        "warianty_tozsamosci": warianty_wyniku,
        "rozstep_wariantow": max(wartosci_wariantow) - min(wartosci_wariantow),
        "podzbiory_pol": podzbiory_pol(pelny, docs),
        "sd_podproby_200": sd_podproby(pelny),
    }
    raport["holm_bazy"] = holm_bazy(raport)
    RAPORT.write_text(json.dumps(raport, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("panel").set_defaults(fn=cmd_panel)
    e = sub.add_parser("evaluate")
    e.add_argument("--model", choices=list(MODELE), required=True)
    e.add_argument("--model_path", required=True)
    e.add_argument("--sample", choices=["panel200", "full"], required=True)
    e.add_argument("--device", default="cpu")
    e.add_argument("--limit", type=int, default=0, help="smoke run on the first N documents; writes nothing")
    e.set_defaults(fn=cmd_evaluate)
    sub.add_parser("report").set_defaults(fn=cmd_report)
    a = p.parse_args()
    a.fn(a)
