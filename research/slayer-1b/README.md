# Slayer 1B: wyniki testów (30.10.2026)

Slayer 1.06 wypada losowo w testach z literami A/B/C/D, bo za często wybiera „A” (83–94% odpowiedzi w testach angielskich, 63% w polskim Belebele), podobnie jak Pythia-1B, więc to cecha skali ~1B, nie brak wiedzy. Liczony po treści odpowiedzi model się uczy (ARC-C acc_norm 0,2176 → 0,2577 od 1.00 do 1.06), a wygaszanie LR obniża loss o 0,047 nat bez zmiany trafności.

**Wykresy i tabele:** https://claude.ai/artifact/A25Hg6FfP9ZaXrRpUdzqaa

## Co dalej

- Zadania dla chętnych (A1–A7 bez GPU, B1–B4 z GPU): [`lab/DLA_ARKA_I_CHETNYCH.md`](lab/DLA_ARKA_I_CHETNYCH.md).
- Ślepa paczka do A1 (`paczka_testerzy.zip`, poza repo): sha256 `da0edbd792d2c8074bda39d7232c628fcfbf60933278728afd6db9220c225303`; skąd go wziąć albo jak
  wygenerować dane samemu: `paczka_testerzy/INSTRUKCJA.md`.
- Testy kodu (po `pip install -r slayer_eval/requirements.lock.txt`, Python 3.9+, bez sieci i bez wag):
  `python tests/test_slayer_eval.py && python tests/test_testy_danych_slayer.py`. Ewaluacja Slayera: `slayer_eval/README.md`.
