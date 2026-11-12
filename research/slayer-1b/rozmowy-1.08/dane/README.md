# Zestaw poleceń „rozmowy 1.08”: TYLKO DO OCENY

- `polecenia.jsonl`: 240 poleceń (8 kategorii po 30) z odpowiedziami wzorcowymi, listami form dopuszczalnych,
  testami kodu i kryteriami oceny. `shoty.jsonl`: 24 przykłady few-shot (3 na kategorię).
- `SPEC.md`: specyfikacja, według której zestaw napisano. `INSTRUKCJA_SEDZIEGO.md`: instrukcja ślepej oceny parami.
- **Autor:** model Claude (Anthropic), 12.11.2026, od zera, bez kopiowania publicznych benchmarków (skan n-gramów:
  `../wyniki/skazenie.json`).
- **Zakaz treningu.** Zestawu, jego wzorców ani tekstów w tym stylu nie używa się do treningu ani douczania żadnego
  modelu: to treść wygenerowana przez Claude (warunki Anthropic) i materiał testowy (METODOLOGIA, „Czystość
  benchmarku”). Kto składa dane treningowe, usuwa z nich teksty pokrywające się z tym zestawem.
- sha256 plików: `../PROTOKOL.md`, sekcja 2.
