"""tools/wykres_przebiegu.py takes the Slayer label from MODELE in tools/przebieg_centralny.sh, not its own copy."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN / "tools"))
import wykres_przebiegu as Wp  # noqa: E402


def test_slayer_label_is_the_slayer_row_of_modele():
    env = {**os.environ, "WS": tempfile.mkdtemp(), "K": str(KORZEN)}
    lista = subprocess.run(["bash", str(KORZEN / "tools" / "przebieg_centralny.sh"), "lista"], capture_output=True,
                           text=True, check=True, env=env).stdout.splitlines()
    slayery = [l.split("|")[0] for l in lista if l.split("|")[1].startswith("SlayerLab/")]
    assert Wp.M[0][0] == Wp.etykieta_slayera() == slayery[0] and len(slayery) == 1


def test_label_follows_the_script_and_rejects_two_slayers(tmp_path):
    s = tmp_path / "przebieg_centralny.sh"
    wiersz = '  "slayer1b-9.99|SlayerLab/Slayer1B-9.99|{}|slayer|lock"\n'.format("0" * 40)
    inny = '  "qwen|Qwen/Q|{}|hf|new"\n'.format("1" * 40)
    s.write_text("A=1\nMODELE=(\n" + inny + wiersz + ")\nB=2\n")
    assert Wp.etykieta_slayera(s) == "slayer1b-9.99"
    s.write_text("A=1\nMODELE=(\n" + wiersz + wiersz.replace("9.99", "9.98") + ")\n")
    with pytest.raises(ValueError):
        Wp.etykieta_slayera(s)
