"""Czyste funkcje EWoK (benchmarks/ewok/ewok.py), bez sieci i bez wag.

Próbka `common/tests/data/ewok.jsonl` to 10 rekordów w formacie ewok-core-1.0 z wymyślonymi zdaniami (nie z EWoK,
TERMS_OF_USE) i log P jednego modelu. Uruchom: python tests/test_ewok.py (albo pytest).
"""
import gzip
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks" / "ewok"))
import ewok as E  # noqa: E402

SAMPLE = [json.loads(line) for line in (ROOT / "common" / "tests" / "data" / "ewok.jsonl").read_text(encoding="utf-8").splitlines()]
META = {f"r{r['source_id']}": {"source_id": r["source_id"], "Domain": r["Domain"]} for r in SAMPLE}


def scores(shift=0):
    """Scores of the sample model; `shift` > 0 makes a worse model by rotating the rows."""
    lls = [r["ll"] for r in SAMPLE]
    lls = lls[shift:] + lls[:shift]
    return {f"r{i}": E.evaluate({"ll": ll}) for i, ll in enumerate(lls)}


def test_obie_pary_trafione_daja_punkt():
    s = E.evaluate({"ll": [[-1.0, -5.0], [-3.0, -2.0]]})
    assert s == {"ewok": 1.0, "both": 1.0, "constant_target": 0.0}


def test_jedna_para_i_staly_target():
    # T1 wins after both contexts: half a point and a constant target
    s = E.evaluate({"ll": [[-1.0, -5.0], [-3.0, -6.0]]})
    assert s == {"ewok": 0.5, "both": 0.0, "constant_target": 1.0}


def test_remis_to_pudlo_i_jest_liczony():
    w = {"ll": [[-1.0, -1.0], [-1.0, -1.0]]}
    s = E.evaluate(w)
    assert s["ewok"] == 0.0 and s["constant_target"] == 0.0
    assert E.ties(w) == 2


def test_losowy_model_ma_0_5():
    # a model that always prefers T1, whatever the context, gets exactly one of the two comparisons
    assert E.evaluate({"ll": [[-1.0, -2.0], [-1.0, -2.0]]})["ewok"] == 0.0
    assert E.evaluate({"ll": [[-1.0, -2.0], [-1.5, -2.0]]})["ewok"] == 0.5


def test_szablony_maskuja_wypelnienia():
    t = E.templates(SAMPLE)
    assert len(set(t.values())) == 3
    assert t[0] == t[1] == t[2] and t[3] == t[4] == t[5] and t[6] == t[7] == t[8] == t[9]
    assert len({t[0], t[3], t[6]}) == 3


def test_srednia_po_szablonach():
    t = E.templates(SAMPLE)
    s = scores()
    m = E.cluster_mean([x["ewok"] for x in s.values()], [t[META[i]["source_id"]] for i in s], reps=2000)
    assert m["n"] == 10 and m["n_templates"] == 3
    assert abs(m["value"] - sum(x["ewok"] for x in s.values()) / 10) < 1e-12
    assert m["se"] > 0 and m["ci95"][0] <= m["value"] <= m["ci95"][1]


def test_podsumowanie_ma_metryki_i_domeny():
    out = E.summarize(scores(), META, E.templates(SAMPLE))
    assert set(E.METRICS) <= set(out)
    assert set(out["by_domain"]) == {"agent-properties", "spatial-relations"}
    assert out["ewok"]["n"] == 10


def test_kontrast_z_samym_soba_to_zero():
    t = E.templates(SAMPLE)
    k = E.contrast(scores(), scores(), "a", "a", META, t)
    assert k["diff"]["value"] == 0 and k["a_better"] == k["b_better"] == 0
    assert k["diff_by_template"]["verdict"] == "szum"


def test_kontrast_ma_znak_a_minus_b():
    t = E.templates(SAMPLE)
    a, b = scores(), scores(shift=3)
    k = E.contrast(a, b, "a", "b", META, t)
    expected = sum(a[i]["ewok"] - b[i]["ewok"] for i in a) / len(a)
    assert abs(k["diff_by_template"]["value"] - expected) < 1e-12
    assert k["diff_by_template"]["verdict"] in ("pewne", "prawdopodobne", "szum")


def test_werdykt_jak_bramka_liczb():
    assert E.verdict(3.0) == "pewne" and E.verdict(-2.0) == "prawdopodobne" and E.verdict(1.99) == "szum"


class _WordModel:
    """Word-level stand-in for a tokenizer; `bos` like a tokenizer whose add_special_tokens=True prepends BOS."""

    def __init__(self, bos):
        self.vocab, self.bos = {}, bos

    def encode_special(self, s):
        ids = [self.vocab.setdefault(w, len(self.vocab) + 10) for w in s.split()]
        return ([1] if self.bos else []) + ids


def test_para_autorow_bierze_bos_od_tokenizera():
    for bos in (False, True):
        m = _WordModel(bos)
        ctx, tgt = E.authors_pair(m, "Ann is hungry.", "Ann eats lunch.")
        assert ctx == m.encode_special("Ann is hungry.") and len(tgt) == 3
        assert (ctx[0] == 1) == bos


def test_maska_pad_jak_surprisal():
    # tiny random GPT-2 on CPU, no weights from the network: `authors` masks the pad logit before the softmax
    import torch
    from transformers import GPT2Config, GPT2LMHeadModel

    class Tiny:
        def __init__(self):
            torch.manual_seed(0)
            self.m = GPT2LMHeadModel(GPT2Config(n_layer=2, n_embd=32, n_head=2, vocab_size=50, n_positions=32,
                                                    bos_token_id=1, eos_token_id=1)).eval()
            self.device, self.pad, self.max_len, self.rule = "cpu", 0, 32, "authors"
            self.masked_id = lambda: 7

        def ukryte(self, ids):
            with torch.no_grad():
                return self.m.transformer(ids).last_hidden_state

        def glowa(self, h):
            with torch.no_grad():
                return self.m.lm_head(h).float()

    m = Tiny()
    pairs = [([3, 4, 5], [6, 8]), ([9, 2], [11, 12, 13])]
    got = E.logliks(m, pairs, batch=2)
    for (c, t), (v, n) in zip(pairs, got):
        with torch.no_grad():
            lg = m.m(torch.tensor([c + t])).logits[0].float()
        lg[:, 7] = -float("inf")
        lp = torch.log_softmax(lg, -1)
        ref = sum(lp[len(c) - 1 + i, tok].item() for i, tok in enumerate(t))
        assert n == len(t) and abs(v - ref) < 1e-4


def test_p_studenta_znane_wartosci():
    # tables of Student's t: two-sided p = 0.05 at t = 2.228, df = 10; for df = 2, p = 1 - t / sqrt(t^2 + 2)
    assert abs(E.p_student(2.228, 10) - 0.05) < 1e-4
    assert abs(E.p_student(3.0, 2) - (1 - 3.0 / (9.0 + 2) ** 0.5)) < 1e-9


def test_domeny_jako_klastry():
    # 3 domains: sd with ddof = 1 is 1, SE = 1/sqrt(3), t = 3.46 at df = 2, p = 0.074: noise, although |t| >= 3
    g = E.domain_clusters([1.0, 2.0, 3.0])
    assert g["k"] == 3 and g["df"] == 2 and g["value"] == 2.0
    assert abs(g["se"] - 3 ** -0.5) < 1e-12 and abs(g["t"] - 2 * 3 ** 0.5) < 1e-12
    assert abs(g["p"] - (1 - g["t"] / (g["t"] ** 2 + 2) ** 0.5)) < 1e-9
    assert g["verdict"] == "szum"


def test_zapis_odczyt_ocena():
    # pairs in the order of `record_pairs`: (C1,T1), (C1,T2), (C2,T1), (C2,T2), T1 and T2 without context
    recs = [{"id": "ewok-en-0000", "source_id": 0}, {"id": "ewok-en-0001", "source_id": 1}]
    ll = [(-1.0, 3), (-5.0, 4), (-3.0, 3), (-2.0, 4), (-9.0, 3), (-8.0, 4),
          (-1.0, 2), (-2.0, 5), (-3.0, 2), (-4.0, 5), (-7.0, 2), (-6.0, 5)]
    with tempfile.TemporaryDirectory() as d:
        E.write_rows(Path(d) / "ewok.jsonl", recs, ll)
        got = E.read_rows(Path(d) / "ewok.jsonl")
    assert got["ewok-en-0000"]["ll"] == [[-1.0, -5.0], [-3.0, -2.0]]
    assert got["ewok-en-0000"]["bezw"] == [-9.0, -8.0] and got["ewok-en-0000"]["ntok"] == [3, 4]
    assert E.evaluate(got["ewok-en-0000"]) == {"ewok": 1.0, "both": 1.0, "constant_target": 0.0}
    assert E.evaluate(got["ewok-en-0001"]) == {"ewok": 0.5, "both": 0.0, "constant_target": 1.0}


def test_wyniki_z_pliku_gz():
    rows = [{"id": f"ewok-en-{i:04d}", "source_id": i, "ll": r["ll"], "bezw": [-9.0, -9.0], "ntok": [3, 3]}
            for i, r in enumerate(SAMPLE)]
    text = "".join(json.dumps(r) + "\n" for r in rows)
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "ewok.jsonl.gz").write_bytes(gzip.compress(text.encode()))
        got = E.read_rows(Path(d) / "ewok.jsonl")
    assert list(got) == [r["id"] for r in rows] and got["ewok-en-0003"]["ll"] == SAMPLE[3]["ll"]


if __name__ == "__main__":
    for name, f in list(globals().items()):
        if name.startswith("test_"):
            f()
    print("OK")
