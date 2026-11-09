"""Testy runnera bez GPU i bez sieci: python -m pytest -q test_ewaluacja.py"""
import json
import shutil
import types
from pathlib import Path

import pytest

import ewaluacja as E


def test_config_is_read_from_the_central_run_script():
    ms = E.modele()
    assert "slayer1b-1.07" in ms and ms["slayer1b-1.07"].loader == "slayer-ckpt"
    assert "pythia-1b-v0" in ms and "slayer1b-1.06" in ms
    kat = E.katalogi()
    assert kat["T01"] == "blimp" and kat["T53"] == "ewok" and len(kat) == 52
    assert set(E.gotowe()) <= set(kat) and len(E.gotowe()) == 15
    assert E.kod_zadan() == {"T53": "benchmarks/ewok/ewok.py"}


def test_central_tasks_are_the_recorded_directories():
    kat = E.katalogi()
    zapisane = {p.name for p in E.ODNIESIENIE.iterdir() if p.is_dir()}
    assert {kat[t] for t in E.CENTRAL} == zapisane


def test_task_spec_expansion():
    assert E.rozwin_zadania("central") == E.CENTRAL
    assert E.rozwin_zadania("t02, T04") == ["T02", "T04"]
    with pytest.raises(SystemExit):
        E.rozwin_zadania("T99")


def _args(**kw):
    d = dict(probka="pelna", probka_rolling=None, device="cuda", dane="hf")
    d.update(kw)
    return types.SimpleNamespace(**d)


def test_command_matches_the_central_run_flags():
    ms = E.modele()
    py, w, out = Path("py"), Path("wagi"), Path("out")
    c = E.polecenie(ms["slayer1b-1.06"], "T02", _args(), py, w, out)
    assert c[1].endswith("ewaluuj.py") and c[c.index("--model") + 1] == "slayer"
    assert c[c.index("--batch") + 1] == "1" and c[c.index("--probka") + 1] == "pelna"
    hf = E.polecenie(ms["eurollm-1.7b"], "T03", _args(), py, w, out)
    assert hf[hf.index("--max_length") + 1] == "4096"          # okno rolling tylko dla HF
    assert "--max_length" not in E.polecenie(ms["slayer1b-1.06"], "T03", _args(), py, w, out)
    lfm3 = E.polecenie(ms["lfm3-1.7b-base"], "T02", _args(), py, w, out)
    assert "--trust_remote_code" in lfm3
    ewok = E.polecenie(ms["pythia-1b-v0"], "T53", _args(), py, w, out)
    assert ewok[1].endswith("ewok.py") and ewok[2] == "przebieg"


def test_compare_recorded_run_with_itself_is_identical(tmp_path):
    ref = E.ODNIESIENIE / "arc-challenge" / "slayer1b-1.06"
    lok = tmp_path / "arc-challenge" / "slayer1b-1.06"
    shutil.copytree(ref, lok)
    w = E.porownaj_pare(lok, ref)
    assert w["n_wspolnych"] == w["n_ref"] == 1172
    assert w["zgodnosc_pred"] == 1.0 and w["max_dloglik"] == 0.0
    assert E.werdykt(w, 1e-3) == "IDENTYCZNE"


def test_compare_detects_a_changed_answer(tmp_path):
    import gzip
    ref = E.ODNIESIENIE / "blimp" / "slayer1b-1.06"
    lok = tmp_path / "blimp" / "slayer1b-1.06"
    shutil.copytree(ref, lok)
    p = lok / "probki" / "T01_space.jsonl.gz"
    rows = [json.loads(l) for l in gzip.open(p, "rt", encoding="utf-8")]
    fr = json.loads(rows[0]["filtered_resps"]) if isinstance(rows[0]["filtered_resps"], str) else rows[0]["filtered_resps"]
    fr[0][0], fr[1][0] = fr[1][0], fr[0][0]                     # zamiana logliku: inna predykcja
    rows[0]["filtered_resps"] = json.dumps(fr) if isinstance(rows[0]["filtered_resps"], str) else fr
    with gzip.open(p, "wt", encoding="utf-8") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)
    w = E.porownaj_pare(lok, ref)
    assert w["max_dloglik"] > 0 and w["zgodnosc_pred"] < 1.0
    assert E.werdykt(w, 1e-3) != "IDENTYCZNE"


def test_subset_comparison_uses_only_common_questions(tmp_path):
    import gzip
    ref = E.ODNIESIENIE / "social-iqa" / "slayer1b-1.06"
    lok = tmp_path / "social-iqa" / "slayer1b-1.06"
    shutil.copytree(ref, lok)
    p = lok / "probki" / "T46_space.jsonl.gz"
    rows = [json.loads(l) for l in gzip.open(p, "rt", encoding="utf-8")][:20]
    with gzip.open(p, "wt", encoding="utf-8") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)
    roz = json.loads((lok / "results_rozszerzone.json").read_text(encoding="utf-8"))
    roz["observations"][0]["n_scored"] = 20
    (lok / "results_rozszerzone.json").write_text(json.dumps(roz), encoding="utf-8")
    w = E.porownaj_pare(lok, ref)
    assert w["n_wspolnych"] == 20 and E.werdykt(w, 1e-3) == "IDENTYCZNE (na próbce)"
    assert w["metryka_lok_wspolne"] == w["metryka_ref_wspolne"]


def test_added_models_and_dtype():
    ms = E.modele()
    for v in ("1.00", "1.01", "1.02", "1.03", "1.04", "1.05", "1.06", "1.08"):
        assert ms[f"slayer1b-{v}"].loader == "slayer" and ms[f"slayer1b-{v}"].dtype == "float32"
    assert ms["slayer1b-1.07-hf"].repo == "SlayerLab/Slayer1B-1.07"
    assert ms["lfm3-1.7b"].loader == "hf-trust" and ms["lfm3-1.7b"].env == "new"
    for e in ("bielik-11b-v3-base", "bielik-11b-v3-instruct"):
        assert ms[e].dtype == "bfloat16"
    for m in ms.values():
        assert len(m.rewizja) == 40, m.etykieta          # każda rewizja przypięta pełnym sha
    py, w, out = Path("py"), Path("wagi"), Path("out")
    c = E.polecenie(ms["bielik-11b-v3-base"], "T02", _args(), py, w, out)
    assert c[c.index("--dtype") + 1] == "bfloat16"
    assert "--dtype" not in E.polecenie(ms["pythia-1b-v0"], "T02", _args(), py, w, out)


def test_hf_cache_repo_dir():
    snap = Path("/x/hub/models--org--name/snapshots/abc")
    assert E.katalog_repo_w_cache(snap) == Path("/x/hub/models--org--name")
    assert E.katalog_repo_w_cache(Path("/x/modele/slayer1b-1.07")) is None


def test_export_manifest_of_control_results(tmp_path):
    import tarfile
    a = types.SimpleNamespace(wyniki=str(TU_K), modele=[], wyjscie=str(tmp_path / "e.tgz"), bez_probek=True,
                              python_lock=None, python_new=None)
    wiersze = E.wiersze_manifestu(a)
    pary = {(w["benchmark"], w["model"]) for w in wiersze}
    assert ("piqa", "pythia-1b-v0") in pary and ("ewok", "gpt2-xl") in pary and len(wiersze) == 8
    piqa = next(w for w in wiersze if w["benchmark"] == "piqa")
    assert piqa["zadanie"] == "T06" and piqa["rewizja"].startswith("f3f1b6d5") and piqa["n"] == 1838
    assert abs(piqa["wartosc"] - 0.7095) < 1e-4 and piqa["se"] and piqa["s"] == 304.7
    hs = next(w for w in wiersze if w["benchmark"] == "hellaswag-10shot")
    assert hs["zadanie"] == "T05" and hs["fewshot"] == 10
    try:
        assert E.cmd_eksport(a) == 0
        with tarfile.open(tmp_path / "e.tgz") as t:
            nazwy = t.getnames()
        assert any(n.endswith("/manifest.jsonl") for n in nazwy) and any(n.endswith("/srodowisko.json") for n in nazwy)
        assert any("/wyniki/piqa/pythia-1b-v0/results.json" in n for n in nazwy)
    finally:
        for f in ("manifest.jsonl", "srodowisko.json"):
            (TU_K / f).unlink(missing_ok=True)


TU_K = Path(__file__).resolve().parent / "wyniki_kontrolne"
