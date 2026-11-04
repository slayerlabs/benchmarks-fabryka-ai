"""Definicje zadań niezależnej ewaluacji Slayera 1B jako słowniki konfiguracji lm-eval.

Każde zadanie z panelu Space ma tu wariant „space" (ten sam prompt i wybory co
`lm_eval/tasks/...` wskazane w tasks_50.json Space) i, gdy Space liczy MC w formacie
litery, wariant „cloze" (wybory = treść odpowiedzi). Do każdego wariantu MC dochodzi
`acc_mutual_info`, więc w próbkach lądują też logliki bezwarunkowe do kalibracji PMI.

Źródło danych: `hf` (repo i rewizja przypięte jak w tasks_50.json) albo `lokalne`
(pliki JSONL z `tests/data/`, test na sucho bez sieci).
"""

import importlib.util
import sys
from pathlib import Path

import lm_eval

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metryki as M  # noqa: E402

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
                parquet=True, rewizja_parquet="13a7d15476092370cbabb6475390e7e69b74d2f2"),
    "T45": dict(benchmark_id="medmcqa", task="medmcqa", family="biomedical_qa", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="openlifescienceai/medmcqa", rewizja="91c6572c454088bf71b679ad90aa8dffcd0d5868",
                split="validation", rodzaj="mc", klasy_stale=True, cloze=True, pole_id="id"),
    "T46": dict(benchmark_id="social_iqa", task="social_iqa", family="commonsense", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="allenai/social_i_qa", rewizja="8835ceb9141d7896d9d968634a9b21ae440e3ec5",
                split="validation", rodzaj="mc", klasy_stale=False, parquet=True),
    # --- (c): config from the installed lm-eval YAML (`lm_eval` / `grupa`), dataset pinned as in tasks_50.json.
    # rodzaj: mc = own MC metrics from logliks; proba = lm-eval per-question metric `klucz` of filter `filtr`;
    # korpus = corpus metric over (gold, pred) pairs. baza: how the constant-answer baseline is computed
    # (ewaluuj.bazy_proby). shots > 0 with a separate few-shot split: demonstrations from the hash-selected
    # disjoint bank (METHOD.md §4, ewaluuj.uzyj_banku); fixed source shots (BBH) stay as published.
    "T07": dict(benchmark_id="winogrande", task="winogrande", family="winogrande", language="EN",
                metric="acc,none", unit="score", higher_is_better=True, lm_eval="winogrande",
                repo="allenai/winogrande", rewizja="01e74176c63542e6b0bcb004dcdea22d94fb67b5",
                nazwa_hf="winogrande_xl", split="validation", rodzaj="mc", klasy_stale=True),
    "T14": dict(benchmark_id="wsc273", task="wsc273", family="wsc273", language="EN",
                metric="acc,none", unit="score", higher_is_better=True, lm_eval="wsc273",
                repo="ErnestSDavis/winograd_wsc", rewizja="8052c534a4cecd8328c0bc879f6a5aa07404c4da",
                nazwa_hf="wsc273", split="test", rodzaj="mc", klasy_stale=True,
                rewizja_parquet="24cdebf4993560f25ff220b171e40f1027f3d9e6"),
    "T17": dict(benchmark_id="lambada", task="lambada_openai", family="lambada", language="EN",
                metric="acc,none", unit="score", higher_is_better=True, lm_eval="lambada_openai",
                repo="EleutherAI/lambada_openai", rewizja="900124bf3b8235c6daf21033af9948b3f07346c4",
                nazwa_hf="default", split="test", rodzaj="proba", klucz="acc", baza="cloze"),
    "T32": dict(benchmark_id="mmlu", task="mmlu", family="mmlu", language="EN",
                metric="acc,none", unit="score", higher_is_better=True, grupa="mmlu",
                repo="hails/mmlu_no_train", rewizja="b2e1ec9aa795adafe68e8e983248dbd4b52a1c60",
                split="test", rodzaj="mc", klasy_stale=True, shots=5),
    "T33": dict(benchmark_id="gsm8k", task="gsm8k", family="gsm8k", language="EN",
                metric="exact_match,strict-match", unit="score", higher_is_better=True, lm_eval="gsm8k",
                repo="openai/gsm8k", rewizja="740312add88f781978c0658806c59bc2815b9866",
                nazwa_hf="main", split="test", rodzaj="proba", klucz="exact_match", filtr="strict-match",
                baza="gen", shots=5),
    "T34": dict(benchmark_id="math", task="hendrycks_math", family="math", language="EN",
                metric="exact_match,none", unit="score", higher_is_better=True, grupa="hendrycks_math",
                repo="EleutherAI/hendrycks_math", rewizja="21a5633873b6a120296cce3e2df9d5550074f4a3",
                split="test", rodzaj="proba", klucz="exact_match", baza="gen"),
    "T35": dict(benchmark_id="truthfulqa", task="truthfulqa_mc2", family="truthfulqa", language="EN",
                metric="acc,none", unit="score", higher_is_better=True, lm_eval="truthfulqa_mc2",
                repo="truthfulqa/truthful_qa", rewizja="741b8276f2d1982aa3d5b832d3ee81ed3b896490",
                nazwa_hf="multiple_choice", split="validation", rodzaj="proba", klucz="acc", baza="masa"),
    "T36": dict(benchmark_id="ifeval", task="ifeval", family="ifeval", language="EN",
                metric="prompt_level_strict_acc,none", unit="score", higher_is_better=True, lm_eval="ifeval",
                repo="google/IFEval", rewizja="966cd89545d6b6acfd7638bc708b98261ca58e84",
                split="train", rodzaj="proba", klucz="prompt_level_strict_acc", baza="pusta"),
    "T38": dict(benchmark_id="squad2", task="squadv2", family="squad2", language="EN",
                metric="f1,none", unit="percent", higher_is_better=True,
                repo="rajpurkar/squad_v2", rewizja="3ffb306f725f7d2ce8394bc1873b24868140c412",
                nazwa_hf="squad_v2", split="validation", rodzaj="proba", klucz="f1", baza="gen",
                podzbior="HasAns"),
    "T39": dict(benchmark_id="drop", task="drop", family="drop", language="EN",
                metric="f1,none", unit="score", higher_is_better=True, lm_eval="drop",
                repo="EleutherAI/drop", rewizja="619386fc7ffe6dace3cc6d3483c69b164ebf6bf3",
                split="validation", rodzaj="proba", klucz="f1", baza="gen"),
    "T41": dict(benchmark_id="coqa", task="coqa", family="coqa", language="EN",
                metric="f1,none", unit="score", higher_is_better=True, lm_eval="coqa",
                repo="EleutherAI/coqa", rewizja="82e11af842af6c1396f5e9a5c7de260107c50cf1",
                split="validation", rodzaj="proba", klucz="f1", baza="gen"),
    "T42": dict(benchmark_id="nq_open", task="nq_open", family="nq_open", language="EN",
                metric="exact_match,remove_whitespace", unit="score", higher_is_better=True, lm_eval="nq_open",
                repo="google-research-datasets/nq_open", rewizja="5dd9790a83002ad084ddeb7c420dc716852c6f28",
                nazwa_hf="nq_open", split="validation", rodzaj="proba", klucz="exact_match",
                filtr="remove_whitespace", baza="gen"),
    "T43": dict(benchmark_id="triviaqa", task="triviaqa", family="triviaqa", language="EN",
                metric="exact_match,remove_whitespace", unit="score", higher_is_better=True, lm_eval="triviaqa",
                repo="mandarjoshi/trivia_qa", rewizja="0f7faf33a3908546c6fd5b73a660e0f8ff173c2f",
                nazwa_hf="rc.nocontext", split="validation", rodzaj="proba", klucz="exact_match",
                filtr="remove_whitespace", baza="gen"),
    "T47": dict(benchmark_id="bbh", task="bbh_fewshot", family="bbh", language="EN",
                metric="exact_match,none", unit="score", higher_is_better=True, grupa="bbh_fewshot",
                repo="lukaemon/bbh", rewizja="982bb89fd79532a8ac676a61fc42eb1aeec63f99",
                split="test", rodzaj="proba", klucz="exact_match", baza="gen", shots=3, strip=True),
    "T49": dict(benchmark_id="cola", task="cola", family="cola", language="EN",
                metric="mcc,none", unit="score", higher_is_better=True, lm_eval="cola",
                repo="nyu-mll/glue", rewizja="bcdcba79d07bc864c1c254ccfcedcce55bcc9a8c",
                nazwa_hf="cola", split="validation", rodzaj="korpus", klucz="mcc", baza="mcc"),
    "T50": dict(benchmark_id="record", task="record", family="record", language="EN",
                metric="f1,none", unit="score", higher_is_better=True, lm_eval="record",
                repo="aps/super_glue", rewizja="3de24cf8022e94f4ee4b9d55a6f539891524d646",
                nazwa_hf="record", split="validation", rodzaj="proba", klucz="f1", baza="wybor_losowy"),
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
    if meta.get("rewizja_parquet"):
        # GOTCHA: datasets 3.6 sees only the "default" config on refs/convert/parquet, so a named
        # config is read from its parquet files at the pinned commit of that ref.
        sciezka = f"hf://datasets/{meta['repo']}@{meta['rewizja_parquet']}/{meta['nazwa_hf']}/{meta['split']}/*.parquet"
        return {"dataset_path": "parquet", "dataset_name": None,
                "dataset_kwargs": {"data_files": {"test": sciezka}}, "test_split": "test"}
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


_MENEDZER = []


def _yaml(nazwa):
    """Config zadania z YAML-a zainstalowanego lm-eval (`!function` rozwiązane), świeża kopia do nadpisania."""
    if not _MENEDZER:
        from lm_eval.tasks import TaskManager
        _MENEDZER.append(TaskManager())
    return dict(_MENEDZER[0]._get_config(nazwa))


def czlonkowie_grupy(grupa):
    """Podtesty grupy lm-eval; MMLU to grupa grup po tagach, więc członków daje katalog `mmlu/default`."""
    if grupa == "mmlu":
        return sorted(p.stem for p in (ZADANIA_LM_EVAL / "mmlu" / "default").glob("mmlu_*.yaml"))
    return list(_yaml(grupa)["task"])


def _zrodlo_yaml(task_id, meta, zrodlo, nazwa, cfg):
    """Pola datasetu configu z YAML-a. Lokalnie: `tests/data/<podtest>.jsonl`, bank demonstracji z
    `<podtest>_demo.jsonl`. Z HF: repo i rewizja Space, podzbiór grupy z YAML-a podtestu, splity YAML-a poza testowym."""
    if zrodlo == "lokalne":
        pliki = {"test": str(DANE_TESTOWE / f"{nazwa}.jsonl")}
        demo = DANE_TESTOWE / f"{nazwa}_demo.jsonl"
        if demo.exists():
            pliki["demo"] = str(demo)
        return {"dataset_path": "json", "dataset_name": None, "dataset_kwargs": {"data_files": pliki},
                "test_split": "test", "validation_split": None, "training_split": None,
                "fewshot_split": "demo" if demo.exists() else None}
    pola = _zrodlo(task_id, meta, zrodlo)
    if meta.get("grupa"):
        pola["dataset_name"] = cfg.get("dataset_name")
    return pola


def _z_lm_eval(task_id, meta, zrodlo, nazwa, **nadpisz):
    cfg = _yaml(nazwa)
    for klucz in ("group", "tag"):
        cfg.pop(klucz, None)
    cfg.update(_zrodlo_yaml(task_id, meta, zrodlo, nazwa, cfg))
    cfg.update(task=f"slayer_{nazwa}", num_fewshot=meta.get("shots", 0),
               metadata={**(cfg.get("metadata") or {}), "task_id": task_id, "czlonek": nazwa})
    cfg.update(nadpisz)
    return cfg


def mc2_wyniki(doc, results):
    """TruthfulQA MC2 w wersji 6d2abda4 (Space); 0.4.9.1 przepisało `process_results_mc2`."""
    return {"acc": M.mc2([r[0] for r in results], doc["mc2_targets"]["labels"])}


def squad2_klasa(cfg):
    """SQuAD 2.0: legacy klasa lm-eval (prompt, żądania, `until: \\n`), jak każe tasks_50.json; podmienione są
    tylko zbiór (przypięty) i metryka: F1/EM squad_v2 per pytanie offline (metryki.squad_f1), średnia = f1 modułu
    `evaluate` przy progu no-answer 1,0, którego exp(logprob) nie przekracza."""
    from lm_eval.api.metrics import mean
    from lm_eval.api.task import ConfigurableTask
    baza = _modul_lm_eval("squadv2/task.py").SQuAD2
    klucze = ("f1", "exact", "HasAns")
    pola = {k: cfg[k] for k in ("dataset_path", "dataset_name", "dataset_kwargs", "test_split")}

    class SlayerSQuAD2(baza):
        def __init__(self, config=None):
            ConfigurableTask.__init__(self, config={"task": "slayer_squadv2", "output_type": "generate_until",
                                                    "metadata": {"version": self.VERSION}, **pola})

        def has_training_docs(self):
            return "train" in self.dataset

        def validation_docs(self):
            return self.dataset[pola["test_split"]]

        def process_results(self, doc, results):
            zlote = list(doc["answers"]["text"])
            return {"f1": M.squad_f1(results[0], zlote), "exact": M.squad_em(results[0], zlote),
                    "HasAns": float(bool(zlote))}

        def aggregation(self):
            return {k: mean for k in klucze}

        def higher_is_better(self):
            return {k: True for k in klucze}

    return SlayerSQuAD2


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
    if t == "squadv2":
        # metadata.klasa: ewaluuj.zbuduj_zadania builds squad2_klasa(cfg); the dict stays a valid TaskConfig
        return [("space", {"task": "slayer_squadv2", "output_type": "generate_until",
                           "metric_list": [{"metric": "f1", "aggregation": "mean", "higher_is_better": True}],
                           "metadata": {"task_id": task_id, "czlonek": t, "klasa": "squadv2"},
                           **_zrodlo(task_id, meta, zrodlo)})]
    if t == "ifeval":
        from langdetect import DetectorFactory
        DetectorFactory.seed = 0  # METHOD.md §4: language instructions reproducible
    nadpisz = {"mmlu": {"metric_list": METRYKI_MC}, "truthfulqa_mc2": {"process_results": mc2_wyniki}}.get(t, {})
    if meta.get("grupa"):
        return [("space", _z_lm_eval(task_id, meta, zrodlo, m, **nadpisz)) for m in czlonkowie_grupy(meta["grupa"])]
    if meta.get("lm_eval"):
        return [("space", _z_lm_eval(task_id, meta, zrodlo, meta["lm_eval"], **nadpisz))]
    raise KeyError(task_id)
