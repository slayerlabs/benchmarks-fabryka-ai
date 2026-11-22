"""What produced a run: code version, runner checksums, hardware, effective sampling; and sha256 manifests of inputs.

  python provenance.py generation <out>/<model-id>
      run.sh, before generation: appends one line to <out>/<model-id>/generation.jsonl with the commit of this repo
      (and whether the worktree was dirty), the sha256 of every runner file, the GPU (nvidia-smi) and platform of
      the generating machine, the sampling settings in effect (PROTOCOL.md, Amendment 3) and whether the generation
      prompt leaves a reasoning block open (`reasoning`, which decides strict scoring, Amendment 4).
  python provenance.py generation-end <out>/<model-id>
      run.sh, after generation: adds to that line `api_events`, the counts of the api-events.jsonl lines (predict.py)
      written during this call (null with the reason for Slayer, which sends no HTTP request).
  python provenance.py manifest <out>/<model-id>
      run.sh, after generation and RULER scoring: writes <out>/<model-id>/inputs.sha256.json, the sha256 of every
      file summarize.py reads. summarize.py stops when a file differs from it. summarize.py records the sha256 of the
      result files it writes in results.sha256.json next to them; compare.py stops when one differs.

Effective sampling on vLLM 0.34.0 (`--generation-config auto`, its default): a field the request does not set comes
from the model's generation_config.json at the pinned revision, else from vLLM's OpenAI default
(vllm/config/model.py `get_diff_sampling_param`, vllm/entrypoints/openai/protocol.py `to_sampling_params`: user ->
server default -> OpenAI default). The Fabryka API's own defaults are not visible; Slayer decodes greedily.
"""

import argparse
import datetime
import hashlib
import json
import os
import platform
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER_FILES = ["run.sh", "predict.py", "slayer_predict.py", "prepare_limited.py", "ruler.py", "summarize.py",
                "compare.py", "provenance.py", "diagnostics.py", "report.py", "declared_provenance.json",
                "requirements.lock.txt", "nemo_shim/nemo/collections/asr/parts/utils/manifest_utils.py",
                "../../common/slayer_lm.py", "../../tools/statystyka.py"]
# vLLM 0.34.0 vllm/config/model.py get_diff_sampling_param: the generation_config.json fields it uses
VLLM_CONFIG_FIELDS = ["repetition_penalty", "presence_penalty", "frequency_penalty", "temperature", "top_k", "top_p",
                      "min_p", "max_new_tokens", "skip_special_tokens"]
# vLLM 0.34.0 ChatCompletionRequest._DEFAULT_SAMPLING_PARAMS: the last fallback
VLLM_OPENAI_DEFAULTS = {"repetition_penalty": 1.0, "presence_penalty": 0.0, "frequency_penalty": 0.0,
                        "temperature": 1.0, "top_p": 1.0, "top_k": 0, "min_p": 0.0}
INPUTS = "inputs.sha256.json"
RESULTS = "results.sha256.json"
INPUT_GLOBS = ["run.json", "generation.jsonl", "*/skip.json", "*/data/*/validation.jsonl", "*/data/*/skip.json",
               "*/raw/*.jsonl", "*/pred/*.jsonl", "*/pred/summary*.csv", "*/api-events.jsonl"]
THINK_OPEN, THINK_CLOSE = "<think>", "</think>"
PROBE = [{"role": "user", "content": "Probe."}]
TOKENIZER_FILES = ["*.json", "*.jinja", "*.txt", "*.model", "*.tiktoken"]  # as run.sh downloads them
NO_HTTP = "no HTTP requests: Slayer runs locally through research/common/slayer_lm.py"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _run(*command):
    try:
        return subprocess.run(command, capture_output=True, text=True, check=True, timeout=60).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def code_version(root=HERE):
    """{"commit", "dirty"} of the repo holding this script; both None with a reason outside a git checkout."""
    commit = _run("git", "-C", str(root), "rev-parse", "HEAD")
    if commit is None:
        return {"commit": None, "dirty": None, "reason": "not a git checkout or no git"}
    status = _run("git", "-C", str(root), "status", "--porcelain")
    return {"commit": commit, "dirty": None if status is None else bool(status)}


def uncommitted_runner_files(root=HERE):
    """Runner files that differ from HEAD (modified, staged or untracked); None outside a git checkout."""
    status = _run("git", "-C", str(root), "status", "--porcelain", "--untracked-files=all", "--",
                  *(name for name in RUNNER_FILES if (Path(root) / name).exists()))
    # `_run` strips the output, which can cut the first line's leading status column: split on whitespace instead
    return None if status is None else sorted(line.split(None, 1)[1] for line in status.splitlines() if line.strip())


def require_committed(who, root=HERE):
    """Stop before writing a published result while a runner file differs from the commit (the first summary of
    this benchmark was written by a summarize.py that is in no commit)."""
    changed = uncommitted_runner_files(root)
    if changed is None:
        raise SystemExit(f"{who}: STOP: not a git checkout; a published result needs the commit of its code")
    if changed:
        raise SystemExit(f"{who}: STOP: runner files differ from the commit: {', '.join(changed)}; commit them "
                         "first, a published result must name a commit that holds the code that wrote it")


def runner_sha256(root=HERE):
    return {name: sha256(root / name) if (root / name).is_file() else None for name in RUNNER_FILES}


def hardware():
    gpu = _run("nvidia-smi", "--query-gpu=name", "--format=csv,noheader")
    return {"gpu": gpu.splitlines() if gpu else None, "platform": platform.platform(), "machine": platform.machine(),
            "processor": platform.processor() or None, "cpu_count": os.cpu_count(),
            "python": platform.python_version()}


def machine(root=HERE):
    """Code version, runner checksums and hardware of the machine running this now."""
    return {"time": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "code": code_version(root), "runner_sha256": runner_sha256(root), "hardware": hardware()}


def effective_sampling(mode, sent, generation_config=None, source=None):
    """The sampling settings in effect: what the request sends, and what the server fills in."""
    if mode == "vllm":
        config = generation_config or {}
        from_config = {k: config[k] for k in VLLM_CONFIG_FIELDS if config.get(k) is not None}
        if "max_new_tokens" in from_config:
            from_config["max_tokens"] = from_config.pop("max_new_tokens")
        effective = {**VLLM_OPENAI_DEFAULTS, **from_config, **sent}
        return {"sent": sent, "from_generation_config": {k: v for k, v in from_config.items() if k not in sent},
                "effective": effective,
                "source": "vLLM 0.34.0 --generation-config auto: request, then generation_config.json "
                          f"({source}), then vLLM's OpenAI defaults"}
    if mode == "api":
        return {"sent": sent, "server_defaults": "unknown (Fabryka API)"}
    return {"sent": sent, "effective": {"decoding": "greedy (research/common/slayer_lm.py SlayerLM.generate, argmax)",
                                        **sent}}


def serving_mode(settings):
    """vllm, api or slayer, from run.json settings.serving as run.sh writes it."""
    serving = settings["serving"]
    return "vllm" if serving.startswith("vLLM") else "api" if serving.startswith("Fabryka") else "slayer"


def sampling(settings, read_config=None):
    """Effective sampling of a run from its run.json `settings` (serving, weights "repo @ revision ...", temperature,
    top_p, seed, max_tokens as run.sh writes them); vLLM reads generation_config.json at the pinned revision."""
    mode = serving_mode(settings)
    if mode == "slayer":  # slayer_predict.py: no sampling, RULER's answer budget
        return effective_sampling(mode, {"max_tokens": settings["max_tokens"]})
    sent = {k: settings[k] for k in ("temperature", "top_p", "seed")}
    sent["max_tokens"] = f"per request: {settings['max_tokens']}"
    if mode == "api":
        return effective_sampling(mode, sent)
    repo, _, revision = settings["weights"].split()[:3]
    config = (read_config or generation_config)(repo, revision)
    return effective_sampling(mode, sent, config, f"{repo} @ {revision}")


def render_generation_prompt(repo, revision):
    """One user message through the model's chat template at the pinned revision, template defaults, with the
    generation prompt: what vLLM and the Fabryka API append before the model's first token (local cache first)."""
    from huggingface_hub import snapshot_download
    from huggingface_hub.errors import LocalEntryNotFoundError
    from transformers import AutoTokenizer

    try:
        path = snapshot_download(repo, revision=revision, allow_patterns=TOKENIZER_FILES, local_files_only=True)
    except LocalEntryNotFoundError:
        path = snapshot_download(repo, revision=revision, allow_patterns=TOKENIZER_FILES)
    tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=False)
    return tokenizer.apply_chat_template(PROBE, add_generation_prompt=True, tokenize=False)


def reasoning(settings, render=None):
    """Whether the generation prompt opens a reasoning block, i.e. ends with an open `<think>` (LFM3-1.7B); a
    prompt that closes it (`<think></think>`, Bielik's default) or has none, and Slayer's raw prompt, do not. Strict
    scoring (an output without `</think>` scores 0, Amendment 4) applies only when it opens."""
    if serving_mode(settings) == "slayer":
        return {"opens": False, "reason": "raw prompt without a chat template: no reasoning block"}
    repo, _, revision = settings["weights"].split()[:3]
    rendered = (render or render_generation_prompt)(repo, revision)
    opens = rendered.rstrip().endswith(THINK_OPEN)
    out = {"opens": opens, "prompt_end": rendered[-40:],
           "source": f"chat template of {repo} @ {revision}, defaults, add_generation_prompt"}
    if not opens:
        out["reason"] = ("the generation prompt closes the reasoning block (ends `<think></think>`): outputs carry no "
                         "`</think>`" if rendered.rstrip().endswith(THINK_OPEN + THINK_CLOSE) else
                         "the generation prompt opens no reasoning block")
    return out


def generation_config(repo, revision):
    """generation_config.json at the pinned revision (local cache first); None when the model has none. Any other
    failure (offline and not cached) raises: an unknown config must not read as an empty one."""
    from huggingface_hub import hf_hub_download
    from huggingface_hub.errors import EntryNotFoundError, LocalEntryNotFoundError

    try:
        path = hf_hub_download(repo, "generation_config.json", revision=revision, local_files_only=True)
    except LocalEntryNotFoundError:
        try:
            path = hf_hub_download(repo, "generation_config.json", revision=revision)
        except EntryNotFoundError:
            return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def input_files(out_dir):
    out_dir = Path(out_dir)
    return sorted({p.relative_to(out_dir).as_posix() for g in INPUT_GLOBS for p in out_dir.glob(g) if p.is_file()})


def hashes(directory, names):
    return {name: sha256(Path(directory) / name) for name in names}


def write_manifest(directory, names, manifest_name):
    """Record the sha256 of `names` (relative to `directory`) in `directory/manifest_name`, keeping other entries."""
    path = Path(directory) / manifest_name
    recorded = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    recorded.update(hashes(directory, names))
    path.write_text(json.dumps(dict(sorted(recorded.items())), indent=2) + "\n", encoding="utf-8")


def check(directory, names, manifest_name, who, add_unrecorded):
    """Stop when a file in `names` has another sha256 than `directory/manifest_name` records. A file the manifest
    does not list is recorded now when there is no manifest yet or `add_unrecorded`, else it stops too. Returns the
    names recorded now (their sha256 is from now, not from when they were written)."""
    path = Path(directory) / manifest_name
    recorded = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    actual = hashes(directory, names)
    changed = [n for n in names if n in recorded and recorded[n] != actual[n]]
    if changed:
        raise SystemExit(f"{who}: STOP: sha256 differs from {path}: {', '.join(changed)} "
                         "(the file changed after it was recorded; rerun the step that writes it)")
    unrecorded = [n for n in names if n not in recorded]
    if unrecorded and path.is_file() and not add_unrecorded:
        raise SystemExit(f"{who}: STOP: not in {path}: {', '.join(unrecorded)} (written after the manifest)")
    if unrecorded:
        write_manifest(directory, unrecorded, manifest_name)
    return unrecorded


def verify_inputs(out_dir, who="summarize.py"):
    """Inputs of summarize.py in an out dir against inputs.sha256.json (run.sh writes it after scoring). Returns a
    warning when the manifest was not written by run.sh (an out dir from a run.sh before this check): summarize.py
    then writes it from the files as they are, which is not a verification of the first summary, and the warning
    stays in the manifest for every later one."""
    names = input_files(out_dir)
    manifest = Path(out_dir) / INPUTS
    if manifest.is_file():
        listed = json.loads(manifest.read_text(encoding="utf-8"))
        gone = [n for n in listed if not n.startswith("_") and n not in names]
        if gone:
            raise SystemExit(f"{who}: STOP: files in {manifest} are missing: {', '.join(gone)}")
        check(out_dir, names, INPUTS, who, add_unrecorded=False)
        return listed.get("_warning")
    check(out_dir, names, INPUTS, who, add_unrecorded=False)
    warning = (f"no {INPUTS} from run.sh in this out dir (generated by a run.sh before this check): the sha256 of "
               f"its {len(names)} input files were recorded by {who} at its first run, not when they were written")
    listed = json.loads(manifest.read_text(encoding="utf-8"))
    manifest.write_text(json.dumps({"_warning": warning, **listed}, indent=2) + "\n", encoding="utf-8")
    return warning


def record_inputs(out_dir):
    """run.sh after scoring: inputs.sha256.json rewritten whole, the files as they are now."""
    names = input_files(out_dir)
    (Path(out_dir) / INPUTS).unlink(missing_ok=True)
    write_manifest(out_dir, names, INPUTS)
    return names


def record_generation(out_dir, read_config=None, render=None):
    """run.sh before generation: one line in generation.jsonl."""
    run = json.loads((Path(out_dir) / "run.json").read_text(encoding="utf-8"))
    entry = {**machine(), "sampling": sampling(run["settings"], read_config),
             "reasoning": reasoning(run["settings"], render)}
    with open(Path(out_dir) / "generation.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def read_events(out_dir):
    """Every line of <out>/<length>/api-events.jsonl, all lengths."""
    events = []
    for path in sorted(Path(out_dir).glob("*/api-events.jsonl")):
        events += [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return events


def record_generation_end(out_dir):
    """run.sh after generation: `api_events` on the last generation.jsonl line, counted over the api-events.jsonl
    lines written since that line's time (this run.sh call)."""
    from predict import event_counts

    path = Path(out_dir) / "generation.jsonl"
    entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    run = json.loads((Path(out_dir) / "run.json").read_text(encoding="utf-8"))
    if serving_mode(run["settings"]) == "slayer":
        entries[-1].update(api_events=None, api_events_reason=NO_HTTP)
    else:
        start = datetime.datetime.fromisoformat(entries[-1]["time"])
        entries[-1]["api_events"] = event_counts([e for e in read_events(out_dir)
                                                  if datetime.datetime.fromisoformat(e["time"]) >= start])
    path.write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")
    return entries[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["generation", "generation-end", "manifest"])
    ap.add_argument("out_dir", type=Path)
    args = ap.parse_args()
    if args.command == "manifest":
        names = record_inputs(args.out_dir)
        print(f"provenance.py: {len(names)} input files recorded in {args.out_dir / INPUTS}")
    elif args.command == "generation-end":
        entry = record_generation_end(args.out_dir)
        print(f"provenance.py: api events {entry.get('api_events')}")
    else:
        entry = record_generation(args.out_dir)
        print(f"provenance.py: code {entry['code']}, GPU {entry['hardware']['gpu']}, sampling {entry['sampling']}, "
              f"reasoning {entry['reasoning']}")


if __name__ == "__main__":
    main()
