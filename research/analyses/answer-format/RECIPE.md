# Analiza formatu odpowiedzi: przepis

Wszystkie komendy uruchamiasz w `research/`. Surowych plików per pytanie (`<model>/<task>.jsonl`) **nie ma** w
repo; jest tylko zbiorczy `results/raport_formatu.json`. Kto chce odtworzyć raport, najpierw generuje surowe
pliki (komendy niżej), potem uruchamia analizę.

## Wspólne dla wszystkich wyników

| pole | wartość |
|---|---|
| commit kodu przebiegów | nie zapisany. Surowe pliki i `raport_formatu.json` weszły do repo w `626449d` (2026-10-30, kod był wtedy w `slayer-1b/slayer_eval/`); scorer z tego commitu to najbliższy zapisany stan |
| obecny kod | `common/hipoteza_formatu.py` (scorer), `common/slayer_model.py` (forward Slayera), `analyses/answer-format/analiza_formatu.py` (testy T0-T5), przeniesione tu w `a9e8410` |
| zmiany kodu od przebiegów | `hipoteza_formatu.py` teraz odrzuca wejścia dłuższe niż kontekst modelu (`<task>.odrzucone.jsonl`) zamiast przycinać je z lewej i używa BOS (inaczej EOS) jako tokenu pustego kontekstu dla modeli HF (wcześniej EOS; dla Pythii i Qwena to ten sam token). Prompty i reguły wyboru bez zmian. Po tych zmianach nie liczono ponownie |
| raport wygenerowany | `raport_formatu.json` ostatnio zmieniony w `3ed788c` (2026-10-31; tylko blok `slayer_wikitext_kontrola`) |
| środowisko | `common/requirements.lock.txt` (Python `3.9.6` według `slayer-1b/paczka_testerzy/INSTRUKCJA.md`) |
| biblioteki | `transformers==4.57.6`, `torch==2.8.0`, `datasets==3.6.0`, `lm_eval==0.4.9.1` (tylko kodowanie), `scipy==1.13.1` (testy T1-T5); transformers z PyPI, bez commitu z gita |
| zbiory | `allenai/ai2_arc` @ `210d026faf9955653af8916fad021475a3f00453`; `openlifescienceai/medmcqa` @ `91c6572c454088bf71b679ad90aa8dffcd0d5868`; `allenai/social_i_qa` @ `refs/convert/parquet` (nieprzypięty); `facebook/belebele` `pol_Latn` (nieprzypięty); `cais/mmlu` (nieprzypięty, przedmioty z lokalnego cache HF); `jumelet/multiblimp` @ `de923efa8d2483d6b13364ee68e65308e990a991` `pol/data.tsv`. Pobieranie: `common/pobierz_zbiory.py` |
| seed | brak losowania w zadaniach 0-shot; przykłady few-shot losowane `random.Random("1234|5|{id}")` (`arc_c_mc_5shot`) i `random.Random("1234|{id}")` (`arc_c_cloze_25shot`) |
| precyzja | float32 (modele HF: `torch_dtype=torch.float32`; Slayer: domyślne `dtype=torch.float32` w `slayer_model.py`) |
| sprzęt | nie zapisany (scorer obsługuje `cpu`, `mps`, `cuda`; `INSTRUKCJA.md` mówi, że liczby mogą różnić się na ostatnich miejscach zależnie od sprzętu i batcha) |
| batch | 16 (domyślny; komendy w `INSTRUKCJA.md` podają `--batch 16`) |
| data | przebiegi najpóźniej 2026-10-30 (data commitu `626449d`); dokładna data nie zapisana |

## Slayer 1.06

- Model: `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`
- Komenda:

```bash
huggingface-cli download SlayerLab/Slayer1B-1.06 --revision ef81be58742544ad32e1afab38db011fec209609 --local-dir models/slayer-1.06
.venv-eval/bin/python common/hipoteza_formatu.py licz --model models/slayer-1.06 \
  --zadania arc_c_mc,arc_c_cloze,arc_c_mc_przes,arc_c_mc_bezspacji,arc_c_mc_5shot,arc_e_mc,arc_e_cloze,med_mc,med_cloze,mmlu_mc,mmlu_cloze,siqa_mc,siqa_cloze,belebele_mc,belebele_cloze,multiblimp \
  --wyjscie analyses/answer-format/results/1.06 --device cpu --batch 16
```

## Slayer 1.03 i Slayer 1.00 (T5 i porównanie wersji)

- Modele: `SlayerLab/Slayer1B-1.03` i `SlayerLab/Slayer1B-1.00`; rewizja użyta w tej analizie nie zapisana.
  Rewizje zapisane gdzie indziej w repo: `fee113efcad47f48dd0b80aa37952434f00bed43` dla Slayer 1.03
  (`slayer-1b/wygaszanie/wyniki/pobrane.json`); `43e7ca20` (prefiks) dla Slayer 1.00 (`benchmarks/ewok-pl/README.md`).
- Komenda (taka sama dla obu, etykieta `1.03` / `1.00`):

```bash
.venv-eval/bin/python common/hipoteza_formatu.py licz --model models/slayer-1.03 \
  --zadania arc_c_mc,arc_c_cloze --wyjscie analyses/answer-format/results/1.03 --device cpu --batch 16
```

## Pythia-1B

- Model: `EleutherAI/pythia-1b` @ `f73d7dcc545c8bd326d8559c8ef84ffe92fea6b2` (rewizja z `research/README.md`;
  komenda w `INSTRUKCJA.md` pobiera bez `--revision`, więc faktycznie użyta rewizja nie jest zapisana)
- Komenda:

```bash
huggingface-cli download EleutherAI/pythia-1b --revision f73d7dcc545c8bd326d8559c8ef84ffe92fea6b2 --local-dir models/pythia-1b
.venv-eval/bin/python common/hipoteza_formatu.py licz --model models/pythia-1b \
  --zadania arc_c_mc,arc_c_cloze,arc_e_mc,arc_e_cloze,med_mc,med_cloze,mmlu_mc,mmlu_cloze,siqa_mc,siqa_cloze,belebele_mc,belebele_cloze,multiblimp \
  --wyjscie analyses/answer-format/results/pythia-1b --device cpu --batch 16
```

## `Qwen2.5-0.5B` (tylko T0)

- Model: etykieta `Qwen2.5-0.5B`; repo na Hubie i rewizja nie zapisane.
- Komenda: nie zapisana. Obecnym kodem byłoby to `licz --zadania arc_c_cloze,arc_e_cloze,arc_c_cloze_25shot
  --wyjscie analyses/answer-format/results/Qwen2.5-0.5B` (trzy pliki, które raport czyta dla tej etykiety).

## Analiza (wszystkie modele)

```bash
.venv-eval/bin/python analyses/answer-format/analiza_formatu.py --wyniki analyses/answer-format/results
```

Czyta `<results>/<etykieta>/<task>.jsonl` dla etykiet `1.06`, `1.03`, `1.00`, `pythia-1b`, `Qwen2.5-0.5B` i zapisuje
`results/raport_formatu.json`. Blok `slayer_wikitext_kontrola` wymaga `results/1.06/wikitext.json` z
`common/hipoteza_formatu.py wikitext` (opis w `benchmarks/wikitext-2/`). Po zmianie raportu
`tools/liczby.py` generuje na nowo `results/LICZBY.json`.
