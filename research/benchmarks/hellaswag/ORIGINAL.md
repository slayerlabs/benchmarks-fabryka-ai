# HellaSwag: karta oryginału (etap A)

Znaczenie pól opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „A. Karta oryginału (ORIGINAL.md)”. Odczyt
źródeł: 2026-11-02.

| pole | wartość |
|---|---|
| Co mierzy | Zdroworozsądkowe wnioskowanie o codziennych czynnościach (commonsense NLI): wybór najbardziej prawdopodobnego dalszego ciągu opisu zdarzenia spośród 4 opcji. |
| Źródła: praca | Zellers i in., „HellaSwag: Can a Machine Really Finish Your Sentence?”, ACL 2019, [arXiv:1905.07830](https://arxiv.org/abs/1905.07830) |
| Źródła: repo autorów | [`rowanz/hellaswag`](https://github.com/rowanz/hellaswag) niedostępne (HTTP 451) po [zgłoszeniu DMCA od WikiHow](https://github.com/github/dmca/blob/master/2026/09/2026-09-14-wikihow.md) z 14.09.2026. Zamiast kodu autorów: praca, zadanie lm-eval i zbiór na HF. |
| Źródła: lm-eval | Space: [`hellaswag` @ `6d2abda4`](https://github.com/EleutherAI/lm-evaluation-harness/tree/6d2abda4fd171e68a8789330c4149e37c1ca0bda/lm_eval/tasks/hellaswag) (tag `v0.4.8`); repo: [`hellaswag` @ `v0.4.9.1`](https://github.com/EleutherAI/lm-evaluation-harness/tree/v0.4.9.1/lm_eval/tasks/hellaswag) |
| Źródła: zbiór HF | [`Rowan/hellaswag`](https://huggingface.co/datasets/Rowan/hellaswag/tree/218ec52e09a7e7462a5400043bb9a69a41d06b76) @ `218ec52e09a7e7462a5400043bb9a69a41d06b76` |
| Dane: split w pracy | walidacja i test (tabela 1 pracy) |
| Dane: n walidacja | 10042 <!-- liczba-spoza-wynikow: karta zbioru Rowan/hellaswag --> |
| Dane: n test | 10003 <!-- liczba-spoza-wynikow: karta zbioru Rowan/hellaswag --> |
| Dane: split w Space/repo | `validation`, panel 200 (METHOD.md Space); test T05, 0-shot |
| Dane: licencja | licencja autorów: MIT (według karty zbioru HF); tag HF: brak tagu; część tekstów z WikiHow objęta roszczeniem DMCA, więc status tej części jest niejasny. Ukryte odpowiedzi w teście: tak |
| Format zadania | Wybór 1 z 4 zakończeń. Błędne zakończenia wygenerowane maszynowo i dobrane przez Adversarial Filtering. Konteksty z ActivityNet Captions i WikiHow. |
| Prompt | Praca nie ma promptu (modele dostrajane). lm-eval (`utils.py`): `activity_label + ": " + ctx_a + " " + ctx_b.capitalize()`, separator spacja, opcja = zakończenie. Oba teksty czyszczone: `" [title]"` → `". "`, usunięte `[...]`, podwójne spacje. 0-shot. |
| Ocena | Log-likelihood każdej opcji po kontekście. `acc`: najwyższa suma log-prob; `acc_norm`: suma podzielona przez długość opcji w znakach. |
| Metryka decyzyjna | `acc_norm` (metryka T05 w Space) |
| Agregacja | Średnia po pytaniach, bez wag. Bez podziału na in-domain / zero-shot i ActivityNet / WikiHow, który podaje praca. |
| Bazy: losowa | 25% <!-- liczba-spoza-wynikow: 1/k przy k=4 --> |
| Bazy: większościowa | 25,7% (zawsze pozycja 2: 2584 z 10042; rozkład 0/1/2/3: 2515/2485/2584/2458) <!-- liczba-spoza-wynikow: policzone z Rowan/hellaswag validation, refs/convert/parquet --> |
| SNR: źródło | Praca Mamba (Gu, Dao 2023, [arXiv:2312.00752v2](https://arxiv.org/html/2312.00752v2), tabela 1, 0-shot acc_norm): 8 modeli 0,8–1,5B (Pythia-1B, Mamba-790M, GPT-Neo 1.3B, H3-1.3B, OPT-1.3B, Pythia-1.4B, RWKV-1.5B, Mamba-1.4B) |
| SNR: rozrzut | odchylenie std. ok. 3,6 pkt proc. <!-- liczba-spoza-wynikow: wyliczone z tabeli 1 pracy Mamba --> |
| SNR: SE pełna walidacja | ok. 0,5 pkt proc. (√(p(1−p)/n), n = 10042, p ok. 0,53) <!-- liczba-spoza-wynikow: wyliczone, n z karty HF --> |
| SNR: iloraz pełna walidacja | ok. 7 <!-- liczba-spoza-wynikow: rozrzut / SE, wyliczone --> |
| SNR: SE panel 200 | ok. 3,5 pkt proc. (√(p(1−p)/n), n = 200, p ok. 0,53) <!-- liczba-spoza-wynikow: wyliczone --> |
| SNR: iloraz panel 200 | ok. 1: na panelu 200 Space (T05) SE jest tego samego rzędu co rozrzut między modelami ~1B, więc T05 słabo je rozróżnia <!-- liczba-spoza-wynikow: rozrzut / SE panelu 200, wyliczone --> |
| Wynik referencyjny: EuroLLM-1.7B (kontrola etapu B) | 0,6057, HellaSwag po angielsku, `utter-project/EuroLLM-1.7B` @ `c730cd9b616799ace3c65e927d63191446f59374`, karta modelu <!-- liczba-spoza-wynikow: karta modelu EuroLLM-1.7B --> |
| EuroLLM: shoty i metryka | 10-shot (praca EuroLLM, [arXiv:2409.16235](https://arxiv.org/abs/2409.16235), rys. 6). Metryka (prawdopodobnie `acc_norm`) i protokół Okapi: nieustalone, bo karta modelu ich nie podaje. Space liczy T05 0-shot. |
| Wynik informacyjny: Pythia-1B | 47,2 (0-shot, acc_norm, wagi v1; praca Mamba, tabela 1 i dodatek E.2.3) <!-- liczba-spoza-wynikow: Gu i Dao 2023, tabela 1 --> |
| Wynik informacyjny: ludzie | 95,6% (praca) <!-- liczba-spoza-wynikow: Zellers i in. 2019 --> |
| Train policy | `eval_only` dla wszystkich splitów |
| Decyzja treningowa | Słaby wynik może wskazywać na brak angielskiego tekstu proceduralnego i narracyjnego w miksie. Nie mówi nic o polskim. Nie trenujemy na żadnym splicie HellaSwag. |
| Znane rozbieżności: lm-eval | `hellaswag.yaml`: `6d2abda4` (blob `c0735bbd97773488d99c047ab1342ad65aca4142`) → `v0.4.9.1` (blob `e0a2b87d7a2fd8831406d7bbce6c8b49065fbbca`): `dataset_path: hellaswag` → `Rowan/hellaswag`, usunięte `trust_remote_code: true`. Prompt i metryki bez zmian. `utils.py` identyczny (blob `b526a9e93076f7db54221072d58ca4bd7161ee97`). |
| Znane rozbieżności: zbiór | Stary skrypt HF pobierał dane z repo autorów, więc dziś nie działa. Działa konwersja parquet (`refs/convert/parquet`). |
| Znane rozbieżności: praca a lm-eval | Praca ocenia modele dostrajane, lm-eval 0-shot log-likelihoodem. Wyniki nie są porównywalne. |
| Znane rozbieżności: kontaminacja | Teksty WikiHow i ActivityNet są publiczne, więc mogły trafić do korpusów webowych. |