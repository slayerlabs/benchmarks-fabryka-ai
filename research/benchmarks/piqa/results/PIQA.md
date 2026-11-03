# PIQA (T06): Slayer 1.06 i kontrola Pythia-1B v0

Wygenerowane przez `benchmarks/piqa/piqa.py report` z `results/piqa.json`; nie edytuj ręcznie (bramka (g) `tools/sprawdz_raporty.py`).
Protokół: [`PROTOCOL.md`](../PROTOCOL.md), zacommitowany przed pierwszym surowym wynikiem. Przepis: [`RECIPE.md`](../RECIPE.md).
Slayer 1.06 to checkpoint z około 1/8 planu treningu, bez wygaszania LR; Pythia-1B v0 skończyła trening.

## Liczba dla Space

Slayer 1.06, acc_norm, panel Space (protokół Space, `min(200, N)` pytań): 0,6800 (n 200, CI95 0,6150–0,7450). Obok dokładniejszy pełny split walidacyjny: 0,6415 (n 1838, CI95 0,6197–0,6632); główna teza niżej opiera się na pełnym splicie.
*Dodane po pomiarze (eksploracyjne, nie ma tego w PROTOCOL.md): która z dwóch liczb idzie do Space i test panel minus pełny split. PROTOCOL.md nie ustalił liczby dla Space; panel idzie według protokołu Space (`bench50-v0.3.1-panel200`), ale METHOD.md nie definiuje postaci kanonicznej wiersza, z której powstaje id źródła, więc nie ma pewności, że nasz panel to panel Space.*
Panel minus pełny split: Slayer 3,85 pkt (z 1,23, szum), Pythia 2,05 pkt (z 0,69, szum); z = różnica / (SE panelu × sqrt((N − n) / (N − 1))), czyli poprawka na skończoną populację, bo panel jest losowany z pełnego splitu. <!-- liczba-spoza-wynikow: pkt wprost z kluczy panel_minus_full_pts w piqa.json, linię trzyma bramka (g) -->

Główna teza: Slayer 1.06 ma 0,6415 na pełnym splicie, 14,15 pkt ponad bazą losową (z 12,64, pewne). Teza dotyczy wyniku, nie rozumowania fizycznego: Space oznacza T06 dla Slayera 1.06 jako skażony (`contamination: flagged`), a bez korpusu treningowego nie powiemy, ile z tego marginesu pochodzi z pytań widzianych w treningu (brak wartości bez trafień). Teza upada, gdyby z wobec bazy losowej było poniżej 3 albo gdyby kontrola wyszła poza tolerancję. <!-- liczba-spoza-wynikow: pkt wprost z klucza comparisons.slayer_vs_random_full.difference_pts w piqa.json, linię trzyma bramka (g) -->

## Wyniki (acc_norm, 0-shot, lm-eval 0.4.9.1, float32, batch 1)

| model | split | n | acc_norm | SE | CI95 | acc | udział opcji 1 (acc_norm) | najczęstsza predykcja |
|---|---|---:|---:|---:|---|---:|---:|---:|
| Slayer 1.06 | pełny walidacyjny | 1838 | 0,6415 | 0,0112 | 0,6197–0,6632 | 0,6561 | 0,4978 | 0,5022 |
| Slayer 1.06 | panel Space | 200 | 0,6800 | 0,0331 | 0,6150–0,7450 | 0,6250 | 0,4600 | 0,5400 |
| Pythia-1B v0 | pełny walidacyjny | 1838 | 0,7095 | 0,0106 | 0,6882–0,7301 | 0,7051 | 0,4918 | 0,5082 |
| Pythia-1B v0 | panel Space | 200 | 0,7300 | 0,0315 | 0,6650–0,7900 | 0,6800 | 0,5100 | 0,5100 |

SE = odchylenie standardowe z próby / sqrt n; CI95 = bootstrap percentylowy po pytaniach, 10 000 powtórzeń, seed 20261028.
Bazy: losowa 0,5000; większościowa (udział najczęstszej poprawnej opcji) 0,5049 na pełnym splicie (n 1838) i 0,5100 na panelu (n 200); udział opcji 1 wśród poprawnych odpowiedzi 0,4951 (pełny) i 0,5100 (panel).
Remisy (równe wyniki obu opcji): acc 0 i acc_norm 0 dla Slayera, acc 0 i acc_norm 0 dla Pythii (pełny split); remis poszedłby do opcji 1, jak w argmax lm-eval.

## Diagnostyka (pełny split, eksploracyjna: dodana po pomiarze, nie służy żadnej tezie)

| model | BPB poprawnej odpowiedzi, średnia po pytaniach | BPB, łącznie | wybiera dłuższą opcję (acc_norm) | wybiera dłuższą opcję (acc) |
|---|---:|---:|---:|---:|
| Slayer 1.06 | 1,3066 | 1,1122 | 0,5759 | 0,3233 |
| Pythia-1B v0 | 1,1223 | 0,9487 | 0,5642 | 0,3442 |

BPB liczy bajty kontynuacji razem z wiodącą spacją (to, co model przewidywał). Średnia po pytaniach uśrednia BPB poszczególnych pytań; łącznie to suma NLL / (ln 2 × suma bajtów).
Dłuższa opcja: na 1627 pytaniach, których opcje różnią się długością (w znakach); poprawna opcja jest dłuższa w 0,4720 z nich. Czy preferencja długości różni się między modelami, jest nierozstrzygnięte (protokół nie ustalił testu).

## Panel

200 pytań, rosnący SHA-256 z `20261028|piqa|piqa|<source id>` (METHOD.md, sekcja 3). Id źródła = SHA-256 wiersza kanonicznego (JSON z posortowanymi kluczami, separatory `,` i `:`, UTF-8; wiersze PIQA nie mają natywnego id). Skrót panelu = SHA-256 z 200 id źródeł w kolejności splitu, połączonych `\n`: `47f3ab401075f29b934f9e7321df350d4032e24086617eb1ae393434489d992e`.
Space nie ma wartości T06 ani `source_id_digest` dla żadnego modelu, więc panelu nie sprawdzamy względem Space. Wyciąg z METHOD.md i tasks_50.json w rewizji Space: [`../SPACE_METHOD.md`](../SPACE_METHOD.md).

## Kontrola

| metryka | Pythia-1B v0, nasza | opublikowana | różnica, pkt | tolerancja, pkt | w tolerancji |
|---|---:|---:|---:|---:|---|
| acc | 0,7051 | 0,7040 | 0,11 | 2,13 | tak |
| acc_norm | 0,7095 | 0,7051 | 0,44 | 2,13 | tak |

Tolerancja = max(2 pkt, 2 × opublikowane SE).
Wersja harnessu: tasks_50.json podaje dla T06 `instrument: lm_eval_0.4.8`, a METHOD.md w sekcji 2 przypina zadania angielskie do commita lm-eval `6d2abda4`; ten pomiar szedł na lm-eval 0.4.9.1. Porównany był tylko katalog zadania (`piqa.yaml`, `README.md`), nie kod harnessu; zob. METODOLOGIA.md, sekcja „Wersja lm-eval”.
Opublikowane acc_norm leży 19,28 błędów standardowych ponad bazą losową i 18,82 ponad bazą większościową (błąd standardowy 0,0106), więc kontrola odróżnia działający kod od zgadywania. Kontrola zaliczona: tak.

BOS różni się między modelami: Slayer dostaje jeden BOS przed każdym żądaniem, tak jak robi to wrapper `slayer` z #44 (METHOD.md wiąże BOS z `add_bos_token` tokenizera, a Slayer nie ma tokenizer_config.json), Pythia żadnego (konwencja jej tokenizera i harness z 2022 roku, który dał opublikowaną wartość). Wpływ BOS na Pythię, a więc na porównanie Slayer − Pythia: NOT RUN (wymaga drugiego przebiegu Pythii z BOS; samą kontrolę liczymy tak, jak liczono opublikowaną wartość).

## Porównania (werdykt: |z| ≥ 3 pewne, 2–3 prawdopodobne, < 2 szum)

| porównanie | split | różnica, pkt | z | werdykt |
|---|---|---:|---:|---|
| Slayer 1.06 − baza losowa | pełny | 14,15 | 12,64 | pewne |
| Slayer 1.06 − baza większościowa | pełny | 13,66 | 12,20 | pewne |
| Slayer 1.06 − Pythia-1B v0 (SE parowane) | pełny | −6,80 | −7,16 | pewne |
| Slayer 1.06 − baza losowa | panel | 18,00 | 5,44 | pewne |
| Slayer 1.06 − baza większościowa | panel | 17,00 | 5,14 | pewne |
| Slayer 1.06 − Pythia-1B v0 (SE parowane) | panel | −5,00 | −1,84 | szum |

z wobec bazy = (wartość − baza) / SE wartości; Slayer − Pythia używa SE parowanego (odchylenie standardowe różnic per pytanie / sqrt n).
Pewna różnica między Slayerem a Pythią nie mówi o swojej przyczynie. Alternatywy: udział angielskiego w danych treningowych (około 10% dla Slayera, 100% dla Pythii) i etap treningu. Możliwe skażenie Slayera na PIQA działa w drugą stronę: podniosłoby wynik Slayera, więc bez niego różnica mogłaby być większa. Różnica BOS opisana wyżej nie jest zmierzona. <!-- ocena-bez-se: alternatywne przyczyny różnicy, której z jest w tabeli wyżej, bez nowego porównania -->

## Ten sam przebieg Pythii na innych GPU

| GPU | n | acc_norm | decyzje inne niż w przebiegu głównym | maks. bezwzględna różnica logprob |
|---|---:|---:|---:|---|
| NVIDIA RTX A6000 | 1838 | 0,7095 | 0 | 6.3e-04 |
| NVIDIA GeForce RTX 3090 | 1838 | 0,7095 | 0 | 6.3e-04 |
