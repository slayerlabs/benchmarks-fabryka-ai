"""Ocena automatyczna odpowiedzi (metryki a, c, d z PROTOKOL.md). Czyste funkcje + uruchamianie testów kodu.

Wejście każdej oceny to odpowiedź JUŻ UCIĘTA na napisie stopu (szablony.utnij).
"""
import math
import os
import re
import subprocess
import sys
import tempfile
import unicodedata

_INTERP = re.compile(r"[^\w\s]", re.UNICODE)
_LICZBA = re.compile(r"(?<![\w.,])-?\d{1,3}(?:[   ]\d{3})+(?:[.,]\d+)?(?![\d])|(?<![\w])-?\d+(?:[.,]\d+)?")


def normalizuj(t):
    t = unicodedata.normalize("NFC", t).lower()
    t = t.replace("’", "'").replace("'", " ")
    t = _INTERP.sub(" ", t)
    return " ".join(t.split())


def pierwsza_linia(t):
    for linia in t.split("\n"):
        if linia.strip():
            return linia.strip()
    return ""


def zawiera(tekst_n, fraza):
    f = normalizuj(fraza)
    return bool(f) and f" {f} " in f" {tekst_n} "


def ocen_krotka(odp, akceptowane, zakazane):
    linia = normalizuj(pierwsza_linia(odp))
    if any(zawiera(linia, z) for z in zakazane):
        return 0
    return int(any(zawiera(linia, a) for a in akceptowane))


def ocen_zdanie(odp, akceptowane):
    linia = normalizuj(pierwsza_linia(odp))
    return int(any(linia == normalizuj(a) for a in akceptowane))


def _na_float(s):
    s = s.replace(" ", "").replace(" ", "").replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def wyciagnij_liczbe(odp):
    """Pierwsza liczba po OSTATNIM „Wynik:”, a bez tego znacznika ostatnia liczba odpowiedzi; None, gdy brak."""
    i = odp.rfind("Wynik:")
    if i >= 0:
        m = _LICZBA.search(odp[i + len("Wynik:"):])
        return _na_float(m.group()) if m else None
    wszystkie = _LICZBA.findall(odp)
    return _na_float(wszystkie[-1]) if wszystkie else None


def ocen_liczba(odp, cel, tol=0.005):
    x = wyciagnij_liczbe(odp)
    return int(x is not None and abs(x - float(cel)) <= tol)


def wyciagnij_kod(odp):
    """Treść pierwszego bloku ```python (do zamykającego ``` albo do końca); bez bloku cała odpowiedź."""
    i = odp.find("```python")
    if i >= 0:
        reszta = odp[i + len("```python"):]
        j = reszta.find("```")
        return (reszta if j < 0 else reszta[:j]).strip("\n")
    i = odp.find("```")
    if i >= 0:
        reszta = odp[i + 3:]
        j = reszta.find("```")
        return (reszta if j < 0 else reszta[:j]).strip("\n")
    return odp.strip("\n")


PROFIL_SANDBOX = "(version 1)(allow default)(deny network*)"


def uruchom_testy(kod, testy, limit_s=10, python=sys.executable):
    """1, gdy kod + testy kończą się kodem 0 w osobnym podprocesie (bez sieci: sandbox-exec, pusty katalog, -I)."""
    with tempfile.TemporaryDirectory() as d:
        plik = os.path.join(d, "kandydat.py")
        with open(plik, "w", encoding="utf-8") as f:
            f.write(kod + "\n\n" + testy + "\n")
        cmd = [python, "-I", plik]
        if os.path.exists("/usr/bin/sandbox-exec"):
            cmd = ["/usr/bin/sandbox-exec", "-p", PROFIL_SANDBOX] + cmd
        env = {"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": "0"}
        try:
            r = subprocess.run(cmd, cwd=d, env=env, capture_output=True, timeout=limit_s, stdin=subprocess.DEVNULL)
            return int(r.returncode == 0), r.stderr.decode("utf-8", "replace")[-300:]
        except subprocess.TimeoutExpired:
            return 0, "timeout"


def ocen_kod(odp, testy, **kw):
    return uruchom_testy(wyciagnij_kod(odp), testy, **kw)


def slowa(t):
    return re.findall(r"\w+", t.lower())


def powtorzone_3gramy(t):
    """Udział 3-gramów słów, które już wystąpiły wcześniej w tej samej odpowiedzi; None przy < 3 słowach."""
    s = slowa(t)
    g = [tuple(s[i:i + 3]) for i in range(len(s) - 2)]
    if not g:
        return None
    widziane, pow_ = set(), 0
    for x in g:
        pow_ += x in widziane
        widziane.add(x)
    return pow_ / len(g)


def distinct_n(t, n=2):
    s = slowa(t)
    g = [tuple(s[i:i + n]) for i in range(len(s) - n + 1)]
    return len(set(g)) / len(g) if g else None


ZNACZNIKI_PRZECIEKU = ("<think>", "</think>", "<|im_start|>", "<|im_end|>")
ZNACZNIKI_GSM8K = (re.compile(r"<<[^<>]*=[^<>]*>>"), re.compile(r"^####\s*-?\d", re.M))


def przeciek_rozumowania(t):
    return int(any(z in t for z in ZNACZNIKI_PRZECIEKU))


def format_gsm8k(t):
    return int(any(r.search(t) for r in ZNACZNIKI_GSM8K))


def bpb(suma_logprob_nat, n_bajtow):
    return -suma_logprob_nat / (math.log(2) * n_bajtow)
