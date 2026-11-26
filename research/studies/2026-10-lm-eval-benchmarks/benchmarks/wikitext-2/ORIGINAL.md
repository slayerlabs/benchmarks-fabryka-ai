# WikiText-2: karta oryginału (etap A)

Opisujemy tu dwie warstwy: zbiór danych w wersji autorów (Merity i in. 2016) oraz metrykę liczoną przez
implementację, której używa Space (zadanie lm-eval `wikitext` w commicie
`6d2abda4fd171e68a8789330c4149e37c1ca0bda`). Nasze wyniki porównujemy z tą drugą.

## Co mierzy

Jakość modelowania języka na długim, starannie napisanym angielskim tekście z Wikipedii. Karta zbioru
mówi, że WikiText to "a collection of over 100 million tokens extracted from the set of verified Good and
Featured articles on Wikipedia", który "retains the original case, punctuation and numbers". Wynik to
perpleksja; im niższa, tym lepiej dla modelu (to kierunek metryki, nie porównanie wyników).

## Źródła

- Praca: Merity, Xiong, Bradbury, Socher, "Pointer Sentinel Mixture Models", 2016,
  [arXiv](https://arxiv.org/abs/1609.07843) (wprowadza WikiText-2 i WikiText-103).
- Implementacja używana przez Space: EleutherAI lm-evaluation-harness, zadanie `wikitext`, commit
  `6d2abda4fd171e68a8789330c4149e37c1ca0bda`:
  [`lm_eval/tasks/wikitext/`](https://github.com/EleutherAI/lm-evaluation-harness/tree/6d2abda4fd171e68a8789330c4149e37c1ca0bda/lm_eval/tasks/wikitext),
  zwłaszcza [`wikitext.yaml`](https://github.com/EleutherAI/lm-evaluation-harness/blob/6d2abda4fd171e68a8789330c4149e37c1ca0bda/lm_eval/tasks/wikitext/wikitext.yaml)
  i [`preprocess_wikitext.py`](https://github.com/EleutherAI/lm-evaluation-harness/blob/6d2abda4fd171e68a8789330c4149e37c1ca0bda/lm_eval/tasks/wikitext/preprocess_wikitext.py).
  Dokładna kopia tego drugiego pliku leży w `lm_eval_src/`. Ten sam plik w tagu `v0.4.9.1` (wersja
  przypięta w `common/requirements.lock.txt`) jest identyczny z kopią (sprawdzone `diff`).
- Karta zbioru używana przez lm-eval: [`EleutherAI/wikitext_document_level`](https://huggingface.co/datasets/EleutherAI/wikitext_document_level/tree/647234772b9554e208af6c826f23b99e3cac88c8)
  @ `647234772b9554e208af6c826f23b99e3cac88c8`, konfiguracja `wikitext-2-raw-v1`. Karta oryginalnego wydania:
  [`Salesforce/wikitext`](https://huggingface.co/datasets/Salesforce/wikitext).
- Kod autorów: kod modelu z pracy nie jest częścią benchmarku; benchmark to dane i definicja perpleksji.
  Oficjalnego skryptu oceny od autorów nie znaleźliśmy (szukaliśmy w pracy i na karcie zbioru Salesforce).

## Dane

- Split do wyników: `test`.
- n: w zbiorze na poziomie dokumentów, w przypiętej rewizji, 62 dokumenty testowe (train 629, validation 60;
  `results/bajty.json`). Praca (tabela 1) podaje dla WikiText-2 600 / 60 / 60 artykułów, 245569 tokenów
  w teście i słownik 33278 słów. Dlaczego zbiór na poziomie dokumentów ma 62 dokumenty testowe, a nie 60,
  nie ustaliliśmy (nie porównywaliśmy granic artykułów).
- Rozmiar testu tak, jak liczy go lm-eval: 1290527 bajtów UTF-8 i 241335 słów (podział oryginalnego tekstu
  po białych znakach) w 62 dokumentach (`results/bajty.json`, `results/mianownik.json`).
- Licencja: tagi `cc-by-sa-3.0` i `gfdl` na karcie Salesforce (tekst karty wymienia też `CC BY-SA 4.0`).
- Ukryte odpowiedzi: nie. Tekst testu jest publiczny, więc mógł trafić do korpusu treningowego.

## Format zadania

Perpleksja całego dokumentu. Bez pytania i bez opcji.

## Prompt

Brak. lm-eval używa `output_type: loglikelihood_rolling`, `doc_to_text: ""` i
`doc_to_target: wikitext_detokenizer(doc)`: surowy tekst (`doc["page"]`, w którym tokeny rozdzielają
spacje, a liczby są zapisane jak `1 @,@ 000`) najpierw przechodzi detokenizację (`" @-@ "` na `"-"`,
`" , "` na `", "`, usunięte spacje w nawiasach i cudzysłowach itd.). Model ocenia tekst po detokenizacji
w rozłącznych oknach rolling o maksymalnej długości modelu; każde okno jest warunkowane poprzednimi
tokenami do tej długości, a pierwsze dostaje na początek token BOS / end-of-text. 0-shot.

## Ocena

`process_results` zwraca dla każdego dokumentu sumę log-likelihood tekstu po detokenizacji oraz dwa
mianowniki liczone na ORYGINALNYM tekście, przed detokenizacją (komentarz w kodzie mówi to wprost):

- bajty: `len(doc["page"].encode("utf-8"))`
- słowa: `len(re.split(r"\s+", doc["page"]))`

Metryki: `byte_perplexity` = exp(NLL / bajty), `bits_per_byte` = NLL / bajty / ln 2,
`word_perplexity` = exp(NLL / słowa). Niezgodność jest zamierzona: licznik pochodzi z tekstu po
detokenizacji, mianownik z oryginału, który jest dłuższy. Perpleksja w pracy jest liczona na token
słownikowy tekstu stokenizowanego, więc liczby z pracy i z lm-eval są w innej skali.

## Agregacja

Perpleksja ważona na poziomie korpusu: NLL i mianowniki sumuje się po wszystkich dokumentach, dopiero
potem dzieli (agregacje lm-eval `weighted_perplexity` i `bits_per_byte`). Długie dokumenty ważą więcej.
Bez podziału na kategorie.

## Wyniki referencyjne

- Praca, tabela 3: Pointer Sentinel-LSTM, perpleksja na słowo w teście WikiText-2 równa 80,8. <!-- liczba-spoza-wynikow: wartość z pracy Merity i in. 2016, tabela 3, nie liczona przez nas -->
  To model trenowany na WikiText-2 z zamkniętym słownikiem; nie da się go pobrać i nie jest porównywalny
  z perpleksją na bajt z lm-eval.
- Metryka lm-eval, model do pobrania: Space
  [`SlayerLab/Slayer1B-Benchmarks`](https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks), zadanie T03,
  `results.json`: perpleksja na bajt `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`
  = 1,846283836 (n = 62 dokumenty; kopia w `analyses/answer-format/results/raport_formatu.json`, klucz
  `space_1.06_byte_ppl`). Tę wartość odtwarza nasz etap B.
- `EleutherAI/pythia-1b-v0` @ `step143000` (model kontrolny metodologii): w naszych plikach nie ma
  opublikowanej perpleksji na bajt na WikiText; nieustalone.

## Znane rozbieżności

- Mianownik: implementacja, która dzieli przez bajty albo słowa tekstu po detokenizacji (jak nasz stary
  `cmd_wikitext`), dostaje wyższą perpleksję. W 62 dokumentach testu tekst po detokenizacji ma
  1240466 bajtów i 204373 słowa zamiast 1290527 i 241335 (stosunek bajtów 1,0404, `results/bajty.json`).
  Najmocniej zmienia się perpleksja na słowo.
- `wikitext-2-raw-v1` a `wikitext-2-v1`: konfiguracja bez „raw” zastępuje rzadkie słowa przez `<unk>` i ma
  w teście 1256386 bajtów zamiast 1290527 (`results/bajty.json`); lm-eval używa wersji raw.
- Inne definicje perpleksji na bajt: drugi Space `SlayerLab/Slayer1B` trzyma w `scores-history.csv`
  kolumnę `wikitext2_byte_ppl` liczoną inaczej (notatka Space do T03: "not the historical Glint tp^(N/B)
  conversion"; zob. `common/README.md`). Jej wartości nie są porównywalne z T03.
- Długość okna zależy od maksymalnego kontekstu modelu, więc ten sam model oceniany z innym `max_length`
  dostaje nieco inną perpleksję.
- Kontaminacja: tekst to publiczna Wikipedia; nie mamy skanu korpusu treningowego Slayera pod tym kątem.
