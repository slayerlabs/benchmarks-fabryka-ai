# WinoGrande: Slayer 1.06 na T07

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md). Pojęcia (Space, T01–T50, SE, werdykt):
> [słowniczek](../../METODOLOGIA.md#słowniczek).

WinoGrande sprawdza rozumienie zdań z pustym miejscem: model wskazuje jedną z dwóch opcji na miejsce `_`. lm-eval
(`0.4.9.1`, zadanie `winogrande`) podstawia każdą opcję i wybiera tę z wyższym log-prawdopodobieństwem wspólnej
kontynuacji.
Split `validation` zbioru `winogrande_xl`, 0-shot. Metryka decyzyjna to trafność (`acc`). Typ `mc +klastry`: SE
decyzyjne to SE K po klastrach (pary bliźniacze zdań i zdania pojedyncze), SE A po pytaniach jest informacyjne.

## Wyniki

Pełny split, n = 1267, k = 983 klastry.

| model | trafność | n | SE K | SE A |
|---|---:|---:|---:|---:|
| Slayer 1.06 | 0,5217 | 1267 | 0,0122 | 0,0140 |
| `pythia-1b-v0` (kontrola) | 0,5446 | 1267 | 0,0125 | 0,0140 |

Baza b to stała odpowiedź „zawsze opcja 2”: 0,5043. Baza losowa: 0,500.

| porównanie | różnica | SE K | test | werdykt |
|---|---:|---:|---|---|
| Slayer 1.06 wobec b | +1,74 pkt | 0,0162 | t = 1,069, df 982 | szum |
| Pythia wobec b | +4,03 pkt | 0,0159 | t = 2,529, df 982 | prawdopodobne |
| Slayer 1.06 minus Pythia | −2,29 pkt | 0,0160 | t = −1,435, df 982 | szum (po Holmie nie) |

Różnice wobec b są parowane po pytaniach. Pythia odtwarza opublikowane 0,5375 (różnica +0,71 pkt, szum,
w furtce 0,5095–0,5655), więc etap B jest spełniony. Wynik Slayera nie odróżnia się od stałej odpowiedzi.

## Pliki

- [`ORIGINAL.md`](ORIGINAL.md): karta oryginału (etap A)
- [`REPRODUCTION.md`](REPRODUCTION.md): odtworzenie wyniku Pythii (etap B) i werdykt
- [`RECIPE.md`](RECIPE.md): commity, modele, komendy, sprzęt
- [`results/winogrande.json`](results/winogrande.json): liczby zbiorcze; `results/<model>/`: wyniki per pytanie
  (`slayer-1.06`, `pythia-1b-v0`, `pythia-1b-v0-bos`)
- `score.py`, `przelicz.py`: liczenie trafności, SE i testów; `pythia_bos.py`: przebieg kontrolny Pythii z BOS
- `klastry.json`: podział na pary bliźniacze i zdania pojedyncze
- `lm_eval_tasks/winogrande/`: kopia zadania lm-eval z przypiętą rewizją zbioru
