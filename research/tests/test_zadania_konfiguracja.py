"""Every ZADANIA entry builds its lm-eval config without network or weights: pinned source, split, metric, task
directory and, for the Polish tasks, the copied OpenPL YAML. Run: python tests/test_zadania_konfiguracja.py"""
import ast
import os
import re
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN / "common"))
import zadania as Z  # noqa: E402
from lm_eval.api.task import TaskConfig  # noqa: E402

OPENPL = "21d0ea9cf4fd6153dfff4d84d6ad0aab5488f302"
DEMONSTRACJE_Z_TESTU = {"T24"}  # Belebele: the fork's YAML takes the first 5 test documents (only split)


def katalogi():
    env = {**os.environ, "WS": tempfile.mkdtemp(), "K": str(KORZEN)}
    wynik = subprocess.run(["bash", str(KORZEN / "tools" / "przebieg_centralny.sh"), "katalogi"],
                           capture_output=True, text=True, check=True, env=env).stdout
    return dict(l.split() for l in wynik.splitlines())


def nazwy_metryk(cfg):
    return [m["metric"] if isinstance(m["metric"], str) else m["metric"].__name__ for m in cfg["metric_list"]]


def pliki_danych(cfg):
    return list((cfg.get("dataset_kwargs") or {}).get("data_files", {}).values())


def test_every_task_builds_a_valid_config():
    nazwy = []
    for t in Z.ZADANIA:
        warianty = Z.konfiguracje(t)
        assert warianty and warianty[0][0] == "space", t
        for _, cfg in warianty:
            TaskConfig(**cfg)  # unknown or mistyped keys fail here, not on the GPU
            assert cfg["task"].startswith("slayer_") and cfg["metadata"]["task_id"] == t
            nazwy.append(cfg["task"])
    assert len(nazwy) == len(set(nazwy))


def test_source_is_pinned_to_the_zadania_revision():
    for t, meta in Z.ZADANIA.items():
        cfg = Z.konfiguracje(t)[0][1]
        pliki = pliki_danych(cfg)
        if pliki:
            przypiety = meta.get("rewizja_parquet") or meta["rewizja"]
            assert all(f"@{przypiety}/" in p for p in pliki), t
            if meta.get("rewizja_parquet"):
                assert f"/{meta['nazwa_hf']}/{meta['split']}/" in cfg["dataset_kwargs"]["data_files"]["test"], t
        elif meta.get("parquet"):
            assert cfg["dataset_kwargs"]["revision"] == "refs/convert/parquet", t
        else:
            assert cfg["dataset_path"] == meta["repo"] and cfg["dataset_kwargs"]["revision"] == meta["rewizja"], t
            assert cfg["test_split"] == meta["split"] and cfg["dataset_name"] == meta.get("nazwa_hf"), t


def test_zadania_entry_matches_the_benchmark_card():
    """Revision and split of ZADANIA against the card README.md (an independent record, not the same dict)."""
    mapa = katalogi()
    sprawdzone = 0
    for t, meta in Z.ZADANIA.items():
        assert re.fullmatch(r"[0-9a-f]{40}", meta["rewizja"]), t
        karta = KORZEN / "benchmarks" / mapa[t] / "README.md"
        tekst = karta.read_text(encoding="utf-8") if karta.exists() else ""
        if f"`{meta['repo']}` @ `" not in tekst:
            continue
        assert f"`{meta['repo']}` @ `{meta['rewizja']}`" in tekst and f"split `{meta['split']}`" in tekst, t
        sprawdzone += 1
    assert sprawdzone >= 25  # T05-T31, T40, T48 except T06 (benchmarks/piqa/README.md is the card of its own pipeline)


def test_main_metric_is_in_the_config():
    for t, meta in Z.ZADANIA.items():
        cfg = Z.konfiguracje(t)[0][1]
        glowna = meta["metric"].split(",")[0] if meta["rodzaj"] == "rolling" else meta.get("klucz", "acc")
        assert glowna in nazwy_metryk(cfg), t


def test_every_task_has_its_benchmark_directory():
    mapa = katalogi()
    assert list(mapa) == list(Z.ZADANIA)
    for t, k in mapa.items():
        assert (KORZEN / "benchmarks" / k).is_dir(), (t, k)


def test_polish_tasks_use_the_copied_openpl_yaml():
    yamle = {t: m for t, m in Z.ZADANIA.items() if m.get("yaml")}
    assert sorted(yamle) == [f"T{n}" for n in range(22, 32)]
    for t, meta in yamle.items():
        sciezka = Z.BENCHMARKI / meta["yaml"]
        assert OPENPL in sciezka.read_text(encoding="utf-8").splitlines()[0], t
        zrodlowy = Z.wczytaj_yaml(sciezka)
        assert zrodlowy["task"] == meta["task"], t
        cfg = Z.konfiguracje(t)[0][1]
        assert cfg["num_fewshot"] == meta["shoty"] == 5 and cfg["doc_to_text"] == zrodlowy["doc_to_text"], t
        assert "group" not in cfg, t
        for pole in ("process_docs", "doc_to_target", "doc_to_text", "doc_to_choice"):
            if callable(cfg.get(pole)):
                assert cfg[pole].nazwa in definicje(cfg[pole].plik), (t, pole)
        for m in cfg["metric_list"]:
            for f in (m["metric"], m.get("aggregation")):
                if callable(f) and hasattr(f, "plik"):
                    assert f.nazwa in definicje(f.plik), (t, f.nazwa)


def definicje(plik):
    with warnings.catch_warnings():  # the fork's polqa utils.py has a '\.' string escape, copied unchanged
        warnings.simplefilter("ignore", SyntaxWarning)
        drzewo = ast.parse(Path(plik).read_text(encoding="utf-8"))
    return {w.name for w in drzewo.body if isinstance(w, ast.FunctionDef)}


def test_few_shot_demonstrations_do_not_come_from_the_scored_split():
    for t, meta in Z.ZADANIA.items():
        cfg = Z.konfiguracje(t)[0][1]
        if not cfg.get("num_fewshot"):
            continue
        zrodlo = cfg.get("fewshot_split") or cfg.get("training_split") or cfg.get("validation_split")
        if t in DEMONSTRACJE_Z_TESTU:
            assert zrodlo == cfg["test_split"], t
            continue
        assert zrodlo and zrodlo != cfg["test_split"], t
        if pliki_danych(cfg):
            assert zrodlo in cfg["dataset_kwargs"]["data_files"], t


def test_lazy_yaml_function_runs_the_fork_metric():
    cfg = Z.konfiguracje("T25")[0][1]
    f1 = next(m for m in cfg["metric_list"] if nazwy_metryk({"metric_list": [m]}) == ["f1"])
    assert f1["aggregation"]([(1, 1), (0, 1), (1, 0), (1, 1)]) == 2 / 3


def test_paws_keeps_the_space_prompt_not_0_4_9_1():
    cfg = Z.konfiguracje("T48")[0][1]
    assert cfg["doc_to_text"] == "" and "process_docs" not in cfg and "target_delimiter" not in cfg
    assert cfg["doc_to_choice"].startswith('{{[sentence1+", right? No, "')


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__]))
