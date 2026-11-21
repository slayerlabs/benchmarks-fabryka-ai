"""The runner against the research pipeline it is ported from, and end to end on a fake model.

Needs the `eval` extra (lm-eval); without it the module is skipped. No network, GPU, weights, or real benchmark data:
every document below is synthetic, in the record format of its dataset.

- Requests: for every implemented benchmark, the requests lm-eval builds from the runner's configuration equal those
  it builds from research/common/zadania.py, on the same documents.
- Scoring: every scoring function gives the research functions' numbers on the same inputs.
- End to end: a fake model whose log-likelihood of a continuation is minus its length runs through evaluation,
  scoring, and the run directory, which must validate; failures are states, never scores.
"""

import dataclasses
import importlib
import importlib.util
import json
import random
import sys
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("lm_eval", reason="needs the eval extra: uv sync --extra eval")

from lm_eval.api.model import LM

from codesota import catalog
from codesota.results import validate_run
from codesota.runner import execute, models, scoring, tasks

REPO = Path(__file__).resolve().parents[2]
RESEARCH = REPO / "research"

ARC: list[dict[str, Any]] = [
    {
        "id": "syn-arc-1",
        "question": "Which gas do plants take in?",
        "choices": {"text": ["oxygen", "carbon dioxide", "neon", "helium"], "label": ["A", "B", "C", "D"]},
        "answerKey": "B",
    },
    {
        "id": "syn-arc-2",
        "question": "What melts ice?",
        "choices": {"text": ["heat", "a cold wind", "darkness"], "label": ["1", "2", "3"]},
        "answerKey": "1",
    },
    {
        "id": "syn-arc-3",
        "question": "Which is a planet?",
        "choices": {"text": ["the Sun", "Mars", "the Moon", "a comet"], "label": ["A", "B", "C", "D"]},
        "answerKey": "B",
    },
]
DOCS: dict[str, list[dict[str, Any]]] = {
    "arc-easy": ARC,
    "arc-challenge": ARC,
    "hellaswag": [
        {
            "ind": 7,
            "activity_label": "Cooking [title]",
            "ctx_a": "Someone",
            "ctx_b": "chops",
            "endings": ["[header] onions", "a chair.", "the sky.", "salt"],
            "label": "0",
        },
        {
            "ind": 9,
            "activity_label": "Cycling",
            "ctx_a": "A man",
            "ctx_b": "rides",
            "endings": ["home.", "a b.", "c", "d"],
            "label": "1",
        },
    ],
    "piqa": [
        {"goal": "Open a jar", "sol1": "Twist the lid.", "sol2": "Paint the lid.", "label": 0},
        {"goal": "Dry wet hands", "sol1": "Use a towel", "sol2": "Use water", "label": 0},
    ],
    "winogrande": [
        {
            "sentence": "The cup did not fit in the box because _ was too big.",
            "option1": "cup",
            "option2": "box",
            "answer": "1",
        },
        {
            "sentence": "The cup did not fit in the box because _ was too small.",
            "option1": "cup",
            "option2": "box",
            "answer": "2",
        },
        {"sentence": "Anna thanked Ola because _ had helped.", "option1": "Anna", "option2": "Ola", "answer": "2"},
    ],
    "wsc273": [
        {
            "text": "The councilmen refused the crowd a permit because they feared violence.",
            "pronoun": "they",
            "pronoun_loc": 56,
            "quote": "they feared violence",
            "quote_loc": 56,
            "options": ["The councilmen", "The crowd"],
            "label": 0,
            "source": "synthetic",
        },
        {
            "text": "The councilmen refused the crowd a permit because they wanted violence.",
            "pronoun": "they",
            "pronoun_loc": 56,
            "quote": "they wanted violence",
            "quote_loc": 56,
            "options": ["The councilmen", "The crowd"],
            "label": 1,
            "source": "synthetic",
        },
    ],
    "lambada": [{"text": "she opened the door and saw the cat"}, {"text": "he poured a cup of hot tea"}],
    "mathqa": [
        {"Problem": "what is 2 + 2 ?", "options": "a ) 3 , b ) 4 , c ) 5 , d ) 6 , e ) 7", "correct": "b"},
        {"Problem": "what is 3 * 3 ?", "options": "a ) 9 , b ) 6 , c ) 12 , d ) 3 , e ) 1", "correct": "a"},
    ],
    "pubmedqa": [
        {
            "QUESTION": "Does exercise lower heart rate?",
            "CONTEXTS": ["A cohort trained.", "Rate fell."],
            "LONG_ANSWER": "Yes.",
            "final_decision": "yes",
        },
        {
            "QUESTION": "Does drug X cure colds?",
            "CONTEXTS": ["No difference was seen."],
            "LONG_ANSWER": "No.",
            "final_decision": "no",
        },
    ],
    "medmcqa": [
        {
            "id": "syn-med-1",
            "question": "Which organ makes insulin?",
            "opa": "Liver",
            "opb": "Pancreas",
            "opc": "Kidney",
            "opd": "Lung",
            "cop": 1,
        },
        {
            "id": "syn-med-2",
            "question": "Body temperature in Celsius?",
            "opa": "37",
            "opb": "30",
            "opc": "42",
            "opd": "25",
            "cop": 0,
        },
    ],
    "social-iqa": [
        {
            "context": "Kasia walked home in the rain.",
            "question": "How would Kasia feel?",
            "answerA": "wet",
            "answerB": "dry",
            "answerC": "sunburned",
            "label": "1",
        },
        {
            "context": "Tomek helped carry boxes.",
            "question": "What will the neighbor do?",
            "answerA": "ignore him",
            "answerB": "thank him",
            "answerC": "sleep",
            "label": "2",
        },
    ],
    "multiblimp-pl": [
        {"sen": "Kot spi na kanapie.", "wrong_sen": "Kot spia na kanapie.", "phenomenon": "SV-#"},
        {"sen": "Ja czytam.", "wrong_sen": "Ja czyta.", "phenomenon": "SV-P"},
    ],
    "wikitext-2": [
        {"page": " = Synthetic Page = \n The river flows past the old town . It was built in the 14th century . \n"},
        {"page": " = Another Page = \n The company employs 2 @,@ 000 people . \n"},
    ],
}


def local(path: Path) -> dict[str, Any]:
    return {
        "dataset_path": "json",
        "dataset_name": None,
        "dataset_kwargs": {"data_files": {"test": str(path)}},
        "test_split": "test",
        "validation_split": None,
        "training_split": None,
        "fewshot_split": None,
    }


def write_docs(tmp_path: Path, benchmark_id: str) -> Path:
    path = tmp_path / f"{benchmark_id}.jsonl"
    path.write_text("".join(json.dumps(d) + "\n" for d in DOCS[benchmark_id]), encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def research() -> dict[str, Any]:
    """The research pipeline's modules, imported from the repository as the research tests import them."""
    for p in (RESEARCH / "common", RESEARCH / "tools"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    return {name: importlib.import_module(name) for name in ("zadania", "metryki", "statystyka", "ewaluuj")}


def requests(task: Any) -> list[tuple[int, int, tuple[Any, ...]]]:
    task.build_all_requests(rank=0, world_size=1)
    return sorted((i.doc_id, i.idx, tuple(i.arguments)) for i in task.instances)


IMPLEMENTED = [b for b in catalog.IMPLEMENTED]


def test_every_implemented_benchmark_has_a_configuration_and_test_documents() -> None:
    assert {b.id for b in IMPLEMENTED} == tasks.implemented_ids() == set(DOCS)


@pytest.mark.parametrize("benchmark", IMPLEMENTED, ids=lambda b: b.id)
def test_data_source_matches_research(benchmark: catalog.Benchmark, research: dict[str, Any]) -> None:
    z = research["zadania"]
    assert benchmark.dataset is not None and benchmark.legacy_id is not None
    meta = z.ZADANIA[benchmark.legacy_id]
    theirs = z._zrodlo(benchmark.legacy_id, meta, "hf")
    assert tasks.data_fields(benchmark.dataset) == theirs
    assert (meta["repo"], meta["rewizja"], meta["split"]) == (
        benchmark.dataset.repo,
        benchmark.dataset.revision,
        benchmark.dataset.split,
    )
    assert meta.get("pole_id") == (benchmark.dataset.id_field or benchmark.dataset.research_id_field)


@pytest.mark.parametrize("benchmark", IMPLEMENTED, ids=lambda b: b.id)
def test_requests_match_research(benchmark: catalog.Benchmark, research: dict[str, Any], tmp_path: Path) -> None:
    path = write_docs(tmp_path, benchmark.id)
    ours = execute.build_task(tasks.task_config(benchmark, local(path)))
    variant, config = research["zadania"].konfiguracje(benchmark.legacy_id, "hf")[0]
    assert variant == "space"
    config.update(local(path))
    theirs = research["ewaluuj"].zbuduj_zadania([config])[0]
    mine = requests(ours)
    # The research configuration adds acc_mutual_info, whose unconditional requests follow the k conditional ones
    # of each document (idx >= k); the runner leaves them out (runner/tasks.py).
    per_doc = {d: max(i for dd, i, _ in mine if dd == d) for d, _, _ in mine}
    assert mine == [r for r in requests(theirs) if r[1] <= per_doc[r[0]]]
    assert ours.OUTPUT_TYPE == theirs.OUTPUT_TYPE
    assert ours.config.num_fewshot == theirs.config.num_fewshot == 0
    for doc in ours.eval_docs:
        assert ours.doc_to_target(doc) == theirs.doc_to_target(doc)


def test_scoring_matches_research(research: dict[str, Any]) -> None:
    m, s, e = research["metryki"], research["statystyka"], research["ewaluuj"]
    rng = random.Random(0)
    values = [float(rng.random() < 0.6) for _ in range(200)]
    clusters = [i // 2 if i < 120 else i for i in range(200)]
    golds = [rng.randrange(4) for _ in range(200)]

    ours, theirs = scoring.mean_with_uncertainty(values), m.srednia_z_niepewnoscia(values)
    assert {k: ours[k] for k in ("value", "n", "se", "ci95")} == theirs
    ours, theirs = scoring.clustered_mean(values, clusters), m.srednia_klastrowa(values, clusters)
    assert [ours[k] for k in ("value", "n", "se", "ci95", "se_per_question", "k", "df")] == [
        theirs[k] for k in ("value", "n", "se", "ci95", "se_a", "k", "df")
    ]
    lls, words, nbytes = (
        [-rng.uniform(50, 500) for _ in range(30)],
        [rng.randint(20, 90) for _ in range(30)],
        [rng.randint(100, 600) for _ in range(30)],
    )
    ours_ppl, theirs_ppl = scoring.perplexity(lls, words, nbytes), m.perplexity(lls, words, nbytes)
    for name in ("word_perplexity", "byte_perplexity", "bits_per_byte"):
        assert {k: ours_ppl[name][k] for k in ("value", "n", "se", "ci95")} == theirs_ppl[name]

    samples = []
    for g in golds:
        k = 4
        samples.append(
            {
                "filtered_resps": [(-rng.uniform(1, 9), False) for _ in range(k)],
                "arguments": [("ctx", " " + "x" * rng.randint(1, 12)) for _ in range(k)],
                "target": g,
            }
        )
    outcomes = [scoring.multiple_choice_outcome(x) for x in samples]
    references = [m.oceny_mc(x, z_pmi=False) for x in samples]
    for o, r in zip(outcomes, references, strict=True):
        assert {k: o[k] for k in ("k", "gold", "pred_acc", "pred_acc_norm", "acc", "acc_norm")} == {
            k: r[k] for k in ("k", "gold", "pred_acc", "pred_acc_norm", "acc", "acc_norm")
        }
        assert o["bpb_correct"] == r["bpb_poprawnej"]
    for fixed in (True, False):
        assert scoring.choice_baselines(outcomes, fixed, "acc") == m.bazy_mc(references, fixed, "acc")
    accs = [o["acc"] for o in outcomes]
    for cl in (None, clusters):
        main = scoring.mean_with_uncertainty(accs) if cl is None else scoring.clustered_mean(accs, cl)
        theirs_main = m.srednia_z_niepewnoscia(accs) if cl is None else m.srednia_klastrowa(accs, cl)
        for bases in ({"chance_value": 0.25, "majority_value": 0.31}, {"chance_value": 0.25, "majority_value": None}):
            ours_b = scoring.against_baseline(accs, golds, main, bases, cl)
            theirs_b = e.wobec_b(accs, golds, theirs_main, bases, cl)
            assert [ours_b.get(k) for k in ("b", "difference", "se", "z", "t", "df")] == [
                theirs_b.get(k) for k in ("b", "roznica", "se", "z", "t", "df")
            ]
            names = {
                "pewne": "strong",
                "prawdopodobne": "probable",
                "szum": "noise",
                "nierozstrzygalne": "inconclusive",
            }
            assert ours_b["verdict"] == names[theirs_b["werdykt"]]
    for t, df in ((0.5, 3), (2.4, 10), (-3.7, 40), (1.0, 1)):
        assert scoring.p_t(t, df) == s.p_t(t, df)
    # Cloze baseline: the share of the most common target word, compared after stripping spaces.
    assert scoring.cloze_baseline([" cat", "cat", "dog", " tea"])["majority_value"] == 0.5


def test_cluster_rules_match_research() -> None:
    def load(path: Path, name: str) -> Any:
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    winogrande = load(RESEARCH / "benchmarks" / "winogrande" / "przelicz.py", "research_winogrande")
    docs = DOCS["winogrande"] * 3
    assert scoring.winogrande_pairs(docs) == winogrande.klastry_z_opcji([(d["option1"], d["option2"]) for d in docs])
    wsc = load(RESEARCH / "benchmarks" / "wsc273" / "wsc273.py", "research_wsc273")
    docs = [*DOCS["wsc273"], {"text": "A completely different sentence about the sea."}]
    assert scoring.wsc273_schemas(docs) == wsc.schematy(docs) == [0, 0, 1]


# --- golden checks of one question ---


def mc_sample(lls: list[float], continuations: list[str], target: Any) -> dict[str, Any]:
    return {
        "filtered_resps": [(x, False) for x in lls],
        "arguments": [("Q:", c) for c in continuations],
        "target": target,
    }


def test_correct_answer_scores_as_correct_and_wrong_as_wrong() -> None:
    right = scoring.multiple_choice_outcome(mc_sample([-1.0, -5.0, -6.0], [" a", " b", " c"], 0))
    wrong = scoring.multiple_choice_outcome(mc_sample([-9.0, -5.0, -6.0], [" a", " b", " c"], 0))
    assert (right["acc"], right["acc_norm"]) == (1.0, 1.0)
    assert (wrong["acc"], wrong["acc_norm"]) == (0.0, 0.0)


def test_acc_norm_divides_by_the_option_length() -> None:
    # " long answer" has the highest total log-likelihood per character, " no" the highest total.
    o = scoring.multiple_choice_outcome(mc_sample([-3.0, -6.0], [" no", " long answer"], 1))
    assert (o["pred_acc"], o["pred_acc_norm"], o["acc"], o["acc_norm"]) == (0, 1, 0.0, 1.0)


def test_text_target_is_matched_to_its_option() -> None:
    o = scoring.multiple_choice_outcome(mc_sample([-3.0, -1.0, -2.0], [" yes", " no", " maybe"], "no"))
    assert (o["gold"], o["acc"]) == (1, 1.0)


# --- end to end ---


class FakeLM(LM):  # type: ignore[misc]  # lm-eval's LM is untyped
    """Log-likelihood of a continuation = minus its length in characters: the shortest option wins acc, and every
    option ties on acc_norm (-1 per character), where the first wins."""

    def __init__(self, max_length: int = 2048, fail: bool = False, pair_extra: int = 0) -> None:
        super().__init__()
        self.max_length, self.fail, self.prefix_token_id = max_length, fail, 0
        self.pair_extra = pair_extra  # extra tokens of the pair encoding: a tokenizer that splits a pair differently
        self.tokenizer = None

    def tok_encode(self, text: str) -> list[int]:
        return list(text.encode("utf-8"))

    def _encode_pair(self, context: str, continuation: str) -> tuple[list[int], list[int]]:
        return [1] * self.pair_extra + self.tok_encode(context), self.tok_encode(continuation)

    def loglikelihood(self, reqs: list[Any], disable_tqdm: bool = False) -> list[tuple[float, bool]]:
        if self.fail:
            raise RuntimeError("CUDA error: device lost")
        return [(-float(len(r.args[1])), False) for r in reqs]

    def loglikelihood_rolling(self, reqs: list[Any], disable_tqdm: bool = False) -> list[float]:
        return [-float(len(r.args[0])) for r in reqs]

    def generate_until(self, reqs: list[Any], disable_tqdm: bool = False) -> list[str]:
        raise NotImplementedError


SPEC = models.ModelSpec(id="test/fake-lm", repo="test/fake-lm", revision="0" * 40, path=None, device="cpu", bos="none")
RECORD = {"bos": {"bos_token_id": None}, "weights_files": {}, "weights_sha256": None, "max_length": 2048}


def run(tmp_path: Path, lm: Any, n: int | None = None) -> tuple[execute.Outcome, dict[str, Any]]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    benchmark = catalog.CATALOG["arc-easy"]
    assert benchmark.dataset is not None
    benchmark = dataclasses.replace(
        benchmark, dataset=dataclasses.replace(benchmark.dataset, n_population=n or len(ARC))
    )
    outcome = execute.run_benchmark(
        benchmark, lm, SPEC, RECORD, tmp_path / "runs", local(write_docs(tmp_path, "arc-easy"))
    )
    assert outcome.run_dir is not None
    report = validate_run(outcome.run_dir)
    assert report.ok, report.issues
    manifest = json.loads((outcome.run_dir / "manifest.json").read_text(encoding="utf-8"))
    return outcome, manifest


def test_end_to_end_run_is_valid_and_scored_as_expected(tmp_path: Path) -> None:
    outcome, manifest = run(tmp_path, FakeLM())
    # Shortest option: "neon" (wrong), "heat" (right), "Mars" (right): acc 2/3. acc_norm ties, the first option wins:
    # "oxygen" (wrong), "heat" (right), "the Sun" (wrong): 1/3.
    values = {o["metric"]: o["value"] for o in manifest["observations"]}
    assert outcome.state == "ok"
    assert values == {"acc": pytest.approx(2 / 3), "acc_norm": pytest.approx(1 / 3)}
    assert outcome.value == pytest.approx(2 / 3)
    assert manifest["assessment"]["status"] == "verified"
    assert manifest["protocol"]["id"] == "codesota.arc-easy.0shot.none-bos.v1"
    assert manifest["benchmark"]["legacy_id"] == "T51"
    timing = manifest["execution"]["timing"]
    assert timing["requests"] == 4 + 3 + 4 and timing["seconds"] >= 0 and outcome.seconds >= 0
    assert outcome.run_dir is not None
    lines = (outcome.run_dir / "samples.jsonl").read_text(encoding="utf-8").splitlines()
    samples = [json.loads(line) for line in lines]
    assert [s["sample_id"] for s in samples] == ["syn-arc-1", "syn-arc-2", "syn-arc-3"]
    assert [s["gold"] for s in samples] == [1, 0, 1]


def test_prompt_longer_than_the_context_is_unsupported_not_zero(tmp_path: Path) -> None:
    outcome, manifest = run(tmp_path, FakeLM(max_length=8))
    assert outcome.state == "unsupported" and outcome.value is None
    assert {o["state"] for o in manifest["observations"]} == {"unsupported"}
    assert all(o["value"] is None and o["n_scored"] == 0 for o in manifest["observations"])
    assert "ContextTooLong" in (outcome.reason or "")


def test_model_failure_is_failed_not_zero(tmp_path: Path) -> None:
    outcome, manifest = run(tmp_path, FakeLM(fail=True))
    assert outcome.state == "failed" and outcome.value is None
    assert "device lost" in (outcome.reason or "")
    assert any(a["path"] == "error.log" for a in manifest["artifacts"])


def test_split_of_the_wrong_size_fails(tmp_path: Path) -> None:
    outcome, _ = run(tmp_path, FakeLM(), n=4)
    assert outcome.state == "failed"
    assert "DatasetMismatch" in (outcome.reason or "")


def test_duplicate_sample_ids_fail_before_evaluation(tmp_path: Path) -> None:
    lm = FakeLM()
    duplicated = [ARC[0], {**ARC[1], "id": ARC[0]["id"]}, ARC[2]]
    path = tmp_path / "dup.jsonl"
    path.write_text("".join(json.dumps(d) + "\n" for d in duplicated), encoding="utf-8")
    benchmark = catalog.CATALOG["arc-easy"]
    assert benchmark.dataset is not None
    benchmark = dataclasses.replace(benchmark, dataset=dataclasses.replace(benchmark.dataset, n_population=3))
    outcome = execute.run_benchmark(benchmark, lm, SPEC, RECORD, tmp_path / "runs", local(path))
    assert outcome.state == "failed" and "not unique" in (outcome.reason or "")
    assert outcome.run_dir is not None and validate_run(outcome.run_dir).ok


def test_research_digest_uses_the_research_id_field() -> None:
    benchmark = catalog.CATALOG["hellaswag"]
    samples = [{"doc": {"ind": 5}}, {"doc": {"ind": 5}}, {"doc": {"ind": 9}}]
    from codesota.results import source_id_digest

    assert execute.research_digest(benchmark, samples) == source_id_digest([5, 5, 9])
    assert execute.research_digest(catalog.CATALOG["arc-easy"], samples) is None


# --- the context limit counts the tokens the model gets ---


def longest_request(lm: Any, tmp_path: Path) -> int:
    """Tokens of the longest request of the ARC test documents, as `lm` encodes them."""
    task = execute.build_task(tasks.task_config(catalog.CATALOG["arc-easy"], local(write_docs(tmp_path, "arc-easy"))))
    pairs = [p for doc in task.eval_docs for p in execute.request_pairs(task, doc, task.fewshot_context(doc, 0))]
    return max(execute.request_tokens(lm, c, x) for c, x in pairs)


def test_a_request_that_fits_exactly_is_scored_and_one_token_more_is_unsupported(tmp_path: Path) -> None:
    longest = longest_request(FakeLM(), tmp_path)
    # HFLM feeds (context + continuation)[:-1], so max_length + 1 tokens still fit without truncation.
    assert run(tmp_path / "fits", FakeLM(max_length=longest - 1))[0].state == "ok"
    assert run(tmp_path / "over", FakeLM(max_length=longest - 2))[0].state == "unsupported"


def test_the_limit_uses_the_pair_encoding_not_the_concatenated_text(tmp_path: Path) -> None:
    longest = longest_request(FakeLM(), tmp_path)
    # The concatenated text fits; the model's pair encoding is 2 tokens longer and does not.
    assert run(tmp_path / "pair", FakeLM(max_length=longest - 1, pair_extra=2))[0].state == "unsupported"


# --- a model that does not load ---


def test_a_model_that_does_not_load_is_recorded_in_every_selected_benchmark(tmp_path: Path) -> None:
    from codesota.runner.__main__ import main

    empty = tmp_path / "empty-model"
    empty.mkdir()
    out = tmp_path / "runs"
    code = main(["--benchmarks", "wsc273,piqa,blimp", "--model", str(empty), "--out", str(out), "--device", "cpu"])
    assert code == 1
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert [(r["benchmark"], r["state"]) for r in index] == [
        ("blimp", "not_run"),
        ("wsc273", "failed"),
        ("piqa", "failed"),
    ]
    for row in index[1:]:
        run_dir = Path(row["run_dir"])
        assert validate_run(run_dir).ok
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["model"]["id"] == "local/empty-model"
        assert all(o["value"] is None and o["state"] == "failed" for o in manifest["observations"])
        assert (run_dir / "error.log").is_file()


def test_hub_access_errors_are_blocked_access() -> None:
    class RepositoryNotFoundError(Exception):
        pass

    try:
        try:
            raise RepositoryNotFoundError("401 Client Error")
        except RepositoryNotFoundError as inner:
            raise OSError("not a valid model identifier, or a private repository without a token") from inner
    except OSError as e:
        assert execute.state_of(e) == "blocked_access"
    assert execute.state_of(RuntimeError("x")) == "failed"


# --- a real (tiny, random) model from a local directory, through HFLM ---


def tiny_model(path: Path) -> Path:
    """A 2-layer GPT-NeoX with random weights and a word-level tokenizer, saved as a Hub model directory."""
    import torch
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from tokenizers.pre_tokenizers import Whitespace
    from transformers import GPTNeoXConfig, GPTNeoXForCausalLM, PreTrainedTokenizerFast

    words = sorted({w for d in ARC for w in (d["question"] + " " + " ".join(d["choices"]["text"])).split()})
    vocab = {t: i for i, t in enumerate(["<s>", "</s>", "<unk>", "<pad>", "Question", "Answer", ":", "?", *words])}
    tok = Tokenizer(WordLevel(vocab, unk_token="<unk>"))
    tok.pre_tokenizer = Whitespace()
    fast = PreTrainedTokenizerFast(
        tokenizer_object=tok, bos_token="<s>", eos_token="</s>", unk_token="<unk>", pad_token="<pad>"
    )
    torch.manual_seed(0)
    config = GPTNeoXConfig(
        vocab_size=len(vocab),
        hidden_size=16,
        num_hidden_layers=2,
        num_attention_heads=2,
        intermediate_size=32,
        max_position_embeddings=64,
        bos_token_id=0,
        eos_token_id=1,
    )
    GPTNeoXForCausalLM(config).save_pretrained(path, safe_serialization=True)
    fast.save_pretrained(path)
    return path


@pytest.mark.parametrize("bos", ["one", "none"])
def test_a_local_model_runs_end_to_end(tmp_path: Path, bos: models.Bos) -> None:
    path = tiny_model(tmp_path / "tiny")
    spec = models.ModelSpec.from_args(str(path), None, device="cpu", bos=bos)
    spec, lm, record = models.prepare(spec)
    assert spec.id is not None and spec.id.startswith("local/tiny@")
    assert record["weights_sha256"] == models.sha256_file(path / "model.safetensors")
    assert record["bos"]["leading_bos_in_probe_request"] == (1 if bos == "one" else 0)
    benchmark = catalog.CATALOG["arc-easy"]
    assert benchmark.dataset is not None
    benchmark = dataclasses.replace(benchmark, dataset=dataclasses.replace(benchmark.dataset, n_population=len(ARC)))
    data = local(write_docs(tmp_path, "arc-easy"))
    first = execute.run_benchmark(benchmark, lm, spec, record, tmp_path / "runs", data)
    second = execute.run_benchmark(benchmark, lm, spec, record, tmp_path / "runs", data)
    assert first.state == second.state == "ok"
    assert first.value == second.value  # deterministic on CPU
    assert first.run_dir != second.run_dir
    assert first.run_dir is not None and validate_run(first.run_dir).ok
    manifest = json.loads((first.run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["model"]["id"] == spec.id and manifest["protocol"]["bos"] == bos
    assert manifest["execution"]["environment"]["weights_files"] == {"model.safetensors": record["weights_sha256"]}
