"""tools/przebieg_centralny.sh: model list vs METODOLOGIA.md, task dirs vs common/zadania.py ZADANIA.
Runs the script's `lista`, `katalogi` and `plan` stages in a temporary workspace (no GPU, no network)."""
import ast
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent
SKRYPT = KORZEN / "tools" / "przebieg_centralny.sh"
BIELIK = "speakleash/Bielik-1.5B-v3"  # gated repo: counted with access, skipped without (licz_model, dostep_hf)
KONTROLNY = "EleutherAI/pythia-1b-v0"
PYTHIA_STEP143000 = "f3f1b6d5a78e32208be0866398d0b2d32c0e1ce0"  # commit of HF branch step143000


def uruchom(*args, ws=None):
    env = {**os.environ, "WS": ws or tempfile.mkdtemp(), "K": str(KORZEN)}
    return subprocess.run(["bash", str(SKRYPT), *args], capture_output=True, text=True, check=True, env=env).stdout


def modele_skryptu():
    return [l.split("|") for l in uruchom("lista").splitlines()]


def tabela_metodologii():
    tekst = (KORZEN / "METODOLOGIA.md").read_text(encoding="utf-8")
    sekcja = tekst.split("### Pięć modeli odniesienia", 1)[1].split("\n### ", 1)[0]
    return dict(re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{40})` \|", sekcja, re.MULTILINE))


def slayer_metodologii():
    """(repo, revision, checkpoint file or None) from the "Mierzony dziś model" line."""
    tekst = (KORZEN / "METODOLOGIA.md").read_text(encoding="utf-8")
    return re.search(r"\*\*Mierzony dziś model:\*\* `(SlayerLab/Slayer1B-[0-9.]+(?:-checkpoints)?)` @ `([0-9a-f]{40})`"
                     r"(?:, plik\s+`(ckpt_\d+\.pt)`)?", tekst).groups()


def zmienna_skryptu(nazwa):
    env = {**os.environ, "WS": tempfile.mkdtemp(), "K": str(KORZEN)}
    return subprocess.run(["bash", "-c", f"source {SKRYPT} _funkcje; echo \"${nazwa}\""], capture_output=True,
                          text=True, check=True, env=env).stdout.strip()


def klucze_zadan():
    drzewo = ast.parse((KORZEN / "common" / "zadania.py").read_text(encoding="utf-8"))
    for w in drzewo.body:
        if isinstance(w, ast.Assign) and any(getattr(t, "id", None) == "ZADANIA" for t in w.targets):
            return [k.value for k in w.value.keys]
    raise AssertionError("ZADANIA not found in common/zadania.py")


def test_reference_models_match_methodology():
    tabela = tabela_metodologii()
    assert len(tabela) == 5 and BIELIK in tabela
    odniesienia = {repo: rev for _, repo, rev, _, _ in modele_skryptu()
                   if not repo.startswith("SlayerLab/") and repo != KONTROLNY}
    assert odniesienia == tabela


def test_control_model_is_first_on_methodology_list():
    tekst = (KORZEN / "METODOLOGIA.md").read_text(encoding="utf-8")
    sekcja = tekst.split("### Model kontrolny etapu B", 1)[1].split("\n### ", 1)[0]
    assert re.search(r"^1\. \*\*`([^`]+)` @ `step143000`\*\*", sekcja, re.MULTILINE).group(1) == KONTROLNY
    wiersze = [m for m in modele_skryptu() if m[1] == KONTROLNY]
    assert wiersze == [["pythia-1b-v0", KONTROLNY, PYTHIA_STEP143000, "hf", "lock"]]


def test_bielik_runs_in_the_lock_env_with_hflm():
    """LlamaForCausalLM with tokenizer.json (HF model card @ 4b25049): transformers 4.57.6 of the lock loads it, no
    remote code, so neither `new` nor `hf-trust`."""
    assert [(l, w, e) for _, r, _, l, e in modele_skryptu() for w in [r] if r == BIELIK] == [("hf", BIELIK, "lock")]


def atrapa_srodowiska(ws, dostep):
    """$WS/venv-lock/bin/python and venv-new stand-ins: log every call; `auth_check` of Bielik exits 3 (GatedRepoError)
    when `dostep` is False; the rest (snapshot_download, ewaluuj.py) succeeds without doing anything. `logi/` as made by
    `przygotuj`."""
    (Path(ws) / "logi").mkdir(exist_ok=True)
    for env in ("lock", "new"):
        p = Path(ws) / f"venv-{env}" / "bin" / "python"
        p.parent.mkdir(parents=True)
        p.write_text("#!/bin/sh\n"
                     f"echo \"$*\" >> {ws}/wywolania.log\n"
                     "case \"$*\" in *auth_check*" + BIELIK + "*) "
                     + ("exit 0" if dostep else "echo 'GatedRepoError: 403 Client Error.'; exit 3") + ";; esac\n"
                     "exit 0\n")
        p.chmod(0o755)


def kolejka(ws, *etykiety, zadania="T02 T04"):
    """`licz_kolejke - LABEL...` (one queue, no GPU) from the sourced script; returns the completed process."""
    env = {**os.environ, "WS": ws, "K": str(KORZEN), "ZADANIA_ID": zadania, "DEVICE": "cpu", "PATH": os.environ["PATH"]}
    return subprocess.run(["bash", "-c", f"source {SKRYPT} _funkcje; licz_kolejke - {' '.join(etykiety)}"],
                          capture_output=True, text=True, env=env)


def czasy(ws):
    return [json.loads(l) for l in (Path(ws) / "czasy.jsonl").read_text().splitlines()]


def test_gated_model_without_access_is_skipped_and_the_queue_goes_on():
    ws = tempfile.mkdtemp()
    atrapa_srodowiska(ws, dostep=False)
    wynik = kolejka(ws, "bielik-1.5b-v3", "eurollm-1.7b")
    assert wynik.returncode == 0, wynik.stderr
    assert "POMINIETY bielik-1.5b-v3 (speakleash/Bielik-1.5B-v3 @ 4b25049621bf3952a1fc9314c89773102eda0333)" in wynik.stdout
    assert "GatedRepoError" in (Path(ws) / "stan" / "pominiety_bielik-1.5b-v3.txt").read_text()
    wywolania = (Path(ws) / "wywolania.log").read_text()
    assert "snapshot_download" not in wywolania.split("utter-project/EuroLLM-1.7B")[0]  # nothing downloaded for Bielik
    assert "--etykieta bielik-1.5b-v3" not in wywolania
    assert wywolania.count("--etykieta eurollm-1.7b") == 2  # the next model still runs both tasks
    wpisy = czasy(ws)
    assert [w["model"] for w in wpisy if w["etap"] == "pominiety"] == ["bielik-1.5b-v3"]
    assert {(w["model"], w["zadanie"], w["kod"]) for w in wpisy if w["etap"] == "ewaluacja"} == {
        ("eurollm-1.7b", "T02", 0), ("eurollm-1.7b", "T04", 0)}  # `ponow` reads only these: no retry of the skip


def test_gated_model_with_access_is_counted_in_the_lock_env():
    ws = tempfile.mkdtemp()
    (Path(ws) / "stan").mkdir()
    (Path(ws) / "stan" / "pominiety_bielik-1.5b-v3.txt").write_text("old skip\n")
    atrapa_srodowiska(ws, dostep=True)
    wynik = kolejka(ws, "bielik-1.5b-v3")
    assert wynik.returncode == 0, wynik.stderr
    assert "POMINIETY" not in wynik.stdout and not (Path(ws) / "stan" / "pominiety_bielik-1.5b-v3.txt").exists()
    wywolania = (Path(ws) / "wywolania.log").read_text().splitlines()
    assert any("snapshot_download" in w and BIELIK in w for w in wywolania)
    ewaluacje = [w for w in wywolania if "--etykieta bielik-1.5b-v3" in w]
    assert len(ewaluacje) == 2 and all(f"--repo {BIELIK} --revision 4b25049621bf3952a1fc9314c89773102eda0333" in w
                                       and "--model hf " in w and "--trust_remote_code" not in w for w in ewaluacje)
    assert (Path(ws) / "venv-lock").exists() and all(w["env"] == "lock" for w in czasy(ws) if w["etap"] == "ewaluacja")


def test_slayer_revision_matches_methodology():
    slayery = [(repo, rev, loader) for _, repo, rev, loader, _ in modele_skryptu() if repo.startswith("SlayerLab/")]
    repo, rev, plik = slayer_metodologii()
    loader = "slayer-ckpt" if plik else "slayer"
    assert slayery == [(repo, rev, loader)]
    if plik:
        assert repo.endswith("-checkpoints") and zmienna_skryptu("SLAYER_CKPT") == plik


def test_labels_unique_and_fields_valid():
    modele = modele_skryptu()
    assert len({m[0] for m in modele}) == len(modele)
    assert all(m[3] in ("slayer", "slayer-ckpt", "hf", "hf-trust") and m[4] in ("lock", "new") for m in modele)


def test_slayer_ckpt_is_converted_against_the_template_then_evaluated_as_slayer():
    """slayer-ckpt: checkpoint file from the -checkpoints repo at the pinned revision, the template model, konwertuj.py
    into $WS/modele/<label>, both downloads deleted, ewaluuj.py with --model slayer on the converted directory."""
    ws = tempfile.mkdtemp()
    atrapa_srodowiska(ws, dostep=True)
    etykieta, repo, rev, _, _ = next(m for m in modele_skryptu() if m[3] == "slayer-ckpt")
    ckpt, wzorzec = zmienna_skryptu("SLAYER_CKPT"), zmienna_skryptu("SLAYER_WZORZEC").split("|")
    wynik = kolejka(ws, etykieta)
    assert wynik.returncode == 0, wynik.stderr
    wywolania = (Path(ws) / "wywolania.log").read_text().splitlines()
    d = f"{ws}/modele/{etykieta}"
    pobranie = [w for w in wywolania if "hf_hub_download" in w]
    assert len(pobranie) == 1 and f"h('{repo}', '{ckpt}', revision='{rev}', local_dir='{d}.ckpt')" in pobranie[0]
    assert any(f"s('{wzorzec[0]}', revision='{wzorzec[1]}', local_dir='{d}.wzorzec'" in w for w in wywolania)
    konw = [i for i, w in enumerate(wywolania) if "wygaszanie/konwertuj.py" in w]
    assert len(konw) == 1 and wywolania[konw[0]].endswith(f"{d}.ckpt/{ckpt} {d}.wzorzec {d}")
    ewaluacje = [i for i, w in enumerate(wywolania) if f"--etykieta {etykieta}" in w]
    assert len(ewaluacje) == 2 and min(ewaluacje) > konw[0]
    assert all("--model slayer " in wywolania[i] and f"--model_path {d} " in wywolania[i] for i in ewaluacje)
    assert not any(Path(f"{d}{s}").exists() for s in (".ckpt", ".wzorzec"))


def test_slayer_ckpt_already_converted_is_not_downloaded_again():
    ws = tempfile.mkdtemp()
    atrapa_srodowiska(ws, dostep=True)
    etykieta = next(m[0] for m in modele_skryptu() if m[3] == "slayer-ckpt")
    d = Path(ws) / "modele" / etykieta
    d.mkdir(parents=True)
    (d / "model.safetensors").write_bytes(b"x")
    (d / "config.json").write_text(json.dumps({"zrodlo_ckpt": f"/w/{zmienna_skryptu('SLAYER_CKPT')}"}, indent=1))
    env = {**os.environ, "WS": ws, "K": str(KORZEN), "ZADANIA_ID": "T02", "ZOSTAW_WAGI": "1"}
    wynik = subprocess.run(["bash", "-c", f"source {SKRYPT} _funkcje; licz_kolejke - {etykieta}"],
                           capture_output=True, text=True, env=env)
    assert wynik.returncode == 0, wynik.stderr
    assert "juz skonwertowane" in wynik.stdout
    wywolania = (Path(ws) / "wywolania.log").read_text()
    assert "hf_hub_download" not in wywolania and "konwertuj.py" not in wywolania
    assert f"--etykieta {etykieta}" in wywolania


def test_task_dirs_cover_exactly_zadania():
    pary = [l.split() for l in uruchom("katalogi").splitlines()]
    assert [t for t, _ in pary] == klucze_zadan()
    assert len({k for _, k in pary}) == len(pary)


def test_plan_runs_full_set_for_every_model_and_task():
    ws = tempfile.mkdtemp()
    linie = uruchom("plan", ws=ws).splitlines()
    modele, zadania = modele_skryptu(), klucze_zadan()
    assert len(linie) == len(modele) * len(zadania)
    for l in linie:
        assert "--probka pelna" in l and re.search(r" --eval_gpu \S+ ", l)  # own-code tasks too (T53)
    # own-code tasks (EWoK T53) run their script with the ewaluuj.py flags; ewok.py picks the Slayer loader from
    # config.json and always passes trust_remote_code, so it takes neither --model nor --trust_remote_code
    ewok = [l for l in linie if "--zadania T53 " in l]
    assert len(ewok) == len(modele) and all(f"{KORZEN}/benchmarks/ewok/ewok.py przebieg " in l
                                            and f"--model_path {ws}/modele/" in l for l in ewok)
    linie = [l for l in linie if l not in ewok]
    assert all(f"{KORZEN}/common/ewaluuj.py " in l for l in linie)
    lfm3 = [l for l in linie if "LiquidAI/LFM3" in l]
    assert lfm3 and all("--trust_remote_code" in l for l in lfm3)
    wikitext_hf = [l for l in linie if "--zadania T03 " in l and "SlayerLab/" not in l]
    assert wikitext_hf and all("--max_length 4096" in l for l in wikitext_hf)
    assert not [l for l in linie if "--max_length" in l and "--zadania T03 " not in l]
    slayer = [l for l in linie if "SlayerLab/" in l]
    assert slayer and all("--model slayer" in l and f"--model_path {ws}/modele/" in l for l in slayer)
    assert all("--device cuda" in l for l in linie)
    assert all(" --batch 1 " in l for l in linie)  # METODOLOGIA "Ustawienia przebiegu centralnego": batch 1


def test_own_code_list_of_the_script_matches_zadania():
    """KOD in the script = the `kod` fields of ZADANIA (ast, so no lm-eval import)."""
    tekst = SKRYPT.read_text(encoding="utf-8")
    skrypt = dict(p.split(":") for p in re.search(r'^KOD="([^"]*)"', tekst, re.M).group(1).split())
    drzewo = ast.parse((KORZEN / "common" / "zadania.py").read_text(encoding="utf-8"))
    wpisy = next(w.value for w in drzewo.body
                 if isinstance(w, ast.Assign) and any(getattr(t, "id", None) == "ZADANIA" for t in w.targets))
    kod = {k.value: kw.value.value for k, v in zip(wpisy.keys, wpisy.values) for kw in v.keywords if kw.arg == "kod"}
    assert skrypt == kod == {"T53": "benchmarks/ewok/ewok.py"}


def plan_na_gpu(liczba):
    """`plan` with a stand-in nvidia-smi on PATH that lists `liczba` GPUs."""
    ws = tempfile.mkdtemp()
    bin_ = Path(tempfile.mkdtemp())
    atrapa = bin_ / "nvidia-smi"
    atrapa.write_text("#!/bin/sh\n[ \"$1\" = -L ] && { i=0; while [ $i -lt %d ]; do echo \"GPU $i: Atrapa (UUID: GPU-$i)\";"
                      " i=$((i+1)); done; exit 0; }\necho Atrapa GPU\n" % liczba)
    atrapa.chmod(0o755)
    env = {**os.environ, "WS": ws, "K": str(KORZEN), "PATH": f"{bin_}:{os.environ['PATH']}"}
    wynik = subprocess.run(["bash", str(SKRYPT), "plan"], capture_output=True, text=True, check=True, env=env).stdout
    return wynik.replace(ws, "<WS>")


def test_plan_four_gpus_gives_four_queues_each_pair_once():
    linie = plan_na_gpu(4).splitlines()
    naglowki = [l for l in linie if l.startswith("# GPU ")]
    assert [l.split(":")[0] for l in naglowki] == [f"# GPU {i}" for i in range(4)]
    komendy = [l for l in linie if not l.startswith("#")]
    pary = [(re.search(r"--etykieta (\S+)", l)[1], re.search(r"--zadania (\S+)", l)[1]) for l in komendy]
    modele = [m[0] for m in modele_skryptu()]
    assert sorted(pary) == sorted((m, t) for m in modele for t in klucze_zadan())
    kolejka = None
    for l in linie:  # every model sits whole in the queue of its header, and its commands see only that GPU
        if l.startswith("# GPU "):
            kolejka, etykiety = l.split()[2].rstrip(":"), l.split(":", 1)[1].split()
        else:
            assert l.startswith(f"CUDA_VISIBLE_DEVICES={kolejka} ") and re.search(r"--etykieta (\S+)", l)[1] in etykiety


def test_plan_one_gpu_same_as_without_gpu():
    bez = plan_na_gpu(0)
    assert plan_na_gpu(1) == bez and "CUDA_VISIBLE_DEVICES" not in bez and "#" not in bez


def test_proba_cpu_two_questions_per_pair_on_cpu_in_chosen_env():
    ws = tempfile.mkdtemp()
    env = {**os.environ, "WS": ws, "K": str(KORZEN), "SUCHO": "1", "ENV_OVERRIDE": "new"}
    linie = subprocess.run(["bash", str(SKRYPT), "proba_cpu"], capture_output=True, text=True, check=True,
                           env=env).stdout.splitlines()
    assert len(linie) == len(modele_skryptu()) * len(klucze_zadan())
    for l in linie:
        assert l.startswith(f"{ws}/venv-new/bin/python ")
        assert "--device cpu" in l and "--batch 1 " in l and f"--wyjscie {ws}/proba_cpu/" in l
        assert ("--probka 1 " if "--zadania T03 " in l else "--probka 2 ") in l


def test_kontrola_stage_flags_bad_full_results():
    ws = Path(tempfile.mkdtemp())
    for nazwa, wartosc in (("ok", 0.4), ("zly", 1.0)):
        d = ws / "wyniki" / "arc-challenge" / nazwa
        d.mkdir(parents=True)
        obs = {"task_id": "T02", "metric": "acc_norm,none", "state": "ok", "dodatkowe": {"space": {
            "acc_norm": {"value": wartosc}, "bazy": {"chance_value": 0.25}}}}
        (d / "results_rozszerzone.json").write_text(json.dumps({"observations": [obs]}))
    env = {**os.environ, "WS": str(ws), "K": str(KORZEN)}
    wynik = subprocess.run(["bash", str(SKRYPT), "kontrola"], capture_output=True, text=True, env=env)
    assert wynik.returncode == 1 and "zly" in wynik.stdout and "/ok" not in wynik.stdout


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__]))
