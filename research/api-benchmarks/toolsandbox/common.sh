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
# openai==1.17.0 (a harness pin) passes `proxies=` to httpx, which httpx 0.28 removed; the harness does not pin httpx.
"$VENV/bin/python" -c "import httpx,sys; sys.exit(httpx.__version__ != '0.27.2')" 2>/dev/null || uv pip install --python "$VENV/bin/python" "httpx==0.27.2"
PY="$VENV/bin/python"
export PYTHONWARNINGS=ignore
