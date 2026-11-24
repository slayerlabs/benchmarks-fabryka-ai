"""IFEval on a Modal GPU: runs vllm.sh (Bielik) or run.sh (Slayer) in a container and copies the results back here.

One-time setup (local):
    uv tool install modal && modal setup
    modal secret create huggingface HF_TOKEN=hf_...   # token with access to speakleash/Bielik-11B-v3.1-Instruct
    (another secret name: HF_SECRET=<name> modal run ...)

Run:
    modal run modal_ifeval.py --limit 5                   # smoke test
    modal run modal_ifeval.py                             # Bielik 11B v3.1 with vLLM, both runs (see vllm.sh)
    modal run modal_ifeval.py --model slayer1b-1.08       # Slayer, as `bash run.sh slayer1b-1.08`,
                                                          # written as results/slayer1b-1.08-modal.*
    modal run modal_ifeval.py --model lfm3-1.7b           # LiquidAI/LFM3-1.7B with vLLM 0.34.0 (see lfm3.sh)

The venvs are installed when Modal builds the image (no GPU time). The weights are cached in the Modal volume
`hf-cache`, so a second run does not download them again. Results land in results/ and the lm-eval output (with
vllm.log for Bielik) in out/, as with run.sh. A failed run still copies out/ back, then exits with an error.
"""

import os
import pathlib
import subprocess
import sys

import modal

HERE = pathlib.Path(__file__).parent
# .parent.parent, not .parents[1]: in the container this file is /root/modal_ifeval.py and parents[1] is an IndexError
COMMON = HERE.parent.parent / "common"
# The same layout as the repo: lm_eval_slayer.py finds research/common/ two levels up.
REMOTE = "/research/api-benchmarks/ifeval"
HF_SECRET = os.environ.get("HF_SECRET", "huggingface")  # Modal secret holding HF_TOKEN
WORK = "/tmp/ifeval"  # a string: on Windows a Path would turn into backslashes in the image env
TORCH_INDEX = "https://download.pytorch.org/whl/cu128"  # as in run.sh

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("curl")
    .pip_install("uv")
    .add_local_file(HERE / "vllm.sh", "/opt/vllm.sh", copy=True)
    .run_commands(
        "VENV_VLLM=/opt/venv-vllm VENV=/opt/venv bash /opt/vllm.sh --setup-only",
        # Slayer's packages (run.sh installs them again, from the uv cache)
        f"uv pip install --python /opt/venv/bin/python --index-url {TORCH_INDEX} torch",
        "uv pip install --python /opt/venv/bin/python safetensors tokenizers huggingface_hub",
    )
    # LFM3 needs vLLM 0.34.0 in its own venv (added after the steps above so their cached layers stay valid)
    .add_local_file(HERE / "lfm3.sh", "/opt/lfm3.sh", copy=True)
    .run_commands("VENV_VLLM_LFM3=/opt/venv-vllm-lfm3 VENV=/opt/venv bash /opt/lfm3.sh --setup-only")
    .env({
        "VENV_VLLM": "/opt/venv-vllm",
        "VENV_VLLM_LFM3": "/opt/venv-vllm-lfm3",
        "VENV": "/opt/venv",
        "HF_HOME": "/hf",
        "OUT_DIR": f"{WORK}/out",
        "RESULTS_DIR": f"{WORK}/results",
    })
    .add_local_dir(HERE, REMOTE, ignore=[".venv*", "out", "results", "**/__pycache__", "modal_ifeval.py"])
    .add_local_file(COMMON / "slayer_lm.py", "/research/common/slayer_lm.py")
    .add_local_file(COMMON / "slayer_model.py", "/research/common/slayer_model.py")
)
hf_cache = modal.Volume.from_name("hf-cache", create_if_missing=True)
app = modal.App("ifeval-bielik", image=image)


@app.function(
    gpu="A100-80GB",
    timeout=4 * 3600,
    volumes={"/hf": hf_cache},
    secrets=[modal.Secret.from_name(HF_SECRET)],
)
def ifeval(model: str, limit: int = 0) -> tuple[int, dict[str, bytes]]:
    limit_args = ["--limit", str(limit)] if limit else []
    env = dict(os.environ)
    if model == "bielik":
        args = ["bash", f"{REMOTE}/vllm.sh", *limit_args]
    elif model == "lfm3-1.7b":
        args = ["bash", f"{REMOTE}/lfm3.sh", *limit_args]
    else:
        args = ["bash", f"{REMOTE}/run.sh", model, *limit_args]
        env["RESULT_ID"] = f"{model}-modal"
    returncode = subprocess.run(args, env=env).returncode
    work = pathlib.Path(WORK)
    files = {p.relative_to(work).as_posix(): p.read_bytes() for p in work.rglob("*") if p.is_file()}
    return returncode, files


@app.local_entrypoint()
def main(model: str = "bielik", limit: int = 0):
    if model not in ("bielik", "slayer1b-1.08", "lfm3-1.7b"):
        sys.exit(f"unknown --model {model} (bielik | slayer1b-1.08 | lfm3-1.7b)")
    returncode, files = ifeval.remote(model, limit)
    for rel, data in files.items():
        path = HERE / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print(f"wrote {path}")
    if returncode:
        sys.exit(f"the run failed with exit code {returncode}; see out/")
