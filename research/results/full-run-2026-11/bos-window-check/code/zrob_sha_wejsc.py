"""sha_wejsc.json z pobranej paczki (nie z rozpakowanych plikow): python zrob_sha_wejsc.py <calosc.tgz> <manifest> <sha_wejsc.json>"""
import hashlib
import json
import sys
import tarfile
from pathlib import Path

paczka, manifest, wy = sys.argv[1:4]
surowe = {}
with tarfile.open(paczka) as t:
    for m in t.getmembers():
        if m.isfile():
            nazwa = m.name[len("wyniki/"):] if m.name.startswith("wyniki/") else m.name
            surowe[nazwa] = hashlib.sha256(t.extractfile(m).read()).hexdigest()
stary = Path(manifest).parent / "wsc273" / "pythia-1b-v0" / "results_rozszerzone.json"
Path(wy).write_text(json.dumps({"paczka_sha": hashlib.sha256(Path(paczka).read_bytes()).hexdigest(),
                                "manifest": hashlib.sha256(Path(manifest).read_bytes()).hexdigest(),
                                "wsc273_stary": hashlib.sha256(stary.read_bytes()).hexdigest(),
                                "surowe": surowe}, indent=1), encoding="utf-8")
print(len(surowe))
