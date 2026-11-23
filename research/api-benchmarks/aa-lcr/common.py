"""Shared loading for AA-LCR: dataset at a pinned revision, prompt template from the dataset card, tokenizers."""
import csv
import hashlib
import os
import zipfile
from pathlib import Path

REPO = "ArtificialAnalysis/AA-LCR"
REVISION = "9a77ef56b717057ade24ceab4d273712a0b4f19e"          # v1.1, 2026-09-04
REVISION_V1_0 = "bdae010bbce259820c0e34c1d7cce210d966fb75"      # v1.0.0, kept reproducible by the dataset card
BIELIK_REPO, BIELIK_REVISION = "speakleash/Bielik-11B-v3.1-Instruct", "d6e755d356ad418d0f0e30b8c428db267415ddb9"
SLAYER_REPO, SLAYER_REVISION = "SlayerLab/Slayer1B-1.08", "5f854a0cc7160594d54d1788d37a44e8ebabe16c"
HERE = Path(__file__).resolve().parent
CACHE = Path(os.environ.get("AALCR_CACHE", HERE / ".cache"))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(filename, revision, local_dir):
    from huggingface_hub import hf_hub_download   # imported here: the light tests do not install it
    return Path(hf_hub_download(REPO, filename, repo_type="dataset", revision=revision, local_dir=local_dir))


def fetch_data(revision=REVISION):
    """Download the CSV and the extracted-text zip at `revision`, unpack the zip, return (rows, lcr dir, files sha256)."""
    d = CACHE / "data" / revision[:8]
    csv_path = _download("AA-LCR_Dataset.csv", revision, d)
    zip_path = _download("extracted_text/AA-LCR_extracted-text.zip", revision, d)
    ex = d / "unzipped"
    if not ex.exists():
        with zipfile.ZipFile(zip_path) as z:
            # The archive stores UTF-8 names without the UTF-8 flag; zipfile reads them as cp437, which breaks the
            # file names in the CSV (for example a typographic apostrophe). Decode the names as UTF-8.
            for info in z.infolist():
                name = info.filename if info.flag_bits & 0x800 else info.filename.encode("cp437").decode("utf-8")
                target = ex / name
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(z.read(info))
    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows, ex / "lcr", {"AA-LCR_Dataset.csv": sha256(csv_path), "AA-LCR_extracted-text.zip": sha256(zip_path)}


def build_prompt(row, lcr_dir):
    """The prompt template of the dataset card (Prompt Template), documents in the order of data_source_filenames."""
    base = Path(lcr_dir) / row["document_category"] / row["document_set_id"]
    docs = [(base / f).read_text(encoding="utf-8") for f in row["data_source_filenames"].split(";")]
    documents_text = "\n\n".join(f"BEGIN DOCUMENT {i + 1}:\n{doc}\nEND DOCUMENT {i + 1}" for i, doc in enumerate(docs))
    return f"""BEGIN INPUT DOCUMENTS

{documents_text}

END INPUT DOCUMENTS

Answer the following question using the input documents provided above.

START QUESTION

{row['question']}

END QUESTION
"""
