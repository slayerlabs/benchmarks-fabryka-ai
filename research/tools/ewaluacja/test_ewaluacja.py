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


KONTROLNE = Path(E.__file__).parent / "wyniki_kontrolne"


def _wynik(d, probka):
    d.mkdir(parents=True)
    (d / "results.json").write_text(json.dumps({"observations": [{"state": "ok"}]}), encoding="utf-8")
    (d / "results_rozszerzone.json").write_text(json.dumps({"probka": probka}), encoding="utf-8")
    return d


def test_resume_needs_the_same_sample_or_a_full_split(tmp_path):
    proba, pelna = _wynik(tmp_path / "a", "20"), _wynik(tmp_path / "b", "pelna")
    assert not E.wynik_gotowy(proba, "pelna")
    assert E.wynik_gotowy(proba, "20")
    assert E.wynik_gotowy(pelna, "pelna") and E.wynik_gotowy(pelna, "20")
    assert not E.wynik_gotowy(tmp_path / "brak", "pelna")


def test_resume_reads_the_sample_of_own_code_tasks():
    ewok = KONTROLNE / "ewok" / "gpt2-xl"
    assert E.probka_wyniku(ewok) == "pelna" and E.wynik_gotowy(ewok, "pelna")


def _porownanie(dll, zgodnosc):
    return {"stan_lok": "ok", "wartosc_ref": 1.0, "n_wspolnych": 62, "n_lok": 62, "n_ref": 62,
            "max_dloglik": dll, "zgodnosc_pred": zgodnosc}


def test_numeric_agreement_needs_close_logliks():
    assert E.werdykt(_porownanie(500.0, 1.0), 1e-3) == "ROZNE"       # jedna wartość na dokument: zgodność zawsze 1,0
    assert E.werdykt(_porownanie(0.01, 0.995), 1e-3) == "ZGODNE ~num"


def test_compare_exits_nonzero_on_a_different_run(tmp_path):
    import gzip
    model = "eurollm-1.7b"
    lok = tmp_path / "w" / "wikitext-2" / model
    shutil.copytree(E.ODNIESIENIE / "wikitext-2" / model, lok)
    argumenty = ["--wyniki", str(tmp_path / "w"), "porownaj"]
    assert E.main(argumenty) == 0
    p = lok / "probki" / "T03_space.jsonl.gz"
    rows = [json.loads(l) for l in gzip.open(p, "rt", encoding="utf-8")]
    fr = rows[0]["filtered_resps"]
    rows[0]["filtered_resps"] = json.dumps([json.loads(fr)[0] - 500.0]) if isinstance(fr, str) else [fr[0] - 500.0]
    with gzip.open(p, "wt", encoding="utf-8") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)
    assert E.main(argumenty) == 1


def test_control_exit_codes(tmp_path):
    w = tmp_path / "w"
    shutil.copytree(KONTROLNE, w)
    argumenty = ["--wyniki", str(w), "kontrola"]
    assert E.main(argumenty) == 0
    shutil.rmtree(w / "piqa")
    assert E.main(argumenty) == 3
    p = w / "arc-easy" / "pythia-1b-v0" / "results_rozszerzone.json"
    j = json.loads(p.read_text(encoding="utf-8"))
    j["observations"][0]["dodatkowe"]["space"]["acc"]["value"] = 0.30
    p.write_text(json.dumps(j), encoding="utf-8")
    assert E.main(argumenty) == 1


def test_control_fails_on_a_sample(tmp_path):
    w = tmp_path / "w"
    shutil.copytree(KONTROLNE, w)
    p = w / "blimp" / "pythia-1b-v0" / "results_rozszerzone.json"
    j = json.loads(p.read_text(encoding="utf-8"))
    j["probka"] = "20"
    p.write_text(json.dumps(j), encoding="utf-8")
    assert E.main(["--wyniki", str(w), "kontrola"]) == 1


def test_skipped_model_fails_the_run(tmp_path, monkeypatch):
    monkeypatch.setattr(E, "sciezka_wag", lambda m: None)
    assert E.main(["--wyniki", str(tmp_path / "w"), "--python-lock", "py", "licz", "pythia-1b-v0", "--zadania", "T01"]) == 1


def test_checkpoint_weights_need_the_documented_sum(tmp_path):
    (tmp_path / "model.safetensors").write_bytes(b"inne wagi")
    ms = E.modele()
    assert not E.wagi_ckpt_zgodne(ms["slayer1b-1.07"], tmp_path)
    assert E.wagi_ckpt_zgodne(ms["pythia-1b-v0"], tmp_path)


def test_sanity_check_reports_a_failed_task(tmp_path):
    d = tmp_path / "arc-easy" / "pythia-1b-v0"
    shutil.copytree(KONTROLNE / "arc-easy" / "pythia-1b-v0", d)
    a = types.SimpleNamespace(probka="pelna")
    assert E.kontrola_sensu([d], a) == 0
    p = d / "results_rozszerzone.json"
    j = json.loads(p.read_text(encoding="utf-8"))
    j["observations"][0]["state"] = "failed"
    p.write_text(json.dumps(j), encoding="utf-8")
    assert E.kontrola_sensu([d], a) != 0


def _zmien(p, fn):
    j = json.loads(p.read_text(encoding="utf-8"))
    fn(j)
    p.write_text(json.dumps(j), encoding="utf-8")


def _kopia_kontrolnych(tmp_path):
    w = tmp_path / "w"
    shutil.copytree(KONTROLNE, w)
    return w


def test_control_fails_on_a_nan_score(tmp_path):
    w = _kopia_kontrolnych(tmp_path)
    p = w / "arc-easy" / "pythia-1b-v0" / "results_rozszerzone.json"
    _zmien(p, lambda j: j["observations"][0]["dodatkowe"]["space"]["acc"].update(value=float("nan")))
    assert E.main(["--wyniki", str(w), "kontrola"]) == 1


def test_control_counts_a_failed_run_as_a_failure(tmp_path):
    w = _kopia_kontrolnych(tmp_path)
    p = w / "arc-easy" / "pythia-1b-v0" / "results_rozszerzone.json"
    _zmien(p, lambda j: j["observations"][0].update(state="failed"))
    assert E.main(["--wyniki", str(w), "kontrola"]) == 1


def test_control_reports_a_broken_file_as_missing(tmp_path):
    w = _kopia_kontrolnych(tmp_path)
    (w / "piqa" / "pythia-1b-v0" / "results_rozszerzone.json").write_text("{", encoding="utf-8")
    assert E.main(["--wyniki", str(w), "kontrola"]) == 3


def test_resume_needs_the_same_model_revision_and_weights(tmp_path):
    ms = E.modele()
    d = tmp_path / "piqa" / "pythia-1b-v0"
    shutil.copytree(KONTROLNE / "piqa" / "pythia-1b-v0", d)
    assert E.wynik_gotowy(d, "pelna", ms["pythia-1b-v0"])
    assert not E.wynik_gotowy(d, "pelna", ms["eurollm-1.7b"])
    _zmien(d / "results.json", lambda j: j["models"][0].update(revision="0" * 40))
    assert not E.wynik_gotowy(d, "pelna", ms["pythia-1b-v0"])
    assert E.wynik_gotowy(KONTROLNE / "ewok" / "gpt2-xl", "pelna", ms["gpt2-xl"])   # ewok.py: model w observations

    m = ms["slayer1b-1.07"]
    ck = _wynik(tmp_path / "ck", "pelna")
    for suma, gotowy in ((E.SUMY_WAG_CKPT[m.etykieta], True), ("f" * 64, False), (None, True)):
        _zmien(ck / "results.json", lambda j: j.update(models=[{"repo": m.repo, "revision": m.rewizja,
                                                                "weights_sha256": suma}]))
        assert E.wynik_gotowy(ck, "pelna", m) is gotowy, suma


def test_compare_exits_nonzero_without_common_samples(tmp_path):
    model = "eurollm-1.7b"
    lok = tmp_path / "w" / "wikitext-2" / model
    shutil.copytree(E.ODNIESIENIE / "wikitext-2" / model, lok)
    for f in (lok / "probki").glob("*"):
        f.rename(f.with_name(f.name.replace("_space", "_inne")))
    assert E.main(["--wyniki", str(tmp_path / "w"), "porownaj"]) == 1


def test_compare_exits_nonzero_on_a_missing_local_result(tmp_path):
    model = "eurollm-1.7b"
    lok = tmp_path / "w" / "wikitext-2" / model
    shutil.copytree(E.ODNIESIENIE / "wikitext-2" / model, lok)
    (lok / "results_rozszerzone.json").unlink()
    assert E.main(["--wyniki", str(tmp_path / "w"), "porownaj"]) == 1


def test_looser_loglik_tolerance_does_not_tighten_agreement():
    assert E.werdykt(_porownanie(0.3, 0.995), 0.5) == "ZGODNE ~num"
    assert E.werdykt(_porownanie(0.3, 1.0), 0.5) == "IDENTYCZNE"
    assert E.werdykt(_porownanie(0.3, 0.995), 1e-3) == "ROZNE"


def test_checkpoint_weights_need_the_whole_sum(tmp_path, monkeypatch):
    import hashlib
    assert E.SUMY_WAG_CKPT["slayer1b-1.07"].startswith("d826b4a1") and len(E.SUMY_WAG_CKPT["slayer1b-1.07"]) == 64
    (tmp_path / "model.safetensors").write_bytes(b"wagi")
    suma = hashlib.sha256(b"wagi").hexdigest()
    m = E.modele()["slayer1b-1.07"]
    monkeypatch.setitem(E.SUMY_WAG_CKPT, m.etykieta, suma)
    assert E.wagi_ckpt_zgodne(m, tmp_path)
    monkeypatch.setitem(E.SUMY_WAG_CKPT, m.etykieta, suma[:8])
    assert not E.wagi_ckpt_zgodne(m, tmp_path)


def test_full_split_sanity_check_looks_at_the_score(tmp_path):
    d = tmp_path / "arc-easy" / "pythia-1b-v0"
    shutil.copytree(KONTROLNE / "arc-easy" / "pythia-1b-v0", d)
    _zmien(d / "results_rozszerzone.json", lambda j: j["observations"][0]["dodatkowe"]["space"]["acc"].update(value=1.0))
    assert E.kontrola_sensu([d], types.SimpleNamespace(probka="pelna")) != 0
    assert E.kontrola_sensu([d], types.SimpleNamespace(probka="20")) == 0


def _licz_bez_gpu(tmp_path, monkeypatch):
    """`licz` z udawanym przygotowaniem i procesem `pass`; zwraca listę (model, test) wysłanych do liczenia."""
    import sys
    from concurrent.futures import Future
    wagi = tmp_path / "wagi"
    wagi.mkdir()
    monkeypatch.setattr(E, "TU", tmp_path)
    monkeypatch.setattr(E, "sciezka_wag", lambda m: wagi if m.etykieta == "pythia-1b-v0" else None)

    def przygotowane(zadania, a, py):
        f = Future()
        f.set_result(True)
        return {t: f for t in zadania}

    liczone = []

    def polecenie(m, task, *reszta):
        liczone.append((m.etykieta, task))
        return [sys.executable, "-c", "pass"]

    monkeypatch.setattr(E, "przygotuj_w_tle", przygotowane)
    monkeypatch.setattr(E, "polecenie", polecenie)
    return ["--wyniki", str(tmp_path / "w"), "--python-lock", sys.executable, "licz"], liczone


def test_skipped_model_fails_a_run_that_computed_the_other(tmp_path, monkeypatch):
    poczatek, _ = _licz_bez_gpu(tmp_path, monkeypatch)
    assert E.main(poczatek + ["pythia-1b-v0", "--zadania", "T01"]) == 0
    assert E.main(poczatek + ["pythia-1b-v0", "gpt2-xl", "--zadania", "T01"]) == 1


def test_run_recomputes_a_result_of_another_revision(tmp_path, monkeypatch):
    poczatek, liczone = _licz_bez_gpu(tmp_path, monkeypatch)
    d = tmp_path / "w" / "piqa" / "pythia-1b-v0"
    shutil.copytree(KONTROLNE / "piqa" / "pythia-1b-v0", d)
    t = next(t for t, k in E.katalogi().items() if k == "piqa")
    assert E.main(poczatek + ["pythia-1b-v0", "--zadania", t]) == 0 and liczone == []
    _zmien(d / "results.json", lambda j: j["models"][0].update(revision="0" * 40))
    E.main(poczatek + ["pythia-1b-v0", "--zadania", t])
    assert liczone == [("pythia-1b-v0", t)]
