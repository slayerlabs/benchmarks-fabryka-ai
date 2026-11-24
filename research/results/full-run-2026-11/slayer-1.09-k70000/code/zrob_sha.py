"""probki_sha256.json: sha256 paczki eksportu i każdego pliku w jej wyniki/, plus środowisko z srodowisko.json eksportu.
Zapisywany i commitowany przed raportem; liczby_109.py odmawia liczenia, gdy którakolwiek suma się nie zgadza.

    python zrob_sha.py <rozpakowany eksport> <paczka .tgz> <commit kodu na instancji> <karta> <probki_sha256.json>
"""
import hashlib
import json
import sys
from pathlib import Path


def sha256_pliku(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for kawalek in iter(lambda: f.read(1 << 20), b""):
            h.update(kawalek)
    return h.hexdigest()


def main():
    eksport, paczka, commit, karta, wyj = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4], Path(sys.argv[5])
    pliki = {str(p.relative_to(eksport)).replace("\\", "/"): sha256_pliku(p)
             for p in sorted((eksport / "wyniki").rglob("*")) if p.is_file()}
    sr = json.loads((eksport / "srodowisko.json").read_text(encoding="utf-8"))
    lock = (sr.get("srodowiska") or {}).get("lock") or {}
    out = {"paczka": {"nazwa": paczka.name, "sha256": sha256_pliku(paczka)},
           "srodowisko": {"commit_kodu": commit, "karta": karta, "gpu_nvidia_smi": sr.get("gpu"), "lm_eval": lock.get("lm_eval"),
                          "torch": lock.get("torch"), "cuda": lock.get("cuda"), "transformers": lock.get("transformers"),
                          "datasets": lock.get("datasets"), "python": lock.get("python"), "precyzja": "float32, TF32 wyłączony",
                          "batch": 1, "seed": "domyślny ewaluuj.py i ewok.py", "platforma": sr.get("platforma")},
           "pliki": pliki}
    wyj.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(pliki)} plików, paczka {out['paczka']['sha256']}")


if __name__ == "__main__":
    main()
