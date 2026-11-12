# Instrukcja: niezależna kontrola wzorców (20 pozycji)

Sprawdzasz, czy odpowiedzi wzorcowe w zestawie testowym są poprawne i czy reguły oceny są uczciwe. Nie oceniasz
żadnego modelu i nie otwierasz wyników modeli ani innych plików badania poza tym katalogiem i `SPEC.md` obok.

Wejście: `kontrola_wzorcow.jsonl`, jedna pozycja na linię (pola jak w `SPEC.md`). Ocena automatyczna w badaniu:
- `krotka`: pierwsza linia odpowiedzi po normalizacji (małe litery, interpunkcja zamieniona na spację) musi zawierać
  jako całą frazę któryś napis z `akceptowane` i nie może zawierać żadnego z `zakazane`;
- `zdanie`: pierwsza linia po normalizacji musi być równa któremuś napisowi z `akceptowane`;
- `liczba`: liczba po „Wynik:” (albo ostatnia liczba) równa `liczba` z tolerancją 0,005;
- `kod`: kod z odpowiedzi + `testy` muszą przejść.

Dla każdej pozycji ustal SAMODZIELNIE (rozwiąż zadanie, sprawdź fakt w swojej wiedzy, uruchom kod i testy w
python3, policz rachunek), a potem porównaj ze wzorcem:

1. `wzorzec`: `poprawny` / `bledny` / `niejednoznaczny` (pytanie ma więcej niż jedną obronialną odpowiedź albo fakt
   jest sporny lub nieaktualny).
2. `ryzyko_oceny`: czy reguła oceny może ODRZUCIĆ poprawną odpowiedź (brak częstej poprawnej formy w `akceptowane`,
   napis z `zakazane` występujący w poprawnej odpowiedzi, testy wymagające zachowania, którego polecenie nie
   opisuje) albo PRZYJĄĆ błędną. Wartości: `brak` / `odrzuca_poprawne` / `przyjmuje_bledne` / `oba`, z przykładem.

Wyjście: `kontrola_wzorcow_oceny.jsonl`, jedna linia na pozycję:

```
{"id": "...", "wzorzec": "poprawny", "ryzyko_oceny": "brak", "uzasadnienie": "1-2 zdania, przy błędzie poprawna odpowiedź"}
```

Na koniec jedno zdanie: ile pozycji `bledny` i `niejednoznaczny`.
