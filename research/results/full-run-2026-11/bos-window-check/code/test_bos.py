"""Test mechanizmu BOS na atrapie, bez sieci i wag. Uruchomienie: python -m pytest test_bos.py -q

Atrapy maja bos != eot, zeby zapalic mutacje biorace BOS z eot albo wpisujace go na sztywno.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

sys.path.insert(0, str(Path(__file__).parent))

import bos_start as B  # noqa: E402
from lm_eval.api.model import CacheHook, TemplateLM  # noqa: E402
from lm_eval.models.huggingface import HFLM  # noqa: E402

BOS = 7
EOT = 3
V = 300


class Atrapa(TemplateLM):
    """Tokenizer: kazdy znak to token ord(c) (zawsze > BOS); opcjonalnie sam dokleja BOS."""

    def __init__(self, tokenizer_dokleja=False):
        super().__init__()
        self.tokenizer = SimpleNamespace(bos_token_id=BOS)
        self.dokleja = tokenizer_dokleja
        self.max_length = 50
        self.zadania = []

    @property
    def eot_token_id(self):
        return EOT

    @property
    def prefix_token_id(self):
        return BOS

    def tok_encode(self, s, **k):
        return ([BOS] if self.dokleja else []) + [ord(c) for c in s]

    def _loglikelihood_tokens(self, requests, **k):
        self.zadania.extend(requests)
        return [(0.0, True) for _ in requests]

    def _model_call(self, inps, **k):
        return "wynik-modelu"

    def loglikelihood_rolling(self, requests, **k):
        return []

    def generate_until(self, requests, **k):
        return []


def nowa_klasa():
    return type("AtrapaBos", (Atrapa,), {})


def test_bos_z_tokenizera_nie_stala_ani_eot():
    k = nowa_klasa()
    B.zastosuj(k)
    ctx, _ = k()._encode_pair("ab", "c")
    assert ctx[0] == BOS and BOS not in (0, EOT)


def test_jeden_bos_i_kontynuacja_bez_zmian():
    czysta = Atrapa()
    oczekiwana_cont = czysta._encode_pair("ab ", "cd")[1]
    k = nowa_klasa()
    B.zastosuj(k)
    ctx, cont = k()._encode_pair("ab ", "cd")
    assert ctx == [BOS, ord("a"), ord("b")]
    assert cont == oczekiwana_cont == [ord(" "), ord("c"), ord("d")]


def test_tokenizer_z_bos_nie_daje_podwojnego():
    k = nowa_klasa()
    B.zastosuj(k)
    ctx, _ = k(tokenizer_dokleja=True)._encode_pair("ab", "c")
    assert ctx[:2] == [BOS, ord("a")]


def test_pusty_kontekst_ma_jeden_bos():
    k = nowa_klasa()
    B.zastosuj(k)
    lm = k()
    lm.loglikelihood([SimpleNamespace(args=("", "xy"))], disable_tqdm=True)
    assert lm.zadania[0][1] == [BOS]
    assert B.wiodace(lm.zadania[0][1] + lm.zadania[0][2], BOS) == 1


@pytest.mark.parametrize("ctx", [[50, 60], [BOS, BOS, 50]], ids=["brak", "podwojny"])
def test_kontrola_zapala_sie_na_zlym_bos(ctx):
    with pytest.raises(B.BladBos):
        B.sprawdz_zadanie(ctx, [70], BOS, 50)


def test_kontrola_zapala_sie_przy_uruchomieniu_bez_kodowania():
    k = nowa_klasa()
    oryg = k._encode_pair
    B.zastosuj(k)
    k._encode_pair = oryg
    lm = k()
    with pytest.raises(B.BladBos):
        lm.loglikelihood([SimpleNamespace(args=("ab", "c"))], disable_tqdm=True)


def test_kontrola_zapala_sie_po_ucieciu_bos_z_lewej():
    with pytest.raises(B.BladBos):
        B.sprawdz_zadanie([BOS] + list(range(10, 90)), [99], BOS, 50)


def test_poprawne_zadanie_przechodzi():
    assert B.sprawdz_zadanie([BOS, 50, 60], [70], BOS, 50) == (1, 1, 4)


@pytest.mark.parametrize("wiersz", [[50, 60], [BOS, BOS, 50]], ids=["brak", "podwojny"])
def test_kontrola_tensora_zapala_sie(wiersz):
    k = nowa_klasa()
    B.zastosuj(k)
    with pytest.raises(B.BladBos):
        k()._model_call(torch.tensor([wiersz]))


def test_kontrola_tensora_przepuszcza_jeden_bos_i_wola_model():
    k = nowa_klasa()
    B.zastosuj(k)
    assert k()._model_call(torch.tensor([[BOS, 50, 60]])) == "wynik-modelu"


def test_dziennik_zapisuje_zadania_i_wywolania(tmp_path):
    p = tmp_path / "bos.jsonl"
    k = nowa_klasa()
    with open(p, "w", buffering=1) as f:
        B.zastosuj(k, f)
        lm = k()
        lm.loglikelihood([SimpleNamespace(args=("ab", "c"))], disable_tqdm=True)
        lm._model_call(torch.tensor([[BOS, 50]]))
    assert p.read_text().splitlines() == ['{"t":"z","n":1,"w":1,"d":4}', '{"t":"m","n":1}']


class ProbnyHFLM(HFLM):
    """Prawdziwe HFLM._loglikelihood_tokens na deterministycznych logitach: logit zalezy od tokenu i pozycji wejscia."""

    AUTO_MODEL_CLASS = None

    def __init__(self, batch):
        self.tokenizer_ = SimpleNamespace(bos_token_id=BOS, eos_token_id=EOT, pad_token_id=0)
        self.batch = batch
        self.backend = "causal"
        self.logits_cache = False
        self.softmax_dtype = None
        self.cache_hook = CacheHook(None)

    tokenizer = property(lambda self: self.tokenizer_)
    batch_size = property(lambda self: self.batch)
    device = property(lambda self: torch.device("cpu"))
    rank = property(lambda self: 0)
    world_size = property(lambda self: 1)
    max_length = property(lambda self: 500)
    eot_token_id = property(lambda self: EOT)
    prefix_token_id = property(lambda self: BOS)

    def tok_encode(self, s, left_truncate_len=None, add_special_tokens=None):
        return [ord(c) for c in s]

    def _model_call(self, inps, attn_mask=None, labels=None):
        n, dl = inps.shape
        cel = (inps + 1 + torch.arange(dl).expand(n, dl)) % V
        v = torch.arange(V).float().expand(n, dl, V)
        return -0.01 * (v - cel.unsqueeze(-1).float()) ** 2


def oczekiwany_ll(pelne, n_cont):
    """Suma log p tokenow kontynuacji przy logicie z pozycji poprzedzajacej (wzor z ProbnyHFLM, liczony osobno)."""
    suma = 0.0
    for j in range(len(pelne) - n_cont, len(pelne)):
        v = torch.arange(V).float()
        cel = (pelne[j - 1] + 1 + (j - 1)) % V
        suma += torch.log_softmax(-0.01 * (v - cel) ** 2, dim=-1)[pelne[j]].item()
    return suma


PARY = [("ab", "c"), ("abcd", "ef"), ("x", "yz"), ("hello there", " world"), ("q", "r")]


def policz(klasa, batch):
    lm = klasa(batch)
    return lm, [r[0] for r in lm.loglikelihood([SimpleNamespace(args=p) for p in PARY], disable_tqdm=True)]


def klasa_bos():
    k = type("ProbnyBos", (ProbnyHFLM,), {})
    B.zastosuj(k)
    return k


def test_wybor_pozycji_z_bos_na_deterministycznych_logitach():
    _, wyn = policz(klasa_bos(), 1)
    for (c, k), ll in zip(PARY, wyn):
        pelne = [BOS] + [ord(x) for x in c + k]
        assert ll == pytest.approx(oczekiwany_ll(pelne, len(k)), abs=1e-5)


def test_bos_przesuwa_pozycje_wzgledem_wariantu_bez_bos():
    _, z = policz(klasa_bos(), 1)
    _, bez = policz(ProbnyHFLM, 1)
    for (c, k), a, b in zip(PARY, z, bez):
        assert b == pytest.approx(oczekiwany_ll([ord(x) for x in c + k], len(k)), abs=1e-5)
        assert a != pytest.approx(b, abs=1e-3)


@pytest.mark.parametrize("n", [2, 5])
def test_batch_1_rowny_batch_n(n):
    _, a = policz(klasa_bos(), 1)
    _, b = policz(klasa_bos(), n)
    assert a == pytest.approx(b, abs=1e-5)
