"""Wariant BOS z PROTOKOL.md: niezmieniony common/ewaluuj.py, jeden wiodacy BOS w kazdym zadaniu loglik HFLM.

Uzycie (reszta argumentow to dokladnie argumenty ewaluuj.py):
  BOS_LOG=/sciezka/bos.jsonl python bos_start.py /sciezka/do/common/ewaluuj.py --model hf ...

Podmieniane jest tylko TemplateLM._encode_pair widziane przez HFLM. tok_encode zostaje, wiec liczniki tokenow
ewaluuj.py dzialaja jak w przebiegu. Plik startowy lezy poza common/, zeby sha256 runnera sie nie zmienilo.

Dziennik BOS_LOG, po jednej linii JSON:
  {"t":"z","n":N,"w":W,"d":D}  zadanie: N wiodacych BOS w ctx+cont, W wiodacych BOS w wejsciu modelu, D dlugosc
  {"t":"m","n":N}              wywolanie modelu: N wiodacych BOS w tensorze (batch 1)
Zadanie z N != 1 albo W != 1 przerywa liczenie wyjatkiem: BladBos.
"""
import os
import runpy
import sys


class BladBos(RuntimeError):
    pass


def wiodace(ids, bos):
    n = 0
    for x in ids:
        if int(x) != bos:
            break
        n += 1
    return n


def sprawdz_zadanie(ctx, cont, bos, max_length):
    """(n, w, d) zadania; BladBos, gdy brak BOS albo jest ich wiecej niz jeden, takze po przycieciu z lewej."""
    ids = list(ctx) + list(cont)
    n = wiodace(ids, bos)
    wejscie = ids[-(max_length + 1):][:-1]
    w = wiodace(wejscie, bos)
    if n != 1 or w != 1:
        raise BladBos(f"wiodace BOS: {n} w zadaniu, {w} w wejsciu modelu, dlugosc {len(ids)}")
    return n, w, len(ids)


def _bos_id(lm):
    bos = lm.tokenizer.bos_token_id
    if bos is None:
        raise BladBos("tokenizer bez bos_token_id")
    return bos


def zastosuj(klasa, dziennik=None):
    """Podmienia kodowanie pary, kontrole zadan i wywolan modelu w klasie `klasa`."""
    oryg_para = klasa._encode_pair
    oryg_tokeny = klasa._loglikelihood_tokens
    oryg_model = getattr(klasa, "_model_call", None)

    def pisz(linia):
        if dziennik is not None:
            dziennik.write(linia + "\n")

    def para_z_bos(self, context, continuation):
        ctx, cont = oryg_para(self, context, continuation)
        bos = _bos_id(self)
        if list(ctx[:1]) != [bos]:
            ctx = [bos] + list(ctx)
        return ctx, cont

    def tokeny(self, requests, *a, **k):
        bos = _bos_id(self)
        for r in requests:
            n, w, d = sprawdz_zadanie(r[1], r[2], bos, self.max_length)
            pisz(f'{{"t":"z","n":{n},"w":{w},"d":{d}}}')
        return oryg_tokeny(self, requests, *a, **k)

    klasa._encode_pair = para_z_bos
    klasa._loglikelihood_tokens = tokeny

    if oryg_model is not None:
        def model(self, inps, *a, **k):
            bos = _bos_id(self)
            for wiersz in inps.tolist():
                n = wiodace(wiersz, bos)
                if n != 1:
                    raise BladBos(f"{n} wiodacych BOS w tensorze modelu")
                pisz(f'{{"t":"m","n":{n}}}')
            return oryg_model(self, inps, *a, **k)
        klasa._model_call = model


def main():
    runner = sys.argv[1]
    from lm_eval.models.huggingface import HFLM
    sciezka = os.environ["BOS_LOG"]
    os.makedirs(os.path.dirname(sciezka), exist_ok=True)
    dziennik = open(sciezka, "w", buffering=1)
    zastosuj(HFLM, dziennik)
    sys.argv = [runner] + sys.argv[2:]
    runpy.run_path(runner, run_name="__main__")


if __name__ == "__main__":
    main()
