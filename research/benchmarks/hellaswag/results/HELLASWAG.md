# HellaSwag: wyniki

Wygenerowane z `results/raw/*.jsonl.gz` przez `python benchmarks/hellaswag/hellaswag.py report`.
Metryka decyzyjna to `acc_norm`. `acc` jest obok, bez osobnego werdyktu.

| przebieg | n | acc_norm | SE | acc | najczęstsza predykcja | baza większościowa |
|---|---:|---:|---:|---:|---:|---:|
| EuroLLM 10-shot | 10042 | 0,6074 | 0,0049 | 0,4534 | 0,2521 | 0,2573 |
| Slayer 10-shot | 10042 | 0,3953 | 0,0049 | 0,3247 | 0,2548 | 0,2573 |
| Slayer 0-shot, cały split | 10042 | 0,3938 | 0,0049 | 0,3244 | 0,2589 | 0,2573 |
| Slayer 0-shot, panel 200 | 200 | 0,4350 | 0,0351 | 0,2750 | 0,2750 | 0,3000 |

Baza losowa to 0,25.
EuroLLM wobec bazy większościowej: różnica 0,3501, SE 0,0065, z = 53,63, pewne.
Slayer 10-shot wobec bazy większościowej: różnica 0,1380, SE 0,0065, z = 21,20, pewne.
Slayer minus EuroLLM, 10-shot, te same pytania: różnica −0,2121, SE 0,0045, z = −46,83, pewne.
Karta EuroLLM: 0,6057. Nasz EuroLLM: 0,6074. Różnica 0,0017. Próg 0,02, a 2 SE naszego wyniku to 0,0097, więc obowiązuje próg 0,02. Warunek odtworzenia: spełniony.
Space T05, Slayer 0-shot, panel 200: 0,365. Nasz panel: 0,435. Różnica 0,0700. 2 SE panelu 0,0701. Różnica jest mniejsza od 2 SE.
