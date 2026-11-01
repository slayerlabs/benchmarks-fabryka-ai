# Protokół: SNR i baza większościowa ARC-Easy (karta oryginału)

Plik roboczy, usuwany przed PR. Ustalony przed jakimkolwiek liczeniem.

**Pytanie.** Jaki jest SNR ARC-Easy z opublikowanych wyników jednej rodziny modeli i jaka jest baza większościowa
(udział najczęstszej pozycji poprawnej odpowiedzi) na teście?

**Dane.**
- Wyniki modeli: repo `EleutherAI/pythia` @ `a19eecb807ec2c79a39ebf18108816e6ffffc1d5`, katalog `evals/pythia-v0`.
  Bierzesz każdy rozmiar bez sufiksu `-deduped`, który ma plik 0-shot z `global_step143000` i zadaniem `arc_easy`.
  Gdy rozmiar ma kilka takich plików, bierzesz najnowszy po dacie w nazwie i zapisujesz to. Metryka `acc`.
  Lista plików (ścieżka + blob sha) idzie do wyniku.
- Zbiór: `allenai/ai2_arc`, konfiguracja `ARC-Easy`, split `test`, rewizja `210d026` (ta sama co w karcie).

**Wzory (METODOLOGIA, Słowniczek „SNR”; README „Bazy”).**
- Rozrzut: odchylenie standardowe `acc` między modelami, z poprawką próbkową (ddof=1). Dla porównania także ddof=0.
- Typowe SE: √(p̄(1−p̄)/n), p̄ = średnia `acc` modeli, n = liczba pytań testu ze zbioru. Kontrolnie mediana
  `acc_stderr` z plików.
- SNR = rozrzut / typowe SE.
- Baza większościowa: indeks `answerKey` w `choices.label` każdego pytania; udział najczęstszego indeksu w całym
  teście. Dodatkowo rozkład indeksów i baza losowa (średnia 1/k) do porównania z kartą.

**Warunek potwierdzenia.** Skrypt liczy wszystko z pobranych plików, kończy się kodem 0, wartości trafiają do
`results/LICZBY.json` przez `tools/liczby.py`, a bramka `tools/sprawdz_raporty.py` kończy się kodem 0.

**Warunek obalenia.** Wniosek „ARC-Easy rozróżnia modele tej rodziny ponad szum (SNR ≥ 2)” upada, gdy inny rozsądny
wybór (wersja `-deduped`, ddof, SE z plików zamiast wzoru) daje SNR < 2. Wartość bazy większościowej upada, gdy
inny sposób mapowania etykiet (cyfry `1`–`4`, pytania z 3 i 5 opcjami) zmienia najczęstszą pozycję albo jej udział.

**Kontrola.** Baza losowa przeliczona tą samą drogą ma wyjść równa wartości już stojącej w karcie (średnia 1/k).

## Uzupełnienie przed liczeniem (2026-11-01)

Dopisane przed uruchomieniem skryptu. Odczytano tylko listę plików drzewa repo Pythii @ `a19eecb` (nazwy, bez treści)
i nic z wartości `acc`. Ustala to, czego protokół wyżej nie ustala.

1. **Dopasowanie pliku.** Plik w `evals/pythia-v0/<rozmiar>/zero-shot/` o nazwie
   `<rozmiar>-0shot-global_step143000_+eval_results_<MM-DD-YYYY-HH-MM-SS>.json` (jeden albo więcej znaków `_`
   przed `eval_results`; w drzewie `pythia-2.8b` ma `__`). „Najnowszy po dacie w nazwie” = maksimum daty w tym
   formacie. Rozmiar bez takiego pliku (w drzewie: 160m, 410m, 1.4b) albo z plikiem bez `results.arc_easy.acc`
   wypada i trafia do wyniku na liście wykluczonych z powodem.
2. **Integralność.** Plik z GitHuba pobierany z `raw.githubusercontent.com` po pełnym sha commita; skrypt liczy git
   blob sha pobranych bajtów i przerywa, gdy różni się od blob sha z drzewa. Zbiór: plik
   `ARC-Easy/test-00000-of-00001.parquet` @ `210d026faf9955653af8916fad021475a3f00453` przez `huggingface_hub`
   (pamięć podręczna, `HF_HUB_OFFLINE=1`); skrypt liczy sha256 i przerywa, gdy różni się od oid LFS (nazwa blobu).
3. **n** = liczba wierszy splitu `test` (bez filtrowania).
4. **Baza większościowa — wariant główny.** Indeks = `choices.label.index(answerKey)` (jak lm-eval), na wszystkich
   pytaniach; udział = liczba pytań z najczęstszym indeksem / n. Remis na maksimum: podajemy wszystkie indeksy
   z remisu, udział ten sam.
5. **Warianty obalenia bazy większościowej** (liczone obok, nie zamiast): (a) tylko pytania z 4 opcjami;
   (b) bez pytań z etykietami cyfrowymi; (c) klasa = dosłowna etykieta (`A`–`E` i `1`–`4` jako osobne klasy).
   Wartość upada, gdy w którymkolwiek wariancie najczęstsza pozycja jest inna (w (c): litera innej pozycji niż
   w wariancie głównym) albo udział różni się od głównego o więcej niż 0,01 (1 pkt, rząd SE `acc` przy n = 2376). <!-- liczba-spoza-wynikow: próg protokołu ustalony przed pomiarem -->
6. **Warianty obalenia SNR**: pełna siatka {bez `-deduped`, tylko `-deduped` (te same reguły 1)} × {ddof=1, ddof=0}
   × {SE ze wzoru, mediana `acc_stderr` z plików} = 8 wartości. Wariant główny: bez `-deduped`, ddof=1, SE ze wzoru.
   Wniosek „SNR ≥ 2” upada, gdy minimum z 8 wartości < 2; raport podaje minimum i wariant, który je daje.
7. **Kontrola bazy losowej**: wynik zaokrąglony do 4 miejsc ≠ 0,2502 → skrypt kończy się kodem ≠0 i nic nie <!-- liczba-spoza-wynikow: wartość z karty sprzed pomiaru, próg kontroli -->
   trafia do karty.
8. **Zapis w karcie**: udziały, SE i rozrzut z 4 miejscami po przecinku, iloraz SNR z 2 miejscami; wszystkie z
   `results/snr_baselines.json` (pula `arc-easy` w `results/LICZBY.json`).
