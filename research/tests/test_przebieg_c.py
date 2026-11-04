"""Testy (c) przebiegu centralnego: generacja, bank demonstracji, limit kontekstu, grupy z wagami, metryki
korpusowe, MC2, ReCoRD, SQuAD 2.0, IFEval, cel zadań wielokontekstowych (T07, T14).

Bez sieci i bez wag: `common/ewaluuj.ocen_zadanie` na atrapie modelu (`AtrapaLM`, odpowiedzi ustalone w teście)
i lokalnych JSONL w katalogu tymczasowym. Wartości oczekiwane policzone ręcznie w komentarzach.
Uruchom: python tests/test_przebieg_c.py (albo pytest).
"""
import json
import math
import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))
import ewaluuj as E  # noqa: E402
import metryki as M  # noqa: E402
import zadania as Z  # noqa: E402
from lm_eval.api.model import LM  # noqa: E402


class AtrapaLM(LM):
    """Model-atrapa: `ll(kontekst, kontynuacja)` -> (loglik, zachłanne), `gen(kontekst)` -> tekst."""

    def __init__(self, ll=None, gen=None):
        super().__init__()
        self.ll, self.gen, self.konteksty = ll, gen, []

    def loglikelihood(self, requests):
        return [self.ll(*r.args) for r in requests]

    def loglikelihood_rolling(self, requests):
        return [-1.0 for _ in requests]

    def generate_until(self, requests):
        wynik = []
        for r in requests:
            self.konteksty.append(r.args[0])
            wynik.append(self.gen(r.args[0]))
        return wynik


def slowa(tekst):
    return len(tekst.split())


def ocen(task_id, dane, lm, tmp_path, monkeypatch, probka="pelna"):
    """`dane`: {plik bez .jsonl: dokumenty} w tests/data atrapy; zwraca (obserwacja, dodatkowe['space'])."""
    katalog = tmp_path / "data"
    katalog.mkdir(exist_ok=True)
    for nazwa, docs in dane.items():
        (katalog / f"{nazwa}.jsonl").write_text("".join(json.dumps(d) + "\n" for d in docs))
    monkeypatch.setattr(Z, "DANE_TESTOWE", katalog)
    wyj = tmp_path / "wyj"
    for podkatalog in ("probki", "trace"):
        (wyj / podkatalog).mkdir(parents=True, exist_ok=True)
    obs, roz, _, _ = E.ocen_zadanie(lm, task_id, "lokalne", probka, slowa, wyj, "0" * 64, "atrapa", "p")
    return obs, roz["dodatkowe"]["space"]


def ostatnie_pytanie(ctx, znacznik):
    return ctx.rsplit(znacznik, 1)[1]


# --- generacja + bank demonstracji (T33 GSM8K) ---

GSM_TEST = [{"question": "What is 2+3?", "answer": "2+3=5\n#### 5"},
            {"question": "What is 3+4?", "answer": "3+4=7\n#### 7"},
            {"question": "What is 2+2?", "answer": "2+2=4\n#### 4"}]
GSM_DEMO = [{"question": f"Demo {i}?", "answer": f"step\n#### {i}"} for i in range(7)] + [GSM_TEST[0]]
GSM_ODP = {"What is 2+3?": " 2+3=5\n#### 5", "What is 3+4?": " #### 8", "What is 2+2?": " The answer is 4"}


def gsm_gen(ctx):
    return GSM_ODP[ostatnie_pytanie(ctx, "Question: ").split("\n")[0]]


def test_gsm8k_generation_strict_match_and_disjoint_bank(tmp_path, monkeypatch):
    lm = AtrapaLM(gen=gsm_gen)
    obs, d = ocen("T33", {"gsm8k": GSM_TEST, "gsm8k_demo": GSM_DEMO}, lm, tmp_path, monkeypatch)
    # strict-match: only "#### 5" matches its gold; "#### 8" is wrong, "The answer is 4" has no "#### "
    assert d["glowna"]["value"] == pytest.approx(1 / 3) and d["glowna"]["metryka"] == "exact_match"
    assert obs["state"] == "ok" and obs["value"] == pytest.approx(1 / 3) and obs["n_scored"] == 3
    # baselines: empty answer 0; most common gold (first of three distinct ones, "#### 5") hits 1 of 3
    assert d["bazy_szczegoly"]["gsm8k"]["pusta"] == 0.0 and d["bazy"]["majority_value"] == pytest.approx(1 / 3)
    # bank: first 5 demo documents in hash order, the copy of a scored question left out, same for every question
    ids = [M.sha256_tekstu(json.dumps(x, sort_keys=True, ensure_ascii=False)) for x in GSM_DEMO]
    oczekiwane = [ids[i] for i in M.ranking_banku("gsm8k", "gsm8k", ids) if i != 7][:5]
    assert d["demonstracje"] == {"gsm8k": oczekiwane}
    kolejnosc = [GSM_DEMO[ids.index(i)]["question"] for i in oczekiwane]
    for ctx in lm.konteksty:
        assert ctx.count("Question: ") == 6
        assert re.findall(r"Question: (Demo \d\?)", ctx) == kolejnosc
        assert ctx.count("What is 2+3?") == (1 if ctx.endswith("What is 2+3?\nAnswer:") else 0)


def test_context_limit_drops_demonstrations_from_the_end():
    class Stub:
        OUTPUT_TYPE = "generate_until"
        config = SimpleNamespace(generation_kwargs={"max_gen_toks": 3}, target_delimiter=" ", task="stub")

        def fewshot_context(self, doc, num_fewshot, **kw):
            return " ".join([f"d{i} x" for i in range(num_fewshot)] + ["q"] * doc["dl"])

    zad = Stub()
    E.ogranicz_kontekst(zad, slowa, 10)
    # 2 words per demonstration + question 1 + budget 3 <= 10 -> 3 demonstrations, the first three
    assert zad.fewshot_context({"dl": 1}, num_fewshot=5) == "d0 x d1 x d2 x q"
    with pytest.raises(ValueError):
        zad.fewshot_context({"dl": 8}, num_fewshot=5)  # question alone + budget > limit: never truncated


# --- grupa z wagami populacji (T34 MATH, gen) ---

MATH_CZLONKOWIE = ["hendrycks_math_algebra", "hendrycks_math_counting_and_prob", "hendrycks_math_geometry",
                   "hendrycks_math_intermediate_algebra", "hendrycks_math_num_theory",
                   "hendrycks_math_prealgebra", "hendrycks_math_precalc"]


def test_math_group_weighted_by_population(tmp_path, monkeypatch):
    dane = {m: [{"problem": f"{m} p0", "solution": "so \\boxed{4}"}] for m in MATH_CZLONKOWIE}
    dane["hendrycks_math_algebra"].append({"problem": "algebra p1", "solution": "so \\boxed{6}"})
    odp = {"hendrycks_math_algebra p0": "$4$", "algebra p1": "$5$", "hendrycks_math_counting_and_prob p0": "$4$"}
    lm = AtrapaLM(gen=lambda ctx: odp.get(ostatnie_pytanie(ctx, "Problem: ").split("\n")[0], "$1$"))
    _, d = ocen("T34", dane, lm, tmp_path, monkeypatch)
    g = d["glowna"]
    # weights 2/8 algebra, 1/8 each other: 2/8 * 1/2 + 1/8 * 1 = 0.25 (= micro mean on the full set)
    assert g["value"] == pytest.approx(0.25) and g["n"] == 8
    assert g["czlonkowie"]["hendrycks_math_algebra"]["waga"] == pytest.approx(0.25)
    # SE W = sqrt(sum w^2 SE_i^2): only algebra has SE (sd 0.7071 / sqrt 2 = 0.5) -> 0.25 * 0.5
    assert g["se"] == pytest.approx(0.125)


# --- grupa MC z bankiem (T32 MMLU) ---

def test_mmlu_group_mc_with_bank(tmp_path, monkeypatch):
    czlonkowie = Z.czlonkowie_grupy("mmlu")
    assert len(czlonkowie) == 57
    dane = {}
    for i, m in enumerate(czlonkowie):
        dane[m] = [{"question": f"{m} q", "subject": m, "choices": ["a", "b", "c", "d"], "answer": i % 4}]
        dane[f"{m}_demo"] = [{"question": f"{m} demo {j}", "subject": m, "choices": ["a", "b", "c", "d"],
                              "answer": 0} for j in range(5)]
    lm = AtrapaLM(ll=lambda ctx, kont: (0.0 if kont == " A" else -1.0, False))
    _, d = ocen("T32", dane, lm, tmp_path, monkeypatch)
    # always "A": hits members with answer 0 (i % 4 == 0 -> 15 of 57), equal populations -> 15/57
    assert d["acc"]["value"] == pytest.approx(15 / 57) and d["acc"]["n"] == 57
    assert d["bazy"]["chance_value"] == pytest.approx(0.25) and d["udzial_najczestszej_predykcji"] == 1.0
    assert len(d["demonstracje"]) == 57 and all(len(v) == 5 for v in d["demonstracje"].values())


# --- BBH: stałe demonstracje źródła, odpowiedź bez spacji (T47) ---

def test_bbh_strip_and_source_shots(tmp_path, monkeypatch):
    czlonkowie = Z.czlonkowie_grupy("bbh_fewshot")
    dane = {m: [{"input": f"{m} x", "target": "True" if i < 9 else "False"}] for i, m in enumerate(czlonkowie)}
    lm = AtrapaLM(gen=lambda ctx: " True")
    _, d = ocen("T47", dane, lm, tmp_path, monkeypatch)
    # " True" stripped hits the 9 members with target True of 27 (equal weights) -> 1/3; literal match 0
    assert d["glowna"]["value"] == pytest.approx(1 / 3)
    assert set(d["zrodlowa_doslowna"].values()) == {0.0}
    assert "demonstracje" not in d  # source shots, no bank
    assert all(ctx.count("Q: ") == 4 for ctx in lm.konteksty)  # 3 source demonstrations + the question


# --- masa (T35 TruthfulQA MC2) ---

def test_truthfulqa_mc2_mass(tmp_path, monkeypatch):
    docs = [{"question": "q1", "mc2_targets": {"choices": ["t1", "t2", "f1"], "labels": [1, 1, 0]}},
            {"question": "q2", "mc2_targets": {"choices": ["t", "f"], "labels": [1, 0]}}]
    ll = {" t1": math.log(0.5), " t2": math.log(0.25), " f1": math.log(0.25), " t": -1.0, " f": -1.0}
    lm = AtrapaLM(ll=lambda ctx, kont: (ll[kont], False))
    _, d = ocen("T35", {"truthfulqa_mc2": docs}, lm, tmp_path, monkeypatch)
    # q1: 0.75 of the mass on true options; q2: equal logliks -> 0.5
    assert d["glowna"]["value"] == pytest.approx(0.625)
    assert d["bazy"]["chance_value"] == pytest.approx((2 / 3 + 1 / 2) / 2)  # share of true options


def test_mc2_matches_lm_eval_on_true_first_labels():
    tq = Z._modul_lm_eval("truthfulqa/utils.py")
    doc = {"mc2_targets": {"labels": [1, 1, 0, 0]}}
    lls = [-1.0, -2.5, -0.5, -3.0]
    assert M.mc2(lls, [1, 1, 0, 0]) == pytest.approx(tq.process_results_mc2(doc, [(x, False) for x in lls])["acc"])


# --- MCC (T49 CoLA) ---

def test_cola_mcc(tmp_path, monkeypatch):
    docs = [{"sentence": f"s{i}", "label": z, "idx": i} for i, z in enumerate([1, 1, 0, 0])]
    pred = {"s0": " yes", "s1": " no", "s2": " no", "s3": " no"}
    lm = AtrapaLM(ll=lambda ctx, kont: (0.0 if pred[ctx.split("\n")[0]] == kont else -1.0, False))
    obs, d = ocen("T49", {"cola": docs}, lm, tmp_path, monkeypatch)
    # TP 1, FN 1, TN 2, FP 0: (1*2 - 0*1) / sqrt(1 * 2 * 2 * 3) = 0.57735
    assert d["glowna"]["value"] == pytest.approx(2 / math.sqrt(12)) and d["glowna"]["metryka"] == "mcc"
    assert d["bazy"]["chance_value"] == 0.0 and d["bazy"]["majority_value"] == 0.0


def test_mcc_and_f1_match_sklearn():
    from sklearn.metrics import f1_score, matthews_corrcoef
    z, p = [0, 1, 2, 2, 1, 0, 1], [0, 2, 2, 1, 1, 0, 0]
    assert M.mcc(z, p) == pytest.approx(matthews_corrcoef(z, p))
    assert M.f1_korpus(z, p, "macro") == pytest.approx(f1_score(z, p, average="macro"))
    assert M.f1_korpus([1, 1, 0, 0], [1, 0, 0, 1]) == pytest.approx(f1_score([1, 1, 0, 0], [1, 0, 0, 1]))
    assert M.mcc([1, 1], [1, 1]) == 0.0  # zero denominator


def test_f1_corpus_for_openpl_mc_tasks():
    """T25/T27/T28 (wpisy wykonawcy A): klucz f1 przy rodzaju mc, agregacja z YAML-a forka (binarne / makro)."""
    from sklearn.metrics import f1_score

    def agg_f1(items):
        p, r = zip(*items)
        return f1_score(r, p)

    def agg_f1_macro(items):
        p, r = zip(*items)
        return f1_score(r, p, average="macro")

    def probka(pred, gold):
        return {"arguments": [("q", " Nie"), ("q", " Tak")], "target": gold, "doc": {},
                "filtered_resps": [(0.0 if i == pred else -1.0, False) for i in range(2)]}

    probki = [probka(p, g) for p, g in zip([1, 0, 0, 1], [1, 1, 0, 0])]
    meta = {"rodzaj": "mc", "klucz": "f1", "klasy_stale": True}
    for agg, oczekiwane in ((agg_f1, 0.5), (agg_f1_macro, 0.5)):
        cfg = {"metric_list": [{"metric": "acc"}, {"metric": type("f", (), {"__name__": "f1"})(), "aggregation": agg}]}
        d = E.podsumuj_wariant(meta, [("dyk", cfg, SimpleNamespace(eval_docs=[0] * 4), probki)])
        assert d["glowna"]["value"] == pytest.approx(oczekiwane) and d["glowna"]["metryka"] == "f1"
        # best constant class: always 1 -> F1 2/3 (binary); macro 1/3
        assert d["bazy"]["majority_value"] == pytest.approx(2 / 3 if agg is agg_f1 else 1 / 3)


# --- ReCoRD (T50) ---

def test_record_entity_f1(tmp_path, monkeypatch):
    docs = [{"passage": "P1 text\n@highlight\nH1", "query": "@placeholder won", "entities": ["Alice", "Alice Smith"],
             "answers": ["Alice Smith"], "idx": {"passage": 0, "query": 0}},
            {"passage": "P2 text", "query": "@placeholder lost", "entities": ["Bob", "Carl"], "answers": ["Carl"],
             "idx": {"passage": 1, "query": 1}}]
    wybor = {"P1": "Alice won", "P2": "Carl lost"}
    lm = AtrapaLM(ll=lambda ctx, kont: (0.0 if kont.strip(" -") == wybor[ctx[:2]] else -1.0, False))
    _, d = ocen("T50", {"record": docs}, lm, tmp_path, monkeypatch)
    # "Alice" vs "Alice Smith": P 1, R 1/2 -> F1 2/3; "Carl" exact -> 1; mean 5/6
    assert d["glowna"]["value"] == pytest.approx(5 / 6)
    # random entity: doc 1 (2/3 + 1) / 2, doc 2 (0 + 1) / 2
    assert d["bazy"]["chance_value"] == pytest.approx(((2 / 3 + 1) / 2 + 0.5) / 2)


# --- SQuAD 2.0 (T38, legacy klasa, procenty) ---

def test_squad2_legacy_class_f1_percent_and_hasans(tmp_path, monkeypatch):
    def doc(i, pytanie, odp):
        return {"id": f"q{i}", "title": "T", "context": "C", "question": pytanie,
                "answers": {"text": odp, "answer_start": [0] * len(odp)}}
    docs = [doc(0, "who won", ["Denver Broncos"]), doc(1, "unanswerable one", []), doc(2, "who lost", ["Carolina"])]
    odp = {"who won": " the Broncos", "unanswerable one": "", "who lost": ""}
    lm = AtrapaLM(gen=lambda ctx: odp[ostatnie_pytanie(ctx, "Question: ").split("\n")[0]],
                  ll=lambda ctx, kont: (-5.0, False))
    obs, d = ocen("T38", {"squadv2": docs}, lm, tmp_path, monkeypatch)
    # "the Broncos" -> "broncos" vs "denver broncos": F1 2/3; empty on no-answer: 1; empty on answerable: 0
    assert d["glowna"]["value"] == pytest.approx((2 / 3 + 1 + 0) / 3)
    assert obs["unit"] == "percent" and obs["value"] == pytest.approx(100 * (2 / 3 + 1) / 3)
    assert d["podzbior"]["glowna"]["value"] == pytest.approx(1 / 3)  # HasAns: (2/3 + 0) / 2
    # HasAns b: empty answer gives 0 there, the constant "Denver Broncos" hits 1 of the 2 -> b = 0.5
    assert d["podzbior"]["bazy"]["majority_value"] == pytest.approx(0.5)
    assert d["bazy_szczegoly"]["squadv2"]["pusta"] == pytest.approx(1 / 3)


def test_squad_f1_official_normalisation():
    assert M.squad_f1("The Denver Broncos!", ["Denver Broncos"]) == 1.0
    assert M.squad_f1("", []) == 1.0 and M.squad_f1("x", []) == 0.0
    assert M.squad_em("an apple", ["Apple", "pear"]) == 1.0


# --- IFEval (T36) ---

def test_ifeval_prompt_level_strict(tmp_path, monkeypatch):
    nltk = pytest.importorskip("nltk")
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        pytest.skip("NLTK punkt_tab missing (IFEval downloads it on import, the test runs offline)")
    pytest.importorskip("langdetect")
    docs = [{"key": i, "prompt": f"Write {i}", "instruction_id_list": ["length_constraints:number_words"],
             "kwargs": [{"relation": "at least", "num_words": 2}]} for i in range(2)]
    odp = {"Write 0": "hello world", "Write 1": "hello"}
    lm = AtrapaLM(gen=lambda ctx: odp[ctx])
    _, d = ocen("T36", {"ifeval": docs}, lm, tmp_path, monkeypatch)
    assert d["glowna"]["value"] == pytest.approx(0.5)  # two words pass "at least 2", one does not
    assert d["bazy"]["majority_value"] == 0.0  # empty answer fails


# --- LAMBADA (T17, is_greedy) ---

def test_lambada_greedy_accuracy_and_cloze_baseline(tmp_path, monkeypatch):
    docs = [{"text": "the cat sat on the mat"}, {"text": "a dog ran to the mat"}, {"text": "I saw a bird"}]
    lm = AtrapaLM(ll=lambda ctx, kont: (-1.0, kont == " mat" and ctx.startswith("the")))
    _, d = ocen("T17", {"lambada_openai": docs}, lm, tmp_path, monkeypatch)
    assert d["glowna"]["value"] == pytest.approx(1 / 3)
    assert d["bazy"]["majority_value"] == pytest.approx(2 / 3)  # "mat" is the target of 2 of 3


# --- cel zadań wielokontekstowych (T07 WinoGrande): regresja indeksu 0 ---

def test_multi_context_gold_comes_from_doc_to_text(tmp_path, monkeypatch):
    docs = [{"sentence": "The trophy fit in the case because _ was small.", "option1": "trophy",
             "option2": "case", "answer": "2"},
            {"sentence": "Ann thanked Mary because _ had helped.", "option1": "Ann", "option2": "Mary",
             "answer": "2"}]
    # the model always prefers the context with the second option
    lm = AtrapaLM(ll=lambda ctx, kont: (0.0 if ctx.endswith(("case", "Mary")) else -1.0, False))
    _, d = ocen("T07", {"winogrande": docs}, lm, tmp_path, monkeypatch)
    assert d["acc"]["value"] == 1.0  # with gold = index 0 (the old bug) this was 0.0
    assert d["bazy"]["majority_value"] == 1.0  # both golds are option 2


def test_target_text_with_identical_continuations_raises():
    probka = {"arguments": [("ctx a", " rest"), ("ctx b", " rest")], "target": "rest",
              "filtered_resps": [(-1.0, False), (0.0, False)]}
    with pytest.raises(ValueError):
        M.rozbierz_mc(probka, z_pmi=False)
    assert M.rozbierz_mc({**probka, "gold": 1}, z_pmi=False)[3] == 1


# --- grupy: przydział panelu i SE warstwowe (czyste funkcje) ---

def test_group_allocation_reserves_two_then_largest_deficit():
    # budget 10, populations 10/5/5: reserve 2 each (6), deficits 3, 0.5, 0.5 -> a three times (9),
    # then a 0, b 0.5, c 0.5 -> b wins the tie by name (10)
    assert M.przydzial_grupy({"c": 5, "a": 10, "b": 5}, 10) == {"a": 5, "b": 3, "c": 2}
    assert M.przydzial_grupy({"a": 1, "b": 3}, 200) == {"a": 1, "b": 3}  # never more than the population


def test_group_allocation_order_independent():
    pop = {f"m{i}": 3 + i for i in range(6)}
    assert M.przydzial_grupy(dict(reversed(list(pop.items()))), 20) == M.przydzial_grupy(pop, 20)


def test_stratified_weights_ignore_sample_quota():
    w = M.warstwy({"a": [1, 1], "b": [0, 0, 0, 0]}, {"a": 3, "b": 1}, powtorzenia=200)
    assert w["value"] == pytest.approx(0.75) and w["se"] == 0.0 and w["n"] == 6


# --- kontrola sensu na metrykach innych niż acc ---

def test_sanity_check_other_metrics():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    import kontrola_sensu as K

    def obs(metric, wartosc, losowa=0.0):
        return {"task_id": "T", "state": "ok", "metric": metric, "dodatkowe": {"space": {
            "glowna": {"metryka": metric.split(",")[0], "value": wartosc}, "bazy": {"chance_value": losowa}}}}
    assert K.bledy_obserwacji(obs("mcc,none", -0.2)) == []  # MCC may be negative
    assert K.bledy_obserwacji(obs("f1,none", 0.3)) == []
    assert K.bledy_obserwacji(obs("levenshtein,none", 0.4)) == []
    assert K.bledy_obserwacji(obs("exact_match,strict-match", 1.0))  # score 1.000 is an error
    assert K.bledy_obserwacji(obs("acc,none", 0.3, losowa=0.5))  # mass below random - 5 points
    assert K.bledy_obserwacji(obs("f1,none", None))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
