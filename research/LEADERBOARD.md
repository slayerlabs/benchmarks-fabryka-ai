# Leaderboard i meta-ocena

Leaderboard pokazuje wiele modeli na wielu testach i jedną ocenę na model w każdym języku (meta-ocenę). Pliku zestawu
i kodu rankingu jeszcze nie ma; ten dokument mówi, co muszą spełniać, zanim powstanie pierwszy ranking. Typ testu, b,
SE i werdykt definiuje [METODOLOGIA.md](METODOLOGIA.md) (rdzeń i tabela typów).

## Co wchodzi

Meta-ocenę liczysz wyłącznie z wyników per pytanie z przebiegów repo (przebieg centralny albo wpis `RECIPE.md`).
Wynik wpisany ręcznie albo zgłoszony przez autora modelu bez naszego przeliczenia nie wchodzi
([Lessons from the Trenches, App. D](https://arxiv.org/abs/2405.14782)). W rankingu stoją mierzone modele i modele
odniesienia, więc ranking rusza po przebiegu centralnym.

## Plik zestawu

Przed pierwszym rankingiem w `results/` leży plik zestawu z numerem wersji zestawu (wersja zestawu testów, nie
Slayera). Podaje:

- listę testów z typem z tabeli typów, kategorię każdego testu, wagi kategorii (sumują się do 1) i minimalną liczbę
  testów w kategorii;
- metrykę decyzyjną każdego testu i split, z którego liczysz b;
- próg SNR, skład panelu SNR (wiersze `MODELE` z commitem wyników, METODOLOGIA, „Panel SNR”), najwyższe dopuszczalne b;
- liczbę powtórzeń bootstrapu i seed;
- hash zbioru i konfiguracji ewaluacji każdego testu;
- dla każdej pary model × test pole kontaminacji: „sprawdzona: metoda”, „znana: źródło” albo „nieznana”.

Zmiana czegokolwiek z tej listy daje nową wersję zestawu i nowy ranking, a stary zostaje bez zmian.

## Który test wchodzi

Test wchodzi do meta-oceny, gdy:

- przeszedł etap B (warunek odtworzenia albo „bez kontroli” z kodem zgodnym i kontrolą z tabeli typów; „bez
  kontroli: nierozstrzygnięte” nie wystarcza), wersja polska obie kontrole D3, a benchmark bez oryginału kontrolę
  karty zbioru;
- ma skalę z dolną kotwicą b: typy `ppl` i `sedzia` nie wchodzą, `ppl` stoi w osobnej kolumnie;
- próg SNR z pliku zestawu przekraczają dolna granica przedziału 95% jego SNR i najmniejszy SNR bez jednego modelu
  panelu (akapit niżej), a b nie przekracza najwyższego dopuszczalnego b (przy wysokim b dzielnik
  1 − b mnoży SE testu i jeden test przejąłby zmienność całej oceny).

SNR to pole SNR karty, liczone na modelach przebiegu centralnego poza mierzonym (METODOLOGIA, „Panel SNR”). Kryterium
bierze dolną granicę przedziału i minimum bez jednego modelu zamiast samego SNR, bo panel ma modele rankingu, a test dobrany na ich szumie albo na jednym odstającym modelu zawyżałby różnice albo wyróżniał ten model
(METODOLOGIA, „Panel a ranking”). Test ze znaną kontaminacją u danego modelu zostaje u tego modelu kolumną
informacyjną, poza średnią ([OLMo, §4.3](https://arxiv.org/abs/2402.00838)); tak samo test polski z SE większym niż w
oryginale (wiersz `+pl` tabeli typów). Jeden zbiór pytań (konfiguracja zbioru na HF; ARC-Easy i ARC-Challenge to dwa)
to jedna pozycja, nawet z kilkoma metrykami. Test, który nie spełnia warunków, zostaje w tabeli jako kolumna
informacyjna.

## Skala

Wynik testu to 100 · (x − b) / (1 − b), gdzie x i b są w skali 0–1 (po `+proc` podzielone przez 100), a b pochodzi z
tabeli typów. Z tego wynikają przypadki brzegowe: przy `f1-korpus` b to F1 najlepszej stałej predykcji, nie udział
klasy; przy `mcc` b = 0, więc wynik to 100 · MCC, od −100 do 100; przy `ifeval` b to wynik pustej odpowiedzi; przy
`gen` b to wynik stałej odpowiedzi. Test z `+warstwy` centrujesz w każdym podteście jego własnym b, a potem uśredniasz
z wagami oryginału (pole „Agregacja i grupy” karty).

Wyniku poniżej b nie obcinasz do zera, bo obcięcie zawyża modele przy poziomie losowym. Open LLM Leaderboard v2 obcina
do zera i bierze b = 1/k, więc nasza meta-ocena nie jest porównywalna z jego średnią
([Scores Normalization](https://huggingface.co/docs/leaderboards/open_llm_leaderboard/normalization)).

## Wzór

Najpierw średnia testów w kategorii, potem średnia kategorii z wagami z pliku zestawu. Kategoria z mniejszą liczbą
testów niż minimum daje meta-ocenę „N/A”. Polski i angielski liczysz osobno i każdy język ma własny ranking. Brak
wyniku (także `not_run`) to „N/A”, nigdy zero. Model bez kompletu testów danej wersji zestawu dostaje wyniki
cząstkowe, bez meta-oceny i miejsca.

## Niepewność i miejsce

SE meta-oceny i SE różnicy każdej pary modeli liczysz bootstrapem parowanym: w każdym powtórzeniu losujesz ze
zwracaniem jednostki każdego testu osobno, te same indeksy dla wszystkich modeli. Jednostka to ta z kolumny „SE” typu:
pytanie, dokument albo klaster wiążącego poziomu, a przy `+warstwy` losujesz wewnątrz podtestów. Dla każdej pary
liczysz z = różnica / SE różnicy i p dwustronne, a p poprawiasz metodą Holma po wszystkich parach rankingu, z progiem
jak dla |z| = 2. Miejsce to 1 plus liczba modeli z wyższą meta-oceną i różnicą, która przechodzi ten próg po poprawce,
więc modele bez takiej różnicy dzielą miejsce. Dopisanie modelu zmienia liczbę par, więc miejsca liczysz od nowa.

Obok rankingu podajesz wrażliwość: bootstrap po testach, wynik bez każdego testu po kolei, miejsca według
[head-to-head win rate z HELM, §8.1](https://arxiv.org/abs/2211.09110) i według średniej bez wag. Do reguły miejsca
wrażliwość nie wchodzi, bo nie jest błędem pomiaru.

## Checkpointy i wydajność

Ranking checkpointów jednego modelu bierze szum z checkpointów, nie z różnych modeli
([Signal and Noise, §3.1](https://arxiv.org/abs/2508.13144)). Wynik z etykietą „bez wygaszania LR” stoi w rankingu z
tą etykietą i nie jest wynikiem końcowym modelu (METODOLOGIA, „Następna wersja Slayera”).

Ocena na parametr albo na FLOP to osobna kolumna, nigdy mnożnik meta-oceny. Liczbę parametrów liczysz z wag, nie
bierzesz z deklaracji autora.
