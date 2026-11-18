# Instrukcja dla sędziego: ślepa ocena parami

Oceniasz pary odpowiedzi dwóch anonimowych modeli językowych na to samo polecenie. Modele to małe modele BAZOWE
(nie czatowe), które dopisywały odpowiedź po kilku przykładach. Nie wiesz, które modele to są, i nie próbujesz tego
ustalić. Pracujesz wyłącznie na plikach z tego katalogu; nie otwierasz innych plików ani repozytoriów.

## Wejście

`pary.jsonl`: jedna para na linię, pola `para_id`, `polecenie`, `kryteria` (lista), `odpowiedz_A`, `odpowiedz_B`.
Odpowiedź mogła zostać ucięta na limicie długości; oceniasz ją taką, jaka jest.

## Jak oceniasz

Dla każdej pary wybierasz lepszą odpowiedź według, w tej kolejności:

1. Spełnienie `kryteriów` polecenia i poprawność merytoryczna (błąd faktu waży więcej niż styl).
2. Wykonanie polecenia (temat, forma, język polecenia: polski albo angielski).
3. Jakość języka: poprawność gramatyczna, ortografia, spójność.
4. Użyteczność: brak zapętleń i powtórzeń, brak treści niezwiązanych z poleceniem (np. doklejone kolejne zadania,
   znaczniki techniczne), odpowiedź doprowadzona do końca.

Długość sama w sobie nie jest zaletą. Strona (A czy B) i kolejność par nie mają znaczenia — są losowe.

**Remis** wybierasz tylko wtedy, gdy po przejściu wszystkich czterech punktów nie potrafisz wskazać lepszej
odpowiedzi (np. obie są równie bezużyteczne albo równie dobre). Nie używasz remisu, by uniknąć decyzji.

## Wyjście

Plik `oceny_<twoj_identyfikator>.jsonl` (identyfikator poda zlecający), jedna linia na KAŻDĄ parę z `pary.jsonl`:

```
{"para_id": "P001", "werdykt": "A", "uzasadnienie": "jedno zdanie: główny powód"}
```

`werdykt` to dokładnie `"A"`, `"B"` albo `"remis"`. Oceniasz wszystkie pary, każdą niezależnie, bez wracania do
wcześniejszych decyzji na podstawie późniejszych. Nie konsultujesz ocen z innym sędzią.
