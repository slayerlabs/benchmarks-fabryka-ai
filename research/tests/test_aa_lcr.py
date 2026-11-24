"""AA-LCR (api-benchmarks/aa-lcr): checks without network, tokenizers or API key.

Checked: the prompt template is the dataset card's (documents in the order of `data_source_filenames`, blank lines
around the question), the zip file names are decoded as UTF-8 (the archive stores them without the UTF-8 flag), the
fit rule, and that the committed null results follow PROTOCOL.md (score null with a reason, no generation).
Run: python3 tests/test_aa_lcr.py (or pytest).
"""
import json
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest import mock

BENCH = Path(__file__).resolve().parents[1] / "api-benchmarks" / "aa-lcr"
sys.path.insert(0, str(BENCH))
import common  # noqa: E402
import fit_check  # noqa: E402


def test_prompt_template_is_the_card_template():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "Cat" / "set1"
        d.mkdir(parents=True)
        (d / "b.txt").write_text("BBB", encoding="utf-8")
        (d / "a.txt").write_text("AAA", encoding="utf-8")
        row = {"document_category": "Cat", "document_set_id": "set1", "data_source_filenames": "b.txt;a.txt",
               "question": "Q?"}
        got = common.build_prompt(row, t)
    want = ("BEGIN INPUT DOCUMENTS\n\nBEGIN DOCUMENT 1:\nBBB\nEND DOCUMENT 1\n\nBEGIN DOCUMENT 2:\nAAA\nEND DOCUMENT 2\n\n"
            "END INPUT DOCUMENTS\n\nAnswer the following question using the input documents provided above.\n\n"
            "START QUESTION\n\nQ?\n\nEND QUESTION\n")
    assert got == want


def test_zip_names_decoded_as_utf8():
    name = "lcr/Legal/x/EU’s Act.txt"                       # typographic apostrophe, as in the dataset
    with tempfile.TemporaryDirectory() as t:
        zp = Path(t) / "a.zip"
        # write the name's UTF-8 bytes without the UTF-8 flag: zipfile then reads it as cp437, as AA-LCR's archive does
        info = zipfile.ZipInfo(name.encode("utf-8").decode("cp437"))
        with mock.patch.object(zipfile.ZipInfo, "_encodeFilenameFlags",
                               lambda self: (name.encode("utf-8"), self.flag_bits & ~0x800)):
            with zipfile.ZipFile(zp, "w") as z:
                z.writestr(info, "text")
        assert not zipfile.ZipFile(zp).infolist()[0].flag_bits & 0x800
        assert zipfile.ZipFile(zp).infolist()[0].filename != name
        csv_dir = Path(t) / "data" / common.REVISION[:8]
        csv_dir.mkdir(parents=True)
        (csv_dir / "AA-LCR_Dataset.csv").write_text("question_id\n1\n", encoding="utf-8")
        fake = {"AA-LCR_Dataset.csv": csv_dir / "AA-LCR_Dataset.csv",
                "extracted_text/AA-LCR_extracted-text.zip": zp}
        common.CACHE = Path(t)
        with mock.patch.object(common, "_download", side_effect=lambda f, rev, d: fake[f]):
            _, lcr, _ = common.fetch_data()
        assert (lcr / "Legal" / "x" / "EU’s Act.txt").read_text() == "text"


def test_null_result_fields():
    r = fit_check.null_result("bielik-11b-v3.1", [100913, 120000, 141519], 100, 0, True)
    assert r["score"] is None and r["stderr"] is None and r["n"] is None
    assert "100913" in r["other_metrics"]["reason"] and "32768" in r["other_metrics"]["reason"]
    assert r["other_metrics"]["prompts_that_fit"] == 0


def test_committed_results_are_null_with_reason_and_nothing_fits():
    lengths = json.loads((BENCH / "results" / "lengths.json").read_text())
    assert lengths["dataset"]["n"] == 100 and len(lengths["per_question"]) == 100
    for model, win_key, count_key in [("bielik-11b-v3.1", "bielik-11b-v3.1 (Fabryka API)", "bielik_templated"),
                                      ("slayer1b-1.09-k70000", "slayer1b (block)", "slayer_raw")]:
        r = json.loads((BENCH / "results" / f"{model}.json").read_text())
        window = lengths["windows"][win_key]
        assert r["score"] is None and r["settings"]["context_window"] == window
        assert min(q[count_key] for q in lengths["per_question"]) + 1 > window
        assert r["other_metrics"]["tokens_min"] == lengths["distribution"][count_key]["min"]
        assert r["other_metrics"]["prompts_that_fit"] == 0 and r["other_metrics"]["reason"]
    assert not list((BENCH / "results").glob("*.jsonl.gz"))      # nothing was generated


def test_api_window_probe_matches_listed_window():
    p = json.loads((BENCH / "results" / "api-window.json").read_text())
    ok = [x["local_templated_tokens"] for x in p["probes"] if x["status"] == 200]
    bad = [x["local_templated_tokens"] for x in p["probes"] if x["status"] == 400]
    assert max(ok) + 1 == p["listed_context_length"] == 32768 and min(bad) == 32768
    for x in p["probes"]:
        if x["status"] == 200:
            assert x["usage"]["prompt_tokens"] == x["local_templated_tokens"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
