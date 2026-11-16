"""tools/przebieg_centralny.sh: model list vs METODOLOGIA.md, task dirs vs common/zadania.py ZADANIA.
Runs the script's `lista`, `katalogi` and `plan` stages in a temporary workspace (no GPU, no network)."""
import ast
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

KORZEN = Path(__file__).resolve().parent.parent
SKRYPT = KORZEN / "tools" / "przebieg_centralny.sh"
BIELIK = "speakleash/Bielik-1.5B-v3"  # gated repo: counted with access, skipped without (licz_model, dostep_hf)
KONTROLNY = "EleutherAI/pythia-1b-v0"
PYTHIA_STEP143000 = "f3f1b6d5a78e32208be0866398d0b2d32c0e1ce0"  # commit of HF branch step143000


def uruchom(*args, ws=None):
    env = {**os.environ, "WS": ws or tempfile.mkdtemp(), "K": str(KORZEN)}
    return subprocess.run(["bash", str(SKRYPT), *args], capture_output=True, text=True, check=True, env=env).stdout


def modele_skryptu():
    """MODELE rows: label|repo|revision|loader|env[|dtype[|ckpt_file|ckpt_sha256|template_repo@revision]]."""
    return [l.split("|") for l in uruchom("lista").splitlines()]


def ckpt_wiersza(m):
    """(ckpt_file, ckpt_sha256, template_repo, template_revision) of a slayer-ckpt row."""
    assert len(m) == 9, m
    return (m[6], m[7], *m[8].split("@"))


def tabela_metodologii(naglowek="### Pięć modeli odniesienia"):
    tekst = (KORZEN / "METODOLOGIA.md").read_text(encoding="utf-8")
    sekcja = tekst.split(naglowek, 1)[1].split("\n### ", 1)[0]
    return dict(re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{40})` \|", sekcja, re.MULTILINE))


def porownawcze_metodologii():
    return tabela_metodologii("### Modele porównawcze z #190")


def slayer_metodologii():
    """(repo, revision, checkpoint file or None) from the "Mierzony dziś model" line."""
    tekst = (KORZEN / "METODOLOGIA.md").read_text(encoding="utf-8")
    return re.search(r"\*\*Mierzony dziś model:\*\* `(SlayerLab/Slayer1B-[0-9.]+(?:-checkpoints)?)` @ `([0-9a-f]{40})`"
                     r"(?:, plik\s+`(ckpt_\d+\.pt)`)?", tekst).groups()


def zmienna_skryptu(nazwa):
    env = {**os.environ, "WS": tempfile.mkdtemp(), "K": str(KORZEN)}
    return subprocess.run(["bash", "-c", f"source {SKRYPT} _funkcje; echo \"${{{nazwa}-}}\""], capture_output=True,
                          text=True, check=True, env=env).stdout.strip()


def klucze_zadan():
    drzewo = ast.parse((KORZEN / "common" / "zadania.py").read_text(encoding="utf-8"))
    for w in drzewo.body:
        if isinstance(w, ast.Assign) and any(getattr(t, "id", None) == "ZADANIA" for t in w.targets):
            return [k.value for k in w.value.keys]
    raise AssertionError("ZADANIA not found in common/zadania.py")


def test_reference_models_match_methodology():
    tabela, porownawcze = tabela_metodologii(), porownawcze_metodologii()
    assert len(tabela) == 5 and BIELIK in tabela
    odniesienia = {m[1]: m[2] for m in modele_skryptu()
                   if not m[1].startswith("SlayerLab/") and m[1] != KONTROLNY and m[1] not in porownawcze}
    assert odniesienia == tabela


def test_comparison_models_match_methodology_and_come_after_the_measured_list():
    """Every row outside the measured Slayer, the five references and the control model is in "Modele porównawcze
    z #190" with the same revision, and the other way round; they follow the measured list (MODELE+=)."""
    porownawcze = porownawcze_metodologii()
    modele = modele_skryptu()
    repo_slayera = slayer_metodologii()[0]
    reszta = [m for m in modele if m[1] not in tabela_metodologii() and m[1] not in (KONTROLNY, repo_slayera)]
    assert {(m[1], m[2]) for m in reszta} == set(porownawcze.items())
    assert {"speakleash/Bielik-11B-v3.1-Instruct", "LiquidAI/LFM3-1.7B",
            "SlayerLab/Slayer1B-1.09-checkpoints"} <= set(porownawcze)
    assert modele[-len(reszta):] == reszta
    assert "### Modele porównawcze z #190" in (KORZEN / "METODOLOGIA.md").read_text(encoding="utf-8")


def test_bielik_11b_runs_in_bfloat16_everywhere_and_float32_rows_keep_their_command():
    """11B float32 weights (~45 GB) do not fit a 32 GB card: every command of the row, own-code EWoK too, gets
    --dtype bfloat16; a float32 row gets no --dtype (same command as the earlier runs)."""
    ws = tempfile.mkdtemp()
    wiersz = next(m for m in modele_skryptu() if m[0] == "bielik-11b-v3.1-instruct")
    assert wiersz == ["bielik-11b-v3.1-instruct", "speakleash/Bielik-11B-v3.1-Instruct",
                      "d6e755d356ad418d0f0e30b8c428db267415ddb9", "hf", "lock", "bfloat16"]
    linie = uruchom("plan", "bielik-11b-v3.1-instruct lfm3-1.7b", ws=ws).splitlines()
    bielik = [l for l in linie if "--etykieta bielik-11b-v3.1-instruct " in l]
    assert len(bielik) == len(klucze_zadan()) and all(l.endswith(" --dtype bfloat16") for l in bielik)
    assert any("ewok.py przebieg " in l for l in bielik)
    assert not [l for l in linie if "--dtype" in l and l not in bielik]


def test_control_model_is_first_on_methodology_list():
    tekst = (KORZEN / "METODOLOGIA.md").read_text(encoding="utf-8")
    sekcja = tekst.split("### Model kontrolny etapu B", 1)[1].split("\n### ", 1)[0]
    assert re.search(r"^1\. \*\*`([^`]+)` @ `step143000`\*\*", sekcja, re.MULTILINE).group(1) == KONTROLNY
    wiersze = [m for m in modele_skryptu() if m[1] == KONTROLNY]
    assert wiersze == [["pythia-1b-v0", KONTROLNY, PYTHIA_STEP143000, "hf", "lock"]]


def test_bielik_runs_in_the_lock_env_with_hflm():
    """LlamaForCausalLM with tokenizer.json (HF model card @ 4b25049): transformers 4.57.6 of the lock loads it, no
    remote code, so neither `new` nor `hf-trust`."""
    assert [m for m in modele_skryptu() if m[1] == BIELIK] == [
        ["bielik-1.5b-v3", BIELIK, "4b25049621bf3952a1fc9314c89773102eda0333", "hf", "lock"]]


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
    """The measured Slayer (METODOLOGIA line) is the first SlayerLab row, its checkpoint file in its own row; any
    other SlayerLab row is a comparison model."""
    slayery = [m for m in modele_skryptu() if m[1].startswith("SlayerLab/")]
    repo, rev, plik = slayer_metodologii()
    loader = "slayer-ckpt" if plik else "slayer"
    assert (slayery[0][1], slayery[0][2], slayery[0][3]) == (repo, rev, loader)
    if plik:
        assert repo.endswith("-checkpoints") and ckpt_wiersza(slayery[0])[0] == plik
    assert {(m[1], m[2]) for m in slayery[1:]} <= set(porownawcze_metodologii().items())


def test_labels_unique_and_fields_valid():
    modele = modele_skryptu()
    assert len({m[0] for m in modele}) == len(modele)
    assert all(m[3] in ("slayer", "slayer-ckpt", "hf", "hf-trust") and m[4] in ("lock", "new") for m in modele)
    assert all(len(m) == 5 or m[5] in ("float32", "bfloat16") for m in modele)
    assert all(m[5] == "float32" for m in modele if m[3].startswith("slayer") and len(m) > 5)  # Slayer: float32 only
    for m in modele:  # checkpoint fields only and always on slayer-ckpt rows
        assert (len(m) == 9) == (m[3] == "slayer-ckpt"), m
        if len(m) == 9:
            plik, sha, wz_repo, wz_rev = ckpt_wiersza(m)
            assert plik.endswith(".pt") and re.fullmatch(r"[0-9a-f]{64}", sha) and re.fullmatch(r"[0-9a-f]{40}", wz_rev)
            assert wz_repo.startswith("SlayerLab/Slayer1B-") and not wz_repo.endswith("-checkpoints")


def test_slayer_rows_carry_their_own_checkpoint():
    """1.07 and 1.09-k40000: file, sha256 (card / SHA256SUMS of the revision) and template per row, no global."""
    ck = {m[0]: ckpt_wiersza(m) for m in modele_skryptu() if m[3] == "slayer-ckpt"}
    assert ck["slayer1b-1.07"] == ("ckpt_22327.pt", "48cdb5eb16b69e0ee9a7a2ed72895ff47c0ba57aca0f4516b1f7e9cba286685c",
                                   "SlayerLab/Slayer1B-1.06", "ef81be58742544ad32e1afab38db011fec209609")
    assert ck["slayer1b-1.09-k40000"] == (
        "wagi_40000.pt", "f83f7017872f7121f002bc77499c625304bd28e2c87fb4afaa0e3d445bd31881",
        "SlayerLab/Slayer1B-1.08", "5f854a0cc7160594d54d1788d37a44e8ebabe16c")
    for nazwa in ("SLAYER_CKPT", "SLAYER_CKPT_SHA256", "SLAYER_WZORZEC"):
        assert zmienna_skryptu(nazwa) == ""


def test_slayer_ckpt_row_without_checkpoint_fields_stops():
    env = {**os.environ, "WS": tempfile.mkdtemp(), "K": str(KORZEN)}
    wiersz = "x|SlayerLab/Slayer1B-9.99-checkpoints|" + "0" * 40 + "|slayer-ckpt|lock"
    wynik = subprocess.run(["bash", "-c", f"source {SKRYPT} _funkcje; MODELE=('{wiersz}'); model x"],
                           capture_output=True, text=True, env=env)
    assert wynik.returncode == 1 and "ckpt_file|ckpt_sha256" in wynik.stderr


SLAYERY_CKPT = [m[0] for m in modele_skryptu() if m[3] == "slayer-ckpt"]


@pytest.mark.parametrize("etykieta", SLAYERY_CKPT)
def test_slayer_ckpt_is_converted_against_the_template_then_evaluated_as_slayer(etykieta):
    """slayer-ckpt: checkpoint file of the row from the -checkpoints repo at the pinned revision, the row's template,
    konwertuj.py into $WS/modele/<label>, both downloads deleted, ewaluuj.py with --model slayer on the result."""
    ws = tempfile.mkdtemp()
    atrapa_srodowiska(ws, dostep=True)
    m = next(m for m in modele_skryptu() if m[0] == etykieta)
    repo, rev = m[1], m[2]
    ckpt, sha, wz_repo, wz_rev = ckpt_wiersza(m)
    wynik = kolejka(ws, etykieta)
    assert wynik.returncode == 0, wynik.stderr
    wywolania = (Path(ws) / "wywolania.log").read_text().splitlines()
    d = f"{ws}/modele/{etykieta}"
    pobranie = [w for w in wywolania if "hf_hub_download" in w]
    assert len(pobranie) == 1 and f"h('{repo}', '{ckpt}', revision='{rev}', local_dir='{d}.ckpt')" in pobranie[0]
    assert any(f"s('{wz_repo}', revision='{wz_rev}', local_dir='{d}.wzorzec'" in w for w in wywolania)
    konw = [i for i, w in enumerate(wywolania) if "tools/konwertuj.py" in w]
    assert len(konw) == 1 and wywolania[konw[0]].endswith(f"{d}.ckpt/{ckpt} {d}.wzorzec {d} --sha256 {sha}")
    ewaluacje = [i for i, w in enumerate(wywolania) if f"--etykieta {etykieta}" in w]
    assert len(ewaluacje) == 2 and min(ewaluacje) > konw[0]
    assert all("--model slayer " in wywolania[i] and f"--model_path {d} " in wywolania[i] for i in ewaluacje)
    assert not any("--dtype" in wywolania[i] for i in ewaluacje)
    assert not any(Path(f"{d}{s}").exists() for s in (".ckpt", ".wzorzec"))


@pytest.mark.parametrize("etykieta", SLAYERY_CKPT)
def test_slayer_ckpt_already_converted_is_not_downloaded_again(etykieta):
    """A directory converted from this row's checkpoint (sha256 in config.json) is reused; one converted from another
    checkpoint is converted again."""
    ckpt, sha, _, _ = ckpt_wiersza(next(m for m in modele_skryptu() if m[0] == etykieta))
    for sha_katalogu, ponownie in ((sha, False), ("f" * 64, True)):
        ws = tempfile.mkdtemp()
        atrapa_srodowiska(ws, dostep=True)
        d = Path(ws) / "modele" / etykieta
        d.mkdir(parents=True)
        (d / "model.safetensors").write_bytes(b"x")
        (d / "config.json").write_text(json.dumps({"zrodlo_ckpt": f"/w/{ckpt}", "ckpt_sha256": sha_katalogu}, indent=1))
        env = {**os.environ, "WS": ws, "K": str(KORZEN), "ZADANIA_ID": "T02", "ZOSTAW_WAGI": "1"}
        wynik = subprocess.run(["bash", "-c", f"source {SKRYPT} _funkcje; licz_kolejke - {etykieta}"],
                               capture_output=True, text=True, env=env)
        assert wynik.returncode == 0, wynik.stderr
        assert ("juz skonwertowane" in wynik.stdout) != ponownie
        wywolania = (Path(ws) / "wywolania.log").read_text()
        assert ("hf_hub_download" in wywolania and "konwertuj.py" in wywolania) == ponownie
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
