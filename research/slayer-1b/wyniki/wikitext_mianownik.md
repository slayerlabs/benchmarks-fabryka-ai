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

## Diagnoza i trzy niezależne sprawdzenia

Diagnoza: trzech agentów z różnymi kątami (tekst i mianownik, okno i stride, dane i agregacja);
przyczynę znalazł kąt „tokenizacja” (`wyniki/wikitext_diagnoza/tokenizacja/mianownik.py`), dwa
pozostałe zatrzymano po jej znalezieniu. Źródło lm-eval: `process_results` w `6d2abda4` (wersja
Space) liczy mianownik z `doc["page"]`, kopia w `wyniki/wikitext_diagnoza/dane/lm_eval_src/`.

Potem trzy osobne sprawdzenia, każde bez wglądu w pozostałe:

1. Przeliczenie od zera: własne pobranie zbioru, własne liczenie bajtów i słów obiema definicjami,
   ten sam wynik co Space do 8. cyfry (`wyniki/wikitext_diagnoza/dane/bajty.py`).
2. Przegląd adwersarialny z zadaniem obalenia: potwierdził definicję w lm-eval, tę samą agregację
   ważoną po obu stronach, zgodność tokenów (różnica sumy NLL rzędu setnych nata) i to, że liczba
   Space powstała przed naszą, więc nie została przepisana z naszego kodu.
3. Zasięg błędu: ten sam wzorzec tylko w `cmd_wikitext` (i wołającym go `wygaszanie/ewal.py`);
   żaden wniosek porównawczy się nie zmienia, bo korekta jest wspólną monotoniczną transformacją.

Test regresyjny `tests/test_wikitext_mianownik.py` uruchamia `cmd_wikitext` na dokumencie z
„ @-@ ” i „ , ” (model i zbiór podstawione) i na starym kodzie pada na wartości byte_perplexity.

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
