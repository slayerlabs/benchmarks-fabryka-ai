#!/usr/bin/env bash
# On the instance, from a clone of the protocol branch in /workspace/repos/fabryka: the `lock` venv (torch 2.8.0 from
# requirements.lock.txt, the image has none), NLTK data, the EWoK cache if $WS/ewok_cache.tgz was copied (gated; no
# HF token on the instance), then kolejka.sh under a hard 4 h limit. One background process.
set -u
WS=/workspace
K=$WS/repos/fabryka/research
mkdir -p "$WS/logi" "$WS/.hf_home/hub"
export K WS HF_HOME=$WS/.hf_home PIP_NO_CACHE_DIR=1
git -C "$K" rev-parse HEAD > "$WS/logi/commit.txt"
if [[ -f $WS/ewok_cache.tgz ]]; then tar xzf "$WS/ewok_cache.tgz" -C "$WS/.hf_home/hub"; fi
python3 -m venv "$WS/venv-lock"
"$WS/venv-lock/bin/pip" install -q -r "$K/common/requirements.lock.txt" > "$WS/logi/pip.log" 2>&1
"$WS/venv-lock/bin/pip" install -q protobuf==7.36.2 sentencepiece==0.2.2 >> "$WS/logi/pip.log" 2>&1
"$WS/venv-lock/bin/pip" freeze > "$WS/logi/freeze_lock.txt"
"$WS/venv-lock/bin/python" -c "import nltk, sys; sys.exit(0 if nltk.download('punkt_tab', download_dir='$WS/nltk_data', quiet=True) else 1)"
"$WS/venv-lock/bin/python" -c "import torch, json; print(json.dumps({'torch': torch.__version__, 'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(0), 'n_gpu': torch.cuda.device_count()}))" \
  > "$WS/srodowisko.json" 2>> "$WS/logi/pip.log"
echo "environment $(cat "$WS/srodowisko.json")" > "$WS/logi/start.log"
timeout 4h bash "$K/results/full-run-2026-11/slayer-1.09-k70000/code/kolejka.sh" > "$WS/logi/kolejka_stdout.log" 2>&1
echo "queue exit $?" >> "$WS/logi/start.log"
