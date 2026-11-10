"""sha256 runnera liczone jak w ewaluuj.sha256_runnera: bajty common/*.py, potem common/*.sh."""
import hashlib
import sys
from pathlib import Path

K = Path(sys.argv[1])
pliki = sorted(K.glob("*.py")) + sorted(K.glob("*.sh"))
print(len(pliki), hashlib.sha256(b"".join(p.read_bytes() for p in pliki)).hexdigest())
