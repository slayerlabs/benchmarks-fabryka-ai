"""Szablony promptu few-shot (A główny, B wariant wrażliwości), ciąg wzorca do BPB i reguły stopu. Czyste funkcje.

A: "Polecenie: …\nOdpowiedź:<sep><odpowiedź>" bloki rozdzielone pustą linią; sep = " " dla typów krótkich, "\n" dla
   `kod` i `otwarte`. Stop: "\nPolecenie:".
B: "### Zadanie\n…\n### Rozwiązanie\n<odpowiedź>" bloki rozdzielone pustą linią. Stop: "\n### ".
Kategoria `angielski` ma etykiety angielskie (A: Task/Answer, B: Problem/Solution).
"""

ETYKIETY = {
    "A": {"pl": ("Polecenie:", "Odpowiedź:"), "en": ("Task:", "Answer:")},
    "B": {"pl": ("### Zadanie", "### Rozwiązanie"), "en": ("### Problem", "### Solution")},
}
WIELOLINIOWE = {"kod", "otwarte"}
MAX_TOKENOW = {"krotka": 48, "zdanie": 48, "liczba": 160, "kod": 256, "otwarte": 400}


def jezyk(kat):
    return "en" if kat == "angielski" else "pl"


def separator(szablon, typ):
    if szablon == "B":
        return "\n"
    return "\n" if typ in WIELOLINIOWE else " "


def blok(szablon, kat, typ, polecenie, odpowiedz=None):
    lp, la = ETYKIETY[szablon][jezyk(kat)]
    if szablon == "A":
        glowa = f"{lp} {polecenie}\n{la}"
    else:
        glowa = f"{lp}\n{polecenie}\n{la}"
    if odpowiedz is None:
        return glowa
    return glowa + separator(szablon, typ) + odpowiedz


def prompt(szablon, pozycja, shoty):
    """Kontekst kończący się etykietą odpowiedzi (bez spacji ani nowej linii)."""
    czesci = [blok(szablon, s["kat"], s["typ"], s["polecenie"], s["wzorzec"]) for s in shoty]
    czesci.append(blok(szablon, pozycja["kat"], pozycja["typ"], pozycja["polecenie"]))
    return "\n\n".join(czesci)


def ciag_wzorca(szablon, pozycja):
    """Ciąg, którego log p liczy BPB: separator + wzorzec (tak jak odpowiedź stoi w przykładach)."""
    return separator(szablon, pozycja["typ"]) + pozycja["wzorzec"]


def stopy(szablon, kat):
    lp = ETYKIETY[szablon][jezyk(kat)][0]
    return ["\n" + lp] if szablon == "A" else ["\n### "]


def utnij(tekst, stop_napisy):
    """(tekst do pierwszego napisu stopu, czy_trafiony)."""
    pozycje = [tekst.find(s) for s in stop_napisy if s in tekst]
    if not pozycje:
        return tekst, False
    return tekst[:min(pozycje)], True


def prompt_sondy(pozycja, z_nowa_linia):
    """Sonda EOS (0-shot, bez szablonu few-shot): pytanie i wzorcowa odpowiedź, po których dokument powinien się skończyć."""
    lp, la = ("Question:", "Answer:") if jezyk(pozycja["kat"]) == "en" else ("Pytanie:", "Odpowiedź:")
    t = f"{lp} {pozycja['polecenie']}\n{la} {pozycja['wzorzec']}"
    return t + "\n" if z_nowa_linia else t
