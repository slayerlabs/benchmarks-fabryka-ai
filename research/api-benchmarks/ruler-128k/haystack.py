"""The essay haystack: the part of PaulGrahamEssays.json that RULER's samples use, pinned, and a check that they use
nothing else.

RULER's download_paulgraham_essay.py (@ db43f92) writes one text: the 49 essays of
github.com/gkamradt/LLMTest_NeedleInAHaystack (`raw/main`, sorted by file name), then 169 essays fetched live from
paulgraham.com. niah.py takes the first words of that text as the haystack of the five essay tasks. The live part
made the file differ between runs of the same day (sha256 LFM3-1.7B 8d31e1b6, Bielik 58e35253). The GitHub part is
pinned here by commit and sha256; `check-out` shows that every essay haystack of a run is a prefix of it, so the
unpinned paulgraham.com part never reaches a sample. Lengths are counted in characters without whitespace, because
RULER's sentence split moves spaces (`good.[2]` becomes `good. [2]`).

Usage: python haystack.py urls SRC DST          RULER's URL list (SRC) with the GitHub essays at the pinned commit
       python haystack.py check-file FILE       exit 1 unless FILE (PaulGrahamEssays.json) opens with the pinned part
       python haystack.py check-out OUT FILE    exit 1 unless every essay haystack in OUT's RULER data is a prefix of
                                                the pinned part of FILE; prints the most characters a sample uses
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ESSAY_REPO = "https://github.com/gkamradt/LLMTest_NeedleInAHaystack/raw/"
COMMIT = "78774ab3e2ce64051713ca784d521ac4df5ac64e"  # last change of needlehaystack/PaulGrahamEssays, 2024-03-12
PART_CHARS = 643830  # the 49 GitHub essays concatenated as RULER's downloader does it
PART_SHA256 = "b3a70ebc054f2eab5057baf3c4b7e857711472be8086240a516fd29b648ad857"
# RULER @ db43f92 scripts/synthetic.yaml: the tasks with `type_haystack: essay`
ESSAY_TASKS = ["niah_single_2", "niah_single_3", "niah_multikey_1", "niah_multivalue", "niah_multiquery"]
LENGTHS = [4096, 8192, 16384, 32768, 65536, 131072]
# a needle of niah.py's template, in text without whitespace
NEEDLE = re.compile(r"Oneofthespecialmagic(?:numbers|words|uuids)for[^:]{1,80}?is:[^.]{1,60}\.")


def squeeze(text):
    return re.sub(r"\s+", "", text)


def pinned_urls(urls):
    """RULER's URL list with each GitHub essay at COMMIT instead of `main`."""
    pinned = urls.replace(ESSAY_REPO + "main/", ESSAY_REPO + COMMIT + "/")
    if pinned.count(COMMIT) != 49:
        raise ValueError(f"expected 49 GitHub essays in the URL list, found {pinned.count(COMMIT)}")
    return pinned


def pinned_part(text):
    """The first PART_CHARS characters of the essay text when their sha256 is PART_SHA256, else ValueError."""
    part = text[:PART_CHARS]
    if hashlib.sha256(part.encode("utf-8")).hexdigest() != PART_SHA256:
        raise ValueError(f"the essay text does not open with the 49 GitHub essays at {COMMIT[:8]} (sha256 "
                         f"{PART_SHA256[:8]})")
    return part


def haystack(sample):
    """The essay text of one RULER sample, without whitespace and needles: the input between the instruction line
    and the question line."""
    body = sample["input"].split("\n", 1)[1].rsplit("\n", 1)[0]
    return NEEDLE.sub("", squeeze(body))


def reach(out_dir, part):
    """length -> {samples, max_chars, outside}: the essay samples of the out dir, the most characters (without
    whitespace) one of them uses, and how many are not a prefix of `part`."""
    pinned = squeeze(part)
    out = {}
    for length in LENGTHS:
        used = []
        for task in ESSAY_TASKS:
            path = Path(out_dir) / str(length) / "data" / task / "validation.jsonl"
            if path.is_file():
                used += [haystack(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines()
                         if line.strip()]
        if used:
            out[str(length)] = {"samples": len(used), "max_chars": max(map(len, used)),
                                "outside": sum(not pinned.startswith(h) for h in used)}
    return out


def read_text(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))["text"]


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    urls = sub.add_parser("urls")
    urls.add_argument("src", type=Path)
    urls.add_argument("dst", type=Path)
    check_file = sub.add_parser("check-file")
    check_file.add_argument("file", type=Path)
    check_out = sub.add_parser("check-out")
    check_out.add_argument("out", type=Path)
    check_out.add_argument("file", type=Path)
    args = ap.parse_args()
    try:
        if args.cmd == "urls":
            args.dst.write_text(pinned_urls(args.src.read_text(encoding="utf-8")), encoding="utf-8")
        elif args.cmd == "check-file":
            pinned_part(read_text(args.file))
        else:
            per_length = reach(args.out, pinned_part(read_text(args.file)))
            outside = {x: v["outside"] for x, v in per_length.items() if v["outside"]}
            if outside:
                raise ValueError(f"essay haystacks outside the pinned part, per length: {outside}")
            print("haystack.py: every essay haystack is in the pinned GitHub part ("
                  + ", ".join(f"{x}: up to {v['max_chars']} characters" for x, v in per_length.items())
                  + f" of {len(squeeze(read_text(args.file)[:PART_CHARS]))}, whitespace left out)")
    except ValueError as e:
        sys.exit(f"haystack.py: {e}")


if __name__ == "__main__":
    main()
