"""MMLU T32 (common/zadania.py, benchmarks/mmlu/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, RECIPE.md and the README type row (`mc +warstwy`: 57 subjects, population
weights); the `+warstwy` functions on the card's numbers: the 57 test populations N_i of `hails/mmlu_no_train`
@ b2e1ec9a (sum 14042) and the per-subject count of the most frequent gold letter give the card's b 0,3094
(`metryki.wazona_baza`) and its panel-200 allocation (`metryki.przydzial_grupy`); `metryki.warstwy` on invented
subjects gives the weighted (micro) mean and SE W = sqrt(sum w_i^2 SE_i^2). With lm-eval installed (.venv-eval) the
group has the same 57 members and the subject YAML has the card's header and prompt. Run: python tests/test_mmlu.py
(or pytest).
"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wpis_benchmarku as W  # noqa: E402
import metryki as M  # noqa: E402  (research/common, on the path through wpis_benchmarku)

Z = W.Z
# (N_i test rows, rows with the subject's most frequent gold letter), parquets hails/mmlu_no_train @ b2e1ec9a
PRZEDMIOTY = {
    "abstract_algebra": (100, 31), "anatomy": (135, 45), "astronomy": (152, 51), "business_ethics": (100, 30),
    "clinical_knowledge": (265, 79), "college_biology": (144, 38), "college_chemistry": (100, 41),
    "college_computer_science": (100, 33), "college_mathematics": (100, 31), "college_medicine": (173, 58),
    "college_physics": (102, 38), "computer_security": (100, 30), "conceptual_physics": (235, 76),
    "econometrics": (114, 32), "electrical_engineering": (145, 43), "elementary_mathematics": (378, 101),
    "formal_logic": (126, 46), "global_facts": (100, 33), "high_school_biology": (310, 98),
    "high_school_chemistry": (203, 60), "high_school_computer_science": (100, 33),
    "high_school_european_history": (165, 47), "high_school_geography": (198, 70),
    "high_school_government_and_politics": (193, 71), "high_school_macroeconomics": (390, 142),
    "high_school_mathematics": (270, 71), "high_school_microeconomics": (238, 83), "high_school_physics": (151, 50),
    "high_school_psychology": (545, 190), "high_school_statistics": (216, 102), "high_school_us_history": (204, 53),
    "high_school_world_history": (237, 64), "human_aging": (223, 84), "human_sexuality": (131, 37),
    "international_law": (121, 45), "jurisprudence": (108, 32), "logical_fallacies": (163, 49),
    "machine_learning": (112, 35), "management": (103, 39), "marketing": (234, 68), "medical_genetics": (100, 30),
    "miscellaneous": (783, 225), "moral_disputes": (346, 101), "moral_scenarios": (895, 244), "nutrition": (306, 90),
    "philosophy": (311, 93), "prehistory": (324, 95), "professional_accounting": (282, 76),
    "professional_law": (1534, 415), "professional_medicine": (272, 122), "professional_psychology": (612, 169),
    "public_relations": (110, 38), "security_studies": (245, 98), "sociology": (201, 54),
    "us_foreign_policy": (100, 28), "virology": (166, 53), "world_religions": (171, 55),
}
POPULACJE = {f"mmlu_{s}": n for s, (n, _) in PRZEDMIOTY.items()}  # members as in ewaluuj.wybor_probki


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA, the card, RECIPE.md and the README row."""
    oczekiwane = {"repo": "hails/mmlu_no_train", "rewizja": "b2e1ec9aa795adafe68e8e983248dbd4b52a1c60",
                  "nazwa_hf": None, "split": "test", "metric": "acc,none", "grupa": "mmlu", "lm_eval": None,
                  "rodzaj": "mc", "klasy_stale": True, "klastry": None}
    meta, karta = W.sprawdz_wpis("T32", oczekiwane, shoty=5, typ="mc +warstwy")
    assert "| Metryka decyzyjna | `acc`, 5-shot, średnia przedmiotów ważona liczebnościami (SE W)." in karta
    assert "n: 14042 (suma 57 konfiguracji, policzona z parquetów @ `b2e1ec9a`)" in karta
    assert ("`The following are multiple choice questions (with answers) about abstract algebra.\\n\\n`"
            in karta)
    assert ("`{{question.strip()}}\\nA. {{choices[0]}}\\nB. {{choices[1]}}\\nC. {{choices[2]}}\\nD. "
            "{{choices[3]}}\\nAnswer:`") in karta
    assert "SE W: √(Σ w_i² · SE_i²), w_i = N_i / 14042" in karta
    assert "`metryki.wazona_baza`, w_i = N_i/14042): 0,3094" in karta and "4345 z 14042 (0,3094)" in karta
    assert W.wiersz_readme("mmlu")[2] == "warstwy: 57 przedmiotów, wagi populacji"


def test_population_weights_give_the_card_baseline_and_panel():
    """57 subjects, 14042 rows; b = majority share per subject averaged with w_i = N_i/14042, which equals
    sum(majority counts)/14042 = 4345/14042 = 0.30943; panel 200 = 2 per subject (114) + 86 by largest deficit."""
    assert len(POPULACJE) == 57 and sum(POPULACJE.values()) == 14042
    bazy = {f"mmlu_{s}": {"chance_value": 0.25, "majority_value": m / n} for s, (n, m) in PRZEDMIOTY.items()}
    b = M.wazona_baza(bazy, POPULACJE)
    assert b["chance_value"] == pytest.approx(0.25)
    assert b["majority_value"] == pytest.approx(4345 / 14042) and round(b["majority_value"], 4) == 0.3094
    assert b["majority_prediction_share"] is None and b["constant_prediction"] is None
    przydz = M.przydzial_grupy(POPULACJE, 200)
    assert sum(przydz.values()) == 200 and min(przydz.values()) == 2
    najwieksze = sorted(przydz.items(), key=lambda kv: -kv[1])[:5]
    assert najwieksze == [("mmlu_professional_law", 22), ("mmlu_moral_scenarios", 12), ("mmlu_miscellaneous", 11),
                          ("mmlu_professional_psychology", 8), ("mmlu_high_school_psychology", 7)]


def test_warstwy_weighted_mean_and_se_on_invented_subjects():
    """a: [1, 0], N 100; b: [1, 1, 1, 0], N 300; c is in the weights but has no rows -> weights renormalised to
    0.25 / 0.75. Value 0.25*0.5 + 0.75*0.75 = 0.6875 (macro mean would be 0.625). SE_a = 0.7071/sqrt2 = 0.5,
    SE_b = 0.5/2 = 0.25, SE W = sqrt(0.0625*0.25 + 0.5625*0.0625) = sqrt(0.05078125)."""
    w = M.warstwy({"a": [1, 0], "b": [1, 1, 1, 0]}, {"a": 100, "b": 300, "c": 600}, powtorzenia=500)
    assert w["value"] == pytest.approx(0.6875) and w["n"] == 6
    assert w["se"] == pytest.approx(math.sqrt(0.05078125))
    assert w["czlonkowie"]["a"]["waga"] == pytest.approx(0.25) and w["czlonkowie"]["b"]["se"] == pytest.approx(0.25)
    with pytest.raises(ValueError):
        M.warstwy({"a": [1], "b": []}, {"a": 1, "b": 1})  # a missing group member is an explicit error


def test_wazona_baza_on_invented_subjects():
    """majority 0.5 (N 100) and 0.3 (N 300): 0.25*0.5 + 0.75*0.3 = 0.35; prediction share = max of the subjects."""
    bazy = {"a": {"chance_value": 0.25, "majority_value": 0.5, "majority_prediction_share": 1.0},
            "b": {"chance_value": 0.25, "majority_value": 0.3, "majority_prediction_share": 0.6}}
    b = M.wazona_baza(bazy, {"a": 100, "b": 300})
    assert b["majority_value"] == pytest.approx(0.35) and b["chance_value"] == pytest.approx(0.25)
    assert b["majority_prediction_share"] == 1.0 and b["constant_prediction"] is False


@pytest.mark.skipif(not W.MA_LM_EVAL, reason="needs lm-eval (.venv-eval): reads the installed mmlu YAMLs")
def test_installed_group_has_the_card_members_and_prompt():
    assert Z.czlonkowie_grupy("mmlu") == sorted(POPULACJE)
    cfg = Z._yaml("mmlu_abstract_algebra")
    assert cfg["description"] == "The following are multiple choice questions (with answers) about abstract algebra.\n\n"
    assert cfg["doc_to_text"] == ("{{question.strip()}}\nA. {{choices[0]}}\nB. {{choices[1]}}\nC. {{choices[2]}}\n"
                                  "D. {{choices[3]}}\nAnswer:")
    assert cfg["doc_to_choice"] == ["A", "B", "C", "D"] and cfg["fewshot_split"] == "dev"
    assert [m["metric"] for m in cfg["metric_list"]] == ["acc"] and "num_fewshot" not in cfg


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
