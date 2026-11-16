"""LLMzSzŁ T37 (common/zadania.py, benchmarks/llmzszl/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the copied Space definition `llmzszl.yaml` (bytes below the header = Probierz blob
142edb86), the 0-shot prompt of the paper (section 3.2; continuations = space + letter ` A`..` D`, gold =
`correct_answer_index` from 0) and the decision metric `acc`. A row with 5 answers keeps only A-D in the prompt and is
scored like the others (card "Znane rozbieżności: dane"). Data: 4 invented rows. Run: python tests/test_llmzszl.py.
"""
import subprocess
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z = C.Z
YAML = Z.BENCHMARKI / "llmzszl" / "lm_eval_tasks" / "llmzszl" / "llmzszl.yaml"
DANE = [{"question": f" Pytanie {i}? ", "answers": ["jeden", "dwa", "trzy", "cztery"] + (["pięć"] if i == 3 else []),
         "correct_answer_index": [1, 0, 1, 3][i], "year": 2024, "type": "Egzaminy Zawodowe", "name": "Test"}
        for i in range(4)]


def szablon(d):
    a = d["answers"]
    return (f"Przykładowe pytanie egzaminacyjne, test jednokrotnego wyboru\n{d['question'].strip()}\n"
            f"A. {a[0]}\nB. {a[1]}\nC. {a[2]}\nD. {a[3]}\nPrawidłowa odpowiedź:")


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T37"], ZK.karta("T37").read_text(encoding="utf-8")
    oczekiwane = {"repo": "amu-cai/llmzszl-dataset", "rewizja": "9c11d52a415147f1e2c44038a9d4d4155f064e1a",
                  "split": "test", "metric": "acc,none", "task": "n05_llmzszl", "benchmark_id": "llmzszl",
                  "yaml": "llmzszl/lm_eval_tasks/llmzszl/llmzszl.yaml"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0
    assert meta["klasy_stale"] and "pole_id" not in meta  # no id field: panel id = row index (card "Bazy: panel 200")
    for k in ("repo", "rewizja", "task"):
        assert oczekiwane[k] in karta, k
    assert "| Metryka decyzyjna | `acc`" in karta and "split: `test`" in karta and "0-shot" in karta
    assert "lm_eval_tasks/llmzszl/llmzszl.yaml" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T37"] == "llmzszl"


def test_yaml_copy_is_the_probierz_blob():
    linie = YAML.read_bytes().split(b"\n")
    assert all(l.startswith(b"#") for l in linie[:4]) and linie[4] == b"task: n05_llmzszl"
    blob = subprocess.run(["git", "hash-object", "--stdin"], input=b"\n".join(linie[4:]), capture_output=True,
                          check=True).stdout.decode().strip()
    assert blob == "142edb868977497f522786d753a233f5d42f368e"


def test_config_pins_the_card_revision():
    (wariant, cfg), = Z.konfiguracje("T37")
    assert wariant == "space" and cfg["task"] == "slayer_n05_llmzszl" and cfg["num_fewshot"] == 0
    assert cfg["dataset_path"] == "amu-cai/llmzszl-dataset" and cfg["dataset_name"] is None
    assert cfg["dataset_kwargs"] == {"revision": "9c11d52a415147f1e2c44038a9d4d4155f064e1a"}
    assert cfg["doc_to_choice"] == ["A", "B", "C", "D"] and cfg["doc_to_target"] == "correct_answer_index"


# the model answers B everywhere; golds B, A, B, D -> acc 2/4
def test_zero_shot_prompt_letters_and_acc(tmp_path, monkeypatch):
    roz, zadania = C.ocen_loglik("T37", {"n05_llmzszl": DANE}, lambda ctx, kont: -1.0 if kont == " B" else -2.0,
                                 tmp_path, monkeypatch)
    for d in DANE:
        assert [k for c, k in zadania if c == szablon(d)] == [" A", " B", " C", " D"]
    assert {c for c, _ in zadania if c} == {szablon(d) for d in DANE}
    assert all("pięć" not in c for c, _ in zadania)
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(2 / 4)
    assert roz["metric"] == "acc,none" and roz["value"] == pytest.approx(2 / 4) and roz["n_scored"] == 4


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
