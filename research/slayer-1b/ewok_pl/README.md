Na angielskim EWoK (4374 rekordy) Slayer rośnie z 53,1 do 58,9% (1.00 → 1.06, p < 0,001), a na tych samych
625 rekordach co EWoK-PL o +5,0 pkt. Po polsku przyrost wynosi 1,0 pkt i mieści się w szumie. Bielik-1.5B-v3 ma
po polsku 66,0% (+10,6 pkt nad Slayerem 1.06), LFM3-1.7B-Base 57,4% (różnica ze Slayerem nieistotna).
EWoK-PL obejmuje na razie tylko domenę `agent-properties`.

**Podsumowanie wyników i wnioski: [`WYNIKI.md`](WYNIKI.md).** Pełne liczby: [`../wyniki_ewok/raport_ewok.md`](../wyniki_ewok/raport_ewok.md) (CI95, kontrasty, rozbicia), dane: `raport_ewok.json`.

## Protokół

Jest zgodny z paperem EWoK (Ivanova i in. 2024, [arXiv:2405.09605](https://arxiv.org/abs/2405.09605)), tryb LOGPROBS.

- **Rekord:** C1, C2, T1, T2. T1 pasuje do C1, T2 do C2. Liczymy `log P(T | C)` jako sumę logprob tokenów
  `" " + T` po kontekście `C`.
- **Reguła główna (target stały):** `s1 = [P(T1|C1) > P(T1|C2)]`, `s2 = [P(T2|C2) > P(T2|C1)]`, `wynik = (s1+s2)/2`.
  Losowo wychodzi 50%, remis liczy się jako pudło. Po obu stronach porównania jest ten sam napis T, więc prior
  litery i długości odpowiedzi (główny problem z [raportu Slayera](../README.md)) z definicji
  się tu nie pojawia.
- **Scorer:** `slayer_eval/hipoteza_formatu.py` (`para`, `licz_logliki`, forward `slayer_model.py`). Pary
  kodujemy jak w lm-eval, z jednym BOS przed kontekstem dla wszystkich modeli (METHOD.md Space), w float32.
  Modele HF ładujemy przez `AutoModelForCausalLM` (LFM3 z `trust_remote_code`). Sprawdziliśmy, że
  `glowa(ukryte) == logits` (max |Δ| = 0).
- **Niepewność:** CI95 z bootstrapu (10 000 powtórzeń, seed 20261028). Kontrasty liczymy sparowanym testem
  permutacyjnym z poprawką Holma w każdej rodzinie, jak w Space. Każdą wielkość podajemy na dwa sposoby:
  po rekordach i **po szablonach**. Miarodajna jest ta druga. EWoK wypełnia szablon kilkoma zestawami
  imion i obiektów, więc rekordy jednego szablonu nie są niezależne. Szablon odtwarzamy z EN (`szablony()`):
  w obrębie (para pojęć, domena) słowa obecne w mniej niż 30% rekordów maskujemy jako wypełnienia.
  Daje to 130 szablonów na 625 rekordów PL, zwykle po 5 rekordów. Bootstrap losuje wtedy całe
  szablony, a test permutacyjny zmienia znak różnicy dla całego szablonu naraz.
- **Różnica różnic:** (PL 1.06 − PL 1.00) − (EN 1.06 − EN 1.00) per rekord na tych samych `source_id`.
- **Diagnostyki:**
  - `oba`: obie pary trafione (25% tylko przy niezależnych porównaniach; prior zdania spycha ją niżej);
  - `kontekst_staly`: T1 vs T2 przy tym samym C, wrażliwe na prior zdania;
  - `kontekst_staly_pmi`: to samo po odjęciu `log P(T)`;
  - `staly_target`: udział rekordów, w których model przy obu kontekstach woli to samo zdanie
    (odpowiednik stałej litery A).

| model | rewizja HF |
|---|---|
| SlayerLab/Slayer1B-1.00 … 1.06 | 43e7ca20, 727b5f5e, bf7117b9, fee113ef, 09aa8abf, 21a05bc5, **ef81be58** (= Space) |
| speakleash/Bielik-1.5B-v3 | 4b250496 |
| LiquidAI/LFM3-1.7B-Base | 545fc8f4 (wersja Base, bo loglik liczymy bez szablonu czatu) |
| ewok-core/ewok-core-1.0 (EN) | 34d912a6 |

## Wyniki i ograniczenia

Są w [`WYNIKI.md`](WYNIKI.md): tabela główna z CI po szablonach, wnioski, domeny EN, PL vs EN według par,
stan tłumaczenia, ograniczenia i kolejne kroki. Tutaj ich nie powtarzamy, żeby liczby żyły w jednym miejscu.

## Uruchomienie

```bash
# dane PL czytamy prosto z zipa (hasło jak w oryginale, TERMS_OF_USE EWoK); w repo nie ma tekstu rekordów
python ewok_pl/ewok.py licz --model models/Slayer1B-1.06 --zip ewok-pl-complete-0001-0625.zip \
  --wyjscie wyniki_ewok/Slayer1B-1.06            # domyślnie --dane pl,en; EN wymaga akceptacji gated repo
python ewok_pl/ewok.py analiza --wyniki wyniki_ewok --zip ewok-pl-complete-0001-0625.zip
python tests/test_ewok_pl.py
```

Na RTX 5060 Ti (16 GB) jeden model to ok. 7 min (PL + pełny EN, float32).
Surowe logliki per rekord (`wyniki_ewok/*/*.jsonl`) zostają lokalnie (.gitignore).
