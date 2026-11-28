#!/usr/bin/env bash
# AA-LCR: fit check and null results. Usage: bash run.sh <model-id> [--limit N]
#   model-id: bielik-11b-v3.1 | slayer1b-1.09-k70000
# Downloads AA-LCR at the pinned revision, builds the prompt of every question (or the first N with --limit),
# counts its tokens with the model's tokenizer, and applies PROTOCOL.md: if no prompt fits the model's window the
# result is `score: null` with the reason, written to results/<model-id>.json, and the script stops BEFORE any
# generation or judging. If some prompt fits it stops with an error: what to do then is Dario's decision
# (PROTOCOL.md, "If part of the set fits"), not this script's.
# No API key and no judge model are needed. The window probe (probe_window.py) needs FABRYKA_API_KEY and is a
# separate step: it only records what the API accepted.
set -euo pipefail
MODEL="${1:?usage: bash run.sh <model-id> [--limit N]}"; shift || true
LIMIT=""
while [[ $# -gt 0 ]]; do case "$1" in --limit) LIMIT="$2"; shift 2;; *) echo "unknown arg $1" >&2; exit 2;; esac; done
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${VENV:-$HERE/.venv}"
command -v uv >/dev/null || python3 -m pip install -q uv
[[ -d "$VENV" ]] || uv venv -q --python 3.12 "$VENV"
uv pip install -q --python "$VENV/bin/python" -r "$HERE/requirements.in"
cd "$HERE"
"$VENV/bin/python" fit_check.py "$MODEL" ${LIMIT:+--limit "$LIMIT"}
