# WikiText-2: mianownik perpleksji na bajt i na słowo

WikiText-2 (Merity i in. 2016) to zadanie modelowania języka T03 w Space: perpleksja 62 dokumentów
testowych, liczona przez lm-eval w commicie `6d2abda4fd171e68a8789330c4149e37c1ca0bda`. W tym katalogu jest
diagnoza i poprawka różnicy między naszą perpleksją na bajt Slayera 1.06 a wartością ze Space (PR #8).

- [ORIGINAL.md](ORIGINAL.md): karta zbioru i zadania `wikitext` z lm-eval (etap A).
- [REPRODUCTION.md](REPRODUCTION.md): odtworzenie wartości Space dla Slayera 1.06 i czego brakuje (etap B).
- [RECIPE.md](RECIPE.md): modele, rewizje, komendy i sprzęt dla każdej liczby niżej.

## Problem

Nasza perpleksja na bajt Slayera 1.06 wynosiła 1,8925, a Space podaje 1,846283836. Forward był zgodny
z kodem treningu (`common/slayer_model.py`), więc źródło różnicy było nieznane.

## Przyczyna

Obie strony liczą tę samą sumę NLL: tekst po `wikitext_detokenizer`, okna rolling, BOS jako prefiks.
Różnił się mianownik.

- lm-eval, `process_results` w `preprocess_wikitext.py`: bajty i słowa ORYGINALNEGO tekstu `doc["page"]`,
  przed detokenizacją (komentarz w kodzie mówi to wprost).
- Nasz stary `cmd_wikitext` w `common/hipoteza_formatu.py`: bajty i słowa tekstu po detokenizacji, który
  jest krótszy (detokenizer usuwa spacje w `" @-@ "`, `" , "`, `" . "` i podobnych).

| 62 dokumenty testu | oryginał (lm-eval) | po detokenizacji (nasz stary kod) |
|---|---:|---:|
| bajty | 1290527 | 1240466 |
| słowa | 241335 | 204373 |

Ta sama suma NLL (791319 natów) podzielona przez mniej bajtów daje wyższą perpleksję na bajt. Źródło:
`results/bajty.json`, `results/mianownik.json`.

## Wyniki przed poprawką i po niej

Przeliczenie bez modelu: nowe ln(ppl) = stare ln(ppl) x stary mianownik / nowy mianownik, osobno dla
bajtów i słów (`przelicz_mianownik.py`). Wszystkie wartości: n = 62 dokumenty. W naszych plikach
perpleksja nie ma SE (nie liczyliśmy bootstrapu po dokumentach), więc żaden wiersz go nie ma.

| model | ppl na bajt przed | ppl na bajt po | bity na bajt po | ppl na słowo przed | ppl na słowo po |
|---|---:|---:|---:|---:|---:|
| Slayer 1.06 (przebieg kontrolny, `raport_formatu.json`) | 1,8925 | 1,846283824 | 0,8846 | 48,0352 | 26,5471 |
| Slayer 1.06 (`wygaszanie/wyniki/1.06`) | 1,8925 | 1,846283823 | 0,8846 | 48,0352 | 26,5471 |
| A (wygaszanie LR, `wygaszanie/wyniki/A`) | 1,8921 | 1,8459 | 0,8843 | 47,9722 | 26,5177 |
| B (stały LR, `wygaszanie/wyniki/B`) | 1,9205 | 1,8725 | 0,9049 | 52,5025 | 28,6236 |
| Space, Slayer 1.06 | | 1,846283836 | | | |

## Wnioski

- Po poprawce nasz Slayer 1.06 i Space zgadzają się do ósmej cyfry znaczącej, więc cała różnica
  pochodziła z mianownika (werdykt wobec spisanego progu: nierozstrzygalne, bo metodologia nie ma jeszcze
  progu dla perpleksji, zadanie #41); zob. [REPRODUCTION.md](REPRODUCTION.md).
- Najmocniej spada perpleksja na słowo (z 48,0352 do 26,5471), bo oryginalny tekst ma dużo więcej słów
  rozdzielonych białymi znakami niż tekst po detokenizacji (241335 wobec 204373).
- Zmienia się tylko mianownik. Suma NLL, forward, okna i tokenizacja zostają bez zmian.
- Porównania między checkpointami się nie zmieniają, bo wszystkie modele mają ten sam mianownik: kolejność
  A, Slayer 1.06, B na WikiText-2 zostaje i zostaje wybór wariantu modelu (RoPE `gptj`, value residual
  `add`). Czy A jest lepszy od Slayera 1.06 albo od B, jest nierozstrzygalne: te perpleksje nie mają SE.
- `results/mianownik.json` porównuje z wartością Space zaokrągloną do `1.846`; jego `roznica_po_proc`
  odzwierciedla to zaokrąglenie. Porównanie w pełnej precyzji jest w `results/bajty.json`.
- Wartości z 3-dokumentowej sondy wariantów w komentarzu `common/slayer_model.py` są w starej konwencji;
  ranking wariantów nie zależy od mianownika.

## Pliki

- `bajty.py`, `results/bajty.json`: bajty i słowa obiema definicjami, obie konfiguracje zbioru, per dokument.
- `mianownik.py`, `results/mianownik.json`: pierwsza diagnoza (kąt mianownika).
- `przelicz_mianownik.py`: przelicza zapisane wyniki w `slayer-1b/wygaszanie/wyniki/` i
  `analyses/answer-format/results/raport_formatu.json`.
- `lm_eval_src/`: kopia `preprocess_wikitext.py` z lm-eval w `6d2abda4fd171e68a8789330c4149e37c1ca0bda`.
- Poprawka kodu: `cmd_wikitext` w `common/hipoteza_formatu.py` dzieli teraz przez oryginalny tekst i
  zapisuje `nll_suma`, `bajty`, `slowa`; test regresyjny `tests/test_wikitext_mianownik.py`.

## Co dodaje metodologia

- [ ] Uruchomić samo lm-eval (`--tasks wikitext`, commit `6d2abda4fd171e68a8789330c4149e37c1ca0bda`) na
      Slayerze 1.06 i porównać z naszym `cmd_wikitext`; na razie etap B stoi na naszym forwardzie
      z elementami lm-eval.
- [ ] Model kontrolny `EleutherAI/pythia-1b-v0` @ `step143000` na WikiText-2, przez lm-eval i naszym kodem.
- [ ] Ustalić próg zgodności dla perpleksji i BPB (zadanie #41 metodologii), potem dać etapowi B formalny
      werdykt.
- [ ] Dodać SE albo CI dla perpleksji na bajt (np. bootstrap po 62 dokumentach), żeby porównania
      checkpointów (A wobec B) dostały werdykt.
- [ ] Test zgodności `tests/test_wikitext_zgodnosc.py`: wartości per dokument z oryginalnego kodu dla 10-20
      dokumentów w pliku, nasz kod w granicach limitu per dokument, bez sieci. Obecny
      `tests/test_wikitext_mianownik.py` sprawdza tylko mianownik.
- [ ] Pięć modeli odniesienia z metodologii na WikiText-2.
- [ ] Brakujące pola przepisu: commit kodu każdego przebiegu forwardu, sprzęt przebiegu kontrolnego, wersje
      pakietów na instancji GPU, miejsce wag A i B ([RECIPE.md](RECIPE.md)).
