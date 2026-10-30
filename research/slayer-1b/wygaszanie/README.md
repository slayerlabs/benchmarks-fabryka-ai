# Wygaszanie LR na Slayer 1B 1.06: przebieg

Progi: `PROGI.md` (zmiana Z1 → Z2 zapisana przed pomiarem loss).

## Rozbieg i wybór K (30.10.2026)

- Instancja vast.ai 2× RTX 4090 (oferta 45040009, Quebec, reliability 0,995, 0,85 $/h), obraz
  `pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel`, torch 2.6.0+cu124. Bezpiecznik `po 24600` uzbrojony
  przed wysyłką kodu (destroy najpóźniej 6 h 50 min po wynajmie).
- `pobierz.py`: sha256 `ckpt_13848.pt` zgodne z `config.json` 1.06, trener zgodny (`db36c150…`).
- `konwertuj.py ckpt_13848 --porownaj`: max |różnica| wobec wag 1.06 = **0,0**.
- `dane.py`: 200 032 825 tokenów train, 4 211 374 heldout, rewizja zbioru `d50df04a`, 603 020
  13-gramów ewaluacji, dekontaminacja usunęła 7 dokumentów (core_sa 1, legal 4, en 2). Tokenizacja
  2 przykładów (web) dzieli polskie słowa sensownie.
- Trener: łatka `latka_trenera.py` (kotwica `torch.load` ma w r23 komentarz `# r20`, poprawione).
  Flagi: `--resume --steps 13848+K --batch 256 --grad-accum 128 --block 4096 --dtype uint16
  --data-seed 20261023 --sampler random --optimizer muon --act-ckpt --loss-chunk 1024 --compile`,
  architektura z `config` checkpointu. Log obu ramion: `RESUME @ 13848`, `train RNG fast-forward o 13848`.
- Pomiar (próba 3 kroki, stały LR): mikrobatch 2 (`--grad-accum 128`) **11 440 tok/s** na kartę
  (91,7 s/krok, 20,2 GB), mikrobatch 1: 10 460 tok/s. Strata kroku 13849/13850/13851 identyczna w obu
  konfiguracjach (2,2789 / 2,2668 / 2,2844).
- **K = 150** (157 286 400 tokenów, ok. 3 h 50 min na ramię): największe K, przy którym trening, pomiar
  baz, heldout i benchmarki mieszczą się przed bezpiecznikiem z zapasem ok. 1 h. Koszt instancji
  ok. 0,85 $/h × ~6 h ≈ 5 $, poniżej limitu 10 $.
- Test przeuczenia: nie robiony. Wznawiamy gotowy checkpoint 1.06 trenerem
  Arka bez zmian w modelu ani stracie; strata startowa 2,28 = kontynuacja, nie trening od zera.
  Bramka „przerwanie po 20% kroków bez spadku o 10%”: nie dotyczy (model zbieżny, oczekiwany spadek
  o setne części nat).

## Trening ramion

A (liniowe wygaszenie 6e-4 → 0) i B (stały 6e-4): kroki 13848 → 13998, start 05:21 UTC, koniec
A 09:11, B 09:17, oba `ckpt @ 13998`, `DONE`, 11 450 / 11 240 tok/s przez cały bieg.

## Zmienność odniesienia (zmierzona PRZED loss ramion A/B)

`heldout.py`, 1027 okien × 4096 tokenów, te same okna dla wszystkich modeli:

| model | krok | loss (nat/token) | SE |
|---|---:|---:|---:|
| 1.06 | 13848 | 2,33104 | 0,01212 |
| ckpt_13800 | 13800 | 2,33215 | 0,01209 |
| 1.03 | 7150 | 2,46998 | 0,01208 |

- **Z2** = |L(13800) − L(13848)| = **0,00110** nat (główna miara szumu): 3 × Z2 = 0,0033, więc w werdykcie
  wiąże próg −0,03 nat i 2·SE(Δ), nie Z2.
- **Z1** = |L(1.03) − L(1.06)| = **0,13894** nat (kontekst: postęp 6698 kroków treningu, 3 × Z1 = 0,417).

## Wynik (pełna tabela: `wyniki/porownanie.md`, surowe pliki per pytanie: `wyniki/pelne_wyniki.tgz`)

**Loss heldout:** A 2,2807, B 2,3276, 1.06 2,3310. Δ A−B = **−0,0470 nat** (SE 0,0006, parowany bootstrap
po 1027 oknach). Warunki: Δ ≤ −0,03 tak, |Δ| ≥ 3 × Z2 (0,0033) tak, |Δ| > 2·SE tak.
**Werdykt: „działa"** wg głównej miary szumu Z2; **nie** wg Z1 (|Δ| < 3 × Z1 = 0,417). Spadek jest we
wszystkich komponentach (web −0,055, core −0,020, legal −0,037, en −0,058). B (stały LR, te same dane)
prawie nie rusza lossu wobec 1.06 (−0,0034), czyli zysk A pochodzi z wygaszenia, nie z danych.

**Benchmarki (A−B, |Δ| > 2 SE):** trafność (acc) bez ruchu na ARC-C, MedMCQA, Social IQa, MultiBLiMP;
wszystkie przy bazie losowej jak 1.06. Ponad 2 SE poza acc: MultiBLiMP acc_norm +0,005 i bpb +0,004
na korzyść A, Social IQa PMI −0,012 na niekorzyść A (bez poprawki na wielokrotne porównania). PubMedQA acc_norm −0,058 i bpb −0,022 na niekorzyść A (n=500,
sygnał do sprawdzenia, nie wynik). BPB poprawnej odpowiedzi: A lepsze od B w ARC-C cloze
(−0,044), MedMCQA cloze (−0,063), MultiBLiMP (−0,022) i Social IQa MC (−0,046), gorsze w ARC-C MC
(+0,053), MedMCQA MC (+0,016), Social IQa cloze (+0,018) i PubMedQA (+0,177), więc podział cloze/litery
nie wyznacza kierunku. Obie gałęzie pogarszają BPB poprawnej w formatach literowych
wobec 1.06 (A / B: ARC-C MC +0,39 / +0,34, Social IQa MC +0,56 / +0,61): kroki na pack-07 przesuwają rozkład liter niezależnie
od LR. WikiText-2: A 1,8921 byte-ppl (1.06 1,8925, B 1,9205).

Zgodnie z „Ryzykiem interpretacji" w PROGI.md: niższy loss po wygaszeniu nie przełożył się na trafność
benchmarków. Wynik dotyczy wygaszenia krótkiego (150 kroków, 157 M tokenów).
