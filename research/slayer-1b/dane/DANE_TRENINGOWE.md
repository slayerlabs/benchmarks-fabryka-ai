# Dane treningowe Slayera 1B, wersje 1.00–1.09

<a href="https://huggingface.co/spaces/SlayerLab/Slayer1B/tree/3f2adb00d5db043a879ca7a0847c0220a5a42543"><img src="../../../docs/img/dane/space-slayer1b.svg" alt="Space Slayer1B" height="36"></a>
<a href="https://huggingface.co/SlayerLab/Slayer1B-1.08/blob/ea0945b11153e67517b70d21192e6076d161f658/DATA_CARD.md"><img src="../../../docs/img/dane/karta-108.svg" alt="Karta danych 1.08" height="36"></a>
<a href="https://huggingface.co/SlayerLab/Slayer1B-1.09/blob/b25aec4ef6fb0c13717c5e5e27a426c572df54c6/DATA_CARD.md"><img src="../../../docs/img/dane/karta-109.svg" alt="Karta danych 1.09" height="36"></a>
<a href="REJESTR_DATASETOW.md"><img src="../../../docs/img/dane/rejestr.svg" alt="Rejestr zbiorów" height="36"></a>
<a href="METODOLOGIA.md"><img src="../../../docs/img/dane/metodologia-zbioru.svg" alt="Metodologia zbioru" height="36"></a>

Na czym trenowano każdą wersję Slayera 1B i jakie zbiory doszły później. Wersje 1.00–1.06 odczytano 2026-11-04,
1.07–1.09 i tokeny wersji ze [Space][space] 2026-11-14. Licencje składników `slayer-pl-8x3b`:
[`REJESTR_DATASETOW.md`](REJESTR_DATASETOW.md), sekcja 1.

Nowy zbiór budujesz według [`METODOLOGIA.md`](METODOLOGIA.md). Chwilowo trafia do Twojego repo na Hugging Face do wglądu Arka (metodologia, sekcja 4), docelowo do [`SlayerLab/dataset-team-submissions`][subm].

## Tokeny wersji

Tokeny tokenizera Slayera od kroku 1 do końca wersji, z wcześniejszymi wersjami ([`releases.json`][releases]).

| wersja | tokeny |
|---|---:|
| 1.00 | 1 499 463 680 |
| 1.01 | 2 998 927 360 |
| 1.02 | 5 997 854 720 |
| 1.03 | 7 497 318 400 |
| 1.04 | 10 496 245 760 |
| 1.05 | 13 495 173 120 |
| 1.06 | 14 520 680 448 |
| 1.07 | 23 411 556 352 |
| 1.08 | 25 203 572 736 |
| 1.09 (krok 35 000) | 61 903 732 736 |

## Wersje 1.07–1.09

| wersja | start | zbiór | rewizja | licencja | tokeny | źródło |
|---|---|---|---|---|---:|---|
| 1.07 | 1.06, krok 13848 | [`SlayerLab/slayer-1.07-pretrain`][d107]: `pl_web` (HPLT v3 PL, pliki nieużyte w 1.06), `pl_replay_A`, `pl_replay_B` (replay `core` i `legal` z 1.06), `en_mix`, `en_fineweb_edu` | `6a337bbf` | ODC-By (FineWeb-Edu, FineMath, open-web-math), CC BY (DCLM), CC0 kompilacji HPLT | 8 891 005 707 | [karta zbioru][d107], [DATA_CARD 1.08][dc108] |
| 1.07 | | ↳ `en_mix`: FineWeb-Edu, FineMath, open-web-math, DCLM-baseline z [`SlayerLab/minimal-en-corpus-5b`][min5b] | `bb3aec23` | jak wyżej | 1 650 618 814 | [karta zbioru][d107], [Space][space] |
| 1.07 | | ↳ `en_fineweb_edu`: [FineWeb-Edu][fwe107] `sample/10BT` | `87f09149` | ODC-By | 2 235 660 025 | [karta zbioru][d107] |
| 1.08 | 1.07 @ [`a090b54e`][m107rev], nowy optymalizator | [`SlayerLab/slayer-pl-logika-2b`][logika] | `e24c8b71` | według źródła: ODC-By (FinePDFs), CC BY 4.0 (Dolci), licencje DOAB per książka | 1 911 918 958 z EOS | [DATA_CARD 1.08][dc108] |
| 1.08 | | [`SlayerLab/english-technical-1b`][entech] | `3b833d36` | per wiersz: MIT, Apache-2.0, BSD-3-Clause, CC0-1.0 | 899 001 323 (train) | [DATA_CARD 1.08][dc108] |
| 1.08 | | replay [`slayer-1.07-pretrain`][d107]: `pl_web` / `en_fineweb_edu` / `en_mix` | `6a337bbf` | jak 1.07 | 435 000 183 / 220 000 324 / 220 000 212 | [DATA_CARD 1.08][dc108] |
| 1.09 | kontynuacja 1.08 | [`SlayerLab/gollem-corpus-16b-pl`][gollem]: segmenty c01, c02, c06 (PL) | `17f9d37a` | CC0-1.0 opakowania HPLT, prawa tekstów osobno | 1 069 547 741 pozycji (c01) | [DATA_CARD 1.09][dc109] |
| 1.09 | | [`HuggingFaceFW/finepdfs-edu`][fpe]: segmenty c03–c06 (PL) | `9cfabe21` | ODC-By | — | [DATA_CARD 1.09][dc109] |
| 1.09 | | [`HuggingFaceFW/fineweb-edu`][fwe]: segmenty c01–c06 (EN) | brak w karcie | ODC-By | 4 278 190 159 pozycji (c01) | [DATA_CARD 1.09][dc109] |
| 1.08b (eksperyment, niewydany) | 1.07, krok 22327 | [`SlayerLab/slayer-1.08b-pretrain`][d108b]: OpenR1-Math-220k, OpenThoughts-114k, Bespoke-Stratos-17k, SYNTHETIC-1, self-oss-instruct, OpenCodeReasoning, ProofWriter i replay PL z 1.07 | `0b5a12b7` | dane niepublikowane | 782 469 318 na ramię | [karta zbioru][d108b] |

Proporcje języków: 1.00–1.06 ok. 82% PL / 18% EN; 1.07 56,3% PL / 43,7% EN; nowe wejście 1.09 najpierw 20% PL / 80% EN, od 12.11.2026 cel 30% PL / 70% EN ([Space, sekcja Data][space]). <!-- liczba-spoza-wynikow: proporcje języków ze Space SlayerLab/Slayer1B -->

Karta 1.09 nie podaje źródeł segmentów c07–c10 ani s01–s03.

## Dopisane później

Status: `w budowie` (rezerwacja na [tablicy Dataset team](https://github.com/orgs/slayerlabs/projects/11)) → `u Arka do wglądu` (repo autora na Hugging Face) → `opublikowany`.

| data | zbiór | kto | rezerwacja | status |
|---|---|---|---|---|
| 2026-11-20 | `finepdfs-technika-pl`: FinePDFs pol_Latn wybrane adnotacjami propella, technika (energetyka, elektronika, sprzęt IT, przemysł) | DarioRSL | [polish-dynaword-v2#145](https://github.com/slayerlabs/polish-dynaword-v2/issues/145) | w budowie |
| 2026-11-14 | [DCLM-baseline 1.0 EN][dclm] | LoIlita | [#197](https://github.com/slayerlabs/benchmarks-fabryka-ai/issues/197) | w budowie |
| 2026-11-14 | [`SlayerLab/hutnictwo-gornictwo-spawalnictwo-preview`][hgs] | SlayerLab | bez rezerwacji | opublikowany |
| 2026-11-09 | [`SlayerLab/polish-dynaword-pretraining-mix`][pdpm] | SlayerLab | bez rezerwacji | opublikowany |
| 2026-11-08 | [`SlayerLab/technika-i-nauka`][tin] | SlayerLab | bez rezerwacji | opublikowany |

## Wersje 1.00–1.06: wspólne

- **Zbiór.** Wersje 1.00–1.06 trenowano na jednym zbiorze, `slayer-pl-8x3b` @ `d50df04` (pole `datasets` we
  wszystkich kartach). Model trenowano od zera (tag `from-scratch`).
- **Przebieg.** Jest jeden przebieg po korpusie. Każde okno 4096 tokenów trafia do treningu najwyżej raz, a pakiety
  idą po kolei: pack-00, pack-01 i dalej ([karta 1.02][m102], [karta 1.06][m106]). Krok to 1 048 576 tokenów
  tokenizera Slayera (BPE, 32 768 tokenów), nie tokenów cl100k.
- **Gałęzie boczne.** Kroki 1051–1430 wersji 1.00 i kroki 2251–2860 wersji 1.01 to gałęzie z wygaszaniem LR. Następna
  wersja startuje z wcześniejszego checkpointu, ale dostaje te same batche ([karta 1.01][m101], „Resume check”;
  [checkpointy 1.02][c102], „batches up to step 3594 are identical”). Gałęzie różnią się więc LR, a dane mają te same.
- **Skład pakietu.** Pakiet to własny, rozłączny wycinek `web` (HPLT v3 PL) i część plików `shared/`. W treningu
  `core` i `core_sa` tworzą jedną pulę „rdzeń”, `legal` i `legal_sa` jedną pulę „legal”, a `en` jest osobno. Dokumenty
  wspólne każdego pakietu losuje się z przedziału hasha rozłącznego z wcześniejszymi pakietami ([karta 1.01][m101],
  [karta 1.02][m102]), więc wspólny dokument trafia najwyżej do jednego pakietu.
- **Wagi próbkowania** (w tokenach cl100k): web 0,63, rdzeń 0,19, legal 0,08, en 0,10 ([`pack-04/manifest.json`][pack04], [karta 1.00][m100]). <!-- liczba-spoza-wynikow: wagi_probkowania z pack-XX/manifest.json -->
- **Ile części wspólnych bierze pakiet.** pack-00 i pack-01 biorą po 15,4% puli rdzenia, 12,0% puli legal i 12,5% `en` (pole `frakcje` w [`run/wsad_p01_manifest.json`][wsad]). <!-- liczba-spoza-wynikow: frakcje z run/wsad_v2_manifest.json i run/wsad_p01_manifest.json, Slayer1B-1.01-checkpoints -->
- **Walidacja.** Z każdego pakietu odłożono 0,1% dokumentów PL i 0,5% dokumentów EN (`val_pl_frac`, `val_en_frac` w [manifeście strumienia][wsad]). Te dokumenty nie weszły do treningu. <!-- liczba-spoza-wynikow: val_pl_frac, val_en_frac z run/wsad_p01_manifest.json -->
- **Dekontaminacja w zbiorze** obejmuje wszystkie wersje, ale tylko warstwę `web`. Zrobiono ją po hashach wobec 8tags,
  PolEmo2 i własnego held-out zbioru i usunięto 10 541 dokumentów ([`dataset.json`][dsjson], `higiena`). `core`,
  `legal` i `en` nie przeszły dekontaminacji w zbiorze. Deduplikacji near-dup w `web` nie zrobiono ([karta zbioru][zbior-readme]).
- **`en`** w `slayer-pl-8x3b` to tylko `fineweb-edu`. `dataset.json` wymienia też finemath, ale w danych go nie ma
  (REJESTR, 1.2). FineMath weszło dopiero w 1.07, w `en_mix` ([karta zbioru][d107]).
- **Proporcje języków** 1.00–1.06: ok. 82% PL / 18% EN w tokenach Slayera ([Space, sekcja Data][space]); wagi
  cl100k wyżej dają 10% EN, bo cl100k dzieli angielski na mniej kawałków. <!-- liczba-spoza-wynikow: proporcje ze Space i z pack-XX/manifest.json -->
- **Dane osobowe** maskowano regułami przed tokenizacją: e-mail, telefon, PESEL, NIP, REGON, dowód. Maskowanie nie
  daje gwarancji, że usunięto wszystko ([karta 1.00][m100], karty 1.01–1.03).

## Wersje 1.00–1.06

Kolumna „tokeny” podaje tokeny tokenizera Slayera od kroku 1 do końca wersji. Proporcje to udział tokenów tokenizera
Slayera w `train.bin` pakietu, w kolejności web / rdzeń / legal / en. Liczy się je inaczej niż wagi cl100k, bo
tokenizer dzieli angielski na więcej kawałków.

| wersja | start | kroki tej wersji | tokeny (do końca wersji) | pakiety, kroki | proporcje | dekontaminacja poza zbiorem | inne dane | źródło |
|---|---|---|---:|---|---|---|---|---|
| 1.00 | od zera | 1–1430 | 1 499 463 680 | pack-00 (1–1430) | pack-00: 51,79 / 22,19 / 8,46 / 17,56 | brak | brak w karcie | [karta][m100], [ckpt][c100] <!-- liczba-spoza-wynikow: udzial_v6 z run/wsad_v2_manifest.json, karta 1.01 --> |
| 1.01 | 1.00 `ckpt_1050` | 1051–2860 | 2 998 927 360 | pack-00 (1–1801), pack-01 (1802–2860) | pack-01: 52,16 / 22,14 / 8,20 / 17,49 | brak; 13-gramy pack-01 sprawdzono wobec testów, niczego nie usunięto | brak w karcie | [karta][m101], [ckpt][c101] <!-- liczba-spoza-wynikow: karta 1.01, Training data --> |
| 1.02 | 1.01 `ckpt_2250` | 2251–5720 | 5 997 854 720 | pack-00 (1–1801), pack-01 (1802–3594), pack-02 (3595–5389), pack-03 (5390–5720) | pack-02: 52,09 / 21,63 / 8,66 / 17,62; pack-03: 51,68 / 22,27 / 8,59 / 17,46 | brak; 13-gramów pack-02 i pack-03 nie sprawdzano | brak w karcie | [karta][m102], [ckpt][c102] <!-- liczba-spoza-wynikow: karta 1.02, Training data --> |
| 1.03 | 1.02 `ckpt_5720` | 5721–7150 | 7 497 318 400 | jak 1.02, pack-03 do kroku 7150 | jak 1.02 | brak | brak w karcie | [karta][m103], [ckpt][c103] |
| 1.04 | 1.03 `ckpt_7150` | 7151–10010 | 10 496 245 760 | reszta pack-03 (7151–7192), pack-04 (7193–8990), pack-05 (od 8991) | pack-04 i pack-05: nieustalone | od kroku 7193 wyłączono 5133 dokumenty z trafieniami n-gramów BoolQ, MMLU i ARC (lista sha256 `84caed78…`); kroki do 7192 trenowano na danych bez tego filtra | brak w karcie | [karta][m104], [ckpt][c104] |
| 1.05 | 1.04 `ckpt_10010` | 10011–12870 | 13 495 173 120 | dalszy ciąg przebiegu; granice pakietów nieustalone | nieustalone | jak 1.04, cały odcinek z filtrem | brak w karcie | [karta][m105], [ckpt][c105] |
| 1.06 | 1.05 `ckpt_12870` | 12871–13848 | 14 520 680 448 | koniec przebiegu po korpusie; notatka przebiegu 7150–13848 podaje pakiety 4–7 | nieustalone | jak 1.04, cały odcinek z filtrem | brak w karcie | [karta][m106], [ckpt][c106], [notatka][track] |

## Nieustalone i gdzie szukano

- **Granice pack-05, pack-06 i pack-07 w krokach 8991–13848 oraz to, czy pack-07 wszedł w całości.** Sprawdzono karty
  modeli i checkpointów 1.04–1.06, notatkę `public_note` i `config` przebiegu [`f056bb5c`][track] (API trackera) oraz
  [`CHECKPOINTS.md`](../../benchmarks/blimp/results/CHECKPOINTS.md) BLiMP. Repozytoria checkpointów 1.03–1.06 nie
  mają katalogu `run/` z manifestami strumieni, a 1.01 i 1.02 go mają.
- **Proporcje komponentów w pack-04 … pack-07.** Szukano w tych samych miejscach.
- **Podział rdzenia na `core` i `core_sa` w treningu.** Manifest strumienia łączy oba pliki w jedną pulę: 8 579 260
  wierszy rdzenia to `core` plus `core_sa`. Osobnego udziału manifest nie podaje.
- **Korpus, na którym wytrenowano tokenizer.** Karta 1.00 mówi tylko, że tokenizer „is trained on Polish”. Karty
  1.01–1.06 tego nie opisują.
- **Maskowanie danych osobowych w 1.04–1.06.** Karty tych wersji o nim nie piszą.

## Znane przecieki testów do danych

Space skanuje cały korpus treningowy względem każdego testu: 13-gramy słów w polach od 13 słów i dokładne
dopasowanie pól 3–12 słów ([METHOD.md, §6][space-method]). Liczby pochodzą z panelu 200 pytań dla Slayera 1.06
([`results.json`][space-results]). Trafienie oznacza wspólny tekst z danymi, a nie zmierzony stopień kontaminacji.
Wspólne dokumenty są rozłożone po pakietach według hasha, więc bez listy trafionych dokumentów nie wiadomo, która
wersja widziała które z nich.

| test | co wiadomo | źródło |
|---|---|---|
| PolQA (T30) | `polqa` leży w `core_sa`. Trafienie ma 193 z 200 pytań, w polach z odpowiedzią tylko 1 (trafienia głównie w pasażach z Wikipedii) | [`results.json`][space-results]; [REJESTR, sekcja 1](REJESTR_DATASETOW.md#1-slayer-1b--slayerlabslayer-pl-8x3b) |
| PoQuAD (T31) | `poquad` leży w `core`. Trafienie ma 200 z 200 pytań, w polach z odpowiedzią 42 | [`results.json`][space-results]; REJESTR, 1.2 |
| MultiBLiMP PL (T04) | Trafienie ma 16 z 200 zdań. W 1.01 10 z 3272 zdań miało co najmniej połowę 13-gramów w pack-01. Zdania krótsze niż 13 słów nie dają 13-gramów. Podejrzenie: zdania z publicznych drzew UD są w danych | [karta 1.01][m101]; [`results.json`][space-results]; [#36][i36]; [README](../../benchmarks/multiblimp-pl/README.md) |
| BoolQ, MMLU, ARC | Skan przecieków znalazł w `shared/en` 1428, 1429 i 1345 dokumentów. Od kroku 7193 wyłączono 5133 dokumenty, więc 1.00–1.03 i kroki do 7192 trenowano bez tego filtra. Na panelu Space trafienie ma BoolQ 37 z 200 (w polach z odpowiedzią 0), MMLU 6 z 200, ARC-Challenge 4 z 200 | [karta 1.03][m103]; [`results.json`][space-results]; pełne splity liczy [#36][i36] |
| WikiText-2 (T03) | Trafienie ma 21 z 62 dokumentów. W 1.01 26 z 62 dokumentów miało co najmniej jeden wspólny 13-gram z pack-01 | [karta 1.01][m101]; [`results.json`][space-results] |
| DYK (T25), WiC (T13), PPC (T26) | Trafienie ma 160, 75 i 56 z 200 pytań | [`results.json`][space-results] |

[zbior]: https://huggingface.co/datasets/SlayerLab/slayer-pl-8x3b/tree/d50df04a6ad46876fa559a87cca5d3e2a96e7098
[zbior-readme]: https://huggingface.co/datasets/SlayerLab/slayer-pl-8x3b/blob/d50df04a6ad46876fa559a87cca5d3e2a96e7098/README.md
[dsjson]: https://huggingface.co/datasets/SlayerLab/slayer-pl-8x3b/blob/d50df04a6ad46876fa559a87cca5d3e2a96e7098/dataset.json
[pack04]: https://huggingface.co/datasets/SlayerLab/slayer-pl-8x3b/blob/d50df04a6ad46876fa559a87cca5d3e2a96e7098/pack-04/manifest.json
[wsad]: https://huggingface.co/SlayerLab/Slayer1B-1.01-checkpoints/blob/fd7e55d177c162b3d8f6677d833a34e05afe7275/run/wsad_p01_manifest.json
[track]: https://track.fabryka.ai/run/f056bb5c-f1da-56d5-9776-cc33063f10a5
[m100]: https://huggingface.co/SlayerLab/Slayer1B-1.00/blob/43e7ca2022dbd96a1bd0ed448f1ebb78209dbbfc/README.md
[m101]: https://huggingface.co/SlayerLab/Slayer1B-1.01/blob/727b5f5ea4598e685af98d7aac2f3d4aad7f72d5/README.md
[m102]: https://huggingface.co/SlayerLab/Slayer1B-1.02/blob/bf7117b97417b22c6a76710a91038724f2be927d/README.md
[m103]: https://huggingface.co/SlayerLab/Slayer1B-1.03/blob/fee113efcad47f48dd0b80aa37952434f00bed43/README.md
[m104]: https://huggingface.co/SlayerLab/Slayer1B-1.04/blob/09aa8abf19e8a6edc00615e739c949578b6b1021/README.md
[m105]: https://huggingface.co/SlayerLab/Slayer1B-1.05/blob/21a05bc59932b54ac90da995e3ffb994c427ae16/README.md
[m106]: https://huggingface.co/SlayerLab/Slayer1B-1.06/blob/ef81be58742544ad32e1afab38db011fec209609/README.md
[c100]: https://huggingface.co/SlayerLab/Slayer1B-1.00-checkpoints/blob/950a62a9d30b522c65bd76931157cef7929f3113/README.md
[c101]: https://huggingface.co/SlayerLab/Slayer1B-1.01-checkpoints/blob/fd7e55d177c162b3d8f6677d833a34e05afe7275/README.md
[c102]: https://huggingface.co/SlayerLab/Slayer1B-1.02-checkpoints/blob/177fe19f9b6583713be0590d06fd4eeba802b8af/README.md
[c103]: https://huggingface.co/SlayerLab/Slayer1B-1.03-checkpoints/blob/b8ac4d483204b6d00acade3af2d8bfec95f84bce/README.md
[c104]: https://huggingface.co/SlayerLab/Slayer1B-1.04-checkpoints/blob/14b5a8ccb60ac79570593e3410124c7edb879780/README.md
[c105]: https://huggingface.co/SlayerLab/Slayer1B-1.05-checkpoints/blob/085ef34e49d317c6b59ec161193f2bf09ee79f9d/README.md
[c106]: https://huggingface.co/SlayerLab/Slayer1B-1.06-checkpoints/blob/1113e3e657c1e82d0da09c1fb6d08a356edb8aa3/README.md
[space-method]: https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks/blob/2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9/METHOD.md
[space-results]: https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks/blob/2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9/results.json
[i36]: https://github.com/slayerlabs/benchmarks-fabryka-ai/issues/36
[space]: https://huggingface.co/spaces/SlayerLab/Slayer1B/tree/3f2adb00d5db043a879ca7a0847c0220a5a42543
[releases]: https://huggingface.co/spaces/SlayerLab/Slayer1B/blob/3f2adb00d5db043a879ca7a0847c0220a5a42543/releases.json
[dc108]: https://huggingface.co/SlayerLab/Slayer1B-1.08/blob/ea0945b11153e67517b70d21192e6076d161f658/DATA_CARD.md
[dc109]: https://huggingface.co/SlayerLab/Slayer1B-1.09/blob/b25aec4ef6fb0c13717c5e5e27a426c572df54c6/DATA_CARD.md
[m107rev]: https://huggingface.co/SlayerLab/Slayer1B-1.07/tree/a090b54e658fb57dc5166c1fcc90cc6bf5c80106
[d107]: https://huggingface.co/datasets/SlayerLab/slayer-1.07-pretrain/tree/6a337bbfba518d88f14eb54f7d0a9b9f297df0d1
[min5b]: https://huggingface.co/datasets/SlayerLab/minimal-en-corpus-5b/tree/bb3aec23e3cff66707cecc577650763893834857
[fwe107]: https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu/tree/87f09149ef4734204d70ed1d046ddc9ca3f2b8f9
[fwe]: https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu
[logika]: https://huggingface.co/datasets/SlayerLab/slayer-pl-logika-2b/tree/e24c8b71526ca1dc56a280100f88c2f09a79ecdd
[entech]: https://huggingface.co/datasets/SlayerLab/english-technical-1b/tree/3b833d36bd3ba9aeecf46f39605c9ac849bb96a3
[gollem]: https://huggingface.co/datasets/SlayerLab/gollem-corpus-16b-pl/tree/17f9d37af3c9803178adcc1e056f664ba62a3558
[fpe]: https://huggingface.co/datasets/HuggingFaceFW/finepdfs-edu/tree/9cfabe2127faca99b3d5c4dc6d1fcb397399ebde
[d108b]: https://huggingface.co/datasets/SlayerLab/slayer-1.08b-pretrain/tree/0b5a12b7a19a27c549a11d13748fb7e113620bee
[subm]: https://huggingface.co/datasets/SlayerLab/dataset-team-submissions
[dclm]: https://huggingface.co/datasets/mlfoundations/dclm-baseline-1.0/tree/a3b142c183aebe5af344955ae20836eb34dcf69b
[hgs]: https://huggingface.co/datasets/SlayerLab/hutnictwo-gornictwo-spawalnictwo-preview
[pdpm]: https://huggingface.co/datasets/SlayerLab/polish-dynaword-pretraining-mix
[tin]: https://huggingface.co/datasets/SlayerLab/technika-i-nauka
