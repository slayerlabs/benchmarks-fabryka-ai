"""Definicje zadań niezależnej ewaluacji Slayera 1B jako słowniki konfiguracji lm-eval.

Każde zadanie z panelu Space ma tu wariant „space" (ten sam prompt i wybory co
`lm_eval/tasks/...` wskazane w tasks_50.json Space) i, gdy Space liczy MC w formacie
litery, wariant „cloze" (wybory = treść odpowiedzi). Do każdego wariantu MC dochodzi
`acc_mutual_info`, więc w próbkach lądują też logliki bezwarunkowe do kalibracji PMI.

Źródło danych: `hf` (repo i rewizja przypięte jak w tasks_50.json) albo `lokalne`
(pliki JSONL z `tests/data/`, test na sucho bez sieci).
"""

import importlib.util
from pathlib import Path

import lm_eval

KATALOG = Path(__file__).resolve().parent
DANE_TESTOWE = KATALOG / "tests" / "data"
ZADANIA_LM_EVAL = Path(lm_eval.__file__).resolve().parent / "tasks"

METRYKI_MC = [
    {"metric": "acc", "aggregation": "mean", "higher_is_better": True},
    {"metric": "acc_norm", "aggregation": "mean", "higher_is_better": True},
    {"metric": "acc_mutual_info", "aggregation": "mean", "higher_is_better": True},
]


def _modul_lm_eval(sciezka_wzgledna):
    """Moduł pomocniczy zadania lm-eval (katalogi zadań nie są pakietami)."""
    plik = ZADANIA_LM_EVAL / sciezka_wzgledna
    spec = importlib.util.spec_from_file_location(plik.stem, plik)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def medmcqa_cloze_text(doc):
    return "Question: " + doc["question"] + "\nAnswer:"


def medmcqa_choices(doc):
    return [doc["opa"], doc["opb"], doc["opc"], doc["opd"]]


PARY_MULTIBLIMP = [("sen", "wrong_sen"), ("sentence_good", "sentence_bad"), ("good", "bad")]


def multiblimp_choices(doc):
    """Para minimalna [poprawne, błędne]; nazwy kolumn TSV niezweryfikowane, stąd kilka wariantów."""
    for dobre, zle in PARY_MULTIBLIMP:
        if dobre in doc and zle in doc:
            return [doc[dobre], doc[zle]]
    raise KeyError(f"MultiBLiMP: brak kolumn pary minimalnej, są {sorted(doc)}")


# Metadane z tasks_50.json Space (odczyt 29.10.2026). `klasy_stale` steruje bazą
# większościową: Space podaje ją tylko dla zadań o stałym zbiorze klas.
ZADANIA = {
    # BLiMP: lm-eval group `blimp` (67 members, 6d2abda4 _template_yaml). One config over all 67
    # parquet files; on the full set the micro mean equals the group's equal-weight mean (1000 pairs
    # each). The panel of 200 needs the group allocation from blimp.panel(), not wybor_probki.
    # Counted results (Slayer included) come from `hipoteza_formatu.py licz --zadania blimp`.
    "T01": dict(benchmark_id="blimp", task="blimp", family="blimp", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="nyu-mll/blimp", rewizja="877fba0801ffb7cbd8c39c1ff314a46f053f6036",
                parquet_hf="*/train-*.parquet", split="train", rodzaj="mc", klasy_stale=False),
    "T02": dict(benchmark_id="arc", task="arc_challenge", family="science_qa", language="EN",
                metric="acc_norm,none", unit="score", higher_is_better=True, klucz="acc_norm",
                repo="allenai/ai2_arc", rewizja="210d026faf9955653af8916fad021475a3f00453",
                nazwa_hf="ARC-Challenge", split="test", rodzaj="mc", klasy_stale=True, pole_id="id",
                trace=True),
    "T03": dict(benchmark_id="wikitext2", task="wikitext", family="language_modeling", language="EN",
                metric="byte_perplexity,none", unit="byte_ppl", higher_is_better=False,
                repo="EleutherAI/wikitext_document_level", rewizja="647234772b9554e208af6c826f23b99e3cac88c8",
                nazwa_hf="wikitext-2-raw-v1", split="test", rodzaj="rolling", probkowanie=False),
    "T04": dict(benchmark_id="multiblimp", task="multiblimp_pl", family="grammar", language="PL",
                metric="accuracy", unit="percent", higher_is_better=True,
                repo="jumelet/multiblimp", rewizja="de923efa8d2483d6b13364ee68e65308e990a991",
                plik_hf="pol/data.tsv", split="pol/data.tsv", rodzaj="mc", klasy_stale=False),
    "T44": dict(benchmark_id="pubmedqa", task="pubmedqa", family="biomedical_qa", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="bigbio/pubmed_qa", rewizja="15578e80ef02c2c9636d33fdd7eb6b05b987ba60",
                nazwa_hf="pubmed_qa_labeled_fold0_source", split="test", rodzaj="mc", klasy_stale=True,
                parquet=True),
    "T45": dict(benchmark_id="medmcqa", task="medmcqa", family="biomedical_qa", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="openlifescienceai/medmcqa", rewizja="91c6572c454088bf71b679ad90aa8dffcd0d5868",
                split="validation", rodzaj="mc", klasy_stale=True, cloze=True, pole_id="id"),
    "T46": dict(benchmark_id="social_iqa", task="social_iqa", family="commonsense", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="allenai/social_i_qa", rewizja="8835ceb9141d7896d9d968634a9b21ae440e3ec5",
                split="validation", rodzaj="mc", klasy_stale=False, parquet=True),
}

# ARC-C pierwszy: priorytet zespołu (wynik dosłownie losowy, potrzebny trace per pytanie).
PIATKA = ["T02", "T03", "T04", "T44", "T45", "T46"]


def arc_mc_text(doc):
    """ARC w formacie litery (wariant diagnostyczny): opcje z etykietami zbioru, odpowiedź literą."""
    opcje = "\n".join(f"{l}. {t}" for l, t in zip(doc["choices"]["label"], doc["choices"]["text"]))
    return f"Question: {doc['question']}\n{opcje}\nAnswer:"


def arc_mc_choices(doc):
    return list(doc["choices"]["label"])


def arc_target(doc):
    return doc["choices"]["label"].index(doc["answerKey"])


def _zrodlo(task_id, meta, zrodlo):
    """Pola datasetu: przypięte HF albo lokalny JSONL o tej samej strukturze rekordu."""
    if zrodlo == "lokalne":
        plik = DANE_TESTOWE / f"{meta['task']}.jsonl"
        return {"dataset_path": "json", "dataset_name": None,
                "dataset_kwargs": {"data_files": {"test": str(plik)}}, "test_split": "test"}
    if zrodlo != "hf":
        raise ValueError(f"nieznane źródło danych: {zrodlo}")
    kw = {"revision": meta["rewizja"]}
    if meta.get("parquet"):
        # Repo z loading scriptem: Space czyta przypiętą konwersję parquet (METHOD.md);
        # gałąź refs/convert/parquet nie ma przypiętego SHA, więc rewizja idzie do raportu.
        kw = {"revision": "refs/convert/parquet"}
    if meta.get("parquet_hf"):
        return {"dataset_path": "parquet", "dataset_name": None,
                "dataset_kwargs": {"data_files": {"test": f"hf://datasets/{meta['repo']}@{meta['rewizja']}/{meta['parquet_hf']}"}},
                "test_split": "test"}
    if meta.get("plik_hf"):
        return {"dataset_path": "csv", "dataset_name": None,
                "dataset_kwargs": {"data_files": {"test": f"hf://datasets/{meta['repo']}@{meta['rewizja']}/{meta['plik_hf']}"},
                                   "delimiter": "\t"},
                "test_split": "test"}
    return {"dataset_path": meta["repo"], "dataset_name": meta.get("nazwa_hf"),
            "dataset_kwargs": kw, "test_split": meta["split"]}


def konfiguracje(task_id, zrodlo="hf"):
    """Lista (wariant, config) dla jednego zadania Space. Pierwszy wariant = format Space."""
    warianty = _konfiguracje(task_id, zrodlo)
    for _, cfg in warianty:
        cfg["task_alias"] = cfg["task"]  # tabela wyników lm-eval wywraca się na aliasie None
    return warianty


def _konfiguracje(task_id, zrodlo):
    meta = ZADANIA[task_id]
    baza = {"output_type": "multiple_choice", "num_fewshot": 0, "metric_list": METRYKI_MC,
            "metadata": {"version": 1.0, "task_id": task_id}, **_zrodlo(task_id, meta, zrodlo)}
    t = meta["task"]
    if t == "blimp":
        # lm-eval blimp: empty context, default delimiter " ", gold = good sentence; metric acc only
        return [("space", {**baza, "task": "slayer_blimp", "doc_to_text": "", "target_delimiter": " ",
                           "doc_to_choice": "{{[sentence_good, sentence_bad]}}", "doc_to_target": 0,
                           "metric_list": [METRYKI_MC[0]]})]
    if t == "arc_challenge":
        # Space liczy ARC-C jak lm-eval arc_challenge (cloze, metryka główna acc_norm).
        return [("space", {**baza, "task": "slayer_arc_challenge", "doc_to_text": "Question: {{question}}\nAnswer:",
                           "doc_to_choice": "{{choices.text}}", "doc_to_target": arc_target}),
                ("mc", {**baza, "task": "slayer_arc_challenge_mc", "doc_to_text": arc_mc_text,
                        "doc_to_choice": arc_mc_choices, "doc_to_target": arc_target})]
    if t == "wikitext":
        wt = _modul_lm_eval("wikitext/preprocess_wikitext.py")
        return [("space", {**baza, "task": "slayer_wikitext", "output_type": "loglikelihood_rolling",
                           "doc_to_text": "", "doc_to_target": wt.wikitext_detokenizer,
                           "process_results": wt.process_results,
                           "metric_list": [{"metric": "word_perplexity"}, {"metric": "byte_perplexity"},
                                           {"metric": "bits_per_byte"}]})]
    if t == "multiblimp_pl":
        # „space-prefix log-probability-sum" z tasks_50: pusty kontekst, zdanie po spacji, suma logprob.
        return [("space", {**baza, "task": "slayer_multiblimp_pl", "doc_to_text": "",
                           "target_delimiter": " ", "doc_to_choice": multiblimp_choices, "doc_to_target": 0})]
    if t == "pubmedqa":
        pm = _modul_lm_eval("pubmedqa/preprocess_pubmedqa.py")
        return [("space", {**baza, "task": "slayer_pubmedqa", "doc_to_text": pm.doc_to_text,
                           "doc_to_choice": ["yes", "no", "maybe"], "doc_to_target": "final_decision"})]
    if t == "medmcqa":
        mm = _modul_lm_eval("medmcqa/utils_medmcqa.py")
        return [("space", {**baza, "task": "slayer_medmcqa", "doc_to_text": mm.doc_to_text,
                           "doc_to_choice": ["A", "B", "C", "D"], "doc_to_target": "cop"}),
                ("cloze", {**baza, "task": "slayer_medmcqa_cloze", "doc_to_text": medmcqa_cloze_text,
                           "doc_to_choice": medmcqa_choices, "doc_to_target": "cop"})]
    if t == "social_iqa":
        return [("space", {**baza, "task": "slayer_social_iqa", "doc_to_text": "Q: {{context}} {{question}}\nA:",
                           "target_delimiter": " ", "doc_to_choice": "{{[answerA, answerB, answerC]}}",
                           "doc_to_target": "{{ (label|int) - 1 }}"})]
    raise KeyError(task_id)
