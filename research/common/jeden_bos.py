"""METODOLOGIA, „Wejście”: każde żądanie modelu HF zaczyna się dokładnie jednym tokenem BOS tokenizera modelu.

Sam HFLM tego nie daje. lm-eval 0.4.9.1 (`lock`) koduje tekst bez tokenów specjalnych, więc niepusty kontekst nie ma
BOS. lm-eval 0.4.13 (`new`) bierze domyślne zachowanie tokenizera, więc BOS jest tylko tam, gdzie tokenizer dokleja go
sam. `add_bos_token=True` też tego nie wyrównuje: BOS dokleja wtedy post-procesor tokenizera, czyli nie u każdego
modelu, a w 0.4.9.1 pusty kontekst (BLiMP) i okna perpleksji (WikiText) dostają drugi BOS, bo stoją już za
`prefix_token_id`.

`HFLMJedenBOS` koduje zawsze bez tokenów specjalnych i stawia jeden BOS przed kontekstem par loglik i przed promptem
generacji. Pusty kontekst i okna perpleksji zaczynają się od `prefix_token_id` (BOS, bez BOS: EOS) jak w HFLM.
Tokenizer bez `bos_token` daje żądanie bez BOS. `zbadaj_bos` koduje próbne żądania i zapisuje, ile wiodących BOS
dostały (pole `bos` w results_rozszerzone.json).
"""
from lm_eval.models.huggingface import HFLM

PROBA_KONTEKST, PROBA_KONTYNUACJA = "Question: 2 + 2 =\nAnswer:", " 4"


def wiodace(ids, bos):
    """Ile tokenów `bos` stoi na początku `ids` (0, gdy model nie ma BOS)."""
    if bos is None:
        return 0
    n = 0
    for t in ids:
        if t != bos:
            break
        n += 1
    return n


class HFLMJedenBOS(HFLM):
    """HFLM z jednym wiodącym BOS w każdym żądaniu z niepustym kontekstem."""

    # Tokeny specjalne nigdy nie idą przez tokenizer: przypisanie z HFLM.__init__ (i wymuszenie BOS dla Gemmy w 0.4.9.1)
    # nie zmienia tej wartości, więc tokenizer nie dołoży drugiego BOS.
    @property
    def add_bos_token(self):
        return False

    @add_bos_token.setter
    def add_bos_token(self, _):
        pass

    @property
    def bos_wiodacy(self):
        return getattr(self.tokenizer, "bos_token_id", None)

    def _encode_pair(self, context, continuation):
        context_enc, continuation_enc = super()._encode_pair(context, continuation)
        bos = self.bos_wiodacy
        if bos is not None and context_enc[:1] != [bos]:
            context_enc = [bos] + list(context_enc)
        return context_enc, continuation_enc

    def tok_batch_encode(self, strings, padding_side="left", left_truncate_len=None, truncation=False):
        import torch

        bos = self.bos_wiodacy
        if bos is None:
            return super().tok_batch_encode(strings, padding_side=padding_side, left_truncate_len=left_truncate_len,
                                            truncation=truncation)
        assert padding_side == "left", padding_side
        ids, mask = super().tok_batch_encode(strings, padding_side=padding_side,
                                             left_truncate_len=left_truncate_len - 1 if left_truncate_len else None,
                                             truncation=truncation)
        pierwsze = mask.long().argmax(dim=1)  # pierwsza kolumna bez dopełnienia w każdym wierszu
        if bool((ids.gather(1, pierwsze.view(-1, 1)) == bos).all()):
            return ids, mask
        # Dopełnienie z lewej: kolumna BOS staje przed dopełnieniem, które `generate` pomija przez maskę.
        return (torch.cat([ids.new_full((ids.shape[0], 1), bos), ids], dim=1),
                torch.cat([mask.new_ones((mask.shape[0], 1)), mask], dim=1))


def zbadaj_bos(lm):
    """Pole `bos` wyniku: token BOS modelu i liczba wiodących BOS w próbnej parze loglik, w prompcie generacji
    i w żądaniu z pustym kontekstem, policzone tym samym kodowaniem, którego używa przebieg."""
    tok = lm.tokenizer
    bos = getattr(tok, "bos_token_id", None)
    kontekst, _ = lm._encode_pair(PROBA_KONTEKST, PROBA_KONTYNUACJA)
    generacja, _ = lm.tok_batch_encode([PROBA_KONTEKST])
    kontynuacja_pusty = lm.tok_encode(PROBA_KONTYNUACJA.strip())
    return {"bos_token": getattr(tok, "bos_token", None) if bos is not None else None, "bos_token_id": bos,
            "prefix_token_id": lm.prefix_token_id,
            "wiodace_bos": {"loglik": wiodace(kontekst, bos), "generacja": wiodace(generacja[0].tolist(), bos),
                            "pusty_kontekst": wiodace([lm.prefix_token_id] + list(kontynuacja_pusty), bos)},
            "regula": "jeden BOS" if bos is not None else "tokenizer bez bos_token: żądanie bez BOS"}
