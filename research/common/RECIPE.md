# Przepis: nakładka lm-eval `slayer`

Ten plik nie ma jeszcze wyniku. Kontrolę nakładki na opublikowanych wagach Slayera 1.06 (WikiText-2 przez
`lm_eval --model slayer`) robi #15 i dopisuje tu jej wpis.

## Dlaczego nie ma wyniku T02

Pierwsza wersja nakładki policzyła T02 ARC-Challenge na próbce Space bez BOS przed kontekstem. Space daje jeden
BOS przed każdym zapytaniem, więc tamten wynik nie pochodzi z obecnego kodu. Nie liczymy go ponownie, bo Slayer
ma na T02 wynik na poziomie losowym, więc ta kontrola nie odróżnia działającego modelu od zepsutego.

## Na czym opiera się poprawność

`tests/test_lm_eval_slayer.py`, bez sieci i bez wag:

- forward `slayer_model.py` daje te same logity co oficjalna klasa `GPT` z repo HF modelu
  (`SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`, `load_slayer.py` i
  `train_gpt_ref_r23.py`). Wartości referencyjne liczy `tests/make_slayer_reference.py` na małym losowym checkpoincie
  i zapisuje w `common/tests/data/slayer_reference_logits.json`;
- `loglikelihood`, `loglikelihood_rolling` (także tekst dłuższy niż dwa okna) i `generate_until` dają to samo co
  liczenie bezpośrednio przez `Slayer.logits`, z jednym BOS na początku każdego zapytania;
- nakładka odrzuca `config.json` z kluczami, których `slayer_model.py` nie obsługuje (np. `logit_cap`, `loop`).

## Znane rozbieżności ze Space

- Za długie wejście: Space odrzuca wejście dłuższe niż 4096 tokenów, a lm-eval tnie kontekst od lewej z ostrzeżeniem.
  Przy cięciu znika też BOS. Sprawdź w logu przebiegu, czy pojawiło się „Left truncation applied”.
- Kodu, który policzył wartości Space, nie ma w tym repo, więc adaptera Space nie porównano wprost.
- Lokalne `common/lm_eval_tasks/arc_challenge.yaml` scala `arc_easy.yaml` i `arc_challenge.yaml` z lm-eval (te pliki
  są identyczne w `6d2abda4`, wersji Space, i w 0.4.9.1). Przypina rewizję zbioru z `tasks_50.json` Space, jawnie
  ustawia `target_delimiter: " "` i nie liczy dekontaminacji. Prompt i metryka są te same.
- `generate_until` liczy bez pamięci KV i wiersz po wierszu, więc długie generowanie (IFEval) jest wolne.
