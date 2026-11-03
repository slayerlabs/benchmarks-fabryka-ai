"""BLiMP: our scorer (common/hipoteza_formatu.py + benchmarks/blimp/blimp.py) against lm-eval 0.4.9.1, etap C.

Sample tests/dane/blimp_zgodnosc.json (benchmarks/blimp/lm_eval_compare.py sample): pairs 0 and 500 of every
paradigm plus the 7 pairs with identical sentences, for Pythia-1B v0 @ step143000 and Slayer 1.06, with the
log-likelihoods and decisions of lm-eval (`--log_samples`, LM_EVAL_PROTOCOL.md P2, P3), ours (P1 and the repo
file of Slayer 1.06), and the token ids lm-eval feeds the model. No network, no weights.
Run: python tests/test_blimp_zgodnosc.py (or pytest)."""
import json
import math
import sys
from pathlib import Path

import pytest

KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN / "benchmarks" / "blimp"))
sys.path.insert(0, str(KORZEN / "common"))
import blimp as B  # noqa: E402

PROBKA = json.loads((Path(__file__).resolve().parent / "dane" / "blimp_zgodnosc.json").read_text())
MODELE = sorted(PROBKA["models"])
MIN_ZGODNOSC = 0.99  # METODOLOGIA.md, etap C


def dokumenty():
    return [{"id": p["id"], "grupa": p["grupa"], "zjawisko": p["zjawisko"], "opcje": p["opcje"], "gold": 0}
            for p in PROBKA["pairs"]]


def test_probka_kompletna():
    d = dokumenty()
    po = {}
    for x in d:
        po[x["grupa"]] = po.get(x["grupa"], 0) + 1
    assert len(po) == 67 and min(po.values()) >= 2 and len({x["id"] for x in d}) == len(d)
    assert sum(x["opcje"][0] == x["opcje"][1] for x in d) == 7  # all pairs with identical sentences in BLiMP
    assert MODELE == ["pythia-1b-v0", "slayer-1.06"] and PROBKA["lm_eval"] == "0.4.9.1"
    for m in MODELE:
        assert set(PROBKA["models"][m]["rows"]) == {x["id"] for x in d}


@pytest.mark.parametrize("model", MODELE)
def test_decyzje_lm_eval_to_argmax_jego_logprob(model):
    """The stored lm-eval decision is argmax over [good, bad] of its own log-likelihoods, a tie picking good."""
    for r in PROBKA["models"][model]["rows"].values():
        ll = r["ll_lm_eval"]
        assert r["acc_lm_eval"] == (1 if ll[0] >= ll[1] else 0)


@pytest.mark.parametrize("model", MODELE)
def test_nasze_decyzje_zgodne_z_lm_eval(model):
    """Our decision rule (blimp.trafienie_pary) on our log-likelihoods agrees with lm-eval on >= 99% of the pairs."""
    rows = PROBKA["models"][model]["rows"]
    d = dokumenty()
    zgodne = sum(B.trafienie_pary(x, {"ll": rows[x["id"]]["ll_ours"]}) == rows[x["id"]]["acc_lm_eval"] for x in d)
    assert zgodne / len(d) >= MIN_ZGODNOSC, f"{model}: {zgodne}/{len(d)}"


@pytest.mark.parametrize("model", MODELE)
def test_agregacja_jak_grupa_blimp_lm_eval(model):
    """On lm-eval's own log-likelihoods our statistics give lm-eval's group value: mean of the paradigm means of
    `acc` (group `blimp`, weight_by_size False). Fails on another tie rule or a pair-weighted mean."""
    rows = PROBKA["models"][model]["rows"]
    d = [x for x in dokumenty() if x["opcje"][0] != x["opcje"][1]]  # identical sentences: lm-eval ll tie only by noise
    po = {}
    for x in d:
        po.setdefault(x["grupa"], []).append(rows[x["id"]]["acc_lm_eval"])
    oczek = sum(sum(v) / len(v) for v in po.values()) / len(po)
    wiersze = {x["id"]: {"ll": rows[x["id"]]["ll_lm_eval"]} for x in d}
    assert math.isclose(B.statystyki_modelu(wiersze, d, bootstrap=False)["acc"], oczek, rel_tol=1e-12)
    traf = [B.trafienie_pary(x, wiersze[x["id"]]) for x in d]
    assert math.isclose(B.wartosc_grupy(traf, [x["grupa"] for x in d]), oczek, rel_tol=1e-12)


def _model_pythii(monkeypatch, m):
    """ModelHF built by its own __init__ on a stub tokenizer that returns lm-eval's token ids for each continuation."""
    transformers = pytest.importorskip("transformers")
    import hipoteza_formatu as H
    tokeny = {}
    for p in PROBKA["pairs"]:
        for zdanie, (_, cont) in zip(p["opcje"], m["rows"][p["id"]]["lm_eval_tokens"]):
            tokeny[" " + zdanie] = cont

    class Tok:
        bos_token_id, eos_token_id = m["bos"], m["eos"]

        def __call__(self, s, add_special_tokens=True):
            return type("Enc", (), {"input_ids": ([self.bos_token_id] if add_special_tokens else []) + tokeny[s]})

    class BezWag:
        config = type("C", (), {"max_position_embeddings": 2048})()

        def to(self, *_):
            return self

        def eval(self):
            return self

    monkeypatch.setattr(transformers.AutoTokenizer, "from_pretrained", staticmethod(lambda *a, **k: Tok()))
    monkeypatch.setattr(transformers.AutoModelForCausalLM, "from_pretrained", staticmethod(lambda *a, **k: BezWag()))
    return H.ModelHF("brak", "cpu")


def _model_slayera(monkeypatch, m):
    """ModelSlayer built by its own __init__ on a stub Slayer (BOS from slayer_model) with lm-eval's token ids."""
    pytest.importorskip("torch")
    import hipoteza_formatu as H
    import slayer_model
    tokeny = {}
    for p in PROBKA["pairs"]:
        for zdanie, (_, cont) in zip(p["opcje"], m["rows"][p["id"]]["lm_eval_tokens"]):
            tokeny[" " + zdanie] = cont

    class BezWag:
        bos, blok = slayer_model.Slayer.BOS, 4096

        def encode(self, s):
            return tokeny[s]

    monkeypatch.setattr(slayer_model, "Slayer", lambda katalog, device: BezWag())
    return H.ModelSlayer("brak", "cpu")


@pytest.mark.parametrize("model", MODELE)
def test_kodowanie_par_jak_lm_eval(monkeypatch, model):
    """Our pair encoding (prompt_para + para, prefix from the model class) gives exactly the context and continuation
    ids lm-eval fed the model: one prefix token = lm-eval prefix_token_id, then " " + sentence. Fails on another
    BOS/EOS rule (ModelHF or ModelSlayer), a missing space or a changed split of context and continuation."""
    import hipoteza_formatu as H
    m = PROBKA["models"][model]
    ours = (_model_pythii if model == "pythia-1b-v0" else _model_slayera)(monkeypatch, m)
    assert ours.prefiks_pusty == [m["prefix_token_id"]]
    for p in PROBKA["pairs"]:
        ctx, konty = H.prompt_para({"opcje": p["opcje"]})
        nasze = [list(map(list, H.para(ours, ctx, c))) for c in konty]
        assert nasze == m["rows"][p["id"]]["lm_eval_tokens"], p["id"]


@pytest.mark.parametrize("model", MODELE)
def test_liczba_tokenow_naszego_przebiegu_jak_lm_eval(model):
    """Our stored run scored as many continuation tokens per sentence as lm-eval encodes (a run with another
    tokenization or without the space shows up here even when its decisions agree)."""
    for r in PROBKA["models"][model]["rows"].values():
        assert r["ntok_ours"] == [len(cont) for _, cont in r["lm_eval_tokens"]]


def test_lm_eval_compare_wiersz_i_zgodnosc():
    """lm_eval_compare: a --log_samples record (log-likelihoods as strings, as lm-eval 0.4.9.1 writes them) -> our id;
    agreement counts the pairs whose decisions differ, accuracy is the mean of paradigm means."""
    import lm_eval_compare as C
    s = {"doc": {"UID": "adjunct_island", "pair_id": 7}, "filtered_resps": [["-3.5", "False"], ["-2.0", "False"]],
         "acc": 0.0}
    assert C.sample_row(s) == {"id": "blimp_adjunct_island/7", "ll": [-3.5, -2.0], "acc": 0}
    d = dokumenty()[:6]
    ours = {x["id"]: {"ll": [-1.0, -2.0]} for x in d}
    ref = {x["id"]: {"ll": [-1.0, -2.0], "acc": 1} for x in d}
    ref[d[2]["id"]] = {"ll": [-2.0, -1.0], "acc": 0}
    ag = C.agreement(ours, ref, d, partial=True)
    assert ag["n"] == 6 and ag["agree"] == 5 and [x["id"] for x in ag["disagreements"]] == [d[2]["id"]]
    assert ag["max_abs_dll"] == 1.0 and math.isclose(ag["acc_ours"], 1.0)
    po = {}
    for x in d:
        po.setdefault(x["grupa"], []).append(0 if x["id"] == d[2]["id"] else 1)
    assert math.isclose(ag["acc_lm_eval"], sum(sum(v) / len(v) for v in po.values()) / len(po))
    with pytest.raises(SystemExit):  # the full comparison needs every pair on both sides
        C.agreement(ours, ref, dokumenty(), partial=False)


def test_lm_eval_compare_trafnosc_srednia_paradygmatow_przy_roznej_liczbie_par():
    """accuracy and agreement: equal weight per paradigm (group `blimp`, weight_by_size False), also when the
    paradigms have different numbers of pairs (a --partial run, a paradigm cut short). Pair-weighted: 0.25."""
    import lm_eval_compare as C
    d = ([{"id": "blimp_a/0", "grupa": "a", "opcje": ["x", "y"]}]
         + [{"id": f"blimp_b/{i}", "grupa": "b", "opcje": ["x", "y"]} for i in range(3)])
    hits = {"blimp_a/0": 1, "blimp_b/0": 0, "blimp_b/1": 0, "blimp_b/2": 0}
    assert math.isclose(C.accuracy(hits, d)["acc"], 0.5)
    ours = {x["id"]: {"ll": [-1.0, -2.0] if hits[x["id"]] else [-2.0, -1.0]} for x in d}
    ref = {x["id"]: {**ours[x["id"]], "acc": hits[x["id"]]} for x in d}
    ag = C.agreement(ours, ref, d, partial=True)
    assert ag["agree"] == 4 and math.isclose(ag["acc_ours"], 0.5) and math.isclose(ag["acc_lm_eval"], 0.5)


def test_lm_eval_compare_sprawdza_sha256_wejsc_przed_liczeniem(tmp_path):
    """check_inputs: a changed, missing or unlisted input stops compare before anything is computed."""
    import hashlib
    import lm_eval_compare as C
    for n in C.INPUTS:
        (tmp_path / n).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / n).write_bytes(n.encode())
    repo = tmp_path / "repo.jsonl.gz"
    repo.write_bytes(b"repo")
    h = {n: hashlib.sha256(n.encode()).hexdigest() for n in C.INPUTS}
    manifest = tmp_path / C.MANIFEST
    manifest.write_text("".join(f"{v}  ./{n}\n" for n, v in h.items()))
    rh = hashlib.sha256(b"repo").hexdigest()
    assert C.check_inputs(tmp_path, manifest, repo, rh) == {**h, "repo.jsonl.gz": rh}
    with pytest.raises(SystemExit, match="repo.jsonl.gz: sha256"):
        C.check_inputs(tmp_path, manifest, repo, "0" * 64)
    (tmp_path / C.INPUTS[1]).write_bytes(b"changed after the measurement")
    with pytest.raises(SystemExit, match=C.INPUTS[1]):
        C.check_inputs(tmp_path, manifest, repo, rh)
    (tmp_path / C.OPTIONAL_INPUTS[0]).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / C.OPTIONAL_INPUTS[0]).write_bytes(b"p4")
    with pytest.raises(SystemExit, match="not listed"):
        C.check_inputs(tmp_path, manifest, repo, rh)


def test_lm_eval_compare_manifest_w_repo_pasuje_do_plikow():
    """The committed inputs of results/lm_eval_agreement.json match results/lm-eval/SHA256SUMS and the pinned
    sha256 of the Slayer 1.06 repo file."""
    import lm_eval_compare as C
    R = KORZEN / "benchmarks" / "blimp" / "results"
    assert set(C.check_inputs(R, R / C.MANIFEST)) == {*C.INPUTS, *C.OPTIONAL_INPUTS,
                                                       "benchmarks/blimp/results/1.06/blimp.jsonl.gz"}


def test_lm_eval_agreement_bez_sciezek_bezwzglednych():
    """The committed lm_eval_agreement.json names its inputs by paths relative to the repo, not to a checkout."""
    zapis = json.loads((KORZEN / "benchmarks" / "blimp" / "results" / "lm_eval_agreement.json").read_text())
    klucze = list(zapis["inputs_sha256"])
    assert len(klucze) == 5 and not [k for k in klucze if Path(k).is_absolute() or ".." in Path(k).parts], klucze


def test_lm_eval_compare_warunki_protokolu():
    """(a) +-2 points or 2 SE when larger; (b)/(c) >= 99% same decisions and |difference| <= 1 SE of lm-eval."""
    import lm_eval_compare as C
    assert C.verdict_published(C.PUBLISHED_V0 + 0.0199, 0.001)["pass"]
    assert not C.verdict_published(C.PUBLISHED_V0 - 0.0201, 0.001)["pass"]
    assert C.verdict_published(C.PUBLISHED_V0 + 0.03, 0.016)["pass"]  # 2 SE = 0.032 > 2 points
    ok = {"share": 0.99, "diff": 0.001, "se_lm_eval": 0.0013}
    assert C.verdict_agreement(ok)["pass"]
    assert not C.verdict_agreement({**ok, "share": 0.9899})["pass"]
    assert not C.verdict_agreement({**ok, "diff": -0.0014})["pass"]
    assert C.sense(0.82) and not C.sense(1.0) and not C.sense(0.44)


def test_wzgledem_referencji_v0():
    """blimp.wzgledem_referencji: paradigms certain against v1, re-read against v0; a paradigm stays when it is
    certain and Holm-significant against both weights with the same sign."""
    def e(z, w="pewne"):
        return {"roznica": z / 100, "z": z, "werdykt": w}
    v1 = {"paradygmaty": {"a": e(10.0), "b": e(9.0), "c": e(-12.0), "d": e(1.0, "szum"), "e": e(3.1)}}
    v0 = {"ogolem": e(-3.0),
          "paradygmaty": {"a": e(11.0), "b": e(0.0, "szum"), "c": e(-10.0), "d": e(20.0), "e": e(3.08)}}
    for v in (v1, v0):  # 65 paradigms: Holm needs p <= 0.05 / 62 at the 4th rank, z = 3.08 (p = 0.0021) fails it
        v["paradygmaty"].update({f"n{i}": e(0.5, "szum") for i in range(60)})
    r = B.wzgledem_referencji(v1, v0)
    assert set(r["pewne_v1"]) == {"a", "b", "c", "e"}
    assert r["pewne_v1"]["a"]["zostaje"] and not r["pewne_v1"]["b"]["zostaje"]
    assert r["pewne_v1"]["e"]["v0"]["werdykt"] == "pewne" and not r["pewne_v1"]["e"]["v0"]["holm"]
    assert not r["pewne_v1"]["e"]["zostaje"]  # certain against both, not Holm: does not stay
    assert r["pewne_v1"]["c"] == {"v1": {"roznica": -0.12, "z": -12.0, "holm": True},
                                  "v0": {"roznica": -0.10, "z": -10.0, "werdykt": "pewne", "holm": True},
                                  "zostaje": True}
    assert r["liczby"] == {"slayer_pewne_v1": 3, "pythia_pewne_v1": 1, "slayer_pewne_v0": 3, "pythia_pewne_v0": 1,
                           "slayer_holm_v1": 2, "pythia_holm_v1": 1, "slayer_holm_v0": 2, "pythia_holm_v0": 1,
                           "slayer_zostaje": 1, "pythia_zostaje": 1}
    v0["paradygmaty"]["a"] = e(-11.0)  # certain, but the other sign: does not stay
    assert not B.wzgledem_referencji(v1, v0)["pewne_v1"]["a"]["zostaje"]
    k = B.kontrola_wobec_opublikowanej(B.REFERENCJA_PYTHIA["wartosc"] + 0.001)
    assert k["w_progu"] and math.isclose(k["roznica"], 0.001)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
