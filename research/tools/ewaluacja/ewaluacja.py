#!/usr/bin/env python3
"""Lokalny runner benchmarków fabryki (benchmarks-fabryka-ai) — bez vast.ai, bez bash, działa na Windows/Linux.

Liczy dokładnie tym samym kodem co przebieg centralny (research/common/ewaluuj.py, te same ZADANIA, fp32, batch 1),
tylko orkiestracja jest tutaj: jedna para model x test = jeden proces, log, czas, szczyt VRAM, wznawianie.
Listę modeli (MODELE), testów (KATALOGI), GOTOWE i KOD czyta z research/tools/przebieg_centralny.sh, więc nie ma
drugiej kopii konfiguracji.

    python ewaluacja.py lista
    python ewaluacja.py plan slayer1b-1.06 --zadania gotowe --probka 20
    python ewaluacja.py licz slayer1b-1.06 --zadania T02,T04 --probka 20
    python ewaluacja.py licz slayer1b-1.06 pythia-1b-v0 --zadania central --probka pelna
    python ewaluacja.py porownaj                       # lokalne wyniki vs results/central-run, pytanie po pytaniu
    python ewaluacja.py stan

Katalogi (względem tego pliku): fabryka/ = klon benchmarks-fabryka-ai (main), wyniki/<benchmark>/<model>/ jak na
instancji, logi/, czasy.jsonl. Interpreter: venv-lock/ (env "lock") i venv-new/ (env "new"), albo --python-lock/-new.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

TU = Path(__file__).resolve().parent
# W repo: research/tools/ewaluacja/ -> research/. Poza repo: klon w ./fabryka/.
FABRYKA = TU.parents[1] if (TU.parents[1] / "tools" / "przebieg_centralny.sh").exists() else TU / "fabryka" / "research"
SKRYPT_PRZEBIEGU = FABRYKA / "tools" / "przebieg_centralny.sh"
ODNIESIENIE = FABRYKA / "results" / "central-run"
OKNO_ROLLING = 4096

# Modele spoza MODELE skryptu, z zapisanymi wynikami w results/central-run (1.06 zastąpiono tam przez 1.07).
MODELE_DODATKOWE = [
    "slayer1b-1.06|SlayerLab/Slayer1B-1.06|ef81be58742544ad32e1afab38db011fec209609|slayer|lock",
    # modele kontrolne etapu B spoza MODELE (REPRODUCTION.md): EWoK i WSC273
    "gpt2-xl|openai-community/gpt2-xl|15ea56dee5df4983c59b2538573817e1667135e2|hf|lock",
    "bloom-560m|bigscience/bloom-560m|ac2ae5fab2ce3f9f40dc79b5ca9f637430d24971|hf|lock",
]
# Testy z zapisanymi wynikami przebiegu centralnego (7 katalogów results/central-run).
CENTRAL = ["T01", "T02", "T03", "T04", "T44", "T45", "T46"]


# --------------------------------------------------------------------------- konfiguracja z przebieg_centralny.sh

@dataclass
class Model:
    etykieta: str
    repo: str
    rewizja: str
    loader: str     # slayer | slayer-ckpt | hf | hf-trust
    env: str        # lock | new


def _tekst_skryptu() -> str:
    if not SKRYPT_PRZEBIEGU.exists():
        raise SystemExit(f"brak {SKRYPT_PRZEBIEGU} - sklonuj benchmarks-fabryka-ai do {TU / 'fabryka'}")
    return SKRYPT_PRZEBIEGU.read_text(encoding="utf-8")


def _zmienna(tekst: str, nazwa: str) -> str:
    """Wartość NAZWA="..." plus wszystkie NAZWA+=" ..." w kolejności."""
    czesci = re.findall(rf'^{nazwa}\+?="([^"]*)"', tekst, re.MULTILINE | re.DOTALL)
    if not czesci:
        raise SystemExit(f"{SKRYPT_PRZEBIEGU.name}: nie znaleziono {nazwa}")
    return " ".join(czesci)


def modele() -> dict[str, Model]:
    tekst = _tekst_skryptu()
    blok = re.search(r"^MODELE=\((.*?)^\)", tekst, re.MULTILINE | re.DOTALL).group(1)
    wiersze = re.findall(r'^\s*"([^"]+)"', blok, re.MULTILINE) + MODELE_DODATKOWE
    out = {}
    for w in wiersze:
        e, repo, rew, loader, env = w.split("|")
        out[e] = Model(e, repo, rew, loader, env)
    return out


def katalogi() -> dict[str, str]:
    """T01 -> blimp, w kolejności przebiegu."""
    pary = _zmienna(_tekst_skryptu(), "KATALOGI").split()
    return dict(p.split(":", 1) for p in pary)


def gotowe() -> list[str]:
    return _zmienna(_tekst_skryptu(), "GOTOWE").split()


def kod_zadan() -> dict[str, str]:
    pary = _zmienna(_tekst_skryptu(), "KOD").split()
    return dict(p.split(":", 1) for p in pary)


def rozwin_zadania(spec: str) -> list[str]:
    k = katalogi()
    if spec == "wszystkie":
        return list(k)
    if spec == "gotowe":
        return gotowe()
    if spec == "central":
        return list(CENTRAL)
    ids = [s.strip().upper() for s in spec.split(",") if s.strip()]
    nieznane = [t for t in ids if t not in k]
    if nieznane:
        raise SystemExit(f"nieznane zadania: {nieznane}; dostępne: {' '.join(k)}")
    return ids


# --------------------------------------------------------------------------- środowisko

def python_env(env: str, a) -> Path | None:
    jawny = getattr(a, f"python_{env}", None)
    if jawny:
        return Path(jawny)
    for kand in (TU / f"venv-{env}" / "Scripts" / "python.exe", TU / f"venv-{env}" / "bin" / "python"):
        if kand.exists():
            return kand
    return None


def sciezka_wag(m: Model) -> Path | None:
    """Katalog wag w lokalnym cache HF (dokładnie przypięta rewizja), bez pobierania."""
    if m.loader == "slayer-ckpt":
        d = TU / "modele" / m.etykieta
        return d if (d / "model.safetensors").exists() else None
    try:
        from huggingface_hub import snapshot_download
        d = Path(snapshot_download(m.repo, revision=m.rewizja, local_files_only=True))
    except Exception:
        return None
    # snapshot w cache bywa częściowy (np. sam tokenizer.json): wymagamy configu i kompletu wag
    if not (d / "config.json").exists():
        return None
    indeks = d / "model.safetensors.index.json"
    if indeks.exists():
        pliki = set(json.loads(indeks.read_text(encoding="utf-8"))["weight_map"].values())
        return d if all((d / p).exists() for p in pliki) else None
    return d if any(d.glob("*.safetensors")) or any(d.glob("pytorch_model*.bin")) else None


def nazwa_gpu() -> str:
    try:
        n = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                           capture_output=True, text=True, timeout=20).stdout.strip().splitlines()[0]
    except Exception:
        n = "cpu"
    return n.replace(" ", "_")


class SzczytVram:
    """Próbkuje nvidia-smi co `co` s; .szczyt_mib = maksimum memory.used w trakcie."""

    def __init__(self, co: float = 1.0):
        self.co, self.szczyt_mib, self._stop = co, None, threading.Event()
        self._t = threading.Thread(target=self._petla, daemon=True)

    def _petla(self):
        while not self._stop.is_set():
            try:
                v = int(subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                       capture_output=True, text=True, timeout=10).stdout.split()[0])
                self.szczyt_mib = max(self.szczyt_mib or 0, v)
            except Exception:
                pass
            self._stop.wait(self.co)

    def __enter__(self):
        self._t.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._t.join(timeout=5)


# --------------------------------------------------------------------------- komendy ewaluacji

def polecenie(m: Model, task: str, a, py: Path, wagi: Path, wyj: Path) -> list[str]:
    """Ta sama linia, którą buduje `polecenie()` w przebieg_centralny.sh (dla lokalnych ścieżek)."""
    probka = a.probka_rolling if (task == "T03" and a.probka_rolling) else a.probka
    wspolne = ["--repo", m.repo, "--revision", m.rewizja, "--model_path", str(wagi), "--zadania", task,
               "--probka", str(probka), "--device", a.device, "--batch", "1", "--eval_gpu", nazwa_gpu(),
               "--etykieta", m.etykieta, "--wyjscie", str(wyj)]
    kod = kod_zadan().get(task)
    if kod:
        return [str(py), str(FABRYKA / kod), "przebieg", *wspolne]
    skrypt = [str(FABRYKA / "common" / "ewaluuj.py")]
    if getattr(a, "fewshot", None) is not None:
        skrypt = [str(TU / "ewaluuj_shoty.py"), str(a.fewshot)]
    cmd = [str(py), *skrypt, "--model", "slayer" if m.loader.startswith("slayer") else "hf", *wspolne]
    if a.dane != "hf":
        cmd += ["--dane", a.dane]
    if m.loader == "hf-trust":
        cmd.append("--trust_remote_code")
    if task == "T03" and not m.loader.startswith("slayer"):
        cmd += ["--max_length", str(OKNO_ROLLING)]
    return cmd


def srodowisko_procesu(a) -> dict:
    env = dict(os.environ)
    env.update(PYTHONUTF8="1",            # ewaluuj.py pisze write_text() bez encoding: na Windows bez tego cp1250
               PYTHONUNBUFFERED="1", NVIDIA_TF32_OVERRIDE="0", HF_HUB_DISABLE_PROGRESS_BARS="1")
    if a.offline:
        env.update(HF_HUB_OFFLINE="1", HF_DATASETS_OFFLINE="1")
    return env


def katalog_wynikow(a) -> Path:
    return Path(a.wyniki).resolve()


def wynik_gotowy(wyj: Path) -> bool:
    """results.json z obserwacją state=ok (failed / blocked liczymy jeszcze raz)."""
    p = wyj / "results.json"
    if not p.exists():
        return False
    try:
        obs = json.loads(p.read_text(encoding="utf-8"))["observations"]
        return bool(obs) and all(o.get("state") == "ok" for o in obs)
    except Exception:
        return False


def zapisz_czas(a, wpis: dict):
    with open(Path(a.wyniki).resolve().parent / "czasy.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(wpis, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------- potok: CPU przygotowuje, GPU liczy

GOTOWOSC = TU / "gotowe"            # znaczniki <T>.ok / <T>.blad z przygotuj_zadanie.py
ROLLING = {"T03"}                   # WikiText: okno 4096 w fp32, szczyt VRAM ~2x większy -> liczony sam


def vram_total_mib() -> int | None:
    try:
        return int(subprocess.run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                                  capture_output=True, text=True, timeout=20).stdout.split()[0])
    except Exception:
        return None


def vram_used_mib() -> int:
    try:
        return int(subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                  capture_output=True, text=True, timeout=20).stdout.split()[0])
    except Exception:
        return 0


def szacunek_vram(etyk: str, task: str, wagi: Path | None) -> int:
    """MiB na proces: najwyższy szczyt z czasy.jsonl dla modelu (bez rolling), inaczej z rozmiaru wag (fp32)."""
    p = TU / "czasy.jsonl"
    szczyty = []
    if p.exists():
        for l in p.read_text(encoding="utf-8").splitlines():
            r = json.loads(l)
            if r.get("model") == etyk and r.get("vram_szczyt_mib") and r.get("zadanie") not in ROLLING \
                    and r.get("rownolegle", 1) == 1 and r.get("kod") == 0:
                szczyty.append(r["vram_szczyt_mib"])
    if szczyty:
        return max(szczyty) + 300
    bajty = sum(f.stat().st_size for f in wagi.glob("*") if f.suffix in (".safetensors", ".bin")) if wagi else 0
    mnoznik = 2 if bajty and next(wagi.glob("*.safetensors"), None) and bajty < 3e9 else 1  # bf16 na dysku -> fp32
    return int(bajty * mnoznik / 2**20 * 1.25) + 1500 if bajty else 9000


def przygotuj_w_tle(zadania: list[str], a, py: Path) -> dict:
    """Uruchamia przygotowanie testów w puli wątków (każdy = osobny proces CPU). Zwraca {T: Future}."""
    from concurrent.futures import ThreadPoolExecutor
    GOTOWOSC.mkdir(exist_ok=True)
    (TU / "logi").mkdir(exist_ok=True)
    pula = ThreadPoolExecutor(max_workers=max(1, a.cpu))

    def jedno(t):
        if (GOTOWOSC / f"{t}.ok").exists() and not a.przygotuj_od_nowa:
            return True
        log = TU / "logi" / f"przygotuj_{t}.log"
        t0 = time.time()
        with open(log, "w", encoding="utf-8") as f:
            env = srodowisko_procesu(a)
            env.pop("HF_HUB_OFFLINE", None), env.pop("HF_DATASETS_OFFLINE", None)   # przygotowanie = z siecią
            kod = subprocess.run([str(py), str(TU / "przygotuj_zadanie.py"), t, str(GOTOWOSC)], stdout=f,
                                 stderr=subprocess.STDOUT, env=env, cwd=str(FABRYKA)).returncode
        print(f"  [przygotuj {t}] {'gotowe' if kod == 0 else 'BLAD (log ' + str(log.relative_to(TU)) + ')'} "
              f"{time.time() - t0:.0f} s", flush=True)
        return kod == 0

    futures = {t: pula.submit(jedno, t) for t in zadania}
    pula.shutdown(wait=False)
    return futures


@dataclass
class Praca:
    m: Model
    task: str
    py: Path
    wagi: Path
    wyj: Path
    vram: int
    proc: subprocess.Popen | None = None
    log_f: object = None
    t0: float = 0.0


def cmd_przygotuj(a) -> int:
    py = python_env("lock", a)
    if py is None:
        raise SystemExit("brak venv-lock")
    futures = przygotuj_w_tle(rozwin_zadania(a.zadania), a, py)
    ok = [t for t, f in futures.items() if f.result()]
    print(f"gotowe {len(ok)}/{len(futures)}: {' '.join(ok)}")
    return 0 if len(ok) == len(futures) else 1


def cmd_licz(a) -> int:
    ms, kat = modele(), katalogi()
    zadania = rozwin_zadania(a.zadania)
    (TU / "logi").mkdir(exist_ok=True)
    wyniki = katalog_wynikow(a)

    # 1) lista prac (model x test), bez gotowych
    kolejka: list[Praca] = []
    for etyk in a.modele:
        if etyk not in ms:
            raise SystemExit(f"nieznany model {etyk}; dostępne: {' '.join(ms)}")
        m = ms[etyk]
        py = python_env(m.env, a)
        wagi = sciezka_wag(m)
        if py is None or wagi is None:
            print(f"POMINIETY {etyk}: " + ("brak interpretera env " + m.env if py is None else
                  f"brak kompletnych wag {m.repo}@{m.rewizja[:8]} w cache HF"))
            continue
        for t in zadania:
            wyj = wyniki / (kat[t] + (f"-{a.fewshot}shot" if a.fewshot is not None else "")) / etyk
            if wynik_gotowy(wyj) and not a.nadpisz:
                print(f"[{etyk} {t}] już policzone - pomijam (--nadpisz liczy od nowa)")
                continue
            kolejka.append(Praca(m, t, py, wagi, wyj, szacunek_vram(etyk, t, wagi)))
    if not kolejka:
        return 0

    # 2) CPU w tle przygotowuje zbiory (od razu wszystkie testy, po a.cpu naraz); GPU czeka tylko na swój test
    py_przyg = python_env("lock", a) or kolejka[0].py
    gotowe = przygotuj_w_tle(sorted({p.task for p in kolejka}, key=zadania.index), a, py_przyg)

    # 3) harmonogram GPU: kilka procesów naraz w budżecie VRAM; rolling sam
    total = vram_total_mib() or 16000
    budzet = total - vram_used_mib() - a.zapas_vram
    print(f"VRAM {total} MiB, budżet na liczenie {budzet} MiB, max {a.rownolegle} procesów naraz; "
          f"{len(kolejka)} par model x test", flush=True)
    biegnace: list[Praca] = []
    bledy = 0
    # Bez wymuszonego offline: datasets 3.6.0 przy przypiętej rewizji pyta hub o metadane nawet z pełnym cache
    # (OfflineModeIsEnabled). Dane są już w cache po przygotowaniu, sieć dostaje tylko lekkie zapytania.
    env = srodowisko_procesu(a)
    vram_mon = SzczytVram(co=2.0).__enter__()

    def start(p: Praca):
        if p.wyj.exists():
            shutil.rmtree(p.wyj)
        cmd = polecenie(p.m, p.task, a, p.py, p.wagi, p.wyj)
        log = TU / "logi" / f"{p.m.etykieta}_{p.task}.log"
        p.log_f = open(log, "w", encoding="utf-8")
        p.log_f.write(" ".join(cmd) + "\n\n")
        p.log_f.flush()
        p.t0 = time.time()
        p.proc = subprocess.Popen(cmd, stdout=p.log_f, stderr=subprocess.STDOUT, env=env, cwd=str(FABRYKA))
        print(f"[{p.m.etykieta} {p.task}] start (~{p.vram} MiB, naraz {len(biegnace) + 1})", flush=True)

    def koniec(p: Praca):
        nonlocal bledy
        kod = p.proc.returncode
        p.log_f.close()
        s = round(time.time() - p.t0, 1)
        print(f"[{p.m.etykieta} {p.task}] {'ok' if kod == 0 else f'BLAD kod={kod}'}  {s} s", flush=True)
        if kod:
            bledy += 1
            log = TU / "logi" / f"{p.m.etykieta}_{p.task}.log"
            print("    " + "\n    ".join(log.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-5:]))
        zapisz_czas(a, {"etap": "ewaluacja", "model": p.m.etykieta, "zadanie": p.task, "kod": kod, "s": s,
                        "vram_szczyt_mib": vram_mon.szczyt_mib if a.rownolegle == 1 else None,
                        "rownolegle": a.rownolegle, "gpu": nazwa_gpu(), "probka": str(a.probka), "env": p.m.env,
                        "wyniki": str(wyniki), "czas": time.strftime("%Y-%m-%dT%H:%M:%S")})
        vram_mon.szczyt_mib = None

    try:
        while kolejka or biegnace:
            for p in [p for p in biegnace if p.proc.poll() is not None]:
                biegnace.remove(p)
                koniec(p)
            zajete = sum(p.vram for p in biegnace)
            rolling_biegnie = any(p.task in ROLLING for p in biegnace)
            for p in list(kolejka):
                f = gotowe[p.task]
                if not f.done():
                    continue                                   # CPU jeszcze przygotowuje ten test
                if not f.result():
                    kolejka.remove(p)
                    bledy += 1
                    print(f"[{p.m.etykieta} {p.task}] POMINIETY: przygotowanie nieudane (logi/przygotuj_{p.task}.log)")
                    continue
                if len(biegnace) >= a.rownolegle or rolling_biegnie:
                    break
                if p.task in ROLLING and biegnace:
                    continue                                   # rolling czeka na pustą kartę
                if biegnace and zajete + p.vram > budzet:
                    continue
                kolejka.remove(p)
                start(p)
                biegnace.append(p)
                zajete += p.vram
                rolling_biegnie = p.task in ROLLING
            time.sleep(0.5)
    finally:
        vram_mon.__exit__(None, None, None)
    return 1 if bledy else 0


def cmd_plan(a) -> int:
    ms, kat = modele(), katalogi()
    for etyk in a.modele:
        m = ms[etyk]
        py = python_env(m.env, a) or Path(f"<venv-{m.env}>/python")
        wagi = sciezka_wag(m) or Path(f"<wagi {m.repo}@{m.rewizja[:8]}>")
        for t in rozwin_zadania(a.zadania):
            print(" ".join(polecenie(m, t, a, py, wagi, katalog_wynikow(a) / kat[t] / etyk)))
    return 0


def cmd_lista(a) -> int:
    ms, kat, got = modele(), katalogi(), set(gotowe())
    print("MODELE (z przebieg_centralny.sh + dodatkowe)")
    for m in ms.values():
        wagi = sciezka_wag(m)
        py = python_env(m.env, a)
        print(f"  {m.etykieta:20s} {m.loader:12s} env={m.env:4s} wagi={'OK' if wagi else 'brak':4s} "
              f"python={'OK' if py else 'brak':4s} {m.repo}@{m.rewizja[:8]}")
    print("\nZADANIA (* = GOTOWE w STATUS.md, c = zapisane w results/central-run)")
    kody = kod_zadan()
    for t, b in kat.items():
        flagi = ("*" if t in got else " ") + ("c" if (ODNIESIENIE / b).exists() else " ")
        print(f"  {t} {flagi} {b}" + (f"   (własny kod: {kody[t]})" if t in kody else ""))
    return 0


# --------------------------------------------------------------------------- porównanie

def _probki(katalog: Path) -> dict[str, list[dict]]:
    """{nazwa pliku bez rozszerzenia: [rekordy]} z probki/*.jsonl i *.jsonl.gz."""
    out = {}
    for p in sorted((katalog / "probki").glob("*.jsonl*")):
        otworz = gzip.open if p.suffix == ".gz" else open
        with otworz(p, "rt", encoding="utf-8") as f:
            out[p.name.split(".jsonl")[0]] = [json.loads(l) for l in f if l.strip()]
    return out


def _logliki(rek: dict) -> list[float]:
    fr = rek.get("filtered_resps")
    if isinstance(fr, str):
        try:
            fr = json.loads(fr)
        except Exception:
            return []
    out = []
    for x in fr or []:
        if isinstance(x, (list, tuple)) and x and isinstance(x[0], (int, float)):
            out.append(float(x[0]))
        elif isinstance(x, (int, float)):
            out.append(float(x))
    return out


def _metryka_rekordu(rek: dict, nazwa: str) -> float | None:
    v = rek.get(nazwa)
    try:
        return float(v) if not isinstance(v, (list, dict)) else None
    except (TypeError, ValueError):
        return None


def _obserwacja(katalog: Path) -> dict | None:
    p = katalog / "results_rozszerzone.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))["observations"][0]


def porownaj_pare(lok: Path, ref: Path) -> dict:
    """Jedna para benchmark x model. Wynik główny + zgodność per pytanie na wspólnych dokumentach (doc_hash)."""
    ol, orf = _obserwacja(lok), _obserwacja(ref)
    wiersz = {"stan_lok": ol.get("state") if ol else "brak", "metryka": (orf or ol or {}).get("metric")}
    if not ol or ol.get("state") != "ok":
        return wiersz
    wiersz.update(wartosc_lok=ol["value"], n_lok=ol["n_scored"])
    if not orf:
        return wiersz
    wiersz.update(wartosc_ref=orf["value"], n_ref=orf["n_scored"])
    se = None
    try:
        glowna = orf["metric"].split(",")[0]
        d = orf["dodatkowe"]["space"]
        se = (d.get(glowna) or d.get("byte_perplexity") or {}).get("se")
    except Exception:
        pass
    wiersz["se_ref"] = se

    pl, pr = _probki(lok), _probki(ref)
    nazwa = next((n for n in pl if n.endswith("_space") or "_space_" in n), None) or next(iter(pl), None)
    if not nazwa or nazwa not in pr:
        return wiersz
    po_hash = {r["doc_hash"]: r for r in pr[nazwa]}
    wspolne = [(r, po_hash[r["doc_hash"]]) for r in pl[nazwa] if r["doc_hash"] in po_hash]
    if not wspolne:
        return wiersz
    glowna = orf["metric"].split(",")[0]
    zgodne_pred, max_dll, ml, mr, n_m = 0, 0.0, 0.0, 0.0, 0
    for rl, rr in wspolne:
        ll, lr = _logliki(rl), _logliki(rr)
        if ll and len(ll) == len(lr):
            max_dll = max(max_dll, max(abs(x - y) for x, y in zip(ll, lr)))
            zgodne_pred += int(max(range(len(ll)), key=ll.__getitem__) == max(range(len(lr)), key=lr.__getitem__))
        vl, vr = _metryka_rekordu(rl, glowna), _metryka_rekordu(rr, glowna)
        if vl is not None and vr is not None:
            ml, mr, n_m = ml + vl, mr + vr, n_m + 1
    wiersz.update(n_wspolnych=len(wspolne), zgodnosc_pred=zgodne_pred / len(wspolne), max_dloglik=max_dll)
    if n_m:
        wiersz.update(metryka_lok_wspolne=ml / n_m, metryka_ref_wspolne=mr / n_m)
    return wiersz


def werdykt(w: dict, tol_loglik: float) -> str:
    if w.get("stan_lok") != "ok":
        return w.get("stan_lok", "brak")
    if "wartosc_ref" not in w:
        return "brak odniesienia"
    if "n_wspolnych" not in w:
        return "brak wspólnych próbek"
    pelne = w["n_lok"] == w["n_ref"]
    if w["max_dloglik"] <= tol_loglik and w["zgodnosc_pred"] == 1.0:
        return "IDENTYCZNE" if pelne else "IDENTYCZNE (na próbce)"
    if w["zgodnosc_pred"] >= 0.99:
        return "ZGODNE ~num" + ("" if pelne else " (próbka)")
    return "ROZNE"


def cmd_porownaj(a) -> int:
    wyniki, ref_root = katalog_wynikow(a), Path(a.odniesienie).resolve()
    if not wyniki.exists():
        raise SystemExit(f"brak {wyniki} - najpierw `licz`")
    rows = []
    for bench in sorted(p for p in wyniki.iterdir() if p.is_dir()):
        for mdir in sorted(p for p in bench.iterdir() if p.is_dir()):
            w = porownaj_pare(mdir, ref_root / bench.name / mdir.name)
            rows.append((bench.name, mdir.name, w, werdykt(w, a.tol_loglik)))
    f = lambda v, n=4: "-" if v is None else (f"{v:.{n}f}" if isinstance(v, float) else str(v))
    print(f"{'benchmark':15s} {'model':18s} {'metryka':16s} {'lokalnie':>9s} {'zapisane':>9s} {'Δ':>8s} "
          f"{'SE zap.':>7s} {'n lok/zap':>11s} {'wsp.':>6s} {'zgodn.':>7s} {'maxΔll':>8s}  werdykt")
    for b, m, w, v in rows:
        d = (w["wartosc_lok"] - w["wartosc_ref"]) if "wartosc_lok" in w and "wartosc_ref" in w else None
        print(f"{b:15s} {m:18s} {f(w.get('metryka'))[:16]:16s} {f(w.get('wartosc_lok')):>9s} "
              f"{f(w.get('wartosc_ref')):>9s} {f(d):>8s} {f(w.get('se_ref')):>7s} "
              f"{f(w.get('n_lok'))+'/'+f(w.get('n_ref')):>11s} {f(w.get('n_wspolnych')):>6s} "
              f"{f(w.get('zgodnosc_pred'), 3):>7s} {f(w.get('max_dloglik'), 2) if w.get('max_dloglik') is not None else '-':>8s}  {v}")
        if "metryka_lok_wspolne" in w and w["n_lok"] != w.get("n_ref"):
            print(f"{'':35s} na wspólnych pytaniach: lokalnie {w['metryka_lok_wspolne']:.4f}, "
                  f"zapisane {w['metryka_ref_wspolne']:.4f}")
    if a.json:
        Path(a.json).write_text(json.dumps([{"benchmark": b, "model": m, **w, "werdykt": v} for b, m, w, v in rows],
                                           ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nzapisano {a.json}")
    return 0


def _ostatnia_probka(model: str, task: str, katalog: Path):
    """`probka` z ostatniego udanego przebiegu pary model × test w czasy.jsonl."""
    wynik = None
    for p in (TU / "czasy.jsonl", katalog / "czasy.jsonl"):
        if not p.exists():
            continue
        for linia in p.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(linia)
            except ValueError:
                continue
            if r.get("etap") == "ewaluacja" and r.get("model") == model and r.get("zadanie") == task and r.get("kod") == 0:
                wynik = r.get("probka")
    return wynik


def cmd_kontrola(a) -> int:
    """Pełne przebiegi modeli kontrolnych vs wartości opublikowane (kontrole.json z REPRODUCTION.md)."""
    k = json.loads((TU / "kontrole.json").read_text(encoding="utf-8"))["kontrole"]
    wyniki = katalog_wynikow(a)
    print(f"{'benchmark':11s} {'model':13s} {'metryka':9s} {'nasz':>7s} {'SE':>6s} {'n':>6s} {'opubl.':>7s} "
          f"{'Δ pkt':>6s} {'próg':>5s} {'fabryka':>7s} {'Δfab':>6s}  werdykt")
    for c in k:
        d = wyniki / c["benchmark"] / c["model"]
        if c.get("tylko_osobnym_kodem"):
            print(f"{c['benchmark']:11s} {c['model']:13s} {c['metryka']:9s} {'-':>7s}  kontrola tylko osobnym kodem: "
                  f"{c['kod_fabryki']} (wynik pipeline'u nie jest tą kontrolą)")
            continue
        o = _obserwacja(d)
        wiersze = [(c["metryka"], c)] + [(m, v) for m, v in (c.get("pomocnicze") or {}).items()]
        for i, (met, ref) in enumerate(wiersze):
            if not o or o.get("state") != "ok":
                stan = "brak pełnego przebiegu" if not o else o.get("state")
                print(f"{c['benchmark']:11s} {c['model']:13s} {met:9s} {'-':>7s}  {stan}")
                break
            try:
                rozsz = json.loads((d / "results_rozszerzone.json").read_text(encoding="utf-8"))
                pelna = rozsz.get("probka") == "pelna"
            except Exception:
                rozsz, pelna = {}, False
            if "probka" not in rozsz:   # zadania z własnym kodem (ewok.py) nie zapisują próbki - bierzemy z czasy.jsonl
                pelna = _ostatnia_probka(c["model"], c["task"], wyniki) == "pelna"
            sp = (o.get("dodatkowe") or {}).get("space") or {}
            v = sp.get(met) or {}
            if not v and (sp.get("glowna") or {}).get("metryka") == met:   # testy z metryką w `glowna` (LAMBADA)
                v = sp["glowna"]
            wart = v.get("value", o["value"] if i == 0 else None)
            if wart is None:
                print(f"{c['benchmark']:11s} {c['model']:13s} {met:9s} brak metryki w wyniku")
                continue
            if wart > 1.5:          # procenty (np. ewok 65.4)
                wart /= 100
            se_ref = ref.get("se_opublikowanej")
            prog = max(0.02, 2 * se_ref) if se_ref else 0.02
            delta = wart - ref["opublikowana"]
            fab = ref.get("fabryka")
            w = ("W PROGU" if abs(delta) <= prog else "POZA PROGIEM") + ("" if i == 0 else " (pomocnicza)")
            if not pelna:
                w += " [NIE pełny split!]"
            print(f"{c['benchmark']:11s} {c['model']:13s} {met:9s} {wart:7.4f} {v.get('se') or 0:6.4f} "
                  f"{v.get('n') or o.get('n_scored'):>6} {ref['opublikowana']:7.4f} {100*delta:+6.2f} {100*prog:5.2f} "
                  f"{('-' if fab is None else f'{fab:.4f}'):>7s} {('-' if fab is None else f'{100*(wart-fab):+.2f}'):>6s}  {w}")
    return 0


def cmd_stan(a) -> int:
    p = Path(a.wyniki).resolve().parent / "czasy.jsonl"
    if not p.exists():
        print("brak czasy.jsonl")
        return 0
    ost = {}
    for l in p.read_text(encoding="utf-8").splitlines():
        r = json.loads(l)
        ost[(r["model"], r["zadanie"])] = r
    for (m, t), r in sorted(ost.items()):
        print(f"{m:20s} {t}  {'ok ' if r['kod'] == 0 else 'BLAD'}  {r['s']:>8.1f} s  VRAM {r.get('vram_szczyt_mib')} MiB"
              f"  probka={r.get('probka')}")
    return 0


# --------------------------------------------------------------------------- CLI

def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wyniki", default=str(TU / "wyniki"))
    ap.add_argument("--python-lock", dest="python_lock")
    ap.add_argument("--python-new", dest="python_new")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def wspolne(p):
        p.add_argument("modele", nargs="+")
        p.add_argument("--zadania", default="gotowe", help="gotowe | wszystkie | central | T01,T02,...")
        p.add_argument("--probka", default="pelna", help="pelna | panel200 | liczba dokumentów")
        p.add_argument("--probka-rolling", dest="probka_rolling", default=None, help="osobna próbka dla T03")
        p.add_argument("--device", default="cuda")
        p.add_argument("--dane", default="hf", choices=["hf", "lokalne"])
        p.add_argument("--offline", action="store_true", help="HF_HUB_OFFLINE=1 (tylko cache)")
        p.add_argument("--nadpisz", action="store_true")
        p.add_argument("--rownolegle", type=int, default=2, help="max procesów liczących naraz na GPU")
        p.add_argument("--cpu", type=int, default=3, help="wątki przygotowania zbiorów w tle")
        p.add_argument("--zapas-vram", dest="zapas_vram", type=int, default=800, help="MiB zostawione wolne")
        p.add_argument("--przygotuj-od-nowa", dest="przygotuj_od_nowa", action="store_true")
        p.add_argument("--fewshot", type=int, default=None,
                       help="nadpisz num_fewshot (np. kontrola HellaSwag 10-shot); wynik w <benchmark>-<N>shot/")

    wspolne(sub.add_parser("licz", help="potok: CPU przygotowuje zbiory w tle, GPU liczy kilka par naraz"))
    wspolne(sub.add_parser("plan", help="pokaż komendy bez liczenia"))
    pp = sub.add_parser("przygotuj", help="tylko przygotowanie zbiorów (sieć, CPU)")
    pp.add_argument("--zadania", default="gotowe")
    pp.add_argument("--cpu", type=int, default=3)
    pp.add_argument("--przygotuj-od-nowa", dest="przygotuj_od_nowa", action="store_true")
    pp.add_argument("--offline", action="store_true")
    sub.add_parser("lista", help="modele, wagi w cache, zadania")
    sub.add_parser("stan", help="ostatnie przebiegi z czasy.jsonl")
    sub.add_parser("kontrola", help="pełne przebiegi modeli kontrolnych vs wartości opublikowane (kontrole.json)")
    p = sub.add_parser("porownaj", help="lokalne wyniki vs results/central-run")
    p.add_argument("--odniesienie", default=str(ODNIESIENIE))
    p.add_argument("--tol-loglik", dest="tol_loglik", type=float, default=1e-3)
    p.add_argument("--json")
    a = ap.parse_args(argv)
    return {"licz": cmd_licz, "plan": cmd_plan, "lista": cmd_lista, "stan": cmd_stan,
            "porownaj": cmd_porownaj, "przygotuj": cmd_przygotuj, "kontrola": cmd_kontrola}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
