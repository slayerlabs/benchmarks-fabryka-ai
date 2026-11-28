# Shared setup, sourced by run.sh and smoke.sh. Rebuilds the pinned harness and the venv when absent.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TS_COMMIT="c8571d7854316d2e1c5f288e59fe1e34e53f6dd1"   # apple/ToolSandbox, main as of 2026-11-23
OUT="${OUT_DIR:-$HERE/out}"
VENV="${VENV:-$HERE/.venv}"
REPO="$OUT/ToolSandbox"
mkdir -p "$OUT"
if [[ ! -d "$REPO/.git" ]]; then
  git init -q "$REPO"
  git -C "$REPO" fetch -q --depth 1 https://github.com/apple/ToolSandbox.git "$TS_COMMIT"
  git -C "$REPO" checkout -q FETCH_HEAD
fi
[[ "$(git -C "$REPO" rev-parse HEAD)" == "$TS_COMMIT" ]] || { echo "ToolSandbox checkout is not $TS_COMMIT" >&2; exit 1; }
if [[ ! -x "$VENV/bin/tool_sandbox" ]]; then   # the README's Python 3.9 and the exact pins of pyproject.toml
  uv venv --python 3.9 "$VENV"
  uv pip install --python "$VENV/bin/python" "$REPO[dev]"
fi
# Every dependency version of the runs, including the transitive ones the harness does not pin (httpx 0.27.2: openai==1.17.0
# passes `proxies=` to httpx, which httpx 0.28 removed). The harness itself stays the pinned clone installed above.
"$VENV/bin/python" - "$HERE/requirements.lock.txt" <<'PYEOF' || uv pip install --python "$VENV/bin/python" -r "$HERE/requirements.lock.txt"
import sys
from importlib.metadata import version
want = [l.split("==") for l in open(sys.argv[1]) if "==" in l and not l.startswith("#")]
sys.exit(any(version(n.strip()) != v.strip() for n, v in want))
PYEOF
PY="$VENV/bin/python"
export PYTHONWARNINGS=ignore
