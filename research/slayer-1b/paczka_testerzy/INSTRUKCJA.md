# Paczka dla testerów: surowe log-prawdopodobieństwa Slayer1B-1.06 i Pythia-1B

Paczka zawiera wyłącznie surowe dane per pytanie. Nie ma w niej żadnych wyników zbiorczych —
liczysz je sam (zadania w `PYTANIA.md`).

W repozytorium są tylko `INSTRUKCJA.md`, `PYTANIA.md` i `SHA256SUMS`. Katalog `dane/` jest w
`paczka_testerzy.zip`, który dostajesz od autorów repo osobno (sha256 zipa w `README.md`), albo
generujesz sam kodem repo (sekcja „Jak wygenerować surowe dane od zera”); własne pliki nie
przejdą pieczęci bajt w bajt. Przed pracą na zipie sprawdź pieczęć:

    cd paczka_testerzy && shasum -a 256 -c SHA256SUMS

## Zawartość

- `dane/slayer-1.06/*.jsonl` — model `SlayerLab/Slayer1B-1.06`, rewizja `ef81be58742544ad32e1afab38db011fec209609`.
- `dane/pythia-1b/*.jsonl` — model `EleutherAI/pythia-1b` (gałąź główna HF).
- Jeden plik = jedno zadanie, jeden wiersz = jedno pytanie (JSON).

Zadania (nazwa pliku):

| plik | zbiór | split | format |
|---|---|---|---|
| `arc_c_mc`, `arc_c_cloze` | allenai/ai2_arc ARC-Challenge, rew. `210d026f…` | test | litery / treść |
| `arc_c_mc_przes` (tylko Slayer) | jw., treści odpowiedzi przesunięte cyklicznie | test | litery |
| `arc_c_mc_bezspacji` (tylko Slayer) | jw., kontynuacja „A” bez spacji | test | litery |
| `arc_c_mc_5shot` (tylko Slayer) | jw., 5 przykładów z train przed pytaniem | test | litery |
| `arc_e_mc`, `arc_e_cloze` | ARC-Easy | test | litery / treść |
| `med_mc`, `med_cloze` | openlifescienceai/medmcqa, rew. `91c6572c…` | validation | litery / treść |
| `mmlu_mc`, `mmlu_cloze` | cais/mmlu, wszystkie przedmioty | test | litery / treść |
| `siqa_mc`, `siqa_cloze` | allenai/social_i_qa | validation | litery / treść |
| `belebele_mc`, `belebele_cloze` | facebook/belebele pol_Latn | test | litery / treść |
| `multiblimp` | jumelet/multiblimp pol (pary zdań) | — | para zdań |

## Pola wiersza

- `id` — identyfikator pytania ze zbioru (dla siqa `siqa{i}`, dla mmlu `{przedmiot}|{i}`, dla
  multiblimp `mb{i}`). Te same `id` w obu modelach dotyczą tego samego pytania.
- `grupa` (nie we wszystkich plikach) — przedmiot MMLU albo zjawisko MultiBLiMP; inaczej `null`.
- `gold` — indeks poprawnej odpowiedzi, od 0 (0 = A, 1 = B, …).
- `k` — liczba opcji.
- `ll` — lista długości `k`: dla każdej opcji SUMA log-prawdopodobieństw (logarytm naturalny)
  tokenów kontynuacji pod warunkiem kontekstu (promptu), czyli log P(kontynuacja | prompt).
- `ntok` — liczba tokenów kontynuacji każdej opcji (tokenizer danego modelu; modele mają RÓŻNE
  tokenizery).
- `bezw` — tylko w części plików cloze (`arc_c_cloze`, `med_cloze`, `siqa_cloze`,
  `belebele_cloze`), gdzie indziej `null`: suma log-prawd. tej samej kontynuacji z PUSTYM
  kontekstem (sam token początkowy modelu), czyli log P(kontynuacja). Służy do PMI:
  `ll[i] − bezw[i]`.
- `bajty` — długość kontynuacji w bajtach UTF-8, łącznie z wiodącą spacją (np. „ A” = 2 bajty,
  „A” bez spacji = 1). Do normalizacji `ll / bajty`.
- `znaki` — w cloze i multiblimp: liczba znaków treści opcji BEZ wiodącej spacji; w formatach
  liter: 1 (długość litery). Do normalizacji `ll / znaki` (tak liczy `acc_norm` lm-eval).

## Budowa promptów (z kodu `research/wspolne/hipoteza_formatu.py`)

Wszędzie: kontynuacja jest oceniana jako całość, końcowe spacje kontekstu przechodzą do
kontynuacji (jak `_encode_pair` w lm-evaluation-harness), 0-shot o ile nie napisano inaczej.

**Format liter (mc)** — model widzi pytanie i ponumerowane opcje, oceniana jest litera:

    Question: {pytanie}
    A. {opcja A}
    B. {opcja B}
    ...
    Answer:

kontynuacje: `" A"`, `" B"`, … (po jednej literze ze spacją).
- `med_mc`: `Question: {pytanie}\nChoices:\nA. …\nB. …\nC. …\nD. …\nAnswer:`.
- `mmlu_mc`: przed pytaniem nagłówek
  `The following are multiple choice questions (with answers) about {przedmiot}.\n\n`, potem
  `{pytanie}\nA. …\n…\nAnswer:` (bez „Question:”).
- `siqa_mc`: `Question: {kontekst} {pytanie}\nA. …\nB. …\nC. …\nAnswer:` (3 opcje).
- `belebele_mc`: `P: {pasaż}\nQ: {pytanie}\nA: …\nB: …\nC: …\nD: …\nAnswer:` (dwukropek po literze).
- `arc_c_mc_przes`: jak `arc_c_mc`, ale treści opcji przesunięte cyklicznie o jedną pozycję
  (treść z A idzie na B, B na C, …, ostatnia na A); `gold` przesunięty razem z poprawną treścią.
- `arc_c_mc_bezspacji`: jak `arc_c_mc`, kontynuacje `"A"`, `"B"`, … bez spacji.
- `arc_c_mc_5shot`: przed pytaniem 5 przykładów z ARC-Challenge train (losowanie
  `random.Random("1234|5|{id}")`), każdy w tym samym formacie zakończony ` {litera}\n\n`.

**Format treści (cloze)** — model nie widzi opcji, oceniana jest pełna treść odpowiedzi:

    Question: {pytanie}
    Answer:

kontynuacje: `" " + treść opcji`. Dotyczy `arc_c_cloze`, `arc_e_cloze`, `med_cloze`, `mmlu_cloze`.
- `siqa_cloze`: `Q: {kontekst} {pytanie}\nA:` + `" " + treść`.
- `belebele_cloze`: `P: {pasaż}\nQ: {pytanie}\nAnswer:` + `" " + treść`.

**multiblimp** — pusty kontekst, kontynuacje `" " + zdanie` dla zdania poprawnego (indeks 0) i
niepoprawnego (indeks 1); `gold` zawsze 0.

## Jak wygenerować surowe dane od zera

Kod: katalog `research/wspolne/` tego repozytorium; komendy niżej uruchamiasz w `research/`.
Wymagania: Python 3.9+ (lock spisany na 3.9.6), pakiety z `wspolne/requirements.lock.txt` (m.in. torch, datasets
3.6.0, lm_eval 0.4.9.1), dostęp do Hugging Face, kilka GB dysku na modele i zbiory. Działa na CPU
(wolno) albo GPU (`--device cuda`).

    python3 -m venv .venv-eval
    .venv-eval/bin/pip install -r wspolne/requirements.lock.txt
    .venv-eval/bin/python wspolne/pobierz_zbiory.py

Modele pobierz do katalogów lokalnych w podanych rewizjach, np.:

    huggingface-cli download SlayerLab/Slayer1B-1.06 --revision ef81be58742544ad32e1afab38db011fec209609 --local-dir models/slayer-1.06
    huggingface-cli download EleutherAI/pythia-1b --local-dir models/pythia-1b

Liczenie (jeden plik `{zadanie}.jsonl` na zadanie w katalogu `--wyjscie`; przerwane liczenie
wznawia się od brakujących `id`):

    .venv-eval/bin/python wspolne/hipoteza_formatu.py licz --model models/slayer-1.06 \
      --zadania arc_c_mc,arc_c_cloze,arc_c_mc_przes,arc_c_mc_bezspacji,arc_c_mc_5shot,arc_e_mc,arc_e_cloze,med_mc,med_cloze,mmlu_mc,mmlu_cloze,siqa_mc,siqa_cloze,belebele_mc,belebele_cloze,multiblimp \
      --wyjscie moje_wyniki/slayer-1.06 --device cpu --batch 16

    .venv-eval/bin/python wspolne/hipoteza_formatu.py licz --model models/pythia-1b \
      --zadania arc_c_mc,arc_c_cloze,arc_e_mc,arc_e_cloze,med_mc,med_cloze,mmlu_mc,mmlu_cloze,siqa_mc,siqa_cloze,belebele_mc,belebele_cloze,multiblimp \
      --wyjscie moje_wyniki/pythia-1b --device cpu --batch 16

Uwagi: `mmlu` bierze przedmioty z lokalnego cache HF (`~/.cache/huggingface/datasets/cais___mmlu/`),
`multiblimp` wymaga `jumelet/multiblimp` (snapshot `de923efa…`) w cache HF — oba ściąga
`pobierz_zbiory.py`. Wyniki w float mogą różnić się od paczki na ostatnich miejscach po przecinku
zależnie od sprzętu i batcha; porównuj z dokładnością do tolerancji, nie bajt w bajt.
