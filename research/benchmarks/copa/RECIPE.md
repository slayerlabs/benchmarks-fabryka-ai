# COPA (T11): przepis

Jeden wpis na każdy wynik. Wyników jeszcze nie ma: liczy je przebieg centralny, a wpis dostaje wtedy commit, sprzęt i datę.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13)
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII)
- Zbiór: `aps/super_glue@3de24cf8022e94f4ee4b9d55a6f539891524d646` (wpis `T11` w `common/zadania.py`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie zadania; dla tego zadania woła `common/ewaluuj.py --zadania T11 --probka pelna --device cuda` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T11 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: niezapisane (przed przebiegiem)
- Sprzęt: niezapisane (przed przebiegiem)
- Data: niezapisane (przed przebiegiem)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/copa/<model>/results.json`

## Smoke test przed przebiegiem

Siedem wierszy `validation` (`aps/super_glue` @ `3de24cf8022e94f4ee4b9d55a6f539891524d646`, konfiguracja `copa`). Tekst jest z `doc_to_text` i `doc_to_choice` w `utils.py` o blobie `3afc868eb486c47c51b0036ce955502bc377c9c4` (tag lm-eval `v0.4.9.1`). Oceniana kontynuacja to spacja separatora (`target_delimiter`, domyślnie spacja) doklejona przed opcją, która sama zaczyna się od spacji, więc poniżej są dwie spacje. Złoto to numer opcji (`label` 0 = pierwsza). Logprobu modelu nie ma: wag nie ładowano.

`idx` w zbiorze jest równy numerowi wiersza, od 0 do 99. Identyfikatory 401–500 z karty to numery tych samych pytań w paczce autorów, nie to pole. W każdym punkcie są trzy teksty: kontekst, pierwsza kontynuacja, druga kontynuacja.

- idx 0, `effect`, złoto druga: `The man turned on the faucet therefore` / `  the toilet filled with water.` / `  water flowed from the spout.`
- idx 4, `cause`, złoto druga: `The hamburger meat browned because` / `  the cook froze it.` / `  the cook grilled it.`
- idx 19, `cause`, złoto pierwsza: `The woman ran her finger under cold water because` / `  she burned her finger on the toaster.` / `  she put a diamond ring on her finger.` To jest przykład z karty.
- idx 24, `effect`, złoto pierwsza: `The man confessed his love for the woman therefore` / `  the woman rejected him.` / `  the woman envied him.`
- idx 49, `effect`, złoto pierwsza: `I pressed my hand into the wet cement therefore` / `  my handprint dried in the cement.` / `  cracks emerged in the cement.`
- idx 80, `cause`, złoto pierwsza: `Everyone in the class turned to stare at the student because` / `  the student's phone rang.` / `  the student took notes.`
- idx 99, `effect`, złoto druga: `The woman was in a bad mood therefore` / `  she engaged in small talk with her friend.` / `  she told her friend to leave her alone.`

Na wszystkich 100 wierszach: premisa kończy się kropką, opcja nie ma białych znaków na brzegu i zaczyna się wielką literą, a tekst złota jest równy opcji o tym `label`. Pytań `cause` jest 52, `effect` 48. Pierwsza opcja jest złotem w 55 wierszach, druga w 45. Szablon z tych siedmiu pytań jest więc szablonem całego splitu.
