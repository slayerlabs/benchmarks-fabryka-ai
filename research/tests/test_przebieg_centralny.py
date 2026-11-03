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
POMINIETE = {"speakleash/Bielik-1.5B-v3"}  # gated repo, left out of v1


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
    tekst = (KORZEN / "METODOLOGIA.md").read_text(encoding="utf-8")
    return re.search(r"`(SlayerLab/Slayer1B-1\.06)` @ `([0-9a-f]{40})`", tekst).groups()


def klucze_zadan():
    drzewo = ast.parse((KORZEN / "common" / "zadania.py").read_text(encoding="utf-8"))
    for w in drzewo.body:
        if isinstance(w, ast.Assign) and any(getattr(t, "id", None) == "ZADANIA" for t in w.targets):
            return [k.value for k in w.value.keys]
    raise AssertionError("ZADANIA not found in common/zadania.py")


def test_reference_models_match_methodology_without_bielik():
    tabela = tabela_metodologii()
    assert len(tabela) == 5 and POMINIETE <= set(tabela)
    odniesienia = {repo: rev for _, repo, rev, _, _ in modele_skryptu() if not repo.startswith("SlayerLab/")}
    assert odniesienia == {r: v for r, v in tabela.items() if r not in POMINIETE}


def test_slayer_revision_matches_methodology():
    slayery = [(repo, rev, loader) for _, repo, rev, loader, _ in modele_skryptu() if repo.startswith("SlayerLab/")]
    assert slayery == [(*slayer_metodologii(), "slayer")]


def test_labels_unique_and_fields_valid():
    modele = modele_skryptu()
    assert len({m[0] for m in modele}) == len(modele)
    assert all(m[3] in ("slayer", "hf", "hf-trust") and m[4] in ("lock", "new") for m in modele)


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
        assert "--probka pelna" in l and f"{KORZEN}/common/ewaluuj.py" in l
    lfm3 = [l for l in linie if "LiquidAI/LFM3" in l]
    assert lfm3 and all("--trust_remote_code" in l for l in lfm3)
    wikitext_hf = [l for l in linie if "--zadania T03 " in l and "SlayerLab/" not in l]
    assert wikitext_hf and all("--max_length 4096" in l for l in wikitext_hf)
    assert not [l for l in linie if "--max_length" in l and "--zadania T03 " not in l]
    slayer = [l for l in linie if "SlayerLab/" in l]
    assert slayer and all("--model slayer" in l and f"--model_path {ws}/modele/" in l for l in slayer)
    assert all("--device cuda" in l for l in linie)


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
