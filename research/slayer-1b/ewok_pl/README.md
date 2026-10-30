# EWoK-PL: Slayer 1B 1.00–1.06, Bielik 1.5B, LFM3 1.7B (30.10.2026)

Na polskim EWoK-PL (625 rekordów) Slayer 1.06 ma 55,4% przy losowym 50% i nie rośnie od 1.00
(+1,0 pkt, p = 0,55). Na pełnym angielskim EWoK (4374) ten sam model rośnie z 53,1 do 58,9%
(+5,7 pkt, p < 0,001). Bielik-1.5B-v3 ma po polsku 66,0%, czyli 10,6 pkt więcej niż Slayer 1.06 (p < 0,001).
LFM3-1.7B-Base ma po polsku 57,4% (różnica ze Slayerem w granicach szumu), ale po angielsku 66,6%.
Dzisiejszy EWoK-PL obejmuje tylko domenę `agent-properties`, więc nie mówi jeszcze nic
o fizyce, przestrzeni ani relacjach społecznych.

Pełne liczby: [`../wyniki_ewok/raport_ewok.md`](../wyniki_ewok/raport_ewok.md) (CI95, kontrasty, rozbicia), dane: `raport_ewok.json`.

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
  permutacyjnym (zmiana znaku per rekord) z poprawką Holma w każdej rodzinie, jak w Space.
- **Diagnostyki:**
  - `oba`: obie pary trafione (losowo 25%);
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

## Wyniki

| model | PL (625) | EN, te same 625 | EN pełny (4374) | PL `stały target` |
|---|---|---|---|---|
| Bielik-1.5B-v3 | **66,0** [63,4; 68,5] | 62,8 | 69,5 | 75% |
| LFM3-1.7B-Base | 57,4 [55,0; 59,8] | 66,6 | **69,7** | 74% |
| Slayer1B-1.00 | 54,4 [52,0; 56,8] | 51,3 | 53,1 | 81% |
| Slayer1B-1.03 | 54,6 [52,3; 56,9] | 52,0 | 55,8 | 81% |
| Slayer1B-1.06 | 55,4 [53,0; 57,8] | 56,2 | 58,9 | 84% |

Wnioski:

1. **Slayer uczy się wiedzy o świecie, ale na PL-625 tego nie widać.** Na EN 1.06 jest lepszy od 1.00
   o 5,7 pkt (CI95 +4,7…+6,8). Rosną głównie `material-dynamics` (53 → 67), `social-properties`
   (58 → 68) i `social-relations` (51 → 57). Na PL-625 różnice między kolejnymi wersjami mają wszystkie
   p_holm > 0,8. Te same 625 rekordów po angielsku (EN625) też dają u Slayera tylko 51–57%, więc wąską
   próbkę wyjaśnia sam wybór domeny, a nie tłumaczenie.
2. **Para „make more / less effort” (220 z 625 rekordów) jest na poziomie losowym dla wszystkich modeli**
   (Bielik 57, LFM3 55, Slayer 48–52). To 35% PL-625 i właśnie ten kawałek spłaszcza wynik. Flagi
   przeglądu (`review_flags`) nie przewidują porażki modeli: 45 rekordów bez flagi wypada nie lepiej niż reszta.
3. **Polski Slayer nie ma przewagi nad LFM3 po polsku** (−2,0 pkt, p = 0,20), choć LFM3 nie deklaruje
   polskiego. Bielik wygrywa wyraźnie (+10,6 pkt). Wniosek jest zawężony do `agent-properties`.
4. **Ślad prioru zdania:** przy porównaniu T1 vs T2 w tym samym kontekście Slayer w 81–85% rekordów
   wybiera to samo zdanie niezależnie od kontekstu (Bielik i LFM3 74–75%). Reguła z paperu jest na to
   odporna, dlatego jest metryką główną.
5. **Gdzie Slayer 1.06 nie ma wiedzy (EN, ≤ 55%):** `physical-relations` 51, `physical-interactions` 54,
   `spatial-relations` 55, `agent-properties` 55. U Bielika i LFM3 te domeny, razem z
   `material-properties`, też wypadają najsłabiej (55–62%).
6. **Do przeglądu tłumaczenia:** tylko 3 rekordy mają średnio po modelach EN − PL ≥ 0,5
   (ewok-pl-0141, 0149, 0171). Lista jest w `raport_ewok.json` → `do_przegladu`.

## Ograniczenia

- EWoK-PL to wersja **robocza** (`draft_review_required`): 580/625 rekordów ma flagę przeglądu.
  Wynik dotyczy jednej domeny i 9 par pojęć.
- Zgodności scorera z liczbami z paperu EWoK nie sprawdzaliśmy (brak opublikowanych liczb dla tych
  modeli). Scorer przeszedł test 0 w `slayer_eval` (Pythia/Qwen vs lm-eval).
- Nie ma skanu kontaminacji. EWoK jest szyfrowany właśnie po to, żeby nie trafiał do korpusów, a EWoK-PL
  nie był publikowany.

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
