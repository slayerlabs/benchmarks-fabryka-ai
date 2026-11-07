"""Definicje zadań niezależnej ewaluacji Slayera 1B jako słowniki konfiguracji lm-eval.

Każde zadanie ma tu wariant główny „space" (nazwa formatu wyniku; prompt i wybory zadania lm-eval z karty
benchmarku, METODOLOGIA „Wersja lm-eval”) i, gdy metryka decyzyjna liczy MC w formacie litery, wariant „cloze"
(wybory = treść odpowiedzi). Do każdego wariantu MC dochodzi `acc_mutual_info`, więc w próbkach lądują też logliki
bezwarunkowe do kalibracji PMI.

Źródło danych: `hf` (repo i rewizja przypięte w ZADANIA, zgodne z kartą: tests/test_zgodnosc_karty.py) albo
`lokalne` (pliki JSONL z `tests/data/`, test na sucho bez sieci).
"""

import importlib.util
import sys
from pathlib import Path

import lm_eval

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metryki as M  # noqa: E402

KATALOG = Path(__file__).resolve().parent
BENCHMARKI = KATALOG.parent / "benchmarks"
DANE_TESTOWE = KATALOG / "tests" / "data"
ZADANIA_LM_EVAL = Path(lm_eval.__file__).resolve().parent / "tasks"

METRYKI_MC = [
    {"metric": "acc", "aggregation": "mean", "higher_is_better": True},
    {"metric": "acc_norm", "aggregation": "mean", "higher_is_better": True},
    {"metric": "acc_mutual_info", "aggregation": "mean", "higher_is_better": True},
]


def _modul_lm_eval(sciezka_wzgledna, katalog=ZADANIA_LM_EVAL):
    """Moduł pomocniczy zadania lm-eval (katalogi zadań nie są pakietami); `katalog` BENCHMARKI = kopia w repo."""
    plik = katalog / sciezka_wzgledna
    spec = importlib.util.spec_from_file_location(plik.stem, plik)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def funkcja_z_pliku(katalog, odwolanie):
    """`!function modul.nazwa` of a task YAML, imported on first call.

    GOTCHA: `__name__` stays the function's own name: lm-eval keys a callable metric by it (`f1`, `levenshtein`).
    """
    nazwa_modulu, nazwa = odwolanie.rsplit(".", 1)
    plik = Path(katalog) / f"{nazwa_modulu}.py"
    zaladowana = []

    def wywolaj(*args, **kwargs):
        if not zaladowana:
            spec = importlib.util.spec_from_file_location(f"{Path(katalog).name}_{nazwa_modulu}", plik)
            modul = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modul)
            zaladowana.append(getattr(modul, nazwa))
        return zaladowana[0](*args, **kwargs)

    wywolaj.__name__ = nazwa
    wywolaj.plik, wywolaj.nazwa = plik, nazwa
    return wywolaj


def wczytaj_yaml(sciezka):
    """Task YAML from benchmarks/*/lm_eval_tasks/ as a dict, `!function` resolved against the YAML's directory."""
    import yaml

    class Ladowacz(yaml.SafeLoader):
        pass

    Ladowacz.add_constructor("!function", lambda l, n: funkcja_z_pliku(Path(sciezka).parent, l.construct_scalar(n)))
    return yaml.load(Path(sciezka).read_text(encoding="utf-8"), Ladowacz)


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


# Ustawienia testów; źródłem jest karta benchmarku (ORIGINAL.md / DATASET.md / POLISH.md), a zgodność wpisu z kartą
# sprawdza tests/test_zgodnosc_karty.py. `klasy_stale` steruje stałą odpowiedzią według typu testu (METODOLOGIA,
# „Typy testów”): True przy `mc`, `mc-k` i `f1-korpus` (udział najczęstszej pozycji poprawnej opcji), False przy
# `para` i `poz` (N/A, b = baza losowa). `klastry` (testy `+klastry`): pole dokumentu albo reguła
# ewaluuj.REGULY_KLASTROW; SE liczy się wtedy po klastrach. Oba klucze sprawdza tests/test_zadania_konfiguracja.py.
ZADANIA = {
    # BLiMP: lm-eval group `blimp` (67 members, 6d2abda4 _template_yaml). One config over all 67
    # parquet files; on the full set the micro mean equals the group's equal-weight mean (1000 pairs
    # each). The panel of 200 needs the group allocation from blimp.panel(), not wybor_probki.
    # Counted results (Slayer included) come from `hipoteza_formatu.py licz --zadania blimp`.
    "T01": dict(benchmark_id="blimp", task="blimp", family="blimp", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="nyu-mll/blimp", rewizja="877fba0801ffb7cbd8c39c1ff314a46f053f6036",
                parquet_hf="*/train-*.parquet", split="train", rodzaj="mc", klasy_stale=False, klastry="UID"),
    "T02": dict(benchmark_id="arc", task="arc_challenge", family="arc", language="EN",
                metric="acc_norm,none", unit="score", higher_is_better=True, klucz="acc_norm",
                repo="allenai/ai2_arc", rewizja="210d026faf9955653af8916fad021475a3f00453",
                nazwa_hf="ARC-Challenge", split="test", rodzaj="mc", klasy_stale=True, pole_id="id",
                trace=True),
    "T03": dict(benchmark_id="wikitext2", task="wikitext", family="wikitext2", language="EN",
                metric="byte_perplexity,none", unit="byte_ppl", higher_is_better=False,
                repo="EleutherAI/wikitext_document_level", rewizja="647234772b9554e208af6c826f23b99e3cac88c8",
                nazwa_hf="wikitext-2-raw-v1", split="test", rodzaj="rolling", probkowanie=False),
    "T04": dict(benchmark_id="multiblimp", task="multiblimp_pl", family="multiblimp", language="PL",
                metric="accuracy", unit="percent", higher_is_better=True,
                repo="jumelet/multiblimp", rewizja="de923efa8d2483d6b13364ee68e65308e990a991",
                plik_hf="pol/data.tsv", split="pol/data.tsv", rodzaj="mc", klasy_stale=False),
    "T05": dict(benchmark_id="hellaswag", task="hellaswag", family="hellaswag", language="EN",
                metric="acc_norm,none", unit="score", higher_is_better=True, klucz="acc_norm",
                repo="Rowan/hellaswag", rewizja="218ec52e09a7e7462a5400043bb9a69a41d06b76",
                split="validation", rodzaj="mc", klasy_stale=True, pole_id="ind"),
    "T06": dict(benchmark_id="piqa", task="piqa", family="piqa", language="EN",
                metric="acc_norm,none", unit="score", higher_is_better=True, klucz="acc_norm",
                repo="ybisk/piqa", rewizja="2e8ac2dffd59bac8c3c6714948f4c551a0848bb0",
                nazwa_hf="plain_text", split="validation", rodzaj="mc", klasy_stale=True,
                rewizja_parquet="142c51238b3ca2bc61e9a075913871b8b600e8e1"),
    "T08": dict(benchmark_id="openbookqa", task="openbookqa", family="openbookqa", language="EN",
                metric="acc_norm,none", unit="score", higher_is_better=True, klucz="acc_norm",
                repo="allenai/openbookqa", rewizja="388097ea7776314e93a529163e0fea805b8a6454",
                nazwa_hf="main", split="test", rodzaj="mc", klasy_stale=True, pole_id="id"),
    "T09": dict(benchmark_id="sciq", task="sciq", family="sciq", language="EN",
                metric="acc_norm,none", unit="score", higher_is_better=True, klucz="acc_norm",
                repo="allenai/sciq", rewizja="2c94ad3e1aafab77146f384e23536f97a4849815",
                split="test", rodzaj="mc", klasy_stale=False),
    "T10": dict(benchmark_id="boolq", task="boolq", family="boolq", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="aps/super_glue", rewizja="3de24cf8022e94f4ee4b9d55a6f539891524d646",
                nazwa_hf="boolq", split="validation", rodzaj="mc", klasy_stale=True, klastry="passage", pole_id="idx"),
    "T11": dict(benchmark_id="copa", task="copa", family="copa", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="aps/super_glue", rewizja="3de24cf8022e94f4ee4b9d55a6f539891524d646",
                nazwa_hf="copa", split="validation", rodzaj="mc", klasy_stale=True, pole_id="idx"),
    "T12": dict(benchmark_id="cb", task="cb", family="cb", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="aps/super_glue", rewizja="3de24cf8022e94f4ee4b9d55a6f539891524d646",
                nazwa_hf="cb", split="validation", rodzaj="mc", klasy_stale=True, pole_id="idx"),
    "T13": dict(benchmark_id="wic", task="wic", family="wic", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="aps/super_glue", rewizja="3de24cf8022e94f4ee4b9d55a6f539891524d646",
                nazwa_hf="wic", split="validation", rodzaj="mc", klasy_stale=True, pole_id="idx"),
    "T15": dict(benchmark_id="rte", task="sglue_rte", family="rte", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="aps/super_glue", rewizja="3de24cf8022e94f4ee4b9d55a6f539891524d646",
                nazwa_hf="rte", split="validation", rodzaj="mc", klasy_stale=True, pole_id="idx"),
    "T16": dict(benchmark_id="anli", task="anli_r3", family="anli", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="facebook/anli", rewizja="8e4813d81f46d313dac7892e1c28076917cfcdf9",
                nazwa_hf="plain_text", split="test_r3", rodzaj="mc", klasy_stale=True, pole_id="uid"),
    "T18": dict(benchmark_id="logiqa", task="logiqa", family="logiqa", language="EN",
                metric="acc_norm,none", unit="score", higher_is_better=True, klucz="acc_norm",
                repo="EleutherAI/logiqa", rewizja="c1eee1b2fd0ddc87777e36490f7ad54d0b97d141",
                nazwa_hf="logiqa", split="test", rodzaj="mc", klasy_stale=True,
                rewizja_parquet="fcd80241270118cd52c96dc517dc38804025f3f5"),
    "T19": dict(benchmark_id="mathqa", task="mathqa", family="mathqa", language="EN",
                metric="acc_norm,none", unit="score", higher_is_better=True, klucz="acc_norm",
                repo="allenai/math_qa", rewizja="c4f1cc784c04c4957b50c97858f23893b633eea6",
                nazwa_hf="default", split="test", rodzaj="mc", klasy_stale=True,
                rewizja_parquet="fafb9f7ee5b9ec4da9499f9c4177a4c91389f2d6"),
    "T20": dict(benchmark_id="prost", task="prost", family="prost", language="EN",
                metric="acc_norm,none", unit="score", higher_is_better=True, klucz="acc_norm",
                repo="corypaik/prost", rewizja="b3efebf08969fc19335ba894353316878b6fa493",
                nazwa_hf="default", split="test", rodzaj="mc", klasy_stale=True,
                rewizja_parquet="0e475b574d98e7d79de2064252dd2fb75bcaa0a8"),
    "T21": dict(benchmark_id="sst2", task="sst2", family="sst2", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="nyu-mll/glue", rewizja="bcdcba79d07bc864c1c254ccfcedcce55bcc9a8c",
                nazwa_hf="sst2", split="validation", rodzaj="mc", klasy_stale=True, pole_id="idx"),
    # Polish tasks (OpenPL fork @ 21d0ea9c, 5-shot). The task YAML is a copy of the fork's file under
    # benchmarks/<dir>/lm_eval_tasks/ (`yaml`, relative to benchmarks/); zadania.py pins the dataset revision.
    # The 5 demonstrations come from the demonstration bank (METODOLOGIA "Przykłady few-shot", ewaluuj.ustaw_bank),
    # not from the YAML's sampler.
    "T22": dict(benchmark_id="polemo2", task="polemo2_in_multiple_choice", family="polemo2", language="PL",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="allegro/klej-polemo2-in", rewizja="9843af31facd613eb091deaa4141df4331d4f918",
                split="test", rodzaj="mc", klasy_stale=True, shoty=5,
                yaml="polemo2/lm_eval_tasks/polemo2/polemo2_in_mc.yaml"),
    "T23": dict(benchmark_id="8tags", task="polish_8tags_multiple_choice", family="8tags", language="PL",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="sdadas/8tags", rewizja="82ddf9c0d06ffc982aeccf2473b7ce31f2167adf",
                split="test", rodzaj="mc", klasy_stale=True, shoty=5,
                yaml="8tags/lm_eval_tasks/polish_8tags/8tags_mc.yaml"),
    # Belebele has only a test split: the bank comes from it and its 5 documents are never scored (METODOLOGIA "Przykłady few-shot",
    # benchmarks/belebele-pl/README.md), instead of the fork's first 5 test documents.
    "T24": dict(benchmark_id="belebele", task="polish_belebele_mc", family="belebele", language="PL",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="facebook/belebele", rewizja="7899cdfa4e1e0d733fd77c848e2c273cb1d32be2",
                nazwa_hf="pol_Latn", split="test", rodzaj="mc", klasy_stale=True, shoty=5,
                yaml="belebele-pl/lm_eval_tasks/polish_belebele/belebele_mc.yaml"),
    "T25": dict(benchmark_id="dyk", task="polish_dyk_multiple_choice", family="dyk", language="PL",
                metric="f1,none", unit="score", higher_is_better=True, klucz="f1",
                repo="allegro/klej-dyk", rewizja="dd7c3c3bb336738c853ea17c64b85d876e6714a9",
                split="test", rodzaj="mc", klasy_stale=True, klastry="question", shoty=5,
                yaml="dyk/lm_eval_tasks/polish_dyk/dyk_mc.yaml"),
    "T26": dict(benchmark_id="ppc", task="polish_ppc_multiple_choice", family="ppc", language="PL",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="sdadas/ppc", rewizja="073012dc81efb47b0fd66b0ab48bf06ddb62f528",
                split="test", rodzaj="mc", klasy_stale=True, shoty=5,
                yaml="ppc/lm_eval_tasks/polish_ppc/ppc_mc.yaml"),
    "T27": dict(benchmark_id="psc", task="polish_psc_multiple_choice", family="psc", language="PL",
                metric="f1,none", unit="score", higher_is_better=True, klucz="f1",
                repo="allegro/klej-psc", rewizja="9585582aef37e7747ef174b0ec3b74855da8bad2",
                split="test", rodzaj="mc", klasy_stale=True, shoty=5,
                yaml="psc/lm_eval_tasks/polish_psc/psc_mc.yaml"),
    "T28": dict(benchmark_id="cbd", task="polish_cbd_multiple_choice", family="cbd", language="PL",
                metric="f1,none", unit="score", higher_is_better=True, klucz="f1",
                repo="ptaszynski/PolishCyberbullyingDataset", rewizja="be3b1236598a02eff6db05ea7ac386afaabc33e8",
                split="test", rodzaj="mc", klasy_stale=True, shoty=5,
                yaml="cbd/lm_eval_tasks/polish_cbd/cbd_mc.yaml"),
    "T29": dict(benchmark_id="klej_ner", task="polish_klej_ner_multiple_choice", family="klej_ner", language="PL",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="allegro/klej-nkjp-ner", rewizja="bfae4047738b985bc2ad533d339dd89c3f7de00d",
                split="test", rodzaj="mc", klasy_stale=True, shoty=5,
                yaml="klej-ner/lm_eval_tasks/polish_klej_ner/klej_ner_mc.yaml"),
    # PolQA and PoQuAD: loading-script repos, read from the pinned parquet conversion; `splity_dodatkowe` brings
    # the train split along as the few-shot source (the YAML's training_split).
    "T30": dict(benchmark_id="polqa", task="polish_polqa_open_book", family="polqa", language="PL",
                metric="levenshtein,none", unit="score", higher_is_better=True, klucz="levenshtein",
                repo="ipipan/polqa", rewizja="d78d036ef08ab3b9f4d85a2893f4d3a0c95a6f37",
                nazwa_hf="pairs", split="test", rodzaj="gen", klasy_stale=False, shoty=5,
                rewizja_parquet="0ba79f193fb3720dc0afa49d13c67abef786977f", splity_dodatkowe=("train",),
                yaml="polqa/lm_eval_tasks/polish_polqa/polqa_open_book.yaml"),
    "T31": dict(benchmark_id="poquad", task="polish_poquad_open_book", family="poquad", language="PL",
                metric="levenshtein,none", unit="score", higher_is_better=True, klucz="levenshtein",
                repo="clarin-pl/poquad", rewizja="a60f228d836fbbf990d11b4590c60b3e7f2aec2d",
                nazwa_hf="poquad", split="validation", rodzaj="gen", klasy_stale=False, shoty=5,
                rewizja_parquet="c76799436661006876ca3a2bf2ef2268b2179ac9", splity_dodatkowe=("train",),
                yaml="poquad/lm_eval_tasks/polish_poquad/poquad_open_book.yaml"),
    # T37 LLMzSzŁ is left out: it has no card with a prompt yet (benchmarks/llmzszl/README.md).
    "T40": dict(benchmark_id="race", task="race", family="race", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="EleutherAI/race", rewizja="66ca2e6374282f5e35b11559e87185db911a6900",
                nazwa_hf="high", split="test", rodzaj="mc", klasy_stale=True),
    "T44": dict(benchmark_id="pubmedqa", task="pubmedqa", family="pubmedqa", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="bigbio/pubmed_qa", rewizja="15578e80ef02c2c9636d33fdd7eb6b05b987ba60",
                nazwa_hf="pubmed_qa_labeled_fold0_source", split="test", rodzaj="mc", klasy_stale=True,
                parquet=True, rewizja_parquet="13a7d15476092370cbabb6475390e7e69b74d2f2"),
    "T45": dict(benchmark_id="medmcqa", task="medmcqa", family="medmcqa", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="openlifescienceai/medmcqa", rewizja="91c6572c454088bf71b679ad90aa8dffcd0d5868",
                split="validation", rodzaj="mc", klasy_stale=True, cloze=True, pole_id="id"),
    "T46": dict(benchmark_id="social_iqa", task="social_iqa", family="social_iqa", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="allenai/social_i_qa", rewizja="8835ceb9141d7896d9d968634a9b21ae440e3ec5",
                split="validation", rodzaj="mc", klasy_stale=True, parquet=True),
    "T48": dict(benchmark_id="paws", task="paws_en", family="paws", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="google-research-datasets/paws-x", rewizja="4cd8187c404bda33cb1f62b49b001115862acf37",
                nazwa_hf="en", split="test", rodzaj="mc", klasy_stale=True, pole_id="id"),
    # --- (c): config from the installed lm-eval YAML (`lm_eval` / `grupa`), dataset pinned here.
    # rodzaj: mc = own MC metrics from logliks; proba = lm-eval per-question metric `klucz` of filter `filtr`;
    # korpus = corpus metric over (gold, pred) pairs. baza: how the constant-answer baseline is computed
    # (ewaluuj.bazy_proby). shots > 0 with a separate few-shot split: demonstrations from the hash-selected
    # disjoint bank (METODOLOGIA "Przykłady few-shot", ewaluuj.uzyj_banku); fixed source shots (BBH) stay as published.
    "T07": dict(benchmark_id="winogrande", task="winogrande", family="winogrande", language="EN",
                metric="acc,none", unit="score", higher_is_better=True, lm_eval="winogrande",
                repo="allenai/winogrande", rewizja="01e74176c63542e6b0bcb004dcdea22d94fb67b5",
                nazwa_hf="winogrande_xl", split="validation", rodzaj="mc", klasy_stale=True, klastry="pary_winogrande"),
    "T14": dict(benchmark_id="wsc273", task="wsc273", family="wsc273", language="EN",
                metric="acc,none", unit="score", higher_is_better=True, lm_eval="wsc273",
                repo="ErnestSDavis/winograd_wsc", rewizja="8052c534a4cecd8328c0bc879f6a5aa07404c4da",
                nazwa_hf="wsc273", split="test", rodzaj="mc", klasy_stale=True, klastry="schematy_wsc273",
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
    # --- T51-T53: settings from the card (ORIGINAL.md of each directory).
    # ARC-Easy: lm-eval arc_easy (cloze, 0-shot), decision metric acc, not acc_norm as in ARC-Challenge.
    "T51": dict(benchmark_id="arc_easy", task="arc_easy", family="arc", language="EN",
                metric="acc,none", unit="score", higher_is_better=True,
                repo="allenai/ai2_arc", rewizja="210d026faf9955653af8916fad021475a3f00453",
                nazwa_hf="ARC-Easy", split="test", rodzaj="mc", klasy_stale=True, pole_id="id"),
    # BLiMP Supplement: not on HF and not in lm-eval; the authors' 5 files from OSF, each pinned by SHA-256 (OSF
    # has no revision), read as the authors' `json` split `train`. Prompt as BLiMP; decision metric = unweighted
    # mean of the 5 subtask accuracies (`wagi="rowne"`).
    "T52": dict(benchmark_id="blimp_supplement", task="blimp_supplement", family="blimp_supplement", language="EN",
                metric="acc,none", unit="score", higher_is_better=True, repo="osf.io/ad7qg",
                pliki_osf={
                    "hypernym": ("jpuax", "4f8a46b377aa3c84275f3f812b14ed3266d0354aa13be9c94610eb287d17659f"),
                    "qa_congruence_easy": ("egr56", "25c94dc5ef2ad7d8012a9695100e525a424135c94650e0dba1f74dbc10d44887"),
                    "qa_congruence_tricky": ("yt2jg", "8df41ef003adb0ca43ba6b286cf406925f3f766c5a59b1c9a96e05326c0a2334"),
                    "subject_aux_inversion": ("wzft7", "2a246a1ac90dd79d68e4c10e3f5ba81fd4a8563e385193a60c658c671aabb865"),
                    "turn_taking": ("2g6jp", "a350fdbd8669e9f84e2608503ed94af1cfe5bf29ceda9a3e0a2c3efc9665c9db")},
                split="train", rodzaj="mc", klasy_stale=False, wagi="rowne"),
    # EWoK: own code (`kod`), not lm-eval; the run calls `benchmarks/ewok/ewok.py przebieg` (rule `authors`).
    "T53": dict(benchmark_id="ewok", task="ewok", family="ewok", language="EN",
                metric="ewok", unit="score", higher_is_better=True,
                repo="ewok-core/ewok-core-1.0", rewizja="34d912a608066c92e2990a0328ffc3bd9a716042",
                split="test", rodzaj="kod", kod="benchmarks/ewok/ewok.py"),
}

# Tasks the run evaluates through common/ewaluuj.py (lm-eval); the rest run their own `kod` command.
ZADANIA_EWALUUJ = [t for t, m in ZADANIA.items() if not m.get("kod")]

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


OSF_POBIERZ = "https://osf.io/download/{}/"


def pobierz_osf(guid, sha256):
    """OSF file `guid` in the cache ($OSF_CACHE, default ~/.cache/slayer-osf/<sha256>.jsonl), downloaded once; bytes
    with another SHA-256 are an error, never a result (OSF has no revision to pin)."""
    import hashlib
    import os
    import requests  # GOTCHA: not urllib, which on macOS python.org builds has no CA bundle (CERTIFICATE_VERIFY_FAILED)
    p = Path(os.environ.get("OSF_CACHE", Path.home() / ".cache" / "slayer-osf")) / f"{sha256}.jsonl"
    if not p.exists():
        r = requests.get(OSF_POBIERZ.format(guid), timeout=300)
        r.raise_for_status()
        dane = r.content
        if hashlib.sha256(dane).hexdigest() != sha256:
            raise ValueError(f"OSF {guid}: SHA-256 {hashlib.sha256(dane).hexdigest()} != {sha256}")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.with_suffix(".tmp").write_bytes(dane)
        p.with_suffix(".tmp").replace(p)
    return p


def dane_osf(osf=None, sha256=None, **_):
    """`custom_dataset` of an OSF-pinned task: the file as the authors' `json` split `train`."""
    import datasets
    return datasets.DatasetDict({"train": datasets.load_dataset("json", data_files=str(pobierz_osf(osf, sha256)),
                                                                split="train")})


def _zrodlo_osf(meta, zrodlo, podtest):
    if zrodlo == "lokalne":
        return {"dataset_path": "json", "dataset_name": None,
                "dataset_kwargs": {"data_files": {"test": str(DANE_TESTOWE / f"{podtest}.jsonl")}}, "test_split": "test"}
    guid, sha = meta["pliki_osf"][podtest]
    return {"dataset_path": "json", "dataset_name": None, "custom_dataset": dane_osf,
            "dataset_kwargs": {"osf": guid, "sha256": sha}, "test_split": meta["split"]}


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
        def sciezka(split):
            return f"hf://datasets/{meta['repo']}@{meta['rewizja_parquet']}/{meta['nazwa_hf']}/{split}/*.parquet"
        pliki = {"test": sciezka(meta["split"]), **{s: sciezka(s) for s in meta.get("splity_dodatkowe", ())}}
        return {"dataset_path": "parquet", "dataset_name": None,
                "dataset_kwargs": {"data_files": pliki}, "test_split": "test"}
    if meta.get("parquet"):
        # Repo z loading scriptem: czytamy konwersję parquet zamiast uruchamiać skrypt;
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


def zapewnij_squad_metrics():
    """GOTCHA: CoQA (T41) i ReCoRD (T50) lm-eval importują `transformers.data.metrics.squad_metrics`, którego nie ma
    w transformers 5 (środowisko `new`). Wtedy rejestrujemy moduł z funkcjami transformers 4.57.6 (lock), które
    lm-eval woła. Usuń, gdy lm-eval przestanie go importować."""
    try:
        import transformers.data.metrics.squad_metrics  # noqa: F401
        return
    except ImportError:
        pass
    import collections
    import types
    import transformers.data

    def get_tokens(s):
        return M.squad_normalizuj(s).split() if s else []

    def compute_exact(a_gold, a_pred):
        return int(M.squad_normalizuj(a_gold) == M.squad_normalizuj(a_pred))

    def compute_f1(a_gold, a_pred):
        zlote, pred = get_tokens(a_gold), get_tokens(a_pred)
        wspolne = sum((collections.Counter(zlote) & collections.Counter(pred)).values())
        if not zlote or not pred:
            return int(zlote == pred)
        if wspolne == 0:
            return 0
        precyzja, czulosc = wspolne / len(pred), wspolne / len(zlote)
        return 2 * precyzja * czulosc / (precyzja + czulosc)

    metryki = types.ModuleType("transformers.data.metrics")
    squad = types.ModuleType("transformers.data.metrics.squad_metrics")
    squad.normalize_answer, squad.get_tokens = M.squad_normalizuj, get_tokens
    squad.compute_exact, squad.compute_f1 = compute_exact, compute_f1
    metryki.squad_metrics = squad
    transformers.data.metrics = metryki
    sys.modules.update({metryki.__name__: metryki, squad.__name__: squad})


def _yaml(nazwa):
    """Config zadania z YAML-a zainstalowanego lm-eval (`!function` rozwiązane, `include` scalone), świeża kopia.

    GOTCHA: 0.4.9.1 (lock) daje go przez `TaskManager._get_config`, 0.4.13 (środowisko `new` przebiegu) nie ma tej
    metody: indeks trzyma `Entry.yaml_path`, a scala `tasks._yaml_loader.load_yaml`."""
    if not _MENEDZER:
        from lm_eval.tasks import TaskManager
        zapewnij_squad_metrics()
        _MENEDZER.append(TaskManager())
    tm = _MENEDZER[0]
    if hasattr(tm, "_get_config"):
        return dict(tm._get_config(nazwa))
    from lm_eval.tasks._yaml_loader import load_yaml
    wpis = tm.task_index.get(nazwa)
    if wpis is None or wpis.yaml_path is None:
        raise KeyError(f"lm-eval {lm_eval.__version__}: brak YAML-a zadania {nazwa}")
    return dict(load_yaml(wpis.yaml_path, resolve_func=True))


def czlonkowie_grupy(grupa):
    """Podtesty grupy lm-eval; MMLU to grupa grup po tagach, więc członków daje katalog `mmlu/default`."""
    if grupa == "mmlu":
        return sorted(p.stem for p in (ZADANIA_LM_EVAL / "mmlu" / "default").glob("mmlu_*.yaml"))
    return list(_yaml(grupa)["task"])


def _zrodlo_yaml(task_id, meta, zrodlo, nazwa, cfg):
    """Pola datasetu configu z YAML-a. Lokalnie: `tests/data/<podtest>.jsonl`, bank demonstracji z
    `<podtest>_demo.jsonl`. Z HF: repo i rewizja wpisu ZADANIA, podzbiór grupy z YAML-a podtestu, splity YAML-a poza testowym."""
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
    """TruthfulQA MC2 w wersji 6d2abda4 (METODOLOGIA „Wersja lm-eval”); 0.4.9.1 przepisało `process_results_mc2`."""
    return {"acc": M.mc2([r[0] for r in results], doc["mc2_targets"]["labels"])}


def squad2_klasa(cfg):
    """SQuAD 2.0: legacy klasa lm-eval (prompt, żądania, `until: \\n`) z 6d2abda4; podmienione są
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
    """Lista (wariant, config) dla jednego zadania ZADANIA. Pierwszy wariant („space") liczy metrykę decyzyjną."""
    warianty = _konfiguracje(task_id, zrodlo)
    for _, cfg in warianty:
        cfg["task_alias"] = cfg["task"]  # tabela wyników lm-eval wywraca się na aliasie None
    return warianty


def _konfiguracje(task_id, zrodlo):
    meta = ZADANIA[task_id]
    if meta.get("kod"):
        raise KeyError(f"{task_id}: own code {meta['kod']}, not lm-eval; tools/przebieg_centralny.sh runs it directly")
    if meta.get("pliki_osf"):
        # BLiMP Supplement: the authors' _template_yaml (empty context, " " + sentence, gold = good sentence, acc)
        return [("space", {"output_type": "multiple_choice", "num_fewshot": 0, "metric_list": [METRYKI_MC[0]],
                           "metadata": {"version": 1.0, "task_id": task_id, "czlonek": p},
                           **_zrodlo_osf(meta, zrodlo, p), "task": f"slayer_{meta['task']}_{p}", "doc_to_text": "",
                           "target_delimiter": " ", "doc_to_choice": "{{[sentence_good, sentence_bad]}}",
                           "doc_to_target": 0})
                for p in meta["pliki_osf"]]
    baza = {"output_type": "multiple_choice", "num_fewshot": 0, "metric_list": METRYKI_MC,
            "metadata": {"version": 1.0, "task_id": task_id}, **_zrodlo(task_id, meta, zrodlo)}
    t = meta["task"]
    if meta.get("yaml"):
        return [("space", _konfiguracja_yaml(meta, baza))]
    if t == "blimp":
        # lm-eval blimp: empty context, default delimiter " ", gold = good sentence; metric acc only
        return [("space", {**baza, "task": "slayer_blimp", "doc_to_text": "", "target_delimiter": " ",
                           "doc_to_choice": "{{[sentence_good, sentence_bad]}}", "doc_to_target": 0,
                           "metric_list": [METRYKI_MC[0]]})]
    if t == "arc_easy":
        # lm-eval arc_easy.yaml (same blob in 6d2abda4 and 0.4.9.1, card "Znane rozbieżności"), rewritten here
        return [("space", {**baza, "task": "slayer_arc_easy", "doc_to_text": "Question: {{question}}\nAnswer:",
                           "doc_to_choice": "{{choices.text}}", "doc_to_target": arc_target})]
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
    # T05-T21, T40, T48: prompts of the lm-eval 6d2abda4 YAMLs (METODOLOGIA "Wersja lm-eval"), rewritten here
    if t == "hellaswag":
        hs = _modul_lm_eval("hellaswag/utils.py")
        return [("space", {**baza, "task": "slayer_hellaswag", "process_docs": hs.process_docs,
                           "doc_to_text": "{{query}}", "doc_to_target": "{{label}}", "doc_to_choice": "choices"})]
    if t == "piqa":
        return [("space", {**baza, "task": "slayer_piqa", "doc_to_text": "Question: {{goal}}\nAnswer:",
                           "doc_to_target": "label", "doc_to_choice": "{{[sol1, sol2]}}"})]
    if t == "openbookqa":
        return [("space", {**baza, "task": "slayer_openbookqa", "doc_to_text": "question_stem",
                           "doc_to_target": "{{choices.label.index(answerKey.lstrip())}}",
                           "doc_to_choice": "{{choices.text}}"})]
    if t == "sciq":
        return [("space", {**baza, "task": "slayer_sciq",
                           "doc_to_text": "{{support.lstrip()}}\nQuestion: {{question}}\nAnswer:",
                           "doc_to_target": 3, "doc_to_choice": "{{[distractor1, distractor2, distractor3, correct_answer]}}"})]
    if t == "boolq":
        return [("space", {**baza, "task": "slayer_boolq", "doc_to_text": "{{passage}}\nQuestion: {{question}}?\nAnswer:",
                           "doc_to_target": "label", "doc_to_choice": ["no", "yes"]})]
    if t == "copa":
        cp = _modul_lm_eval("super_glue/copa/utils.py")
        return [("space", {**baza, "task": "slayer_copa", "doc_to_text": cp.doc_to_text,
                           "doc_to_target": cp.doc_to_target, "doc_to_choice": cp.doc_to_choice})]
    if t == "cb":
        return [("space", {**baza, "task": "slayer_cb",
                           "doc_to_text": "{{premise}}\nQuestion: {{hypothesis}}. True, False, or Neither?\nAnswer:",
                           "doc_to_target": "label", "doc_to_choice": ["True", "False", "Neither"]})]
    if t == "wic":
        return [("space", {**baza, "task": "slayer_wic",
                           "doc_to_text": "Sentence 1: {{sentence1}}\nSentence 2: {{sentence2}}\nQuestion: Is the word "
                                          "'{{sentence1[start1:end1]}}' used in the same way in the two sentences above?\nAnswer:",
                           "doc_to_target": "label", "doc_to_choice": ["no", "yes"]})]
    if t == "sglue_rte":
        return [("space", {**baza, "task": "slayer_rte",
                           "doc_to_text": "{{premise}}\nQuestion: {{hypothesis}} True or False?\nAnswer:",
                           "doc_to_target": "label", "doc_to_choice": ["True", "False"]})]
    if t == "anli_r3":
        return [("space", {**baza, "task": "slayer_anli_r3",
                           "doc_to_text": "{{premise}}\nQuestion: {{hypothesis}} True, False, or Neither?\nAnswer:",
                           "doc_to_target": "{{['True', 'Neither', 'False'][label]}}",
                           "doc_to_choice": ["True", "Neither", "False"]})]
    if t == "logiqa":
        lq = _modul_lm_eval("logiqa/utils_logiqa.py")
        return [("space", {**baza, "task": "slayer_logiqa", "doc_to_text": lq.doc_to_text,
                           "doc_to_target": lq.doc_to_target, "doc_to_choice": "{{options}}"})]
    if t == "mathqa":
        mq = _modul_lm_eval("mathqa/utils.py")
        return [("space", {**baza, "task": "slayer_mathqa", "doc_to_text": "Question: {{Problem}}\nAnswer:",
                           "doc_to_target": "{{['a', 'b', 'c', 'd', 'e'].index(correct)}}",
                           "doc_to_choice": mq.doc_to_choice})]
    if t == "prost":
        return [("space", {**baza, "task": "slayer_prost", "doc_to_text": "{{context}}\nQuestion: {{ex_question}}\nAnswer:",
                           "doc_to_target": "label", "doc_to_choice": "{{[A, B, C, D]}}"})]
    if t == "sst2":
        return [("space", {**baza, "task": "slayer_sst2",
                           "doc_to_text": "{{sentence}}\nQuestion: Is this sentence positive or negative?\nAnswer:",
                           "doc_to_target": "label", "doc_to_choice": ["negative", "positive"]})]
    if t == "race":
        rc = _modul_lm_eval("race/lm_eval_tasks/preprocess_race.py", BENCHMARKI)
        return [("space", {**baza, "task": "slayer_race", "doc_to_text": rc.doc_to_text,
                           "doc_to_target": rc.doc_to_target, "doc_to_choice": rc.doc_to_choice})]
    if t == "paws_en":
        # 6d2abda4: empty context, default " " delimiter, no process_docs; 0.4.9.1 adds
        # process_docs_paraphrases and target_delimiter "", which changes the prompt
        return [("space", {**baza, "task": "slayer_paws_en", "doc_to_text": "", "doc_to_target": "label",
                           "doc_to_choice": '{{[sentence1+", right? No, "+sentence2, sentence1+", right? Yes, "+sentence2]}}'})]
    if t == "squadv2":
        # metadata.klasa: ewaluuj.zbuduj_zadania builds squad2_klasa(cfg); the dict stays a valid TaskConfig
        return [("space", {"task": "slayer_squadv2", "output_type": "generate_until",
                           "metric_list": [{"metric": "f1", "aggregation": "mean", "higher_is_better": True}],
                           "metadata": {"task_id": task_id, "czlonek": t, "klasa": "squadv2"},
                           **_zrodlo(task_id, meta, zrodlo)})]
    if t == "ifeval":
        from langdetect import DetectorFactory
        DetectorFactory.seed = 0  # language instructions reproducible (METODOLOGIA, seeds)
    nadpisz = {"mmlu": {"metric_list": METRYKI_MC}, "truthfulqa_mc2": {"process_results": mc2_wyniki}}.get(t, {})
    if meta.get("grupa"):
        return [("space", _z_lm_eval(task_id, meta, zrodlo, m, **nadpisz)) for m in czlonkowie_grupy(meta["grupa"])]
    if meta.get("lm_eval"):
        return [("space", _z_lm_eval(task_id, meta, zrodlo, meta["lm_eval"], **nadpisz))]
    raise KeyError(task_id)


def _konfiguracja_yaml(meta, baza):
    """Config from a copied task YAML (T22-T31): its prompt and metrics, our pinned source and shot count."""
    cfg = wczytaj_yaml(BENCHMARKI / meta["yaml"])
    cfg.pop("group", None)  # polemo2 YAML: a group key would make lm-eval build a group, not one task
    zrodlo = {k: v for k, v in baza.items() if k not in ("output_type", "metric_list", "num_fewshot")}
    wynik = {**cfg, **zrodlo, "task": f"slayer_{meta['task']}", "num_fewshot": meta.get("shoty", 0)}
    if cfg["output_type"] == "multiple_choice":
        wynik["metric_list"] = cfg["metric_list"] + [m for m in METRYKI_MC if m["metric"] == "acc_mutual_info"]
    if meta.get("rewizja_parquet"):
        wynik["validation_split"] = None  # the parquet data_files carry only test and `splity_dodatkowe`
    return wynik
