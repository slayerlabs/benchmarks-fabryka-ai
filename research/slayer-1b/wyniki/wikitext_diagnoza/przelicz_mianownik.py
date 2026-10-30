"""Przelicza zapisane wyniki WikiText-2 ze starego mianownika (tekst po detokenizacji) na mianownik lm-eval (oryginał).

Bez modelu: suma NLL się nie zmienia, więc nowe ln(ppl) = stare ln(ppl) × stary mianownik / nowy mianownik,
osobno dla bajtów i słów. Mianowniki z tokenizacja/mianownik.json (62 dokumenty testu, rewizja 64723477).
Plik już przeliczony (pole „metoda”) zostaje bez zmian, więc ponowne uruchomienie niczego nie psuje.

python wyniki/wikitext_diagnoza/przelicz_mianownik.py   (z katalogu głównego repo; potem narzedzia/liczby.py)
"""
import json
import math
from pathlib import Path

KORZEN = Path(__file__).resolve().parents[2]
M = json.loads((Path(__file__).resolve().parent / "tokenizacja/mianownik.json").read_text())
B_STARE, B_NOWE = M["bajty_detok"], M["bajty_oryginal"]
W_STARE, W_NOWE = M["slowa_detok"], M["slowa_oryginal_resplit"]
METODA = "przeliczone z korekty mianownika (bajty i słowa z doc['page'] jak lm-eval, nie z tekstu po detokenizacji)"
SPACE_106 = 1.846283835597753  # results.json Space SlayerLab/Slayer1B-1.06, byte_perplexity


def przelicz(w):
    if "metoda" in w:
        return w
    nll = math.log(w["byte_perplexity"]) * B_STARE
    lw = math.log(w["word_perplexity"]) * W_STARE / W_NOWE
    przed = {k: w[k] for k in ("byte_perplexity", "bits_per_byte", "word_perplexity")}
    return {**w, "byte_perplexity": math.exp(nll / B_NOWE), "bits_per_byte": nll / B_NOWE / math.log(2),
            "word_perplexity": math.exp(lw), "nll_suma": nll, "bajty": B_NOWE, "slowa": W_NOWE,
            "metoda": METODA, "przed_korekta": {**przed, "bajty": B_STARE, "slowa": W_STARE}}


def zapisz(plik, obiekt, wzor):
    tekst = json.dumps(obiekt, indent=1, ensure_ascii=False)
    plik.write_text(tekst + ("\n" if wzor.endswith("\n") else ""))


for m in ("1.06", "A", "B"):
    f = KORZEN / f"wygaszanie/wyniki/{m}/wikitext.json"
    t = f.read_text()
    zapisz(f, przelicz(json.loads(t)), t)

f = KORZEN / "wygaszanie/wyniki/porownanie.json"
t = f.read_text()
por = json.loads(t)
por["wikitext"] = {m: przelicz(w) for m, w in por["wikitext"].items()}
zapisz(f, por, t)

f = KORZEN / "wyniki/raport_formatu.json"
t = f.read_text()
rap = json.loads(t)
wk = {k: v for k, v in rap["slayer_wikitext_kontrola"].items() if k != "space_1.06_byte_ppl"}
rap["slayer_wikitext_kontrola"] = {**przelicz(wk), "space_1.06_byte_ppl": SPACE_106}
zapisz(f, rap, t)
print(json.dumps({m: por["wikitext"][m]["byte_perplexity"] for m in por["wikitext"]}, indent=1))
print(json.dumps(rap["slayer_wikitext_kontrola"], indent=1, ensure_ascii=False))
