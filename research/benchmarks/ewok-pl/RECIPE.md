# EWoK-PL: przepis

Każdy wynik w `results/raport_ewok.json` ma tu wpis. Komendy uruchamiasz w `research/`. Czego nie zapisano, ma
dopisek „niezapisane”.

## Wspólne dla wszystkich wyników

- Commit kodu: `main` @ `0e787f6001ac70431ef378dd3f2324b2e1cf7270` plus kod z PR #93 (`research/ewok`, reguła autorów w
  `benchmarks/ewok/ewok.py`) i PR #76 (`research/ewok-pl`). Hash z gałęzi roboczej znika po spłaszczeniu historii.
  - Wyniki w `results/raport_ewok.json` (wersja 5) liczy `ewok.py licz` z domyślną `--regula autorow`, która woła
    `benchmarks/ewok/ewok.py` (`build_model(rule="authors")`, `score`). Przebiegi z 2026-11-03.
  - EN pełny dla `Slayer1B-1.06`, `Bielik-1.5B-v3` i `LFM3-1.7B-Base` to kopie plików z
    `benchmarks/ewok/results/<model>/ewok.jsonl` (`benchmarks/ewok/ewok.py score --batch 8`), czyli ta sama reguła i
    ten sam kod.
  - `results/raport_ewok_bos.json` (wersja 4) liczył tryb `--regula bos`, wcześniejszym kodem z PR #76 @ `dfa28ec`,
    przebiegi z 2026-10-30 i 2026-11-02, `--batch 32`.
- Środowisko: **nie** `common/requirements.lock.txt`. Python 3.12.2, `torch 2.10.0+cu130`,
  `transformers 5.19.0`, `tokenizers 0.23.3`, `numpy 2.5.3` (lokalne `.venv-gpu`). lm-eval nie jest używany:
  scorer reguły autorów to `authors_pair` i `logliks` z `benchmarks/ewok/ewok.py`; tryb `bos` używa `para` i `licz_logliki` z `common/hipoteza_formatu.py`. Przebieg w środowisku z locka: niezapisane. Pełnego środowiska przebiegu wersji 5 (lista pakietów `.venv-gpu`) nie zapisano, znane są tylko wersje podane wyżej.
- Zbiory:
  - EN: `ewok-core/ewok-core-1.0` @ `34d912a608066c92e2990a0328ffc3bd9a716042`, plik
    `data/test/ewok-core-1.0.parquet`, 4374 rekordy (repo z bramką zgody na HF);
  - PL: `ewok-pl-complete-0001-0625.zip`, sha256
    `f5c5a83c57f714265478606e6f1e236bc1f4d16c335505b64eae0af7e3e94f41`, plik
    `ewok_pl_combined/ewok-pl-0001-0625.jsonl`, 625 rekordów (zip poza repo, hasło z TERMS_OF_USE EWoK).
- Seed: forward deterministyczny, bez próbkowania i bez przykładów w prompcie. Bootstrap i testy permutacyjne w
  `analiza`: seed 20261028, 10 000 powtórzeń (`metryki.SEED`, `metryki.POWTORZENIA`).
- Precyzja: float32 dla wszystkich modeli (wagi ładowane z `dtype=torch.float32`; Slayer natywnie fp32).
- Sprzęt: 1× NVIDIA GeForce RTX 5060 Ti 16 GB, `--device cuda`, `--batch 8` (wersja 5; modele po kolei, jeden proces naraz).
- Raport: `python benchmarks/ewok-pl/ewok.py analiza --wyniki benchmarks/ewok-pl/results --zip ewok-pl-complete-0001-0625.zip`
  (2026-11-03), wynik w `results/raport_ewok.json` i `results/raport_ewok.md`.

Komenda dla jednego modelu (`<model>` i `<katalog>` z tabeli niżej):

```bash
python benchmarks/ewok-pl/ewok.py licz --model <katalog> --dane pl,en --zip ewok-pl-complete-0001-0625.zip --batch 8 --wyjscie benchmarks/ewok-pl/results/<model>
```

## Wyniki

| `<model>` (klucz w `raport_ewok.json` → `modele`) | model HF @ rewizja | `<katalog>` (pobrany z HF) | data (wersja 4 / 5) |
|---|---|---|---|
| `Slayer1B-1.00` | `SlayerLab/Slayer1B-1.00` @ `43e7ca2022dbd96a1bd0ed448f1ebb78209dbbfc` | cały snapshot | 2026-10-30 / 2026-11-03 |
| `Slayer1B-1.01` | `SlayerLab/Slayer1B-1.01` @ `727b5f5ea4598e685af98d7aac2f3d4aad7f72d5` | cały snapshot | 2026-10-30 / 2026-11-03 |
| `Slayer1B-1.02` | `SlayerLab/Slayer1B-1.02` @ `bf7117b97417b22c6a76710a91038724f2be927d` | cały snapshot | 2026-10-30 / 2026-11-03 |
| `Slayer1B-1.03` | `SlayerLab/Slayer1B-1.03` @ `fee113efcad47f48dd0b80aa37952434f00bed43` | cały snapshot | 2026-10-30 / 2026-11-03 |
| `Slayer1B-1.04` | `SlayerLab/Slayer1B-1.04` @ `09aa8abf19e8a6edc00615e739c949578b6b1021` | cały snapshot | 2026-10-30 / 2026-11-03 |
| `Slayer1B-1.05` | `SlayerLab/Slayer1B-1.05` @ `21a05bc59932b54ac90da995e3ffb994c427ae16` | cały snapshot | 2026-10-30 / 2026-11-03 |
| `Slayer1B-1.06` (mierzony model) | `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609` | cały snapshot | 2026-10-30 / 2026-11-03 |
| `Bielik-1.5B-v3` (kontrola: model, który zna polski) | `speakleash/Bielik-1.5B-v3` @ `4b25049621bf3952a1fc9314c89773102eda0333` | cały snapshot | 2026-10-30 / 2026-11-03 |
| `LFM3-1.7B-Base` | `LiquidAI/LFM3-1.7B-Base` @ `545fc8f4c7b5fa9f405105274cd29c4f8f44b526` | cały snapshot, `trust_remote_code` | 2026-10-30 / 2026-11-03 |
| `Aster-0.5B(fp32)` | `OrisTeam/Aster-0.5B` @ `97691358f355c9d3f57e5b1a8b31eb79d5c53f2f` | podkatalog `fp32/`, `trust_remote_code` | 2026-11-02 / 2026-11-03 |

Klucze wyników każdego modelu: `modele/<model>/pl` (625 rekordów PL), `modele/<model>/en` (4374 rekordy EN) i
`modele/<model>/en625` (pierwsze 625 rekordów EN, te same `source_id` co PL), każdy z `ewok`, `ewok_po_szablonach`
(n, SE, CI95) i rozbiciami `wg_*`.

## Kontrola: model, który zna polski

Bielik-1.5B-v3 na EWoK-PL ma wynik wyraźnie powyżej bazy losowej 50%: `modele/Bielik-1.5B-v3/pl/ewok` i
`ewok_po_szablonach` w `raport_ewok.json` (różnica od bazy ponad 2 SE po szablonach). Warunek kontroli z
sekcji „Benchmark bez oryginału” w `METODOLOGIA.md` jest więc spełniony. Etapy A–C (karta oryginału EWoK,
odtworzenie wyniku gpt2-xl z pracy, test zgodności kodu) są w `../ewok/`, a przepis tych przebiegów w
`../ewok/RECIPE.md`. Wyniki wersji 5 liczy reguła autorów. Wersja 4 (`raport_ewok_bos.json`) dawała BOS przed
kontekstem każdemu modelowi (`POLISH.md`, D2 i D3).
