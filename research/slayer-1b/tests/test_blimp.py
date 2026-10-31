"""BLiMP (slayer_eval/blimp.py + the `blimp` task of hipoteza_formatu.py), no network, no weights.
Run: python tests/test_blimp.py (or pytest)."""
import importlib.util
import math
import os
import sys
from pathlib import Path

KAT = Path(__file__).resolve().parent.parent / "slayer_eval"
sys.path.insert(0, str(KAT))
import blimp as B  # noqa: E402

PROBKA = KAT / "testy" / "dane" / "blimp.jsonl"


def docs():
    return B.wczytaj(PROBKA)


def wyniki(trafione):
    """{id: row} with log-likelihoods giving the requested hit (True) or miss (False) per id."""
    return {i: {"id": i, "ll": [-1.0, -2.0] if t else [-2.0, -1.0]} for i, t in trafione.items()}


def test_wczytaj_sortuje_paradygmaty_i_sklada_s_selection():
    d = docs()
    assert len(d) == 9
    assert [x["grupa"] for x in d][:4] == ["adjunct_island"] * 4  # sorted by paradigm, file order inside
    assert [x["id"] for x in d][:2] == ["blimp_adjunct_island/0", "blimp_adjunct_island/1"]
    assert all(x["gold"] == 0 and x["opcje"][0] == x["rekord"]["sentence_good"] for x in d)
    zj = {x["grupa"]: x["zjawisko"] for x in d}
    assert zj["animate_subject_passive"] == "argument_structure"  # HF "s-selection" -> paper group
    assert zj["regular_plural_subject_verb_agreement_1"] == "subject_verb_agreement"


def test_para_jak_lm_eval_pusty_kontekst_bos_i_spacja(monkeypatch):
    import pytest
    pytest.importorskip("torch")
    monkeypatch.setenv("BLIMP_DIR", str(PROBKA))
    import hipoteza_formatu as H

    class Stub:
        prefiks, prefiks_pusty = [], [0]

        def encode(self, s):
            return [ord(c) for c in s]

    dane = H.dokumenty("blimp")
    assert len(dane) == 9 and "rekord" not in dane[0]
    ctx, konty = H.ZADANIA["blimp"][1](dane[0])
    ce, co = H.para(Stub(), ctx, konty[0])
    assert ce == [0]  # exactly one unscored BOS/EOT
    assert co == [ord(c) for c in " " + dane[0]["opcje"][0]]  # target delimiter " " goes to the sentence


class AtrapaModelu:
    """Deterministic logits: hidden state = one-hot of the input token, head = fixed matrix W[V, V]."""

    def __init__(self, V=11, max_len=16):
        import torch
        g = torch.Generator().manual_seed(7)
        self.W = torch.randn(V, V, generator=g)
        self.V, self.max_len, self.pad, self.device = V, max_len, 0, "cpu"

    def ukryte(self, ids):
        import torch
        return torch.nn.functional.one_hot(ids, self.V).float()

    def glowa(self, h):
        return h @ self.W

    def oczekiwany(self, ce, co):
        """Sum of log p(token_t | token_{t-1}) over the continuation, computed directly from W."""
        import torch
        pelne = ce + co
        lp = torch.log_softmax(self.W, -1)
        return sum(lp[pelne[i - 1], pelne[i]].item() for i in range(len(ce), len(pelne)))


PARY_ATRAPY = [([0], [3, 4, 5]), ([0, 2], [7]), ([0], [1, 9, 9, 2, 6, 3]), ([0, 5, 5, 5], [8, 1])]


def test_licz_logliki_bierze_pozycje_kontynuacji():
    import pytest
    pytest.importorskip("torch")
    import hipoteza_formatu as H
    m = AtrapaModelu()
    wynik = H.licz_logliki(m, PARY_ATRAPY, batch=4)
    for (ce, co), (ll, n) in zip(PARY_ATRAPY, wynik):
        assert n == len(co) and math.isclose(ll, m.oczekiwany(ce, co), rel_tol=1e-5)


def test_licz_logliki_batch_1_rowny_batch_n_z_paddingiem():
    import pytest
    pytest.importorskip("torch")
    import hipoteza_formatu as H
    m = AtrapaModelu()
    jeden = H.licz_logliki(m, PARY_ATRAPY, batch=1)
    wiele = H.licz_logliki(m, PARY_ATRAPY, batch=3)  # different lengths in one batch: right padding
    assert all(math.isclose(a[0], b[0], rel_tol=1e-6) for a, b in zip(jeden, wiele))


def test_licz_logliki_odrzuca_za_dlugie_wejscie():
    import pytest
    pytest.importorskip("torch")
    import hipoteza_formatu as H
    m = AtrapaModelu(max_len=4)
    assert H.licz_logliki(m, [([0, 1], [2, 3, 4])], batch=1)  # 4 input tokens: fits
    with pytest.raises(ValueError):
        H.licz_logliki(m, [([0, 1], [2, 3, 4, 5])], batch=1)  # 5 > 4: rejected, not truncated
    # odrzucaj=True (licz_zadanie): the long input gets None, the others are still scored
    wynik = H.licz_logliki(m, [([0, 1], [2, 3, 4, 5]), ([0, 1], [2, 3, 4])], batch=2, odrzucaj=True)
    assert wynik[0] is None and math.isclose(wynik[1][0], m.oczekiwany([0, 1], [2, 3, 4]), rel_tol=1e-5)


def test_licz_zadanie_zapisuje_odrzucone_i_liczy_dalej(monkeypatch, tmp_path):
    """A document with an input over the context does not stop the run (arc_c_mc_25shot on Pythia: 64 of
    4687 over 2048): it goes to <task>.odrzucone.jsonl, the rest is scored, and blimp.py zbierz counts it."""
    import json
    import pytest
    pytest.importorskip("torch")
    monkeypatch.setenv("BLIMP_DIR", str(PROBKA))
    import hipoteza_formatu as H

    class Krotki(AtrapaModelu):
        prefiks, prefiks_pusty = [0], [0]

        def encode(self, s):
            return [ord(c) % 10 + 1 for c in s]

    docs = H.dokumenty("blimp")
    dl = {d["id"]: max(len(o) + 1 for o in d["opcje"]) for d in docs}  # " " + sentence, 1 BOS, minus 1 shift
    prog = sorted(dl.values())[len(dl) // 2]
    m = Krotki(max_len=prog)
    plik = tmp_path / "blimp.jsonl"
    H.licz_zadanie(m, "blimp", plik, batch=4, porcja=4)
    zapisane = [json.loads(l)["id"] for l in plik.read_text().splitlines()]
    odrzucone = [json.loads(l)["id"] for l in H.plik_odrzuconych(plik).read_text().splitlines()]
    assert sorted(odrzucone) == sorted(i for i, n in dl.items() if n > prog) and odrzucone
    assert sorted(zapisane + odrzucone) == sorted(dl) and not set(zapisane) & set(odrzucone)
    assert H.n_odrzuconych(plik) == len(odrzucone) and B.wczytaj_odrzucone(plik) == set(odrzucone)
    H.licz_zadanie(m, "blimp", plik, batch=4)  # resume: rejected ids are not tried again
    assert H.n_odrzuconych(plik) == len(odrzucone) and len(plik.read_text().splitlines()) == len(zapisane)


SLAYER_TOKENIZER_SHA = "0640d3bd3674d7a6e59c540d945a2ad275a12e1bcaeb6007c37a90751f9815dd"


def test_slayer_pusty_kontekst_to_bos_endoftext(monkeypatch):
    """ModelSlayer's empty context is [0], and 0 is <|endoftext|> in the Slayer tokenizer.json (no weights)."""
    import hashlib
    import pytest
    pytest.importorskip("torch")
    sciezka = Path(os.environ.get("SLAYER_TOKENIZER", os.path.expanduser(
        "~/.cache/huggingface/hub/models--SlayerLab--Slayer1B-1.06/snapshots/"
        "ef81be58742544ad32e1afab38db011fec209609/tokenizer.json")))
    if not sciezka.exists():
        # not a silent skip: the run lists it as XFAIL with the path it looked at. The file (2.3 MB, Apache-2.0)
        # is not committed; research/slayer-1b/tokenizer/tokenizer.json is a different tokenizer.
        pytest.xfail(f"NOT CHECKED: Slayer tokenizer.json not found at {sciezka}. Get it with "
                     "`huggingface-cli download SlayerLab/Slayer1B-1.06 tokenizer.json --revision "
                     "ef81be58742544ad32e1afab38db011fec209609` or set SLAYER_TOKENIZER=<path>; expected sha256 "
                     f"{SLAYER_TOKENIZER_SHA}")
    assert hashlib.sha256(sciezka.read_bytes()).hexdigest() == SLAYER_TOKENIZER_SHA
    from tokenizers import Tokenizer
    import slayer_model
    import hipoteza_formatu as H
    assert Tokenizer.from_file(str(sciezka)).id_to_token(slayer_model.Slayer.BOS) == "<|endoftext|>"

    class BezWag:
        bos, blok = slayer_model.Slayer.BOS, 4096

    monkeypatch.setattr(slayer_model, "Slayer", lambda katalog, device: BezWag())
    m = H.ModelSlayer("brak", "cpu")
    assert m.prefiks_pusty == [0] and m.prefiks == [0]


def test_remis_liczy_sie_jako_trafienie():
    assert B.trafienie([-3.0, -3.0]) == 1 and B.trafienie([-3.0, -2.9]) == 0


def test_identyczne_zdania_to_remis_niezaleznie_od_szumu():
    d = {"opcje": ["Same sentence.", "Same sentence."]}
    assert B.trafienie_pary(d, {"ll": [-74.41427, -74.41425]}) == 1  # float noise must not make it an error
    assert B.trafienie_pary({"opcje": ["a", "b"]}, {"ll": [-74.41427, -74.41425]}) == 0


def test_p_wartosci_panelu():
    d = docs()
    w = wyniki({x["id"]: True for x in d})
    p = B.panel(d, "pair_id", budzet=7)
    assert B.p_wartosci_panelu(d, w, p, 1.0, powtorzen=100) == 1.0  # all correct -> every panel gives 1.0
    assert B.p_wartosci_panelu(d, w, p, 0.5, powtorzen=100) == 0.0


def test_panel_przydzial_grupy():
    d = docs()
    p = B.panel(d, "pair_id", budzet=7)
    licz = {}
    for x in p:
        licz[x["grupa"]] = licz.get(x["grupa"], 0) + 1
    # 2 per member first (6), the 7th slot: largest deficit 7/3-2, tie -> first member task name
    assert licz == {"adjunct_island": 3, "animate_subject_passive": 2, "regular_plural_subject_verb_agreement_1": 2}
    assert [x["id"] for x in B.panel(list(reversed(d)), "pair_id", budzet=7)] == [x["id"] for x in p]
    assert len(B.panel(d, "sha256", budzet=200)) == 9  # min(budget, N)


def test_panel_kolejnosc_po_hashu():
    d = [x for x in docs() if x["grupa"] == "adjunct_island"]
    klucze = sorted(B.klucz_wyboru("blimp", "blimp_adjunct_island", str(x["rekord"]["pair_id"])) for x in d)
    p = B.panel(d, "pair_id", budzet=2)
    assert [B.klucz_wyboru("blimp", "blimp_adjunct_island", str(x["rekord"]["pair_id"])) for x in p] == klucze[:2]


def test_wartosc_grupy_rowne_wagi_czlonkow():
    assert math.isclose(B.wartosc_grupy([1, 1, 0, 1, 1], ["a", "a", "a", "b", "b"]), (2 / 3 + 1) / 2)
    # the Space T01 value 0.8407960199 = 338/402: 66 members x 3 pairs, 1 member x 2 pairs
    assert math.isclose(338 / 402, 0.8407960199004975)


def test_statystyki_i_porownanie_parowane():
    d = docs()
    ids = [x["id"] for x in d]
    a = wyniki({i: True for i in ids})
    b = wyniki({i: not i.startswith("blimp_adjunct") for i in ids})
    sa, sb = B.statystyki_modelu(a, d, bootstrap=False), B.statystyki_modelu(b, d, bootstrap=False)
    assert sa["acc"] == 1.0 and math.isclose(sb["acc"], 2 / 3)  # equal paradigm weights, not 5/9
    assert sb["paradygmaty"]["adjunct_island"]["acc"] == 0.0
    assert set(sb["zjawiska"]) == {"argument_structure", "island_effects", "subject_verb_agreement"}
    assert sa["baza_losowa"] == 0.5 and sa["baza_wiekszosciowa"] is None
    por = B.porownanie_parowane(a, b, d)
    assert math.isclose(por["ogolem"]["roznica"], 1 / 3)
    assert por["paradygmaty"]["adjunct_island"]["se"] == 0.0 and por["paradygmaty"]["adjunct_island"]["z"] is None
    assert por["paradygmaty"]["animate_subject_passive"]["roznica"] == 0.0


def test_porownanie_odwrocona_kolejnosc_wejscia():
    d = docs()
    a = wyniki({x["id"]: i % 2 == 0 for i, x in enumerate(d)})
    b = wyniki({x["id"]: i % 3 == 0 for i, x in enumerate(d)})
    p1 = B.porownanie_parowane(a, b, d)
    p2 = B.porownanie_parowane(a, b, list(reversed(d)))
    assert math.isclose(p1["ogolem"]["roznica"], p2["ogolem"]["roznica"])
    assert math.isclose(p1["ogolem"]["se"], p2["ogolem"]["se"])


def test_liczby_porownania_blimp_parowane():
    sys.path.insert(0, str(KAT.parent / "narzedzia"))
    import liczby as Lz
    d = docs()
    ids = [x["id"] for x in d]
    a = wyniki({i: True for i in ids})
    b = wyniki({i: not i.startswith("blimp_adjunct") for i in ids})
    bl = {"modele": {"1.06": B.statystyki_modelu(a, d, bootstrap=False), "pythia-1b": B.statystyki_modelu(b, d, bootstrap=False)},
          "porownanie": {"a": "1.06", "b": "pythia-1b", **B.porownanie_parowane(a, b, d)}}
    por = Lz.porownania_blimp(bl)
    assert len(por) == 1 + 3 + 3  # overall + phenomena + paradigms
    assert {p["test"] for p in por} == {"blimp"} and all(p["rodzina"] == "slayer_vs_pythia" for p in por)
    og = por[0]
    assert og["zadanie"] == "blimp" and math.isclose(og["roznica"], 1 / 3) and og["se"] == og["se_parowane"]


def test_analiza_funkcje_statystyczne():
    import blimp_analiza as A
    m, se, t = A.t_klastrowe([0.1, 0.3])
    assert math.isclose(m, 0.2) and math.isclose(se, 0.1) and math.isclose(t, 2.0)
    assert A.werdykt_grupy([-0.1, -0.11]) == A.NIEROZSTRZYGALNE  # 2 members: no verdict, whatever t says
    assert A.werdykt_grupy([-0.10, -0.105, -0.11]) == "pewne"  # t = -36.4, df = 2: p 0.0008
    # t = -19.05 and -10.39 would be certain read as a z; at df = 2 their p (0.0027, 0.0091) is only probable
    assert A.werdykt_grupy([-0.10, -0.11, -0.12]) == "prawdopodobne"
    assert A.werdykt_grupy([-0.10, -0.12, -0.14]) == "prawdopodobne"


def test_p_t_rozklad_studenta():
    import blimp_analiza as A
    for t in (0.3, 1.0, 2.5, 19.05):  # df = 2 has a closed form: p = 1 - |t| / sqrt(t^2 + 2)
        assert math.isclose(A.p_t(t, 2), 1 - t / math.sqrt(t * t + 2), rel_tol=1e-9)
        assert math.isclose(A.p_t(-t, 2), A.p_t(t, 2))
    assert math.isclose(A.p_t(1.0, 1), 0.5, rel_tol=1e-12)  # df = 1 is Cauchy: P(|T| > 1) = 1/2
    assert math.isclose(A.p_t(3.0, 10 ** 6), A.P_PEWNE, rel_tol=1e-4)  # large df -> normal
    assert math.isclose(A.p_t(2.0, 10 ** 6), A.P_PRAWDOPODOBNE, rel_tol=1e-4)
    assert math.isclose(A.p_t(2.228138851986, 10), 0.05, rel_tol=1e-7)  # t table, df = 10
    assert A.p_t(None, 5) == 1.0
    # the report's cases: overall stays certain, a t near 4 at df 5-7 is only probable
    assert A.werdykt_p(A.p_t(-3.30, 66)) == "pewne"
    assert A.werdykt_p(A.p_t(-3.79, 7)) == "prawdopodobne" and A.werdykt_p(A.p_t(-4.91, 5)) == "prawdopodobne"
    assert A.werdykt_p(A.p_t(-2.91, 64)) == "prawdopodobne" and A.werdykt_p(A.p_t(1.5, 64)) == "szum"


def test_ten_sam_worek_slow():
    import blimp_analiza as A
    assert A.ten_sam_worek_slow("Who did Amy see the man and?", "Who did Amy and see the man?")
    assert A.ten_sam_worek_slow("Susan revealed herself.", "susan herself revealed.")
    # the BLiMP flag lexically_identical is set on these, but the word forms differ
    assert not A.ten_sam_worek_slow("Raymond is selling this sketch.", "Raymond is selling this sketches.")
    assert not A.ten_sam_worek_slow("Susan revealed herself.", "Susan revealed themselves.")
    assert math.isclose(A.test_znakow(0, 5), 2 / 32) and A.test_znakow(3, 3) == 1.0
    odrz = A.holm({"a": 0.001, "b": 0.02, "c": 0.04})
    assert odrz == {"a": True, "b": True, "c": True}  # 0.001<=0.05/3, 0.02<=0.05/2, 0.04<=0.05
    assert A.holm({"a": 0.001, "b": 0.03, "c": 0.04}) == {"a": True, "b": False, "c": False}  # step-down stops
    assert math.isclose(A.spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
    assert math.isclose(A.spearman([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)
    assert A.rangi([5, 1, 5]) == [2.5, 1.0, 2.5]
    p = A.podzbior({"a": [1, 0], "b": [0, 0, 0, 0]})
    assert p["n"] == 6 and math.isclose(p["roznica"], 1 / 6)
    assert A.podzbior({})["roznica"] is None


def test_analiza_na_przykladzie():
    import blimp_analiza as A
    d = docs()
    for x in d:
        x["rekord"] = {**x["rekord"]}
    ids = [x["id"] for x in d]
    a = {i: {"ll": [-1.0, -2.0], "ntok": [3, 3]} for i in ids}
    b = {i: {"ll": [-2.0, -1.0] if i.startswith("blimp_adjunct") else [-1.0, -2.0], "ntok": [3, 4]} for i in ids}
    por = B.porownanie_parowane(a, b, d)["paradygmaty"]
    an = A.analiza(d, a, b, por)
    assert an["generalizacja"]["k"] == 3 and an["generalizacja"]["znak"]["a_lepszy"] == 1
    assert an["zjawiska_klastrowe"]["island_effects"]["werdykt"] == A.NIEROZSTRZYGALNE  # k = 1
    # token differences: a has dn = 0, b has dn = 1 -> no pair with the same tokenization
    assert an["tokenizacja"]["ta_sama_roznica_tokenow"]["n"] == 0
    assert an["tokenizacja"]["rozna_roznica_tokenow"]["n"] == 9
    worek = an["ten_sam_worek_slow"]
    oczek = sum(A.ten_sam_worek_slow(*x["opcje"]) for x in d)
    assert worek["tak"]["n"] == oczek and worek["tak"]["n"] + worek["nie"]["n"] == 9
    for g in an["przewagi_a_odwrocone_na_token"]:
        assert por[g]["werdykt"] == "pewne" and por[g]["roznica"] > 0
        assert an["paradygmaty_dodatkowe"][g]["roznica_na_token"] < 0
    assert an["przewagi_a_pewne"] == sum(1 for r in por.values() if r["werdykt"] == "pewne" and r["roznica"] > 0)


def test_identyczne_zdania_poza_podzialem_slow():
    """A pair with identical good and bad sentence (passive_1, principle_A_case_2) is no word-order contrast:
    it goes to neither side of the same-words split, though it still counts in the overall comparison."""
    import blimp_analiza as A
    d = [dict(x) for x in docs()]
    d[0] = {**d[0], "opcje": [d[0]["opcje"][0], d[0]["opcje"][0]]}
    ids = [x["id"] for x in d]
    a = {i: {"ll": [-1.0, -2.0], "ntok": [3, 3]} for i in ids}
    b = {i: {"ll": [-2.0, -1.0], "ntok": [3, 3]} for i in ids}
    por = B.porownanie_parowane(a, b, d)["paradygmaty"]
    an = A.analiza(d, a, b, por)
    w = an["ten_sam_worek_slow"]
    assert w["tak"]["n"] + w["nie"]["n"] == len(d) - 1
    assert w["tak"]["n"] == sum(A.ten_sam_worek_slow(*x["opcje"]) for x in d[1:])
    assert an["generalizacja"]["k"] == 3  # the pair stays in the paradigm comparison


def test_odwrocenie_przewagi_na_token():
    """Summed ll favours a, per token (b's bad sentence is much longer) b wins: listed as a reversal."""
    import blimp_analiza as A
    d = [x for x in docs() if x["grupa"] == "adjunct_island"]
    ids = [x["id"] for x in d]
    # a: good wins summed (-10 vs -11) but loses per token (-10/2 vs -11/4)
    a = {i: {"ll": [-10.0, -11.0], "ntok": [2, 4]} for i in ids}
    # b: good loses summed (-11 vs -10) but wins per token (-11/6 vs -10/2)
    b = {i: {"ll": [-11.0, -10.0], "ntok": [6, 2]} for i in ids}
    por = {"adjunct_island": {"roznica": 1.0, "z": 9.0, "werdykt": "pewne"}}
    an = A.analiza(d, a, b, por)
    assert an["przewagi_a_pewne"] == 1 and an["przewagi_a_odwrocone_na_token"] == ["adjunct_island"]


def test_werdykt_progi():
    assert B.werdykt(3.0) == "pewne" and B.werdykt(-2.5) == "prawdopodobne" and B.werdykt(1.99) == "szum"
    assert B.werdykt(None) is None


def test_se_i_bootstrap():
    x = [1] * 80 + [0] * 20
    assert math.isclose(B.se_warstwowe([x]), math.sqrt(0.8 * 0.2 * 100 / 99 / 100))  # sample variance / n
    lo, hi = B.bootstrap_ci([x, x], powtorzen=2000)
    assert lo < 0.8 < hi and (lo, hi) == B.bootstrap_ci([x, x], powtorzen=2000)
    lo_w, hi_w = B.wilson(800, 1000)
    assert math.isclose(lo_w, 0.77408, abs_tol=1e-5) and math.isclose(hi_w, 0.82362, abs_tol=1e-5)  # Wilson, z=1.96


def test_wpis_t01_w_zadaniach():
    if importlib.util.find_spec("lm_eval") is None:
        import pytest
        pytest.skip("lm_eval not installed (zadania.py imports it)")
    import zadania as Z
    (wariant, cfg), = Z.konfiguracje("T01", "lokalne")
    assert wariant == "space" and cfg["doc_to_text"] == "" and cfg["target_delimiter"] == " "
    assert cfg["doc_to_target"] == 0 and cfg["dataset_kwargs"]["data_files"]["test"].endswith("blimp.jsonl")
    (_, hf), = Z.konfiguracje("T01", "hf")
    assert hf["dataset_path"] == "parquet" and B.REWIZJA in hf["dataset_kwargs"]["data_files"]["test"]


def test_kontrola_forward_argumenty_i_format():
    """kontrola_forward.py without weights: CLI parsing and the JSON that blimp.py zbierz reads."""
    import json
    import pytest
    import kontrola_forward as K
    a = K.argumenty(["--model", "m", "--watki", "6,1,6", "--sumy", "float64", "--wejscia", "pelne"])
    assert a.model == "m" and a.watki == [1, 6] and a.sumy == ["float64"] and a.wejscia == ["pelne"]
    d = K.argumenty(["--model", "m"])
    assert d.sumy == ["float32", "float64"] and d.wejscia == ["bez_ostatniego", "pelne"]
    assert d.wyjscie.endswith("wyniki/blimp/kontrola_forward.json") and d.wyniki.endswith("raw/1.06.jsonl.gz")
    for zle in (["--sumy", "float16"], ["--wejscia", "x"], ["--watki", "0"], []):  # [] : --model is required
        with pytest.raises(SystemExit):
            K.argumenty((["--model", "m"] if zle else []) + zle)
    przebiegi = [K.przebieg([0.1, 0.3], 0, 1, "pelne", "float32"), K.przebieg([0.2, 0.2], 1, 6, "pelne", "float64")]
    w = K.podsumuj(przebiegi, 1, {"torch": "x"})
    assert w["max_abs_roznica_ll"] == [0.2, 0.3] and w["srednia_abs_roznica_ll"] == [0.2, 0.2]
    assert w["przestawione_pary"] == 1 and w["zdania"] == 2 and "2 runs" in w["opis"]
    # the committed file has the same shape (written by this script)
    zap = json.loads((KAT.parent / "wyniki/blimp/kontrola_forward.json").read_text())
    assert set(zap) == set(w) and set(zap["przebiegi"][0]) == set(przebiegi[0])
    assert zap["max_abs_roznica_ll"] == [min(p["max_abs_roznica_ll"] for p in zap["przebiegi"]),
                                         max(p["max_abs_roznica_ll"] for p in zap["przebiegi"])]


def test_kontrola_forward_sprawdza_sha256sums(tmp_path):
    """Dummy model directory: matching files pass; one changed byte, a missing file or no SHA256SUMS stop the run."""
    import hashlib
    import pytest
    import kontrola_forward as K
    tresc = {n: f"plik {n}\n".encode() for n in K.SPRAWDZANE}
    for n, b in tresc.items():
        (tmp_path / n).write_bytes(b)
    (tmp_path / "SHA256SUMS").write_text("".join(f"{hashlib.sha256(b).hexdigest()}  {n}\n" for n, b in tresc.items()))
    assert set(K.sprawdz_sumy(tmp_path)) == set(K.SPRAWDZANE)
    zly = bytearray(tresc["model.safetensors"])
    zly[0] ^= 1
    (tmp_path / "model.safetensors").write_bytes(bytes(zly))
    with pytest.raises(SystemExit, match="model.safetensors: sha256"):
        K.sprawdz_sumy(tmp_path)
    (tmp_path / "model.safetensors").write_bytes(tresc["model.safetensors"])
    (tmp_path / "tokenizer.json").unlink()
    with pytest.raises(SystemExit, match="tokenizer.json: missing"):
        K.sprawdz_sumy(tmp_path)
    (tmp_path / "SHA256SUMS").unlink()
    with pytest.raises(SystemExit, match="SHA256SUMS: missing"):
        K.sprawdz_sumy(tmp_path)
    with pytest.raises(SystemExit):  # main checks before importing torch or the model code
        K.main(["--model", str(tmp_path)])


def test_kontrola_forward_ll_zdania_na_atrapie():
    """ll_zdania on a dummy causal model (logits at t = W[token t]): one BOS 0, " " before the sentence, the
    logits at t scored against token t + 1. Fails on a missing BOS, a missing space or logits shifted by one."""
    import pytest
    torch = pytest.importorskip("torch")
    import kontrola_forward as K
    V = 11
    W = torch.randn(V, V, generator=torch.Generator().manual_seed(7))

    def model(x):
        return (torch.nn.functional.one_hot(x, V).float() @ W,)  # tuple, like the official GPT

    def encode(s):
        return [ord(c) % 10 + 1 for c in s]  # ' ' -> 3; never 0, so BOS is distinct

    lp = torch.log_softmax(W, -1)
    for zdanie in ("ab", "Who left?"):
        ids = [0] + encode(" " + zdanie)
        oczek = sum(lp[ids[t - 1], ids[t]].item() for t in range(1, len(ids)))
        for wej in K.WEJSCIA:
            w = K.ll_zdania(model, encode, zdanie, wej, ["float32", "float64"])
            assert math.isclose(w["float32"], oczek, rel_tol=1e-5) and math.isclose(w["float64"], oczek, rel_tol=1e-9)
        # what the mutations would compute instead: each differs from the expected value
        bez_bos = encode(" " + zdanie)
        bez_spacji = [0] + encode(zdanie)
        for zle in (sum(lp[bez_bos[t - 1], bez_bos[t]].item() for t in range(1, len(bez_bos))),
                    sum(lp[bez_spacji[t - 1], bez_spacji[t]].item() for t in range(1, len(bez_spacji))),
                    sum(lp[ids[t], ids[t]].item() for t in range(1, len(ids)))):  # logits shifted by one
            assert not math.isclose(zle, oczek, rel_tol=1e-3)


def test_worek_slow_trzy_czytania():
    """The three readings of 'same words' disagree on real BLiMP pairs; the main one ignores case and punctuation."""
    import blimp_analiza as A
    a, b = "Who did Amy see the man and?", "Who did Amy and see the man?"
    assert A.ten_sam_worek_slow(a, b, "bez_interpunkcji") and A.ten_sam_worek_slow(a, b, "interpunkcja_osobno")
    assert not A.ten_sam_worek_slow(a, b, "split")  # "and?" vs "and"
    c, d = "Sam isn't leaving.", "isn't Sam leaving?"
    assert A.ten_sam_worek_slow(c, d) and not A.ten_sam_worek_slow(c, d, "interpunkcja_osobno")  # . vs ?
    assert not A.ten_sam_worek_slow("Amy left.", "amy left.", "split") and A.ten_sam_worek_slow("Amy left.", "amy left.")
    assert A.WOREK_GLOWNY == "bez_interpunkcji" and set(A.WORKI) == {"bez_interpunkcji", "split", "interpunkcja_osobno"}


def test_analiza_tabela_wrazliwosci_worka():
    import blimp_analiza as A
    d = docs()
    ids = [x["id"] for x in d]
    a = {i: {"ll": [-1.0, -2.0], "ntok": [3, 3]} for i in ids}
    b = {i: {"ll": [-2.0, -1.0], "ntok": [3, 3]} for i in ids}
    an = A.analiza(d, a, b, B.porownanie_parowane(a, b, d)["paradygmaty"])
    wr = an["ten_sam_worek_slow"]["wrazliwosc"]
    assert set(wr) == set(A.WORKI)
    for df, r in wr.items():
        assert r["tak"]["n"] + r["nie"]["n"] == sum(x["opcje"][0] != x["opcje"][1] for x in d)
        assert r["tak"]["n"] == sum(A.ten_sam_worek_slow(*x["opcje"], df) for x in d if x["opcje"][0] != x["opcje"][1])
    assert wr[A.WOREK_GLOWNY]["tak"] == an["ten_sam_worek_slow"]["tak"]


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
