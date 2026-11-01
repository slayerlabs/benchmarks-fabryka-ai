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
