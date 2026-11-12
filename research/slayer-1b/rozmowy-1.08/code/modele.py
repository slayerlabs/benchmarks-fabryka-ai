"""Wspólny interfejs trzech modeli bazowych: kodowanie, forward z KV cache (batch B tych samych promptów), logprob ciągu.

Slayer: forward z research/common/slayer_model.py (ten sam, którym liczono EVALUATION.json 1.08; zgodność z referencją
opisana w docstringu tamtego pliku), start id 0, add_special_tokens=False. Bielik i LFM: transformers, BOS dodaje
tokenizer (add_special_tokens=True), fp32. Wagi leżą POZA repo: katalog z env ROZMOWY_MODELE albo domyślna ścieżka
pilota; sha256 wag zapisuje generuj.py w nagłówku każdego pliku wyników.
"""
import os
import sys
from pathlib import Path

import torch

KOD = Path(__file__).resolve().parent
RESEARCH = KOD.parents[2]
sys.path.insert(0, str(RESEARCH / "common"))

MODELE = Path(os.environ.get(
    "ROZMOWY_MODELE",
    "/private/tmp/claude-501/-Users-lolita-Documents-GitHub-labaj-agency/39c771be-97d1-49d4-b962-12af3cec9b39/"
    "scratchpad/slayer-rozmowa/modele"))

# klucz -> (katalog, nazwa HF, rewizja HF)
REJESTR = {
    "slayer": ("slayer-1.08", "SlayerLab/Slayer1B-1.08", "ea0945b1"),
    "bielik": ("bielik-1.5b-v3", "speakleash/Bielik-1.5B-v3", "4b250496"),
    "lfm": ("lfm2.5-1.2b-base", "LiquidAI/LFM2.5-1.2B-Base", "7453bca9"),
}
# Tokeny końca dokumentu: suma eos z tokenizer_config, generation_config i tokenu końca tekstu modelu bazowego.
EOS = {"slayer": {0}, "bielik": {2, 4}, "lfm": {2, 7}}


def urzadzenie():
    return "mps" if torch.backends.mps.is_available() else "cpu"


class SlayerLM:
    klucz = "slayer"

    def __init__(self, katalog, device=None):
        import slayer_model
        self.device = device or urzadzenie()
        self.m = slayer_model.Slayer(katalog, device=self.device, dtype=torch.float32)
        self.eos = EOS["slayer"]
        self.limit = self.m.blok

    def encode(self, tekst):
        return [self.m.bos] + self.m.encode(tekst)

    def encode_bez_bos(self, tekst):
        return self.m.encode(tekst)

    def decode(self, ids):
        return self.m.tok.decode(ids, skip_special_tokens=False)

    def start(self, ids, B=1):
        self.cache = []
        x = torch.tensor([ids] * B, device=self.device)
        return self.m.krok(x, self.cache).float().cpu()

    def krok(self, toks):
        x = torch.tensor([[t] for t in toks], device=self.device)
        return self.m.krok(x, self.cache).float().cpu()

    def logity_pelne(self, ids):
        """ids: lista int -> logity [T, V] float32 na CPU (jeden forward bez cache)."""
        return self.m.logits(torch.tensor([ids], device=self.device))[0].float().cpu()


class HfLM:
    def __init__(self, klucz, katalog, device=None):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.klucz = klucz
        self.device = device or urzadzenie()
        self.tok = AutoTokenizer.from_pretrained(str(katalog))
        self.m = AutoModelForCausalLM.from_pretrained(str(katalog), dtype=torch.float32).to(self.device).eval()
        self.eos = EOS[klucz]
        self.limit = 4096

    def encode(self, tekst):
        return self.tok(tekst, add_special_tokens=True)["input_ids"]

    def encode_bez_bos(self, tekst):
        return self.tok(tekst, add_special_tokens=False)["input_ids"]

    def decode(self, ids):
        return self.tok.decode(ids, skip_special_tokens=False)

    @torch.no_grad()
    def start(self, ids, B=1):
        out = self.m(input_ids=torch.tensor([ids] * B, device=self.device), use_cache=True)
        self.pkv = out.past_key_values
        return out.logits[:, -1].float().cpu()

    @torch.no_grad()
    def krok(self, toks):
        x = torch.tensor([[t] for t in toks], device=self.device)
        out = self.m(input_ids=x, past_key_values=self.pkv, use_cache=True)
        self.pkv = out.past_key_values
        return out.logits[:, -1].float().cpu()

    @torch.no_grad()
    def logity_pelne(self, ids):
        return self.m(input_ids=torch.tensor([ids], device=self.device)).logits[0].float().cpu()


def wczytaj(klucz):
    katalog = MODELE / REJESTR[klucz][0]
    if klucz == "slayer":
        return SlayerLM(katalog)
    return HfLM(klucz, katalog)


def czesc_ciagu(model, kontekst, ciag):
    """Podział jak lm-eval `_encode_pair`: całość kodowana razem, kontekst osobno, ciąg = reszta tokenów.

    Zwraca (ids_calosci, liczba_tokenow_kontekstu, czy_granica_zgodna). Granica niezgodna = tokenizer skleił znak
    kontekstu z początkiem ciągu (wtedy ciąg w tokenach różni się od napisu `ciag`; flaga trafia do wyników).
    """
    n_spacji = len(kontekst) - len(kontekst.rstrip(" "))
    if n_spacji:
        ciag = kontekst[-n_spacji:] + ciag
        kontekst = kontekst[:-n_spacji]
    calosc = model.encode(kontekst + ciag)
    ctx = model.encode(kontekst)
    zgodna = calosc[:len(ctx)] == ctx
    return calosc, len(ctx), zgodna


def logprob_ciagu(model, kontekst, ciag):
    """Suma log p (naturalny log) tokenów ciągu po kontekście, liczba tokenów ciągu, flaga granicy."""
    ids, n_ctx, zgodna = czesc_ciagu(model, kontekst, ciag)
    if len(ids) > model.limit:  # obcięcie z lewej jak w EVALUATION.json; w tym zestawie nie występuje (prompty < 2k tok.)
        k = len(ids) - model.limit
        ids, n_ctx = ids[k:], max(1, n_ctx - k)
    logity = model.logity_pelne(ids)
    lp = torch.log_softmax(logity.double(), -1)
    cel = torch.tensor(ids[n_ctx:])
    wart = lp[n_ctx - 1:len(ids) - 1].gather(1, cel[:, None])[:, 0]
    return float(wart.sum()), len(ids) - n_ctx, zgodna


def p_nastepnego(model, tekst, zbior_ids):
    """p (suma) i ranga najlepszego z `zbior_ids` jako następnego tokenu po `tekst`."""
    ids = model.encode(tekst)
    p = torch.softmax(model.logity_pelne(ids)[-1].double(), -1)
    idx = torch.tensor(sorted(zbior_ids))
    naj = float(p[idx].max())
    return float(p[idx].sum()), int((p > naj).sum()) + 1
