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
            "staly_target": float(k1 != k2),  # przy C1 i C2 wygrywa to samo zdanie
            # o ile nat T1 jest bardziej prawdopodobne po C1 niż po C2 (i symetrycznie dla T2): siła sygnału
            "margines": ((ll[0][0] - ll[1][0]) + (ll[1][1] - ll[0][1])) / 2}


def wczytaj(plik):
    return {w["id"]: w for w in map(json.loads, plik.read_text().splitlines()) if w}


def test_permutacyjny(roznice, seed=SEED, powtorzenia=POWTORZENIA):
    """Sparowany test permutacyjny (losowe zmiany znaku różnic per rekord), dwustronny, jak kontrasty Space."""
    d = np.asarray(roznice, dtype=float)
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


def podsumuj(oceny, meta, grupy=("Domain", "ConceptA", "ContextType", "ContextDiff", "TargetDiff")):
    wynik = {m: srednia_z_niepewnoscia([o[m] for o in oceny.values()])
             for m in ("ewok", "oba", "kontekst_staly", "kontekst_staly_pmi", "staly_target", "margines")}
    for g in grupy:
        kosze = defaultdict(list)
        for i, o in oceny.items():
            klucz = meta[i][g] if g != "ConceptA" else f"{meta[i]['ConceptA']} / {meta[i]['ConceptB']}"
            kosze[klucz].append(o["ewok"])
        wynik[f"wg_{g}"] = {k: srednia_z_niepewnoscia(v) for k, v in sorted(kosze.items())}
    return wynik


def kontrast(a, b, nazwa_a, nazwa_b, po="id"):
    """Różnica średnich `ewok` na wspólnych rekordach (klucz `po`), CI z bootstrapu, p z testu permutacyjnego."""
    wspolne = sorted(set(a) & set(b))
    d = [a[k]["ewok"] - b[k]["ewok"] for k in wspolne]
    return {"a": nazwa_a, "b": nazwa_b, "n": len(d), "roznica": srednia_z_niepewnoscia(d), "p": test_permutacyjny(d),
            "a_lepszy": sum(x > 0 for x in d), "b_lepszy": sum(x < 0 for x in d)}


def cmd_analiza(a):
    korzen = Path(a.wyniki)
    meta = {}
    pl = dane_pl(a.zip) if a.zip else []
    for r in pl:
        meta[r["id"]] = {**{k: r[k] for k in META}, "flaga": r["review_flags"][0] if r["review_flags"] else "brak"}
    for r in dane_en():
        meta[r["id"]] = {k: r[k] for k in META}
    modele = sorted(p.name for p in korzen.iterdir() if p.is_dir())
    oceny = {m: {d: {i: ocen(w) for i, w in wczytaj(korzen / m / f"{d}.jsonl").items()}
                 for d in ("pl", "en625", "en") if (korzen / m / f"{d}.jsonl").exists()} for m in modele}
    for o in oceny.values():  # en625 = pierwsze 625 rekordów pełnego EN (te same source_id co PL)
        if "en" in o and "en625" not in o:
            o["en625"] = {i: v for i, v in o["en"].items() if w_id_src(i) < 625}
    raport = {"protokol": {"regula": "EWoK LOGPROBS, target stały: (s1+s2)/2, losowo 0,5", "separator": "C + ' ' + T",
                           "bos": "jeden BOS (Slayer <|endoftext|>, HF bos_token)", "dtype": "float32",
                           "ewok_en_rewizja": EWOK_REW, "bootstrap": {"powtorzenia": POWTORZENIA, "seed": SEED}},
              "modele": {}, "kontrasty": [], "do_przegladu": []}
    for m in modele:
        raport["modele"][m] = {}
        for d, o in oceny[m].items():
            grupy = ("Domain", "ConceptA", "ContextType", "ContextDiff", "TargetDiff") + (("flaga",) if d == "pl" else ())
            raport["modele"][m][d] = podsumuj(o, meta, grupy)
    # kontrasty: PL vs EN na tych samych source_id, kolejne wersje Slayera, Slayer 1.06 vs pozostałe
    po_zrodle = {m: {d: {w_id_src(i): v for i, v in o.items()} for d, o in oceny[m].items()} for m in modele}
    for m in modele:
        if {"pl", "en625"} <= set(po_zrodle[m]):
            raport["kontrasty"].append({"rodzina": "PL vs EN", **kontrast(po_zrodle[m]["pl"], po_zrodle[m]["en625"], f"{m} PL", f"{m} EN")})
    slayery = [m for m in modele if m.startswith("Slayer1B-")]
    for x, y in zip(slayery, slayery[1:]):
        raport["kontrasty"].append({"rodzina": "Slayer kolejne", **kontrast(oceny[y]["pl"], oceny[x]["pl"], y, x)})
    if len(slayery) > 1:
        for d in ("pl", "en"):
            raport["kontrasty"].append({"rodzina": f"Slayer 1.06 vs 1.00 ({d})",
                                        **kontrast(oceny[slayery[-1]][d], oceny[slayery[0]][d], slayery[-1], slayery[0])})
    for m in modele:
        if m not in slayery and slayery:
            raport["kontrasty"].append({"rodzina": "Slayer vs inne", **kontrast(oceny[slayery[-1]]["pl"], oceny[m]["pl"], slayery[-1], m)})
    for rodzina in {k["rodzina"] for k in raport["kontrasty"]}:
        ks = [k for k in raport["kontrasty"] if k["rodzina"] == rodzina]
        for k, p in zip(ks, holm([k["p"] for k in ks])):
            k["p_holm"] = p
    # kandydaci do przeglądu tłumaczenia: rekord dobry po angielsku u większości modeli, zły po polsku
    if pl:
        z_en = [m for m in modele if "en625" in po_zrodle[m]]
        for r in pl:
            s = r["source_id"]
            en = np.mean([po_zrodle[m]["en625"][s]["ewok"] for m in z_en])
            plw = np.mean([po_zrodle[m]["pl"][s]["ewok"] for m in z_en])
            if en - plw >= 0.5:
                raport["do_przegladu"].append({"id": r["id"], "source_id": s, "en": float(en), "pl": float(plw),
                                               "flaga": meta[r["id"]]["flaga"]})
    korzen.joinpath("raport_ewok.json").write_text(json.dumps(raport, indent=1, ensure_ascii=False), encoding="utf-8")
    korzen.joinpath("raport_ewok.md").write_text(tabela_md(raport), encoding="utf-8")
    print(tabela_md(raport))


def w_id_src(i):
    return int(i.rsplit("-", 1)[1]) - 1 if i.startswith("ewok-pl-") else int(i.rsplit("-", 1)[1])


def _f(m, proc=True):
    if m is None or m.get("value") is None:
        return "—"
    k = 100 if proc else 1
    lo, hi = m["ci95"]
    return f"{m['value'] * k:.1f} [{lo * k:.1f}, {hi * k:.1f}]" if proc else f"{m['value']:.3f} [{lo:.3f}, {hi:.3f}]"


def tabela_md(r):
    out = ["# EWoK-PL: wyniki", "", "Wynik EWoK w % (losowo 50), CI95 bootstrap. `oba` = obie pary trafione (losowo 25).", "",
           "| model | PL ewok (n=625) | PL oba | EN te same 625 | EN pełny (4374) | PL kontekst stały | PL stały target |",
           "|---|---|---|---|---|---|---|"]
    for m, d in r["modele"].items():
        g = lambda z, k: _f(d[z][k]) if z in d else "—"
        out.append(f"| {m} | {g('pl', 'ewok')} | {g('pl', 'oba')} | {g('en625', 'ewok')} | {g('en', 'ewok')} | "
                   f"{g('pl', 'kontekst_staly')} | {g('pl', 'staly_target')} |")
    out += ["", "## PL wg pary pojęć", ""]
    modele = [m for m in r["modele"] if "pl" in r["modele"][m]]
    if modele:
        grupy = list(r["modele"][modele[0]]["pl"]["wg_ConceptA"])
        out += ["| para | n | " + " | ".join(modele) + " |", "|---|---|" + "---|" * len(modele)]
        for gr in grupy:
            n = r["modele"][modele[0]]["pl"]["wg_ConceptA"][gr]["n"]
            out.append(f"| {gr} | {n} | " + " | ".join(f"{r['modele'][m]['pl']['wg_ConceptA'][gr]['value'] * 100:.0f}" for m in modele) + " |")
    z_en = [m for m in r["modele"] if "en" in r["modele"][m]]
    if z_en:
        out += ["", "## EN pełny wg domeny (tło: gdzie model nie ma wiedzy)", "",
                "| domena | n | " + " | ".join(z_en) + " |", "|---|---|" + "---|" * len(z_en)]
        for gr, v in r["modele"][z_en[0]]["en"]["wg_Domain"].items():
            out.append(f"| {gr} | {v['n']} | " + " | ".join(f"{r['modele'][m]['en']['wg_Domain'][gr]['value'] * 100:.0f}" for m in z_en) + " |")
    out += ["", "## Kontrasty (różnica punktów ewok ×100, sparowany test permutacyjny, Holm w rodzinie)", "",
            "| rodzina | A | B | n | A−B | CI95 | p | p_holm |", "|---|---|---|---|---|---|---|---|"]
    for k in r["kontrasty"]:
        d = k["roznica"]
        out.append(f"| {k['rodzina']} | {k['a']} | {k['b']} | {k['n']} | {d['value'] * 100:+.1f} | "
                   f"[{d['ci95'][0] * 100:+.1f}, {d['ci95'][1] * 100:+.1f}] | {k['p']:.4f} | {k['p_holm']:.4f} |")
    out += ["", f"## Do przeglądu tłumaczenia: {len(r['do_przegladu'])} rekordów (EN − PL ≥ 0,5 średnio po modelach)", "",
            ", ".join(x["id"] for x in r["do_przegladu"]), ""]
    return "\n".join(out)


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
