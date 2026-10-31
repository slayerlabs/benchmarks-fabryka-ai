# Czy wygaszenie LR poprawia Slayer 1B — progi zapisane PRZED treningiem

Zapisane 30.10.2026 przed odpaleniem ramion A i B. Po zobaczeniu wyników progów nie zmieniamy.

## Ramiona

- Start obu: pełny checkpoint trenera Arka `SlayerLab/Slayer1B-1.06-checkpoints/ckpt_13848.pt`
  (wagi + stan optymalizatora Muon+AdamW, krok 13848 = wydanie 1.06). Stan optymalizatora JEST
  dostępny (README repo checkpointów), więc bez świeżego warmupu: zakłócenie „brak stanu Adama"
  z projektu nie występuje. Zostaje zakłócenie danych (niżej).
- Trener: `train_gpt_ref_r23.py` z repo HF 1.06 (rewizja ef81be58), łatka `latka_trenera.py`
  dodaje tylko harmonogram z env i ładowanie checkpointu na CPU. Batch jak u Arka: 256 × 4096
  = 1 048 576 tokenów na krok (na 1 GPU: akumulacja gradientu).
- **A:** LR liniowo od 6e-4 w kroku 13848 do 0 w kroku 13848+K (Muon skalowany tym samym mnożnikiem
  `lr_mult` z checkpointu).
- **B:** stały LR 6e-4, te same K kroków.
- Te same dane, ten sam `data_seed` (20261023), więc te same batche w tej samej kolejności.
- K dobrane po pomiarze przepustowości (zapis w `README.md` po rozbiegu).

## Metryki i progi

**Loss** = średnia strata (nat/token) na odłożonej części danych (`heldout.bin`, okna 4096,
dokumenty rozłączne z treningiem). SE(Δ) = bootstrap 10 000 po oknach, parowany (te same okna).

Zmienność odniesienia:
- **Z1 (z projektu):** |L(1.03) − L(1.06)| na tych samych oknach.
- **Z2 (dodatkowa):** |L(ckpt_13800) − L(ckpt_13848)|, czyli dwa sąsiednie checkpointy stałego LR
  (50 kroków), czysty szum trajektorii bez wygaszania.

**Zmiana 30.10.2026 (po recenzji planu, przed treningiem ramion i przed jakimkolwiek pomiarem loss):**
główną miarą szumu jest **Z2**, a Z1 raportujemy obok jako kontekst. Krok 13848 kończy jedyną epokę
korpusu, więc 1.03 → 1.06 to postęp treningu na danych, które 1.06 już widział, a nie szum. Próg
3 × Z1 mierzyłby, czy wygaszenie przebija kilka tysięcy kroków treningu, nie czy przebija szum.
Pozostałe progi (−0,03 nat, 2·SE) bez zmian. Werdykt poniżej czytaj z Z2 w miejscu Z1; linia
„działa wg Z2" przechodzi w „działa także wg Z1" (raportowane osobno, mocniejsze).

Werdykt na loss (Δ = L(A) − L(B)), w brzmieniu sprzed zmiany:
- **„działa"**: Δ ≤ −0,03 nat ORAZ |Δ| ≥ 3 × Z1 ORAZ |Δ| > 2·SE(Δ).
- **„działa wg Z2"** (raportowane osobno, słabsze): Δ ≤ −0,03 ORAZ |Δ| ≥ 3 × Z2 ORAZ |Δ| > 2·SE,
  ale nie 3 × Z1.
- **„szkodzi"**: Δ ≥ +0,03 przy tych samych warunkach szumu.
- W każdym innym przypadku: **„nierozstrzygnięte"** (nie „brak efektu").

Benchmarki (ARC-C, MedMCQA, PubMedQA, Social IQa, MultiBLiMP-pl, WikiText-2): różnica A−B liczy się
tylko przy |Δ| > 2·SE(Δ), SE z parowanego bootstrapu po pytaniach (10 000, seed 20261028).
Poniżej: „nierozstrzygnięte". Ponieważ zadań × metryk jest wiele, pojedyncze przekroczenie 2 SE
traktujemy jako sygnał do sprawdzenia, nie jako wynik (bez poprawki na wielokrotne porównania).

## Ryzyko interpretacji

Niższy loss po wygaszeniu ≠ więcej wiedzy. Wygaszenie zmniejsza szum w wagach (model trafia bliżej
dna doliny), co obniża perplexity, ale nie musi dodać faktów ani umiejętności. Benchmarki MC przy
1B leżą blisko losowej, więc ich brak ruchu jest spodziewany niezależnie od lossu.

## Zakłócenia znane z góry

- **Dane:** mieszanka `SlayerLab/slayer-pl-8x3b` (ten sam zbiór co Arek, proporcje scenariusza B
  z karty: web 63 / core 19 / legal 8 / en 10), pakiet web `pack-07`. Nie wiemy, które dokumenty
  Arek już widział (karta tego nie podaje), więc część tokenów może być powtórką. Obie gałęzie
  dostają to samo, ale wygaszenie na danych widzianych może wyglądać lepiej niż na świeżych.
- **Dekontaminacja:** dokumenty z 13-gramem słów wspólnym z pytaniami ewaluacji (ARC-C test,
  MedMCQA validation, PubMedQA test, Social IQa validation, WikiText-2 test, MultiBLiMP pol) usunięte
  przed tokenizacją. Zdania MultiBLiMP krótsze niż 13 słów nie dają 13-gramów i nie są filtrowane.
- **Sprzęt:** 1 GPU z akumulacją zamiast 8× L40S DDP: ta sama matematyka kroku, inna kolejność
  sumowania (bf16 autocast), różnice numeryczne na poziomie szumu.
- **Długość:** wygaszenie na K ≈ kilkudziesięciu krokach (<1% treningu Arka) to krótszy cooldown niż
  typowe 10-20% w WSD. Wynik mówi o krótkim wygaszeniu, nie o optymalnym.
