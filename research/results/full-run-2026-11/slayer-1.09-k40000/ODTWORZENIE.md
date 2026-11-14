# Odtworzenie pomiaru 1.09 krok 40 000 z plików repo

Każdą liczbę z [`RAPORT.md`](RAPORT.md) i [`LICZBY.json`](LICZBY.json) da się przeliczyć z plików tego repo, bez
paczki eksportu i bez karty graficznej. Wyjątek: EWoK czyta szablony z zamkniętego (gated) zbioru
`ewok-core/ewok-core-1.0` na Hugging Face, więc potrzebny jest dostęp do niego (konto HF z akceptacją warunków).

## Co leży gdzie

| plik | zawartość |
|---|---|
| `../<test>/slayer1b-1.09-k40000/` | wynik 1.09 w formacie reszty przebiegu (`results.json`, `results_rozszerzone.json`, `scores-history-wiersz.csv`) i surowe pliki pary jako gzip: `probki/*.jsonl.gz` (próbki per pytanie z lm_eval: logprob każdej odpowiedzi, wybór, poprawna odpowiedź), `trace/*.jsonl.gz`, `podsumowanie.md.gz` |
| `wyniki/<test>/slayer1b-1.08/` | to samo dla 1.08 przeliczonego na tej samej instancji |
| `eksport/` | `manifest.jsonl`, `srodowisko.json`, `czasy.jsonl` z instancji, bez zmian |
| `logi/` | logi każdej pary (gzip) |
| `probki_sha256.json` | sha256 paczki eksportu, każdego pliku eksportu przed kompresją (`pliki`) i każdego pliku gzip w repo (`pliki_gz`) |
| `code/` | kod pomiaru i analizy |

Paczka eksportu `eksport_k109.tgz` (sha256 `6da5db6650220f45c19064ba89614ba18ac43f9f6e0c772462fbf29416ec257e`) leży
poza repo, lokalnie u autora pomiaru. Do odtworzenia nie jest potrzebna: jej pliki są tu,
a `dolacz_wyniki.py odtworz` sprawdza, że po rozpakowaniu mają te same sha256 co w paczce.

## Wersje

- Protokół: commit `dd309c8`, aneks `b99f72a`. Kod analizy (`liczby_109.py`, `raport_md.py`, `przelicz_niezaleznie.py`):
  commit `88719f1`, przed pierwszym wynikiem. Kod na instancji: deklarowany `git archive` commitu `b99f72a`; eksport
  go nie zapisuje (`srodowisko.json` ma puste `fabryka_commit`, archiwum nie ma `.git`). Dowody pośrednie:
  `runner_sha256` w `eksport/manifest.jsonl` równa się sumie `research/common` w `b99f72a`, a suma wag po konwersji to
  wpis `SUMY_WAG_CKPT` dodany w `b99f72a`, bez którego runner odmawia liczenia.
- Instancja: vast.ai, RTX 5090, obraz `pytorch/pytorch:2.8.0-cuda12.9-cudnn9-runtime`, Python 3.11.13, torch 2.8.0+cu129,
  lm_eval 0.4.9.1, transformers 4.57.6, datasets 3.6.0 (środowisko `lock`, `research/common/requirements.lock.txt`),
  float32 z wyłączonym TF32, batch 1, seed domyślny `ewaluuj.py` i `ewok.py`.
- Wagi: 1.09 `SlayerLab/Slayer1B-1.09-checkpoints` @ `cff81fdcc05f0d91e9ba45b09fe78f769d7e0903`, plik `wagi_40000.pt`
  sha256 `f83f7017872f7121f002bc77499c625304bd28e2c87fb4afaa0e3d445bd31881`, po konwersji `model.safetensors` sha256
  `5d60d691f1ea87db4a900788ff253f2de55e75f9210c93e7e95f3b9f6c434591`; 1.08 `SlayerLab/Slayer1B-1.08` @
  `5f854a0cc7160594d54d1788d37a44e8ebabe16c`, sha256 wag `1c510d9a59d3b9e62360d1db57e08fa450fb9b09df849df7f2eef132ea6715a4`.
- Analiza lokalnie (macOS): Python 3.12 z pakietami z `research/common/requirements.lock.txt` i pytest.

## Komendy

Z katalogu `research/`, w venv z pakietami z `common/requirements.lock.txt`. `PRACA` to dowolny katalog roboczy poza repo.

```bash
P=results/full-run-2026-11/slayer-1.09-k40000
# 1. pliki repo -> układ eksportu; kod 0 tylko przy zgodnych sha256 wszystkich 152 plików
python -I $P/code/dolacz_wyniki.py odtworz results/full-run-2026-11 $PRACA/eksport
# 2. manifest przebiegu w stanie, na którym liczono (przed dopisaniem 1.09); sha256 w LICZBY.json, pole wejscia
git show 88719f1:research/results/full-run-2026-11/manifest.jsonl > $PRACA/manifest_przebiegu.jsonl
# 3. LICZBY.json i RAPORT.md (diff z wersją w repo ma być pusty)
python -I $P/code/liczby_109.py $PRACA/eksport $PRACA/manifest_przebiegu.jsonl $P/probki_sha256.json $PRACA/LICZBY.json $P/dodatki.json
python -I $P/code/raport_md.py $PRACA/LICZBY.json $PRACA/RAPORT.md
diff $PRACA/LICZBY.json $P/LICZBY.json && diff $PRACA/RAPORT.md $P/RAPORT.md
# 4. wykresy i README przebiegu
python -I tools/ewaluacja/raport.py results/full-run-2026-11 results/full-run-2026-11 --bez-porownan --odniesienie results/central-run
# 5. raport wobec LICZBY.json: strażnik liczb, zgodność bajt w bajt z generatorem i sekcja 1.09 README (kod 0)
python -I $P/code/sprawdz_raport.py $P/LICZBY.json $P/RAPORT.md --readme results/full-run-2026-11/README.md
# 6. bramka obliczeń: przeliczenie niezależne (sha256 wejść, bez kodu raport.py, metryki.py, statystyka.py; kod 0)
python -I $P/code/przelicz_niezaleznie.py $PRACA/eksport $P/LICZBY.json $PRACA/manifest_przebiegu.jsonl $P/probki_sha256.json $PRACA/przelicz.json
# 7. mutacje kodu liczącego wobec strażników i mutacje kodu kontrolnego wobec testów (kod 0 = każda złapana)
python -I $P/code/mutacje.py $PRACA/eksport $PRACA/manifest_przebiegu.jsonl $P/probki_sha256.json $P/LICZBY.json $P/RAPORT.md $PRACA/mutacje $PRACA/mutacje.json
python -I $P/code/mutacje_testow.py python $PRACA/mutacje_testow.json
# 8. testy pomiaru (atrapy i dane rzeczywiste z repo)
python -m pytest -q tests/test_slayer_109_k40000.py
```

Wyniki kroków 6 i 7 z tego pomiaru: [`przelicz_niezaleznie.json`](przelicz_niezaleznie.json),
[`mutacje.json`](mutacje.json), [`mutacje_testow.json`](mutacje_testow.json).

Jedną parę od zera (z wagami, na karcie) liczy komenda z pola `komenda` wiersza w `eksport/manifest.jsonl`, a całą
kolejkę `code/kolejka.sh` (na instancji przez `code/start_zdalny.sh`).
