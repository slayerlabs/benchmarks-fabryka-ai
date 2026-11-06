# Dane treningowe Slayera 1B, wersje 1.00–1.06

Ten plik mówi, na czym trenowano każdą wersję Slayera 1B. Opiera się na kartach modeli i checkpointów na HF
(rewizje są w odsyłaczach na dole), na zbiorze [`SlayerLab/slayer-pl-8x3b` @ `d50df04`][zbior] i na publicznej
notatce przebiegu [`f056bb5c`][track]. Wszystko odczytano 2026-11-04. Licencje składników opisuje
[`REJESTR_DATASETOW.md`](REJESTR_DATASETOW.md), sekcja 1.

## Wspólne dla wszystkich wersji

- **Zbiór.** Wszystkie wersje trenowano na jednym zbiorze, `slayer-pl-8x3b` @ `d50df04` (pole `datasets` we
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
- **`en`** to tylko `fineweb-edu`. `dataset.json` wymienia też finemath, ale w danych go nie ma (REJESTR, 1.2).
- **Dane osobowe** maskowano regułami przed tokenizacją: e-mail, telefon, PESEL, NIP, REGON, dowód. Maskowanie nie
  daje gwarancji, że usunięto wszystko ([karta 1.00][m100], karty 1.01–1.03).

## Wersje

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
