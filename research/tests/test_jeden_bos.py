"""METODOLOGIA, „Wejście”: każde żądanie modelu HF ma dokładnie jeden wiodący BOS (common/jeden_bos.py), bez sieci.

Atrapy tokenizera: z BOS, który tokenizer dokleja sam (Bielik-1.5B-v3, EuroLLM, LFM2.5), z BOS, którego nie dokleja
(Pythia, Bielik-11B-v3.1, LFM3), i bez `bos_token` (Qwen3.5). Żądania idą przez kod HFLM zainstalowanej wersji
lm-eval (pusty kontekst, para loglik, prompt generacji, okna perpleksji). Run: python -m pytest tests/test_jeden_bos.py
"""
import argparse
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN / "common"))

import transformers  # noqa: E402
from tokenizers import Regex, Tokenizer  # noqa: E402
from tokenizers.models import WordLevel  # noqa: E402
from tokenizers.pre_tokenizers import Split  # noqa: E402
from tokenizers.processors import TemplateProcessing  # noqa: E402

import ewaluuj as E  # noqa: E402
import jeden_bos as J  # noqa: E402

ZNAKI = "Question: 2+=\nAnswer4abcdxyz"
SPECJALNE = ["<|endoftext|>", "<s>", "</s>", "<pad>"]


def tokenizer(bos, dokleja):
    """bos: "<s>" (osobny token), "<|endoftext|>" (BOS = EOS, jak Pythia) albo None (jak Qwen3.5)."""
    vocab = {t: i for i, t in enumerate(SPECJALNE)}
    for z in sorted(set(ZNAKI)):
        vocab[z] = len(vocab)
    tok = Tokenizer(WordLevel(vocab, unk_token="<pad>"))
    tok.pre_tokenizer = Split(Regex("."), behavior="isolated")
    if dokleja:
        tok.post_processor = TemplateProcessing(single=f"{bos} $A", pair=f"{bos} $A $B", special_tokens=[(bos, vocab[bos])])
    eos = "<|endoftext|>" if bos == "<|endoftext|>" else "</s>"
    return transformers.PreTrainedTokenizerFast(tokenizer_object=tok, bos_token=bos, eos_token=eos, pad_token="<pad>")


ATRAPY = {
    "bos-dokleja": ("<s>", True),
    "bos-nie-dokleja": ("<s>", False),
    "bos-rowny-eos": ("<|endoftext|>", False),
    "bez-bos": (None, False),
}


def model(klasa, tok):
    """HFLM bez wag: tylko pola, których używa kodowanie żądań; __init__ HFLM ustawia też `add_bos_token`."""
    lm = object.__new__(klasa)
    lm.tokenizer = tok
    lm.custom_prefix_token_id = None
    lm.backend = "causal"
    lm.AUTO_MODEL_CLASS = transformers.AutoModelForCausalLM
    lm.add_bos_token = False
    lm.enable_thinking = False  # lm-eval 0.4.13: HFLM.loglikelihood
    return lm


def zadania(lm, pary):
    """Żądania loglik po kodowaniu lm-eval (TemplateLM.loglikelihood), bez forwardu modelu."""
    zlapane = []

    def bez_modelu(reqs, **_):
        zlapane.extend(reqs)
        return [(0.0, True)] * len(reqs)
    lm._loglikelihood_tokens = bez_modelu
    lm.loglikelihood([SimpleNamespace(args=p) for p in pary], disable_tqdm=True)
    return [(kont, cd) for _, kont, cd in zlapane]


def oczekiwane(tok):
    return 0 if tok.bos_token_id is None else 1


@pytest.mark.parametrize("nazwa", sorted(ATRAPY))
def test_para_loglik_ma_jeden_wiodacy_bos_i_te_same_tokeny_odpowiedzi(nazwa):
    tok = tokenizer(*ATRAPY[nazwa])
    lm = model(J.HFLMJedenBOS, tok)
    [(kont, cd)] = zadania(lm, [("Question: 2+2=\nAnswer:", " 4")])
    assert J.wiodace(kont, tok.bos_token_id) == oczekiwane(tok)
    bez_bos = kont[oczekiwane(tok):]
    assert bez_bos + cd == tok.encode("Question: 2+2=\nAnswer: 4", add_special_tokens=False)


@pytest.mark.parametrize("nazwa", sorted(ATRAPY))
def test_pusty_kontekst_i_okna_perpleksji_maja_jeden_prefiks(nazwa):
    """Pusty kontekst (BLiMP) i okna perpleksji (WikiText) stoją za `prefix_token_id`: tokenizer nie może dołożyć
    drugiego BOS, także gdy HFLM.__init__ ustawi `add_bos_token=True` (wymuszenie dla Gemmy)."""
    tok = tokenizer(*ATRAPY[nazwa])
    lm = model(J.HFLMJedenBOS, tok)
    lm.add_bos_token = True
    [(kont, cd)] = zadania(lm, [("", "abc")])
    assert kont == [lm.prefix_token_id] and cd == tok.encode("abc", add_special_tokens=False)
    assert lm.tok_encode("abc") == tok.encode("abc", add_special_tokens=False)


@pytest.mark.parametrize("nazwa", sorted(ATRAPY))
def test_prompt_generacji_ma_jeden_bos_przed_tokenami_i_miesci_sie_w_limicie(nazwa):
    tok = tokenizer(*ATRAPY[nazwa])
    lm = model(J.HFLMJedenBOS, tok)
    ids, maska = lm.tok_batch_encode(["ab", "abcd"])
    for wiersz, m in zip(ids.tolist(), maska.tolist()):
        widziane = [t for t, k in zip(wiersz, m) if k]
        assert J.wiodace(widziane, tok.bos_token_id) == oczekiwane(tok), (wiersz, m)
    ids, _ = lm.tok_batch_encode(["abcd"], left_truncate_len=3)
    assert ids.shape[1] == 3
    assert ids[0].tolist()[oczekiwane(tok):] == tok.encode("abcd", add_special_tokens=False)[-(3 - oczekiwane(tok)):]


@pytest.mark.parametrize("nazwa", sorted(n for n in ATRAPY if ATRAPY[n][0]))
def test_tekst_zaczynajacy_sie_od_bos_nie_dostaje_drugiego(nazwa):
    tok = tokenizer(*ATRAPY[nazwa])
    lm = model(J.HFLMJedenBOS, tok)
    [(kont, _)] = zadania(lm, [(f"{tok.bos_token}Question: 2+2=\nAnswer:", " 4")])
    assert J.wiodace(kont, tok.bos_token_id) == 1
    ids, maska = lm.tok_batch_encode([f"{tok.bos_token}ab"])
    assert J.wiodace(ids[0].tolist(), tok.bos_token_id) == 1


@pytest.mark.parametrize("nazwa", sorted(ATRAPY))
def test_zbadaj_bos_zapisuje_liczbe_wiodacych_bos(nazwa):
    tok = tokenizer(*ATRAPY[nazwa])
    pole = J.zbadaj_bos(model(J.HFLMJedenBOS, tok))
    n = oczekiwane(tok)
    assert pole["wiodace_bos"] == {"loglik": n, "generacja": n, "pusty_kontekst": n}
    assert pole["bos_token_id"] == tok.bos_token_id


def test_main_zapisuje_pole_bos_w_wyniku_rozszerzonym(monkeypatch, tmp_path):
    """ewaluuj.py buduje model HF klasą HFLMJedenBOS i zapisuje pole `bos` w results_rozszerzone.json."""
    zbudowane, klasa = [], J.HFLMJedenBOS

    def atrapa(**kw):
        zbudowane.append(kw)
        return model(klasa, tokenizer("<s>", False))
    monkeypatch.setattr(J, "HFLMJedenBOS", atrapa)

    def bez_zadania(*_a, **_k):
        raise RuntimeError("bez zadania w teście")
    monkeypatch.setattr(E, "ocen_zadanie", bez_zadania)
    monkeypatch.setattr(E, "sha_wag", lambda *_: "0" * 64)
    monkeypatch.setattr(sys, "argv", ["ewaluuj.py", "--repo", "atrapa/model", "--revision", "abc", "--zadania", "T02",
                                      "--wyjscie", str(tmp_path)])
    with pytest.raises(SystemExit) as wyjscie:
        E.main()
    assert wyjscie.value.code == 3
    assert zbudowane and zbudowane[0]["pretrained"] == "atrapa/model"
    roz = json.loads((tmp_path / "results_rozszerzone.json").read_text())
    assert roz["bos"]["wiodace_bos"] == {"loglik": 1, "generacja": 1, "pusty_kontekst": 1}


def test_regula_raportu_rozpoznaje_wyniki_z_jednym_bos():
    sys.path.insert(0, str(KORZEN / "tools" / "ewaluacja"))
    import raport as R
    pole = J.zbadaj_bos(model(J.HFLMJedenBOS, tokenizer("<s>", False)))
    qwen = J.zbadaj_bos(model(J.HFLMJedenBOS, tokenizer(None, False)))
    assert R.bos_zgodny(pole) and R.bos_zgodny(qwen)
    assert not R.bos_zgodny(None)
    assert not R.bos_zgodny({**pole, "wiodace_bos": {**pole["wiodace_bos"], "loglik": 0}})
    wyniki = [{"benchmark": "arc-challenge", "bos": pole}, {"benchmark": "piqa", "bos": qwen},
              {"benchmark": "ewok", "bos": None}]
    assert R.bos_jednakowy(wyniki)
    assert not R.bos_jednakowy(wyniki + [{"benchmark": "piqa", "bos": None}])


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
