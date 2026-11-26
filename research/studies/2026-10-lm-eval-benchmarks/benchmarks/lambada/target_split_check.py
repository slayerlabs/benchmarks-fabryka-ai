"""LAMBADA: how lm-eval's `text.split(' ')[-1]` target compares with the authors' target word, and the majority baseline.

Inputs (downloaded into DATA_DIR, outside the repo; nothing is written inside the repo):
- EleutherAI/lambada_openai @ 900124bf..., data/lambada_test.jsonl (the file lm-eval's `lambada_openai` scores),
  checked against the SHA-256 listed on the dataset card.
- cimec/lambada (the authors' set, `lambada_standard`), test split, read row by row from HF datasets-server.
  datasets-server serves the current `main` only, so the script first checks that `main` is still 5953bd9...

Prints: n, the number of rows whose lm-eval target (lowercased) equals the authors' last word, the rows that differ
(target with a glued quote or apostrophe, with a newline), and the most frequent target with its share.
Exit code != 0 when an integrity check fails.

Run (Windows, PowerShell): py -3 -I benchmarks\\lambada\\target_split_check.py D:\\VPS\\fabryka\\bench-team\\pobrane\\lambada
Run (bash): python3 -I benchmarks/lambada/target_split_check.py <DATA_DIR>
"""
import hashlib
import json
import re
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

OPENAI_REPO = "EleutherAI/lambada_openai"
OPENAI_REVISION = "900124bf3b8235c6daf21033af9948b3f07346c4"
OPENAI_FILE = "data/lambada_test.jsonl"
OPENAI_SHA256 = "4aa8d02cd17c719165fc8a7887fddd641f43fcafa4b1c806ca8abc31fabdb226"  # dataset card, "Hash Checksums"
STANDARD_REPO = "cimec/lambada"
STANDARD_REVISION = "5953bd97664b64b95754f299b2309ecfbfbe81b9"
STANDARD_N = 5153
PAGE = 100


def get(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read()
        except OSError:
            if attempt == 2:
                raise
            time.sleep(2)


def openai_texts(data_dir):
    path = data_dir / "lambada_test.jsonl"
    if not path.exists():
        url = f"https://huggingface.co/datasets/{OPENAI_REPO}/resolve/{OPENAI_REVISION}/{OPENAI_FILE}"
        path.write_bytes(get(url))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != OPENAI_SHA256:
        sys.exit(f"{path}: SHA-256 {digest}, expected {OPENAI_SHA256}")
    return [json.loads(line)["text"] for line in path.read_text(encoding="utf-8").splitlines()]


def standard_texts(data_dir):
    path = data_dir / "standard_test_rows.json"
    if not path.exists():
        main = json.loads(get(f"https://huggingface.co/api/datasets/{STANDARD_REPO}"))["sha"]
        if main != STANDARD_REVISION:
            sys.exit(f"{STANDARD_REPO}: main is {main}, the card pins {STANDARD_REVISION}")
        rows = []
        for offset in range(0, STANDARD_N, PAGE):
            url = (f"https://datasets-server.huggingface.co/rows?dataset={STANDARD_REPO}&config=plain_text"
                   f"&split=test&offset={offset}&length={PAGE}")
            rows += [r["row"]["text"] for r in json.loads(get(url))["rows"]]
        path.write_text(json.dumps(rows), encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv):
    if len(argv) != 1:
        sys.exit(__doc__)
    data_dir = Path(argv[0])
    data_dir.mkdir(parents=True, exist_ok=True)
    openai, standard = openai_texts(data_dir), standard_texts(data_dir)
    if len(openai) != len(standard):
        sys.exit(f"n differs: openai {len(openai)}, standard {len(standard)}")

    # the same split lm-eval uses: doc_to_target = ' ' + text.split(' ')[-1]
    targets = [t.split(" ")[-1] for t in openai]
    authors = [t.split(" ")[-1] for t in standard]
    same = [a == b.lower() for a, b in zip(authors, targets)]
    differ = [w for w, ok in zip(targets, same) if not ok]
    print(f"n: {len(openai)}")
    print(f"lm-eval target (lowercased) == authors' word: {sum(same)}")
    print(f"different: {len(differ)}, of which with a newline: {sum(chr(10) in w for w in differ)}")
    print(f"targets with characters other than letters: "
          f"{sum(1 for w in targets if not re.fullmatch(r'[A-Za-z]+', w))}")
    for w in differ:
        print("  " + ascii(w))
    for name, words in (("lambada_openai", targets), ("lambada_standard", authors)):
        word, count = Counter(words).most_common(1)[0]
        print(f"majority baseline {name}: {word!r} {count}/{len(words)} = {count / len(words):.4f}")


if __name__ == "__main__":
    main(sys.argv[1:])
