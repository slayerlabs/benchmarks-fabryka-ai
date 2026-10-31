"""Mianownik byte/word perplexity WikiText w hipoteza_formatu.cmd_wikitext: z oryginału doc["page"], jak lm-eval.

Bez modelu i bez sieci: model, zbiór, detokenizer i okna rolling są podstawione. Uruchom: pytest tests/.
"""
import argparse
import importlib
import json
import math
import re
import sys
import types
from pathlib import Path

KAT = Path(__file__).resolve().parent.parent / "common"
STRONA = " = Tytuł = \n Rok 1 @-@ 2 , potem @,@ koniec . \n"
NLL = 1234.5


def _detok(doc):
    s = doc["page"]
    for a, b in ((" @-@ ", "-"), (" @,@ ", ","), (" , ", ", "), (" . ", ". ")):
        s = s.replace(a, b)
    return s


def _modul(monkeypatch):
    if importlib.util.find_spec("torch") is None:
        torch = types.ModuleType("torch")
        torch.no_grad = lambda: (lambda f: f)
        monkeypatch.setitem(sys.modules, "torch", torch)
    utils = types.ModuleType("lm_eval.utils")
    utils.get_rolling_token_windows = lambda token_list, prefix_token, max_seq_len, context_len: [([prefix_token], token_list)]
    utils.make_disjoint_window = lambda o: o
    monkeypatch.setitem(sys.modules, "lm_eval", types.ModuleType("lm_eval"))
    monkeypatch.setitem(sys.modules, "lm_eval.utils", utils)
    zadania = types.ModuleType("zadania")
    zadania._modul_lm_eval = lambda _: types.SimpleNamespace(wikitext_detokenizer=_detok)
    monkeypatch.setitem(sys.modules, "zadania", zadania)
    monkeypatch.syspath_prepend(str(KAT))
    monkeypatch.delitem(sys.modules, "hipoteza_formatu", raising=False)
    H = importlib.import_module("hipoteza_formatu")
    model = types.SimpleNamespace(encode=lambda s: list(s.encode()), prefiks_pusty=[0], max_len=4096)
    monkeypatch.setattr(H, "zbuduj_model", lambda *_: model)
    monkeypatch.setattr(H, "_ds", lambda *_: [{"page": STRONA}])
    monkeypatch.setattr(H, "licz_logliki", lambda m, pary, b: [(-NLL, None)])
    return H


def test_mianownik_wikitext_z_oryginalu_nie_z_detokenizacji(monkeypatch, tmp_path):
    H = _modul(monkeypatch)
    H.cmd_wikitext(argparse.Namespace(model="x", wyjscie=str(tmp_path), device="cpu"))
    w = json.loads((tmp_path / "wikitext.json").read_text())
    bajty, slowa = len(STRONA.encode("utf-8")), len(re.split(r"\s+", STRONA))
    assert len(_detok({"page": STRONA}).encode()) < bajty  # dokument rzeczywiście się skraca
    assert math.isclose(w["byte_perplexity"], math.exp(NLL / bajty))
    assert math.isclose(w["word_perplexity"], math.exp(NLL / slowa))
    assert (w["bajty"], w["slowa"], w["nll_suma"]) == (bajty, slowa, NLL)
