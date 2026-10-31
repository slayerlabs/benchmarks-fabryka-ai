# WikiText-2: odtworzenie (etap B)

## Co odtworzyliśmy

Perpleksję na bajt Slayera 1.06 na teście WikiText-2 ze Space (zadanie T03), liczoną przez lm-eval
w commicie `6d2abda4fd171e68a8789330c4149e37c1ca0bda`.

| | wartość |
|---|---|
| model | `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609` |
| dane | `EleutherAI/wikitext_document_level` @ `647234772b9554e208af6c826f23b99e3cac88c8`, `wikitext-2-raw-v1`, `test` |
| n | 62 dokumenty, 1290527 bajtów, 241335 słów (cały split testowy, bez próbkowania) |
| kod | nasz: `common/hipoteza_formatu.py` `cmd_wikitext` z forwardem z `common/slayer_model.py`; detokenizer i okna rolling wzięte z lm-eval (`preprocess_wikitext.py`, `lm_eval.utils.get_rolling_token_windows`) |
| nasza perpleksja na bajt | 1,846283824 (`analyses/answer-format/results/raport_formatu.json`, `slayer_wikitext_kontrola`); drugi przebieg forwardu w `slayer-1b/wygaszanie/wyniki/1.06/wikitext.json` daje 1,846283823 |
| odniesienie (Space) | 1,846283836 |
| SE | brak: ani nasze pliki, ani skopiowana wartość ze Space nie mają SE ani CI dla tej perpleksji |
| różnica | zgodność do ósmej cyfry znaczącej (`roznica_po_przeliczeniu_proc` w `results/bajty.json`) |
| werdykt | zgodne; dla perpleksji nie ma formalnego progu (zadanie #41 metodologii), więc wobec spisanej reguły werdykt jest nierozstrzygalny |

Nasza wartość pochodzi z przeliczenia, nie z nowego uruchomienia modelu: pierwotny przebieg dzielił tę
samą sumę NLL (791319 natów) przez bajty tekstu po detokenizacji (1240466) i dawał 1,8925. Podział przez
bajty oryginalnego tekstu, jak w lm-eval, daje wartość z tabeli (`przelicz_mianownik.py`,
`results/mianownik.json`). Sama suma NLL się nie zmieniła, więc odtworzenie potwierdza i forward (ten sam
licznik co w lm-eval), i definicję mianownika.

Sprawdzenia, na których stoi werdykt (z raportu PR #8):

1. Niezależne przeliczenie bajtów i słów obiema definicjami na świeżo pobranym zbiorze (`bajty.py`,
   `results/bajty.json`): te same mianowniki, ta sama przeliczona wartość.
2. Przegląd z zadaniem obalenia: definicja mianownika w lm-eval, ta sama ważona agregacja po obu stronach,
   zgodne tokeny (dwie sumy NLL różnią się o około tysięczną część nata), a wartość Space powstała przed
   naszą, więc nie została przepisana z naszego kodu.
3. Zasięg: stary mianownik był tylko w `cmd_wikitext` i w wołającym go `slayer-1b/wygaszanie/ewal.py`.
4. Test regresyjny `tests/test_wikitext_mianownik.py` (model i zbiór podstawione, bez sieci) przechodzi na
   obecnym kodzie; raport podaje, że na starym kodzie pada (tu tego nie sprawdzaliśmy ponownie).

## Czego NIE zrobiliśmy

- **Nie uruchomiliśmy samego lm-eval.** Etap B wymaga oryginalnego kodu; tu licznik pochodzi z naszego
  forwardu Slayera, z detokenizerem, oknami i definicją `process_results` z lm-eval. Zgodność ze Space
  mocno wskazuje, że obie ścieżki liczą to samo, ale to nie jest przebieg `lm_eval --tasks wikitext`.
- **Brak modelu kontrolnego.** `EleutherAI/pythia-1b-v0` @ `step143000` nie był liczony na WikiText-2 ani
  przez lm-eval, ani naszym kodem.
- **Brak progu dla perpleksji.** Reguła zgodności metodologii (2 pkt albo 2 SE) dotyczy trafności; próg
  dla perpleksji i BPB jest wciąż otwarty (zadanie #41 metodologii).
- **Brak porównania per dokument.** Etap C wymaga różnicy per dokument poniżej `0,1%` (próg metodologii,
  nie wynik); wartości per dokument ze Space nie ma w naszych plikach, więc porównaliśmy tylko wartość dla
  całego korpusu.
