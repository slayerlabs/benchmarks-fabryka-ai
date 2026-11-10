"""Rules of the full-run report: stage B verdicts from cards, baselines, flags and consistency of the run files."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "ewaluacja"))
sys.path.insert(0, str(ROOT / "tools"))
import count_params  # noqa: E402
import raport  # noqa: E402

RUN = ROOT / "results" / "full-run-2026-11"
NO_CONTROL = {"arc-challenge", "medmcqa", "mathqa", "multiblimp-pl", "pubmedqa", "social-iqa", "wikitext-2", "wsc273"}
FLAGGED = {"lfm2.5-1.2b-base", "lfm3-1.7b"}


def rows(name):
    return [json.loads(l) for l in (RUN / name).read_text(encoding="utf-8").splitlines()]


@pytest.mark.parametrize("line,expected", [
    ("| werdykt | **spełniony**: dalej | inne |", "spełniony: dalej"),
    ("| werdykt etapu B | bez kontroli: nierozstrzygnięte; wstępny |", "bez kontroli: nierozstrzygnięte; wstępny"),
])
def test_verdict_row(line, expected):
    assert raport.parse_verdict(f"tekst\n{line}\n") == expected


def test_verdict_from_section():
    card = "## Werdykt\n\n| kontrola | werdykt |\n|---|---|\n| etap B: lm-eval | spełniony, 0,10 pkt |\n"
    assert raport.parse_verdict(card) == "spełniony, 0,10 pkt"


def test_control_state():
    assert raport.control_state("**bez kontroli: nierozstrzygnięte** — powód".replace("*", "")) == "no_control"
    assert raport.control_state("spełniony") == "control"
    for verdict in ("niespełniony", "zgodne; werdykt jest nierozstrzygalny", "kontrola spoza listy źródeł; wynik wstępny"):
        assert raport.control_state(verdict) == "no_control"
    with pytest.raises(ValueError):
        raport.control_state("po przebiegu centralnym")


def test_baseline_by_type():
    assert raport.baseline("ppl", {"chance": None}) is None
    row = {"wobec_b": {"b": 0.27, "baza": "stala odpowiedz"}}
    assert raport.baseline("mc-k", row) == (0.27, "stała odpowiedź")
    assert raport.baseline("cloze", {"chance": 0.0, "majority": 0.003}) == (0.003, "stała odpowiedź")
    assert raport.baseline("para +klastry", {"chance": 0.5, "majority": None}) == (0.5, "losowa")


def test_contamination_values():
    assert raport.contamination_label("unscanned") == "nieznana"
    assert raport.contamination_label("sprawdzona: skan, 0%") == "sprawdzona: skan, 0%"
    with pytest.raises(ValueError):
        raport.contamination_label("czysto")


def test_labels_and_classes():
    assert "bez wygaszania LR" in raport.slayer_label("1.05")
    assert "nie jest następcą 1.07" in raport.slayer_label("1.08")
    assert raport.size_class(1_078_891_024) == "ok. 1B"
    assert raport.size_class(1_170_340_608) == "poza klasą"


def result(model, bench, pmi, chance=0.5, max_length=2048):
    return {"model": model, "benchmark": bench, "pmi": None if pmi is None else {"value": pmi}, "chance": chance,
            "max_length": max_length}


def test_flag_rule_is_applied_to_every_model_alike():
    data = [result("a", "piqa", 0.40), result("a", "arc-easy", 0.20), result("b", "piqa", 0.40), result("b", "arc-easy", 0.60)]
    for ordered in (data, list(reversed(data))):
        reasons = raport.flag_rules(ordered, [])
        assert set(reasons) == {"a"}


def test_central_diff_rule():
    diffs = [{"model": "m", "nasz": 0.5, "odniesienie": 0.4}, {"model": "n", "nasz": 0.5, "odniesienie": 0.5}]
    assert set(raport.flag_rules([], diffs)) == {"m"}


def test_window_rule():
    assert raport.window_exceeded({"benchmark": "wikitext-2", "max_length": 4096}, 2048)
    assert not raport.window_exceeded({"benchmark": "wikitext-2", "max_length": 2048}, 2048)
    assert not raport.window_exceeded({"benchmark": "piqa", "max_length": 4096}, 2048)


def test_tensor_count_counts_shared_bytes_once():
    header = {"__metadata__": {}, "a": {"shape": [2, 3], "data_offsets": [0, 6]},
              "tied": {"shape": [2, 3], "data_offsets": [0, 6]}, "b": {"shape": [4], "data_offsets": [6, 10]}}
    assert count_params.count_tensors(header) == 10


def test_every_test_has_a_final_stage_b_verdict():
    cards = raport.read_cards(ROOT / "benchmarks", raport.BENCHMARKI)
    assert len(cards) == 15
    assert {b for b, c in cards.items() if c["state"] == "no_control"} == NO_CONTROL


def test_codesota_table_excludes_no_control_tests_and_flagged_models():
    tab = [r for r in rows("przeglad.jsonl") if r.get("w_tabeli_codesota")]
    assert tab
    assert not {r["benchmark"] for r in tab} & NO_CONTROL
    assert not {r["model"] for r in tab} & FLAGGED
    assert all(r["kontaminacja"] == "nieznana" for r in tab)
    assert not [r for r in tab if r["model"].startswith("slayer1b-") and r["model"] != "slayer1b-1.07-hf"]


def test_flags_match_the_rule_for_all_models():
    flagged = {r["model"] for r in rows("przeglad.jsonl") if r["flaga"] == "do_sprawdzenia"}
    assert flagged == FLAGGED


def test_se_is_the_same_in_manifest_and_review():
    review = {(r["benchmark"], r["model"]): r for r in rows("przeglad.jsonl") if r["benchmark"] != "*"}
    for row in rows("manifest.jsonl"):
        assert row["se"] is not None
        assert row["se"] == pytest.approx(review[(row["benchmark"], row["model"])]["se"], rel=1e-9)


def test_pythia_wikitext_uses_the_window_2048_result():
    row = next(r for r in rows("manifest.jsonl") if r["benchmark"] == "wikitext-2" and r["model"] == "pythia-1b-v0")
    assert row["wartosc"] == pytest.approx(1.6877, abs=1e-4)
    assert "--max_length 2048" in row["komenda"]
    assert row["poprawka"]["stara_wartosc"] > 2.4


def test_environment_record_states_what_is_unknown():
    env = json.loads((RUN / "srodowisko.json").read_text(encoding="utf-8"))
    for name in ("lock", "new"):
        assert env["srodowiska"][name]["pip_freeze"] == "nieustalone"
        assert env["srodowiska"][name]["powod"]


def test_pmi_sensitivity_does_not_depend_on_input_order():
    results = [{"model": "b", "benchmark": "piqa", "pmi": {"value": 0.48, "se": 0.01}, "chance": 0.5},
               {"model": "a", "benchmark": "piqa", "pmi": {"value": 0.49, "se": 0.01}, "chance": 0.5},
               {"model": "b", "benchmark": "arc-challenge", "pmi": {"value": 0.24, "se": 0.01}, "chance": 0.25},
               {"model": "c", "benchmark": "piqa", "pmi": {"value": 0.60, "se": 0.01}, "chance": 0.5}]
    below = raport.pmi_below_chance(results)
    assert below == raport.pmi_below_chance(results[::-1])
    assert [(x["model"], x["benchmark"]) for x in below] == [("a", "piqa"), ("b", "arc-challenge"), ("b", "piqa")]
    assert below[2]["z"] == pytest.approx(-2)
    assert raport.models_at_threshold(below, 2) == ["b"]
    assert raport.models_at_threshold(below, 1) == ["a", "b"]


def test_environment_gap_takes_only_results_from_both_versions():
    central = [{"model": "x", "benchmark": "piqa", "nasz": 0.5, "odniesienie": 0.1, "lm_eval": "1", "lm_eval_odn": "1"},
               {"model": "y", "benchmark": "arc-easy", "nasz": 0.5, "odniesienie": 0.4, "lm_eval": "1", "lm_eval_odn": "2"},
               {"model": "y", "benchmark": "piqa", "nasz": 0.2, "odniesienie": 0.4, "lm_eval": "1", "lm_eval_odn": "2"}]
    gap = raport.environment_gap(central)
    assert gap["models"] == ["y"] and gap["benchmark"] == "piqa" and gap["diff"] == pytest.approx(0.2)
    assert raport.environment_gap(central[:1]) is None


@pytest.mark.parametrize("higher,first,front,expected", [
    (True, 0.5, 0.6, "+0,1000"), (True, 0.6, 0.5, "−0,1000"), (False, 0.6, 0.5, "−0,100")])
def test_first_to_front_is_a_plain_difference(higher, first, front, expected):
    assert raport.first_to_front({"higher": higher}, {"v": first}, {"v": front}) == expected


def test_hellaswag_note_reads_values_from_the_card():
    text = raport.read_cards(ROOT / "benchmarks", ["hellaswag"])["hellaswag"]["text"]
    note = raport.hellaswag_control_note(text)
    assert "0,6074 wobec 0,6057" in note and "10-shot" in note and "0-shot" in note


def test_csv_checksums_match_the_bytes_in_the_repository():
    checked = 0
    for row in rows("manifest.jsonl"):
        expected = row["pliki"].get("scores-history-wiersz.csv")
        if expected:
            data = (RUN / row["benchmark"] / row["model"] / "scores-history-wiersz.csv").read_bytes()
            assert hashlib.sha256(data).hexdigest() == expected, row["katalog"]
            checked += 1
    assert checked == 238
