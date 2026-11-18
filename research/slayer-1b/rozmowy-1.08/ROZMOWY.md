# Rozmowy: wszystkie polecenia i odpowiedzi trzech modeli

Plik generuje `code/rozmowy.py` z `dane/polecenia.jsonl`, `wyniki/surowe/gen_*_A.jsonl` i `wyniki/oceny_pozycji.jsonl`; nie edytuj go ręcznie. Szablon A (few-shot „Polecenie:/Odpowiedź:”), dwa dekodowania: seed 1 (temperatura 0,7, top-p 0,9) i greedy. Odpowiedź jest dosłowna, po obcięciu na znaczniku końca szablonu; potrójny backtick w środku odpowiedzi zapisano jako „` ` `”. Seedy 2 i 3 oraz szablon B są w `wyniki/surowe/`. Ocena automatyczna według reguł z `code/ocena.py` (protokół, sekcja 4); polecenia otwarte nie mają oceny automatycznej.

Modele: Slayer 1.08 (`slayer`), Bielik 1.5B (`bielik`), LFM2.5 1.2B (`lfm`).

## Spis kategorii

- [pl_jezyk](#pl_jezyk)
- [pl_wiedza](#pl_wiedza)
- [wiedza_ogolna](#wiedza_ogolna)
- [rozumowanie](#rozumowanie)
- [matematyka](#matematyka)
- [kod](#kod)
- [angielski](#angielski)
- [tekst_techniczny](#tekst_techniczny)

## pl_jezyk

### pl_jezyk-01 (krotka, trudność 1)

**Polecenie:** Podaj mianownik liczby mnogiej rzeczownika „dziecko”.

**Wzorzec:** dzieci

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 dzieci
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 dzieci
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
dzieci
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
dzieci
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 dzieci
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 dzieci
```

### pl_jezyk-02 (krotka, trudność 1)

**Polecenie:** Podaj stopień wyższy przymiotnika „dobry”.

**Wzorzec:** lepszy

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 dobry
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Dobry
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
dobry
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
dobry
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 13

```text
 Błyskotliwy.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 11

```text
 bardzo dobry.
```

### pl_jezyk-03 (krotka, trudność 1)

**Polecenie:** Podaj narzędnik liczby pojedynczej rzeczownika „mama” (z kim? z czym?).

**Wzorzec:** mamą

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 z mamą
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 mama
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
mama z córką
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
z mamą
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 24

```text
 Mam, a ja zrobimy mu podarować 5 pyłków.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 17

```text
 Mamo, z kim? z czym?
```

### pl_jezyk-04 (krotka, trudność 1)

**Polecenie:** Podaj mianownik liczby mnogiej rzeczownika „kwiat”.

**Wzorzec:** kwiaty

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 kwiaty
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 kwiaty
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
kwiaty
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
kwiaty
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 kwiaty
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 kwiaty
```

### pl_jezyk-05 (krotka, trudność 2)

**Polecenie:** Podaj formę czasu przeszłego 3. osoby liczby pojedynczej rodzaju męskiego czasownika „iść” (on …).

**Wzorzec:** szedł

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 On idzie.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 iść
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
On poszedł.
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
on poszedł.
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 28

```text
 3. osoba liczby pojedynczej rodzaju męskiego czasownika „iść” (on …).
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 10

```text
 On iść.
```

### pl_jezyk-06 (krotka, trudność 2)

**Polecenie:** Podaj dopełniacz liczby mnogiej rzeczownika „ręka” (nie ma czego?).

**Wzorzec:** rąk

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 ręka
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 ręce
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
Ręce
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
rąk
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 32

```text
 dopełniacz liczby mnogiej rzeczownika „ręka” (nie ma czego?).
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 10

```text
 Ręka.
```

### pl_jezyk-07 (krotka, trudność 2)

**Polecenie:** Podaj miejscownik liczby pojedynczej rzeczownika „miasto” (o kim? o czym?).

**Wzorzec:** mieście

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Miasto
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 18

```text

Miasto jest duże, ale nie jest zbyt piękne.
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 18

```text
Miasto, które leży w Polsce, jest stolicą województwa śląskiego.
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
miasto
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Miasto.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 20

```text
 Miasto, które jest w pobliżu naszego domu.
```

### pl_jezyk-08 (krotka, trudność 2)

**Polecenie:** Podaj dopełniacz liczby pojedynczej rzeczownika „tydzień” (nie ma kogo? czego?).

**Wzorzec:** tygodnia

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 tygodnia
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Tydzień
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
tydzien
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
tygodnia
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 48

```text
 Wszyscy podziękowali, kto przyszedł do domu w dzień, i pożegnają się na zewnątrz, aż do północy.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: limit, tokenów: 48

```text
 Dzień dobry, Pani Ewo, dziękuję za pożyczenie drabiny. Oddam ją jutro rano, około ósmej. Pozdrawiam serdecznie, Adam
```

### pl_jezyk-09 (krotka, trudność 3)

**Polecenie:** Podaj narzędnik liczby mnogiej rzeczownika „przyjaciel” (z kim?).

**Wzorzec:** przyjaciółmi

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 przyjaciele
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 przyjaciele
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
przyjaciołom
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
Przyjaciele
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: limit, tokenów: 48

```text
 Pani Ewo, jak mamy być przyjaciela, dziękuję za pomoc. Może być mój przyjaciel, w którym się spotkamy rano, a może będzie ktoś
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 13

```text
 Przyjaciel, Adam.
```

### pl_jezyk-10 (krotka, trudność 3)

**Polecenie:** Podaj formę 2. osoby liczby pojedynczej trybu rozkazującego czasownika „wziąć”.

**Wzorzec:** weź

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Wziąć
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Wziąć
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Weź
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Weź
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 22

```text
 Wziąć 10 gramów cukru z kubka.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 11

```text
 Wziąć.
```

### pl_jezyk-11 (krotka, trudność 3)

**Polecenie:** Podaj formę 3. osoby liczby mnogiej czasu teraźniejszego czasownika „rozumieć” (oni …).

**Wzorzec:** rozumieją

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 20

```text

oni (oni) zrozumieli, co do nich powiedziałem.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: limit, tokenów: 48

```text

Dzień dobry, Pani Ewo, bardzo dziękuję za pożyczenie drabiny, bardzo mi pomogła przy malowaniu. Oddam ją jutro rano, około ósmej. Pozdrawiam serdecznie, Adam z drugiego piętra.

Po
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
oni rozumieją.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
oni rozumieją.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: eos, tokenów: 5

```text
 Rozumieją.
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 18

```text
 Rozumieją, Adam z drugiego piętra.
```

### pl_jezyk-12 (krotka, trudność 3)

**Polecenie:** Podaj celownik liczby pojedynczej rzeczownika „pies” (komu? czemu?).

**Wzorzec:** psu

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 15

```text

Psy, co to za zwierzę?
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 10

```text

Piesom
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 15

```text
Pies - to moje ulubione zwierzę domowe.
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 13

```text
Pies jest moim najlepszym przyjacielem.
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 41

```text
 Nawet jeśli nie znam, ale pewnie jestem w domu, więc ktoś będzie mógł to zrobić.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 15

```text
 Pies, który jest w domu.
```

### pl_jezyk-13 (zdanie, trudność 1)

**Polecenie:** Popraw błąd w zdaniu i napisz całe zdanie poprawnie: Wczoraj poszłem do sklepu po chleb.

**Wzorzec:** Wczoraj poszedłem do sklepu po chleb.

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: limit, tokenów: 48

```text

Dzień dobry, Pani Ewo, bardzo dziękuję za pożyczenie chleba, bardzo mi pomogła Pani przy malowaniu. Oddam ją jutro rano, około ósmej. Pozdrawiam serdecznie, Adam z drugiego piętra.

Polec
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 15

```text
 Wczoraj poszedłem do sklepu po chleb.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 14

```text
Wczoraj poszedłem do sklepu po chleb.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 14

```text
Wczoraj poszedłem do sklepu po chleb.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 22

```text
 Wczoraj poszedłem do sklepu po chleb.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: eos, tokenów: 16

```text
 Wczoraj poszłem do sklepu po chleb.
```

### pl_jezyk-14 (zdanie, trudność 1)

**Polecenie:** Popraw błąd w zdaniu i napisz całe zdanie poprawnie: Moja siostra ma pięć lat i chodzi do pszedszkola.

**Wzorzec:** Moja siostra ma pięć lat i chodzi do przedszkola.

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 17

```text
 Moja siostra ma pięć lat i chodzi do szkoły.
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 17

```text
 Moja siostra ma pięć lat i chodzi do przedszkola.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 16

```text
Moja siostra ma pięć lat i chodzi do przedszkola.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 16

```text
Moja siostra ma pięć lat i chodzi do przedszkola.
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 25

```text
 Moja siostra ma pięć lat i chodzi do pszedszkola.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: eos, tokenów: 19

```text
 Moja siostra ma pięć lat i chodzi do pszedszkola.
```

### pl_jezyk-15 (zdanie, trudność 1)

**Polecenie:** Popraw błąd w zdaniu i napisz całe zdanie poprawnie: Nie lubię ten film, bo jest nudny.

**Wzorzec:** Nie lubię tego filmu, bo jest nudny.

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 16

```text
 Nie lubię ten film, bo jest nudny.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 16

```text
 Nie lubię ten film, bo jest nudny.
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 16

```text
Nie lubię tego filmu, ponieważ jest nudny.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 16

```text
Nie lubię tego filmu, bo jest nudny.
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 19

```text
 Nie lubię ten film, ponieważ jest nudny.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 17

```text
 Nie lubię ten film, bo jest nudny.
```

### pl_jezyk-16 (zdanie, trudność 1)

**Polecenie:** Popraw błąd w zdaniu i napisz całe zdanie poprawnie: Rzeka w naszym mieście jest szeroka i głemboka.

**Wzorzec:** Rzeka w naszym mieście jest szeroka i głęboka.

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 18

```text
 Rzeka w naszym mieście jest szeroka i głęboka.
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 18

```text
 Rzeka w naszym mieście jest szeroka i głęboka.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 18

```text
Rzeka w naszym mieście jest szeroka i głęboka.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 18

```text
Rzeka w naszym mieście jest szeroka i głęboka.
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 21

```text
 Rzeka w naszym mieście jest szeroka i głępka.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 21

```text
 Rzeka w naszym mieście jest szeroka i głemboka.
```

### pl_jezyk-17 (zdanie, trudność 2)

**Polecenie:** Popraw błąd w zdaniu i napisz całe zdanie poprawnie: Włanczam komputer zawsze o ósmej rano.

**Wzorzec:** Włączam komputer zawsze o ósmej rano.

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: limit, tokenów: 48

```text

Dzień dobry, Pani Ewo, bardzo dziękuję za pożyczenie komputera, bardzo mi pomogła przy malowaniu. Oddam ją jutro rano, około ósmej. Pozdrawiam serdecznie, Adam z drugiego piętra.

Polecenie
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 20

```text

Włanczam komputer zawsze o ósmej rano.
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 14

```text
Włanczam komputer o ósmej rano.
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 15

```text
Włanczam komputer zawsze o ósmej rano.
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 24

```text
 Włanczam komputer zawsze o ósmej rano.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 24

```text
 Włanczam komputer zawsze o ósmej rano.
```

### pl_jezyk-18 (zdanie, trudność 2)

**Polecenie:** Popraw błąd w zdaniu i napisz całe zdanie poprawnie: Spotkałem się z dwoma koleżankami w kawiarni.

**Wzorzec:** Spotkałem się z dwiema koleżankami w kawiarni.

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 19

```text
 Spotkałem się z dwoma koleżankami w kawiarni.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 19

```text
 Spotkałem się z dwoma koleżankami w kawiarni.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 17

```text
Spotkałem się z dwiema koleżankami w kawiarni.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 17

```text
Spotkałem się z dwiema koleżankami w kawiarni.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: eos, tokenów: 19

```text
 Spotkałem się z dwiema koleżankami w kawiarni.
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: eos, tokenów: 19

```text
 Spotkałem się z dwiema koleżankami w kawiarni.
```

### pl_jezyk-19 (zdanie, trudność 2)

**Polecenie:** Popraw błąd w zdaniu i napisz całe zdanie poprawnie: Ten problem jest bardziej trudniejszy, niż myślałem.

**Wzorzec:** Ten problem jest trudniejszy, niż myślałem.

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 18

```text

Ten problem jest bardziej skomplikowany, niż myślałem.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 18

```text

Ten problem jest bardziej skomplikowany, niż myślałem.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 15

```text
Ten problem jest bardziej trudny, niż myślałem.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 15

```text
Ten problem jest trudniejszy, niż myślałem.
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 15

```text
 Ten problem jest trudniejszy, niż sądziłem.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 24

```text
 Ten problem jest bardziej trudniejszy, niż myślałem.
```

### pl_jezyk-20 (zdanie, trudność 2)

**Polecenie:** Popraw błąd w zdaniu i napisz całe zdanie poprawnie: Wziąść udział w konkursie może każdy uczeń naszej szkoły.

**Wzorzec:** Wziąć udział w konkursie może każdy uczeń naszej szkoły.

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 15

```text

Każdy uczeń może wziąć udział w konkursie.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 17

```text

Każdy uczeń naszej szkoły może wziąć udział w konkursie.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 19

```text

Wziąć udział w konkursie może każdy uczeń naszej szkoły.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 17

```text
Wziąć udział w konkursie może każdy uczeń naszej szkoły.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 27

```text
 Wziąć udział w konkursie może każdy uczeń naszej szkoły.
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: eos, tokenów: 21

```text
 Wziąć udział w konkursie może każdy uczeń naszej szkoły.
```

### pl_jezyk-21 (zdanie, trudność 3)

**Polecenie:** Popraw błąd w zdaniu i napisz całe zdanie poprawnie: Mój brat mówił prawdę, ale nikt go nie wierzył.

**Wzorzec:** Mój brat mówił prawdę, ale nikt mu nie wierzył.

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 31

```text

Dzień dobry, Panie Piotrze, tak, to prawda, ale nie było żadnych przesłanek, że brat kłamie.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 18

```text
 Mój brat mówił prawdę, ale nikt go nie wierzył.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 17

```text
Mój brat mówił prawdę, ale nikt mu nie wierzył.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 17

```text
Mój brat mówił prawdę, ale nikt mu nie wierzył.
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 20

```text
 Mój brat mówił prawdę, ale nikt go nie wierzył.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 26

```text
 Mój brat mówił prawdę, ale nikt go nie wierzył.
```

### pl_jezyk-22 (zdanie, trudność 3)

**Polecenie:** Popraw błąd w zdaniu i napisz całe zdanie poprawnie: Na zebranie przyszło pięciu nauczycielek i dwóch dyrektorów.

**Wzorzec:** Na zebranie przyszło pięć nauczycielek i dwóch dyrektorów.

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 18

```text
 Na zebranie przyszło pięciu nauczycielek i dwóch dyrektorów.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 19

```text

Na zebranie przyszło pięciu nauczycielek i dwóch dyrektorów.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 18

```text
Na zebranie przyszło pięć nauczycielek i dwóch dyrektorów.
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 18

```text
Na zebranie przyszło pięciu nauczycielek i dwóch dyrektorów.
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 27

```text
 Na zebranie przyszło pięć nauczycieli i dwóch dyrektorów.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 28

```text
 Na zebranie przyszło pięciu nauczycielek i dwóch dyrektorów.
```

### pl_jezyk-23 (zdanie, trudność 3)

**Polecenie:** Popraw błąd w zdaniu i napisz całe zdanie poprawnie: Ta decyzja odegrała ważną funkcję w historii firmy.

**Wzorzec:** Ta decyzja odegrała ważną rolę w historii firmy.

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 17

```text
 Ta decyzja odegrała ważną rolę w historii firmy.
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 17

```text
 Ta decyzja odegrała ważną rolę w historii firmy.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 16

```text
Ta decyzja odegrała ważną rolę w historii firmy.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 16

```text
Ta decyzja odegrała ważną rolę w historii firmy.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 24

```text
 Ta decyzja odegrała ważną rolę w historii firmy.
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 24

```text
 Ta decyzja odegrała ważną rolę w historii firmy.
```

### pl_jezyk-24 (zdanie, trudność 3)

**Polecenie:** Popraw błąd w zdaniu i napisz całe zdanie poprawnie: W każdym bądź razie spotkanie odbędzie się w piątek.

**Wzorzec:** W każdym razie spotkanie odbędzie się w piątek.

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 17

```text

W każdym bądź razie spotkanie odbędzie się w piątek.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: limit, tokenów: 48

```text

Dzień dobry, Pani Ewo, bardzo dziękuję za pożyczenie drabiny, bardzo mi pomogła przy malowaniu. Oddam ją jutro rano, około ósmej. Pozdrawiam serdecznie, Adam z drugiego piętra.

Po
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 16

```text
W każdym bądź razie spotkanie odbędzie się w piątek.
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 16

```text
W każdym bądź razie spotkanie odbędzie się w piątek.
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 23

```text
 W każdym bądź razie spotkanie odbędzie się w piątek.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: eos, tokenów: 23

```text
 W każdym bądź razie spotkanie odbędzie się w piątek.
```

### pl_jezyk-25 (otwarte, trudność 1)

**Polecenie:** Napisz krótkie ogłoszenie (3-4 zdania) o zgubionym czarnym plecaku. Plecak zginął wczoraj na przystanku autobusowym przy ulicy Lipowej. Poproś o kontakt pod numerem 600 123 456.

**Wzorzec:** Zgubiłem czarny plecak! Wczoraj po południu zostawiłem go na przystanku autobusowym przy ulicy Lipowej. W środku były zeszyty i książki, które są dla mnie bardzo ważne. Uczciwego znalazcę proszę o kontakt pod numerem 600 123 456.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 37

```text

Cześć, zgubiłem wczoraj czarny plecak. Plecak jest pod opieką policji, a ja proszę o kontakt pod numerem 600 123 456.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 28

```text

Dzień dobry, zgubiłem wczoraj czarnego plecaka. Proszę o kontakt pod numerem 600 123 456.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 69

```text

Uwaga! Czarny plecak, który zaginął wczoraj na przystanku autobusowym przy ulicy Lipowej, jest poszukiwany. Jeśli go znalazłeś, skontaktuj się pod numerem 600 123 456. Przepraszamy za wszelkie niedogodności i dziękujemy za pomoc.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 47

```text

Zgubiłem czarny plecak na przystanku autobusowym przy ulicy Lipowej. Jeśli ktoś go widział, proszę o kontakt pod numerem 600 123 456.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 6

```text
(pusta odpowiedź)```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 46

```text
 Plecak zginął wczoraj na przystanku autobusowym przy ulicy Lipowej. Proszę o kontakt pod numerem 600 123 456.
```

### pl_jezyk-26 (otwarte, trudność 1)

**Polecenie:** Napisz krótką wiadomość do współlokatora: wrócisz dziś późno, około 22:00, i prosisz, żeby wyjął pranie z pralki i je rozwiesił.

**Wzorzec:** Cześć Kuba, wrócę dziś późno, pewnie około 22:00. Mam do Ciebie prośbę: wyjmij, proszę, pranie z pralki i rozwieś je na suszarce, żeby się nie pogniotło. Dzięki wielkie, odwdzięczę się!

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 54

```text

Witam serdecznie,

Mam nadzieję, że będzie Pani w stanie przyjechać dziś około godziny 15:00.

Na pewno będzie Pani zadowolona,

pozdrawiam,

Andrzej z drugiego piętra.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: limit, tokenów: 400

```text

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,

Dzień dobry,
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 53

```text

Hej, Łukasz, wróciłem trochę później niż myślałem, około 22:00. Chciałbym, żebyś wyjął pranie z pralki i je rozwiesił, bo nie mam czasu. Pozdrawiam, Kuba.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 57

```text

Dzień dobry, Piotrze, bardzo przepraszam, że nie wrócę dziś o 22:00, ale mam dużo pracy. Proszę, żebyś wyjął pranie z pralki i je rozwiesił. Pozdrawiam, Adam z drugiego piętra.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: eos, tokenów: 35

```text
 Wrócisz dziś późno, około 22:00. Proszę wyjął pranie z pralki i je rozwiesił.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: eos, tokenów: 37

```text
 Wrócisz późno, około 22:00, i proszę, żeby wyjął pranie z pralki i je rozwiesił.
```

### pl_jezyk-27 (otwarte, trudność 2)

**Polecenie:** Napisz krótki e-mail do kierowniczki z prośbą o jeden dzień urlopu w najbliższy piątek. Podaj powód (wizyta u lekarza) i napisz, kto w tym dniu zajmie się pilnymi sprawami.

**Wzorzec:** Temat: Prośba o urlop w piątek  
  
Dzień dobry, Pani Kierownik,  
  
zwracam się z prośbą o udzielenie mi jednego dnia urlopu wypoczynkowego w najbliższy piątek. Na ten dzień mam wyznaczoną wizytę u lekarza, której nie mogę przełożyć. Pilnymi sprawami zajmie się w tym czasie Tomasz Nowak, z którym omówiłem już bieżące zadania. W czwartek przekażę mu też listę otwartych tematów.  
  
Z wyrazami szacunku  
Piotr Zieliński

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 57

```text

Dzień dobry, Pani Justyno, mam do Pani bardzo ważną sprawę. W tym tygodniu muszę pojechać na badania, a w tym roku planuję w czerwcu, więc bardzo proszę o dzień wolny w piątek. Pozdrawiam, Adam z drugiego piętra.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 51

```text

Dzień dobry, Pani Ewo, bardzo dziękuję za pożyczenie drabiny, bardzo mi pomogła przy malowaniu. Oddam ją jutro rano, około ósmej. Pozdrawiam serdecznie, Adam z drugiego piętra.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 122

```text

Szanowna Pani Dyrektor,
Zwracam się z prośbą o jeden dzień urlopu w najbliższy piątek, tj. 16.04.2023 r. Jest to dla mnie niezwykle ważny dzień, ponieważ planuję wizytę u lekarza. W tym czasie chciałabym, aby moja siostra, która aktualnie zajmuje się pilnymi sprawami w biurze, przejęła moje obowiązki. Jestem pewna, że poradzi sobie z tym zadaniem, a ja będę mogła skupić się na moim zdrowiu.
Z góry dziękuję za zrozumienie i udzielenie mi urlopu.
Z poważaniem,
Adam Kowalski
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 108

```text

Szanowna Pani Dyrektor,
Zwracam się z prośbą o udzielenie mi jednego dnia urlopu w najbliższy piątek, 15 maja. Powodem jest konieczność wizyty u lekarza, która wymaga mojej obecności. W tym czasie, w zastępstwie za mnie, proszę o pilne załatwienie następujących spraw:
1. Przekazanie dokumentów do księgowości.
2. Przygotowanie raportu kwartalnego.
3. Spotkanie z klientem w sprawie negocjacji cenowych.
Z poważaniem,
Adam Kowalski
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 64

```text
 Staję się w klinice, zanim wejdzę, zapewnia, że nie będę miał problemów z bólem głowy. Przyjmuję w dniu 18.5. Dziękuję za wyjaśnienie.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 89

```text
 Dzień dobry, Pani Ewo, bardzo dziękuję za prośbę o jeden dzień urlopu w najbliższy piątek. Proszę o jedno dzień urlopu w najbliższy piątek. Proszę o pilne sprawy, które w tym dniu zajmie się Pani Ewo.
```

### pl_jezyk-28 (otwarte, trudność 2)

**Polecenie:** Napisz opis produktu do sklepu internetowego (3-5 zdań): drewniany stołek kuchenny z drewna bukowego, wysokość 45 cm, udźwig do 120 kg.

**Wzorzec:** Drewniany stołek kuchenny wykonany z litego drewna bukowego to solidny i praktyczny mebel do każdej kuchni. Ma 45 cm wysokości, dzięki czemu sprawdzi się przy stole i jako podręczny podest. Wytrzymała konstrukcja udźwignie do 120 kg. Naturalny kolor drewna pasuje zarówno do nowoczesnych, jak i tradycyjnych wnętrz.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 33

```text

Paweł, drewniany stołek kuchenny z drewna bukowego, wysokość 45 cm, udźwig do 120 kg.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 21

```text

Dzień dobry,

Proszę o przesłanie produktu do sklepu internetowego.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 142

```text

Drewniany stołek kuchenny z drewna bukowego, o wysokości 45 cm i udźwigu do 120 kg, to doskonałe rozwiązanie dla osób ceniących trwałość i wygodę. Wykonany z wysokiej jakości drewna bukowego, gwarantuje nie tylko wytrzymałość, ale także naturalny wygląd i komfort użytkowania. Dzięki swojemu stabilnemu i solidnemu wykonaniu, stołek ten doskonale sprawdza się zarówno w codziennym użytkowaniu, jak i podczas spotkań towarzyskich. Jego ergonomiczny kształt zapewnia wygodę podczas siedzenia, a możliwość regulacji wysokości umożliwia dostosowanie go do indywidualnych potrzeb. To idealne rozwiązanie dla osób poszukujących funkcjonalnego i trwałego mebla do swojej kuchni.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 96

```text

Drewniany stołek kuchenny z drewna bukowego, o wysokości 45 cm, to praktyczny i solidny mebel, który doskonale sprawdzi się w każdej kuchni. Jego udźwig do 120 kg gwarantuje bezpieczeństwo podczas użytkowania, a drewniany materiał zapewnia trwałość i odporność na uszkodzenia. Stołek jest łatwy w montażu i utrzymaniu czystości, co czyni go idealnym wyborem dla osób ceniących funkcjonalność i estetykę.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 39

```text
 Drewniany stołek kuchenny z drewna bukowego, wysokość 45 cm, udźywanie do 120 kg.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 38

```text
 Drewniany stołek kuchenny z drewna bukowego, wysokość 45 cm, udźwig do 120 kg.
```

### pl_jezyk-29 (otwarte, trudność 3)

**Polecenie:** Napisz ogłoszenie zarządcy budynku dla mieszkańców (4-6 zdań): w środę w godzinach 9:00-15:00 nie będzie ciepłej wody z powodu wymiany rur w piwnicy. Poproś o przygotowanie zapasu wody i przeproś za utrudnienia.

**Wzorzec:** Szanowni Mieszkańcy,  
uprzejmie informujemy, że w środę w godzinach 9:00-15:00 w budynku nie będzie ciepłej wody. Przerwa jest konieczna z powodu wymiany rur w piwnicy. Prosimy o wcześniejsze przygotowanie zapasu wody na ten czas. Za utrudnienia serdecznie przepraszamy i dziękujemy za wyrozumiałość.  
Zarządca budynku

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 69

```text

Dzień dobry, Pani Marleno, bardzo przepraszam za utrudnienia, ale wczorajsze prace przy instalacji ciepłej wody nie były zakończone, dlatego w środę, w godzinach 9:00-15:00 nie będzie ciepłej wody z powodu wymiany rur w piwnicy. Bardzo przepraszam za utrudnienia.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 51

```text

Dzień dobry, Pani Ewo, bardzo dziękuję za pożyczenie drabiny, bardzo mi pomogła przy malowaniu. Oddam ją jutro rano, około ósmej. Pozdrawiam serdecznie, Adam z drugiego piętra.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 56

```text

Zarządca budynku informuje mieszkańców, że w środę w godzinach 9:00-15:00 nie będzie ciepłej wody z powodu wymiany rur w piwnicy. Prosimy o przygotowanie zapasu wody oraz przeproszenie za utrudnienia.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 55

```text

Zarządca budynku informuje, że w środę w godzinach 9:00-15:00 nie będzie ciepłej wody z powodu wymiany rur w piwnicy. Prosimy o przygotowanie zapasu wody i przeproszenie za utrudnienia.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 62

```text
 W środę od 9:00 do 15:00 nie będzie ciepłej wody z powodu wymiany rur w piwnicy. Proszę o przygotowanie zapasu wody i przeproś za utrudnienia.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 64

```text
 W środę w godzinach 9:00-15:00 nie będzie ciepłej wody z powodu wymiany rur w piwnicy. Poproś o przygotowanie zapasu wody i przeproś za utrudnienia.
```

### pl_jezyk-30 (otwarte, trudność 3)

**Polecenie:** Napisz krótką notatkę ze spotkania zespołu. Ustalenia: termin oddania raportu przesunięto na koniec miesiąca, Marta przygotuje prezentację dla klienta, następne spotkanie odbędzie się w poniedziałek o 10:00.

**Wzorzec:** Notatka ze spotkania zespołu  
  
Na dzisiejszym spotkaniu ustalono, co następuje:  
1. Termin oddania raportu przesunięto na koniec miesiąca.  
2. Marta przygotuje prezentację dla klienta.  
3. Następne spotkanie odbędzie się w poniedziałek o godzinie 10:00.  
  
Proszę o zgłaszanie uwag do tych ustaleń przed kolejnym spotkaniem.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 50

```text

Dzień dobry, Pani Ewo, dziękuję za pożyczenie drabiny, bardzo mi pomogła przy malowaniu. Oddam ją jutro rano, około ósmej. Pozdrawiam serdecznie, Adam z drugiego piętra.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 45

```text

Dzień dobry,

Marta,

Bardzo dziękuję za pożyczenie drabiny, bardzo mi pomogła przy malowaniu. Oddam ją jutro rano, około ósmej.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: eos, tokenów: 62

```text

Zespół przyjął następujące ustalenia:
- Termin oddania raportu przesunięto na koniec miesiąca,
- Marta przygotuje prezentację dla klienta,
- Kolejne spotkanie odbędzie się w poniedziałek o 10:00.
Na spotkaniu ustaliliśmy również, że wszystkie szczegóły zostaną omówione na następnym spotkaniu.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 55

```text

Zespół spotkał się w piątek o 14:00. Ustalono, że raport zostanie oddany do końca miesiąca. Marta przygotuje prezentację dla klienta. Kolejne spotkanie odbędzie się w poniedziałek o 10:00.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 57

```text
 Termin oddania raportu przesunięty na koniec miesiąca, Marta przygotuje prezentację dla klienta, następne spotkanie odbędzie się w poniedziałek o 10:00.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 57

```text
 Termin oddania raportu przesunięty na koniec miesiąca, Marta przygotuje prezentację dla klienta, następne spotkanie odbędzie się w poniedziałek o 10:00.
```

## pl_wiedza

### pl_wiedza-01 (krotka, trudność 1)

**Polecenie:** Jak nazywa się najdłuższa rzeka w Polsce?

**Wzorzec:** Wisła

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Wisła
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Wisła
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Wisła
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Wisła
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Odna
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Odra
```

### pl_wiedza-02 (krotka, trudność 1)

**Polecenie:** W którym mieście znajduje się Zamek Królewski na Wawelu?

**Wzorzec:** Kraków

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Kraków
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Kraków
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Kraków
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Kraków
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Kraków
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Kraków
```

### pl_wiedza-03 (krotka, trudność 1)

**Polecenie:** Kto napisał epopeję „Pan Tadeusz”?

**Wzorzec:** Adam Mickiewicz

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 10

```text
 Juliusz Słowacki
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Adam Mickiewicz
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Adam Mickiewicz
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Adam Mickiewicz
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Adam Mickiewicz
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Adam Mickiewicz
```

### pl_wiedza-04 (krotka, trudność 1)

**Polecenie:** Jak nazywa się najwyższy szczyt w Polsce?

**Wzorzec:** Rysy

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Górą
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Tatry
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
Śnieżnik
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
Giewont
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 11

```text
 Wyspa Górna
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 10

```text
 Śnieżka
```

### pl_wiedza-05 (krotka, trudność 1)

**Polecenie:** Nad jakim morzem leży Polska?

**Wzorzec:** Morze Bałtyckie

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Bałtyckie
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 Morze Bałtyckie
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
Bałtykiem
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
Morze Bałtyckie
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 13

```text
 Morze Bałtyckie
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 13

```text
 Morze Bałtyckie
```

### pl_wiedza-06 (krotka, trudność 1)

**Polecenie:** Jak nazywa się kompozytor urodzony w Żelazowej Woli, autor polonezów i mazurków na fortepian?

**Wzorzec:** Fryderyk Chopin

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 11

```text
 Feliks Nowowiejski
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 13

```text
 Fryderyk Chopin
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
Fryderyk Chopin
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
Fryderyk Chopin
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 12

```text
 Stanisław Moniuszko
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 10

```text
 Józef Elsner
```

### pl_wiedza-07 (krotka, trudność 1)

**Polecenie:** Jak nazywa się waluta, którą płaci się w polskich sklepach?

**Wzorzec:** złoty

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Złotówka
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Złotówka
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Złoty
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Złoty
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 złoty
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 złoty
```

### pl_wiedza-08 (krotka, trudność 1)

**Polecenie:** W którym roku odbył się chrzest Mieszka I?

**Wzorzec:** 966

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 966
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 966
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 10

```text
966
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 10

```text
966
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 1583
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 1526
```

### pl_wiedza-09 (krotka, trudność 1)

**Polecenie:** Która uczona urodzona w Warszawie jako pierwsza osoba w historii dostała Nagrodę Nobla dwa razy?

**Wzorzec:** Maria Skłodowska-Curie

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 14

```text
 Maria Skłodowska-Curie
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 14

```text
 Maria Skłodowska-Curie
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 14

```text
Maria Skłodowska-Curie
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 14

```text
Maria Skłodowska-Curie
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Maria Curie
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 12

```text
 Czesław Miłosz
```

### pl_wiedza-10 (krotka, trudność 1)

**Polecenie:** W jakich górach leży Kasprowy Wierch?

**Wzorzec:** Tatry

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Tatry
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Tatry
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Tatry
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Tatry
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 12

```text
 Góry Północne
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Węgry
```

### pl_wiedza-11 (krotka, trudność 2)

**Polecenie:** Kto był pierwszym koronowanym królem Polski?

**Wzorzec:** Bolesław Chrobry

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Mieszko I
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Mieszko I
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
Bolesław Chrobry
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
Bolesław Chrobry
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 11

```text
 Mikołaj I
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 11

```text
 Mikołaj I
```

### pl_wiedza-12 (krotka, trudność 2)

**Polecenie:** W którym roku Polska odzyskała niepodległość po 123 latach zaborów?

**Wzorzec:** 1918

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 1918
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 1918
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 12

```text
1918 rok
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
1918
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 1918
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 1809
```

### pl_wiedza-13 (krotka, trudność 2)

**Polecenie:** Kto jest autorem powieści „Quo vadis”?

**Wzorzec:** Henryk Sienkiewicz

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 Henryk Sienkiewicz
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 Henryk Sienkiewicz
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
Henryk Sienkiewicz
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
Henryk Sienkiewicz
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 12

```text
 Henryk Sienkiewicz
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 12

```text
 Henryk Sienkiewicz
```

### pl_wiedza-14 (krotka, trudność 2)

**Polecenie:** W stoczni którego miasta w sierpniu 1980 roku wybuchł strajk, z którego narodziła się „Solidarność”?

**Wzorzec:** Gdańsk

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Gdańsk
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Gdańsk
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Gdańsk
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Gdańsk
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Gdańsk
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Gdańsk
```

### pl_wiedza-15 (krotka, trudność 2)

**Polecenie:** Nad jaką rzeką leży Wrocław?

**Wzorzec:** Odra

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Odra
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Odra
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Odrą
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Odra
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Odwańska
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Odr
```

### pl_wiedza-16 (krotka, trudność 2)

**Polecenie:** Jak nazywa się największe pod względem powierzchni jezioro w Polsce?

**Wzorzec:** Śniardwy

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Białe
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 15

```text
 Małe Jezioro Lednickie
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 12

```text
Jezioro Łebsko
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 12

```text
Jezioro Śniardwy
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 13

```text
 Jezioro Biała.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 14

```text
 Jezioro Biebrza
```

### pl_wiedza-17 (krotka, trudność 2)

**Polecenie:** Kto namalował obraz „Bitwa pod Grunwaldem”?

**Wzorzec:** Jan Matejko

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 10

```text
 Jan Matejko
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 10

```text
 Jan Matejko
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 10

```text
Jan Matejko
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 10

```text
Jan Matejko
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 10

```text
 Jan Matejko
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 10

```text
 Jan Matejko
```

### pl_wiedza-18 (krotka, trudność 2)

**Polecenie:** W którym roku wojska polsko-litewskie pokonały Krzyżaków pod Grunwaldem?

**Wzorzec:** 1410

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 1410
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 1410
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
1410
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
1410
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 12

```text
 14 lipca 1410
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 1410
```

### pl_wiedza-19 (krotka, trudność 2)

**Polecenie:** W którym mieście urodził się Mikołaj Kopernik?

**Wzorzec:** Toruń

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Toruniu
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Toruniu
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
Kraków
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
Kraków
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 11

```text
 Włocławek
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Toruń
```

### pl_wiedza-20 (krotka, trudność 2)

**Polecenie:** Który polski noblista jest autorem powieści „Chłopi”?

**Wzorzec:** Władysław Reymont

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 11

```text
 Henryk Sienkiewicz
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 10

```text
 Władysław Reymont
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 10

```text
Władysław Stanisław Reymont
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
Władysław Reymont
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 11

```text
 Henryk Wajda
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Adam Mickiewicz
```

### pl_wiedza-21 (krotka, trudność 3)

**Polecenie:** Pod jakim pseudonimem literackim pisał Aleksander Głowacki?

**Wzorzec:** Bolesław Prus

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 11

```text
 Aleksander Głowacki
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 11

```text
 Aleksander Głowacki
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Bolesław Prus
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 10

```text
Stefan Żeromski
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 Bolesław Prus
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 12

```text
 Aleksander Głowacki
```

### pl_wiedza-22 (krotka, trudność 3)

**Polecenie:** W którym roku Sejm Wielki uchwalił Konstytucję 3 maja?

**Wzorzec:** 1791

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 1791
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 1791
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
1791
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
1791
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 12

```text
 3 maja 1791
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 13

```text
 3 maja 1791 roku
```

### pl_wiedza-23 (krotka, trudność 3)

**Polecenie:** Jakie miasto jest stolicą województwa podlaskiego?

**Wzorzec:** Białystok

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Suwałki
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Białystok
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Białystok
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Białystok
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Kielce
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 10

```text
 Gdynia
```

### pl_wiedza-24 (krotka, trudność 3)

**Polecenie:** Kto skomponował operę „Halka”?

**Wzorzec:** Stanisław Moniuszko

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 10

```text
 Stanisław Moniuszko
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 10

```text
 Stanisław Moniuszko
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 10

```text
Stanisław Moniuszko
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 10

```text
Stanisław Moniuszko
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 12

```text
 Stanisław Wyspiański
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 12

```text
 Stanisław Moniuszko
```

### pl_wiedza-25 (krotka, trudność 3)

**Polecenie:** W którym roku zawarto unię lubelską, tworzącą Rzeczpospolitą Obojga Narodów?

**Wzorzec:** 1569

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 1569
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 1569
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
1569
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
1569
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 14

```text
 1 września 1918 r.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 13

```text
 23 września 1918 roku
```

### pl_wiedza-26 (krotka, trudność 3)

**Polecenie:** Która polska poetka otrzymała literacką Nagrodę Nobla w 1996 roku?

**Wzorzec:** Wisława Szymborska

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 Wisława Szymborska
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 Wisława Szymborska
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
Wisława Szymborska
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
Wisława Szymborska
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 12

```text
 Czesława Wolela
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 12

```text
 Czesław Miłosz
```

### pl_wiedza-27 (krotka, trudność 3)

**Polecenie:** Jak nazywał się ostatni król Rzeczypospolitej Obojga Narodów?

**Wzorzec:** Stanisław August Poniatowski

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 Stanisław August Poniatowski
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 Stanisław August Poniatowski
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
Stanisław August Poniatowski
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
Stanisław August Poniatowski
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Michał I
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 11

```text
 Jan III Sobieski
```

### pl_wiedza-28 (krotka, trudność 3)

**Polecenie:** Który polski król dowodził wojskami chrześcijańskimi w bitwie pod Wiedniem w 1683 roku?

**Wzorzec:** Jan III Sobieski

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 10

```text
 Władysław IV Waza
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 Jan III Sobieski
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 10

```text
Jan III Sobieski
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 10

```text
Jan III Sobieski
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 Jan III Sobieski
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 Jan III Sobieski
```

### pl_wiedza-29 (krotka, trudność 3)

**Polecenie:** Jak nazywa się najwyższy szczyt Sudetów?

**Wzorzec:** Śnieżka

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 10

```text
 Góra Śnieżka
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Śnieżka
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
Śnieżnik
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Śnieżka
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Montmartre
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 12

```text
 Pik Kociewski
```

### pl_wiedza-30 (krotka, trudność 3)

**Polecenie:** Nad jaką rzeką leży Poznań?

**Wzorzec:** Warta

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Odra
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Odra
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Warta
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Warta
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 18

```text
 Od Noga, aż po Św. Piotr
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Odmowa
```

## wiedza_ogolna

### wiedza_ogolna-01 (krotka, trudność 1)

**Polecenie:** Która planeta Układu Słonecznego jest największa?

**Wzorzec:** Jowisz

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Mars
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Merkury
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Jowisz
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Jowisz
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Saturn
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Jowisz
```

### wiedza_ogolna-02 (krotka, trudność 1)

**Polecenie:** Jaki gaz rośliny pobierają z powietrza podczas fotosyntezy?

**Wzorzec:** dwutlenek węgla

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 CO2
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 CO2
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
dwutlenek węgla
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
dwutlenek węgla
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 13

```text
 dwutlenek węgla
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 13

```text
 dwutlenek węgla
```

### wiedza_ogolna-03 (krotka, trudność 1)

**Polecenie:** Ile nóg ma pająk?

**Wzorzec:** osiem

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 6 nóg
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 8
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
8
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
cztery
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 cztery
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 8
```

### wiedza_ogolna-04 (krotka, trudność 1)

**Polecenie:** Na którym kontynencie leży większa część Egiptu?

**Wzorzec:** Afryka

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Afryka
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Afryka
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Afryka
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Afryka
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Afryka
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Afryka
```

### wiedza_ogolna-05 (krotka, trudność 1)

**Polecenie:** Jaki jest wzór chemiczny wody?

**Wzorzec:** H2O

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 H2O
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 H2O
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
H2 O
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
H2O
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 10

```text
 H₂O
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 H2O
```

### wiedza_ogolna-06 (krotka, trudność 1)

**Polecenie:** Która planeta krąży najbliżej Słońca?

**Wzorzec:** Merkury

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Merkury
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Merkury
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Merkury
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Merkury
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Merkur
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Merkury
```

### wiedza_ogolna-07 (krotka, trudność 1)

**Polecenie:** Jakie miasto jest stolicą Francji?

**Wzorzec:** Paryż

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Paryż
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Paryż
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Paryż
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Paryż
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Paryż
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Paryż
```

### wiedza_ogolna-08 (krotka, trudność 1)

**Polecenie:** Przy ilu stopniach Celsjusza wrze czysta woda pod ciśnieniem normalnym?

**Wzorzec:** 100

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 20,7
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 0,5
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 10

```text
100
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 12

```text
100 stopni Celsjusza
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 100
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 100
```

### wiedza_ogolna-09 (krotka, trudność 1)

**Polecenie:** Jak nazywa się największy ocean na Ziemi?

**Wzorzec:** Ocean Spokojny

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Pacyfik
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Pacyfik
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Pacyfik
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 10

```text
Ocean Spokojny
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 10

```text
 Ocean Atlantycki
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Atlantyk
```

### wiedza_ogolna-10 (krotka, trudność 1)

**Polecenie:** Który narząd pompuje krew w organizmie człowieka?

**Wzorzec:** serce

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 krew
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 serce
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
serce
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
serce
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 10

```text
 wątroba
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 serce
```

### wiedza_ogolna-11 (krotka, trudność 2)

**Polecenie:** Kto sformułował trzy zasady dynamiki i prawo powszechnego ciążenia?

**Wzorzec:** Isaac Newton

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Isaac Newton
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Isaac Newton
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 10

```text
Isaac Newton
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 10

```text
Isaac Newton
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Galileo Galilei
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Newton
```

### wiedza_ogolna-12 (krotka, trudność 2)

**Polecenie:** Jakie miasto jest stolicą Japonii?

**Wzorzec:** Tokio

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Tokio
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Tokio
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Tokio
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Tokio
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Tokio
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Tokio
```

### wiedza_ogolna-13 (krotka, trudność 2)

**Polecenie:** Jaki pierwiastek chemiczny oznacza się symbolem Fe?

**Wzorzec:** żelazo

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Fe
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Fe
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
żelazo
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
żelazo
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 12

```text
 Fe (kobalt)
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 żelazo
```

### wiedza_ogolna-14 (krotka, trudność 2)

**Polecenie:** W którym roku wyprawa Krzysztofa Kolumba po raz pierwszy dotarła do Ameryki?

**Wzorzec:** 1492

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 1534
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 1492
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
1492
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
1492
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 w 1492 roku
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 1492
```

### wiedza_ogolna-15 (krotka, trudność 2)

**Polecenie:** Jak nazywa się jednostka natężenia prądu elektrycznego w układzie SI?

**Wzorzec:** amper

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 amper
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 amper
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
amper
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
amper
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 kVA
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Ampere
```

### wiedza_ogolna-16 (krotka, trudność 2)

**Polecenie:** Jak nazywa się najwyższa góra na Ziemi?

**Wzorzec:** Mount Everest

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 10

```text
 Mount Everest
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 10

```text
 Mount Everest
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 10

```text
Mount Everest
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 10

```text
Mount Everest
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 15

```text
 Kilkudziesięciowaty
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Mount Everest
```

### wiedza_ogolna-17 (krotka, trudność 2)

**Polecenie:** W której części komórki zachodzi oddychanie komórkowe dostarczające większość energii w postaci ATP?

**Wzorzec:** mitochondrium

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 10

```text
 w mitochondriach
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 11

```text
 w cytoplazmie
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 10

```text
mitochondria
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 10

```text
mitochondrium
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 mitochondria
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 mitochondrium
```

### wiedza_ogolna-18 (krotka, trudność 2)

**Polecenie:** Który europejski kraj na mapie ma kształt buta?

**Wzorzec:** Włochy

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Szwajcaria
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Francja
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Włochy
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
Francja
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 10

```text
 Bułgaria
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Niemcy
```

### wiedza_ogolna-19 (krotka, trudność 2)

**Polecenie:** Kto stworzył szczególną teorię względności?

**Wzorzec:** Albert Einstein

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Albert Einstein
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Albert Einstein
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
Albert Einstein
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
Albert Einstein
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Einsteina
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Einsteina
```

### wiedza_ogolna-20 (krotka, trudność 2)

**Polecenie:** Ile chromosomów ma typowa komórka somatyczna człowieka?

**Wzorzec:** 46

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 23
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 23
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
46
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
46
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 46
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 46
```

### wiedza_ogolna-21 (krotka, trudność 3)

**Polecenie:** Kto jest autorem książki „O powstawaniu gatunków”?

**Wzorzec:** Karol Darwin

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Karol Darwin
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Darwin
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
Karol Darwin
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
Karol Darwin
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Charles Darwin
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Charles Darwin
```

### wiedza_ogolna-22 (krotka, trudność 3)

**Polecenie:** W którym roku upadł mur berliński?

**Wzorzec:** 1989

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 1961
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 1989
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
1989
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
1989
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 1945
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 1945
```

### wiedza_ogolna-23 (krotka, trudność 3)

**Polecenie:** Jakie miasto jest stolicą Australii?

**Wzorzec:** Canberra

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Sydney
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Sydney
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
Canberra
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
Canberra
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Canberra
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Canberra
```

### wiedza_ogolna-24 (krotka, trudność 3)

**Polecenie:** Który gaz stanowi największą część objętości atmosfery Ziemi?

**Wzorzec:** azot

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 tlen
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 azot
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
azot
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
azot
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 13

```text
 dwutlenek węgla
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 azot
```

### wiedza_ogolna-25 (krotka, trudność 3)

**Polecenie:** Jak nazywa się podział komórki, w wyniku którego powstają gamety o połowie liczby chromosomów?

**Wzorzec:** mejoza

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 meiosis
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 10

```text
 haploidalna
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
mitoza
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
mejoza
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 mejoza
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 mejoza
```

### wiedza_ogolna-26 (krotka, trudność 3)

**Polecenie:** Który pierwiastek chemiczny ma liczbę atomową 1?

**Wzorzec:** wodór

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 sód
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 sód
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
hel
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
hel
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 wodór
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 wodór
```

### wiedza_ogolna-27 (krotka, trudność 3)

**Polecenie:** Kto jako pierwszy człowiek odbył lot w przestrzeń kosmiczną?

**Wzorzec:** Jurij Gagarin

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 Jurij Gagarin
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 Jurij Gagarin
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
Jurij Gagarin
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
Jurij Gagarin
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 Juri Gagarin
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 Juri Gagarin
```

### wiedza_ogolna-28 (krotka, trudność 3)

**Polecenie:** W którym roku paryżanie zdobyli Bastylię, rozpoczynając rewolucję francuską?

**Wzorzec:** 1789

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 w 1789 r.
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 1789
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
1789
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
1789
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 w 1789 roku
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 1789
```

### wiedza_ogolna-29 (krotka, trudność 3)

**Polecenie:** Jak nazywa się cieśnina oddzielająca Hiszpanię od Maroka i łącząca Morze Śródziemne z Atlantykiem?

**Wzorzec:** Cieśnina Gibraltarska

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 11

```text
 Kanał La Mancha
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 14

```text
 Cieśnina Gibraltarska
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
Gibraltarska
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 10

```text
Gibraltar
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 12

```text
 Cieśnina Gibraltar
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 Gibraltarska
```

### wiedza_ogolna-30 (krotka, trudność 3)

**Polecenie:** Który metal jest cieczą w temperaturze pokojowej?

**Wzorzec:** rtęć

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 bor
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 sód
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
Wrzątek
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
woda
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 woda
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 wodór
```

## rozumowanie

### rozumowanie-01 (krotka, trudność 1)

**Polecenie:** Wszystkie jabłonie w sadzie pana Zenona kwitną w maju. Drzewo przy furtce to jabłoń z sadu pana Zenona. Czy drzewo przy furtce kwitnie w maju? Odpowiedz „tak” albo „nie”.

**Wzorzec:** Tak

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Tak
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Tak
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Tak
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Tak
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Tak
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Tak
```

### rozumowanie-02 (krotka, trudność 1)

**Polecenie:** Dziś jest wtorek. Jaki dzień tygodnia będzie za dwa dni?

**Wzorzec:** Czwartek

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Nie wiem
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Środa
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Czwartek
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Czwartek
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 12

```text
 Dwudziestu.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 20

```text
 Dzień tygodnia będzie za dwa dni.
```

### rozumowanie-03 (krotka, trudność 1)

**Polecenie:** Marta jest wyższa od Kingi, a Kinga jest wyższa od Zosi. Która z dziewczyn jest najniższa?

**Wzorzec:** Zosia

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Zosia
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Zosia
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Zosia
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
Kinga
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Zosi
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Zosi
```

### rozumowanie-04 (krotka, trudność 1)

**Polecenie:** Żaden pingwin w tym zoo nie umie latać. Pik jest pingwinem z tego zoo. Czy Pik umie latać? Odpowiedz „tak” albo „nie”.

**Wzorzec:** Nie

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Tak
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Nie
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Nie
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Nie
```

### rozumowanie-05 (krotka, trudność 1)

**Polecenie:** W szufladzie leżą wyłącznie skarpety czerwone i niebieskie. Wyjęłam jedną skarpetę i wiem, że nie jest czerwona. Jakiego koloru jest ta skarpeta?

**Wzorzec:** Niebieska

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Niebieskiego
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Niebieska
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
Niebieski
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
Niebieski
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Czerwona
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Czerwona
```

### rozumowanie-06 (krotka, trudność 1)

**Polecenie:** Pani Teresa jest matką Oli. Ola ma syna Janka. Kim jest Janek dla pani Teresy?

**Wzorzec:** Wnuk

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Janek
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Janek
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 11

```text
Jankiem jest syn Oli
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
Ojcem
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 19

```text
 Ola jest synem Janka dla pani Teresy.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 13

```text
 Janek dla pani Teresy
```

### rozumowanie-07 (krotka, trudność 1)

**Polecenie:** Basia jest starsza od Celiny. Czy Celina jest młodsza od Basi? Odpowiedz „tak” albo „nie”.

**Wzorzec:** Tak

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Tak
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Tak
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
Nie
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Tak
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Nie
```

### rozumowanie-08 (krotka, trudność 1)

**Polecenie:** Wczoraj była sobota. Jaki dzień tygodnia jest dzisiaj?

**Wzorzec:** Niedziela

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 10

```text
 Poniedziałek
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Sobota
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Niedziela
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
Poniedziałek
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 25

```text
 Wczoraj był popołudniu. Dzisiaj jest porankiem.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 15

```text
 Dzisiaj jest poniedziałek
```

### rozumowanie-09 (krotka, trudność 1)

**Polecenie:** Każdy uczeń klasy 3b był na wycieczce w Toruniu. Filip jest uczniem klasy 3b. Czy Filip był na wycieczce w Toruniu? Odpowiedz „tak” albo „nie”.

**Wzorzec:** Tak

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Tak
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Tak
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Tak
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Tak
```

### rozumowanie-10 (krotka, trudność 1)

**Polecenie:** Kasia ma czerwony rower, a Tomek zielony. Rower Igi ma taki sam kolor jak rower Tomka. Jakiego koloru jest rower Igi?

**Wzorzec:** Zielony

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Czerwonego
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Zielony
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Zielony
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Czerwony
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Czerwony
```

### rozumowanie-11 (krotka, trudność 2)

**Polecenie:** Zawsze, gdy pada deszcz, Bartek bierze do pracy parasol. Dziś Bartek nie wziął parasola. Czy dziś padał deszcz? Odpowiedz „tak” albo „nie”.

**Wzorzec:** Nie

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Nie
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Nie
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Nie
```

### rozumowanie-12 (krotka, trudność 2)

**Polecenie:** Za trzy dni będzie sobota. Jaki dzień tygodnia był wczoraj?

**Wzorzec:** Wtorek

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Niedziela
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Sobota
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
Poniedziałek
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
Piątek
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Pięć
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 16

```text
 Wczoraj był poniedziałek.
```

### rozumowanie-13 (krotka, trudność 2)

**Polecenie:** Czterech chłopców biegło na 100 metrów. Adam był szybszy od Bogdana, Cezary był wolniejszy od Bogdana, a Darek był szybszy od Adama. Kto przybiegł na metę jako drugi?

**Wzorzec:** Adam

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Bogdan
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Bogdan
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
Cezary
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
Cezary
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Bogdana
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Bogdana
```

### rozumowanie-14 (krotka, trudność 2)

**Polecenie:** Kim jest dla mnie brat mojej mamy?

**Wzorzec:** Wujek

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Jego mama.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 15

```text
 Bratem mojej mamy jest mój tata.
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
bratem
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 13

```text
Bratem mojej mamy jest mój ojciec
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 17

```text
 Zawsze brata mojej mamy.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Mamo
```

### rozumowanie-15 (krotka, trudność 2)

**Polecenie:** Niektóre psy w schronisku mają czarną sierść. Burek jest psem z tego schroniska. Czy na pewno Burek ma czarną sierść? Odpowiedz „tak” albo „nie”.

**Wzorzec:** Nie

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Tak
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
Tak
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Nie
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Tak
```

### rozumowanie-16 (krotka, trudność 2)

**Polecenie:** Wszyscy goście przyjęcia przyszli przed godziną 18:00. Pan Roman przyszedł o 18:15. Czy pan Roman mógł być jednym z gości przyjęcia? Odpowiedz „tak” albo „nie”.

**Wzorzec:** Nie

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Tak
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
Tak
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Nie
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Tak
```

### rozumowanie-17 (krotka, trudność 2)

**Polecenie:** Jeśli Ola ma dyżur, to Piotr nie ma dyżuru. Wiadomo, że Piotr ma dyżur. Czy to prawda, że Ola nie ma dyżuru? Odpowiedz „tak” albo „nie”.

**Wzorzec:** Tak

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
Nie
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
Nie
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Nie
```

### rozumowanie-18 (krotka, trudność 2)

**Polecenie:** Agata urodziła się w maju. Bożena urodziła się dwa miesiące po Agacie, a Celina miesiąc przed Bożeną. W którym miesiącu urodziła się Celina?

**Wzorzec:** W czerwcu

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Celina
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Celina
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
W lutym
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
W kwietniu
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Bożena
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 10

```text
 Ciężka
```

### rozumowanie-19 (krotka, trudność 2)

**Polecenie:** Jeśli sklep jest otwarty, to świeci się szyld. Jeśli świeci się szyld, to na parkingu jest jasno. Sklep jest otwarty. Czy na parkingu jest jasno? Odpowiedz „tak” albo „nie”.

**Wzorzec:** Tak

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Tak
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Tak
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Tak
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Tak
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Nie
```

### rozumowanie-20 (krotka, trudność 2)

**Polecenie:** Przedwczoraj był piątek. Jaki dzień tygodnia będzie jutro?

**Wzorzec:** Poniedziałek

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Sobota
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Piątek
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
Poniedziałek
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
Sobota
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 10

```text
 Poniedziałek
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 15

```text
 Jutro będzie piątek.
```

### rozumowanie-21 (krotka, trudność 3)

**Polecenie:** Na wyspie mieszkają rycerze, którzy zawsze mówią prawdę, i łotrzy, którzy zawsze kłamią. Adam mówi: „Obaj z Borysem jesteśmy łotrami”. Kim jest Borys: rycerzem czy łotrem?

**Wzorzec:** Rycerzem

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 18

```text
 Adam jest łotrem, a Borys rycerzem
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 12

```text
 Borys jest łotrem
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
Łotrem
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
Borysem
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Rycerzem
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 Rycerzem
```

### rozumowanie-22 (krotka, trudność 3)

**Polecenie:** Zawsze, gdy pada deszcz, chodnik przed szkołą jest mokry. Rano chodnik przed szkołą był mokry. Czy na pewno rano padał deszcz? Odpowiedz „tak” albo „nie”.

**Wzorzec:** Nie

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Tak
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Nie
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Nie
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Nie
```

### rozumowanie-23 (krotka, trudność 3)

**Polecenie:** Wszyscy członkowie chóru śpiewają. Niektóre osoby, które śpiewają, grają na gitarze. Czy na pewno któryś członek chóru gra na gitarze? Odpowiedz „tak” albo „nie”.

**Wzorzec:** Nie

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Nie
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Nie
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Tak
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Nie
```

### rozumowanie-24 (krotka, trudność 3)

**Polecenie:** Hania, Iwo i Julek siedzą obok siebie na trzyosobowej ławce. Hania nie siedzi na żadnym końcu ławki. Iwo nie siedzi na prawo od Hani. Kto siedzi na prawym końcu ławki?

**Wzorzec:** Julek

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Iwo
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Julek
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
Hania
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Julek
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Hania
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Iwo
```

### rozumowanie-25 (krotka, trudność 3)

**Polecenie:** Jedna z trzech osób zjadła ostatnie ciastko. Kasia mówi: „To nie ja”. Lena mówi: „To Kasia”. Marek mówi: „To nie ja”. Dokładnie jedna z tych osób mówi prawdę. Kto zjadł ciastko?

**Wzorzec:** Marek

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Kasia
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Kasia
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
Kasia
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
Kasia
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Marek
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Marek
```

### rozumowanie-26 (krotka, trudność 3)

**Polecenie:** Pociąg do Gdańska odjeżdża później niż pociąg do Krakowa, ale wcześniej niż pociąg do Lublina. Pociąg do Poznania odjeżdża po pociągu do Lublina. Do którego miasta jedzie pociąg, który odjeżdża jako drugi?

**Wzorzec:** Do Gdańska

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Lublina
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Lublin
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
Do Lublina
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
Do Poznania
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Poznań
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Gdańsk
```

### rozumowanie-27 (krotka, trudność 3)

**Polecenie:** Trzy domy stoją w rzędzie: czerwony, żółty i biały, ale niekoniecznie w tej kolejności. Czerwony dom nie stoi na żadnym końcu. Żółty dom stoi na lewo od czerwonego. Jakiego koloru jest dom stojący na prawym końcu?

**Wzorzec:** Biały

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Żółtego
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 Żółty
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Biały
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
Biały
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Biały
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 Biały
```

### rozumowanie-28 (krotka, trudność 3)

**Polecenie:** Konferencja trwała pięć kolejnych dni, a jej ostatnim dniem była niedziela. W jaki dzień tygodnia się zaczęła?

**Wzorzec:** W środę

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Niedziela
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Niedziela
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
Sobota
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
Sobota
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 41

```text
 Zawierała cztery dni, a jej ostatnim dniem była niedziela. W jaki dzień tygodnia się zaczęła?
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 9

```text
 niedziela
```

### rozumowanie-29 (krotka, trudność 3)

**Polecenie:** Mój dziadek ze strony ojca ma tylko jednego syna. Kim jest dla mnie ten syn?

**Wzorzec:** Ojcem

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 11

```text
 To jest ten syn.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 17

```text
 Mój dziadek ze strony ojca ma tylko jednego syna.
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
Bratem
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
Bratem
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: limit, tokenów: 48

```text
 Który z mężczyzn urodził się na moim dziadku, a kto jest dla mnie, ten syn? Odpowiedz „tak” albo „nie”.
Odpowiedź:
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 19

```text
 Mój dziadek ma tylko jednego syna.
```

### rozumowanie-30 (krotka, trudność 3)

**Polecenie:** Żaden ptak w tej wolierze nie jest papugą. Kuba jest papugą. Czy można stąd wywnioskować, że Kuba nie jest ptakiem z tej woliery? Odpowiedz „tak” albo „nie”.

**Wzorzec:** Tak

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
Nie
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
Nie
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 Nie
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Tak
```

## matematyka

### matematyka-01 (liczba, trudność 1)

**Polecenie:** Pani Grażyna kupiła na targu 3 kg truskawek po 14 zł za kilogram. Ile złotych zapłaciła?

**Wzorzec:** Zapłaciła 3 · 14 = 42 zł. Wynik: 42

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 23

```text
 Pani Grażyna zapłaciła 3 × 14 = 56 zł. Wynik: 56
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 21

```text
 Pani Grażyna zapłaciła 14 zł za kilogram. Wynik: 14
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 31

```text
Za truskawki zapłaciła 3 · 14 = 42 zł. Wynik: 42
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 31

```text
Za truskawki zapłaciła 3 · 14 = 42 zł. Wynik: 42
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 31

```text
 Pani Grażyna zapłaciła 3 · 14 = 42 złoty. Wynik: 42
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 31

```text
 Pani Grażyna zapłaciła 3 · 14 = 42 złoty. Wynik: 42
```

### matematyka-02 (liczba, trudność 1)

**Polecenie:** Pan Leszek wyjechał z domu o 9:15 i dotarł do celu o 11:05. Ile minut trwała jego podróż?

**Wzorzec:** Od 9:15 do 11:15 są 2 godziny, czyli 120 minut, a 120 − 10 = 110 minut. Wynik: 110

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 17

```text
 3 · 5 = 15 minut. Wynik: 15
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 22

```text
 Pan Leszek dotarł do celu o 11:05. Wynik: 11
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 38

```text
Podróż trwała 11:05 − 9:15 = 1:50 minut. Wynik: 1:50
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 43

```text
Podróż trwała 11:05 − 9:15 = 1 godzinę i 50 minut. Wynik: 1 godzina i 50 minut
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 34

```text
 Trwała podróż 11:05 − 9:15 = 2:40. Wynik: 2:40
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 34

```text
 Podróż trwała 11:05 − 9:15 = 2:40. Wynik: 2,40
```

### matematyka-03 (liczba, trudność 1)

**Polecenie:** Rowerzystka jedzie ze stałą prędkością 18 km/h. Ile kilometrów przejedzie w ciągu 3 godzin?

**Wzorzec:** Przejedzie 18 · 3 = 54 km. Wynik: 54

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 24

```text
 Rowerzystka przejedzie 18 · 3 = 54 km. Wynik: 54
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 20

```text
 Rowerzystka przejedzie 18 km. Wynik: 18
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 31

```text
Rowerzystka przejedzie 18 · 3 = 54 km. Wynik: 54
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 31

```text
Rowerzystka przejedzie 18 · 3 = 54 km. Wynik: 54
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 32

```text
 W ciągu 3 godzin przejedzie 18 · 3 = 54 km. Wynik: 54
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 32

```text
 W ciągu 3 godzin przejedzie 18 · 3 = 54 km. Wynik: 54
```

### matematyka-04 (liczba, trudność 1)

**Polecenie:** W klasie 4c jest 28 uczniów, a jedna czwarta z nich dojeżdża do szkoły autobusem. Ilu uczniów dojeżdża autobusem?

**Wzorzec:** Autobusem dojeżdża 28 : 4 = 7 uczniów. Wynik: 7

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 17

```text
 29 uczniów dojeżdża autobusem. Wynik: 29
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 34

```text
 28 + 1/4 = 28 + 3/4 = 28 + 7/4 = 28 + 7 = 42. Wynik: 42
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 29

```text
Dojeżdża autobusem 28 · 1/4 = 7 uczniów. Wynik: 7
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 27

```text
Dojeżdża 28 × 1/4 = 7 uczniów. Wynik: 7
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 23

```text
 28 / 4 = 7 uczniów. Wynik: 7
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 23

```text
 28 / 4 = 7 uczniów. Wynik: 7
```

### matematyka-05 (liczba, trudność 1)

**Polecenie:** Kurtka zimowa kosztowała 240 zł. Na wyprzedaży jej cena spadła o 10%. Ile złotych kosztuje teraz?

**Wzorzec:** 10% z 240 zł to 24 zł, więc kurtka kosztuje 240 − 24 = 216 zł. Wynik: 216

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 34

```text
 Kurtka kosztowała 240 zł. Po wyprzedaży jej cena spadła o 10% do 240 zł. Wynik: 240 zł
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 18

```text
 Kurtka kosztuje teraz 240 zł. Wynik: 240
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 43

```text
Kurtka kosztuje 240 − (240 · 0,10) = 216 zł. Wynik: 216
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 65

```text
Cena kurtki spadła o 10%, czyli o 240 zł · 10% = 24 zł. Teraz kurtka kosztuje 240 zł − 24 zł = 216 zł. Wynik: 216
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 43

```text
 Koszta na wyprzedaży wynosi 240 − 10% · 240 = 240 − 24 = 216 złotych. Wynik: 216
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 36

```text
 Koszt teraz wynosi 240 − 10% · 240 = 240 − 24 = 216 zł. Wynik: 216
```

### matematyka-06 (liczba, trudność 1)

**Polecenie:** Słoik miodu gryczanego waży 0,9 kg. Ile kilogramów ważą razem 4 takie słoiki?

**Wzorzec:** Cztery słoiki ważą 4 · 0,9 = 3,6 kg. Wynik: 3,6

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 23

```text
 4 · 0,9 = 1,2 kg. Wynik: 1,2
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 33

```text
 Słoik miodu gryczanego waży 0,9 · 4 = 2,4 kg. Wynik: 2,4
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 33

```text
Słoiki ważą 4 · 0,9 = 3,6 kg. Wynik: 3,6
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 33

```text
Słoiki ważą 0,9 · 4 = 3,6 kg. Wynik: 3,6
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 27

```text
 4 · 0,9 = 3,6 kg. Wynik: 3,6
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 35

```text
 Słoiki ważą razem 4 · 0,9 = 3,6 kg. Wynik: 3,6
```

### matematyka-07 (liczba, trudność 1)

**Polecenie:** Antek czyta codziennie 15 stron. W ile dni przeczyta książkę, która ma 240 stron?

**Wzorzec:** Przeczyta ją w 240 : 15 = 16 dni. Wynik: 16

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 21

```text
 Antek przeczyta w dniach, w których przeczytał 15 stron.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 22

```text
 Antek przeczyta w ciągu 5 dni 240 stron. Wynik: 240
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 31

```text
Antek przeczyta 240 ÷ 15 = 16 dni. Wynik: 16
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 31

```text
Antek przeczyta 240 ÷ 15 = 16 dni. Wynik: 16
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 26

```text
 Wystarczy 240 / 15 = 16 dni. Wynik: 16
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 27

```text
 Przeczyta 15 · 240 = 3600 stron. Wynik: 3600
```

### matematyka-08 (liczba, trudność 1)

**Polecenie:** Na parkingu przed urzędem gminy stało 36 samochodów. Odjechało 9, a potem przyjechało 14. Ile samochodów stoi teraz na parkingu?

**Wzorzec:** Po odjeździe zostało 36 − 9 = 27 samochodów, a po przyjeździe 27 + 14 = 41. Wynik: 41

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 20

```text
 Zniknęło 14 − 9 = 6 samochodów. Wynik: 6
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 21

```text
 Odjechało 9 samochodów, a przyjechało 14. Wynik: 14
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 52

```text
Po przyjeździe do 9 samochodów, jest ich 36 − 9 = 27. Następnie na parkingu jest 27 + 14 = 41 samochodów. Wynik: 41
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 30

```text
Na parkingu stoi teraz 36 − 9 = 27 samochodów. Wynik: 27
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 28

```text
 Stało 36 − 9 + 14 = 41 samochody. Wynik: 41
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 47

```text
 Na początku było 36, a potem 9, więc 36 − 9 = 27, a potem 27 + 14 = 41. Wynik: 41
```

### matematyka-09 (liczba, trudność 1)

**Polecenie:** Trzydniowa wycieczka do Zakopanego kosztuje 380 zł od osoby. Ile złotych zapłaci za nią czteroosobowa rodzina?

**Wzorzec:** Rodzina zapłaci 4 · 380 = 1520 zł. Wynik: 1520

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 26

```text
 Trzydniowa wycieczka do Zakopanego kosztuje 380 zł od osoby. Wynik: 380
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 23

```text
 Trzydniowa wycieczka kosztuje 380 zł od osoby. Wynik: 380
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 32

```text
Rodzina zapłaci 4 · 380 = 1520 zł. Wynik: 1520
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 32

```text
Rodzina zapłaci 4 · 380 = 1520 zł. Wynik: 1520
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 33

```text
 Czteroosobowa rodzina zapłaci 4 · 380 = 1520 zł. Wynik: 1520
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 33

```text
 Czteroosobowa rodzina zapłaci 380 · 4 = 1520 zł. Wynik: 1520
```

### matematyka-10 (liczba, trudność 1)

**Polecenie:** W dzbanku były 2 litry kompotu z wiśni. Nalano z niego 8 kubków po 0,2 litra. Ile litrów kompotu zostało w dzbanku?

**Wzorzec:** Nalano 8 · 0,2 = 1,6 l, więc zostało 2 − 1,6 = 0,4 l. Wynik: 0,4

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 33

```text
 Po nalaniu do dzbanka kompotu z wiśni zostało 8 kubków po 0,2 litra. Wynik: 8
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 24

```text
 8 · 0,2 = 4,8 litra. Wynik: 4,8
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 40

```text
Po nalaniu zostało 2 − 8 · 0,2 = 0,4 litra. Wynik: 0,4
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 40

```text
W dzbanku zostało 2 − 8 · 0,2 = 0,4 litra. Wynik: 0,4
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 35

```text
 Z niego wylanano 8 · 0,2 = 1,6 litra. Wynik: 1,6
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 33

```text
 W dzbanku było 8 · 0,2 = 1,6 litra. Wynik: 1,6
```

### matematyka-11 (liczba, trudność 2)

**Polecenie:** W piekarni Marek kupił 3 bułki po 1,20 zł i kostkę masła za 7,50 zł. Zapłacił banknotem 20 zł. Ile złotych reszty dostał?

**Wzorzec:** Bułki kosztowały 3 · 1,20 = 3,60 zł, razem z masłem 3,60 + 7,50 = 11,10 zł, więc reszta to 20 − 11,10 = 8,90 zł. Wynik: 8,9

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 52

```text
 Marek kupił 3 bułki po 1,20 zł i kostkę masła za 7,50 zł. Zapłacił banknotem 20 zł. Wynik: 7,50 zł reszty. Wynik: 7,50
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 20

```text
 Marek dostał 3 · 20 = 60 złotych reszty. Wynik: 60
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 64

```text
Zapłacił 3 · 1,20 + 7,50 = 10,50 zł. Różnica to 20 − 10,50 = 9,50 zł. Wynik: 9,50
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 66

```text
Zapłacił 3 · 1,20 + 7,50 = 12,70 zł. Resztę dostał 20 − 12,70 = 7,30 zł. Wynik: 7,30
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 33

```text
 Marek zapłacił 20 − 7,50 = 12,50 zł. Wynik: 12,50
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 33

```text
 Marek zapłacił 20 − 7,50 = 12,50 zł. Wynik: 12,50
```

### matematyka-12 (liczba, trudność 2)

**Polecenie:** Samochód pani Doroty spala średnio 6,5 litra benzyny na 100 km. Ile litrów benzyny spali na trasie długości 340 km?

**Wzorzec:** 340 km to 3,4 razy po 100 km, więc spali 3,4 · 6,5 = 22,1 l. Wynik: 22,1

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 28

```text
 Samochód spala średnio 6,5 · 100 = 600 litrów benzyny. Wynik: 600
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 28

```text
 Średnia spalanie benzyny wynosi 6,5 litra na 100 km. Wynik: 6,5
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 35

```text
Samochód spali 6,5 · 340 = 2210 litrów benzyny. Wynik: 2210
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 35

```text
Samochód spali 6,5 · 340 = 2210 litrów benzyny. Wynik: 2210
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 30

```text
 Spali 340 / 6,5 = 52,38 litra. Wynik: 52,38
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 32

```text
 Samochód spali 6,5 · 340 = 2210 litrów. Wynik: 2210
```

### matematyka-13 (liczba, trudność 2)

**Polecenie:** Pani Iwona zarabia na rękę 5000 zł miesięcznie. 30% tej kwoty wydaje na mieszkanie, a jedną piątą tego, co zostanie, na jedzenie. Ile złotych wydaje na jedzenie?

**Wzorzec:** Na mieszkanie idzie 0,3 · 5000 = 1500 zł, zostaje 5000 − 1500 = 3500 zł, a na jedzenie 3500 : 5 = 700 zł. Wynik: 700

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 24

```text
 Pani Iwona wydaje 5 · 5000 zł = 10000 zł. Wynik: 10000
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 28

```text
 Pani Iwona wydaje na jedzenie 5000 zł. 30% tej kwoty to 5000 zł. Wynik: 5000 zł
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 50

```text
30% z 5000 zł to 1500 zł, a 1/5 z 1500 zł to 300 zł. Wynik: 300
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 76

```text
30% z 5000 zł to 0,3 · 5000 = 1500 zł. Następnie 1/5 z 1500 zł to 0,2 · 1500 = 300 zł. Wynik: 300
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 31

```text
 Wydaje na jedzenie 5000 · 1/4 = 1250 zł. Wynik: 1250
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 31

```text
 Wydaje na jedzenie 5000 · 1/5 = 1000 zł. Wynik: 1000
```

### matematyka-14 (liczba, trudność 2)

**Polecenie:** Pociąg jechał przez 2 godziny i 15 minut ze średnią prędkością 80 km/h. Ile kilometrów przejechał?

**Wzorzec:** 2 godziny i 15 minut to 2,25 h, więc pociąg przejechał 2,25 · 80 = 180 km. Wynik: 180

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 21

```text
 Średnia prędkość pociągu to 80 km/h. Wynik: 80
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 17

```text
 Pociąg przejechał 80 km. Wynik: 80
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 37

```text
Przejechał 80 · 2 · 15 = 2400 km. Wynik: 2400
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 33

```text
Pociąg przejechał 80 · 2,5 = 200 km. Wynik: 200
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 40

```text
 Prędkość wynosi 80 km/h, więc przejechał 2 · 60 + 15 = 135 km. Wynik: 135
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 56

```text
 Pociąg przejechał 2 + 15/60 = 2,25 godziny. Ilość kilometrów przejechał 2,25 · 80 = 180 km. Wynik: 180
```

### matematyka-15 (liczba, trudność 2)

**Polecenie:** Na weselu jest 120 gości, a przy każdym stole siedzi 8 osób. Oprócz stołów dla gości ustawiono jeszcze jeden stół dla orkiestry. Ile stołów ustawiono w sumie?

**Wzorzec:** Dla gości potrzeba 120 : 8 = 15 stołów, a ze stołem orkiestry 15 + 1 = 16. Wynik: 16

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 19

```text
 Na weselu ustawiono 12 stołów. Wynik: 12
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 19

```text
 Stoły ustawiono w sumie na 12. Wynik: 12
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 50

```text
Przy stołach siedzą 120 − 8 = 112 osób. Do tego 1 stół dla orkiestry. Łącznie 113 stołów. Wynik: 113
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 72

```text
Przy stole dla orkiestry siedzi 8 osób, a przy każdym innym stole 8 osób. Razem jest 120 + 8 = 128 osób. Ponieważ każdy stół może pomieścić 8 osób, to 128 ÷ 8 = 16 stołów. Wynik: 16
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 37

```text
 Ustawiono 8 stołów dla gości + 1 stoł dla orkiestry = 9 stołów. Wynik: 9
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 25

```text
 Ustawiono 120 / 8 = 15 stołów. Wynik: 15
```

### matematyka-16 (liczba, trudność 2)

**Polecenie:** Babcia Halina robi z 1 kg mąki 60 pierogów. Ile kilogramów mąki potrzebuje na 150 pierogów?

**Wzorzec:** Potrzebuje 150 : 60 = 2,5 kg mąki. Wynik: 2,5

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 23

```text
 Babcia Halina potrzebuje 1 · 2 = 2 kg mąki. Wynik: 2
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 23

```text
 Babcia Halina potrzebuje 1 · 60 = 60 kg mąki. Wynik: 60
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 44

```text
Mąka potrzebna na 150 pierogów to 150 · 1/60 = 2,5 kg. Wynik: 2,5
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 41

```text
Mąka potrzebna na 150 pierogów to 150 · 1 = 150 g. Wynik: 150
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 35

```text
 Potrzebuje 60 / 150 = 0,4 kg mąki na pierog. Wynik: 0,4
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 28

```text
 Potrzebuje 1 · 150 = 150 kg mąki. Wynik: 150
```

### matematyka-17 (liczba, trudność 2)

**Polecenie:** Zeszyt kosztuje 4,50 zł, a długopis 2,80 zł. Ile złotych trzeba zapłacić za 6 zeszytów i 5 długopisów?

**Wzorzec:** Zeszyty kosztują 6 · 4,50 = 27 zł, długopisy 5 · 2,80 = 14 zł, razem 27 + 14 = 41 zł. Wynik: 41

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 29

```text
 Trzeba zapłacić 12,50 zł za 6 zeszytów i 5 długopisów. Wynik: 12,50
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 34

```text
 Zeszyty kosztują 4,50 zł, długopisy 2,80 zł. Wynik: 6 · 5 = 30 zł.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 79

```text
Za 6 zeszytów trzeba zapłacić 6 · 4,50 = 27 zł. Za 5 długopisów trzeba zapłacić 5 · 2,80 = 14 zł. Razem za zeszyty i długopisy trzeba zapłacić 27 + 14 = 41 zł. Wynik: 41
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 72

```text
Za 6 zeszytów trzeba zapłacić 6 · 4,50 = 27 zł, a za 5 długopisów 5 · 2,80 = 14 zł. Razem trzeba zapłacić 27 + 14 = 41 zł. Wynik: 41
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 55

```text
 Za 6 zeszytów i 5 długopisów trzeba zapłacić 6 · 4,50 + 5 · 2,80 = 27,50 zł. Wynik: 27,50
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 88

```text
 Za 6 zeszytów trzeba zapłacić 6 · 4,50 = 27,00 zł, a za 5 długopisów 5 · 2,80 = 14,00 zł. W sumie trzeba zapłacić 27,00 + 14,00 = 41,00 zł. Wynik: 41,00
```

### matematyka-18 (liczba, trudność 2)

**Polecenie:** Kuba przepłynął 24 długości basenu, który ma 25 metrów. Ile to kilometrów?

**Wzorzec:** Przepłynął 24 · 25 = 600 m, czyli 0,6 km. Wynik: 0,6

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 23

```text
 Kuba przepłynął 24 · 25 = 6600 metrów. Wynik: 6600
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 17

```text
 24 · 25 = 600 metrów. Wynik: 600
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 51

```text
Przepłynął 24 · 25 = 600 metrów, czyli 600 ÷ 1000 = 0,6 km. Wynik: 0,6
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 31

```text
Przepłynął 24 · 25 = 600 metrów. Wynik: 600
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 28

```text
 Kuba przepłynął 24 · 25 = 600 metrów. Wynik: 600
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 31

```text
 Kuba przepłynął 24 / 25 = 0,96 km. Wynik: 0,96
```

### matematyka-19 (liczba, trudność 2)

**Polecenie:** Litr mleka w wiejskim sklepie podrożał z 3,20 zł do 4,00 zł. O ile procent wzrosła cena?

**Wzorzec:** Cena wzrosła o 4,00 − 3,20 = 0,80 zł, a 0,80 : 3,20 = 0,25, czyli o 25%. Wynik: 25

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 30

```text
 Z 3,20 zł do 4,00 zł, cena mleka podrożała o 20%. Wynik: 20%
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 23

```text
 Cena mleka podrożała o 4,00 zł. Wynik: 4,00
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 87

```text
Wzrosła o 4,00 − 3,20 = 0,80 zł. Aby przeliczyć na procent, dzielimy 0,80 na 3,20 i mnożymy przez 100: (0,80 / 3,20) * 100 = 25%. Wynik: 25
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 79

```text
Cena wzrosła o 4,00 − 3,20 = 0,80 zł. Aby znaleźć procent, dzielimy różnicę przez cenę początkową i mnożymy przez 100: (0,80 / 3,20) * 100 = 25%. Wynik: 25%
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 57

```text
 Różnica ceny wynosi 4,00 − 3,20 = 0,80 zł. Procent wzrostu wynosi (0,80 / 3,20) · 100 = 25%. Wynik: 25%
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 37

```text
 Cena wzrosła o (4 − 3) / 3 · 100 = 6,67%. Wynik: 6,67
```

### matematyka-20 (liczba, trudność 2)

**Polecenie:** Na mapie turystycznej w skali 1 : 50 000 odcinek szlaku ma długość 7 cm. Ile kilometrów ma ten odcinek w terenie?

**Wzorzec:** W terenie to 7 · 50 000 = 350 000 cm, czyli 3,5 km. Wynik: 3,5

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 22

```text
 7 cm × 50 000 = 500 000 cm. Wynik: 500 000 cm
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 18

```text
 7 cm = 0,07 km. Wynik: 7
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 47

```text
Długość odcinka szlaku w terenie wynosi 7 · 50 000 = 350 000 cm = 3,5 km. Wynik: 3,5
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 46

```text
Długość odcinka w terenie wynosi 7 · 50 000 = 350 000 cm = 3,5 km. Wynik: 3,5
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 31

```text
 Odcinek ma 7 · 50 000 = 350 000 cm. Wynik: 350 000
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 33

```text
 7 cm = 7 / 50 000 = 0,00014 km. Wynik: 0,00014
```

### matematyka-21 (liczba, trudność 3)

**Polecenie:** Telewizor kosztował 2500 zł. Sklep najpierw obniżył cenę o 20%, a po miesiącu podniósł nową cenę o 10%. Ile złotych kosztuje teraz telewizor?

**Wzorzec:** Po obniżce kosztował 2500 · 0,8 = 2000 zł, a po podwyżce 2000 · 1,1 = 2200 zł. Wynik: 2200

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 20

```text
 Telewizor kosztuje teraz 2500 zł. Wynik: 2500
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 20

```text
 Telewizor kosztuje teraz 2500 zł. Wynik: 2500
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 86

```text
Po obniżce cena wynosi 2500 − (2500 × 0,20) = 2000 zł. Po podwyżce cena wynosi 2000 − (2000 × 0,10) = 1800 zł. Wynik: 1800
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 64

```text
Po obniżce cena wynosi 2500 · 0,8 = 2000 zł. Po podwyżce cena wynosi 2000 · 1,1 = 2200 zł. Wynik: 2200
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 63

```text
 Po obniżeniu ceny o 20%, koszt wynosi 2500 − 500 = 2000 zł. Następnie podniósł o 10% do 2000 + 200 = 2200 zł. Wynik: 2200
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 62

```text
 Po obniżeniu o 20% koszt wynosi 2500 − 500 = 2000 zł. Po podniesieniu o 10% koszt wynosi 2000 + 200 = 2200 zł. Wynik: 2200
```

### matematyka-22 (liczba, trudność 3)

**Polecenie:** Z dwóch miejscowości odległych o 270 km wyjechały jednocześnie naprzeciw siebie dwa samochody. Jeden jedzie z prędkością 70 km/h, a drugi 80 km/h. Po ilu minutach się spotkają?

**Wzorzec:** Zbliżają się z prędkością 70 + 80 = 150 km/h, więc spotkają się po 270 : 150 = 1,8 h, czyli po 1,8 · 60 = 108 minutach. Wynik: 108

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 38

```text
 Po ilu minutach spotkają się? Kierunek pierwszego samochodu to północ, a drugiego to wschód. Wynik: Po ilu minutach spotkają się?
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 33

```text
 Po ilu minutach spotkają się? Kierunek jazdy: 70 km/h. Prędkość: 80 km/h.
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 57

```text
Różnica prędkości wynosi 10 km/h, a odległość do przebycia to 270 km. Czas spotkania wynosi 270 − 10 = 260 km/h. Wynik: 260
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 38

```text
Czas spotkania wynosi 270 − 70 − 80 = 20 minut. Wynik: 20
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 46

```text
 Prędkość ich spotkania wynosi 70 + 80 = 150 km/h. Zatem 150 · 60 / 150 = 60 minut. Wynik: 60
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 63

```text
 Po spotkaniu samochód z prędkością 70 km/h i drugi z prędkością 80 km/h będą się spotkać po 270 / (80 − 70) = 9 minutach. Wynik: 9
```

### matematyka-23 (liczba, trudność 3)

**Polecenie:** Pan Zbigniew sam kosi trawnik w 3 godziny, a jego syn w 6 godzin. W ile minut skoszą ten trawnik razem, pracując dwiema kosiarkami?

**Wzorzec:** W godzinę ojciec kosi 1/3 trawnika, a syn 1/6, razem 1/3 + 1/6 = 1/2, więc skoszą go w 2 godziny, czyli 120 minut. Wynik: 120

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 22

```text
 Pan Zbigniew ma 3 kosy, a panowie razem 5 kosiarek.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 31

```text
 Pan Zbigniew pracuje dwiema kosiarkami, a jego syn jedną. Wynik: 2 · 6 = 12 minut.
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 41

```text
Razem koszą 3 + 6 = 9 godzin, czyli 9 × 60 = 540 minut. Wynik: 540
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 25

```text
Razem koszą 3 + 6 = 9 godzin. Wynik: 90 minut
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 33

```text
 W 3 + 6 = 9 godzin = 9 · 60 = 540 minut. Wynik: 540
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 44

```text
 Kosiarki pracują razem 6 + 3 = 9 godzin. W godzinach 9 · 60 = 540 minut. Wynik: 540
```

### matematyka-24 (liczba, trudność 3)

**Polecenie:** Średnia czterech ocen Oli z matematyki wynosi 4,5. Jaką ocenę musi dostać z piątego sprawdzianu, żeby średnia z pięciu ocen wyniosła 4,6?

**Wzorzec:** Suma czterech ocen to 4 · 4,5 = 18, potrzebna suma pięciu to 5 · 4,6 = 23, więc brakuje 23 − 18 = 5. Wynik: 5

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: limit, tokenów: 160

```text
 Średnia ocen Oli z matematyki wynosi 4,5. Średnia z pięciu ocen wynosi 5,5. Średnia z pięciu ocen wynosi 5,5. Średnia z pięciu ocen wynosi 4,6. Średnia z pięciu ocen wynosi 4,6. Średnia z pięciu ocen wynosi 4,5. Średnia z pięciu ocen wynosi 4,6. Średnia z pięciu ocen wynosi 4,5. Średnia z pięciu ocen wynosi 4,6. Średnia z pięciu ocen wynosi 4,6. Średnia z pięciu ocen wynosi 4,5. Średnia z pięciu ocen wynosi 4,6. Średnia z pięciu ocen wynosi 4,6. Średnia z pięciu ocen wynosi 4,5. Średnia z pięciu ocen wynosi 4,6. Średnia z pięciu ocen wynosi 4,6
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 22

```text
 Średnia z pięciu ocen to 4,5. Wynik: 4,5
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 118

```text
Aby uzyskać średnią 4,6, trzeba dodać 5 ocen i podzielić przez 5. Oznaczmy przez x ocenę piątego sprawdzianu. Mamy równanie: (4 + 4 + 4 + 4 + x) / 5 = 4,6. Rozwiązując to równanie, otrzymujemy x = 4,6 · 5 − 4 − 4 − 4 − 4 = 4,6. Wynik: 4,6
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 73

```text
Aby uzyskać średnią 4,6, suma ocen musi wynosić 4,6 · 5 = 23. Z czterech ocen mamy 4,5 · 4 = 18. Zatem piąta ocena musi wynosić 23 − 18 = 5. Wynik: 5
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 39

```text
 Oli musi otrzymać 4,6 — 4,5 + 0,1 = 4,6. Wynik: 4,6
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 47

```text
 Ola musi uzyskać 4,6, co oznacza, że musi uzyskać 4,6 · 5 = 23 ocen. Wynik: 23
```

### matematyka-25 (liczba, trudność 3)

**Polecenie:** Działka pana Romana jest prostokątem o wymiarach 30 m na 24 m. Chce ją ogrodzić siatką, zostawiając 4 m wolnego miejsca na bramę. Metr siatki kosztuje 18 zł. Ile złotych wyda na siatkę?

**Wzorzec:** Obwód działki to 2 · (30 + 24) = 108 m, bez bramy 108 − 4 = 104 m, więc siatka kosztuje 104 · 18 = 1872 zł. Wynik: 1872

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 17

```text
 Siatka kosztuje 18 zł. Wynik: 18
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 17

```text
 Siatka kosztuje 18 zł. Wynik: 18
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 72

```text
Całkowita długość ogrodzenia to 30 + 24 = 54 m. Zaoszczędzone 4 m to 4 · 18 zł = 72 zł. Zatem całkowity koszt to 54 − 72 = 24 m. Wynik: 24
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 57

```text
Całkowita długość siatki to 30 + 24 + 4 + 4 = 62 metry. Koszt siatki to 62 · 18 = 1116 zł. Wynik: 1116
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 29

```text
 Na siatkę wyda pan 4 · 18 = 72 złoty. Wynik: 72
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 47

```text
 Na siatkę kosztuje 18 zł. Na 4 m wolnego miejsca na bramę kosztuje 18 · 4 = 72 zł. Wynik: 72
```

### matematyka-26 (liczba, trudność 3)

**Polecenie:** Pani Jadwiga wpłaciła 10 000 zł na lokatę na 2 lata z oprocentowaniem 5% w skali roku. Odsetki są dopisywane po każdym roku i potem też się oprocentowują. Ile złotych odsetek zarobi w sumie, nie licząc podatku?

**Wzorzec:** Po roku ma 10 000 · 1,05 = 10 500 zł, po dwóch latach 10 500 · 1,05 = 11 025 zł, więc odsetki to 11 025 − 10 000 = 1025 zł. Wynik: 1025

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 21

```text
 Pani Jadwiga zarobi 6 000 zł. Wynik: 6 000
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 26

```text
 Pani Jadwiga zarobi 10 000 zł · 5% = 5000 zł. Wynik: 5000
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 41

```text
10 000 · 0,05 · 2 = 1000 zł. Wynik: 1000
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 77

```text
Po pierwszym roku zarobi 10 000 · 0,05 = 500 zł. Po drugim roku zarobi 500 · 0,05 = 25 zł. Razem zarobi 500 + 25 = 525 zł. Wynik: 525
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 71

```text
 Po pierwszym roku odsetki to 10 000 · 0,05 = 500 zł. Po drugim roku dodatkowy oprocentowanie to 500 · 0,05 = 25 zł. Wynik: 500 + 25 = 525 zł. Wynik: 525
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 27

```text
 Odsetki są 10 000 · 5 = 500 zł. Wynik: 500
```

### matematyka-27 (liczba, trudność 3)

**Polecenie:** Turysta w Bieszczadach szedł przez 2 godziny z prędkością 5 km/h, a potem przez 1 godzinę pod stromą górę z prędkością 2 km/h. Jaka była jego średnia prędkość na całej trasie w km/h?

**Wzorzec:** Przeszedł 2 · 5 + 1 · 2 = 12 km w 2 + 1 = 3 godziny, więc średnio 12 : 3 = 4 km/h. Wynik: 4

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 49

```text
 Turysta szedł przez 2 godziny z prędkością 5 km/h, a potem przez 1 godzinę pod stromą górę z prędkością 2 km/h. Średnia prędkość na całej trasie w km/h wynosi:
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 36

```text
 Turysta szedł z prędkością 5 km/h. Średnia prędkość na całej trasie to 5 km/h. Wynik: 5 km/h
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 33

```text
Średnia prędkość wynosi (5 + 2) · 3 = 19 km/h. Wynik: 19
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 50

```text
Średnia prędkość wynosi (2 · 5 + 1 · 2) / (2 + 1) = 12 / 3 = 4 km/h. Wynik: 4
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 38

```text
 Średnia prędkość wynosi (5 + 2) / 2 = 3,5 km/h. Wynik: 3,5
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 50

```text
 Turysta pokonał 2 + 1 = 3 godziny. Prędkość na całej trasie wynosi 5 + 2 = 7 km/h. Wynik: 7
```

### matematyka-28 (liczba, trudność 3)

**Polecenie:** Siostry Kasia, Lena i Maja podzieliły 900 zł ze sprzedaży starych rowerów w stosunku 2 : 3 : 4. Ile złotych dostała Maja?

**Wzorzec:** Części jest 2 + 3 + 4 = 9, jedna część to 900 : 9 = 100 zł, więc Maja dostała 4 · 100 = 400 zł. Wynik: 400

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 21

```text
 Maja dostała 2 × 900 = 1800 zł. Wynik: 1800 zł
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 22

```text
 Maja dostała 3 · 900 = 2700 zł. Wynik: 2700
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 28

```text
Maja otrzymała 900 : 9 = 100 zł. Wynik: 100
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 47

```text
Maja dostała 900 ÷ (2 + 3 + 4) = 900 ÷ 9 = 100 zł. Wynik: 100
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 52

```text
 Siostry podzieliły 900 zł w stosunku 2 : 3 : 4. Maja otrzymała 4/2 · 900 = 1800 zł. Wynik: 1800
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 27

```text
 Maja otrzymała 4/9 · 900 = 400 zł. Wynik: 400
```

### matematyka-29 (liczba, trudność 3)

**Polecenie:** Rachunek za obiad w karczmie wyniósł 186 zł. Troje znajomych dodało 10% napiwku i podzieliło całą kwotę po równo. Ile złotych zapłaciła każda osoba?

**Wzorzec:** Napiwek to 18,60 zł, razem 186 + 18,60 = 204,60 zł, więc na osobę 204,60 : 3 = 68,20 zł. Wynik: 68,2

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 20

```text
 186 × 0,10 = 84 zł. Wynik: 84
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 20

```text
 Każda osoba zapłaciła 186 zł. Wynik: 186
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 83

```text
Popiwek wynosi 186 zł × 10% = 18,6 zł. Razem zapłacili 186 zł + 18,6 zł = 204,6 zł. Każdy zapłacił 204,6 zł ÷ 3 = 68,2 zł. Wynik: 68,2
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 87

```text
Napiwek wyniósł 186 zł · 10% = 18,6 zł. Razem zapłacili 186 zł + 18,6 zł = 194,6 zł. Każdy zapłacił 194,6 zł · 1/3 = 64,87 zł. Wynik: 64,87
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 64

```text
 Wraz z napiwem zapłaciła 10% 186 = 18,60 zł. Ilość zapłacona przez każdej osoby to 18,60 / 3 = 6,20 zł. Wynik: 6,20
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 67

```text
 Zaobraz zostało dodane 10% na 186 zł, co daje 186 · 10% = 18,6 zł. Każda osoba zapłaciła 18,6 / 3 = 6,2 zł. Wynik: 6,2
```

### matematyka-30 (liczba, trudność 3)

**Polecenie:** Paweł wychodzi z domu o 7:35. Na przystanek idzie 12 minut, na autobus czeka 8 minut, a jazda do pracy trwa 34 minuty. Ile minut przed 9:00 dotrze do pracy?

**Wzorzec:** Cała droga trwa 12 + 8 + 34 = 54 minuty, więc Paweł dotrze o 8:29, czyli 31 minut przed 9:00. Wynik: 31

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 12

```text
 8. Wynik: 8
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 24

```text
 Po 9:00 Paweł dotrze do pracy o 9:00. Wynik: 9
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 55

```text
O 9:00 jest 60 minut. Wychodzi o 7:35, więc musi się spóźnić 60 − 7:35 = 25 minut. Wynik: 25
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 67

```text
Czas podróży wynosi 34 + 8 + 12 = 54 minuty. Różnica między 9:00 a 7:35 to 145 minut. 145 − 54 = 91 minut. Wynik: 91
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 34

```text
 Dotrze do pracy 7:35 + 12 + 8 + 34 = 71 minut. Wynik: 71
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 34

```text
 Do pracy idzie 7:35 + 12 + 8 + 34 = 61 minut. Wynik: 61
```

## kod

### kod-01 (kod, trudność 1)

**Polecenie:** Napisz funkcję, która zamienia kwotę podaną w groszach na zapis w złotych z przecinkiem i dopiskiem „zł”.  
```python  
def kwota_zl(grosze):  
    """Zamienia kwotę w groszach (liczba całkowita >= 0) na napis w formacie „12,34 zł”."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def kwota_zl(grosze):
    """Zamienia kwotę w groszach (liczba całkowita >= 0) na napis w formacie „12,34 zł”."""
    return f"{grosze // 100},{grosze % 100:02d} zł"
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 58

```text

` ` `python
def kwota_zl(grosze):
    """Zwraca napis w formacie „12,34 zł” w groszach."""
    return grosze.upper() + " ".join(grosze)
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 69

```text

` ` `python
def kwota_zl(grosze):
    """Zamienia kwotę w groszach (liczba całkowita >= 0) na napis w formacie „12,34 zł”."""
    return grosze[:1].upper() + grosze[1:].lower()
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 130

```text

` ` `python
def kwota_zl(grosze):
    """Zamienia kwotę w groszach (liczba całkowita >= 0) na napis w formacie „12,34 zł”."""
    if grosze < 0:
        return '-' + kwota_zl(-grosze)
    return '{:,.2f} zł'.format(grosze / 100)
` ` `
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 110

```text

` ` `python
def kwota_zl(grosze):
    """Zamienia kwotę w groszach (liczba całkowita >= 0) na napis w formacie „12,34 zł”."""
    zl = f"{grosze // 100},{grosze % 100:02} zł"
    return zl
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 65

```text


` ` `python
def kwota_zl(grosze):
    """Zamienia kwotę w groszach (liczba całkowita >= 0) na napis w formacie „12,34 zł”."""
    return f"{grosze:.2f} zł"
` ` `
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

### kod-02 (kod, trudność 1)

**Polecenie:** Napisz funkcję, która usuwa z tekstu polskie znaki diakrytyczne.  
```python  
def usun_polskie_znaki(tekst):  
    """Zamienia polskie litery na odpowiedniki bez znaków diakrytycznych (ą→a, ł→l, ż→z itd.), zachowując wielkość liter."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def usun_polskie_znaki(tekst):
    """Zamienia polskie litery na odpowiedniki bez znaków diakrytycznych (ą→a, ł→l, ż→z itd.), zachowując wielkość liter."""
    return tekst.translate(str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ"))
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 78

```text

` ` `python
def usun_polskie_znaki(tekst):
    """Zamienia polskie litery na odpowiedniki bez znaków diakrytycznych (ą→a, ł→l, ż→z itd.), zachowując wielkość liter."""
    return text.replace('.', 'a', '_')
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 79

```text

` ` `python
def usun_polskie_znaki(tekst):
    """Zamienia polskie litery na odpowiedniki bez znaków diakrytycznych (ą→a, ł→l, ż→z itd.), zachowując wielkość liter."""
    return text.replace(char.upper(), char.lower())
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: limit, tokenów: 256

```text

` ` `python
def usun_polskie_znaki(tekst):
    """Zamienia polskie litery na odpowiedniki bez znaków diakrytycznych (ą→a, ł→l, ż→z itd.), zachowując wielkość liter."""
    return ''.join([chr(ord(c) - ord('Ą')) if c in 'ĄČDĊEČĀFēĐđĉĒĕĐĉėĕĐĉķĕĉĩĕķĕķĕķĭĕĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭĭ
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 119

```text

` ` `python
def usun_polskie_znaki(tekst):
    """Zamienia polskie litery na odpowiedniki bez znaków diakrytycznych (ą→a, ł→l, ż→z itd.), zachowując wielkość liter."""
    return ''.join([chr(ord(c) - ord('ĸ')) if c in 'ĸ' else c for c in tekst])
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 102

```text


` ` `python
def usun_polskie_znaki(tekst):
    """Zamienia polskie litery na odpowiedniki bez znaków diakrytycznych (ą→a, ł→l, ż→z itd.), zachowując wielkość liter."""
    return ''.join(char for char in tekst.lower() if char.isalpha() and char.lower() not in ['ą', 'ł', 'ż']).upper()
` ` `
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 87

```text


` ` `python
def usun_polskie_znaki(tekst):
    """Zamienia polskie litery na odpowiedniki bez znaków diakrytycznych (ą→a, ł→l, ż→z itd.), zachowując wielkość liter."""
    return ''.join(c if c.isalpha() else c for c in tekst)
` ` `
```

### kod-03 (kod, trudność 1)

**Polecenie:** Napisz funkcję, która liczy samogłoski w polskim tekście.  
```python  
def policz_samogloski(tekst):  
    """Zwraca liczbę samogłosek w tekście; samogłoski to a, ą, e, ę, i, o, ó, u, y (bez względu na wielkość liter)."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def policz_samogloski(tekst):
    """Zwraca liczbę samogłosek w tekście; samogłoski to a, ą, e, ę, i, o, ó, u, y (bez względu na wielkość liter)."""
    return sum(1 for znak in tekst.lower() if znak in "aąeęioóuy")
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 78

```text

` ` `python
def policz_samogloski(tekst):
    """Zwraca liczbę samogłosek w tekście; samogłoski to a, ą, e, ę, i, o, ó, u, y (bez względu na wielkość liter)."""
    return len(sorted(text)) + 1
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 85

```text

` ` `python
def policz_samogloski(tekst):
    """Zwraca liczbę samogłosek w tekście; samogłoski to a, ą, e, ę, i, o, ó, u, y (bez względu na wielkość liter)."""
    return sum(v for v in text if v.lower() == 'a')
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 143

```text

` ` `python
def policz_samogloski(tekst):
    """Zwraca liczbę samogłosek w tekście; samogłoski to a, ę, e, i, o, u, y (bez względu na wielkość liter)."""
    samogłoski = 'aeiou'
    zliczone = 0
    for znak in tekst:
        if znak in samogłoski:
            zliczone += 1
    return zliczone
` ` `
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 108

```text

` ` `python
def policz_samogloski(tekst):
    """Zwraca liczbę samogłosek w tekście; samogłoski to a, ą, e, ę, i, o, ó, u, y (bez względu na wielkość liter)."""
    samogloski = 'aeiou'
    return sum(1 for znak in tekst if znak in samogloski)
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 193

```text


` ` `python
def policz_samogloski(tekst):
    """Zwraca liczbę samogłosek w tekście; samogłoski to a, ą, e, ę, i, o, ó, u, y (bez względu na wielkość liter)."""
    samogłoski = {
        'a': 1, 'ą': 1, 'e': 1, 'ę': 1, 'i': 1,
        'o': 1, 'ó': 1, 'u': 1, 'y': 1
    }
    liczba_samogloski = 0
    for litera in tekst:
        if litera in samogłoski:
            liczba_samogloski += samogłoski[litera]
    return liczba_samogloski
` ` `
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: eos, tokenów: 121

```text


` ` `python
def policz_samogloski(tekst):
    """Zwraca liczbę samogłosek w tekście; samogłoski to a, ą, e, ę, i, o, ó, u, y (bez względu na wielkość liter)."""
    samogłoski = "aeiouąęiöü"
    liczba_samogloski = sum(1 for char in tekst if char in samogłoski)
    return liczba_samogloski
` ` `
```

### kod-04 (kod, trudność 1)

**Polecenie:** Napisz funkcję, która sumuje liczby parzyste z listy.  
```python  
def suma_parzystych(liczby):  
    """Zwraca sumę liczb parzystych z listy liczb całkowitych (dla pustej listy 0)."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def suma_parzystych(liczby):
    """Zwraca sumę liczb parzystych z listy liczb całkowitych (dla pustej listy 0)."""
    return sum(x for x in liczby if x % 2 == 0)
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 66

```text

` ` `python
def suma_parzystych(liczby):
    """Zwraca sumę liczb parzystych z listy liczb całkowitych (dla pustej listy 0)."""
    return sum(int(x) for x in numbers if x % 2 == 0)
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 64

```text

` ` `python
def suma_parzystych(liczby):
    """Zwraca sumę liczb parzystych z listy liczb całkowitych (dla pustej listy 0)."""
    return sum(int(x) for x in numbers) if numbers else 0
` ` `
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 81

```text

` ` `python
def suma_parzystych(liczby):
    """Zwraca sumę liczb parzystych z listy liczb całkowitych (dla pustej listy 0)."""
    return sum(x for x in liczby if x % 2 == 0)
` ` `
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 81

```text

` ` `python
def suma_parzystych(liczby):
    """Zwraca sumę liczb parzystych z listy liczb całkowitych (dla pustej listy 0)."""
    return sum(x for x in liczby if x % 2 == 0)
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 75

```text


` ` `python
def suma_parzystych(liczby):
    """Zwraca sumę liczb parzystych z listy liczb całkowitych (dla pustej listy 0)."""
    return sum(x for x in liczby if x % 2 == 0)
` ` `
```

### kod-05 (kod, trudność 1)

**Polecenie:** Napisz funkcję, która sprawdza, czy rok jest przestępny w kalendarzu gregoriańskim.  
```python  
def czy_rok_przestepny(rok):  
    """Zwraca True, gdy rok jest przestępny (podzielny przez 4, ale nie przez 100, chyba że przez 400), w przeciwnym razie False."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def czy_rok_przestepny(rok):
    """Zwraca True, gdy rok jest przestępny (podzielny przez 4, ale nie przez 100, chyba że przez 400), w przeciwnym razie False."""
    return rok % 4 == 0 and (rok % 100 != 0 or rok % 400 == 0)
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 64

```text

` ` `python
def czy_rok_przestepny(rok):
    """Zwraca True, gdy rok jest przestępny (podzielny przez 4, ale nie przez 100, chyba że przez 400), w przeciwnym razie False."""
    return year %4 ==0
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 64

```text

` ` `python
def czy_rok_przestepny(rok):
    """Zwraca True, gdy rok jest przestępny (podzielny przez 4, ale nie przez 100, chyba że przez 400), w przeciwnym razie False."""
    return year % 100 == 0
` ` `
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 117

```text

` ` `python
def czy_rok_przestepny(rok):
    """Zwraca True, gdy rok jest przestępny (podzielny przez 4, ale nie przez 100, chyba że przez 400), w przeciwnym razie False."""
    return rok % 4 == 0 and (rok % 100 != 0 or rok % 400 == 0)
` ` `
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 117

```text

` ` `python
def czy_rok_przestepny(rok):
    """Zwraca True, gdy rok jest przestępny (podzielny przez 4, ale nie przez 100, chyba że przez 400), w przeciwnym razie False."""
    return rok % 4 == 0 and (rok % 100 != 0 or rok % 400 == 0)
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 3

```text
 `True`
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 105

```text


` ` `python
def czy_rok_przestepny(rok):
    """Zwraca True, gdy rok jest przestępny (podzielny przez 4, ale nie przez 100, chyba że przez 400), w przeciwnym razie False."""
    if rok % 4 == 0 and rok % 100 != 0 and rok % 400 == 0:
        return True
    return False
` ` `
```

### kod-06 (kod, trudność 1)

**Polecenie:** Napisz funkcję, która tworzy inicjały z imion i nazwiska.  
```python  
def inicjaly(osoba):  
    """Zwraca inicjały wszystkich słów napisu jako wielkie litery z kropkami, np. „Jan Kowalski” → „J.K.”."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def inicjaly(osoba):
    """Zwraca inicjały wszystkich słów napisu jako wielkie litery z kropkami, np. „Jan Kowalski” → „J.K.”."""
    return "".join(slowo[0].upper() + "." for slowo in osoba.split())
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 52

```text

` ` `python
def inicjaly(osoba):
    """Zwraca inicjały wszystkich słów napisu jako wielkie litery z kropkami, np. „Jan Kowalski” → „J.K.”."""
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 77

```text

` ` `python
def inicjaly(osoba):
    """Zwraca inicjały wszystkich słów napisu jako wielkie litery z kropkami, np. „Jan Kowalski” → „J.K.”."""
    return [osoba.upper() for os in os.lower() if os.upper()]
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 123

```text

` ` `python
def inicjaly(osoba):
    """Zwraca inicjały wszystkich słów napisu jako wielkie litery z kropkami, np. „Jan Kowalski” → „J.K.”."""
    imiona = osoba.split()
    return '. '.join([f"{i.capitalize()}." for i in imiona])
` ` `
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 116

```text

` ` `python
def inicjaly(osoba):
    """Zwraca inicjały wszystkich słów napisu jako wielkie litery z kropkami, np. „Jan Kowalski” → „J.K.”."""
    return '. '.join([word[0].upper() + '.' for word in osoba.split()])
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

### kod-07 (kod, trudność 1)

**Polecenie:** Napisz funkcję, która liczy cenę brutto z ceny netto i stawki VAT.  
```python  
def cena_brutto(netto, stawka_vat):  
    """Zwraca cenę brutto zaokrągloną do 2 miejsc po przecinku; stawka VAT jest podana w procentach."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def cena_brutto(netto, stawka_vat):
    """Zwraca cenę brutto zaokrągloną do 2 miejsc po przecinku; stawka VAT jest podana w procentach."""
    return round(netto * (1 + stawka_vat / 100), 2)
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 83

```text

` ` `python
def cena_brutto(netto, stawka_vat):
    """Zwraca cenę brutto zaokrągloną do 2 miejsc po przecinku; stawka VAT jest podana w procentach."""
    return netto.price_percentage + (netto.price * stawka_vat)
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 80

```text

` ` `python
def cena_brutto(netto, stawka_vat):
    """Zwraca cenę brutto zaokrągloną do 2 miejsc po przecinku; stawka VAT jest podana w procentach."""
    return netto.upper() + (netto.lower() * stawka_vat)
` ` `
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 91

```text

` ` `python
def cena_brutto(netto, stawka_vat):
    """Zwraca cenę brutto zaokrągloną do 2 miejsc po przecinku; stawka VAT jest podana w procentach."""
    return round(netto * (1 + stawka_vat / 100), 2)
` ` `
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 116

```text

` ` `python
def cena_brutto(netto, stawka_vat):
    """Zwraca cenę brutto zaokrągloną do 2 miejsc po przecinku; stawka VAT jest podana w procentach."""
    vat = (stawka_vat / 100) * netto
    cena_brutto = netto + vat
    return round(cena_brutto, 2)
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 88

```text


` ` `python
def cena_brutto(netto, stawka_vat):
    """Zwraca cenę brutto zaokrągloną do 2 miejsc po przecinku; stawka VAT jest podana w procentach."""
    return round(netto * (1 + stawka_vat / 100), 2)
` ` `
```

### kod-08 (kod, trudność 1)

**Polecenie:** Napisz funkcję, która znajduje najdłuższe słowo w zdaniu.  
```python  
def najdluzsze_slowo(zdanie):  
    """Zwraca najdłuższe słowo zdania (słowa rozdzielone spacjami); przy remisie pierwsze z nich, dla pustego napisu pusty napis."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def najdluzsze_slowo(zdanie):
    """Zwraca najdłuższe słowo zdania (słowa rozdzielone spacjami); przy remisie pierwsze z nich, dla pustego napisu pusty napis."""
    slowa = zdanie.split()
    return max(slowa, key=len) if slowa else ""
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 66

```text

` ` `python
def najdluzsze_slowo(zdanie):
    """Zwraca najdłuższe słowo zdania (słowa rozdzielone spacjami); przy remisie pierwsze z nich, dla pustego napisu pusty napis."""
    return len(zdanie) + 1
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 64

```text

` ` `python
def najdluzsze_slowo(zdanie):
    """Zwraca najdłuższe słowo zdania (słowa rozdzielone spacjami); przy remisie pierwsze z nich, dla pustego napisu pusty napis."""
    return len(zdanie)
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 139

```text

` ` `python
def najdluzsze_slowo(zdanie):
    """Zwraca najdłuższe słowo zdania (słowa rozdzielone spacjami); przy remisie pierwsze z nich, dla pustego napisu pusty napis."""
    najdłuższe = ''
    dla slowo w zdanie:
        jeśli len(slab) > len(najdluzsze):
            najdłuższe = slowo
    return najdłuższe
` ` `
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 111

```text

` ` `python
def najdluzsze_slowo(zdanie):
    """Zwraca najdłuższe słowo zdania (słowa rozdzielone spacjami); przy remisie pierwsze z nich, dla pustego napisu pusty napis."""
    słowa = zdanie.split()
    najdluzsze = max(słowa, key=len)
    return najdluzsze
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 80

```text


` ` `python
def najdluzsze_slowo(zdanie):
    """Zwraca najdłuższe słowo zdania (słowa rozdzielone spacjami); przy remisie pierwsze z nich, dla pustego napisu pusty napis."""
    return max(zdanie, key=len) if zdanie else ""
` ` `
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: eos, tokenów: 113

```text


` ` `python
def najdluzsze_slowo(zdanie):
    """Zwraca najdłuższe słowo zdania (słowa rozdzielone spacjami); przy remisie pierwsze z nich, dla pustego napisu pusty napis."""
    words = zdanie.split()
    if not words:
        return ""
    max_length = max(len(word) for word in words)
    return words[0] if len(words) == max_length else words[1]
` ` `
```

### kod-09 (kod, trudność 1)

**Polecenie:** Napisz funkcję, która odwraca kolejność słów w zdaniu.  
```python  
def odwroc_kolejnosc_slow(zdanie):  
    """Zwraca zdanie ze słowami w odwrotnej kolejności, rozdzielonymi pojedynczą spacją."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def odwroc_kolejnosc_slow(zdanie):
    """Zwraca zdanie ze słowami w odwrotnej kolejności, rozdzielonymi pojedynczą spacją."""
    return " ".join(reversed(zdanie.split()))
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 55

```text

` ` `python
def odwroc_kolejnosc_slow(zdanie):
    """Zwraca zdanie ze słowami w odwrotnej kolejności, rozdzielonymi pojedynczą spacją."""
    return zdanie.rreverse()
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 54

```text

` ` `python
def odwroc_kolejnosc_slow(zdanie):
    """Zwraca zdanie ze słowami w odwrotnej kolejności, rozdzielonymi pojedynczą spacją."""
    return zdanie.reverse()
` ` `
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 82

```text

` ` `python
def odwroc_kolejnosc_slow(zdanie):
    """Zwraca zdanie ze słowami w odwrotnej kolejności, rozdzielonymi pojedynczą spacją."""
    return ' '.join(reversed(zdanie.split()))
` ` `
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 82

```text

` ` `python
def odwroc_kolejnosc_slow(zdanie):
    """Zwraca zdanie ze słowami w odwrotnej kolejności, rozdzielonymi pojedynczą spacją."""
    return ' '.join(reversed(zdanie.split()))
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

### kod-10 (kod, trudność 1)

**Polecenie:** Napisz funkcję, która przelicza temperaturę ze stopni Celsjusza na stopnie Fahrenheita.  
```python  
def na_fahrenheity(celsjusze):  
    """Zwraca temperaturę w stopniach Fahrenheita dla temperatury podanej w stopniach Celsjusza."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def na_fahrenheity(celsjusze):
    """Zwraca temperaturę w stopniach Fahrenheita dla temperatury podanej w stopniach Celsjusza."""
    return celsjusze * 9 / 5 + 32
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 62

```text

` ` `python
def na_fahrenheity(celsjusze):
    """Zwraca temperaturę w stopniach Fahrenheita dla temperatury podanej w stopniach Celsjusza."""
    return (celsjusze * 32) / 5
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 62

```text

` ` `python
def na_fahrenheity(celsjusze):
    """Zwraca temperaturę w stopniach Fahrenheita dla temperatury podanej w stopniach Celsjusza."""
    return celsjusze.fahrenheit()
` ` `
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 83

```text

` ` `python
def na_fahrenheity(celsjusze):
    """Zwraca temperaturę w stopniach Fahrenheita dla temperatury podanej w stopniach Celsjusza."""
    return (celsjusze * 9 / 5) + 32
` ` `
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 82

```text

` ` `python
def na_fahrenheity(celsjusze):
    """Zwraca temperaturę w stopniach Fahrenheita dla temperatury podanej w stopniach Celsjusza."""
    return (celsjusze * 9/5) + 32
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

### kod-11 (kod, trudność 2)

**Polecenie:** Napisz funkcję, która zwraca liczbę razem z poprawnie odmienionym słowem „plik”.  
```python  
def odmien_pliki(n):  
    """Zwraca liczbę z poprawnie odmienionym słowem „plik”, np. „1 plik”, „3 pliki”, „5 plików” (n >= 0)."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def odmien_pliki(n):
    """Zwraca liczbę z poprawnie odmienionym słowem „plik”, np. „1 plik”, „3 pliki”, „5 plików” (n >= 0)."""
    if n == 1:
        forma = "plik"
    elif n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        forma = "pliki"
    else:
        forma = "plików"
    return f"{n} {forma}"
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 57

```text

` ` `python
def odmien_pliki(n):
    """Zwraca liczbę z poprawnie odmienionym słowem „plik”, np. „1 plik”, „3 pliki”, „5 plików” (n >= 0)."""
    return n
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 63

```text

` ` `python
def odmien_pliki(n):
    """Zwraca liczbę z poprawnie odmienionym słowem „plik”, np. „1 plik”, „3 pliki”, „5 plików” (n >= 0)."""
    return n * (n - 1)
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 115

```text

` ` `python
def odmien_pliki(n):
    """Zwraca liczbę z poprawnie odmienionym słowem „plik”, np. „1 plik”, „3 pliki”, „5 plików” (n >= 0)."""
    return str(n) + " pliki" if n else "plik"
` ` `
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 121

```text

` ` `python
def odmien_pliki(n):
    """Zwraca liczbę z poprawnie odmienionym słowem „plik”, np. „1 plik”, „3 pliki”, „5 plików” (n >= 0)."""
    return f"{n} plik" if n == 1 else f"{n} pliki"
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: eos, tokenów: 89

```text


` ` `python
def odmien_pliki(n):
    """Zwraca liczbę z poprawnie odmienionym słowem „plik”, np. „1 plik”, „3 pliki”, „5 plików” (n >= 0)."""
    if n < 0:
        return "Nieprawidłowa liczba"
    return str(n)
` ` `
```

### kod-12 (kod, trudność 2)

**Polecenie:** Napisz funkcję, która zapisuje datę słownie z polską nazwą miesiąca.  
```python  
def data_slownie(data):  
    """Zamienia datę w formacie RRRR-MM-DD na zapis „7 marca 2024” (dzień bez zera wiodącego, miesiąc w dopełniaczu)."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def data_slownie(data):
    """Zamienia datę w formacie RRRR-MM-DD na zapis „7 marca 2024” (dzień bez zera wiodącego, miesiąc w dopełniaczu)."""
    miesiace = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
                "lipca", "sierpnia", "września", "października", "listopada", "grudnia"]
    rok, miesiac, dzien = data.split("-")
    return f"{int(dzien)} {miesiace[int(miesiac) - 1]} {rok}"
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 77

```text

` ` `python
def data_slownie(data):
    """Zamienia datę w formacie RRRR-MM-DD na zapis „7 marca 2024” (dzień bez zera wiodącego, miesiąc w dopełniaczu)."""
    return data[:3].upper() + data[3:].lower()
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 72

```text

` ` `python
def data_slownie(data):
    """Zamienia datę w formacie RRRR-MM-DD na zapis „7 marca 2024” (dzień bez zera wiodącego, miesiąc w dopełniaczu)."""
    return data.upper() + data.lower()
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 242

```text

` ` `python
def data_slownie(data):
    """Zamienia datę w formacie RRRR-MM-DD na zapis „7 marca 2024” (dzień bez zera wiodącego, miesiąc w dopełniaczu)."""
    rok, miesiąc, dzień = data.split('-')
    miesiąc_polski = {'styczeń': 'styczeń', 'luty': 'luty', 'marzec': 'marzec', 'kwiecień': 'kwiecień', 'maj': 'maj', 'czerwiec': 'czerwiec', 'lipiec': 'lipiec', 'sierpień': 'sierpień', 'wrzesień': 'wrzesień', 'październik': 'październik', 'listopad': 'listopad', 'grudzień': 'grudzień'}
    return f"{dzień} {miesiąc_polski[miesięcz]} {rok}"
` ` `
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: limit, tokenów: 256

```text

` ` `python
def data_slownie(data):
    """Zamienia datę w formacie RRRR-MM-DD na zapis „7 marca 2024” (dzień bez zera wiodącego, miesiąc w dopełniaczu)."""
    rok, miesiąc, dzień = data.split('-')
    miesiąc_polski = {
        'styczeń': 'styczeń',
        'luty': 'luty',
        'marzec': 'marzec',
        'kwiecień': 'kwiecień',
        'maj': 'maj',
        'czerwiec': 'czerwiec',
        'lipiec': 'lipiec',
        'sierpień': 'sierpień',
        'wrzesień': 'wrzesień',
 
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 89

```text


` ` `python
def data_slownie(data):
    """Zamienia datę w formacie RRRR-MM-DD na zapis „7 marca 2024” (dzień bez zera wiodącego, miesiąc w dopełniaczu)."""
    return data[:4] + data[4:7] + data[7:]
` ` `
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 89

```text


` ` `python
def data_slownie(data):
    """Zamienia datę w formacie RRRR-MM-DD na zapis „7 marca 2024” (dzień bez zera wiodącego, miesiąc w dopełniaczu)."""
    return data[:4] + data[4:6] + data[6:]
` ` `
```

### kod-13 (kod, trudność 2)

**Polecenie:** Napisz funkcję, która zwraca polską nazwę dnia tygodnia dla podanej daty.  
```python  
def dzien_tygodnia(data):  
    """Zwraca polską nazwę dnia tygodnia (małymi literami) dla daty w formacie RRRR-MM-DD."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def dzien_tygodnia(data):
    """Zwraca polską nazwę dnia tygodnia (małymi literami) dla daty w formacie RRRR-MM-DD."""
    from datetime import date
    dni = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
    return dni[date.fromisoformat(data).weekday()]
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 59

```text

` ` `python
def dzien_tygodnia(data):
    """Zwraca polską nazwę dnia tygodnia (małymi literami) dla daty w formacie RRRR-MM-DD."""
    return data[:5].lower()
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 63

```text

` ` `python
def dzien_tygodnia(data):
    """Zwraca polską nazwę dnia tygodnia (małymi literami) dla daty w formacie RRRR-MM-DD."""
    return data.upper() + data.lower()
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 214

```text

` ` `python
def dzien_tygodnia(data):
    """Zwraca polską nazwę dnia tygodnia (małymi literami) dla daty w formacie RRRR-MM-DD."""
    dni_tygodnia = {
        1: "Poniedziałek",
        2: "Wtorek",
        3: "Środa",
        4: "Czwartek",
        5: "Piątek",
        6: "Sobota",
        7: "Niedziela"
    }
    return dni_tygodnia.get(data.weekday(), "Nieznana data")
` ` `
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 125

```text

` ` `python
def dzien_tygodnia(data):
    """Zwraca polską nazwę dnia tygodnia (małymi literami) dla daty w formacie RRRR-MM-DD."""
    dni_tygodnia = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
    return dni_tygodnia[date.weekday()]
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 70

```text


` ` `python
def dzien_tygodnia(data):
    """Zwraca polską nazwę dnia tygodnia (małymi literami) dla daty w formacie RRRR-MM-DD."""
    return data[:4].lower() + data[4:]
` ` `
```

### kod-14 (kod, trudność 2)

**Polecenie:** Napisz funkcję, która sprawdza, czy tekst jest palindromem.  
```python  
def czy_palindrom(tekst):  
    """Sprawdza, czy tekst czytany wspak jest taki sam, pomijając wielkość liter, spacje i znaki interpunkcyjne."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def czy_palindrom(tekst):
    """Sprawdza, czy tekst czytany wspak jest taki sam, pomijając wielkość liter, spacje i znaki interpunkcyjne."""
    znaki = [z.lower() for z in tekst if z.isalnum()]
    return znaki == znaki[::-1]
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 66

```text

` ` `python
def czy_palindrom(tekst):
    """Sprawdza, czy tekst czytany wspak jest taki sam, pomijając wielkość liter, spacje i znaki interpunkcyjne."""
    return text.isspace() and text.isalnum()
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 64

```text

` ` `python
def czy_palindrom(tekst):
    """Sprawdza, czy tekst czytany wspak jest taki sam, pomijając wielkość liter, spacje i znaki interpunkcyjne."""
    return text.upper() == text.lower()
` ` `
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 106

```text

` ` `python
def czy_palindrom(tekst):
    """Sprawdza, czy tekst czytany wspak jest taki sam, pomijając wielkość liter, spacje i znaki interpunkcyjne."""
    tekst = ''.join(c for c in tekst if c.isalpha()).lower()
    return tekst == tekst[::-1]
` ` `
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 107

```text

` ` `python
def czy_palindrom(tekst):
    """Sprawdza, czy tekst czytany wspak jest taki sam, pomijając wielkość liter, spacje i znaki interpunkcyjne."""
    tekst = ''.join(filter(str.isalnum, tekst.lower()))
    return text == text[::-1]
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 74

```text


` ` `python
def czy_palindrom(tekst):
    """Sprawdza, czy tekst czytany wspak jest taki sam, pomijając wielkość liter, spacje i znaki interpunkcyjne."""
    return tekst.lower() == tekst.lower()[::-1]
` ` `
```

### kod-15 (kod, trudność 2)

**Polecenie:** Napisz funkcję, która liczy wystąpienia słów w tekście.  
```python  
def zlicz_slowa(tekst):  
    """Zwraca słownik {słowo: liczba wystąpień} dla słów tekstu zamienionych na małe litery; słowa rozdzielają spacje, kropki i przecinki."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def zlicz_slowa(tekst):
    """Zwraca słownik {słowo: liczba wystąpień} dla słów tekstu zamienionych na małe litery; słowa rozdzielają spacje, kropki i przecinki."""
    wynik = {}
    for slowo in tekst.lower().replace(".", " ").replace(",", " ").split():
        wynik[slowo] = wynik.get(slowo, 0) + 1
    return wynik
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 78

```text

` ` `python
def zlicz_slowa(tekst):
    """Zwraca słownik {słowo: liczba wystąpień} dla słów tekstu zamienionych na małe litery; słowa rozdzielają spacje, kropki i przecinki."""
    return {word: count(text) for word in text.lower()}
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 78

```text

` ` `python
def zlicz_slowa(tekst):
    """Zwraca słownik {słowo: liczba wystąpień} dla słów tekstu zamienionych na małe litery; słowa rozdzielają spacje, kropki i przecinki."""
    return {word: count(word) for word in text.lower()}
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 140

```text

` ` `python
def zlicz_slowa(tekst):
    """Zwraca słownik {słowo: liczba wystąpień} dla słów tekstu zamienionych na małe litery; słowa rozdzielają spacje, kropki i przecinki."""
    słowa = text.lower().split(' ') + text.lower().split('. ') + text.lower().split('? ')
    return {word: s.count(word) for word in set(words)}
` ` `
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 184

```text

` ` `python
def zlicz_slowa(tekst):
    """Zwraca słownik {słowo: liczba wystąpień} dla słów tekstu zamienionych na małe litery; słowa rozdzielają spacje, kropki i przecinki."""
    z_tekst = tekst.lower().replace('.', ' ').replace(',', ' ').split()
    z_wystepowan = {}
    for slowo in z_tekst:
        z_wystepowan[slowo] = z_wystepowan.get(slowo, 0) + 1
    return z_wystepowan
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 134

```text


` ` `python
def zlicz_slowa(tekst):
    """Zwraca słownik {słowo: liczba wystąpień} dla słów tekstu zamienionych na małe litery; słowa rozdzielają spacje, kropki i przecinki."""
    słownik = {}
    for słowo in tekst.lower().split():
        if słowo in słownik:
            słownik[słowo] += 1
        else:
            słownik[słowo] = 1
    return słownik
` ` `
```

### kod-16 (kod, trudność 2)

**Polecenie:** Napisz funkcję, która skraca serie powtarzających się znaków w napisie.  
```python  
def kompresuj(napis):  
    """Skraca serie powtarzających się znaków: „aaabcc” → „a3bc2” (liczbę dopisuje tylko dla serii dłuższych niż 1)."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def kompresuj(napis):
    """Skraca serie powtarzających się znaków: „aaabcc” → „a3bc2” (liczbę dopisuje tylko dla serii dłuższych niż 1)."""
    wynik = ""
    i = 0
    while i < len(napis):
        j = i
        while j < len(napis) and napis[j] == napis[i]:
            j += 1
        wynik += napis[i] + (str(j - i) if j - i > 1 else "")
        i = j
    return wynik
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 56

```text

` ` `python
def kompresuj(napis):
    """Skraca serie powtarzających się znaków: „aaabcc” → „a3bc2” (liczbę dopisuje tylko dla serii dłuższych niż 1)."""
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 96

```text

` ` `python
def kompresuj(napis):
    """Skraca serie powtarzających się znaków: „aaabcc” → „a3bc2” (liczbę dopisuje tylko dla serii dłuższych niż 1)."""
    return [napis[i] for i in range(len(napis)) if napis[i] == 'a' and napis[i] == 'b']
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 247

```text

` ` `python
def kompresuj(napis):
    """Skraca serie powtarzających się znaków: „aaabcc” → „a3bc2” (liczbę dopisuje tylko dla serii dłuższych niż 1)."""
    if not napis:
        return ''
    prev, count = napis[0], 1
    for char in napis[1:]:
        if char == prev:
            count += 1
        else:
            yield prev * count
            count = 1
            prev = char
    yield prev * count
` ` `
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 244

```text

` ` `python
def kompresuj(napis):
    """Skraca serie powtarzających się znaków: „aaabcc” → „a3bc2” (liczbę dopisuje tylko dla serii dłuższych niż 1)."""
    z_liter = []
    for znak in napis:
        if z_liter and z_liter[-1] == znak:
            z_liter[-1] += 1
        else:
            z_liter.append(znak)
            z_liter.append(str(z_liter[-1]))
    return ''.join(z_liter)
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 99

```text


` ` `python
def kompresuj(napis):
    """Skraca serie powtarzających się znaków: „aaabcc” → „a3bc2” (liczbę dopisuje tylko dla serii dłuższych niż 1)."""
    if len(napis) == 1:
        return napis
    else:
        return napis[:1] + napis[1:]
` ` `
```

### kod-17 (kod, trudność 2)

**Polecenie:** Napisz funkcję, która dzieli rachunek w groszach między kilka osób co do grosza.  
```python  
def podziel_rachunek(grosze, osoby):  
    """Dzieli kwotę w groszach na podaną liczbę osób tak, by części różniły się najwyżej o 1 grosz i sumowały do całości; większe części idą na początek listy."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def podziel_rachunek(grosze, osoby):
    """Dzieli kwotę w groszach na podaną liczbę osób tak, by części różniły się najwyżej o 1 grosz i sumowały do całości; większe części idą na początek listy."""
    czesc, reszta = divmod(grosze, osoby)
    return [czesc + 1 if i < reszta else czesc for i in range(osoby)]
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 76

```text

` ` `python
def podziel_rachunek(grosze, osoby):
    """Dzieli kwotę w groszach na podaną liczbę osób tak, by części różniły się najwyżej o 1 grosz i sumowały do całości; większe części idą na początek listy."""
    return groszes.split(osoby, 0)
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 76

```text

` ` `python
def podziel_rachunek(grosze, osoby):
    """Dzieli kwotę w groszach na podaną liczbę osób tak, by części różniły się najwyżej o 1 grosz i sumowały do całości; większe części idą na początek listy."""
    return grosze.divide(osoby, 1)
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: limit, tokenów: 256

```text

` ` `python
def podziel_rachunek(grosze, osoby):
    """Dzieli kwotę w groszach na podaną liczbę osób tak, by części różniły się najwyżej o 1 grosz i sumowały do całości; większe części idą na początek listy."""
    if nie osoby:
        return [0] * osoby
    
    grosze = int(grosze)
    osoby = int(osobę)
    
    if nie grosze:
        return [0] * osoby
    
    if nie osoby:
        return [0] * osoby
    
    if grosze < 0:
        return [0] * osoby
    
    if osoby < 1:
        return [0] * osoby
    
    grosze += osoby
    grosze += 1
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 206

```text

` ` `python
def podziel_rachunek(grosze, osoby):
    """Dzieli kwotę w groszach na podaną liczbę osób tak, by części różniły się najwyżej o 1 grosz i sumowały do całości; większe części idą na początek listy."""
    if nie osoby:
        return [0] * osoby
    
    dzielenie = [0] * osoby
    dzielenie[0] = grosze
    
    for i in range(1, osoby):
        dzielenie[i] = dzielenie[i-1] - 1
        dzielenie[i] += dzielenie[i-1]
    
    return dzielenie
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 140

```text


` ` `python
def podziel_rachunek(grosze, osoby):
    """Dzieli kwotę w groszach na podaną liczbę osób tak, by części różniły się najwyżej o 1 grosz i sumowały do całości; większe części idą na początek listy."""
    if grosze == 0:
        return 0
    if osoby == 0:
        return grosze
    if grosze % osoby != 0:
        return grosze // osoby
    return grosze // osoby + grosze % osoby
` ` `
```

### kod-18 (kod, trudność 2)

**Polecenie:** Napisz funkcję, która formatuje numer rachunku bankowego w grupach cyfr.  
```python  
def formatuj_nrb(numer):  
    """Formatuje 26-cyfrowy numer rachunku: najpierw 2 cyfry, potem grupy po 4 cyfry, rozdzielone spacjami; spacje w wejściu są pomijane."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def formatuj_nrb(numer):
    """Formatuje 26-cyfrowy numer rachunku: najpierw 2 cyfry, potem grupy po 4 cyfry, rozdzielone spacjami; spacje w wejściu są pomijane."""
    cyfry = numer.replace(" ", "")
    grupy = [cyfry[:2]] + [cyfry[i:i + 4] for i in range(2, len(cyfry), 4)]
    return " ".join(grupy)
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 97

```text

` ` `python
def formatuj_nrb(numer):
    """Formatuje 26-cyfrowy numer rachunku: najpierw 2 cyfry, potem grupy po 4 cyfry, rozdzielone spacjami; spacje w wejściu są pomijane."""
    numer = numer[::-1]
    if numer == 0:
        return "0"
    else:
        return numer[:2] + numer[2:]
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 76

```text

` ` `python
def formatuj_nrb(numer):
    """Formatuje 26-cyfrowy numer rachunku: najpierw 2 cyfry, potem grupy po 4 cyfry, rozdzielone spacjami; spacje w wejściu są pomijane."""
    return [numer[0] for numer in numer[:2]]
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: limit, tokenów: 256

```text

` ` `python
def formatuj_nrb(numer):
    """Formatuje 26-cyfrowy numer rachunku: najpierw 2 cyfry, potem grupy po 4 cyfry, rozdzielone spacjami; spacje w wejściu są pomijane."""
    numer = numer.replace(' ', '')
    return '{:02} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:0
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: limit, tokenów: 256

```text

` ` `python
def formatuj_nrb(numer):
    """Formatuje 26-cyfrowy numer rachunku: najpierw 2 cyfry, potem grupy po 4 cyfry, rozdzielone spacjami; spacje w wejściu są pomijane."""
    return '{:02} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04} {:04
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 122

```text


` ` `python
def formatuj_nrb(numer):
    """Formatuje 26-cyfrowy numer rachunku: najpierw 2 cyfry, potem grupy po 4 cyfry, rozdzielone spacjami; spacje w wejściu są pomijane."""
    return f"{num[:2]}{' '.join(map(str, map(int, zip(range(4), range(4, 12)))))}{' ' * (len(num) - 4)}"
` ` `
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 86

```text


` ` `python
def formatuj_nrb(numer):
    """Formatuje 26-cyfrowy numer rachunku: najpierw 2 cyfry, potem grupy po 4 cyfry, rozdzielone spacjami; spacje w wejściu są pomijane."""
    return f"{numer:04d}"
` ` `
```

### kod-19 (kod, trudność 2)

**Polecenie:** Napisz funkcję, która sortuje listę osób według nazwiska.  
```python  
def sortuj_po_nazwisku(osoby):  
    """Sortuje listę napisów „Imię Nazwisko” według nazwiska, a przy równych nazwiskach według imienia."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def sortuj_po_nazwisku(osoby):
    """Sortuje listę napisów „Imię Nazwisko” według nazwiska, a przy równych nazwiskach według imienia."""
    return sorted(osoby, key=lambda osoba: (osoba.split()[1], osoba.split()[0]))
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 74

```text

` ` `python
def sortuj_po_nazwisku(osoby):
    """Sortuje listę napisów „Imię Nazwisko” według nazwiska, a przy równych nazwiskach według imienia."""
    return sorted(osoby, key=lambda x: x[1], reverse=True)
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 74

```text

` ` `python
def sortuj_po_nazwisku(osoby):
    """Sortuje listę napisów „Imię Nazwisko” według nazwiska, a przy równych nazwiskach według imienia."""
    return sorted(osoby, key=lambda x: x[1], reverse=True)
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 114

```text

` ` `python
def sortuj_po_nazwisku(osoby):
    """Sortuje listę napisów „Imię Nazwisko” według nazwiska, a przy równych nazwiskach według imienia."""
    return sorted(osoby, key=lambda x: (x[-1].split()[0], x[-1].split()[1]))
` ` `
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 100

```text

` ` `python
def sortuj_po_nazwisku(osoby):
    """Sortuje listę napisów „Imię Nazwisko” według nazwiska, a przy równych nazwiskach według imienia."""
    return sorted(osoby, key=lambda x: (x[1], x[0]))
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 81

```text


` ` `python
def sortuj_po_nazwisku(osoby):
    """Sortuje listę napisów „Imię Nazwisko” według nazwiska, a przy równych nazwiskach według imienia."""
    return sorted(osoby, key=lambda x: (x[0], x[1]))
` ` `
```

### kod-20 (kod, trudność 2)

**Polecenie:** Napisz funkcję, która zapisuje liczbę minut jako godziny i minuty.  
```python  
def czas_slownie(minuty):  
    """Zamienia liczbę minut (>= 0) na napis „H h MM min”, np. 125 → „2 h 05 min”."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def czas_slownie(minuty):
    """Zamienia liczbę minut (>= 0) na napis „H h MM min”, np. 125 → „2 h 05 min”."""
    return f"{minuty // 60} h {minuty % 60:02d} min"
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 53

```text

` ` `python
def czas_slownie(minuty):
    """Zamienia liczbę minut (>= 0) na napis „H h MM min”, np. 125 → „2 h 05 min”."""
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 60

```text

` ` `python
def czas_slownie(minuty):
    """Zamienia liczbę minut (>= 0) na napis „H h MM min”, np. 125 → „2 h 05 min”."""
    return min(minutes)
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 178

```text

` ` `python
def czas_slownie(minuty):
    """Zamienia liczbę minut (>= 0) na napis „H h MM min”, np. 125 → „2 h 05 min”."""
    if minuty < 60:
        return f"{int(minuty)} min"
        
    hours = int(minuty / 60)
    minutes = int(minuty % 60)
    return f"{hours} h {minutes} min"
` ` `
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 130

```text

` ` `python
def czas_slownie(minuty):
    """Zamienia liczbę minut (>= 0) na napis „H h MM min”, np. 125 → „2 h 05 min”."""
    h = minuty // 60
    m = minuty % 60
    return f"{h} h {m:02} min"
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

### kod-21 (kod, trudność 3)

**Polecenie:** Napisz funkcję, która zapisuje liczbę od 0 do 99 słownie po polsku.  
```python  
def liczba_slownie(n):  
    """Zwraca zapis słowny liczby całkowitej od 0 do 99, np. 42 → „czterdzieści dwa”."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def liczba_slownie(n):
    """Zwraca zapis słowny liczby całkowitej od 0 do 99, np. 42 → „czterdzieści dwa”."""
    jednosci = ["zero", "jeden", "dwa", "trzy", "cztery", "pięć", "sześć", "siedem", "osiem", "dziewięć",
                "dziesięć", "jedenaście", "dwanaście", "trzynaście", "czternaście", "piętnaście",
                "szesnaście", "siedemnaście", "osiemnaście", "dziewiętnaście"]
    dziesiatki = ["", "", "dwadzieścia", "trzydzieści", "czterdzieści", "pięćdziesiąt",
                  "sześćdziesiąt", "siedemdziesiąt", "osiemdziesiąt", "dziewięćdziesiąt"]
    if n < 20:
        return jednosci[n]
    d, j = divmod(n, 10)
    return dziesiatki[d] + (" " + jednosci[j] if j else "")
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 74

```text

` ` `python
def liczba_slownie(n):
    """Zwraca zapis słowny liczby całkowitej od 0 do 99, np. 42 → „czterdzieści dwa”."""
    return str(n) + '_' + str(n) + '_' + '_' + '_'
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: limit, tokenów: 256

```text

` ` `python
def liczba_slownie(n):
    """Zwraca zapis słowny liczby całkowitej od 0 do 99, np. 42 → „czterdzieści dwa”."""
    return '42' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '' + '
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: limit, tokenów: 256

```text

` ` `python
def liczba_slownie(n):
    """Zwraca zapis słowny liczby całkowitej od 0 do 99, np. 42 → „czterdzieści dwa”."""
    słownie = {'0': 'zero', '1': 'jeden', '2': 'dwa', '3': 'trzy', '4': 'cztery', '5': 'pięć', '6': 'sześć', '7': 'siedem', '8': 'osiem', '9': 'dziewięć', '10': 'dziesięć', '11': 'jedenaście', '12': 'dwanaście', '13': 'trzynaście', '14': 'czternaście', '15': 'piętnaście', '16': 'szesnaście', '17': 'siedemnaście', '18': 'osiemnaście', '19': 'dziewiętnaście', '20': '
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 191

```text

` ` `python
def liczba_slownie(n):
    """Zwraca zapis słowny liczby całkowitej od 0 do 99, np. 42 → „czterdzieści dwa”."""
    if n < 0:
        return "minus" + liczba_slownie(-n)
    if n < 10:
        return str(n)
    if n < 100:
        return liczba_slownie(n // 10 * 10) + " " + liczba_slownie(n % 10)
    return ""
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

### kod-22 (kod, trudność 3)

**Polecenie:** Napisz funkcję, która sprawdza poprawność numeru NIP według sumy kontrolnej.  
```python  
def czy_nip_poprawny(nip):  
    """Sprawdza NIP (10 cyfr, dopuszczalne myślniki): suma pierwszych 9 cyfr pomnożonych przez wagi 6, 5, 7, 2, 3, 4, 5, 6, 7 modulo 11 musi być równa ostatniej cyfrze."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def czy_nip_poprawny(nip):
    """Sprawdza NIP (10 cyfr, dopuszczalne myślniki): suma pierwszych 9 cyfr pomnożonych przez wagi 6, 5, 7, 2, 3, 4, 5, 6, 7 modulo 11 musi być równa ostatniej cyfrze."""
    cyfry = nip.replace("-", "")
    if len(cyfry) != 10 or not cyfry.isdigit():
        return False
    wagi = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    reszta = sum(w * int(c) for w, c in zip(wagi, cyfry)) % 11
    return reszta == int(cyfry[9])
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 109

```text

` ` `python
def czy_nip_poprawny(nip):
    """Sprawdza NIP (10 cyfr, dopuszczalne myślniki): suma pierwszych 9 cyfr pomnożonych przez wagi 6, 5, 7, 2, 3, 4, 5, 6, 7 modulo 11 musi być równa ostatniej cyfrze."""
    return sum( (nip) * (nip) for nip in numeric_values(numbers) ) % 11
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 111

```text

` ` `python
def czy_nip_poprawny(nip):
    """Sprawdza NIP (10 cyfr, dopuszczalne myślniki): suma pierwszych 9 cyfr pomnożonych przez wagi 6, 5, 7, 2, 3, 4, 5, 6, 7 modulo 11 musi być równa ostatniej cyfrze."""
    return sum(nip) % (11 * (6 + 5 + 7 + 2 + 3 + 4 + 5 + 6 + 7))
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 177

```text

` ` `python
def czy_nip_poprawny(nip):
    """Sprawdza NIP (10 cyfr, dopuszczalne myślniki): suma pierwszych 9 cyfr pomnożonych przez wagi 6, 5, 7, 2, 3, 4, 5, 6, 7 modulo 11 musi być równa ostatniej cyfrze."""
    zsumowane = sum([int(x) * (6 + 5 * i) % 11 for i, x in enumerate(nip[::-1])])
    return zsumowane % 11 == int(nip[-1])
` ` `
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: limit, tokenów: 256

```text

` ` `python
def czy_nip_poprawny(nip):
    """Sprawdza NIP (10 cyfr, dopuszczalne myślniki): suma pierwszych 9 cyfr pomnożonych przez wagi 6, 5, 7, 2, 3, 4, 5, 6, 7 modulo 11 musi być równa ostatniej cyfrze."""
    suma = 0
    dla cyfry w nip:
        suma += int(cyfr) * (6, 5, 7, 2, 3, 4, 5, 6, 7)[0]
        waga = (6, 5, 7, 2, 3, 4, 5, 6, 7)[0]
        waga -= 1
        waga %= 11
        waga += 1
        waga %= 11
  
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 189

```text


` ` `python
def czy_nip_poprawny(nip):
    """Sprawdza NIP (10 cyfr, dopuszczalne myślniki): suma pierwszych 9 cyfr pomnożonych przez wagi 6, 5, 7, 2, 3, 4, 5, 6, 7 modulo 11 musi być równa ostatniej cyfrze."""
    n = nip
    for cyfra in nip[:-1]:
        cyfra = cyfra * 10
    for cyfra in nip[-1:]:
        cyfra = cyfra // 10
    n = (n * 6 + cyfra * 5 + cyfra * 7) % 11
    return str(nip) == str(nip[-1])
` ` `
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 175

```text


` ` `python
def czy_nip_poprawny(nip):
    """Sprawdza NIP (10 cyfr, dopuszczalne myślniki): suma pierwszych 9 cyfr pomnożonych przez wagi 6, 5, 7, 2, 3, 4, 5, 6, 7 modulo 11 musi być równa ostatniej cyfrze."""
    if len(nip) != 10:
        return False
    suma = 0
    for i in range(9):
        suma += int(nip[i]) * (i + 1) * 6
    suma += int(nip[9]) * 7
    return suma % 11 == 0
` ` `
```

### kod-23 (kod, trudność 3)

**Polecenie:** Napisz funkcję, która sprawdza cyfry kontrolne polskiego numeru IBAN.  
```python  
def czy_iban_pl_poprawny(iban):  
    """Sprawdza polski IBAN: „PL” i 26 cyfr (spacje pomijane); po przeniesieniu pierwszych 4 znaków na koniec i zamianie P na 25, a L na 21 liczba modulo 97 musi dać 1."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def czy_iban_pl_poprawny(iban):
    """Sprawdza polski IBAN: „PL” i 26 cyfr (spacje pomijane); po przeniesieniu pierwszych 4 znaków na koniec i zamianie P na 25, a L na 21 liczba modulo 97 musi dać 1."""
    s = iban.replace(" ", "").upper()
    if len(s) != 28 or not s.startswith("PL") or not s[2:].isdigit():
        return False
    return int(s[4:] + "2521" + s[2:4]) % 97 == 1
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 87

```text

` ` `python
def czy_iban_pl_poprawny(iban):
    """Sprawdza polski IBAN: „PL” i 26 cyfr (spacje pomijane); po przeniesieniu pierwszych 4 znaków na koniec i zamianie P na 25, a L na 21 liczba modulo 97 musi dać 1."""
    return len(p) % 97 == 0
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 95

```text

` ` `python
def czy_iban_pl_poprawny(iban):
    """Sprawdza polski IBAN: „PL” i 26 cyfr (spacje pomijane); po przeniesieniu pierwszych 4 znaków na koniec i zamianie P na 25, a L na 21 liczba modulo 97 musi dać 1."""
    return (iban.isdigit() and iban.isdigit())
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 242

```text

` ` `python
def czy_iban_pl_poprawny(iban):
    """Sprawdza polski IBAN: „PL” i 26 cyfr (spacje pomijane); po przeniesieniu pierwszych 4 znaków na koniec i zamianie P na 25, a L na 21 liczba modulo 97 musi dać 1."""
    if len(iban) != 26:
        return False
    if iban[0] != 'P' or iban[1] != 'L':
        return False
    iban = iban[4:] + iban[0:4]
    n = 0
    for c in iban:
        n += 97 * int(c)
    return n % 97 == 1
` ` `
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: limit, tokenów: 256

```text

` ` `python
def czy_iban_pl_poprawny(iban):
    """Sprawdza polski IBAN: „PL” i 26 cyfr (spacje pomijane); po przeniesieniu pierwszych 4 znaków na koniec i zamianie P na 25, a L na 21 liczba modulo 97 musi dać 1."""
    if iban[:2] != 'PL':
        return False
    
    iban = iban[2:] + iban[0:2]
    
    if len(iban) != 26:
        return False
    
    iban = iban.replace(' ', '')
    
    if len(iban) != 26:
        return False
    
    if iban[0:4] !=
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 202

```text


` ` `python
def czy_iban_pl_poprawny(iban):
    """Sprawdza polski IBAN: „PL” i 26 cyfr (spacje pomijane); po przeniesieniu pierwszych 4 znaków na koniec i zamianie P na 25, a L na 21 liczba modulo 97 musi dać 1."""
    if len(iban) < 4:
        return False
    i1 = abs(iban[0] - 'P')
    i2 = abs(iban[1] - 'L')
    if i1 == 25 and i2 == 21:
        return True
    i3 = abs(iban[2] - '25')
    i4 = abs(iban[3] - '21')
    if i3 == 97 and i4 == 1:
        return True
    return False
` ` `
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 188

```text


` ` `python
def czy_iban_pl_poprawny(iban):
    """Sprawdza polski IBAN: „PL” i 26 cyfr (spacje pomijane); po przeniesieniu pierwszych 4 znaków na koniec i zamianie P na 25, a L na 21 liczba modulo 97 musi dać 1."""
    if len(iban) != 26:
        return False
    if not all(c.isdigit() for c in iban):
        return False
    if iban[0] != 'PL':
        return False
    if iban[4] != '25':
        return False
    if iban[5] != '21':
        return False
    return (iban[4] + 25) % 97 == 1
` ` `
```

### kod-24 (kod, trudność 3)

**Polecenie:** Napisz funkcję, która scala nachodzące na siebie przedziały liczbowe.  
```python  
def scal_przedzialy(przedzialy):  
    """Scala nachodzące lub stykające się przedziały domknięte [a, b] i zwraca je jako listę list posortowaną rosnąco."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def scal_przedzialy(przedzialy):
    """Scala nachodzące lub stykające się przedziały domknięte [a, b] i zwraca je jako listę list posortowaną rosnąco."""
    wynik = []
    for a, b in sorted(przedzialy):
        if wynik and a <= wynik[-1][1]:
            wynik[-1][1] = max(wynik[-1][1], b)
        else:
            wynik.append([a, b])
    return wynik
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 96

```text

` ` `python
def scal_przedzialy(przedzialy):
    """Scala nachodzące lub stykające się przedziały domknięte [a, b] i zwraca je jako listę list posortowaną rosnąco."""
    return [przedzialy[0] for przedzialy in przedzialy if przedzialy[1:] < przedzialy[0]]
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 80

```text

` ` `python
def scal_przedzialy(przedzialy):
    """Scala nachodzące lub stykające się przedziały domknięte [a, b] i zwraca je jako listę list posortowaną rosnąco."""
    return [przedzialy[0] for przedzialy in przedzialy]
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 218

```text

` ` `python
def scal_przedzialy(przedzialy):
    """Scala nachodzące lub stykające się przedziały domknięte [a, b] i zwraca je jako listę list posortowaną rosnąco."""
    scal_przedzialy = []
    for a, b in przedzialy:
        if scal_przedzialy and scal_przedzialy[-1][1] <= a:
            scal_przedzialy[-1][1] = b
        else:
            scal_przedzialy.append([a, b])
    return scal_przedzialy
` ` `
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 139

```text

` ` `python
def scal_przedzialy(przedzialy):
    """Scala nachodzące lub stykające się przedziały domknięte [a, b] i zwraca je jako listę list posortowaną rosnąco."""
    przedzialy.sort()
    return [[a, b] for a, b in zip(przedzialy, przedzialy[1:] + [float('inf')]) if b - a > 0]
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 85

```text


` ` `python
def scal_przedzialy(przedzialy):
    """Scala nachodzące lub stykające się przedziały domknięte [a, b] i zwraca je jako listę list posortowaną rosnąco."""
    return sorted(przedzialy, key=lambda x: x[0])
` ` `
```

### kod-25 (kod, trudność 3)

**Polecenie:** Napisz funkcję, która liczy dni robocze (od poniedziałku do piątku) między dwiema datami.  
```python  
def dni_robocze(poczatek, koniec):  
    """Zwraca liczbę dni od poniedziałku do piątku w przedziale dat RRRR-MM-DD z oboma końcami włącznie (0, gdy początek jest po końcu)."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def dni_robocze(poczatek, koniec):
    """Zwraca liczbę dni od poniedziałku do piątku w przedziale dat RRRR-MM-DD z oboma końcami włącznie (0, gdy początek jest po końcu)."""
    from datetime import date, timedelta
    dzien = date.fromisoformat(poczatek)
    ostatni = date.fromisoformat(koniec)
    licznik = 0
    while dzien <= ostatni:
        if dzien.weekday() < 5:
            licznik += 1
        dzien += timedelta(days=1)
    return licznik
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 90

```text

` ` `python
def dni_robocze(poczatek, koniec):
    """Zwraca liczbę dni od poniedziałku do piątku w przedziale dat RRRR-MM-DD z oboma końcami włącznie (0, gdy początek jest po końcu)."""
    return len(list(range(1, 10))) + len(list(range(1, 10)))
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 99

```text

` ` `python
def dni_robocze(poczatek, koniec):
    """Zwraca liczbę dni od poniedziałku do piątku w przedziale dat RRRR-MM-DD z oboma końcami włącznie (0, gdy początek jest po końcu)."""
    return sum(days_from_end(poczatek, koniec) for day in days_robocze(poczatek, koniec))
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: limit, tokenów: 256

```text

` ` `python
def dni_robocze(poczatek, koniec):
    """Zwraca liczbę dni od poniedziałku do piątku w przedziale dat RRRR-MM-DD z oboma końcami włącznie (0, gdy początek jest po końcu)."""
    # Zamień przecinki na kropki, aby nie używać niepotrzebnego formatu
    poczatek = poczatek.replace('.', ',')
    koniec = koniec.replace('.', ',')
    
    # Podziel na miesiące i dni
    date_parts = poczatek.split('-')
    miesiąc_start = int(date_parts[1])
    dzien_start = int(date_parts[2])
    rok_start = int(date_parts[0])
    
    date_parts = koniec.split('-')
    miesiąc_end = int(date_parts[
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: limit, tokenów: 256

```text

` ` `python
def dni_robocze(poczatek, koniec):
    """Zwraca liczbę dni od poniedziałku do piątku w przedziale dat RRRR-MM-DD z oboma końcami włącznie (0, gdy początek jest po końcu)."""
    dni_robocze = 0
    for date in range(poczatek.year, koniec.year + 1):
        for month in range(1, 13):
            if month == 2:
                if date % 4 == 0 and date % 100 != 0 or date % 400 == 0:
                    dni_robocze += 29
                else:
            
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 110

```text


` ` `python
def dni_robocze(poczatek, koniec):
    """Zwraca liczbę dni od poniedziałku do piątku w przedziale dat RRRR-MM-DD z oboma końcami włącznie (0, gdy początek jest po końcu)."""
    if początek == koniec:
        return 0
    return (koniec - początek + 1) % 7
` ` `
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 117

```text


` ` `python
def dni_robocze(poczatek, koniec):
    """Zwraca liczbę dni od poniedziałku do piątku w przedziale dat RRRR-MM-DD z oboma końcami włącznie (0, gdy początek jest po końcu)."""
    if początek > koniec:
        początek, koniec = koniec, początek
    return (koniec - początek) // 7
` ` `
```

### kod-26 (kod, trudność 3)

**Polecenie:** Napisz funkcję, która zwraca k najczęstszych słów tekstu.  
```python  
def najczestsze_slowa(tekst, k):  
    """Zwraca listę k najczęstszych słów tekstu (zamienionych na małe litery, rozdzielonych spacjami); przy równej liczbie wystąpień słowa idą alfabetycznie."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def najczestsze_slowa(tekst, k):
    """Zwraca listę k najczęstszych słów tekstu (zamienionych na małe litery, rozdzielonych spacjami); przy równej liczbie wystąpień słowa idą alfabetycznie."""
    licznik = {}
    for slowo in tekst.lower().split():
        licznik[slowo] = licznik.get(slowo, 0) + 1
    return sorted(licznik, key=lambda s: (-licznik[s], s))[:k]
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 89

```text

` ` `python
def najczestsze_slowa(tekst, k):
    """Zwraca listę k najczęstszych słów tekstu (zamienionych na małe litery, rozdzielonych spacjami); przy równej liczbie wystąpień słowa idą alfabetycznie."""
    words = list(tekst.split()).filter(k)
    return [word.lower() for word in words]
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 83

```text

` ` `python
def najczestsze_slowa(tekst, k):
    """Zwraca listę k najczęstszych słów tekstu (zamienionych na małe litery, rozdzielonych spacjami); przy równej liczbie wystąpień słowa idą alfabetycznie."""
    return [word.lower() for word in text if word.count(k) == k]
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 179

```text

` ` `python
def najczestsze_slowa(tekst, k):
    """Zwraca listę k najczęstszych słów tekstu (zamienionych na małe litery, rozdzielonych spacjami); przy równej liczbie wystąpień słowa idą alfabetycznie."""
    from collections import Counter
    słowa = tekst.lower().split()
    częstot = Counter(słowa)
    częstot = częstot.most_common(k)
    częstot = [word for word, _ in częstot]
    częstot = ' '.join([word for word, _ in częstot]).split()
    return częstot
` ` `
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 129

```text

` ` `python
def najczestsze_slowa(tekst, k):
    """Zwraca listę k najczęstszych słów tekstu (zamienionych na małe litery, rozdzielonych spacjami); przy równej liczbie wystąpień słowa idą alfabetycznie."""
    from collections import Counter
    słowa = tekst.lower().split()
    najczestsze = Counter(słowa)
    najczestsze.most_common(k)
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 126

```text


` ` `python
def najczestsze_slowa(tekst, k):
    """Zwraca listę k najczęstszych słów tekstu (zamienionych na małe litery, rozdzielonych spacjami); przy równej liczbie wystąpień słowa idą alfabetycznie."""
    s = tekst.lower().split()
    s = [s[i].lower() for i in range(len(s))]
    return sorted(s, key=lambda x: (-s.count(x), x))
` ` `
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: eos, tokenów: 246

```text


` ` `python
def najczestsze_slowa(tekst, k):
    """Zwraca listę k najczęstszych słów tekstu (zamienionych na małe litery, rozdzielonych spacjami); przy równej liczbie wystąpień słowa idą alfabetycznie."""
    # Zmieniając tekst na małe litery i rozdzielając na słowa
    słowa = tekst.lower().split()
    # Zestawiając słowa według ich częstości
    krotki = {}
    for s in słowa:
        if s in krotki:
            krotki[s] += 1
        else:
            krotki[s] = 1
    # Zestawiając najczęstsze k słowa
    najczestsze = sorted(krotki.items(), key=lambda x: x[1], reverse=True)[:k]
    # Zwraca listę k najczęstszych słów
    return [s[0] for s in najczestsze]
` ` `
```

### kod-27 (kod, trudność 3)

**Polecenie:** Napisz funkcję, która szyfruje tekst szyfrem Cezara w polskim alfabecie.  
```python  
def szyfr_cezara_pl(tekst, przesuniecie):  
    """Szyfruje tekst pisany małymi literami szyfrem Cezara w alfabecie „aąbcćdeęfghijklłmnńoóprsśtuwyzźż” (32 litery, przesunięcie może być ujemne); inne znaki zostają bez zmian."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def szyfr_cezara_pl(tekst, przesuniecie):
    """Szyfruje tekst pisany małymi literami szyfrem Cezara w alfabecie „aąbcćdeęfghijklłmnńoóprsśtuwyzźż” (32 litery, przesunięcie może być ujemne); inne znaki zostają bez zmian."""
    alfabet = "aąbcćdeęfghijklłmnńoóprsśtuwyzźż"
    wynik = ""
    for znak in tekst:
        if znak in alfabet:
            wynik += alfabet[(alfabet.index(znak) + przesuniecie) % len(alfabet)]
        else:
            wynik += znak
    return wynik
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 96

```text

` ` `python
def szyfr_cezara_pl(tekst, przesuniecie):
    """Szyfruje tekst pisany małymi literami szyfrem Cezara w alfabecie „aąbcćdeęfghijklłmnńoóprsśtuwyzźż” (32 litery, przesunięcie może być ujemne); inne znaki zostają bez zmian."""
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 108

```text

` ` `python
def szyfr_cezara_pl(tekst, przesuniecie):
    """Szyfruje tekst pisany małymi literami szyfrem Cezara w alfabecie „aąbcćdeęfghijklłmnńoóprsśtuwyzźż” (32 litery, przesunięcie może być ujemne); inne znaki zostają bez zmian."""
    return tekst.upper() + tekst.lower()
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: limit, tokenów: 256

```text

` ` `python
def szyfr_cezara_pl(tekst, przesuniecie):
    """Szyfruje tekst pisany małymi literami szyfrem Cezara w alfabecie „aąbcćdeęfghijklłmnńoóprsśtuwyzźż” (32 litery, przesunięcie może być ujemne); inne znaki zostają bez zmian."""
    alfabet = "aąbcćdeęfghijklłmnńoóprsśtuwyzźż"
    szyfrowany = ""
    for znak in tekst:
        if znak.isalpha():
            indeks = alfabet.index(znak.lower())
            szyfrowany += alfabet[(indek + przesuniecie) % 32]
        elif not znak.isalpha():
         
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: limit, tokenów: 256

```text

` ` `python
def szyfr_cezara_pl(tekst, przesuniecie):
    """Szyfruje tekst pisany małymi literami szyfrem Cezara w alfabecie „aąbcćdeęfghijklłmnńoóprsśtuwyzźż” (32 litery, przesunięcie może być ujemne); inne znaki zostają bez zmian."""
    alfabet = 'aąbcćdeęfghijklłmnńoóprsśtuwyzźż'
    szyfrowany = ''
    for znak in tekst:
        if znak.isalpha():
            if znak.isupper():
                szyfrowany += alfabet[(alfabet.index(znak.lower()) + przesuniecie) % 32].upper()
            else:
 
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: limit, tokenów: 256

```text


` ` `python
def szyfr_cezara_pl(tekst, przesunięcie):
    """Szyfruje tekst pisany małymi literami szyfrem Cezara w alfabecie „aąbcćdeęfghijklłmnńoóprsśtuwyzźż” (32 litery, przesunięcie może być ujemne); inne znaki zostają bez zmian."""
    a = ord('a')
    b = ord('b')
    c = ord('c')
    d = ord('d')
    e = ord('e')
    f = ord('f')
    g = ord('g')
    h = ord('h')
    i = ord('i')
    j = ord('j')
    k = ord('k')
    l = ord('l')
    m = ord('m')
    n = ord('n')
    o = ord('o')
    p = ord('p')
    r = ord('r')
    s = ord('s')
    t = ord('t')
    u = ord('u')
    v = ord('v')
    w = ord('w')
   
```

### kod-28 (kod, trudność 3)

**Polecenie:** Napisz funkcję, która spłaszcza dowolnie zagnieżdżoną listę.  
```python  
def splaszcz(lista):  
    """Zwraca płaską listę wszystkich elementów z dowolnie zagnieżdżonych list, w kolejności występowania."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def splaszcz(lista):
    """Zwraca płaską listę wszystkich elementów z dowolnie zagnieżdżonych list, w kolejności występowania."""
    wynik = []
    for element in lista:
        if isinstance(element, list):
            wynik.extend(splaszcz(element))
        else:
            wynik.append(element)
    return wynik
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 53

```text

` ` `python
def splaszcz(lista):
    """Zwraca płaską listę wszystkich elementów z dowolnie zagnieżdżonych list, w kolejności występowania."""
    return list(map(int, list))
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 57

```text

` ` `python
def splaszcz(lista):
    """Zwraca płaską listę wszystkich elementów z dowolnie zagnieżdżonych list, w kolejności występowania."""
    return [lista[0] for list in lista]
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 169

```text

` ` `python
def splaszcz(lista):
    """Zwraca płaską listę wszystkich elementów z dowolnie zagnieżdżonych list, w kolejności występowania."""
    def splaszcz_reku(lst):
        if isinstance(lst, list):
            return [item for item in splaszcz_reku(item) for item in lst]
        else:
            return [lst]
    return splaszcz_reku(lista)
` ` `
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 73

```text

` ` `python
def splaszcz(lista):
    """Zwraca płaską listę wszystkich elementów z dowolnie zagnieżdżonych list, w kolejności występowania."""
    return [item for element in lista for item in element]
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 66

```text


` ` `python
def splaszcz(lista):
    """Zwraca płaską listę wszystkich elementów z dowolnie zagnieżdżonych list, w kolejności występowania."""
    return [item for sublist in lista for item in sublist]
` ` `
```

### kod-29 (kod, trudność 3)

**Polecenie:** Napisz funkcję, która znajduje długość najdłuższej rosnącej serii kolejnych elementów listy.  
```python  
def najdluzsza_seria_rosnaca(liczby):  
    """Zwraca długość najdłuższego spójnego fragmentu listy, w którym każda liczba jest większa od poprzedniej (dla pustej listy 0)."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def najdluzsza_seria_rosnaca(liczby):
    """Zwraca długość najdłuższego spójnego fragmentu listy, w którym każda liczba jest większa od poprzedniej (dla pustej listy 0)."""
    if not liczby:
        return 0
    najdluzsza = biezaca = 1
    for i in range(1, len(liczby)):
        biezaca = biezaca + 1 if liczby[i] > liczby[i - 1] else 1
        najdluzsza = max(najdluzsza, biezaca)
    return najdluzsza
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 74

```text

` ` `python
def najdluzsza_seria_rosnaca(liczby):
    """Zwraca długość najdłuższego spójnego fragmentu listy, w którym każda liczba jest większa od poprzedniej (dla pustej listy 0)."""
    return len(set(list)) if len(list) > 0 else 0
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 75

```text

` ` `python
def najdluzsza_seria_rosnaca(liczby):
    """Zwraca długość najdłuższego spójnego fragmentu listy, w którym każda liczba jest większa od poprzedniej (dla pustej listy 0)."""
    return len(list(range(len(list) - 1)) + 1)
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 233

```text

` ` `python
def najdluzsza_seria_rosnaca(liczby):
    """Zwraca długość najdłuższego spójnego fragmentu listy, w którym każda liczba jest większa od poprzedniej (dla pustej listy 0)."""
    seria = []
    for i in range(1, len(liczby)):
        if liczby[i] > liczby[i - 1]:
            seria.append(liczby[i])
            if len(seria) > 1 and liczby[i] - liczby[i - 1] >= 2:
                seria.append(liczby[i - 1])
    return len(seria) if seria else 0
` ` `
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 233

```text

` ` `python
def najdluzsza_seria_rosnaca(liczby):
    """Zwraca długość najdłuższego spójnego fragmentu listy, w którym każda liczba jest większa od poprzedniej (dla pustej listy 0)."""
    if not liczby:
        return 0
    seria = [liczby[0]]
    max_seria = 1
    for num in liczby[1:]:
        if num > seria[-1]:
            seria.append(num)
            max_seria = max(max_seria, len(seria))
        else:
            seria = [num]
    return max_seria
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: eos, tokenów: 173

```text


` ` `python
def najdluzsza_seria_rosnaca(liczby):
    """Zwraca długość najdłuższego spójnego fragmentu listy, w którym każda liczba jest większa od poprzedniej (dla pustej listy 0)."""
    if not liczby:
        return 0
    najdłuższa_seria = [liczby[0]]
    for liczba in liczby[1:]:
        if liczba > najdłuższa_seria[-1]:
            najdłuższa_seria = [liczby[0]] + najdłuższa_seria
    return len(najdłuższa_seria)
` ` `
```

### kod-30 (kod, trudność 3)

**Polecenie:** Napisz funkcję, która liczy podatek dochodowy według podanej w opisie uproszczonej skali.  
```python  
def podatek_skala(dochod):  
    """Liczy podatek: 12% od dochodu do 120000 zł i 32% od nadwyżki ponad 120000 zł, minus kwota zmniejszająca 3600 zł; wynik zaokrąglony do pełnych złotych, nie mniejszy niż 0."""  
```

**Wzorzec (rozwiązanie wzorcowe):**

```text
` ` `python
def podatek_skala(dochod):
    """Liczy podatek: 12% od dochodu do 120000 zł i 32% od nadwyżki ponad 120000 zł, minus kwota zmniejszająca 3600 zł; wynik zaokrąglony do pełnych złotych, nie mniejszy niż 0."""
    if dochod <= 120000:
        podatek = dochod * 0.12
    else:
        podatek = 120000 * 0.12 + (dochod - 120000) * 0.32
    return max(0, round(podatek - 3600))
` ` `
```

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 94

```text

` ` `python
def podatek_skala(dochod):
    """Liczy podatek: 12% od dochodu do 120000 zł i 32% od nadwyżki ponad 120000 zł, minus kwota zmniejszająca 3600 zł; wynik zaokrąglony do pełnych złotych, nie mniejszy niż 0."""
    return sum(dochod) / (do + 3600) if do <= 120000 else 0
` ` `
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 80

```text

` ` `python
def podatek_skala(dochod):
    """Liczy podatek: 12% od dochodu do 120000 zł i 32% od nadwyżki ponad 120000 zł, minus kwota zmniejszająca 3600 zł; wynik zaokrąglony do pełnych złotych, nie mniejszy niż 0."""
    return dochod / 120000
` ` `
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 177

```text

` ` `python
def podatek_skala(dochod):
    """Liczy podatek: 12% od dochodu do 120000 zł i 32% od nadwyżki ponad 120000 zł, minus kwota zmniejszająca 3600 zł; wynik zaokrąglony do pełnych złotych, nie mniejszy niż 0."""
    if dochod <= 120000:
        return dochod * 0.12
    else:
        return 120000 * 0.12 + (dochod - 120000) * 0.32
` ` `
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 189

```text

` ` `python
def podatek_skala(dochod):
    """Liczy podatek: 12% od dochodu do 120000 zł i 32% od nadwyżki ponad 120000 zł, minus kwota zmniejszająca 3600 zł; wynik zaokrąglony do pełnych złotych, nie mniejszy niż 0."""
    if dochod <= 120000:
        return dochod * 0.12
    else:
        return 120000 * 0.12 + (dochod - 120000) * 0.32 - 3600
` ` `
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 166

```text


` ` `python
def podatek_skala(dochod):
    """Liczy podatek: 12% od dochodu do 120000 zł i 32% od nadwyżki ponad 120000 zł, minus kwota zmniejszająca 3600 zł; wynik zaokrąglony do pełnych złotych, nie mniejszy niż 0."""
    niedostatek = 120000 - dochodu
    podatek = (niedostatek * 0.12) + (niedostatek * 0.32)
    podatek -= 3600
    podatek = round(podatek, 2)
    return podatek
` ` `
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 155

```text


` ` `python
def podatek_skala(dochod):
    """Liczy podatek: 12% od dochodu do 120000 zł i 32% od nadwyżki ponad 120000 zł, minus kwota zmniejszająca 3600 zł; wynik zaokrąglony do pełnych złotych, nie mniejszy niż 0."""
    podatek = (dochod * 0.12) if dochod <= 120000 else (dochod * 0.32)
    podatek -= 3600
    podatek = round(podatek, 2)
    return podatek
` ` `
```

## angielski

### angielski-01 (krotka, trudność 1)

**Polecenie:** What is the plural of the noun 'child'?

**Wzorzec:** children

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 6

```text
 children
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 6

```text
 children
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
children
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
children
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 children
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 children
```

### angielski-02 (krotka, trudność 1)

**Polecenie:** What is the past simple form of the verb 'go'?

**Wzorzec:** went

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 I went
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 6

```text
 go
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 5

```text
(pusta odpowiedź)```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 24

```text

The past simple form of the verb 'go' is 'went'.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 went
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 went
```

### angielski-03 (krotka, trudność 1)

**Polecenie:** Translate the Polish word „pies” into English.

**Wzorzec:** dog

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 6

```text
 dogs
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 6

```text
 dogs
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 5

```text
(pusta odpowiedź)```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 5

```text
(pusta odpowiedź)```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 4

```text
 pie
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 4

```text
 pie
```

### angielski-04 (krotka, trudność 1)

**Polecenie:** What is the opposite of the word 'up'?

**Wzorzec:** down

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 6

```text
 up
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 6

```text
 up
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 6

```text
down
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 6

```text
down
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 down
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 down
```

### angielski-05 (krotka, trudność 1)

**Polecenie:** How many days are there in one week?

**Wzorzec:** seven

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 8

```text
 Weekdays
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 13

```text
 There are 7 days in one week.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 15

```text
There are seven days in a week.
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 15

```text
There are 1 day in one week.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 12

```text
 There are 7 days in one week.
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 There are seven days in one week.
```

### angielski-06 (krotka, trudność 1)

**Polecenie:** Translate the Polish word „czerwony” into English.

**Wzorzec:** red

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
 the colour red
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 14

```text
 The word „czerwony” means red.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 6

```text
red
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 6

```text
red
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 red
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 red
```

### angielski-07 (krotka, trudność 2)

**Polecenie:** What is the past participle of the verb 'write'?

**Wzorzec:** written

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 I wrote
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 6

```text
 write
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 8

```text
Written
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
written
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 4

```text
 wrote
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 4

```text
 wrote
```

### angielski-08 (krotka, trudność 2)

**Polecenie:** Fill in the gap with the correct preposition: 'She is very interested ___ music.'

**Wzorzec:** in

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 12

```text
 She is very interested in music.
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 12

```text
 She is very interested in music.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 14

```text
She is very interested in music.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 14

```text
She is very interested in music.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 10

```text
 She is very interested in music.
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 10

```text
 She is very interested in music.
```

### angielski-09 (krotka, trudność 2)

**Polecenie:** What is the plural of the noun 'mouse' (the small animal)?

**Wzorzec:** mice

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 6

```text
 mice
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 6

```text
 mice
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
mice
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
mice
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 mice
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 mice
```

### angielski-10 (krotka, trudność 2)

**Polecenie:** Translate the Polish word „biblioteka” into English.

**Wzorzec:** library

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 a library
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 15

```text
 The library is a place where books are kept.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: eos, tokenów: 36

```text

The Polish word „biblioteka” translates to „library” in English.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 8

```text
library
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 library
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 library
```

### angielski-11 (krotka, trudność 2)

**Polecenie:** What is the comparative form of the adjective 'good'?

**Wzorzec:** better

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 6

```text
 good
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 6

```text
 good
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 5

```text
(pusta odpowiedź)```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
better
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 4

```text
 good
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 4

```text
 good
```

### angielski-12 (krotka, trudność 3)

**Polecenie:** What is the plural of the noun 'phenomenon'?

**Wzorzec:** phenomena

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 6

```text
 phenomena
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 7

```text
 phenomenons
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
phenomena
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
phenomena
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 phenomena
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 phenomena
```

### angielski-13 (krotka, trudność 3)

**Polecenie:** Fill in the gap with the correct preposition: 'Whether we go out depends ___ the weather.'

**Wzorzec:** on

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 16

```text
 'Whether we go out depends on the weather.'
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 16

```text
 'Whether we go out depends on the weather.'
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 19

```text
Whether we go out depends on the weather.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 19

```text
Whether we go out depends on the weather.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 12

```text
 whether we go out depends on the weather.
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 12

```text
 whether we go out depends on the weather.
```

### angielski-14 (krotka, trudność 3)

**Polecenie:** Translate into English the Polish verb „pożyczyć” in the meaning 'to give something to someone for a time' (Pożyczę ci mój rower).

**Wzorzec:** lend

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 21

```text
 The Polish verb „pożyczyć” means to give something for a time.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 15

```text
 I will give you my bike for a time.
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: eos, tokenów: 0

```text
(pusta odpowiedź)
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 5

```text
(pusta odpowiedź)```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 12

```text
 To give me a bike for a while.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 17

```text
 pożyczyć (to give something to someone for a time)
```

### angielski-15 (krotka, trudność 3)

**Polecenie:** What is the past simple form of the verb 'catch'?

**Wzorzec:** caught

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 6

```text
 catch
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 6

```text
 catch
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 27

```text

The past simple form of the verb 'catch' is 'caught'.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 27

```text

The past simple form of the verb 'catch' is 'caught'.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 caught
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 caught
```

### angielski-16 (krotka, trudność 3)

**Polecenie:** What is the chemical symbol of gold?

**Wzorzec:** Au

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 6

```text
 g
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 7

```text
 Au
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 6

```text
Au
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 16

```text

The chemical symbol of gold is Au.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 Au
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 4

```text
 Au
```

### angielski-17 (zdanie, trudność 1)

**Polecenie:** Correct the mistake in the sentence and write the whole sentence: She don't like coffee.

**Wzorzec:** She doesn't like coffee.

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 She doesn't like coffee.
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 She doesn't like coffee.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 16

```text
She doesn't like coffee.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 16

```text
She doesn't like coffee.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 She doesn't like coffee.
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 She doesn't like coffee.
```

### angielski-18 (zdanie, trudność 1)

**Polecenie:** Correct the mistake in the sentence and write the whole sentence: I have two brother and one sister.

**Wzorzec:** I have two brothers and one sister.

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 13

```text
 I have two brother and one sister.
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 13

```text
 I have two brothers and one sister.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 15

```text
I have two brothers and one sister.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 15

```text
I have two brothers and one sister.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 I have two brothers and one sister.
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 I have two brothers and one sister.
```

### angielski-19 (zdanie, trudność 2)

**Polecenie:** Correct the mistake in the sentence and write the whole sentence: He has lived in this town since five years.

**Wzorzec:** He has lived in this town for five years.

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 15

```text
 He has lived in this town for five years.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 15

```text
 He has lived in this town since five years.
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 21

```text
He has lived in this town since five years ago.
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 21

```text
He has lived in this town since five years ago.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 13

```text
 He has lived in this town for five years.
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 13

```text
 He has lived in this town for five years.
```

### angielski-20 (zdanie, trudność 2)

**Polecenie:** Correct the mistake in the sentence and write the whole sentence: If I will see him tomorrow, I will tell him the news.

**Wzorzec:** If I see him tomorrow, I will tell him the news.

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 19

```text
 If I will see him tomorrow, I will tell him the news.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 19

```text
 If I will see him tomorrow, I will tell him the news.
```

**Bielik 1.5B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 23

```text
If I will see him tomorrow, I will tell him the news.
```

**Bielik 1.5B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 23

```text
If I will see him tomorrow, I will tell him the news.
```

**LFM2.5 1.2B, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 17

```text
 If I will see him tomorrow, I will tell him the news.
```

**LFM2.5 1.2B, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 17

```text
 If I will see him tomorrow, I will tell him the news.
```

### angielski-21 (zdanie, trudność 2)

**Polecenie:** Correct the mistake in the sentence and write the whole sentence: There is many people in the waiting room.

**Wzorzec:** There are many people in the waiting room.

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 14

```text
 There are many people in the waiting room.
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 14

```text
 There are many people in the waiting room.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 17

```text
There are many people in the waiting room.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 17

```text
There are many people in the waiting room.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 12

```text
 There are many people in the waiting room.
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 12

```text
 There are many people in the waiting room.
```

### angielski-22 (zdanie, trudność 3)

**Polecenie:** Correct the mistake in the sentence and write the whole sentence: I am agree with your opinion.

**Wzorzec:** I agree with your opinion.

**Slayer 1.08, seed 1** — ocena: niepoprawna; koniec: stop, tokenów: 12

```text
 I am agree with your opinion.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 12

```text
 I am agree with your opinion.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 13

```text
I agree with your opinion.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 13

```text
I agree with your opinion.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 I agree with your opinion.
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 9

```text
 I agree with your opinion.
```

### angielski-23 (zdanie, trudność 3)

**Polecenie:** Correct the mistake in the sentence and write the whole sentence: My cousin is more taller than her sister.

**Wzorzec:** My cousin is taller than her sister.

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 15

```text
 My cousin is taller than her sister.
```

**Slayer 1.08, greedy** — ocena: poprawna; koniec: stop, tokenów: 15

```text
 My cousin is taller than her sister.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 18

```text
My cousin is taller than her sister.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 18

```text
My cousin is taller than her sister.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 My cousin is taller than her sister.
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 11

```text
 My cousin is taller than her sister.
```

### angielski-24 (zdanie, trudność 3)

**Polecenie:** Correct the mistake in the sentence and write the whole sentence: I look forward to see you at the meeting.

**Wzorzec:** I look forward to seeing you at the meeting.

**Slayer 1.08, seed 1** — ocena: poprawna; koniec: stop, tokenów: 15

```text
 I look forward to seeing you at the meeting.
```

**Slayer 1.08, greedy** — ocena: niepoprawna; koniec: stop, tokenów: 15

```text
 I look forward to see you at the meeting.
```

**Bielik 1.5B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 19

```text
I look forward to seeing you at the meeting.
```

**Bielik 1.5B, greedy** — ocena: poprawna; koniec: stop, tokenów: 19

```text
I look forward to seeing you at the meeting.
```

**LFM2.5 1.2B, seed 1** — ocena: poprawna; koniec: stop, tokenów: 13

```text
 I look forward to seeing you at the meeting.
```

**LFM2.5 1.2B, greedy** — ocena: poprawna; koniec: stop, tokenów: 13

```text
 I look forward to seeing you at the meeting.
```

### angielski-25 (otwarte, trudność 1)

**Polecenie:** Write a short note (2-3 sentences) to a friend inviting them to a picnic in the park on Saturday afternoon.

**Wzorzec:** Hi Sam, would you like to come to a picnic in the park on Saturday afternoon? We are meeting by the lake at 2 p.m. and I will bring sandwiches and lemonade. Let me know if you can make it!

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 24

```text
 I would like to invite my friend to a picnic in the park on Saturday afternoon.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 46

```text

Dear friend, I am very happy to invite you to a picnic in the park on Saturday afternoon. I hope you will enjoy the picnic and come back to me in the morning.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 124

```text

Dear Friend,

I am writing to invite you to a picnic in the park on Saturday afternoon. It will be a great way to relax and enjoy the beautiful scenery. I have bought a picnic basket with food and drinks, and I will be picking you up from your house at 6 PM.

Looking forward to seeing you there!

Your friend,

[Your Name]
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 134

```text

Dear [Friend's Name],

I hope this message finds you well. I am excited to invite you to a picnic in the park on Saturday afternoon. It's a perfect day for a relaxing outdoor activity. We can enjoy the beautiful sunset and share some delicious food. Please let me know if you can make it.

Looking forward to seeing you,
[Your Name]
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 78

```text
 Dear [Friend's name], I hope you're having a great day! I'd love for you to join me for a picnic in the park this Saturday afternoon. It's going to be a fun day with lots of games and some delicious food. Let me know if you can make it, and I'll send you all the details. Have a wonderful day!
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 66

```text
 Hi [Friend's Name], I hope you're having a great day! I'd love to invite you to a picnic in the park on Saturday afternoon. We can have some delicious food, games, and enjoy the beautiful weather. Let me know if you're interested, and we can plan everything together.
```

### angielski-26 (otwarte, trudność 1)

**Polecenie:** Describe your favourite season of the year in 3-4 sentences and say why you like it.

**Wzorzec:** My favourite season is autumn. I love walking in the park when the leaves turn red, orange and yellow. The air is fresh and cool, so it is perfect for long walks. I also enjoy drinking hot tea at home on rainy evenings.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 15

```text
 Summer is my favourite season of the year.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 19

```text

I like the summer season because it is hot and sunny.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 132

```text

The fall season is my favorite because it is filled with fall colors and the air is crispy and cozy. I love the trees turning red, orange, and yellow, and the days are still warm enough to go outside and do a little walking or hiking. Plus, there are plenty of festivals and traditions to celebrate, like Halloween and Thanksgiving. I can't wait for the fall season to start!
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 94

```text

My favorite season of the year is summer. I love the warmth and the long days. I can spend hours outside, playing in the sun and swimming in the pool. The beautiful sunsets and the cricket matches are also great. I can't wait for summer to come back every year.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 39

```text
 I love the summer season. The long days, the warm weather, and the fun activities like picnics and beach days make it the best time of the year for me.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 56

```text
 My favourite season is summer. It's the best time of the year because the weather is warm and sunny, and I can spend more time outdoors with my family and friends. I love playing in the park, going to the beach, and enjoying the long days.
```

### angielski-27 (otwarte, trudność 2)

**Polecenie:** Write a short email to a hotel asking whether they have a free double room for two nights next weekend and how much it costs.

**Wzorzec:** Subject: Room availability next weekend  
  
Dear Sir or Madam,  
  
I would like to ask whether you have a double room available for two nights next weekend, from Friday to Sunday. Could you also tell me the price per night and whether breakfast is included? I look forward to your reply.  
  
Kind regards,  
Anna Kowalska

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 59

```text

Dear Mr Green, I have a free double room and it costs $40 per night. I would like to have a free room on the second night and a room with a private bathroom. I can book a room for $100.00 per night.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 82

```text

Dear Mr. Green,

I am looking for a free double room for two nights next weekend. I am a student and I will be staying at a hotel. I would like to book a room for two nights. I would like to pay a reasonable price.

Please let me know if you have any questions.

Thank you very much.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 97

```text

Dear Hotel,

I am writing to inquire about your availability of a free double room for two nights next weekend. I would be very grateful if you could provide me with the necessary information.

Thank you very much for your time and attention.

Best regards,

[Your Name]
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 108

```text

Dear Hotel Manager,

I am writing to inquire about a free double room for two nights next weekend. I would be very grateful if you could provide me with the details of the room, including the room type, size, and location.

Thank you for your time and attention.

Sincerely,
[Your Name]
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 84

```text
 Subject: Dear Mr. Smith,

Answer: Hi,

Thank you for your email. I have checked the hotel's website, and it looks like there is a free double room available for two nights next weekend. The cost is $50 per night. Would you be able to confirm if this is the case?

Thank you for your time and consideration.

Best regards,
[Your Name]
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 61

```text
 Subject: Dear Hotel Manager,

Thank you for your prompt response. I would like to book a double room for two nights next weekend. The cost is $200 per night, and I would like to know if there is a free option available.

Best regards,
[Your Name]
```

### angielski-28 (otwarte, trudność 2)

**Polecenie:** Write a short notice for the office kitchen asking colleagues to wash their cups and not to leave them in the sink.

**Wzorzec:** Dear Colleagues,  
please wash your cups after use and put them back in the cupboard. Do not leave dirty cups in the sink, because there is no room for others to use it. Let's keep our kitchen clean together. Thank you!

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 24

```text
 I want to make sure that all of my cups are washed before I go to the office.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 23

```text

Dear colleagues, please wash your cups and not to leave them in the sink.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 86

```text

As a part of our office cleanup efforts, we need to ask all colleagues to wash their cups and not leave them in the sink. This will ensure that our kitchen is always clean and organized, and our colleagues are respectful of our space.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 93

```text

Notice

Dear Colleagues,

Please remember to wash your cups before leaving them in the sink. This will help prevent any potential damage to the kitchen facilities.

Thank you for your cooperation.

Yours sincerely,

[Your Name]
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 34

```text
 Dear Colleagues, please remember to wash your cups before leaving the office. It's important to keep our kitchen clean and tidy. Thank you.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 16

```text
 Please wash your cups and do not leave them in the sink.
```

### angielski-29 (otwarte, trudność 3)

**Polecenie:** Write a short complaint email to an online shop: you ordered a green jacket but received a blue one. Ask for an exchange and say how you want to return the wrong item.

**Wzorzec:** Subject: Wrong item received, order 4821  
  
Dear Customer Service,  
  
I recently ordered a green jacket from your shop, but the parcel I received contains a blue one. I would like to exchange it for the green jacket in the same size. I can send the blue jacket back by courier if you provide a return label. Please let me know the next steps.  
  
Yours faithfully,  
Mark Lewis

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 44

```text

Dear customer, I ordered a green jacket but received a blue one. I would like to return the wrong item. I would like to exchange the blue one for a green one.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 29

```text
 I ordered a green jacket but received a blue one. I want to exchange the blue one for a green one.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 177

```text

Dear Online Shop,

I'm writing to complain about my recent purchase of a green jacket. Unfortunately, I received a blue jacket instead. I believe this is a deliberate mistake by the online shop.

I would like to exchange the blue jacket for the green one. Please provide me with an option to return the blue jacket. I hope you can rectify this error quickly and send me the replacement jacket immediately.

Thank you for your attention and support.

Sincerely,
[Your Name]
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 150

```text

Dear [Shopname],

I am writing to complain about my recent online shopping experience. I ordered a green jacket, but instead received a blue one.

I would like to exchange the item for a green one, as I am not happy with the color. Please consider my request and provide me with a new green jacket as soon as possible.

Thank you for your attention to this matter.

Sincerely,
[Your Name]
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 59

```text
 I ordered a green jacket, but unfortunately, it arrived in a blue jacket. I would appreciate it if you could exchange the jacket for a green one. If you need to return the wrong item, please let me know so I can process it. Thank you for your understanding.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 67

```text
 Dear [Shop Name], I am writing to express my disappointment in the jacket I received. It is a blue jacket, but I ordered a green one. I would like to exchange the wrong item and return the blue jacket. Please let me know how I can proceed. Thank you for your attention to this matter.
```

### angielski-30 (otwarte, trudność 3)

**Polecenie:** Write a short product description (4-5 sentences) for an online shop: a reusable steel water bottle, 750 ml, keeps drinks cold for 24 hours.

**Wzorzec:** Stay refreshed all day with our reusable steel water bottle. It holds 750 ml, which is enough for a long walk, a workout or a day at the office. Double steel walls keep your drinks cold for 24 hours. The bottle is easy to clean and helps you reduce plastic waste.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 95

```text

This water bottle is made from a high-quality steel that is extremely durable and resistant to corrosion. It is designed to be used for drinking and storage of drinks, but also for keeping drinks cold for 24 hours. This bottle is made from a high-quality steel that is extremely durable and resistant to corrosion. It is designed to be used for drinking and storage of drinks, but also for keeping drinks cold for 24 hours.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 5

```text
(pusta odpowiedź)```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 188

```text

Our reusable steel water bottle is the perfect accessory for your daily outings. It comes in a variety of colors to match your style, and is made from high-quality, reusable materials. This 750 ml bottle keeps drinks cold for up to 24 hours, and has a large capacity for daily use. The bottle is designed with a tight fit, making it easy to carry and keep clean. With its durable construction and long-lasting features, this water bottle is a must-have for anyone who loves the great taste and convenience of cold beverages.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 5

```text
(pusta odpowiedź)```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 137

```text
 Our reusable steel water bottle is the perfect companion for your daily hydration needs. Made from high-quality steel, it keeps your drinks cold for up to 24 hours, ensuring you stay refreshed throughout the day. With a 750 ml capacity, it's the ideal size for a single serving, perfect for your morning coffee or a mid-afternoon snack. Crafted with durability in mind, this bottle is built to withstand the rigors of daily use, making it a reliable and eco-friendly choice for your hydration journey. Plus, its sleek design and easy-to-carry handle make it the perfect accessory for your daily commute or outdoor adventures.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 88

```text
 Our reusable steel water bottle is perfect for staying hydrated on the go. Made from high-quality stainless steel, it keeps your drinks cold for up to 24 hours, ensuring you stay refreshed throughout the day. With its sleek design and durable construction, it's the ideal companion for your daily commute, gym sessions, or outdoor adventures. Choose our bottle for a sustainable and stylish way to stay hydrated.
```

## tekst_techniczny

### tekst_techniczny-01 (otwarte, trudność 1)

**Polecenie:** Wyjaśnij, czym jest kopia zapasowa danych i na czym polega zasada 3-2-1. Odpowiedz w kilku zdaniach.

**Wzorzec:** Kopia zapasowa to dodatkowy egzemplarz danych przechowywany osobno, który pozwala je odtworzyć po awarii dysku, kradzieży sprzętu, ataku ransomware albo przypadkowym skasowaniu pliku. Zasada 3-2-1 mówi, że warto mieć trzy kopie danych: oryginał i dwie kopie zapasowe. Kopie powinny leżeć na dwóch różnych rodzajach nośników, na przykład na dysku zewnętrznym i w chmurze, żeby jedna wada nośnika nie zniszczyła wszystkiego. Jedna kopia musi znajdować się poza miejscem pracy, bo pożar albo zalanie biura niszczy wszystko, co stoi w jednym pomieszczeniu. Sama kopia nie wystarcza: trzeba ją robić regularnie, najlepiej automatycznie, i co jakiś czas sprawdzać, czy da się z niej odtworzyć dane. Kopia, której nikt nigdy nie przywrócił, jest tylko założeniem, że zadziała.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 73

```text

Kopia zapasowa to kopia danych, która jest tworzona automatycznie lub ręcznie. Przy zapisie kopii zapasowej przenoszone są wszystkie dane użytkownika, w tym hasła, numery kont, a także wszystkie dane zapisane w folderze na dysku. W razie uszkodzenia lub utraty danych, użytkownik nie musi ponownie wprowadzać tych informacji.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 90

```text

Kopia zapasowa to kopia danych, które zostały zapisane na dysku twardym komputera. W przypadku awarii dysku twardego, na przykład w wyniku uszkodzenia zasilania, dane są kopiowane na inny dysk twardy. Zasada 3-2-1 to zasada, która mówi, że w przypadku awarii jednego dysku twardego, na przykład w wyniku uszkodzenia zasilania, należy zapisać wszystkie dane na innym dysku twardym.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 103

```text

Kopia zapasowa danych to jej duplikat przechowywany w innym miejscu. Na przykład: kopię zapasową e-maila w poczcie elektronicznej można zapisać na dysku zewnętrznym, a na komputerze na dysku twardym. Zasada 3-2-1 mówi, że należy przechowywać 3 kopie danych w dwóch różnych lokalizacjach, z których jedna powinna znajdować się poza domem. Dzięki temu, jeśli jedna z kopii zostanie uszkodzona lub skradziona, pozostałe będą bezpieczne.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 90

```text

Kopia zapasowa danych to wykonanie kopii oryginalnych plików i ich zawartości na inny nośnik, na przykład dysk zewnętrzny, chmurę lub inny komputer. Zasada 3-2-1 mówi, że należy mieć trzy kopie danych, z których każda znajduje się na dwóch różnych nośnikach, na przykład na dwóch dyskach twardych i w chmurze. Dzięki temu w razie awarii jednego nośnika można odzyskać dane z pozostałych.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 134

```text
 Kopia zapasowa danych to powtórzenie zdarzeń w formie kompletnej i zabezpieczonej w celu ochrony przed stratami lub utratą informacji. Zasada 3-2-1 oznacza, że zapas danych powinien być trzech kopii, zlokalizowanych na dwóch różnych nośnikach, a ostatnia na pokładzie statku. Zasada ta gwarantuje, że jeśli jeden z kopii zostanie zniszczony, druga będzie nadal dostępna.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 111

```text


Kopia zapasowa danych to zbiór danych, który jest kopiowany i przechowywany w celu zapewnienia bezpieczeństwa i odzyskania informacji w przypadku awarii głównego systemu. Zasada 3-2-1 oznacza, że dane powinny być przechowywane w trzech miejscach: na jednym miejscu na pewno, na dwóch miejscach i na trzecim miejscu.
```

### tekst_techniczny-02 (otwarte, trudność 1)

**Polecenie:** Wyjaśnij prostymi słowami, czym jest inflacja i jak wpływa na oszczędności trzymane w gotówce.

**Wzorzec:** Inflacja to ogólny wzrost cen towarów i usług w gospodarce w danym okresie, zwykle podawany w procentach w skali roku. Gdy inflacja wynosi 5%, koszyk zakupów, który rok temu kosztował 100 zł, kosztuje teraz około 105 zł. Oznacza to, że za tę samą kwotę można kupić mniej niż wcześniej, czyli spada siła nabywcza pieniądza. Oszczędności trzymane w gotówce nie rosną, więc przy inflacji realnie tracą na wartości: 10 000 zł po roku inflacji na poziomie 5% wystarczy na zakupy, które wcześniej kosztowały około 9 500 zł. Dlatego oszczędzający porównują oprocentowanie lokaty lub obligacji ze stopą inflacji. Jeśli oprocentowanie jest niższe od inflacji, realna wartość oszczędności i tak maleje, choć ich nominalna kwota rośnie.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 68

```text

Inflacja to wzrost cen dóbr i usług, które kupujemy w sklepach. Obejmuje też wzrost kosztów produkcji i transportu. Powoduje to, że nasze oszczędności tracą na wartości. Warto dbać o to, aby nasze pieniądze nie traciły na wartości i trzymać je w banku lub na koncie oszczędnościowym.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 60

```text

Inflacja to wzrost cen dóbr i usług, który powoduje, że pieniądze tracą na wartości. W Polsce inflacja jest wysoka, bo ceny rosną szybciej niż płace. Wpływ inflacji na oszczędności jest niewielki, bo pieniądze trzymane w gotówce tracą na wartości.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 76

```text

Inflacja to wzrost ogólnego poziomu cen w gospodarce. Gdy ceny rosną, to za tę samą ilość pieniędzy można kupić mniej towarów. Jeśli trzymamy oszczędności w gotówce, to w wyniku inflacji ich wartość maleje, bo możemy kupić mniej za tę samą kwotę. Dlatego warto inwestować oszczędności w akcje lub obligacje, które są mniej narażone na inflację.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 69

```text

Inflacja to wzrost cen towarów i usług w gospodarce. Gdy ceny rosną, oszczędności trzymane w gotówce tracą na wartości, bo nie można ich kupić za tyle, ile się włożyło. Dlatego warto oszczędzać w bezpiecznych miejscach, jak lokaty bankowe, obligacje czy fundusze inwestycyjne, które chronią przed inflacją.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 299

```text


Inflacja to wzrost ogólnej cen w gospodarstwie domowym, który odzwierciedla zmiany na rynkach światowych, szczególnie na rynku surowców i paliw. Wpływa na oszczędności trzymane w gotówce, ponieważ pieniądze tracą na wartości, co oznacza, że kupując ten sam produkt na początku roku kupujesz tyle, ile na koniec. Na przykład, jeśli kupisz 100 dolarów za kilo kawy i w jednym roku zapłaciłeś 120 dolarów za kilo, a w następnym roku kupisz 100 dolarów za kilo, w tym roku wartość pieniędzy spadła o 20%, więc w tym roku kupujesz 120 dolarów za kilo. Inflacja również wpływa na oszczędności, ponieważ zyski oszczędności utrata wartości, a dodatkowo cena pieniędzy zmienia się, więc jeśli kupujesz jedno okazjonalne przedmioty i jeśli kupujesz co roku pewne przedmioty, to przez inflację oszczędzasz więcej.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 142

```text
 Inflacja to wzrost ogólnej cen, co oznacza, że kupno tych samych produktów kosztuje więcej. Na przykład, jeśli kupujesz 1000 złotych za 1000 złotych, a w ciągu roku cena jednego produktu wzrosła o 10%, to w tym roku kupujesz 1100 złotych za 1000 złotych. Inflacja może być spowodowana przez wzrost podaży pieniądza, czy też przez wzrost popytu na określone produkty.
```

### tekst_techniczny-03 (otwarte, trudność 1)

**Polecenie:** Wyjaśnij różnicę między kilowatem (kW) a kilowatogodziną (kWh) i podaj przykład z domowym urządzeniem.

**Wzorzec:** Kilowat to jednostka mocy, czyli tego, jak szybko urządzenie zużywa albo wytwarza energię w danej chwili. Kilowatogodzina to jednostka energii: tyle energii zużywa urządzenie o mocy 1 kW pracujące przez jedną godzinę. Moc można porównać do prędkości, a energię do przejechanej drogi. Czajnik elektryczny o mocy 2 kW, który grzeje wodę przez 3 minuty, czyli 0,05 godziny, zużywa 2 · 0,05 = 0,1 kWh. Żarówka LED o mocy 10 W, czyli 0,01 kW, musiałaby świecić 10 godzin, żeby zużyć tyle samo energii. Rachunek za prąd liczy się w kilowatogodzinach, bo płacimy za zużytą energię, a nie za samą moc urządzeń. Moc ma znaczenie przy doborze instalacji i zabezpieczeń, bo mówi, jakie obciążenie pojawia się jednocześnie.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 58

```text

Kilowatogodzina (kWh) to jednostka energii elektrycznej. Przelicznik jest następujący: 1 kWh = 1000 W. Jeśli w ciągu godziny zużyjemy 1000 kWh, to w ciągu roku zużyjemy 1000 kWh.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 42

```text

Kilowatogodzina to jednostka mocy, czyli energii, którą można wykorzystać w ciągu jednej godziny. Kilowatogodzina jest równa 1 kWh.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 124

```text

Kilowat (k W) to jednostka mocy, a kilowatogodzina (kWh) to jednostka energii. 1 k W to 1000 W, a 1 k Wh to 1000 W·h. Przykładowo, jeśli lodówka zużywa 1 k Wh dziennie, to w ciągu miesiąca (30 dni) zużyje 30 k Wh, czyli 1 k W. W domu jest wiele urządzeń, które działają na tej zasadzie: pralka, zmywarka, komputer, telewizor.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 72

```text

Kilowat (k W) to jednostka mocy, czyli ilości energii zużywanej w jednostce czasu. Kwh to jednostka energii, czyli ilości energii zużytej w czasie. Na przykład, lodówka zużywa około 1 k Wh energii na dobę, co odpowiada 1000 k Wh rocznie.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 130

```text
 Kilowatogodzina (kWh) to jednostka miary energii elektrycznej, która równa się 1 kW działającym przez 1 godzinę. Kilowatogodzina (kWh) to jednostka miary energii elektrycznej, która równa się 1 kW działającym przez 1 godzinę. Przykład: robić prąd w domu 1000 kWh rocznie oznacza, że robi się 1000 kWh energii elektrycznej przez 1 godzinę.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: limit, tokenów: 400

```text
 Kilowatogodzina to jednostka miary energii elektrycznej, równa 1000 kilowatów. Kilowatogodzina to czas, w którym zużyto 1000 kilowatów energii elektrycznej. Na przykład, 1 kWh to 1000 kWh. Kilowatogodziny są używane do mierzenia zużycia energii elektrycznej w domach, a także w urządzeniach takich jak lampy, klimatyzatory, grzejniki, kuchenki, wasztry, kuchenne, klimatyzatory, lampy, klimatyzatory, lampy, kuchenki, wasztry, kuchenki, lampy, klimatyzatory, lampy, kuchenki, lampy, klimatyzatory, lampy, kuchenki, lampy, klimatyzatory, lampy, kuchenki, lampy, klimatyzatory, lampy, kuchenki, lampy, klimatyzatory, lampy, kuchenki, lampy, klimatyzatory, lampy, kuchenki, lampy, klimatyzatory, lampy, kuchenki, lampy, klimatyzatory, lampy, kuchenki, lampy, klimatyzatory, lampy, kuchenki, lampy, klimatyzatory, lampy, kuchenki, lampy, klimatyzatory, lampy, kuchenki, lampy, klimatyzatory, lampy, kuchenki, lampy, klimatyzatory, lampy, kuchenki, lampy, klimatyzatory, lampy, kuchenki, lampy, klimatyzatory, lampy, kuchenki, lampy, klimatyzatory, lampy, kuchen
```

### tekst_techniczny-04 (otwarte, trudność 1)

**Polecenie:** Opisz, na czym polega fotosynteza i dlaczego jest ważna dla życia na Ziemi.

**Wzorzec:** Fotosynteza to proces, w którym rośliny, glony i sinice wytwarzają związki organiczne z prostych substancji nieorganicznych, korzystając z energii światła. Zachodzi głównie w chloroplastach, gdzie barwnik chlorofil pochłania światło. Substratami są dwutlenek węgla pobierany z powietrza i woda, a produktami glukoza i tlen. W uproszczeniu reakcję zapisuje się jako 6 CO₂ + 6 H₂O → C₆H₁₂O₆ + 6 O₂. Glukoza służy roślinie jako źródło energii i materiał do budowy innych związków, na przykład skrobi i celulozy. Fotosynteza jest podstawą większości łańcuchów pokarmowych, bo zwierzęta i ludzie korzystają pośrednio z energii zgromadzonej przez rośliny. Dostarcza też tlenu do atmosfery i pochłania dwutlenek węgla, więc wpływa na skład powietrza i klimat.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 72

```text

Fotosynteza to proces, w którym rośliny przekształcają energię słoneczną w energię chemiczną. Rośliny pochłaniają światło słoneczne, które jest najpierw przekształcane w energię chemiczną. Ta energia chemiczna jest następnie przekształcana w energię biologiczną, która jest wykorzystywana do budowy i funkcjonowania komórek roślinnych.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 71

```text

Fotosynteza to proces, w którym rośliny przekształcają energię słoneczną w energię chemiczną, czyli ATP. Wytwarzają ją w procesie zwanym fotosyntezą, w którym światło słoneczne jest pochłaniane przez chlorofil, a następnie przekształcane w energię chemiczną, czyli ATP.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 123

```text

Fotosynteza to proces, w którym rośliny, algi i niektóre bakterie wykorzystują energię słoneczną do przekształcania dwutlenku węgla i wody w glukozę i tlen. Glukoza jest następnie wykorzystywana przez rośliny jako źródło energii, a tlen jest uwalniany jako produkt uboczny. Fotosynteza jest niezbędna dla życia na Ziemi, ponieważ dostarcza tlenu do atmosfery, bez którego nie byłoby możliwe oddychanie. Ponadto, fotosynteza jest kluczowa dla obiegu węgla w przyrodzie, ponieważ dwutlenek węgla jest usuwany z atmosfery i zmagazynowany w roślinach.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 101

```text

Fotosynteza to proces, w którym rośliny, algi i niektóre bakterie przekształcają energię słoneczną w energię chemiczną w postaci glukozy. Proces ten zachodzi w chloroplastach, gdzie światło jest przekształcane w energię chemiczną dzięki obecności chlorofilu. Fotosynteza jest kluczowa dla życia na Ziemi, ponieważ dostarcza tlenu do atmosfery, który jest niezbędny do oddychania organizmów, a także dostarcza energii dla fotosyntetyzujących organizmów.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 304

```text


Fotosynteza to proces, w którym rośliny i algi pobierają światło słoneczne, wykorzystując je do wytwarzania energii w postaci glukozy i tlenu z wody i dwutlenku węgla. Jest to podstawowy proces w energetyce biologicznej i w biologii wszystkich organizmów autotroficznych, które mogą wykorzystywać światło słoneczne jako źródło energii.

Fotosynteza zachodzi w chloroplastach, gdzie występuje faktoryzacja fotofosforilacji, w której ATP jest wytwarzane z ADP i fosforanu. W trakcie fotosyntezy powstają również NADPH, które służą do tworzenia reduktanek i związków organicznych, takich jak aminokwasy, które są wykorzystywane w biosyntezie.

Fotosynteza jest ważna dla życia na Ziemi, ponieważ jest źródłem energii dla życia. Energia słoneczna jest źródłem energii dla wszelkich form życia na Ziemi, a fotosynteza jest źródłem tlenu, który jest niezbędny dla większości form życia.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 210

```text


Fotosynteza to proces, w którym rośliny, algi i niektóre bakterie przekształcają światło słoneczne w energię chemiczną. W tym procesie rośliny pobierają dwutlenek węgla i wody z otoczenia i przekształcają je w glukozę i tlen. Glukoza jest używana przez rośliny jako źródło energii, a tlen jest uwalniany do otoczenia.

Fotosynteza jest ważna dla życia na Ziemi, ponieważ jest źródłem energii dla większości organizmów. Rośliny, które przeprowadzają fotosyntezę, są podstawą łańcucha pokarmowego, ponieważ dostarczają energii i składników odżywczych dla wszystkich zwierząt.
```

### tekst_techniczny-05 (otwarte, trudność 1)

**Polecenie:** Wyjaśnij, czym jest uwierzytelnianie dwuskładnikowe (2FA) i dlaczego zwiększa bezpieczeństwo konta.

**Wzorzec:** Uwierzytelnianie dwuskładnikowe to sposób logowania, w którym oprócz hasła trzeba podać drugi, niezależny dowód tożsamości. Składniki dzielą się na trzy grupy: coś, co wiesz (hasło, PIN), coś, co masz (telefon, klucz sprzętowy), i coś, czym jesteś (odcisk palca, twarz). Typowy przykład to hasło plus jednorazowy kod z aplikacji w telefonie albo potwierdzenie logowania kluczem USB. Zwiększa to bezpieczeństwo, bo samo wykradzione hasło nie wystarcza do przejęcia konta: napastnik musiałby mieć też dostęp do drugiego składnika. Chroni to przed skutkami wycieku haseł z innych serwisów i przed częścią ataków phishingowych. Najsłabszą formą drugiego składnika jest kod SMS, który da się przechwycić, na przykład przez podmianę karty SIM, dlatego bezpieczniejsze są aplikacje i klucze sprzętowe.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 95

```text

Uwierzytelnianie dwuskładnikowe to rodzaj zabezpieczenia, które polega na tym, że oprócz podania loginu i hasła do konta, wymagane jest jeszcze potwierdzenie tożsamości. W przypadku logowania się do konta internetowego, jest to zazwyczaj dodatkowy kod wysyłany na telefon komórkowy. Po jego wprowadzeniu system sprawdza, czy użytkownik jest uprawniony do zalogowania się. Jeśli nie, to wyświetla komunikat o błędzie i żąda ponownego podania hasła.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 71

```text

Uwierzytelnianie dwuskładnikowe to metoda uwierzytelniania, która wymaga podania dwóch różnych rodzajów danych: hasła i kodu SMS. Hasło jest jednorazowe i służy do logowania się do konta. Kod SMS to jednorazowy kod, który jest wysyłany na telefon komórkowy użytkownika w celu potwierdzenia tożsamości.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 105

```text

Uwierzytelnianie dwuskładnikowe (2FA) to dodatkowa warstwa zabezpieczeń konta. Polega na tym, że oprócz hasła użytkownika potrzebne jest jeszcze drugie hasło, zwykle jednorazowe, generowane przez aplikację mobilną lub w przeglądarce. Dzięki temu nawet jeśli ktoś wykradnie hasło, nie ma możliwości zalogowania się na konto, dopóki nie otrzyma jednorazowego hasła. To zwiększa bezpieczeństwo konta, ponieważ nawet jeśli ktoś zdobędzie hasło, nie może z niego skorzystać bez dodatkowego hasła.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 93

```text

Uwierzytelnianie dwuskładnikowe (2FA) to dodatkowa warstwa zabezpieczeń, która wymaga podania dwóch różnych informacji, aby uzyskać dostęp do konta. Najczęściej jest to hasło i kod z aplikacji lub SMS-a, ale może to być też odcisk palca, rozpoznanie twarzy lub biometria. Zwiększa bezpieczeństwo, bo nawet jeśli ktoś zdobędzie hasło, nie będzie mógł wejść na konto, dopóki nie otrzyma kodu.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 182

```text
 Uwierzytelnianie dwuskładnikowe (2FA) to metoda autentykacji, która dodatkowo wzmacnia bezpieczeństwo konta. Zamiast pisać czytelnikowi swoje zdanie, użytkownik musi podać dwie kolejne informacje: nazwy użytkownika i hasło. Należy podkreślić, że podczas poszukiwania dostępu użytkownik jest zmuszany do podania tych dwóch informacji, co zwiększa bezpieczeństwo. 2FA zapewnia dodatkową warstwę zabezpieczenia, ponieważ zazwyczaj w przeciwnym razie użytkownik musi znać hasło.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 184

```text
 Uwierzytelnianie dwuskładnikowe to metoda uwierzytelniania, która wymaga od użytkownika podania dwóch różnych dowodów tożsamości. Najczęściej jest to połączenie czegoś, co użytkownik wie, z czegoś, co nie wie. Na przykład, aby uzyskać dostęp do konta, użytkownik musi podać zarówno hasło, jak i kod PIN. Uwierzytelnianie dwuskładnikowe zwiększa bezpieczeństwo konta, ponieważ nawet jeśli ktoś uzyskał hasło, nie będzie mógł uzyskać dostęp do konta, jeśli nie zna kodu PIN.
```

### tekst_techniczny-06 (otwarte, trudność 1)

**Polecenie:** Wyjaśnij, do czego służy wyłącznik nadprądowy w domowej instalacji elektrycznej i czym różni się od wyłącznika różnicowoprądowego.

**Wzorzec:** Wyłącznik nadprądowy, potocznie „eska”, chroni przewody instalacji przed przegrzaniem. Odcina obwód, gdy płynie w nim prąd większy niż dopuszczalny, na przykład przy przeciążeniu zbyt wieloma urządzeniami albo przy zwarciu. Przy długotrwałym przeciążeniu działa wyzwalacz termiczny, a przy zwarciu szybki wyzwalacz elektromagnetyczny. Wyłącznik różnicowoprądowy ma inne zadanie: chroni ludzi przed porażeniem. Porównuje prąd wpływający do obwodu z prądem z niego wypływającym i rozłącza obwód, gdy różnica przekroczy niewielką wartość, w domach zwykle 30 mA. Taka różnica oznacza, że część prądu ucieka inną drogą, na przykład przez ciało człowieka do ziemi. Wyłącznik nadprądowy nie zareaguje na tak mały prąd upływu, dlatego w instalacji potrzebne są oba rodzaje zabezpieczeń.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 150

```text

Włącznik nadprądowy jest urządzeniem służącym do ochrony domowej instalacji elektrycznej. Jego zadaniem jest zapobieganie uszkodzeniom instalacji, gdy płynie w niej prąd o dużej wartości. Gdy wartość prądu przekracza ustalone przez producenta napięcie (12V dla instalacji jednofazowych i 24V dla instalacji trójfazowych), prąd przepływa przez rezystor w wyłączniku. Rezystor ten jest częścią instalacji elektrycznej, a w instalacji jednofazowej wynosi zwykle kilka kilowatów. Gdy wartość prądu przekroczy wartość ustaloną przez producenta, załącza się ochronny wyłącznik nadprądowy. W instalacji trójfazowej napięcie między przewodami jest takie samo jak w instalacji jednofazowej.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 101

```text

Wyłącznik nadprądowy służy do ochrony urządzeń elektrycznych przed przeciążeniem. W domowej instalacji elektrycznej jest to bezpiecznik, który chroni obwód elektryczny przed zbyt dużym przepływem prądu. W przypadku przeciążenia, na przykład w wyniku zwarcia, prąd przepływa przez obwód, powodując jego uszkodzenie. Wyłącznik różnicowoprądowy natomiast chroni obwód przed przepływem prądu o zbyt dużym natężeniu, co może prowadzić do uszkodzenia urządzeń elektrycznych.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 129

```text

Wyłącznik nadprądowy, czyli tzw. bezpiecznik, służy do ochrony instalacji elektrycznej przed przepięciami i przeciążeniami. Działa na zasadzie samoczynnego wyłączenia obwodu w momencie wykrycia zbyt wysokiego prądu, który może być spowodowany zwarciem lub przeciążeniem. Wyłącznik różnicowoprądowy, zwany też ochronnym, wykrywa różnicę potencjałów między dwoma punktami obwodu i automatycznie wyłącza zasilanie, gdy wykryje zagrożenie porażeniem prądem. Różni się od wyłącznika nadprądowego tym, że działa na podstawie różnic w przepływie prądu, a nie na podstawie jego wartości.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 127

```text

Wyłącznik nadprądowy (bezpiecznik) chroni instalację elektryczną przed skutkami przeciążenia, czyli zbyt dużego poboru prądu. Działa na zasadzie samoczynnego wyłączania obwodu, gdy prąd przekroczy dopuszczalną wartość. Wyłącznik różnicowoprądowy (RCD) wykrywa prąd różnicowy, czyli różnicę między prądem płynącym w obwodzie a prądem płynącym przez ciało człowieka. Działa na zasadzie samoczynnego wyłączania obwodu, gdy prąd przekroczy dopuszczalną wartość. Różni się od wyłącznika nadprądowego tym, że wykrywa prąd różnicowy, a nie tylko przeciążenie.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 133

```text
 Wyłącznik nadprądowy w domowej instalacji elektrycznej służy do zabezpieczenia urządzeń elektrycznych przed uszkodzeniami spowodowanymi nadmiernym prądem. Może być uruchomiony ręcznie lub automatycznie. Wyłącznik różnicowoprądowy (również znany jako próg) jest wyłącznikiem automatycznym, który działa, gdy przewodnik wytoczony do prądu jest przewodu wytoczonego do odwrotnego kierunku.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 156

```text
 Wyłącznik nadprądowy w domowej instalacji elektrycznej służy do ochrony przed uszkodzeniami spowodowanymi przez nadmierne prądy. Wyłącznik różnicowoprądowy natomiast służy do ochrony przed uszkodzeniami spowodowanymi przez prądy przekraczające prąd zabezpieczający. Wyłącznik nadprądowy jest zazwyczaj wyłączany w przypadku uszkodzenia elektrycznego, podczas gdy wyłącznik różnicowoprądowy jest zazwyczaj wyłączany w przypadku nadmiernego prądu.
```

### tekst_techniczny-07 (otwarte, trudność 1)

**Polecenie:** Wyjaśnij różnicę między ceną netto a ceną brutto i pokaż na przykładzie, jak policzyć cenę brutto przy stawce VAT 23%.

**Wzorzec:** Cena netto to cena towaru lub usługi bez podatku VAT. Cena brutto to cena, którą płaci kupujący, czyli netto powiększone o należny VAT. Podatek liczy się od ceny netto według stawki przypisanej do danego towaru. Przy stawce 23% i cenie netto 200 zł VAT wynosi 200 · 0,23 = 46 zł, więc cena brutto to 246 zł. Odwrotnie, żeby z ceny brutto wyliczyć netto, trzeba ją podzielić przez 1,23, a nie odjąć 23% od brutto: 246 / 1,23 = 200 zł, podczas gdy odjęcie 23% od 246 zł dałoby błędnie około 189 zł. Firmy będące czynnymi podatnikami VAT zwykle porównują oferty w cenach netto, bo podatek mogą odliczyć. Konsument końcowy płaci pełną cenę brutto.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 37

```text

Cena brutto to cena, którą nabywca musi zapłacić za towar lub usługę. Cena netto to cena, którą płaci sprzedawca za towar lub usługę.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 37

```text

Cena netto to cena, którą nabywca płaci za towar lub usługę. Cena brutto to cena, którą sprzedawca musi zapłacić za towar lub usługę.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 101

```text

Cena netto to kwota, jaką płacisz za produkt lub usługę, bez podatku VAT. Cena brutto to cena netto plus podatek VAT. Na przykład, jeśli kupujesz coś za 100 zł, a VAT wynosi 23%, to cena brutto wyniesie 123 zł. Aby policzyć cenę brutto, dodaj VAT do ceny netto: 100 zł + (100 zł * 23%) = 123 zł.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 106

```text

Cena netto to kwota, którą płacisz za produkt lub usługę, zanim zostaną doliczone podatki i inne opłaty. Cena brutto to cena netto powiększona o podatek VAT. Na przykład, jeśli cena netto to 100 zł, a VAT wynosi 23%, to cena brutto to 123 zł. Aby policzyć cenę brutto, mnożysz cenę netto przez 1 + VAT (w tym przypadku 1 + 0,23 = 1,23).
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 143

```text
 Cena brutto to ta, która obliczamy w szacunku do VAT, a w szacunku do VAT. Zazwyczaj należy policzyć cenę netto, która po usunięciu VAT daje właściwą cenę. Na przykład, jeśli sprzedaje się 100 dolarów za dwie pieniądze za dostawa, a VAT wynosi 23%, to cenę brutto to 100 dolarów + 23% = 113 dolarów, a cenę netto to 113 dolarów – 100 dolarów.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 113

```text
 Cena brutto to cena, która obejmuje podatek VAT. Cena netto to cena, która nie obejmuje podatku VAT. Na przykład, jeśli kupujesz 1000 zł w sklepie, a w sklepie VAT wynosi 23%, to cena brutto to 1000 + 23% = 1023 zł, a cena netto to 1023 - 23% = 979,9 zł.
```

### tekst_techniczny-08 (otwarte, trudność 1)

**Polecenie:** Wyjaśnij, co oznacza skala pH, i podaj przykłady substancji kwaśnych, obojętnych i zasadowych.

**Wzorzec:** Skala pH opisuje, jak kwaśny lub zasadowy jest roztwór wodny. Jest związana ze stężeniem jonów wodorowych: pH to ujemny logarytm dziesiętny tego stężenia. W praktyce skala obejmuje zwykle wartości od 0 do 14. Roztwór o pH 7 jest obojętny, jak czysta woda w temperaturze 25 °C. Wartości poniżej 7 oznaczają odczyn kwaśny, na przykład sok z cytryny ma pH około 2, a ocet około 3. Wartości powyżej 7 oznaczają odczyn zasadowy, na przykład roztwór sody oczyszczonej ma pH około 8, a środki do udrażniania rur nawet powyżej 13. Skala jest logarytmiczna, więc spadek pH o jedną jednostkę oznacza dziesięciokrotnie większe stężenie jonów wodorowych. Dlatego różnica między pH 3 a pH 5 jest stukrotna, a nie dwukrotna.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 73

```text

Skala pH to miara kwasowości lub zasadowości roztworów wodnych, wyrażona w postaci pH = log(H + pKa), gdzie pH oznacza potencjał wodny (potencjał zjonizowanej wody), a pKa – potencjał jonizacji wody (potencjał zjonizowanej wody).
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 99

```text

Skala pH to skala logarytmiczna, w której 0 oznacza obojętność, a 100 – kwasowość. Skala pH jest stosowana do oznaczania kwasowości roztworów wodnych. Na przykład roztwór o pH 7 oznacza, że jest on obojętny, a roztwór o pH 9 – kwasowy. Skala pH jest stosowana w laboratoriach chemicznych, gdzie mierzy się pH roztworów, aby określić ich kwasowość lub zasadowość.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 146

```text

Skala pH to skala logarytmiczna, która określa, jak kwaśny lub zasadowy jest roztwór. Wartość pH jest odwrotnością logarytmu dziesiętnego stężenia jonów wodorowych (H+). Poniższa tabela przedstawia przykłady substancji kwaśnych, obojętnych i zasadowych:

| Substancja | pH | Przykład |
|-----------|-----|---------|
| Kwaśna | < 7 | Woda, ocet, cytryna |
| Bezbarwna | 7 | Woda |
| Kwaśna | > 7 | Napoje gazowane, soki, wino |
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 137

```text

Skala pH to skala logarytmiczna, która określa kwasowość lub zasadowość roztworu. Im niższa wartość pH, tym bardziej kwaśny jest roztwór, a im wyższa, tym bardziej zasadowy. Przykładowe substancje:
- Kwaśne: ocet, cytryna, kwasek cytrynowy, kwas solny, kwas siarkowy, kwas azotowy.
- Neutralne: woda, mleko, sok jabłkowy, woda mineralna.
- Zasadowe: soda oczyszczona, proszek do pieczenia, wapno gaszone, soda kaustyczna, soda oczyszczona.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 145

```text
 Skala pH jest miarą poziomu kwasowości lub zasadowości roztworu. Jest to wartość liczbowa na skali od 0 do 14, gdzie 0 to skala kwasowości, 7 jest neutralnością, a powyżej 7 zasadowość, poniżej 7 kwaśność. Właściwie pH jest miarą maksymalnej liczby jonów hydronium (H3O+). Na przykład w roztworze wodnym z jonami H3O+ i OH− w równowadze pH wynosi 7.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 127

```text
 Skala pH to miara poziomu kwasowości lub zasadowości roztworu. Jest to liczba liczby decydującej o tym, czy roztwór jest kwaśny, zasadny lub neutralny. Skala pH ma 14 punktów, od 0 do 14, przy czym pH 7 jest neutralnym poziomem kwasowości lub zasadowości. pH 0 to najbardziej kwaśny poziom, pH 14 to najbardziej zasadny poziom.
```

### tekst_techniczny-09 (otwarte, trudność 1)

**Polecenie:** Opisz w kilku zdaniach, jak panel fotowoltaiczny zamienia światło na prąd i po co w instalacji jest falownik.

**Wzorzec:** Panel fotowoltaiczny składa się z ogniw, najczęściej krzemowych, w których zachodzi zjawisko fotowoltaiczne. Ogniwo ma dwie warstwy półprzewodnika o różnym typie przewodnictwa, n i p, a na ich styku powstaje złącze z wbudowanym polem elektrycznym. Fotony światła wybijają elektrony, a pole złącza rozdziela ładunki, dzięki czemu między elektrodami pojawia się napięcie i może płynąć prąd. Panel wytwarza prąd stały, a jego moc zależy od natężenia promieniowania, kąta padania światła i temperatury: nagrzane ogniwa pracują mniej wydajnie. Urządzenia w domu i sieć energetyczna działają na prądzie przemiennym o częstotliwości 50 Hz, dlatego potrzebny jest falownik, czyli inwerter. Zamienia on prąd stały z paneli na przemienny, synchronizuje się z siecią i zwykle szuka punktu pracy o największej mocy.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 76

```text

Panel fotowoltaiczny zamienia światło słoneczne na prąd stały, który jest przechowywany w akumulatorach. Aby móc wykorzystać prąd wytworzony w panelach, trzeba podłączyć go do sieci energetycznej. Wytworzony w panelach prąd jest przetwarzany przez falownik, który zamienia go na napięcie stałe, a następnie trafia do akumulatorów.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 79

```text

Panel fotowoltaiczny zamienia światło słoneczne na prąd stały, który jest wykorzystywany do zasilania urządzeń elektrycznych. W panelach fotowoltaicznych wykorzystuje się półprzewodniki, które pobierają energię z promieniowania słonecznego i zamieniają ją na prąd stały. W falowniku zamienia się ten prąd stały na prąd zmienny, który jest wykorzystywany do zasilania urządzeń elektrycznych.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 99

```text

Panel fotowoltaiczny zamienia światło słoneczne na energię elektryczną za pomocą ogniw fotowoltaicznych. Składa się z cienkich warstw półprzewodników, na przykład krzemu, które pod wpływem promieniowania słonecznego generują elektrony, tworząc prąd stały. Falownik, zwany inwerterem, przekształca ten prąd stały w prąd przemienny, który można wykorzystać do zasilania urządzeń elektrycznych w domu lub firmie. Pomaga to w integracji energii słonecznej z istniejącym systemem energetycznym.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 87

```text

Panel fotowoltaiczny zamienia światło słoneczne na energię elektryczną za pomocą ogniw fotowoltaicznych. Światło pada na ogniwa, które zawierają półprzewodniki, takie jak krzem, i powodują przepływ prądu elektrycznego. Falownik przekształca prąd stały z paneli w prąd zmienny, który jest używany w gniazdkach elektrycznych. Dzięki temu można korzystać z energii słonecznej w domu, biurze czy na działce.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 120

```text
 Panel fotowoltaiczny jest zbiorem komponentów przekształcających światło słoneczne w energię elektryczną. Energia słoneczna wchodzi do pana przez panel fotowoltaiczny i przekształcana jest w energię elektryczną. Energia elektryczna jest następnie przekształcona w energię prądu, która może być wykorzystana przez sieć elektroenergetyczną lub przechowywana w akumulatorach.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 74

```text
 Panel fotowoltaiczny zamienia światło słoneczne na prąd elektryczny za pomocą półprzewodników. W instalacji jest falownik, który przekształca prąd stały w prąd zmienny, aby mógł być wykorzystany przez urządzenia elektryczne.
```

### tekst_techniczny-10 (otwarte, trudność 1)

**Polecenie:** Wyjaśnij, czym jest adres IP i do czego służy system DNS, gdy wpisujemy w przeglądarce adres strony.

**Wzorzec:** Adres IP to numer identyfikujący urządzenie w sieci, dzięki któremu dane wiedzą, dokąd mają trafić. W wersji IPv4 ma postać czterech liczb od 0 do 255 oddzielonych kropkami, na przykład 192.168.1.10, a nowsza wersja IPv6 używa dłuższych adresów zapisywanych szesnastkowo. Ludziom łatwiej zapamiętać nazwy niż liczby, dlatego powstał DNS, czyli system nazw domenowych. Gdy wpisujemy w przeglądarce adres strony, komputer najpierw pyta serwer DNS, jaki adres IP odpowiada tej nazwie. Serwer zwraca adres, a przeglądarka łączy się już bezpośrednio z serwerem o tym numerze i pobiera stronę. Odpowiedzi DNS są przechowywane w pamięci podręcznej komputera i routera, więc kolejne wejście na tę samą stronę nie wymaga ponownego pytania. DNS działa więc jak książka telefoniczna internetu.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 107

```text

Adres IP (ang. Internet Protocol) to adres protokołu internetowego, który umożliwia komunikację między urządzeniami. To numer, który identyfikuje urządzenie w sieci i pozwala na jego identyfikację. Adresy IP są generowane automatycznie przez serwery DNS. Każdy komputer podłączony do sieci Internet musi mieć przypisany unikalny adres IP, który jest niezbędny do nawiązywania połączeń z innymi urządzeniami w sieci. Adresy IP są wykorzystywane do wysyłania i odbierania danych w Internecie.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 58

```text

Adres IP to numer, pod którym komputer w sieci lokalnej (np. w domu) ma dostęp do internetu. Adres IP jest przypisany do komputera, a nie do konkretnej maszyny. Adres IP jest unikalny dla każdego komputera w sieci lokalnej.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: eos, tokenów: 126

```text

Adres IP to unikalny numer identyfikujący urządzenie podłączone do sieci komputerowej. Składa się z 4 liczb dziesiętnych, oddzielonych kropkami, na przykład 192.168.1.1. Adres IP pozwala na identyfikację urządzenia i jego lokalizację w sieci. System DNS (Domain Name System) to usługa, która tłumaczy nazwy domen na adresy IP. Gdy wpisujemy adres strony internetowej, system DNS zamienia go na odpowiedni adres IP, który przeglądarka może odczytać. Dzięki temu możemy korzystać z zasobów sieci bez konieczności zapamiętywania numerów IP.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 102

```text

Adres IP to unikalny numer, który identyfikuje urządzenie w sieci. Składa się z 4 lub 12 cyfr i liter, na przykład 192.168.1.1. System DNS (Domain Name System) to baza danych, która tłumaczy nazwy domen na adresy IP. Gdy wpisujemy adres strony w przeglądarce, system DNS przeszukuje bazę, aby znaleźć odpowiedni adres IP i wyświetlić stronę.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 222

```text


Adres IP (Internet Protocol) to adres unikalny dla każdego urządzenia połączonego z Internetem. Jest to po prostu inny sposób na unikalny numer, który identyfikuje każdego komputera, telefonu czy innych urządzeń połączonych z Internetem.

System DNS (Domain Name System) to system, który pozwala na przeglądanie stron internetowych za pomocą znaków, a nie adresów IP. Na przykład, w celu odwiedzenia strony www.funkcjewebowe.pl, zamiast wprowadzić adres IP (188.8.131.52), wpisujemy adres DNS, który zawiera informacje o stronie. System DNS przekształca adres IP w adres DNS, a następnie przekazuje go do serwera internetowego, który odczyta adres i przekazuje go do komputera użytkownika.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 79

```text


Adres IP to adres unikalny, który identyfikuje dane komputerowe, na przykład adres IP 192.168.1.1. System DNS (Domain Name System) przekształca adres IP w adres URL, który jest łatwiejszy do zapamiętania i pisania.
```

### tekst_techniczny-11 (otwarte, trudność 2)

**Polecenie:** Porównaj protokoły TCP i UDP: czym się różnią i do jakich zastosowań pasuje każdy z nich.

**Wzorzec:** TCP i UDP to protokoły warstwy transportowej, które przenoszą dane między programami w sieci. TCP przed wysłaniem danych zestawia połączenie, numeruje segmenty, potwierdza ich odbiór i powtarza zgubione pakiety, dzięki czemu dane docierają kompletne i w kolejności. Ma też kontrolę przepływu i przeciążenia. Ceną jest większy narzut i opóźnienie. UDP wysyła pojedyncze datagramy bez zestawiania połączenia i bez potwierdzeń, więc pakiet może zginąć albo dotrzeć w innej kolejności, ale komunikacja jest szybka i lekka. TCP pasuje tam, gdzie liczy się kompletność: strony WWW, poczta, przesyłanie plików. UDP wybiera się, gdy ważniejsze jest małe opóźnienie niż każdy pakiet: rozmowy głosowe, wideokonferencje, gry sieciowe, a także krótkie zapytania DNS. Brakujące funkcje niezawodności można wtedy dodać w samej aplikacji.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 81

```text

Protokół TCP (Transmission Control Protocol) to standardowy sposób przesyłania danych. Polega na wysyłaniu ramek, czyli pakietów danych, między dwoma komputerami w sieci. Protokół UDP (User Datagram Protocol) to protokół sieciowy, który łączy urządzenia w sieci. UDP zapewnia większą niezawodność niż TCP.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 87

```text

Protokół TCP (Transmission Control Protocol) to protokół używany do przesyłania danych między komputerami. Jest to protokół sieciowy, który umożliwia przesyłanie danych między komputerami. Protokół UDP (User Datagram Protocol) to protokół używany do przesyłania danych między urządzeniami. Jest to protokół sieciowy, który umożliwia przesyłanie danych między urządzeniami.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 114

```text

TCP (Transmission Control Protocol) i UDP (User Datagram Protocol) to dwa protokoły transportowe w sieci Internet. TCP zapewnia niezawodne przesyłanie danych, co jest ważne w aplikacjach wymagających wysokiego poziomu usług, takich jak gry online czy przesyłanie strumieniowe wideo. UDP, z kolei, jest szybszy i bardziej efektywny w przesyłaniu danych, więc jest idealny dla aplikacji, które nie wymagają tak dokładnego dostarczania danych, na przykład komunikatory lub sieci społecznościowe.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 118

```text

TCP (Transmission Control Protocol) i UDP (User Datagram Protocol) to dwa protokoły sieciowe, które różnią się sposobem obsługi danych. TCP zapewnia niezawodne przesyłanie danych, zapewniając poprawność i integralność informacji. UDP jest prostszy i szybszy, ale nie gwarantuje poprawności danych. TCP jest używany w aplikacjach wymagających wysokiej jakości transmisji, takich jak gry online, podczas gdy UDP jest odpowiedni dla aplikacji wymagających szybkości i niskiego opóźnienia, takich jak przesyłanie strumieniowe wideo.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: limit, tokenów: 400

```text


Protokoły TCP (Transmission Control Protocol) i UDP (User Datagram Protocol) to protokoły używane do komunikacji w sieci. Są one różne, ponieważ różnią się sposobem obsługi danych i charakterem sieci. TCP (Transmission Control Protocol) jest protokole utrzymujące równoważność i niezawodności, UDP (User Datagram Protocol) to protokole statyczne, bez równoważności, bez zabezpieczeń.

Protokoły TCP (Transmission Control Protocol) to protokoły utrzymujące równoważność i niezawodność. Używają sekwencyjnych pakietów, które są zabezpieczone poprzez wskaźniki i pętle zabezpieczające. Pakiety są uzupełniane, zabezpieczane i przekazane. Protokoły TCP zapewniają wysoką niezawodność, ale są wolniejsze.

Protokoły UDP (User Datagram Protocol) to protokoły statyczne, bez równoważności, bez zabezpieczeń. Używają statycznych pakietów, które nie są zabezpieczane. Pakiety są uzupełniane, zabezpieczane i przekazane. Protokoły UDP są szybsze, ale niezawodne.

Protokoły TCP i UDP: w której przypadku jest preferowane?
W przypadku gdy dokładność jest najważniejsza, protokoły TCP są preferowane. Używają sekwencyjnych pakietów, które są zabezpieczone poprzez wskaźniki i
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 193

```text


Protokoły TCP i UDP to dwa podstawowe protokoły komunikacji w sieci. TCP (Transmission Control Protocol) to protokół zapewniający niezawodną transmisję danych, podczas gdy UDP (User Datagram Protocol) to protokół niezawodny, ale niezawodny. TCP jest używany do przesyłania dużych danych, takich jak pliki, podczas gdy UDP jest używany do przesyłania małych danych, takich jak wiadomości tekstowe. TCP jest również używany do przesyłania danych w czasie rzeczywistym, takich jak gry wideo, podczas gdy UDP jest używany do przesyłania danych w czasie rzeczywistym, takich jak transmisja wideo.
```

### tekst_techniczny-12 (otwarte, trudność 2)

**Polecenie:** Porównaj dysk SSD i dysk HDD pod względem budowy, szybkości, odporności na uszkodzenia i ceny za gigabajt.

**Wzorzec:** Dysk HDD zapisuje dane magnetycznie na wirujących talerzach, a odczyt i zapis wykonuje głowica na ruchomym ramieniu. Dysk SSD nie ma części ruchomych: przechowuje dane w komórkach pamięci flash, którymi zarządza kontroler. Dzięki temu SSD jest znacznie szybszy, zwłaszcza przy dostępie do wielu małych plików, bo nie musi czekać, aż talerz obróci się pod głowicę. Komputer z SSD szybciej się uruchamia i otwiera programy. SSD jest też odporniejszy na wstrząsy, cichszy i zużywa mniej energii, co ma znaczenie w laptopach. Komórki flash mają jednak ograniczoną liczbę cykli zapisu, choć w zwykłym użytkowaniu rzadko jest to problem. HDD wygrywa ceną za gigabajt, dlatego nadal stosuje się go do przechowywania dużych archiwów i kopii zapasowych, gdzie pojemność jest ważniejsza niż szybkość.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 47

```text

Dysk SSD ma znacznie większą gęstość niż dysk HDD. Dzięki temu jest bardziej odporny na uszkodzenia mechaniczne i szybsze. Dyski SSD są też tańsze od dysków HDD.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 70

```text

Dysk SSD jest szybszy od dysku HDD, ponieważ ma mniejszą powierzchnię, a więc i mniejszą objętość. Większa powierzchnia oznacza większą gęstość, a więc większą objętość. Dysk HDD jest droższy od dysku SSD, ponieważ ma większą powierzchnię, a więc i większą objętość.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 72

```text

Dysk SSD to pamięć flash, która nie ma ruchomych części. Jest bardzo szybki i niezawodny, ale droższy. Dysk HDD ma ruchome talerze, które mogą ulec uszkodzeniu, ale jest tańszy i bardziej pojemny. Oba mają swoje zalety i wady, a wybór zależy od indywidualnych potrzeb.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 105

```text

Dysk SSD (Solid State Drive) to pamięć flash, która nie ma ruchomych części i jest szybsza niż dysk HDD (Hard Disk Drive). Działa bez przerwy, nie ma przerw w odczycie i zapisie danych. Jest też odporny na wstrząsy i upadki, ale jest droższy. Dysk HDD ma ruchome talerze i głowicę, więc wolniej się zapisuje i odczytuje dane, ale jest tańszy.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 161

```text


Dysk SSD (Solid State Drive) i dysk HDD (Hard Disk Drive) to dwa typy dysków twardych, które można używać do przechowywania danych na komputerze. Dysk SSD to dysk z pamięci flash, który nie ma ruchomych części, co zapewnia szybsze działanie. Dysk HDD to dysk z mechanicznymi częściami, które obracają się, aby uzyskać dostęp do danych. Dysk HDD jest tańszy, ale jest wolniejszy. Dysk SSD jest droższy, ale jest szybszy i bardziej odporny na uszkodzenia.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: limit, tokenów: 400

```text


Dysk SSD (Solid State Drive) to dysk twardy, który nie zawiera rurki, ale ma wewnętrzną płytekę z układami elektronicznymi i sprzętem. Jest to dysk elektroniczny, który nie ma rurki, ale ma wewnętrzną płytekę z układami elektronicznymi i sprzętem. Jest to dysk elektroniczny, który nie ma rurki, ale ma wewnętrzną płytekę z układami elektronicznymi i sprzętem. Jest to dysk elektroniczny, który nie ma rurki, ale ma wewnętrzną płytekę z układami elektronicznymi i sprzętem. Jest to dysk elektroniczny, który nie ma rurki, ale ma wewnętrzną płytekę z układami elektronicznymi i sprzętem. Jest to dysk elektroniczny, który nie ma rurki, ale ma wewnętrzną płytekę z układami elektronicznymi i sprzętem. Jest to dysk elektroniczny, który nie ma rurki, ale ma wewnętrzną płytekę z układami elektronicznymi i sprzętem. Jest to dysk elektroniczny, który nie ma rurki, ale ma wewnętrzną płytekę z układami elektronicznymi i sprzętem. Jest to dysk elektroniczny, który nie ma rurki, ale ma wewnętrzną płytekę z układami elektronicznymi i sprzętem. Jest to dysk elektroniczny, który nie ma rurki, ale ma wewnętrzną płytekę z układami elektronicznymi i sprzętem.
```

### tekst_techniczny-13 (otwarte, trudność 2)

**Polecenie:** Wyjaśnij różnicę między procentem prostym a składanym na przykładzie lokaty 10 000 zł oprocentowanej 10% rocznie przez 3 lata.

**Wzorzec:** Przy procencie prostym odsetki liczy się zawsze od kwoty początkowej. Lokata 10 000 zł na 10% rocznie daje co roku 1 000 zł odsetek, więc po 3 latach na koncie jest 13 000 zł. Przy procencie składanym odsetki po każdym okresie dopisuje się do kapitału i w następnym roku one też pracują. Po pierwszym roku jest 11 000 zł, po drugim 11 000 · 1,1 = 12 100 zł, a po trzecim 12 100 · 1,1 = 13 310 zł. Różnica wynosi 310 zł i rośnie coraz szybciej z każdym kolejnym rokiem, bo kapitał rośnie wykładniczo. Ogólny wzór dla procentu składanego to K · (1 + r)ⁿ. Ten sam mechanizm działa przeciw kredytobiorcy, gdy niespłacone odsetki powiększają dług. W przykładzie pominięto podatek od odsetek, który w praktyce zmniejsza zysk.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 61

```text

Procent składany polega na tym, że co roku zwiększa się wartość odsetek od kapitału, a odsetki od kapitału są dodawane do odsetek, które już zostały wypłacone. W ten sposób po 3 latach odsetki od kapitału będą już znacznie większe od odsetek od odsetek.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: limit, tokenów: 400

```text

Procent prosty to procent składany, czyli procent składany, który jest sumą procentu składanego i procentu składanego. Procent składany to procent składany, który jest sumą procentu składanego i procentu składanego. Procent składany to procent składany, który jest sumą procentu składanego i procentu składanego. Procent składany to procent składany, który jest sumą procentu składanego i procentu składanego. Procent składany to procent składany, który jest sumą procentu składanego i procentu składanego. Procent składany to procent składany, który jest sumą procentu składanego i procentu składanego. Procent składany to procent składany, który jest sumą procentu składanego i procentu składanego. Procent składany to procent składany, który jest sumą procentu składanego i procentu składanego. Procent składany to procent składany, który jest sumą procentu składanego i procentu składanego. Procent składany to procent składany, który jest sumą procentu składanego i procentu składanego. Procent składany to procent składany, który jest sumą procentu składanego i procentu składanego. Procent składany to procent składany, który jest sumą procentu składanego i procentu składanego. Procent składany to procent składany, który jest sumą procentu składanego i procentu składanego. Procent składany to procent składany, który jest sumą procentu składanego i procentu składanego. Procent składany to procent składany, który jest sumą procentu składanego i procentu składanego. Procent składany to procent składany, który jest sumą procentu składanego i procentu składanego. Procent składany to procent składany, który jest sumą procentu składanego i procentu składanego. Procent składany
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 151

```text

Procent składany jest naliczany od całości kapitału, a nie tylko od odsetek. W przypadku lokaty 10 000 zł oprocentowanej 10% rocznie przez 3 lata, przy procentowym prostym oprocentowanie wyniesie 10% rocznie, co daje 1000 zł odsetek rocznie. Po 3 latach odłóżałoby się 3000 zł. Z kolei przy procentowym składanym, oprocentowanie jest naliczane co roku od aktualnego salda, co oznacza, że w pierwszym roku oprocentowanie wynosi 1000 zł, a w drugim i trzecim roku 1100 zł. W rezultacie po 3 latach odłóżałoby się 3310 zł.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 185

```text

Procent składany to sposób obliczania odsetek, w którym odsetki są dodawane do kapitału i naliczane od nowego kapitału. Na przykład, jeśli wpłacamy 10 000 zł na 10% rocznie przez 3 lata, to po pierwszym roku mamy 10 000 zł + 1000 zł = 11 000 zł. Po drugim roku mamy 11 000 zł + 1100 zł = 12 100 zł. Po trzecim roku mamy 12 100 zł + 1210 zł = 13 310 zł. W przypadku procentowego wzrostu, po 3 latach mamy 13 310 zł, ale w przypadku procentowego wzrostu, po 3 latach mamy 13 310 zł.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 141

```text
 Procent prosta na przykładzie lokaty 10 000 zł oprocentowanej 10% rocznie przez 3 lata oznacza, że za każdy rok oszczędzasz 10% (10 000 x 10/100) 100 zł. Po 3 latach oszczędności łącznie wynosi 300 zł (100 zł + 100 zł + 100 zł). To oznacza, że 10% rocznie to procent składany, ponieważ obliczany jest z uwzględnieniem składania zysku z poprzedniego roku.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 113

```text
 Procent prosty to procent odsetka, który jest obliczany na początku okresu i nie zmienia się w ciągu okresu. Na przykład, jeśli procent roczny wynosi 10%, to w pierwszym roku odsetek wynosi 10% zainwestowanych 10 000 zł, w drugim roku 10% zainwestowanych 10 000 zł i w trzecim roku 10% zainwestowanych 10 000 zł.
```

### tekst_techniczny-14 (otwarte, trudność 2)

**Polecenie:** Wyjaśnij, jak działa powietrzna pompa ciepła i co oznacza współczynnik COP.

**Wzorzec:** Pompa ciepła nie wytwarza ciepła ze spalania, tylko przenosi je z otoczenia do budynku, podobnie jak lodówka przenosi ciepło z wnętrza na zewnątrz. W obiegu krąży czynnik chłodniczy. W parowniku odbiera on ciepło z powietrza zewnętrznego i odparowuje, nawet przy ujemnej temperaturze. Sprężarka napędzana prądem spręża parę, przez co rośnie jej temperatura. W skraplaczu czynnik oddaje ciepło wodzie w instalacji grzewczej i skrapla się, a zawór rozprężny obniża jego ciśnienie i cykl zaczyna się od nowa. COP to stosunek ciepła oddanego do budynku do zużytej energii elektrycznej. COP równy 3 oznacza, że z 1 kWh prądu pompa dostarcza 3 kWh ciepła. Współczynnik spada, gdy na zewnątrz robi się zimniej, a woda w instalacji ma wyższą temperaturę, dlatego pompy najlepiej pracują z ogrzewaniem podłogowym.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 135

```text

Pompa ciepła to urządzenie, które przekształca energię cieplną (ciepło) z jednego medium (np. z powietrza) na inne medium (np. wodę). W pompie ciepła ciepło jest pobierane z otoczenia (np. z powietrza, gruntu, wody) i przekazywane do cieczy, która jest następnie używana do ogrzewania budynku. Współczynnik COP (Coefficient of Performance) to stosunek ilości ciepła dostarczonego do energii pobranej z otoczenia do ilości ciepła dostarczonego do medium. Im wyższy współczynnik COP, tym lepsza wydajność pompy ciepła. Współczynnik COP jest miarą efektywności energetycznej pompy ciepła.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 104

```text

Pompa ciepła to urządzenie, które pobiera ciepło z otoczenia i przekazuje je do wnętrza budynku. W pompie ciepła ciepło jest pobierane z powietrza, wody lub gruntu, a następnie przekazywane do wnętrza budynku. Współczynnik COP (Coefficient of Performance) to stosunek ilości ciepła, które pompa ciepła jest w stanie dostarczyć do budynku, do ilości ciepła, które pompa ciepła jest w stanie z niego odebrać. Im wyższy współczynnik COP, tym lepsza wydajność pompy ciepła.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 123

```text

Pompa ciepła pobiera ciepło z otoczenia (powietrza, wody lub gruntu) i przekazuje je do instalacji grzewczej w budynku. W pompach powietrznych czynnikiem chłodniczym jest freon, a obieg zamknięty, zamknięty obieg otwarty lub otwarty obieg otwarty. Współczynnik COP (coefficient of performance) to stosunek mocy grzewczej do mocy elektrycznej pobieranej przez pompę. Im wyższy, tym bardziej efektywna jest pompa. Współczynnik COP określa, ile ciepła może pobrać pompa na jednostkę energii elektrycznej pobranej z sieci.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 109

```text

Pompa ciepła pobiera ciepło z otoczenia, np. z powietrza, i przekazuje je do instalacji grzewczej. W pompach powietrznych powietrze jest pobierane przez wentylator i ogrzewane przez czynnik chłodniczy, który krąży w obiegu zamkniętym. Współczynnik COP (ang. Coefficient of Performance) to stosunek ilości ciepła dostarczonego do instalacji grzewczej do ilości energii elektrycznej zużytej przez pompę. Im wyższy COP, tym bardziej efektywna jest pompa ciepła.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: limit, tokenów: 400

```text


Pompa ciepła powietrzna jest polegająca na przetwarzaniu powietrza z zewnątrz, wzmacniając jego temperaturę i kierując go do pompy ciepła, a następnie wykorzystując wytworzony ciepło do ogrzewania pomieszczenia. Jej działanie opiera się na zasadzie wzmacniania ciepła z powietrza, który jest rozdzielany na dwa gazy o różnych temperaturach. Gdy gazy są przepuszczane przez specjalną jednostkę zwaną odgrzewaczem, wychodzi chłodniejszy gaz, który jest wciągany przez kompresor i włącza się do procesu ogrzewania pomieszczenia.

Współczynnik COP (Coeficient Ogrzewania) to wartość mierząca efektywność pompy ciepła. Oznacza ona ilość ciepła zapewnianego przez jednostkę energii elektrycznej wytwarzanego przez kompresor. Jest to wyrażone w postaci:

COP = ciepło wyjściowe / energia wejściowa

Na przykład, jeśli pompa ciepła o współczynniku COP 3,0 wytwarza 3 kWh ciepła, a zużywa 1 kWh energii elektrycznej, to jest jej efektywność:

COP = 3 kWh / 1 kWh = 3

Oznacza to, że za każdy kWh energii elektrycznej wytworzona przez pompę ciepła, jest wytworzono 3 k
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 233

```text


Pompa ciepła powietrzna to urządzenie, które pobiera ciepło z powietrza i przenosi je do pomieszczenia, gdzie jest potrzebne. W przeciwieństwie do tradycyjnych systemów grzewczych, które ciepłem wytwarzają, pompy ciepła pobierają ciepło z powietrza i je przekształcają w ciepło, które jest następnie rozprowadzane do pomieszczenia.

Współczynnik COP (Coefficient of Performance) to stosunek ciepła wyjściowego do ciepła wejściowego. Jest to wskaźnik wydajności pompy ciepła. Na przykład, jeśli pompa ciepła ma współczynnik COP równy 4, oznacza to, że dla każdego 1 kWh energii elektrycznej pobierana jest 4 kWh ciepła.
```

### tekst_techniczny-15 (otwarte, trudność 2)

**Polecenie:** Wyjaśnij, dlaczego w budownictwie łączy się beton ze stalą (żelbet) i gdzie w belce umieszcza się zbrojenie.

**Wzorzec:** Beton dobrze przenosi ściskanie, ale jego wytrzymałość na rozciąganie jest mniej więcej dziesięć razy mniejsza, więc pod obciążeniem szybko pęka po rozciąganej stronie. Stal ma dużą wytrzymałość na rozciąganie, dlatego pręty zbrojeniowe przejmują siły, których beton nie wytrzymałby sam. Połączenie działa, bo stal i beton mają zbliżony współczynnik rozszerzalności cieplnej i dobrze ze sobą współpracują dzięki przyczepności, wspomaganej żebrowaniem prętów. Otulina betonowa chroni też stal przed korozją i ogniem. W belce swobodnie podpartej obciążonej z góry dolna część jest rozciągana, a górna ściskana, dlatego główne zbrojenie umieszcza się na dole przekroju. Przy podporach stosuje się dodatkowo strzemiona, które przenoszą siły ścinające. W belce wspornikowej rozciągana jest strona górna, więc tam trafia zbrojenie główne.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 125

```text

W betonie naprężenie ściskające w kierunku ściskania jest znacznie większe niż w kierunku rozciąganym. W betonie naprężenie ściskające w kierunku rozciąganym jest mniejsze niż w kierunku ściskającym, bo w betonie nie ma sił rozciągających. Dlatego w betonie naprężenie ściskające w kierunku ściskania jest mniejsze niż w kierunku rozciąganym. W betonie naprężenie ściskające w kierunku rozciąganym jest mniejsze niż w kierunku ściskającym, bo w betonie nie ma sił rozciągających.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 65

```text

W betonie zbrojenie jest umieszczone w betonie, a nie w stali. Beton jest materiałem, który ma dużą gęstość, więc w nim zbrojenie jest umieszczone w betonie. Stal jest materiałem, który ma małą gęstość, więc w nim zbrojenie jest umieszczone w stali.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 81

```text

Beton i stal łączy się, by zwiększyć wytrzymałość konstrukcji. Zbrojenie wzmacnia beton, ograniczając naprężenia rozciągające w betonie. To zabezpiecza belkę przed pęknięciem pod obciążeniem. Zbrojenie to pręty stalowe lub pręty z drutu stalowego, które są umieszczane w betonie w specjalnych otworach, zwanych prętami zbrojeniowymi.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 124

```text

Beton i stal są ze sobą łączone, aby zwiększyć wytrzymałość konstrukcji. Beton jest materiałem o dużej wytrzymałości na ściskanie, ale słabym na rozciąganie, podczas gdy stal jest mocna na rozciąganie, ale słaba na ściskanie. Łącząc je, uzyskuje się materiał o wysokiej wytrzymałości na rozciąganie i ściskanie. Zbrojenie umieszcza się w belce, aby zwiększyć jej wytrzymałość na rozciąganie. Zbrojenie to pręty lub druty wykonane z metalu, które są wbijane lub wciskane w beton, tworząc siatkę wzmacniającą belkę.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 151

```text
 W budownictwie beton jest stosowany jako materiał konstrukcyjny ze względu na swoją wysoką wytrzymałość, stabilność, przewidywalność i niski koszt. Beton jest zazwyczaj mieszany z żwirkiem, piaskiem, kruszami i innych materiałami. Zbrojenie jest dodawane do betonu w celu zwiększenia jego wytrzymałości i wytrzymałości na rozciąganie. Zbrojenie jest zazwyczaj w formie drutu stalowego, ale czasami stosuje się stal, żelazo lub beton.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 123

```text


Łączenie betonu ze stalą (żelbetu) jest stosowane w konstrukcjach, które wymagają wysokiej wytrzymałości i stabilności. Stal jest używana do wzmacniania konstrukcji, aby zwiększyć ich wytrzymałość i wytrzymałość na rozciąganie. Zbrojenie jest umieszczane w belce, aby zapewnić dodatkową wytrzymałość i stabilność konstrukcji.
```

### tekst_techniczny-16 (otwarte, trudność 2)

**Polecenie:** Opisz krok po kroku, jak w zespole programistów wprowadza się zmianę w kodzie przy użyciu gita i pull requesta.

**Wzorzec:** Najpierw programista pobiera aktualny stan głównej gałęzi poleceniem git pull, żeby zaczynać od najnowszej wersji. Następnie tworzy osobną gałąź na zadanie, na przykład git switch -c poprawka-logowania, dzięki czemu jego praca nie miesza się z pracą innych. Wprowadza zmiany, uruchamia testy i zapisuje je w małych commitach z opisowymi komunikatami: git add, a potem git commit. Gotową gałąź wysyła na serwer poleceniem git push i otwiera pull request do gałęzi głównej. W pull requeście inni członkowie zespołu przeglądają kod, a automatyczne testy sprawdzają, czy zmiana niczego nie psuje. Autor poprawia uwagi kolejnymi commitami. Gdy recenzja i testy są pozytywne, gałąź zostaje scalona z główną, a gałąź zadania można usunąć. Jeśli główna gałąź w międzyczasie się zmieniła, trzeba najpierw rozwiązać ewentualne konflikty.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 145

```text

W zespole programistów, który pracuje nad nowym projektem, każdy członek zespołu ma swoją rolę do odegrania. Jednym z zadań jest wprowadzenie zmiany w kodzie źródłowym, aby poprawić jego funkcjonalność lub wydajność. Gdy zespół programistów pracuje nad nowym projektem, zwykle ma dostęp do kilku narzędzi, które pomagają w tym procesie. Jednym z takich narzędzi jest git, które umożliwia zespołowi programistów zmianę kodu źródłowego. Git jest narzędziem, które pozwala zespołowi programistów na modyfikację kodu źródłowego w celu poprawy jego funkcjonalności lub wydajności. Git umożliwia zespołowi programistów wprowadzanie zmian w kodzie źródłowym w jednym pliku, co pozwala na łatwiejszą i bardziej efektywną pracę.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 79

```text

W zespole programistów wprowadza się zmianę w kodzie przy użyciu gita i pull requesta. Polega to na tym, że w kodzie źródłowym zapisuje się zmiany w pliku, który następnie jest przekazywany do gita. W gicie sprawdza się, czy zmiany zostały wprowadzone, a następnie wysyła się pull request do zespołu, który je wprowadza.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: eos, tokenów: 145

```text

W zespole programistów zmiana w kodzie wprowadzana jest za pomocą gita (git pull -rebase) i pull requestu (git pull rebase -r repozytorium). Najpierw zespół repopluje zmiany z repozytorium, a następnie rebazuje je do aktualnej gałęzi (poprzez rebaz, czyli wsteczne wykonanie zmian). Po rebazie zespół sprawdza, czy zmiany zostały uwzględnione w repozytorium, i zgłasza je jako pull request. W odpowiedzi na ten request zespół sprawdza, czy zmiany zostały uwzględnione i jeśli tak, akceptuje je. Jeśli nie, zespół może zaproponować poprawki i ponownie rebazować zmiany.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 243

```text

1. Zespół programistów tworzy pull request (PR) w systemie kontroli wersji, takim jak Git Hub.
2. W PR opisuje się zmiany, które mają zostać wprowadzone, na przykład dodanie nowego pliku lub poprawki w istniejącym.
3. Zespół zatwierdza PR, akceptując zmiany lub zgłaszając uwagi.
4. Po zatwierdzeniu PR jest wysyłany do repozytorium, gdzie jest dostępny dla innych członków zespołu.
5. Zespół programistów korzysta z gita (Git Assistant) do przeglądania i zarządzania zmianami w kodzie.
6. Gdy zmiany są gotowe, zespół programistów tworzy nowy repozytorium, które będzie zawierało zaktualizowany kod.
7. Zespół programistów tworzy pull request dla nowego repozytorium, opisując zmiany i proponując ich przyjęcie.
8. Zespół zatwierdza pull request, akceptując zmiany lub zgłaszając uwagi.
9. Po zatwierdzeniu pull request jest wysyłany do repozytorium, gdzie jest dostępny dla innych członków zespołu.
10. Zespół programistów korzysta z gita do przeglądania i zarządzania zmianami w kodzie.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 101

```text


Wzajemne wpisy w kodzie źródłowym są tworzone za pomocą języków programowania, takich jak C, C++, Java, PHP, Python, Ruby, Go i Swift. Wzajemne wpisy w kodzie źródłowym są tworzone za pomocą języków programowania, takich jak C, C++, Java, PHP, Python, Ruby, Go i Swift.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: limit, tokenów: 400

```text


Krok po kroku wprowadzanie zmian w kodzie przy użyciu gita i pull requesta:

1. Zadbaj o zrozumienie kodu źródłowego. Zanim zaczniesz wprowadzać zmiany, zrozum, jak kod działa, jakie zmiany wprowadzasz i jakie mają one na kod.

2. Zadbaj o zrozumienie kodu docentowego. Zanim zaczniesz wprowadzać zmiany, zrozum, jak kod docentowy działa, jakie zmiany wprowadzasz i jakie mają na kod.

3. Zadbaj o zrozumienie kodu testowego. Zanim zaczniesz wprowadzać zmiany, zrozum, jak kod testowy działa, jakie zmiany wprowadzasz i jakie mają na kod.

4. Zadbaj o zrozumienie kodu dokumentacyjnego. Zanim zaczniesz wprowadzać zmiany, zrozum, jak kod dokumentacyjny działa, jakie zmiany wprowadzasz i jakie mają na kod.

5. Zadbaj o zrozumienie kodu testowego. Zanim zaczniesz wprowadzać zmiany, zrozum, jak kod testowy działa, jakie zmiany wprowadzasz i jakie mają na kod.

6. Zadbaj o zrozumienie kodu docentowego. Zanim zaczniesz wprowadzać zmiany, zrozum, jak kod docentowy działa, jakie zmiany wprowadzasz i jakie mają na kod.

7. Zadbaj o zrozumienie kodu testowego.
```

### tekst_techniczny-17 (otwarte, trudność 2)

**Polecenie:** Wyjaśnij mechanizm efektu cieplarnianego i rolę gazów takich jak dwutlenek węgla.

**Wzorzec:** Promieniowanie słoneczne dociera do Ziemi głównie jako światło widzialne, które w dużej części przechodzi przez atmosferę i ogrzewa powierzchnię. Ogrzana powierzchnia oddaje energię jako promieniowanie podczerwone. Gazy cieplarniane, przede wszystkim para wodna, dwutlenek węgla, metan i podtlenek azotu, pochłaniają część tej podczerwieni i wypromieniowują ją we wszystkich kierunkach, także z powrotem ku powierzchni. Dzięki temu Ziemia jest cieplejsza, niż byłaby bez atmosfery: naturalny efekt cieplarniany podnosi średnią temperaturę o około 33 °C, z mniej więcej −18 °C do około 15 °C. Problemem jest wzmocnienie tego efektu. Spalanie węgla, ropy i gazu oraz wylesianie zwiększyły stężenie CO₂ w atmosferze od czasów przedprzemysłowych o ponad 40%, przez co mniej energii ucieka w kosmos i średnia temperatura rośnie.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 98

```text

Efekt cieplarniany to proces, który powoduje ocieplenie klimatu, czyli wzrost średniej temperatury na Ziemi. Polega na zatrzymywaniu promieniowania słonecznego, które zostaje pochłonięte przez powierzchnię Ziemi, przez co zmniejsza się ilość energii cieplnej docierającej do planety. Z powodu efektu cieplarnianego temperatura na Ziemi stale rośnie, co powoduje topnienie lodowców, podnoszenie się poziomu mórz i oceanów oraz podnoszenie się poziomu wód w oceanach.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 65

```text

Efekt cieplarniany to zjawisko, w którym temperatura na Ziemi wzrasta, ponieważ więcej energii cieplnej jest zatrzymywane przez gazy cieplarniane, takie jak dwutlenek węgla. W efekcie temperatura na Ziemi rośnie, co prowadzi do topnienia lodowców i podnoszenia się poziomu mórz.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 78

```text

Efekt cieplarniany to zjawisko polegające na zatrzymywaniu ciepła wewnątrz atmosfery. Głównym gazem odpowiedzialnym za ten efekt jest dwutlenek węgla (CO2), który pochłania energię słoneczną i nie pozwala jej uciec z powrotem do kosmosu. Jego stężenie w atmosferze wzrosło wskutek działalności człowieka, takiej jak spalanie paliw kopalnych, co prowadzi do globalnego ocieplenia.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 89

```text

Efekt cieplarniany to zjawisko, w którym gazy cieplarniane, takie jak dwutlenek węgla, zatrzymują ciepło w atmosferze, co prowadzi do wzrostu średniej temperatury na Ziemi. Dwutlenek węgla jest jednym z głównych gazów cieplarnianych, produkowanym przez działalność człowieka, na przykład przez spalanie paliw kopalnych. Jego obecność w atmosferze zwiększa zdolność do zatrzymywania ciepła, co prowadzi do globalnego ocieplenia.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 294

```text


Efekt cieplarniany to zjawisko ośrodka atmosfery, w którym pewne gazy, takie jak dwutlenek węgla i parę wodną, zatrzymują część promieniowania słonecznego w górę, zanim dotrze do powierzchni Ziemi. To powoduje podwyższenie średniej temperatury powierzchni.

Gazy te powstają głównie przez działalność człowieka, np. spalanie paliw kopalnych, które emituje duże ilości dwutlenku węgla. Zwiększona temperatura powoduje, że rośliny pochłaniają mniej dwutlenku węgla i więcej dwutlenku węgla, co dodatkowo podwyższa efekt cieplarniany.

Dodatkowo, zmiany klimatyczne mogą również zmniejszać efekt cieplarniany. Na przykład, niektóre badania sugerują, że na Ziemi zdolność do zatrzymywania ciepła może zmniejszać się, jeśli zimne wody w oceanach zaczną doświadczać mniej częstych i intensywniejszych powodzi.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 243

```text


Efekt cieplarniany to zjawisko, w którym gazom cieplarnianym, takich jak dwutlenek węgla, węgiel czarny i metan, zatrzymuje ciepło emitowane przez powierzchnię Ziemi. Ziemia emituje ciepło, gdy wychodzi na zewnątrz promieniowanie elektromagnetyczne. Gazy cieplarniane zatrzymują część tego promieniowania, co powoduje, że temperatura powierzchni Ziemi jest wyższa niż w przypadku braku takich gazów.

Gazy cieplarniane są naturalne i występują w atmosferze Ziemi w niewielkich ilościach. Jednak z powodu działalności człowieka, szczególnie spalanie paliw kopalnych, zwiększyła się ilość gazów cieplarnianych w atmosferze, co powoduje efekt cieplarniany i globalne ocieplenie.
```

### tekst_techniczny-18 (otwarte, trudność 2)

**Polecenie:** Wyjaśnij pojęcie kosztu alternatywnego na przykładzie z życia albo z firmy.

**Wzorzec:** Koszt alternatywny to wartość najlepszej możliwości, z której rezygnujemy, wybierając inną. Nie zawsze widać go w księgowości, bo nie jest wydatkiem, tylko utraconą korzyścią. Przykład: właścicielka małej firmy ma 50 000 zł wolnej gotówki. Może kupić za nie nową maszynę albo obligacje oprocentowane 6% rocznie. Jeśli wybierze maszynę, jej kosztem alternatywnym jest między innymi 3 000 zł odsetek, których nie dostanie w ciągu roku. Zakup ma sens ekonomiczny tylko wtedy, gdy maszyna przyniesie więcej niż ta utracona korzyść. Podobnie student, który zamiast pracować dorywczo za 4 000 zł miesięcznie uczy się w pełnym wymiarze, ponosi koszt w postaci utraconego wynagrodzenia. Myślenie kosztem alternatywnym pomaga porównywać decyzje, które na pierwszy rzut oka wydają się darmowe.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 48

```text

Koszt alternatywny to cena, którą klient musiałby zapłacić za usługi oferowane przez firmę. W przypadku firm koszty alternatywne to koszty, które firma musi ponieść, aby zapewnić sobie uzyskanie tych samych wyników.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 54

```text

Koszt alternatywny to koszt, jaki poniósłby konsument, gdyby alternatywny produkt nie istniał. Na przykład, jeśli konsument kupiłby samochód, to koszt alternatywny byłby niższy, gdyby zamiast niego kupił rower.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 138

```text

Koszt alternatywny to koszt, który ponosimy, wybierając jedną z opcji zamiast innej. W życiu codziennym może to być decyzja o tym, czy kupić droższą, ale lepszą kawę, czy tańsze, ale mniej smaczne. W firmie koszt alternatywny to różnica między zyskiem, który moglibyśmy osiągnąć, gdyby zainwestowaliśmy w inny projekt, a tym, co faktycznie zarobiliśmy. Na przykład, jeśli firma może zainwestować 100 000 zł w reklamę w telewizji, ale lepiej zainwestować w reklamę w internecie, która kosztuje 50 000 zł, to koszt alternatywny to 50 000 zł.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 97

```text

Koszt alternatywny to cena, jaką trzeba zapłacić za rezygnację z jednej opcji na rzecz innej. Na przykład, jeśli firma musi wybrać między dwoma projektami inwestycyjnymi, koszt alternatywny to różnica między potencjalnymi zyskami z obu projektów. Jeśli projekt A przyniesie 100 000 zł zysku, a projekt B 120 000 zł, to koszt alternatywny projektu A to 20 000 zł.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 185

```text


Koszt alternatywny to koszty, które można zaoszczędzić, gdyby wybrał się kogoś innego zamiast samego. Na przykład, jeśli chcesz zjeść jedzenie, możesz zacząć od pikantnych kakao, a nie od masła. Jeśli chcesz zjeść zupę, możesz zamiast pomarańczy, kupić zupa na pieniądze. Jeśli chcesz zjść kawę, możesz zamiast kawy zawsze wziąć herbatę. Jeśli chcesz zjeść jedzenie, możesz zamiast kupować jedzenie, zacząć od przygotowywania jedzenia w domu.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 126

```text


Koszt alternatywny to koszt, który można osiągnąć za pomocą innej metody lub technologii. Na przykład, jeśli firma chce zrealizować projekt, może wybrać między różnymi metodami realizacji projektu. Koszt alternatywny to koszt, który można osiągnąć za pomocą innej metody lub technologii. Na przykład, jeśli firma chce zrealizować projekt, może wybrać między różnymi metodami realizacji projektu.
```

### tekst_techniczny-19 (otwarte, trudność 2)

**Polecenie:** Wyjaśnij, dlaczego energię elektryczną przesyła się na duże odległości liniami wysokiego napięcia.

**Wzorzec:** Przy przesyle energii część mocy tracona jest na ogrzewanie przewodów. Straty te są proporcjonalne do kwadratu natężenia prądu i do oporu linii: P = I² · R. Moc przesyłana to iloczyn napięcia i natężenia, więc tę samą moc można przesłać przy wyższym napięciu i mniejszym prądzie. Dziesięciokrotne podniesienie napięcia zmniejsza prąd dziesięć razy, a straty w przewodach aż sto razy. Dlatego przy elektrowni napięcie podnosi się transformatorami do kilkuset kilowoltów; w polskiej sieci przesyłowej stosuje się między innymi 220 kV i 400 kV. W pobliżu odbiorców kolejne stacje transformatorowe obniżają napięcie do średniego, a potem do 230 V w gniazdkach. Transformatory działają na prądzie przemiennym, co było jednym z głównych powodów, dla których sieci energetyczne zbudowano na prądzie przemiennym.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 69

```text

Energię elektryczną przesyła się na duże odległości, wykorzystując linie wysokiego napięcia. Gdy prąd płynie przez ziemię, płynie przez dziesiątki kilometrów, a gdy płynie przez morze, płynie przez tysiące kilometrów. Do przesyłu energii wykorzystuje się linie napowietrzne, które układają się w korytarze, którymi płynie prąd.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 50

```text

Energia elektryczna jest przesyłana na duże odległości liniami wysokiego napięcia, ponieważ prąd elektryczny jest nośnikiem energii. W liniach wysokiego napięcia prąd płynie w kierunku od źródła do odbiornika, a nie odwrotnie.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 72

```text

Energię elektryczną przesyła się na duże odległości liniami wysokiego napięcia, bo prąd jest słabszy w wyższych odległościach. Napięcie elektryczne jest odwrotnie proporcjonalne do kwadratu odległości. Linie wysokiego napięcia mają grubość przewodów i napięcie większe niż w zwykłych liniach, a do przesyłania energii potrzeba mniej przewodów.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 70

```text

Energia elektryczna przesyła się na duże odległości liniami wysokiego napięcia, aby zmniejszyć straty energii podczas przesyłania. Wysoka moc linii pozwala przesyłać energię z elektrowni do odbiorców bez strat. Dzięki temu można dostarczać prąd do odległych miejsc, na przykład do miast i wsi, bez konieczności budowania długich linii niskiego napięcia.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 127

```text
 Linie wysokiego napięcia przesyłają energię elektryczną na duże odległości dzięki wyższej napięciu, ponieważ to pozwala zmniejszyć straty energii podczas transmisji. Gdy napięcie jest niskie, linia przesyłowa jest bardzo długa, a energia przekazywana jest słabo. W przypadku wysokiego napięcia, linia przesyłowa jest krótsza, a energia jest przekazywana bardzo dobrze.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 88

```text
 Energia elektryczna przesyła się na duże odległości liniami wysokiego napięcia, ponieważ wysokie napięcie zmniejsza straty energii w przewodach. Gdy napięcie jest niskie, energia jest tracona w postaci ciepła, co zmniejsza efektywność transmisji.
```

### tekst_techniczny-20 (otwarte, trudność 2)

**Polecenie:** Wyjaśnij, czym jest indeks w relacyjnej bazie danych, jakie daje korzyści i jakie ma koszty.

**Wzorzec:** Indeks to dodatkowa struktura danych, najczęściej drzewo B, która przechowuje wartości wybranej kolumny w uporządkowanej postaci razem ze wskaźnikami do wierszy tabeli. Działa jak skorowidz na końcu książki: zamiast przeglądać wszystkie strony, od razu wiadomo, gdzie szukać. Bez indeksu zapytanie z warunkiem na kolumnie email wymaga przejrzenia całej tabeli, co przy milionach wierszy jest wolne. Z indeksem baza znajduje wiersz w kilku krokach. Indeksy przyspieszają też sortowanie i łączenie tabel. Mają jednak koszty. Zajmują miejsce na dysku, a każde wstawienie, zmiana albo usunięcie wiersza wymaga aktualizacji wszystkich indeksów tabeli, co spowalnia zapis. Dlatego indeksuje się kolumny często używane w warunkach wyszukiwania i złączeniach, a nie wszystkie. Przy kolumnie o kilku możliwych wartościach indeks zwykle niewiele daje.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 73

```text

Indeks to uporządkowany zbiór elementów bazy danych. W relacyjnej bazie danych każdy element (nazwa, wartość, typ, atrybut) jest identyfikowany przez unikatowy numer. Dzięki temu, gdy baza danych jest rozbudowywana, w wyniku dodawania nowych rekordów, możliwe jest odnalezienie danego elementu w bazie.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 51

```text

Indeks to liczba, która jest przechowywana w bazie danych. W relacyjnej bazie danych jest to liczba, która jest przechowywana w tabeli. Tabela zawiera informacje o wszystkich rekordach, które są w niej zawarte.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 70

```text

Indeks w relacyjnej bazie danych to struktura, która umożliwia szybkie wyszukiwanie danych. Pokazuje, które wiersze są połączone z innymi, więc nie trzeba przeglądać całej tabeli, tylko tylko interesujący fragment. Pozwala skrócić czas wyszukiwania, ale wymaga dodatkowych zasobów, takich jak miejsce na dysku i moc obliczeniowa.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 104

```text

Indeks to struktura danych, która pozwala na szybkie wyszukiwanie rekordów w bazie danych. Składa się z kluczy, które są unikalnymi identyfikatorami dla rekordów, oraz pól, które zawierają wartości dla każdego klucza. Dzięki indeksom można szybko znaleźć rekordy, które spełniają określone kryteria, na przykład po nazwie lub adresie. Korzyści z indeksów to szybsze wyszukiwanie i mniejsza ilość danych do przetworzenia. Koszty to większa złożoność struktury danych i większe zapotrzebowanie na pamięć.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 178

```text


Indeks w relacyjnej bazie danych to zestawowy element, który pozwala na wyszukiwanie danych w bazie danych. Wszystkie wartości w indeksie są indeksowane, co oznacza, że każda wartość ma określony indeks. W indeksie zbiorowo wyznaczono indeksy, które są używane do wyszukiwania w bazie danych. W zależności od indeksu, które używasz, wyniki wyszukiwania będą różne. Przykładem indeksu jest indeks kolumny "odniesienie" w relacji między tablicą "klienty" a tablicą "szlachetności".
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 126

```text


Indeks w relacyjnej bazie danych to tablica, która zawiera informacje o relacji między różnymi tabelami. Dzięki indeksowi można szybko znaleźć dane, które są powiązane z danymi w innych tabelach. Na przykład, jeśli w jednej tabeli znajdują się informacje o produktach, a w innej o klientach, indeks pozwala znaleźć informacje o produktach, które kupili dana osoba.
```

### tekst_techniczny-21 (otwarte, trudność 3)

**Polecenie:** Firma produkuje kubki. Koszty stałe wynoszą 20 000 zł miesięcznie, koszt zmienny jednego kubka 30 zł, a cena sprzedaży 50 zł. Przeanalizuj próg rentowności i oceń, co się stanie z wynikiem przy sprzedaży 1 500 kubków oraz po obniżce ceny do 45 zł.

**Wzorzec:** Każdy sprzedany kubek daje marżę na pokrycie kosztów stałych równą 50 − 30 = 20 zł. Próg rentowności to 20 000 / 20 = 1 000 kubków miesięcznie: przy takiej sprzedaży firma nie ma ani zysku, ani straty. Przy sprzedaży 1 500 kubków marża wynosi 1 500 · 20 = 30 000 zł, a po odjęciu kosztów stałych zostaje 10 000 zł zysku. Obniżka ceny do 45 zł zmniejsza marżę jednostkową do 15 zł, więc próg rośnie do 20 000 / 15 ≈ 1 334 kubków. Przy 1 500 sztukach zysk spadłby do 1 500 · 15 − 20 000 = 2 500 zł. Żeby utrzymać zysk 10 000 zł, firma musiałaby sprzedać 30 000 / 15 = 2 000 kubków, czyli o jedną trzecią więcej. Obniżka opłaca się więc tylko wtedy, gdy realnie zwiększy sprzedaż co najmniej o tyle.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: eos, tokenów: 86

```text

Koszty zmienne (w tym marża) to cena sprzedaży, czyli cena za jeden kubek. Próg rentowności jest to cena sprzedaży, która pozwala na zwrot z inwestycji. Przy cenie 45 zł próg rentowności wynosi około 10% (czyli 20 000 zł / 1 500 = 10%). Przy cenie 50 zł próg rentowności wynosi około 10% (czyli 45 zł / 1 500 = 10%).
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 31

```text

Koszty stałe wynoszą 20 000 zł miesięcznie, koszt zmienny jednego kubka 30 zł, a cena sprzedaży 50 zł.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 179

```text

Zysk na sprzedaży 1 500 kubków: 1 500 x 10 zł = 15 000 zł.
Zysk na sprzedaży po obniżce: 1 500 x 5 zł = 7 500 zł.
Próg rentowności: 20 000 zł / 10 zł = 2 000 kubków.
Jeśli sprzeda się 1 500 kubków, będzie strata 5 000 zł.
Po obniżce ceny do 45 zł, próg rentowności wynosi 20 000 zł / 5 zł = 4 000 kubków. Przy sprzedaży 1 500 kubków nie będzie straty.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 201

```text

Próg rentowności to poziom sprzedaży, przy którym koszty stałe i zmienne zrównają się, a firma zacznie przynosić zyski. Przy sprzedaży 1 500 kubków koszty stałe wynoszą 20 000 zł, a koszty zmienne 450 000 zł (1 500 kubków x 30 zł). Zysk wyniesie 20 000 zł - 450 000 zł = -430 000 zł. Przy obniżeniu ceny do 45 zł koszty zmienne wynoszą 675 000 zł (1 500 kubków x 45 zł). Zysk wyniesie 20 000 zł - 675 000 zł = -655 000 zł. Firma nie osiągnie zysku przy sprzedaży 1 500 kubków ani po obniżce ceny.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: limit, tokenów: 400

```text


Próba wyczerpania
Zastosowanie:
Próba wyczerpania jest powszechnie stosowana podczas naukowej badań. Najczęściej polega na pomiarze objętości cieczy, co pozwala na określenie jej gęstości.

Gęstość cieczy
Gęstość to ilość masy cieczy na jednostkę objętości. Zazwyczaj wyrażana jest w kilogramach na litr (g/cm³), ale można również użyć jednostki g/cm³ lub kg/m³.

Przykład:
Ocena gęstości wody w klimacie słodkowodnym wynosi około 1000 kg/m³.

Rozmiar kubka
Obliczanie rozmiaru kubka jest stosunkowo proste. Dbajmy ostatecznie o 3 metry kątowe na bok i 1,2 metra na bok. Włączamy w to 1 metr na bok. Otrzymujemy kąt i boki, a następnie przekształcamy je w cały kubek.

Przykład:
1. Boki kubka: 1,2 m × 1,2 m
1. Kąt: 60°
Obliczamy powierzchnię kątową: 1,2 m × 60° = 72° m
Obliczamy powierzchnię boku: 1,2 m × 1,2 m = 1,44 m²
Obliczamy całkowitą powierzchnię: 72° m + 1,44 m² = 1,69 m²
Obliczamy objętość kubka: 
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 178

```text
 Próg rentowności to punkt, w którym przychodzenie zysku przekracza koszty produkcji. Przy sprzedaży 1 500 kubków przy cenie 50 zł każdy, przychodzenie zysku wynosi 1 500 × 50 – 20 000 = 70 000 zł. Przy obniżce ceny do 45 zł, przychodzenie zysku wynosi 1 500 × 45 – 20 000 = 62 500 zł. Oceń, że przy sprzedaży 1 500 kubków przy cenie 50 zł każdy, przychodzenie zysku przekroczy koszty produkcji, gdy przychodzenie zysku przekroczy 62 500 zł.
```

### tekst_techniczny-22 (otwarte, trudność 3)

**Polecenie:** Właściciel domu z instalacją fotowoltaiczną produkuje najwięcej prądu w południe, a najwięcej zużywa wieczorem. Przeanalizuj, kiedy opłaca mu się domowy magazyn energii, i wskaż czynniki, od których to zależy.

**Wzorzec:** Problem polega na rozjeździe w czasie: w południe instalacja produkuje nadwyżkę, która trafia do sieci, a wieczorem dom kupuje prąd z sieci. Magazyn energii ładuje się nadwyżką w dzień i oddaje ją wieczorem, zwiększając autokonsumpcję, czyli udział własnej energii zużytej na miejscu. Opłacalność zależy głównie od różnicy między ceną zakupu prądu z sieci a tym, ile właściciel dostaje za energię oddaną do sieci. Im większa ta różnica, tym więcej warta jest każda przechowana kilowatogodzina. Liczą się też koszt magazynu w przeliczeniu na kWh pojemności, jego trwałość wyrażona liczbą cykli oraz sprawność ładowania i rozładowania, bo część energii się traci. Pojemność powinna odpowiadać typowej wieczornej konsumpcji, a nie maksymalnej nadwyżce, bo niewykorzystana pojemność nie zarabia. Dodatkowym argumentem może być zasilanie awaryjne przy przerwach w dostawie prądu.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 86

```text

Prąd z instalacji fotowoltaicznej jest produkowany w ciągu dnia, kiedy słońce świeci wysoko, a instalacja fotowoltaiczna jest w stanie dostarczyć go do domu. W ciągu dnia produkcja energii jest wyższa, więc fotowoltaika pracuje na pełnych obrotach, a nadwyżki są magazynowane w akumulatorach. Kiedy słońce zachodzi, a instalacja fotowoltaiczna jest w stanie dostarczyć energię, instalacja przestaje pracować.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 37

```text

Zależy od tego, ile energii elektrycznej jest produkowane w ciągu dnia. Im więcej prądu, tym więcej energii elektrycznej jest produkowane w ciągu dnia.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 103

```text

Domowy magazyn energii jest opłacalny, gdy koszt zakupu energii z sieci przewyższa koszt magazynowania. Z obliczeń wynika, że przy cenie energii 100 zł/MWh (10 gr/k Wh) opłacalność wynosi około 4-5 godzin w ciągu doby. Magazynowanie jest też opłacalne w przypadku problemów z siecią, awarii, awarii akumulatora, wyłączenia, potrzeby prądu w domu o wysokim poborze (na przykład w czasie prac remontowych).
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 149

```text

Domowy magazyn energii jest opłacalny, gdy produkcja prądu w ciągu dnia jest większa niż zużycie w nocy. Wtedy nadwyżki można zmagazynować i wykorzystać w godzinach szczytu. Czynniki wpływające na opłacalność to:
1. Cena energii elektrycznej: Im wyższa, tym bardziej opłacalne jest magazynowanie.
2. Koszt instalacji magazynu: Im tańszy, tym bardziej opłacalne.
3. Koszt energii z magazynu: Im tańsza, tym bardziej opłacalne.
4. Czas zwrotu inwestycji: Im krótszy, tym bardziej opłacalne.
5. Regularność produkcji: Im bardziej regularna, tym bardziej opłacalne.
6. Koszty utrzymania magazynu: Im niższe, tym bardziej opłacalne.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 200

```text
 Podstawowym czynnikiem jest odległość między zbiornikiem a punktem poboru energii, np. domem. Gdy zbiornik znajduje się bliżej domu, do jego poboru energii zapotrzebowanie jest niższe, ponieważ łatwiej jest zaopatrywać go. Podobnie jak przy produkcji energii elektrycznej, wykorzystanie energii słonecznej jest najbardziej opłacalne w okresie, gdy słonecy są najbardziej intensywnie wytwarzający energię. Warto jednak weźmieć pod uwagę inne czynniki, np. efektywność energetyczną domu, koszty energii elektrycznej, cen energii słonecznej, koszt utrzymania instalacji fotowoltaicznej.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 311

```text


Właściciel domu z instalacją fotowoltaiczną produkuje najwięcej prądu w południe, ponieważ w tym czasie słońce jest najjaśniejsze. W południe fotowoltaiczne systemy generują więcej energii niż zużywają, ponieważ światło słoneczne jest najbardziej intensywne. W tym samym czasie dom jest najbardziej zapotrzebowany na energię elektryczną, ponieważ większość gospodarstw domowych jest w pełni wyposażonych w urządzenia elektryczne. W rezultacie domowy magazyn energii jest najbardziej efektywnie wykorzystywany w południe.

Właściciel domu z instalacją fotowoltaiczną produkuje najwięcej zużywa wieczorem, ponieważ w tym czasie zapotrzebowanie na energię elektryczną jest najniższe. W tym samym czasie dom jest najbardziej zapotrzebowany na energię elektryczną, ponieważ większość gospodarstw domowych jest w pełni wyposażonych w urządzenia elektryczne. W rezultacie domowy magazyn energii jest najbardziej nieefektywnie wykorzystywany w wieczorze.
```

### tekst_techniczny-23 (otwarte, trudność 3)

**Polecenie:** Sklep internetowy po kampanii reklamowej zaczął działać bardzo wolno: strony ładują się kilka sekund, a serwer bazy danych ma stale prawie 100% obciążenia procesora. Przeanalizuj prawdopodobne przyczyny i zaproponuj kolejność działań.

**Wzorzec:** Pełne obciążenie procesora bazy przy wolnych stronach wskazuje, że wąskim gardłem jest baza, a nie łącze czy serwer aplikacji. Najbardziej prawdopodobne przyczyny to zapytania bez odpowiednich indeksów, które przy większym ruchu przeglądają całe tabele, oraz problem N+1, czyli wiele małych zapytań wykonywanych dla każdej pozycji listy produktów. Pierwszym krokiem powinno być włączenie dziennika wolnych zapytań i sprawdzenie planów wykonania najczęstszych z nich. Szybką ulgę daje pamięć podręczna, na przykład w Redisie, dla danych rzadko zmienianych, takich jak strony kategorii i opisy produktów. Następnie warto dodać brakujące indeksy i połączyć powtarzane zapytania. Dopiero gdy zapytania są zoptymalizowane, ma sens skalowanie: mocniejszy serwer albo repliki do odczytu. Kupowanie większej maszyny na początku tylko odsuwa problem do kolejnej kampanii.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 72

```text

Przyczyny mogą być różne. Najprostsza to zbyt wolna prędkość internetu. Drugą przyczyną może być brak aktualizacji oprogramowania serwera bazy danych. Po trzecie, może to być problem z serwerem, który nie może obsłużyć dużego ruchu. W końcu może to być problem z dostawcą internetu, który ma ograniczoną przepustowość.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: limit, tokenów: 400

```text


1. W pierwszej kolejności należy sprawdzić, czy strona jest poprawnie skonfigurowana.
2. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
3. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
4. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
5. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
6. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
7. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
8. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
9. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
10. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
11. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
12. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
13. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
14. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
15. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
16. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
17. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
18. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
19. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
20. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
21. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
22. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
23. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
24. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
25. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
26. Następnie należy sprawdzić, czy strona jest poprawnie skonfigurowana.
27. Następnie należy sprawdzić,
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 40

```text

Przyczyna 1: Reklama spowodowała gwałtowny wzrost ruchu na stronie, przeciążając serwer.
Przyczyna 2: Serwer bazy danych ma problem z wydajnością.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 18

```text

Przyczyna: Serwer bazy danych jest przeciążony.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: limit, tokenów: 400

```text


1. Analiza danych:
Powód: Stale duży obciążenie procesora na serwerze bazy danych.

2. Zmiana programu:
Powód: Stalna zgłoszona przez bęben procesora kursora zapytał, czy zobaczył, że działał program reklamowy, który był odkryty w ostatniej kampanii reklamowej.

3. Zmiana ruchu:
Powód: Zamiast reklamowego programu, który był już z nami, program reklamowy został wyłączony, a zamiast go, napisano pożądany program, który został zainicjowany.

4. Zmiana programu:
Powód: Program reklamowy został zainicjowany przez program reklamowy.

5. Zmiana urządzenia:
Powód: Zamiast programu reklamowego, który był już z nami, program reklamowy został wyłączony, a zamiast go, napisano pożądany program, który został zainicjowany.

6. Zmiana urządzenia:
Powód: Program reklamowy został zainicjowany przez program reklamowy.

7. Zmiana strony:
Powód: Program reklamowy został zainicjowany przez program reklamowy.

8. Zmiana strony:
Powód: Program reklamowy został zainicjowany przez program reklamowy.

9. Zmiana strony:
Powód: Program reklamowy został zainicjowany przez program reklamowy.

10. Zmiana strony:
Powód: Program reklamowy został
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: limit, tokenów: 400

```text


1. Przeanalizuj, czy strony są zbyt duże. Jeśli tak, spróbuj zredukować ich rozmiar, na przykład poprzez usunięcie niepotrzebnych elementów graficznych lub optymalizację kodu.

2. Przeanalizuj, czy strony są zbyt duże. Jeśli tak, spróbuj zredukować ich rozmiar, na przykład poprzez usunięcie niepotrzebnych elementów graficznych lub optymalizację kodu.

3. Przeanalizuj, czy strony są zbyt duże. Jeśli tak, spróbuj zredukować ich rozmiar, na przykład poprzez usunięcie niepotrzebnych elementów graficznych lub optymalizację kodu.

4. Przeanalizuj, czy strony są zbyt duże. Jeśli tak, spróbuj zredukować ich rozmiar, na przykład poprzez usunięcie niepotrzebnych elementów graficznych lub optymalizację kodu.

5. Przeanalizuj, czy strony są zbyt duże. Jeśli tak, spróbuj zredukować ich rozmiar, na przykład poprzez usunięcie niepotrzebnych elementów graficznych lub optymalizację kodu.

6. Przeanalizuj, czy strony są zbyt duże. Jeśli tak, spróbuj zredukować ich rozmiar, na przykład poprzez usunięcie niepotrzebnych elementów graficznych lub optymalizację kodu.

7. Przeanalizuj, czy strony są zbyt
```

### tekst_techniczny-24 (otwarte, trudność 3)

**Polecenie:** Porównaj sprawność napędu elektrycznego i silnika spalinowego w samochodzie osobowym i wyjaśnij, skąd bierze się różnica.

**Wzorzec:** Sprawność to stosunek energii zamienionej na ruch do energii dostarczonej. Silnik spalinowy w samochodzie osiąga w typowej jeździe około 20–35%, a w najlepszym punkcie pracy około 40%. Większość energii paliwa zamienia się w ciepło odprowadzane przez spaliny i układ chłodzenia. Wynika to z natury silnika cieplnego: jego sprawność ograniczają prawa termodynamiki i straty przy częściowym obciążeniu, które w mieście jest normą. Dochodzą tarcie i praca na biegu jałowym. Silnik elektryczny zamienia energię elektryczną na mechaniczną bezpośrednio, przez oddziaływanie pól magnetycznych, i ma sprawność około 90–95%, wysoką w szerokim zakresie obrotów. Napęd elektryczny odzyskuje też część energii przy hamowaniu rekuperacyjnym. Uczciwe porównanie powinno jednak uwzględniać cały łańcuch: straty przy ładowaniu i w akumulatorze oraz sprawność wytwarzania prądu w elektrowni, która zmniejsza przewagę samochodu elektrycznego.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 82

```text

Silnik spalinowy jest zasilany paliwem, a silnik elektryczny z akumulatorem. Różnica polega na tym, że silnik spalinowy nie potrzebuje paliwa, a silnik elektryczny może pracować bez zasilania. Napęd elektryczny jest tańszy od spalinowego, ponieważ silnik elektryczny nie zużywa paliwa, a akumulator ładuje się samoczynnie, gdy bateria jest rozładowana.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 46

```text

Silnik spalinowy jest znacznie bardziej wydajny niż elektryczny, ponieważ ma mniejszą masę i jest bardziej elastyczny. Silnik elektryczny jest lżejszy i bardziej wydajny, ale ma mniejszą moc.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 91

```text

Elektryczny napęd samochodu osobowego jest znacznie bardziej efektywny niż silnik spalinowy, ponieważ energia elektryczna jest przetwarzana na energię mechaniczną bezpośrednio, bez pośrednictwa spalania paliwa. W silniku spalinowym energia elektryczna jest przekształcana w energię mechaniczną w wyniku spalania paliwa, co wiąże się z powstawaniem szkodliwych gazów i emisji hałasu. Różnica w sprawności wynika z różnicy w efektywności wykorzystania energii w obu napędach.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 73

```text

Silnik spalinowy jest bardziej wydajny niż silnik elektryczny, bo spalanie paliwa dostarcza energii mechanicznej, a nie elektrycznej. Silnik elektryczny potrzebuje baterii, które muszą być ładowane, a to oznacza straty energii. Ponadto silnik spalinowy ma większą moc i może osiągać wyższe prędkości, co jest ważne w przypadku samochodów osobowych.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 159

```text
 Sprawność napędu elektrycznego wynika z wyższej sprawności energetycznej. Elektryczny napęd przekształca 100% energii elektrycznej w energię ruchu, podczas gdy silnik spalinowy przekształca zaledwie 30-40% energii chemicznej w paliwa (praca elektryczna jest 100% więcej niż praca spalinowa). Ta różnica wynika z faktu, że silnik spalinowy uwalnia więcej paliwa, z którego można wydobyć energię, podczas gdy energia elektryczna jest wytwarzana bez uwolnienia paliwa.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 110

```text
 Sprawność napędu elektrycznego to stosunek mocy wyjściowej do mocy wejściowej. Sprawność napędu silnika spalinowego to stosunek mocy wyjściowej do mocy wejściowej. Sprawność napędu elektrycznego jest wyższa, ponieważ napęd elektryczny nie traci energii w postaci ciepła, jak w przypadku silnika spalinowego.
```

### tekst_techniczny-25 (otwarte, trudność 3)

**Polecenie:** Wyjaśnij, jak powstaje oporność bakterii na antybiotyki i dlaczego nie należy stosować antybiotyków przy przeziębieniu wywołanym przez wirusy.

**Wzorzec:** W dużej populacji bakterii zdarzają się mutacje, a część bakterii może też przejąć od innych geny oporności, na przykład na plazmidach. Antybiotyk zabija lub hamuje wzrost bakterii wrażliwych, a nieliczne oporne przeżywają i mnożą się dalej. To dobór naturalny: po kolejnych kontaktach z lekiem w populacji przeważają szczepy, na które antybiotyk przestaje działać. Proces przyspieszają nadużywanie antybiotyków, przerywanie kuracji przed czasem i stosowanie ich w hodowli zwierząt. Antybiotyki działają na struktury i procesy typowe dla bakterii, takie jak ściana komórkowa czy bakteryjne rybosomy. Wirusy ich nie mają, bo namnażają się wewnątrz komórek gospodarza, więc antybiotyk nie skraca przeziębienia. Przyjęty bez potrzeby naraża za to na działania niepożądane i wywiera presję selekcyjną na bakterie żyjące w organizmie, sprzyjając oporności.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 97

```text

Bakterie rozmnażają się, wykorzystując do tego energię. Mogą to robić w różny sposób, na przykład wytwarzając ATP z węgla i tlenu. Przeprowadzają też reakcje zwane fotosyntezą. Na przykład wytwarzają ATP z dwutlenku węgla i wody, która zostaje pochłonięta przez liście. W rezultacie bakterie uzyskują energię, która w naturalny sposób niszczy wirusy. Wirusy nie mogą zostać zniszczone przez antybiotyki.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 44

```text

Bakterie są bardzo wrażliwe na antybiotyki, ponieważ ich DNA jest bardzo podobne do DNA człowieka. Wirusy nie mają takiego DNA, więc nie mogą się nimi zarazić.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 83

```text

Bakterie rozwijają oporność na antybiotyki poprzez mutacje genetyczne. Antybiotyki nie zabijają bakterii, tylko ich komórki, które są wrażliwe na leki. Antybiotyki nie działają na wirusy, które nie mają ściany komórkowej, nie mogą się więc na nią nachodzić. Dlatego antybiotyki nie mogą być stosowane przy przeziębieniu wywołanym przez wirusy.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 118

```text

Oporność bakterii na antybiotyki powstaje na skutek mutacji genetycznych, które zmieniają sposób działania antybiotyków. Antybiotyki działają na bakterie poprzez blokowanie enzymów, które są niezbędne do ich wzrostu i rozmnażania. Jeśli bakterie mutują i zmieniają sposób działania tych enzymów, antybiotyki przestają być skuteczne. Nie należy stosować antybiotyków przy przeziębieniu wywołanym przez wirusy, ponieważ antybiotyki nie działają na wirusy. Stosowanie antybiotyków w takich przypadkach może prowadzić do rozwoju oporności bakterii na antybiotyki i zmniejszenia skuteczności leczenia w przyszłości.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 188

```text
 Oporność bakterii na antybiotyki powstaje, gdy w organizmie ludzkim bakterie wytwarzają enzymy, które rozkładają antybiotyki. Proces ten zwalnia antybiotyki, pozwalając bakteriom na rozmnażanie się i przeżywanie. Zmniejszając antybiotyki w organizmie ludzkim, antybiotyki pozostają skuteczne i są w stanie zabić bakterie. Jednak niektóre bakterie ewoluują i rozwijają oporność na antybiotyki, gdy antybiotyki są stosowane. Zmniejszając antybiotyki w organizmie ludzkim, antybiotyki pozostają skuteczne i są w stanie zabić bakterie.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: limit, tokenów: 400

```text


Oporność bakterii na antybiotyki powstaje, gdy bakterie rozwijają mechanizmy odporności na antybiotyki. Najczęściej jest to mutacja genetyczna, która pozwala im uniknąć działania antybiotyków.

Antybiotyki działają, gdy wchodzą do komórek bakterii i zabijają je. Jednak niektóre bakterie rozwijają mechanizmy odporności na antybiotyki, które pozwalają im uniknąć działania antybiotyków.

Mechanizmy odporności na antybiotyki mogą być:

1. Bakterie rozwijają mechanizmy odporności na antybiotyki, które pozwalają im uniknąć działania antybiotyków.

2. Bakterie rozwijają mechanizmy odporności na antybiotyki, które pozwalają im uniknąć działania antybiotyków.

3. Bakterie rozwijają mechanizmy odporności na antybiotyki, które pozwalają im uniknąć działania antybiotyków.

4. Bakterie rozwijają mechanizmy odporności na antybiotyki, które pozwalają im uniknąć działania antybiotyków.

5. Bakterie rozwijają mechanizmy odporności na antybiotyki, które pozwalają im uniknąć działania antybiotyków.

6. Bakterie rozwijają mechanizmy odporności na antybiotyki, które pozwalają im uniknąć działania antybiotyków.

7. Bakterie rozwijają mechanizmy odporności na anty
```

### tekst_techniczny-26 (otwarte, trudność 3)

**Polecenie:** Bank centralny podnosi stopy procentowe. Przeanalizuj, jak wpływa to na raty kredytów o zmiennym oprocentowaniu, oprocentowanie lokat i inflację.

**Wzorzec:** Podwyżka stóp procentowych banku centralnego podnosi koszt pieniądza w całej gospodarce. Banki z opóźnieniem przenoszą ją na swoje produkty. Kredyty o zmiennym oprocentowaniu są zwykle powiązane ze wskaźnikiem rynkowym, który rośnie razem ze stopami, więc rata kredytu hipotecznego idzie w górę, często już przy najbliższej aktualizacji oprocentowania. Rośnie też oprocentowanie nowych lokat i obligacji, co zachęca do oszczędzania zamiast wydawania. Droższy kredyt zniechęca firmy do inwestycji, a gospodarstwa domowe do zakupów na raty. Spada popyt, co z czasem hamuje wzrost cen, czyli obniża inflację. Działa to z opóźnieniem, zwykle liczonym w kwartałach, a nie w tygodniach. Kosztem tej polityki jest wolniejszy wzrost gospodarczy i większe obciążenie zadłużonych. Wyższe stopy mogą też umacniać krajową walutę, co obniża ceny importu i dodatkowo ogranicza inflację.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 80

```text

Wraz ze wzrostem stóp procentowych rośnie koszt kredytów. Wzrost oprocentowania to nic innego jak wzrost kosztów pożyczek. Wzrost stóp procentowych oznacza, że banki mają mniejsze zyski, a co za tym idzie, mniej pieniędzy mogą pożyczyć. Raty kredytów o zmiennym oprocentowaniu rosną, bo oprocentowanie rośnie, a co za tym idzie, bank nalicza odsetki.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 74

```text

Stopy procentowe to ceny, po których banki pożyczają sobie pieniądze. W Polsce są to stopy procentowe ustalane przez Radę Polityki Pieniężnej. Wpływ na nie ma inflacja, czyli wzrost cen. Wpływ na stopy procentowe ma też polityka monetarna, czyli decyzje Rady Polityki Pieniężnej.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 70

```text

Kiedy bank centralny podnosi stopy procentowe, stopa procentowa kredytów o zmiennym oprocentowaniu rośnie, co oznacza wyższe raty. Stopa procentowa lokat spada, więc ich oprocentowanie spada. W rezultacie wzrasta koszt kredytu i zmniejsza się zysk z lokaty. Inflacja rośnie, bo banki centralne podnoszą stopy procentowe, aby ograniczyć wzrost cen.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 77

```text

Jeśli stopy procentowe rosną, to banki muszą płacić więcej za pożyczanie pieniędzy, co oznacza, że kredyty o zmiennym oprocentowaniu będą droższe. Z drugiej strony, banki mogą pobierać wyższe odsetki od lokat, co może zachęcić ludzi do oszczędzania. Wzrost stóp procentowych może również wpłynąć na inflację, ponieważ banki centralne mogą chcieć kontrolować wzrost cen poprzez podnoszenie stóp procentowych.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 199

```text


Bank centralny podnosi stopy procentowe w celu zwiększenia wartości pieniądza w gospodarce. Gdy bank centralny podnosi stopy procentowe, oznacza to, że pożycząc pieniądze banki nabywają mniej pieniędzy od użytkowników. Z kolei wartość pieniądza spada, ponieważ pożyczone pieniądze bankowe są mniej wymagane przez użytkowników, więc banki nabywają mniej pieniędzy. Oznacza to, że ludzie nabywali mniej pieniędzy od banków, a banki nie nabywali mniej pieniędzy od użytkowników, więc wartość pieniądza w gospodarce spada.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 122

```text
 Bank centralny podnosi stopy procentowe, aby zmniejszyć ilość pieniędzy w obiegu, co powoduje spowolnienie wzrostu gospodarczego i ograniczenie inflacji. Podniesienie stopy procentowej oznacza, że kredyty stają się droższe, co zmniejsza popyt na kredyty i ogranicza wydatki konsumentów. W rezultacie ceny spadają, a inflacja maleje.
```

### tekst_techniczny-27 (otwarte, trudność 3)

**Polecenie:** Wyjaśnij, czym jest kogeneracja i dlaczego elektrociepłownia wykorzystuje paliwo lepiej niż osobno działające elektrownia i kotłownia.

**Wzorzec:** Kogeneracja to jednoczesne wytwarzanie energii elektrycznej i ciepła w jednym procesie. W zwykłej elektrowni cieplnej tylko około 35–45% energii paliwa zamienia się w prąd, a resztę stanowi głównie ciepło odprowadzane do otoczenia przez chłodnie kominowe albo wodę z rzeki. Elektrociepłownia nie wyrzuca tego ciepła, tylko kieruje je do sieci ciepłowniczej, która ogrzewa budynki i podgrzewa wodę. Dzięki temu łączna sprawność wykorzystania paliwa może sięgać 80–90%. Przy osobnym wytwarzaniu potrzebna byłaby elektrownia tracąca ciepło i dodatkowa kotłownia spalająca paliwo tylko na ogrzewanie, czyli więcej paliwa na te same ilości prądu i ciepła. Ograniczeniem jest to, że zapotrzebowanie na ciepło zależy od pory roku. Latem elektrociepłownia ma mało odbiorców ciepła, więc albo pracuje z mniejszą mocą, albo traci przewagę.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 66

```text

Kogeneracja to skojarzone wytwarzanie energii elektrycznej i ciepła, przy czym energia elektryczna wytwarzana jest z paliw gazowych, a ciepło z paliw ciekłych. Kogeneracja polega na jednoczesnym wytwarzaniu energii elektrycznej i ciepła przy wykorzystaniu tej samej ilości energii pierwotnej.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 88

```text

Kogeneracja to połączenie dwóch lub więcej źródeł energii w jeden system. W elektrociepłowni ciepło jest wytwarzane w kotle, a energia elektryczna w generatorze. W kogeneracji ciepło jest wytwarzane w jednym urządzeniu, a energia elektryczna w drugim. W elektrociepłowni ciepło jest wytwarzane w kotle, a energia elektryczna w generatorze.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 70

```text

Kogeneracja to jednoczesne wytwarzanie energii elektrycznej i ciepła. Dzięki temu wykorzystuje się paliwo lepiej niż osobno działające elektrownia i kotłownia, bo w kogeneracji ciepło jest wykorzystywane w instalacji, w której zachodzi proces spalania. To pozwala na mniejsze straty energii, efektywniejsze wykorzystanie paliwa i mniejsze emisje szkodliwych substancji.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 67

```text

Kogeneracja to jednoczesne wytwarzanie energii elektrycznej i ciepła w jednej instalacji. Elektrociepłownia wykorzystuje paliwo lepiej niż osobno działające elektrownia i kotłownia, ponieważ wykorzystuje ciepło odpadowe z procesu spalania do produkcji ciepła. Dzięki temu zmniejsza się emisja szkodliwych substancji do atmosfery i oszczędza energię.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 221

```text
 Kogeneracja to proces, w którym wytwarzany jest jednocześnie ciepło i energia elektryczna. W elektrociepłowniach paliwo jest uwalniane w postaci ciepła, a następnie przekształcane w energię elektryczną za pomocą turbiny elektrycznej. W kogeneratorze natomiast paliwo jest wykorzystywane do wytwarzania ciepła i energii elektrycznej w jednym procesie, co zwiększa efektywność energetyczną. Elektrociepłownia wykorzystuje paliwo lepiej niż osobno działające elektrownia i kotłownia, ponieważ ciepło jest przekształcane w energię elektryczną i ciepło, a następnie ponownie przekształcane w energię elektryczną, a nie tylko w jeden z nich.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 205

```text
 Kogeneracja to technologia, która pozwala na jednoczesne wytwarzanie energii elektrycznej i ciepła z jednego źródła paliwa. Elektrociepłownia to urządzenie, które wytwarza ciepło poprzez spalanie paliwa, takiego jak gaz ziemny, węgiel czy ropa naftowa. W przeciwieństwie do tradycyjnych elektrowni, które wytwarzają energię elektryczną i ciepło oddzielnie, kogeneracja wykorzystuje ciepło z procesu wytwarzania energii elektrycznej do podgrzewania budynku. Dzięki temu kogeneracja jest bardziej efektywna, ponieważ wykorzystuje ciepło, które w przeciwnym razie byłoby tracone.
```

### tekst_techniczny-28 (otwarte, trudność 3)

**Polecenie:** Porównaj szyfrowanie symetryczne i asymetryczne i wyjaśnij, jak protokół TLS (używany w HTTPS) łączy oba rodzaje.

**Wzorzec:** W szyfrowaniu symetrycznym ten sam klucz służy do szyfrowania i odszyfrowania, jak w algorytmie AES. Jest bardzo szybkie, ale obie strony muszą najpierw bezpiecznie poznać wspólny klucz, a przesłanie go otwartym kanałem byłoby ryzykowne. W szyfrowaniu asymetrycznym każda strona ma parę kluczy: publiczny, który można rozdać wszystkim, i prywatny, trzymany w tajemnicy. To, co zaszyfrowano kluczem publicznym, odszyfruje tylko właściciel klucza prywatnego. Rozwiązuje to problem wymiany kluczy i pozwala tworzyć podpisy cyfrowe, ale jest znacznie wolniejsze. TLS korzysta z obu. Na początku połączenia serwer przedstawia certyfikat z kluczem publicznym, potwierdzony podpisem urzędu certyfikacji, a strony za pomocą kryptografii asymetrycznej, najczęściej wymiany kluczy Diffiego-Hellmana, uzgadniają wspólny klucz sesji. Dalsze dane szyfrowane są już szybko, symetrycznie.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 103

```text

Szyfrowanie symetryczne to rodzaj szyfrowania, w którym wszystkie dane przesyłane między serwerem a klientem są szyfrowane przy użyciu tej samej metody, która jest używana przez wszystkie serwery. Klient używa tej samej metody do szyfrowania i deszyfrowania danych, co jest często nazywane szyfrowaniem asymetrycznym. Szyfrowanie symetryczne jest często używane do zabezpieczania danych wrażliwych, takich jak dane finansowe lub informacje poufne.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 58

```text

Szyfrowanie symetryczne polega na tym, że wszystkie dane przesyłane między serwerem a klientem są szyfrowane w taki sam sposób. Oznacza to, że wszystkie dane są szyfrowane w taki sam sposób, a ich odczytanie jest niemożliwe.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 124

```text

Symetryczne szyfrowanie wykorzystuje tę samą parę kluczy (klucz szyfrujący i klucz deszyfrujący) do zaszyfrowania i odszyfrowania danych. Szyfrowanie asymetryczne wymaga dwóch różnych kluczy: publicznego i prywatnego. Publiczny jest używany do szyfrowania danych, a prywatny do ich dekodowania. Protokół TLS wykorzystuje obie metody. Połączenie HTTPS łączy symetryczne szyfrowanie z asymetrycznym, gdyż szyfrowanie asymetryczne jest szybsze i bezpieczniejsze, a symetryczne zapewnia szybkość.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 114

```text

Symetryczne szyfrowanie wykorzystuje ten sam klucz do szyfrowania i deszyfrowania danych. Szyfrowanie asymetryczne wykorzystuje dwa klucze: publiczny i prywatny. Klucz publiczny jest udostępniany innym, a prywatny jest znany tylko nadawcy i odbiorcy. Protokół TLS (Transport Layer Security) łączy szyfrowanie asymetryczne z symetrycznym, używając klucza publicznego do uwierzytelniania i szyfrowania danych. Klucz prywatny jest używany tylko do deszyfrowania danych, co zapewnia bezpieczeństwo.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 171

```text
 Protokół TLS (Transport Layer Security) to standardowy mechanizm szyfrowania, który zapewnia bezpieczne komunikację w sieci, szczególnie internetowej. Zapewnia on prywatność danych i ich bezpieczeństwo. Protokół TLS łączy oba rodzaje szyfrowania symetryczne i asymetryczne. Szyfrowanie symetryczne jest szybsze, ale nie bezpieczne, ponieważ klucze są udostępnione w transmisji. Szyfrowanie asymetryczne jest wolniejsze, ale bezpieczne, ponieważ klucze są generowane i wymieniane w sposób bezpieczny.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 129

```text
 Szyfrowanie symetryczne to metoda, w której klucz szyfrujący jest używany do szyfrowania danych. Klucz jest wiadomością, która jest szyfrowana za pomocą klucza szyfrującego, aby zostać odczytana tylko przez osobę posiadającą klucz dekodujący. Protokół TLS wykorzystuje szyfrowanie symetryczne do szyfrowania danych między klientem a serwerem.
```

### tekst_techniczny-29 (otwarte, trudność 3)

**Polecenie:** Do przedłużacza oznaczonego na 16 A podłączono jednocześnie czajnik 2 000 W i grzejnik olejowy 2 000 W, a przewód zaczął się wyraźnie nagrzewać. Przeanalizuj sytuację przy napięciu 230 V i zaproponuj bezpieczne rozwiązanie.

**Wzorzec:** Łączna moc odbiorników wynosi 4 000 W. Przy napięciu 230 V płynie więc prąd I = P / U = 4 000 / 230 ≈ 17,4 A, czyli więcej niż dopuszczalne 16 A dla przedłużacza. Moc wydzielana w przewodach jako ciepło rośnie z kwadratem natężenia, więc nawet niewielkie przekroczenie powoduje wyraźne nagrzewanie, zwłaszcza gdy przewód jest zwinięty na bębnie i nie oddaje ciepła. Grozi to stopieniem izolacji, zwarciem i pożarem. Wyłącznik nadprądowy w domowej instalacji może przez dłuższy czas nie zadziałać przy prądzie tylko trochę wyższym od nominalnego. Rozwiązaniem jest natychmiastowe odłączenie jednego urządzenia i podłączanie odbiorników dużej mocy bezpośrednio do osobnych gniazdek, najlepiej w różnych obwodach. Przedłużacz bębnowy należy zawsze całkowicie rozwijać, a do stałego zasilania grzejnika nie używać przedłużacza wcale.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 70

```text

Przy napięciu 230 V, czyli przy przekroczeniu napięcia progowego, do obwodu elektrycznego przyłączonego do przedłużacza dochodzą prądy o natężeniu 50 A. Przy napięciu 230 V prąd ten jest ograniczony do wartości ok. 3 A, więc nie jest niebezpieczny dla podłączonego sprzętu.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 22

```text

W tym przypadku bezpiecznym rozwiązaniem jest zastosowanie bezpieczników topikowych.
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 127

```text

Napięcie w sieci jest takie samo, więc oba urządzenia pobierają tyle samo prądu. Czajnik pobiera około 1200 W, a grzejnik 1200 W, więc razem 2400 W. Przewód ma 16 A, a 2400 W to 150 A. Oznacza to, że przewód jest przeciążony. Bezpieczne rozwiązanie to wyłączenie czajnika i grzejnika, albo zastosowanie bezpiecznika lub wyłącznika różnicowoprądowego (RCD), który wykryje przeciążenie i odłączy prąd.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 117

```text

Przedłużacz jest przeciążony, bo czajnik i grzejnik pobierają więcej prądu niż wynosi jego moc znamionowa. Przedłużacz nie jest przystosowany do tak dużego obciążenia, więc zaczyna się nagrzewać. Aby rozwiązać problem, należy odłączyć urządzenia od przedłużacza i podłączyć je do gniazdka bezpośrednio, np. do gniazdka w kuchni. Można też kupić przedłużacz o większej mocy, np. 32 A, lub użyć innego urządzenia, które nie pobiera tyle prądu, na przykład suszarki do włosów.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 143

```text


Napięcie zaczął się wyraźnie nagrzewać, ponieważ przewód jest połączony z mocowaniem, a następnie z grzejnikiem olejowym. Olej jest dodatkowym źródłem ciepła, co powoduje wzrost temperatury przewodu. Jednak przewód jest podgrzewany przez stałe rozprężenie gazów wypełniających. W przypadku przyłączenia z mocowaniem do mocy, przewód jest podgrzewany przez ciepło przyłożonego przez mocowanie.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: limit, tokenów: 400

```text
 Przeanalizujmy sytuację przy napięciu 230 V. Przez przewód zaczął się wyraźnie nagrzewać, co oznacza, że przewód jest podgrzewany. Przeanalizujmy, dlaczego przewód zaczyna się nagrzewać. Przewód jest podgrzewany przez napięcie elektryczne, które przepływa przez niego. Napięcie elektryczne to siła, która powoduje przepływ ładunków elektrycznych. Napięcie elektryczne jest zjawiskiem, które występuje, gdy dwa różne materiały są połączone w sposób, który pozwala przepływowi ładunków elektrycznych. Napięcie elektryczne jest siłą, która powoduje przepływ ładunków elektrycznych. Napięcie elektryczne jest zjawiskiem, które występuje, gdy dwa różne materiały są połączone w sposób, który pozwala przepływowi ładunków elektrycznych. Napięcie elektryczne jest siłą, która powoduje przepływ ładunków elektrycznych. Napięcie elektryczne jest zjawiskiem, które występuje, gdy dwa różne materiały są połączone w sposób, który pozwala przepływowi ładunków elektrycznych. Napięcie elektryczne jest siłą, która powoduje przepływ ładunków elektrycznych. Napięcie elektryczne jest zjawiskiem, które występuje, gdy dwa różne materiały są połączone w sposób, który pozwala przepływowi ładunków elektrycznych. Napięcie elektryczne jest siłą, która powoduje przepływ ładunk
```

### tekst_techniczny-30 (otwarte, trudność 3)

**Polecenie:** Wyjaśnij, dlaczego woda w wysokich górach wrze w niższej temperaturze niż nad morzem i jak to wpływa na gotowanie. Opisz też, jak działa szybkowar.

**Wzorzec:** Woda wrze, gdy ciśnienie jej pary zrówna się z ciśnieniem otoczenia. Ciśnienie atmosferyczne maleje z wysokością, więc w górach ten warunek jest spełniony w niższej temperaturze. Nad morzem, przy ciśnieniu około 1013 hPa, woda wrze w około 100 °C, a na wysokości około 3 000 m n.p.m. już w około 90 °C. Dalsze podgrzewanie nie podnosi temperatury wrzącej wody, tylko przyspiesza parowanie. Dlatego w górach gotowanie makaronu, ziemniaków czy jajek trwa dłużej: procesy w żywności, takie jak ścinanie białka i mięknięcie skrobi, zależą od temperatury, a nie od samego bulgotania. Szybkowar działa odwrotnie. Szczelna pokrywa zatrzymuje parę, ciśnienie w garnku rośnie o mniej więcej jedną atmosferę ponad ciśnienie otoczenia, a woda wrze wtedy w około 120 °C. Wyższa temperatura skraca czas gotowania, a zawór bezpieczeństwa chroni przed zbyt dużym ciśnieniem.

**Slayer 1.08, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 74

```text

Woda wrze w wysokich górach, bo ma wyższą temperaturę w troposferze niż w głębinach oceanu. Na przykład na Alasce woda wrze w temperaturze około 100°C, czyli około 3 razy wyższej niż w Polsce. W czasie tego procesu woda przechodzi z fazy ciekłej w stan pary, a następnie w stan stały.
```

**Slayer 1.08, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: limit, tokenów: 400

```text

Woda wrze w wysokich górach, ponieważ jest tam chłodniej niż nad morzem. Woda w morzu wrze w temperaturze około 100°C, a w wysokich górach jest cieplejsza. W wysokich górach woda wrze w temperaturze około 100°C, a w morzu w temperaturze około 4°C. W wysokich górach woda wrze w temperaturze około 100°C, a w morzu w temperaturze około 4°C. W wysokich górach woda wrze w temperaturze około 100°C, a w morzu w temperaturze około 4°C. W wysokich górach woda wrze w temperaturze około 100°C, a w morzu w temperaturze około 4°C. W wysokich górach woda wrze w temperaturze około 100°C, a w morzu w temperaturze około 4°C. W wysokich górach woda wrze w temperaturze około 100°C, a w morzu w temperaturze około 4°C. W wysokich górach woda wrze w temperaturze około 100°C, a w morzu w temperaturze około 4°C. W wysokich górach woda wrze w temperaturze około 100°C, a w morzu w temperaturze około 4°C. W wysokich górach woda wrze w temperaturze około 100°C, a w morzu w temperaturze około 4°C. W wysokich górach woda wrze w temperaturze około 100°C, a w morzu w temperaturze około 4°C. W wysokich górach woda wrze w temperaturze około 100°C, a w morzu w temperaturze około 4°C. W wysokich górach woda wrze w temperaturze około 100°C, a w morzu w temperaturze około 4°C. W wysokich górach woda wrze w temperaturze około 100°C, a w morzu w temperaturze około 4°C. W wysokich górach woda wrze w temperaturze około 100°C, a w morzu w temperaturze około 4°C. W wysokich górach woda wrze w temperaturze około 100°C, a w morzu w temperaturze około 4°C. W wysokich górach woda wrze w temperaturze około 100°C, a w m
```

**Bielik 1.5B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 102

```text

Woda wrze w temperaturze 100°C w warunkach normalnych, ale w wysokich górach, gdzie ciśnienie jest niższe, to samo ciało stałe zmienia stan skupienia w stan ciekły w niższej temperaturze. Dlatego w górach woda wrze w niższej temperaturze niż nad morzem, co wpływa na czas gotowania potraw. Szybkowar to urządzenie do gotowania próżniowego, które utrzymuje wysoką temperaturę potrawy bez otwierania pokrywki, dzięki czemu woda wrze szybciej i bardziej efektywnie.
```

**Bielik 1.5B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 101

```text

Woda wrze w wyższych górach, bo ciśnienie atmosferyczne jest niższe, a więc ciśnienie parcjalne tlenu i wodoru jest mniejsze. W wyższych górach ciśnienie parcjalne tlenu i wodoru jest mniejsze, więc temperatura wrzenia wody jest niższa. Gotowanie w szybkowarze polega na tym, że ciśnienie wewnątrz naczynia jest wyższe niż na zewnątrz, co powoduje, że woda wrze w niższej temperaturze niż w normalnych warunkach. Dzięki temu potrawy gotuje się szybciej i oszczędza energię.
```

**LFM2.5 1.2B, seed 1** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 141

```text
 Wysokie góry mają niską temperaturę. Gdy woda w nich wrze, jej temperatura spada do temperatury topnienia, a nie do temperatury wrzenia, co daje niższe ciepło. Dlatego potrawy gotowane w lodowych górach rozpuściły się szybciej i gotowały szybciej. Szybkowary wykorzystują mniej energii i wytwarzają mniej dwutlenku węgla, co ułatwia transport na górę i zmniejsza ryzyko pożaru.
```

**LFM2.5 1.2B, greedy** — ocena: bez oceny automatycznej (polecenie otwarte); koniec: stop, tokenów: 103

```text
 Wysokie góry mają niższe temperatury, ponieważ powietrze w nich jest chłodniejsze. Woda wrze w niższej temperaturze, ponieważ jej punkt wrzenia jest niższy niż temperatura otoczenia. Szybkowar działa, ponieważ wytwarza gorący powietrze, które podgrzewa wodę i przyspiesza proces wrzenia.
```
