"""The code that touches lm-eval internals works in both lm-eval versions of the central run: 0.4.9.1 (`lock`,
common/requirements.lock.txt) and the `new` env pin in tools/przebieg_centralny.sh (Qwen3.5, LFM3).

Run in each env (README.md, "Testy kodu"): python tests/test_lm_eval_wersje.py. Run in one env only, it cannot catch
a call that exists in that version and not in the other (`TaskManager._get_config`, `ContextSampler(docs, task)`).
"""
import json
import os
import re
import sys
from pathlib import Path

import pytest

os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN / "common"))
import ewaluuj as E  # noqa: E402
import lm_eval  # noqa: E402
import zadania as Z  # noqa: E402

LOCK = re.search(r"^lm_eval==(\S+)$", (KORZEN / "common" / "requirements.lock.txt").read_text(), re.M)[1]
NEW = re.search(r"NEW_ENV_PINS=\([^)]*lm_eval==([^ )]+)", (KORZEN / "tools" / "przebieg_centralny.sh").read_text())[1]


def test_installed_lm_eval_is_one_of_the_run_envs():
    assert LOCK != NEW and lm_eval.__version__ in (LOCK, NEW), (lm_eval.__version__, LOCK, NEW)


def nazwy_yaml():
    for meta in Z.ZADANIA.values():
        if meta.get("lm_eval"):
            yield meta["lm_eval"]
        if meta.get("grupa"):
            yield from Z.czlonkowie_grupy(meta["grupa"])


@pytest.mark.parametrize("nazwa", sorted(set(nazwy_yaml())))
def test_task_yaml_of_installed_lm_eval_loads_whole(nazwa):
    cfg = Z._yaml(nazwa)
    assert cfg["task"] == nazwa and "include" not in cfg and cfg.get("output_type")


def test_squad_metrics_of_coqa_and_record_import():
    """CoQA (T41) and ReCoRD (T50) helpers import transformers' squad_metrics, gone in transformers 5."""
    Z.zapewnij_squad_metrics()
    import transformers.data.metrics.squad_metrics as sm
    assert sm.compute_exact("The Cat!", "cat") == 1 and sm.compute_f1("a b c", "b c d") == pytest.approx(0.8)  # "a" is an article
    assert sm.compute_f1("", "") == 1 and sm.compute_f1("x", "") == 0
    for t in ("T41", "T50"):
        assert Z.konfiguracje(t)


def test_race_prompt_is_the_space_version():
    """RACE (T40): 6d2abda4 and 0.4.9.1 keep question[-5:] of a cloze question, 0.4.13 question[:-5]."""
    doc_to_text = Z.konfiguracje("T40")[0][1]["doc_to_text"]
    problemy = [{"question": "He went  _  .", "answer": "A", "options": ["home", "x", "y", "z"]},
                {"question": "Q?", "answer": "B", "options": ["a", "b", "c", "d"]}]
    assert doc_to_text({"article": "A", "problems": str(problemy)}) == "Article: A\n\n _  .home\nQ?"


def zadanie(task_id, tmp_path, monkeypatch, dane):
    katalog = tmp_path / "data"
    katalog.mkdir(exist_ok=True)
    for nazwa, docs in dane.items():
        (katalog / f"{nazwa}.jsonl").write_text("".join(json.dumps(d) + "\n" for d in docs))
    monkeypatch.setattr(Z, "DANE_TESTOWE", katalog)
    return E.zbuduj_zadania([Z.konfiguracje(task_id, "lokalne")[0][1]])[0]  # first variant / group member


GSM = [{"question": f"Q{i}?", "answer": f"r\n#### {i}"} for i in range(3)]
GSM_DEMO = [{"question": f"Demo {i}?", "answer": f"s\n#### {i}"} for i in range(8)]


def test_bank_sampler_gives_bank_in_order_in_the_prompt(tmp_path, monkeypatch):
    zad = zadanie("T33", tmp_path, monkeypatch, {"gsm8k": GSM, "gsm8k_demo": GSM_DEMO})
    assert E.uzyj_banku(zad) and not E.demonstracje_z_testu(zad)
    E.ustaw_bank(zad, Z.ZADANIA["T33"], None, None)
    zad.set_fewshot_seed(1234)  # simple_evaluate does this; 0.4.13 passes the seed on to the sampler
    ctx = zad.fewshot_context(list(zad.eval_docs)[0], num_fewshot=5)
    pokazane = re.findall(r"Question: (Demo \d\?)", ctx)
    bank = [d["question"] for d in zad.sampler.sample(5)]
    assert len(pokazane) == 5 and pokazane == bank and ctx.endswith("Question: Q0?\nAnswer:")


def test_fewshot_config_samples_read_in_both_versions(tmp_path, monkeypatch):
    """BBH keeps its source shots (fewshot_config.samples): a dict in 0.4.9.1, FewshotConfig in 0.4.13."""
    dane = {m: [{"input": "x", "target": "y"}] for m in Z.czlonkowie_grupy("bbh_fewshot")[:1]}
    zad = zadanie("T47", tmp_path, monkeypatch, dane)
    assert zad.config.num_fewshot == 3 and not E.uzyj_banku(zad)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
