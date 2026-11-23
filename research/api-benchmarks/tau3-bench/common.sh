# Shared setup, sourced by run.sh, run_sim_probe.sh and smoke.sh. Rebuilds the pinned harness and the venv when absent.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TAU2_TAG="v1.0.1"
TAU2_COMMIT="fc0055dc4e0a316c3f83133267fbd6faaa770992"   # sierra-research/tau2-bench, tag v1.0.1 (tau3-bench release)
OUT="${OUT_DIR:-$HERE/out}"
VENV="${VENV:-$HERE/.venv}"
REPO="$OUT/tau2-bench"
export TAU2_DATA_DIR="$REPO/data"
mkdir -p "$OUT"
if [[ ! -d "$REPO/.git" ]]; then
  git init -q "$REPO"
  git -C "$REPO" fetch -q --depth 1 https://github.com/sierra-research/tau2-bench.git "$TAU2_COMMIT"
  git -C "$REPO" checkout -q FETCH_HEAD
fi
[[ "$(git -C "$REPO" rev-parse HEAD)" == "$TAU2_COMMIT" ]] || { echo "tau2-bench checkout is not $TAU2_COMMIT" >&2; exit 1; }
[[ -x "$VENV/bin/tau2" ]] || (cd "$REPO" && UV_PROJECT_ENVIRONMENT="$VENV" uv sync --frozen --extra knowledge)
PY="$VENV/bin/python"
# Fabryka AI API (agent and, in the smoke test, simulator and judge): OpenAI-compatible, via litellm's openai/ provider.
: "${FABRYKA_API_KEY:=$(cat "$HOME/.config/fabryka-api.key")}"
export OPENAI_API_KEY="$FABRYKA_API_KEY" OPENAI_API_BASE="https://fabryka.ai/v1"
AGENT="openai/bielik-11b-v3.1"
# LFM3-1.7B card, "Evaluation details": temperature 0.6 and top_p 0.95 unless a benchmark is listed as an exception
# (tau3-bench is not).
AGENT_ARGS='{"temperature":0.6,"top_p":0.95}'
# Task ids per domain, from sample.json (the 20-task sample of PROTOCOL.md).
domain_ids() { "$PY" -c "import json,sys; print('\n'.join(json.load(open('$HERE/sample.json'))['domains']['$1']['ids']))"; }
# run_domain <domain> <save-to> <user-llm> <max-tasks-or-0> ; the judge comes from NL_JUDGE_LLM
run_domain() {
  local domain="$1" save="$2" user="$3" n="$4" ids=() extra=()
  while IFS= read -r id; do ids+=("$id"); done < <(domain_ids "$domain")
  [[ "$n" -gt 0 ]] && ids=("${ids[@]:0:$n}")
  [[ "$domain" == banking_knowledge ]] && extra=(--retrieval-config bm25)
  "$PY" "$HERE/tau3_run.py" run --domain "$domain" --agent-llm "$AGENT" --agent-llm-args "$AGENT_ARGS" \
    --user-llm "$user" --task-ids "${ids[@]}" --num-trials 1 --max-concurrency 2 \
    --save-to "$save" "${extra[@]}"
}
DOMAINS=(airline retail telecom banking_knowledge)
