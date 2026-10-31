# Analiza formatu odpowiedzi: odtworzenie (etap B)

**Etapu B nie zrobiono kodem autorów ani lm-eval.** Najbliżej jest test T0: zanim policzyliśmy Slayera, nasz
własny scorer (`common/hipoteza_formatu.py`) policzył dwa publiczne modele, a wyniki porównano z opublikowanymi.
Pokazuje to, że nasz scorer odtwarza liczby lm-eval dla cloze na ARC. Nic nie mówi o formatach z literami,
MedMCQA, Social IQa, Belebele, MMLU ani MultiBLiMP: dla nich żadnej referencji nie odtworzono.

Źródło każdej liczby niżej: `results/raport_formatu.json`, klucz `test0` (SE z `zestawienie`).

## T0: Pythia-1B, 0-shot ARC (cloze)

| | wartość |
|---|---|
| liczony model | `EleutherAI/pythia-1b` @ `f73d7dcc545c8bd326d8559c8ef84ffe92fea6b2` (gałąź `main`), float32 |
| model referencyjny | `EleutherAI/pythia-v1.1-1b-bf16` @ `step143000`, bfloat16 (pole `model_args` opublikowanego pliku) |
| plik referencyjny | [`evals/pythia-v1/pythia-1b-bf16/zero-shot/1b-bf16_step143000.json`](https://github.com/EleutherAI/pythia/blob/58f33c6e3b521435f5af695eeb3a327a35ac4e58/evals/pythia-v1/pythia-1b-bf16/zero-shot/1b-bf16_step143000.json), stary harness `hf-causal`, wersja zadania 0, batch 32 |
| nasz kod | `common/hipoteza_formatu.py licz`, zadania `arc_e_cloze`, `arc_c_cloze`; prompt `"Question: {q}\nAnswer:"` + `" {option}"` jak lm-eval `arc_easy` / `arc_challenge` |
| dane | `allenai/ai2_arc` @ `210d026faf9955653af8916fad021475a3f00453`, test |

| zadanie | metryka | n | nasza | SE | opublikowana | różnica w punktach | reguła `<= 2 pkt` |
|---|---|---:|---:|---:|---:|---:|---|
| ARC-Easy | acc | 2376 | 0,5699 | 0,0102 | 0,5694 | 0,05 | w granicach |
| ARC-Easy | acc_norm | 2376 | 0,4899 | 0,0103 | 0,4903 | −0,04 | w granicach |
| ARC-Challenge | acc | 1172 | 0,2440 | 0,0125 | 0,2440 | 0,00 | w granicach |
| ARC-Challenge | acc_norm | 1172 | 0,2705 | 0,0130 | 0,2713 | −0,08 | w granicach |

Werdykt: **zgodne** we wszystkich czterech wartościach (największa różnica bezwzględna poniżej dziesiątej
części punktu, w granicach reguły ±2 pkt i w granicach jednego SE).

Ograniczenia (liczb z ich powodu nie zmieniano):

- **To nie jest model kontrolny metodologii.** Metodologia wskazuje `EleutherAI/pythia-1b-v0` @ `step143000`
  jako kontrolę etapu B. Liczyliśmy obecny `EleutherAI/pythia-1b`; plik referencyjny pochodzi z katalogu
  ewaluacji `pythia-v1` dla modelu o nazwie `pythia-v1.1-1b-bf16`. Modelu `-v0` nie policzono.
- **Precyzja.** Referencja liczona na wagach bfloat16, nasza w float32.
- **Rewizja.** Nasza rewizja to `main` (`f73d7dcc`); referencja podaje gałąź `step143000`, która dziś na Hubie
  wskazuje inny commit (`c0fea4b9`). Czy oba mają te same wagi, nie sprawdzono.
- **Harness.** Referencja użyła harnessu sprzed wersji 0.4 (`hf-causal`); nasz scorer kopiuje kodowanie
  `lm-eval 0.4.9.1`. Zgodność sugeruje, że oba kodują ARC tak samo, ale porównania per pytanie nie zrobiono
  (plik referencyjny ma tylko wartości zbiorcze).

## T0: `Qwen2.5-0.5B`, 25-shot ARC-Challenge (cloze)

| | wartość |
|---|---|
| liczony model | etykieta `Qwen2.5-0.5B` (repo na Hubie zapewne `Qwen/Qwen2.5-0.5B`; repo i rewizja nie zapisane), float32 (`ModelHF` ładuje float32) |
| nasz kod | zadanie `arc_c_cloze_25shot`: 25 przykładów z train losowanych dla każdego pytania z seedem `1234|{id}`, potem prompt cloze 0-shot |
| referencja | raport techniczny Qwen2.5, [arXiv](https://arxiv.org/abs/2412.15115), tabela modeli bazowych (Tab. 5 według `analiza_formatu.py`): ARC-C 25-shot acc_norm 0,356 <!-- liczba-spoza-wynikow: identyfikator arXiv w adresie --> |
| n | 1172 |
| nasza | acc_norm 0,3609 (SE nie zapisane w raporcie: `arc_c_cloze_25shot` nie ma w `zestawienie`) |
| różnica w punktach | 0,49 |
| werdykt | **zgodne** z regułą ±2 pkt |

Ograniczenie: raport Qwena nie publikuje przykładów few-shot ani kodu ewaluacji, więc nasze przykłady różnią się
od ich; zgodność dotyczy tylko wartości zbiorczej.

## Co T0 ustala, a czego nie

- To sprawdzenie **naszego scorera**, a nie odtworzenie żadnego benchmarku oryginalnym kodem.
- Obejmuje tylko format cloze na ARC. Żadne inne zadanie ani żaden format z literami nie ma odtworzonej
  referencji; dla większości z nich (litery na ARC/SIQA, cloze na MedMCQA/Belebele/MMLU) opublikowana referencja
  nie istnieje, bo te formaty są nasze.
- Dla tego scorera nie ma testu zgodności (`tests/test_<name>_zgodnosc.py`) z decyzjami lm-eval per pytanie.
