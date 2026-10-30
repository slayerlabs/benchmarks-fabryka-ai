# WikiText-2: mianownik byte_ppl i word_ppl (31.10.2026)

## Problem

Nasz byte_ppl Slayera 1.06 na WikiText-2 test wynosił 1,8925, a Space (lm-eval, commit `6d2abda4`)
podaje 1,846284. <!-- liczba-spoza-wynikow: 2,5% to różnica sprzed korekty, w LICZBY.json jest już wartość po korekcie --> Różnica +2,5% przy forwardzie zgodnym z kodem treningu (`slayer_eval/slayer_model.py`) była
otwartym zadaniem A5 w `lab/DLA_ARKA_I_CHETNYCH.md`.

## Przyczyna

Obie strony liczą tę samą sumę NLL: tekst po `wikitext_detokenizer`, okna rolling, BOS jako prefiks.
Różnił się mianownik.

- lm-eval, `lm_eval/tasks/wikitext/preprocess_wikitext.py`, `process_results`:
  `_bytes = len(doc["page"].encode("utf-8"))`, `_words = len(re.split(r"\s+", doc["page"]))`,
  czyli bajty i słowa ORYGINAŁU, przed detokenizacją (komentarz w kodzie lm-eval mówi to wprost).
- Nasz `slayer_eval/hipoteza_formatu.py` `cmd_wikitext`: `len(tekst.encode())` i `len(tekst.split())`
  na tekście PO detokenizacji, który jest krótszy (detokenizer zjada spacje w „ @-@ ”, „ , ”, „ . ” itd.).

| 62 dokumenty testu | oryginał (lm-eval) | po detokenizacji (nasz stary kod) |
|---|---|---|
| bajty | 1 290 527 | 1 240 466 |
| słowa | 241 335 | 204 373 |

Ta sama suma NLL (791 319 nat) podzielona przez mniej bajtów daje wyższy byte_ppl.

## Liczby przed i po

Przeliczenie bez modelu: nowe ln(ppl) = stare ln(ppl) × stary mianownik / nowy mianownik, osobno dla
bajtów i słów (`wyniki/wikitext_diagnoza/przelicz_mianownik.py`).

| | byte_ppl przed | byte_ppl po | bits_per_byte po | word_ppl przed | word_ppl po |
|---|---|---|---|---|---|
| 1.06 (`raport_formatu`) | 1,8925 | 1,846283824 | 0,8846 | 48,0352 | 26,5471 |
| 1.06 (wygaszanie) | 1,8925 | 1,846283823 | 0,8846 | 48,0352 | 26,5471 |
| A (wygaszanie LR) | 1,8921 | 1,8459 | 0,8843 | 47,9722 | 26,5177 |
| B (stały LR) | 1,9205 | 1,8725 | 0,9049 | 52,5025 | 28,6236 |
| Space 1.06 | | 1,846283836 | | | |

Po korekcie nasz 1.06 i Space różnią się w 8. cyfrze znaczącej (względnie około 6e-9), czyli
różnica +2,5% w całości pochodziła z mianownika. <!-- liczba-spoza-wynikow: 2,5% to różnica sprzed korekty -->

## Cztery niezależne potwierdzenia

1. Źródło lm-eval: `process_results` w `6d2abda4` (wersja używana przez Space) liczy mianownik z
   `doc["page"]`; plik jest identyczny (ten sam SHA-1) w v0.4.8 i v0.4.9.1. Kopia:
   `wyniki/wikitext_diagnoza/dane/lm_eval_src/`.
2. Kąt „dane” (`wyniki/wikitext_diagnoza/dane/bajty.py`, własna przepisana kopia detokenizera):
   liczy bajty obu wersji per dokument i przelicza wynik z `raport_formatu` na 1,846283824.
3. Kąt „tokenizacja” (`wyniki/wikitext_diagnoza/tokenizacja/mianownik.py`, detokenizer wczytany wprost
   z pliku lm-eval): te same liczby bajtów i słów, wynik z wygaszania przeliczony na 1,846283823.
4. Test regresyjny `tests/test_wikitext_mianownik.py`: uruchamia `cmd_wikitext` na dokumencie z
   „ @-@ ” i „ , ” (model i zbiór podstawione) i sprawdza mianownik z oryginału; na starym kodzie
   test pada na wartości byte_perplexity.

## Co się zmienia

- `cmd_wikitext` dzieli przez bajty i słowa oryginału i zapisuje też `nll_suma`, `bajty`, `slowa`.
- Przeliczone (pole `metoda`, stare wartości w `przed_korekta`): `wygaszanie/wyniki/{1.06,A,B}/wikitext.json`,
  sekcja `wikitext` w `wygaszanie/wyniki/porownanie.json`, `slayer_wikitext_kontrola` w
  `wyniki/raport_formatu.json`; z nich `wyniki/LICZBY.json`.
- Stała Space w `slayer_eval/analiza_formatu.py` ma pełną precyzję 1,846283836 zamiast zaokrąglonego 1,846.
- word_ppl spada najmocniej (48,0352 → 26,5471), bo słów w oryginale jest o 18% więcej niż po detokenizacji. <!-- liczba-spoza-wynikow: 18% to stosunek 241 335 / 204 373 z mianownik.json -->

## Co się nie zmienia

- Suma NLL, forward modelu, okna i tokenizacja: korekta dotyczy wyłącznie mianownika.
- Wnioski porównawcze: wszystkie modele dzieli się przez ten sam mianownik, więc kolejność
  A < 1.06 < B na WikiText-2 i wybór wariantu modelu (RoPE gptj + value residual „add”) zostają.
- Liczby z 3-dokumentowej sondy wariantów w komentarzu `slayer_model.py` są w starej konwencji;
  ranking wariantów od mianownika nie zależy.
