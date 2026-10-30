# Testy danych na Slayer 1B: plan przebiegu (po recenzji, karty jeszcze nie wynajęte)

Progi i werdykty: `PROGI.md` (zapisane przed jakimkolwiek wynikiem; zmiana po recenzji opisana na górze).
Infrastruktura z `wygaszanie/` (pobierz, konwertuj, łatka trenera, bezpiecznik) bez zmian, poza kotwicą
`# r20` w łatce (ta sama poprawka, którą opisuje `wygaszanie/README.md`). Flagi trenera skopiowane
z `ramie.sh` działającego przebiegu wygaszania (instancja 58351985, odczyt 30.10 ok. 09:07).

| plik | co robi |
|---|---|
| `dane_ramion.py` | pule dokumentów per plik, dekontaminacja 13-gramów (testy główne + szuflada), dedup FineWeb2-HQ wobec szkicu HPLT z 8 pakietów, `train.bin` czterech ramion (C, C2, E25, PLHQ) i wspólny heldout |
| `heldout_bpb.py` | loss i BPB per okno i per komponent (bajty z tablicy tokenów ByteLevel, sprawdzanej na starcie) |
| `ewal_ramion.py` | testy główne albo szuflada (`--szuflada`), zapisuje krok modelu w `zrodla.json` |
| `porownaj_ramion.py` | Z2, Zk, bootstrap i 95% CI, werdykty; odmawia przy złym kroku modelu; `--szuflada` dopiero po `werdykt_glowny.json` |
| `na_instancji.sh` | etapy na instancji (przygotuj, dane, ewaluuj, trenuj, konwertuj_koniec, stan, pakuj), długie w tle |
| `../tests/test_testy_danych_slayer.py` | 22 testy: czyste funkcje, `zbuduj_pule`, `_filtr_hq`, `main` na fiksturze parquet (rozłączność heldoutu) |

## Instancja i koszt

vast.ai, 2× RTX 4090, ~0,85 $/h, dysk ≥ 250 GB (8 pakietów webu HPLT do szkicu dedupu ok. 50-60 GB,
checkpointy 2 × 8,9 GB + 4 końcowe), RAM ≥ 64 GB, ≥ 16 rdzeni. Przy wyborze oferty sprawdzić cenę
transferu (pobieramy ok. 90 GB).

K = 100, krok 91,7 s (zmierzony w wygaszaniu), start trenera ok. 10 min → ok. 2 h 43 min na ramię.

| czas od wynajmu | GPU0 | GPU1 | CPU | pobranie na komputer lokalny |
|---|---|---|---|---|
| 0:00-0:45 | — | — | `przygotuj` | — |
| 0:45-2:15 | ewal 13848 główne | ewal 13848 szuflada | `dane` | — |
| 2:15-2:30 | heldout 13800 | heldout 13848 | — | `pakuj po_bazach` |
| 2:30-5:15 | trening **C** | trening **E25** | — | `pakuj po_rundzie1` (logi treningu) |
| 5:15-8:00 | trening **PLHQ** | trening **C2** | — | `pakuj po_rundzie2` |
| 8:00-9:50 | ewal C (wszystko), potem PLHQ (wszystko) | ewal E25 (wszystko), potem C2 (heldout + główne) | — | po każdym modelu `pakuj` |
| 9:50-10:05 | `pakuj koniec`, pobranie, zniszczenie instancji | | | |

**Szacunek: ok. 10 h ≈ 8,6 $.** Bezpiecznik `po 39600` (11 h) = najwyżej 9,35 $ za instancję. Niepewne:
czas `dane` (szkic 8 pakietów, nieprzetestowany na pełnej skali) i ewaluacja (MMLU i Global-MMLU 5-shot,
szacunek ok. 1 h na model na 4090). Gdy `dane` nie skończy się do 2:30 albo krok wyjdzie > 95 s,
K liczysz regułą z `PROGI.md` i zapisujesz tu przed startem rundy 1. Bezpiecznik niszczy dysk, więc
wyniki schodzą na komputer lokalny po KAŻDEJ rundzie i po każdym zewaluowanym modelu, nie tylko na końcu.

Kontrola na instancji przed rundą 1: `statystyki.json` → `en_komponenty` (czy `shared/en.parquet` ma
`source_id`; bez niego EN jest jednym komponentem, PROGI to przewiduje), udział `duplikat_hplt` i
`ok_niesprawdzony` w plikach `web_hq`, równe `tokeny_train` czterech ramion.

## Wywołania z komputera lokalnego (każde osobno; klucz i port z panelu vast.ai)

Kod z zacommitowanego stanu gałęzi (jedno archiwum, bez `.venv`, `data/` i checkpointów):

```
git -C <worktree> archive -o $TMPDIR/kod.tar.gz HEAD slayer_eval wygaszanie testy_danych_slayer tests
scp -i <klucz> -P <port> $TMPDIR/kod.tar.gz root@sshN.vast.ai:/workspace/
ssh -i <klucz> -p <port> root@sshN.vast.ai 'mkdir -p /workspace/kod && tar -xzf /workspace/kod.tar.gz -C /workspace/kod'
```

Etapy (po jednym `ssh` na etap; długie wracają od razu, postęp i pliki `.ok`/`.blad` przez `stan`):

```
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh przygotuj 39600'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh dane 135e6'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh ewaluuj 13848 0 glowne'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh ewaluuj 13848 1 szuflada'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh stan'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh ewaluuj 13800 0 heldout'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh ewaluuj 13848 1 heldout'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh pakuj po_bazach'
scp -i <klucz> -P <port> root@sshN.vast.ai:/workspace/glowne_po_bazach.tar.gz <katalog wyników>/
scp -i <klucz> -P <port> root@sshN.vast.ai:/workspace/szuflada_po_bazach.tar.gz <katalog wyników>/
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh trenuj C 0 100'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh trenuj E25 1 100'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh pakuj po_rundzie1'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh trenuj PLHQ 0 100'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh trenuj C2 1 100'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh pakuj po_rundzie2'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh ewaluuj C 0 wszystko'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh ewaluuj E25 1 wszystko'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh ewaluuj PLHQ 0 wszystko'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh ewaluuj C2 1 heldout'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh ewaluuj C2 1 glowne'
ssh -i <klucz> -p <port> root@sshN.vast.ai 'bash /workspace/kod/testy_danych_slayer/na_instancji.sh pakuj koniec'
scp -i <klucz> -P <port> root@sshN.vast.ai:/workspace/glowne_koniec.tar.gz <katalog wyników>/
scp -i <klucz> -P <port> root@sshN.vast.ai:/workspace/szuflada_koniec.tar.gz <katalog wyników>/
```

Po każdym `pakuj` pobierz oba archiwa tej etykiety (dwa `scp` jak po bazach). Etap na danym GPU startuje
się po `.ok` poprzedniego na tym GPU (`stan`). `trenuj` sam sprawdza `RESUME @ 13848`, a
`konwertuj_koniec` konwertuje tylko końcowy `runs/<ramię>/ckpt.pt` (plik, nie dowiązanie startowe)
i przerywa, gdy jego krok ≠ 13848 + K.

Na komputerze lokalnym: rozpakuj `glowne_koniec.tar.gz` do `<wyniki>`, `python testy_danych_slayer/porownaj_ramion.py
--wyniki <wyniki>/wyniki --K 100` → commit `werdykt_glowny.json` → dopiero wtedy rozpakuj szufladę do
`<wyniki>/wyniki/szuflada` i `porownaj_ramion.py --wyniki <wyniki>/wyniki --K 100 --szuflada`.

## Próby lokalne (30.10.2026, CPU)

- `python -m py_compile` wszystkich skryptów i `bash -n na_instancji.sh`: OK.
- `python tests/test_testy_danych_slayer.py`: kod wyjścia 0, 22/22 (w tym `zbuduj_pule` deterministyczna
  i z heldoutem rozłącznym z pulą, `_filtr_hq` rozróżnia duplikat/dekontaminację/krótki/nowy,
  `main` na fiksturze: cztery ramiona równej długości, heldout rozłączny z każdym `train.bin`, C2 ≠ C,
  dedup działa, `en_komponenty` z `source_id`).
- Wcześniej (wersja planu sprzed recenzji): `ewal_ramion.py` przez atrapę modelu na zbiorach z cache HF — arc_e/arc_c/siqa
  cloze, belebele, multiblimp PASS; MMLU 5-shot i szuflada BLOCKED (brak w cache, komputer bez dostępu do HF).
- NOT RUN: `heldout_bpb.py` na modelu Slayera, trening i `porownaj_ramion.py` w nowej wersji na wynikach
  modelu (brak wag lokalnie; jego funkcje werdyktu pokrywają testy).
