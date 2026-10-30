"""EWoK-PL: ewaluacja wiedzy o świecie (Elements of World Knowledge) po polsku, protokół jak w paperze EWoK.

Rekord EWoK to dwa konteksty (C1, C2) i dwa zdania docelowe (T1, T2) w układzie par minimalnych:
T1 pasuje do C1, T2 do C2. Liczymy log P(T | C) = suma logprob tokenów T po „C " (ten sam scorer co
slayer_eval/hipoteza_formatu.py: para jak lm-eval, jeden BOS jak METHOD.md Space).

Reguła główna (Ivanova i in. 2024, LOGPROBS, arXiv:2405.09605): target stały, porównujemy konteksty.
  s1 = [log P(T1|C1) > log P(T1|C2)],  s2 = [log P(T2|C2) > log P(T2|C1)],  wynik = (s1 + s2) / 2.
Losowo 0,5. Ten sam napis T po obu stronach porównania, więc prior litery/długości odpowiedzi
(problem z raportu Slayera 1B) tu nie działa. Diagnostyki: `oba` (s1 i s2), `kontekst_staly`
(porównanie T1 vs T2 przy tym samym C, wrażliwe na prior zdania), `kontekst_staly_pmi` (to samo po
odjęciu log P(T) bez kontekstu) i `staly_target` (udział rekordów, w których przy obu kontekstach
model woli to samo zdanie: ślad prioru, odpowiednik stałej litery).

  python ewok_pl/ewok.py licz --model <katalog> --dane pl --zip ewok-pl-complete-0001-0625.zip --wyjscie wyniki_ewok/<etykieta>
  python ewok_pl/ewok.py licz --model <katalog> --dane en625 --wyjscie wyniki_ewok/<etykieta>
  python ewok_pl/ewok.py licz --model <katalog> --dane en --wyjscie wyniki_ewok/<etykieta>
  python ewok_pl/ewok.py analiza --wyniki wyniki_ewok --zip ewok-pl-complete-0001-0625.zip

Dane PL czytamy prosto z zipa z hasłem (TERMS_OF_USE EWoK: bez odszyfrowanej treści w repo); EN
z ewok-core/ewok-core-1.0 (gated, przypięta rewizja). Wyjście `licz`: <wyjscie>/<dane>.jsonl, wiersz
na rekord (id, source_id, logliki 2×2, bezwarunkowe, tokeny), bez tekstu.
"""

import argparse
import json
import sys
import time
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch

KATALOG = Path(__file__).resolve().parent
sys.path.insert(0, str(KATALOG.parent / "slayer_eval"))

from hipoteza_formatu import ModelSlayer, licz_logliki, para  # noqa: E402
from metryki import POWTORZENIA, SEED, srednia_z_niepewnoscia  # noqa: E402

EWOK_REPO = "ewok-core/ewok-core-1.0"
EWOK_REW = "34d912a608066c92e2990a0328ffc3bd9a716042"
ZIP_PLIK = "ewok_pl_combined/ewok-pl-0001-0625.jsonl"
ZIP_HASLO = b"ewok"  # hasło z TERMS_OF_USE EWoK, to samo co w oryginale
META = ("Domain", "ConceptA", "ConceptB", "ContextType", "ContextDiff", "TargetDiff")


# ---------------------------------------------------------------- modele

class ModelHFBos:
    """Model z transformers (Bielik, LFM3): float32, jeden BOS przed kontekstem jak u Slayera."""

    def __init__(self, katalog, device):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.tok = AutoTokenizer.from_pretrained(katalog, trust_remote_code=True)
        self.m = AutoModelForCausalLM.from_pretrained(katalog, dtype=torch.float32, trust_remote_code=True).to(device).eval()
        self.device = device
        bos = self.tok.bos_token_id if self.tok.bos_token_id is not None else self.tok.eos_token_id
        self.prefiks, self.prefiks_pusty = [bos], [bos]
        self.pad = self.tok.pad_token_id if self.tok.pad_token_id is not None else bos
        self.max_len = min(getattr(self.m.config, "max_position_embeddings", 2048), 4096)

    def encode(self, s):
        return self.tok(s, add_special_tokens=False).input_ids

    @torch.no_grad()
    def ukryte(self, ids):
        return self.m.base_model(ids).last_hidden_state

    @torch.no_grad()
    def glowa(self, h):
        return self.m.get_output_embeddings()(h).float()

    @torch.no_grad()
    def logits(self, ids):
        return self.m(ids).logits.float()


def zbuduj_model(katalog, device):
    cfg = json.loads((Path(katalog) / "config.json").read_text())
    return ModelSlayer(katalog, device) if "n_embd" in cfg and "model_type" not in cfg else ModelHFBos(katalog, device)


# ---------------------------------------------------------------- dane

def dane_pl(zip_sciezka):
    with zipfile.ZipFile(zip_sciezka) as z:
        linie = z.read(ZIP_PLIK, pwd=ZIP_HASLO).decode("utf-8").splitlines()
    return [json.loads(l) for l in linie if l.strip()]


def dane_en(tylko_pl=False):
    import pandas as pd
    from huggingface_hub import hf_hub_download
    p = hf_hub_download(EWOK_REPO, "data/test/ewok-core-1.0.parquet", repo_type="dataset", revision=EWOK_REW)
    df = pd.read_parquet(p)
    rek = [{"id": f"ewok-en-{i:04d}", "source_id": i, **r} for i, r in enumerate(df.to_dict("records"))]
    return rek[:625] if tylko_pl else rek


def rekordy(nazwa, zip_sciezka=None):
    if nazwa == "pl":
        return dane_pl(zip_sciezka)
    return dane_en(tylko_pl=nazwa == "en625")


# ---------------------------------------------------------------- liczenie

def licz(model, recs, plik, porcja=128, batch=32):
    gotowe = set()
    if plik.exists():
        gotowe = {json.loads(l)["id"] for l in plik.read_text().splitlines() if l.strip()}
    recs = [r for r in recs if r["id"] not in gotowe]
    t0 = time.time()
    for s in range(0, len(recs), porcja):
        czesc = recs[s:s + porcja]
        pary = []
        for r in czesc:
            for c in ("Context1", "Context2"):
                for t in ("Target1", "Target2"):
                    pary.append(para(model, r[c], " " + r[t]))
            for t in ("Target1", "Target2"):
                pary.append(para(model, "", r[t]))
        ll = licz_logliki(model, pary, batch)
        with open(plik, "a", encoding="utf-8") as f:
            for j, r in enumerate(czesc):
                w = ll[6 * j:6 * j + 6]
                f.write(json.dumps({"id": r["id"], "source_id": r["source_id"],
                                    "ll": [[w[0][0], w[1][0]], [w[2][0], w[3][0]]],
                                    "bezw": [w[4][0], w[5][0]],
                                    "ntok": [w[0][1], w[1][1]]}) + "\n")
        print(f"[{plik.stem}] {s + len(czesc)}/{len(recs)}  {time.time() - t0:.0f}s", flush=True)


def cmd_licz(a):
    model = zbuduj_model(a.model, a.device)
    wyj = Path(a.wyjscie)
    wyj.mkdir(parents=True, exist_ok=True)
    for nazwa in a.dane.split(","):
        licz(model, rekordy(nazwa, a.zip), wyj / f"{nazwa}.jsonl", batch=a.batch)


# ---------------------------------------------------------------- ocena

def ocen(w):
    """Oceny jednego rekordu; ll[c][t] = log P(T_t | C_c)."""
    ll, b = w["ll"], w["bezw"]
    s1, s2 = ll[0][0] > ll[1][0], ll[1][1] > ll[0][1]
    k1, k2 = ll[0][0] > ll[0][1], ll[1][1] > ll[1][0]
    p1, p2 = ll[0][0] - b[0] > ll[0][1] - b[1], ll[1][1] - b[1] > ll[1][0] - b[0]
    return {"ewok": (s1 + s2) / 2, "oba": float(s1 and s2),
            "kontekst_staly": (k1 + k2) / 2, "kontekst_staly_pmi": (p1 + p2) / 2,
            # przy C1 i C2 wygrywa to samo zdanie; remis T1 = T2 to brak wyboru, nie wybór T2
            "staly_target": float(ll[0][0] != ll[0][1] and ll[1][0] != ll[1][1] and k1 != k2),
            # o ile nat T1 jest bardziej prawdopodobne po C1 niż po C2 (i symetrycznie dla T2): siła sygnału
            "margines": ((ll[0][0] - ll[1][0]) + (ll[1][1] - ll[0][1])) / 2}


def wczytaj(plik):
    return {w["id"]: w for w in map(json.loads, plik.read_text().splitlines()) if w}


def szablony(recs_en, prog=0.3):
    """source_id -> id szablonu. EWoK wypełnia szablon kilkoma zestawami imion/obiektów (zwykle 5), a te
    rekordy nie są niezależne. Szablon odtwarzamy z EN: w obrębie (para pojęć, domena) słowa obecne w mniej
    niż `prog` rekordów to wypełnienia i maskujemy je (prog 0,3 daje 130 szablonów na 625 rekordów PL)."""
    import re
    tok = lambda s: re.findall(r"[A-Za-z']+", s)
    pola = ("Context1", "Context2", "Target1", "Target2")
    grupy = defaultdict(list)
    for r in recs_en:
        grupy[(r["ConceptA"], r["ConceptB"], r["Domain"])].append(r)
    klucze = {}
    for g, xs in grupy.items():
        df = Counter(w for x in xs for w in set(tok(" ".join(x[p] for p in pola))))
        for x in xs:
            klucze[x["source_id"]] = (g,) + tuple(" ".join(w if df[w] >= prog * len(xs) else "_" for w in tok(x[p])) for p in pola)
    numer = {k: i for i, k in enumerate(sorted(set(klucze.values())))}
    return {s: numer[k] for s, k in klucze.items()}


def _sumy_klastrow(wartosci, klastry):
    sumy, liczby = defaultdict(float), Counter()
    for v, k in zip(wartosci, klastry):
        sumy[k] += v
        liczby[k] += 1
    ks = sorted(sumy)
    return np.array([sumy[k] for k in ks]), np.array([liczby[k] for k in ks], dtype=float)


def srednia_klastrowa(wartosci, klastry, seed=SEED, powtorzenia=POWTORZENIA):
    """Średnia po rekordach z CI95 z bootstrapu po szablonach (losujemy całe szablony, nie rekordy)."""
    s, n = _sumy_klastrow(wartosci, klastry)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(s), size=(powtorzenia, len(s)))
    sr = s[idx].sum(1) / n[idx].sum(1)
    lo, hi = np.percentile(sr, [2.5, 97.5])
    return {"value": float(s.sum() / n.sum()), "n": int(n.sum()), "n_szablonow": len(s), "ci95": [float(lo), float(hi)]}


def test_permutacyjny(roznice, seed=SEED, powtorzenia=POWTORZENIA, klastry=None):
    """Sparowany test permutacyjny (losowe zmiany znaku różnic), dwustronny, jak kontrasty Space.
    Z `klastry` znak zmienia się dla całego szablonu naraz (rekordy jednego szablonu nie są niezależne)."""
    d = np.asarray(roznice, dtype=float)
    if klastry is not None:
        d, _ = _sumy_klastrow(d, klastry)
    obs = abs(d.mean())
    rng = np.random.default_rng(seed)
    znaki = rng.choice([-1.0, 1.0], size=(powtorzenia, len(d)))
    return float(((np.abs((znaki * d).mean(axis=1)) >= obs - 1e-12).sum() + 1) / (powtorzenia + 1))


def holm(pv):
    kol = sorted(range(len(pv)), key=lambda i: pv[i])
    out, mx = [None] * len(pv), 0.0
    for r, i in enumerate(kol):
        mx = max(mx, min(1.0, (len(pv) - r) * pv[i]))
        out[i] = mx
    return out


def podsumuj(oceny, meta, grupy=("Domain", "ConceptA", "ContextType", "ContextDiff", "TargetDiff"), szabl=None):
    wynik = {m: srednia_z_niepewnoscia([o[m] for o in oceny.values()])
             for m in ("ewok", "oba", "kontekst_staly", "kontekst_staly_pmi", "staly_target", "margines")}
    if szabl:
        wynik["ewok_po_szablonach"] = srednia_klastrowa([o["ewok"] for o in oceny.values()], [szabl[w_id_src(i)] for i in oceny])
    for g in grupy:
        kosze = defaultdict(list)
        for i, o in oceny.items():
            klucz = meta[i][g] if g != "ConceptA" else f"{meta[i]['ConceptA']} / {meta[i]['ConceptB']}"
            kosze[klucz].append(o["ewok"])
        wynik[f"wg_{g}"] = {k: srednia_z_niepewnoscia(v) for k, v in sorted(kosze.items())}
    return wynik


def kontrast(a, b, nazwa_a, nazwa_b, szabl=None, a2=None, b2=None):
    """Różnica średnich `ewok` na wspólnych rekordach, CI z bootstrapu, p z testu permutacyjnego.

    Z `szabl` także CI i p po szablonach (`roznica_po_szablonach`, `p_po_szablonach`). Z `a2`, `b2`
    różnica różnic per rekord: (a − b) − (a2 − b2), np. (PL 1.06 − PL 1.00) − (EN 1.06 − EN 1.00)."""
    klucz = lambda k: w_id_src(k) if isinstance(k, str) else k
    wspolne = sorted(set(a) & set(b) & (set(a2) & set(b2) if a2 else set(a)))
    d = [a[k]["ewok"] - b[k]["ewok"] - ((a2[k]["ewok"] - b2[k]["ewok"]) if a2 else 0) for k in wspolne]
    out = {"a": nazwa_a, "b": nazwa_b, "n": len(d), "roznica": srednia_z_niepewnoscia(d), "p": test_permutacyjny(d),
           "a_lepszy": sum(x > 0 for x in d), "b_lepszy": sum(x < 0 for x in d)}
    if szabl:
        kl = [szabl[klucz(k)] for k in wspolne]
        out["roznica_po_szablonach"] = srednia_klastrowa(d, kl)
        out["p_po_szablonach"] = test_permutacyjny(d, klastry=kl)
    return out


def cmd_analiza(a):
    korzen = Path(a.wyniki)
    meta = {}
    pl = dane_pl(a.zip) if a.zip else []
    for r in pl:
        meta[r["id"]] = {**{k: r[k] for k in META}, "flaga": r["review_flags"][0] if r["review_flags"] else "brak"}
    en_recs = dane_en()
    for r in en_recs:
        meta[r["id"]] = {k: r[k] for k in META}
    szabl = szablony(en_recs)
    modele = sorted(p.name for p in korzen.iterdir() if p.is_dir())
    oceny = {m: {d: {i: ocen(w) for i, w in wczytaj(korzen / m / f"{d}.jsonl").items()}
                 for d in ("pl", "en625", "en") if (korzen / m / f"{d}.jsonl").exists()} for m in modele}
    for o in oceny.values():  # en625 = pierwsze 625 rekordów pełnego EN (te same source_id co PL)
        if "en" in o and "en625" not in o:
            o["en625"] = {i: v for i, v in o["en"].items() if w_id_src(i) < 625}
    raport = {"protokol": {"regula": "EWoK LOGPROBS, target stały: (s1+s2)/2, losowo 0,5", "separator": "C + ' ' + T",
                           "bos": "jeden BOS (Slayer <|endoftext|>, HF bos_token)", "dtype": "float32",
                           "ewok_en_rewizja": EWOK_REW, "bootstrap": {"powtorzenia": POWTORZENIA, "seed": SEED},
                           "szablony": {"pl_n_szablonow": len({szabl[s] for s in range(625)}),
                                        "en_n_szablonow": len(set(szabl.values())), "prog_wypelnien": 0.3}},
              "modele": {}, "kontrasty": [], "do_przegladu": {}}
    for m in modele:
        raport["modele"][m] = {}
        for d, o in oceny[m].items():
            grupy = ("Domain", "ConceptA", "ContextType", "ContextDiff", "TargetDiff") + (("flaga",) if d == "pl" else ())
            raport["modele"][m][d] = podsumuj(o, meta, grupy, szabl)
    # kontrasty: PL vs EN na tych samych source_id, kolejne wersje Slayera, Slayer 1.06 vs pozostałe
    po_zrodle = {m: {d: {w_id_src(i): v for i, v in o.items()} for d, o in oceny[m].items()} for m in modele}
    K = lambda rodzina, *args, **kw: raport["kontrasty"].append({"rodzina": rodzina, **kontrast(*args, szabl=szabl, **kw)})
    for m in modele:
        if {"pl", "en625"} <= set(po_zrodle[m]):
            K("PL vs EN", po_zrodle[m]["pl"], po_zrodle[m]["en625"], f"{m} PL", f"{m} EN")
    slayery = [m for m in modele if m.startswith("Slayer1B-")]
    for x, y in zip(slayery, slayery[1:]):
        K("Slayer kolejne", oceny[y]["pl"], oceny[x]["pl"], y, x)
    if len(slayery) > 1:
        s1, s0 = slayery[-1], slayery[0]
        for d in ("pl", "en625", "en"):
            K(f"Slayer 1.06 vs 1.00 ({d})", oceny[s1][d], oceny[s0][d], s1, s0)
        # czy przyrost po polsku jest mniejszy niż po angielsku na tych samych rekordach
        K("Slayer 1.06 vs 1.00: PL − EN625 (różnica różnic)", po_zrodle[s1]["pl"], po_zrodle[s0]["pl"], s1, s0,
          a2=po_zrodle[s1]["en625"], b2=po_zrodle[s0]["en625"])
    for m in modele:
        if m not in slayery and slayery:
            K("Inne vs Slayer 1.06 (pl)", oceny[m]["pl"], oceny[slayery[-1]]["pl"], m, slayery[-1])
    for rodzina in {k["rodzina"] for k in raport["kontrasty"]}:
        ks = [k for k in raport["kontrasty"] if k["rodzina"] == rodzina]
        for k, p, ps in zip(ks, holm([k["p"] for k in ks]), holm([k["p_po_szablonach"] for k in ks])):
            k["p_holm"], k["p_holm_po_szablonach"] = p, ps
    # kandydaci do przeglądu tłumaczenia, w obie strony. Odniesieniem są tylko modele spoza rodziny Slayera
    # (Slayer jest po angielsku blisko losowego, więc średnia po wszystkich modelach tłumiłaby sygnał).
    if pl:
        ref = [m for m in modele if m not in slayery and "en625" in po_zrodle[m]]
        raport["protokol"]["do_przegladu"] = {"modele": ref, "prog": 0.5}
        for kier in ("trudniejsze_po_pl", "latwiejsze_po_pl"):
            raport["do_przegladu"][kier] = []
        for r in pl:
            s = r["source_id"]
            en = float(np.mean([po_zrodle[m]["en625"][s]["ewok"] for m in ref]))
            plw = float(np.mean([po_zrodle[m]["pl"][s]["ewok"] for m in ref]))
            if abs(en - plw) >= 0.5:
                raport["do_przegladu"]["trudniejsze_po_pl" if en > plw else "latwiejsze_po_pl"].append(
                    {"id": r["id"], "source_id": s, "szablon": szabl[s], "en": en, "pl": plw, "flaga": meta[r["id"]]["flaga"]})
    korzen.joinpath("raport_ewok.json").write_text(json.dumps(raport, indent=1, ensure_ascii=False), encoding="utf-8")
    korzen.joinpath("raport_ewok.md").write_text(tabela_md(raport), encoding="utf-8")
    print(tabela_md(raport))


def w_id_src(i):
    return int(i.rsplit("-", 1)[1]) - 1 if i.startswith("ewok-pl-") else int(i.rsplit("-", 1)[1])


def zaokr(x, miejsca=1, znak=False):
    """Zaokrąglenie połówek w górę na wartości dziesiętnej (0,575·100 to w float 57,4999…, a ma wyjść 58)."""
    from decimal import ROUND_HALF_UP, Decimal
    d = Decimal(repr(round(x, 10))).quantize(Decimal(1).scaleb(-miejsca), rounding=ROUND_HALF_UP)
    return f"{d:+}" if znak else f"{d}"


def _f(m):
    if m is None or m.get("value") is None:
        return "—"
    lo, hi = m["ci95"]
    return f"{zaokr(m['value'] * 100)} [{zaokr(lo * 100)}, {zaokr(hi * 100)}]"


def _tab_grup(r, modele, zbior, grupa, tytul):
    out = ["", tytul, "", "| grupa | n | " + " | ".join(modele) + " |", "|---|---|" + "---|" * len(modele)]
    for gr, v in r["modele"][modele[0]][zbior][grupa].items():
        out.append(f"| {gr} | {v['n']} | " + " | ".join(zaokr(r["modele"][m][zbior][grupa][gr]["value"] * 100, 0) for m in modele) + " |")
    return out


def tabela_md(r):
    out = ["# EWoK-PL: wyniki", "",
           "Wynik EWoK w % (losowo 50). CI95: bootstrap po rekordach oraz po szablonach (rekordy jednego szablonu nie są "
           "niezależne, ten przedział jest właściwy). `oba` = obie pary trafione (25 tylko przy niezależnych porównaniach).", "",
           "| model | PL ewok (n=625) | PL CI po szablonach | PL oba | EN te same 625 | EN pełny (4374) | PL stały target | EN stały target |",
           "|---|---|---|---|---|---|---|---|"]
    for m, d in r["modele"].items():
        g = lambda z, k: _f(d[z].get(k)) if z in d else "—"
        ci = d["pl"]["ewok_po_szablonach"]["ci95"] if "pl" in d else None
        out.append(f"| {m} | {g('pl', 'ewok')} | {f'[{zaokr(ci[0] * 100)}, {zaokr(ci[1] * 100)}]' if ci else '—'} | "
                   f"{g('pl', 'oba')} | {g('en625', 'ewok')} | {g('en', 'ewok')} | {g('pl', 'staly_target')} | {g('en', 'staly_target')} |")
    modele = [m for m in r["modele"] if "pl" in r["modele"][m]]
    if modele:
        out += _tab_grup(r, modele, "pl", "wg_ConceptA", "## PL wg pary pojęć")
        out += _tab_grup(r, modele, "en625", "wg_ConceptA", "## EN, te same 625 rekordów, wg pary pojęć")
    z_en = [m for m in r["modele"] if "en" in r["modele"][m]]
    if z_en:
        out += _tab_grup(r, z_en, "en", "wg_Domain", "## EN pełny wg domeny")
    out += ["", "## Kontrasty (różnica punktów ewok ×100, sparowany test permutacyjny, Holm w rodzinie)", "",
            "| rodzina | A | B | n | A−B | CI95 po rekordach | CI95 po szablonach | p | p po szablonach | p_holm po szablonach |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for k in r["kontrasty"]:
        d, ds = k["roznica"], k["roznica_po_szablonach"]
        ci = lambda c: f"[{zaokr(c[0] * 100, znak=True)}, {zaokr(c[1] * 100, znak=True)}]"
        out.append(f"| {k['rodzina']} | {k['a']} | {k['b']} | {k['n']} | {zaokr(d['value'] * 100, znak=True)} | {ci(d['ci95'])} | "
                   f"{ci(ds['ci95'])} | {k['p']:.4f} | {k['p_po_szablonach']:.4f} | {k['p_holm_po_szablonach']:.4f} |")
    pr = r["protokol"].get("do_przegladu", {})
    for kier, lista in r["do_przegladu"].items():
        out += ["", f"## Do przeglądu tłumaczenia, {kier.replace('_', ' ')}: {len(lista)} rekordów "
                f"(|EN − PL| ≥ {pr.get('prog')} średnio po {', '.join(pr.get('modele', []))})", "",
                ", ".join(x["id"] for x in lista) or "—"]
    return "\n".join(out) + "\n"


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("licz")
    l.add_argument("--model", required=True); l.add_argument("--dane", default="pl,en")
    l.add_argument("--zip"); l.add_argument("--wyjscie", required=True)
    l.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    l.add_argument("--batch", type=int, default=32)
    an = sub.add_parser("analiza")
    an.add_argument("--wyniki", required=True); an.add_argument("--zip")
    a = p.parse_args()
    {"licz": cmd_licz, "analiza": cmd_analiza}[a.cmd](a)


if __name__ == "__main__":
    main()
