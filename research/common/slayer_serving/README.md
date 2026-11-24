# slayer_serving: Slayer 1B for API benchmarks

Shared code that serves the Slayer 1B base model to generative and API benchmarks. It was copied byte for byte into
four benchmark directories (IFBench #324, IFStruct #325, AA-Omniscience #327, Multi-IF #329); the review asked to keep
one copy in `research/common/`, and those benchmarks now call it from here.

| file | what it does |
|---|---|
| `slayer_package.py` | builds the step-60000 package (load_slayer.py, trainer code, tokenizer, weights) from public pinned files |
| `slayer_kv_lm.py` | lm-eval adapter: greedy decoding with a KV cache, one prompt at a time; also a CLI for raw prompts |
| `slayer_batch.py` | batched decoding with a KV cache and sampling, on top of `slayer_kv_lm.py` |
| `slayer_server.py` | OpenAI-compatible server (`/v1/models`, `/v1/completions`, `/v1/chat/completions`) on `slayer_batch.py` |

`slayer_kv_lm.py` is the file named `slayer_lm.py` in the benchmark directories. It is renamed because
`research/common/slayer_lm.py` is a different adapter (an HFLM-based wrapper registered as the lm-eval model
`slayer` for the log-likelihood runs).

**Same code as the runs.** The only changes against the copies the results were produced with are the new file name
and the lines that name it: the docstrings, one error message, and `import slayer_kv_lm as slayer_lm` in
`slayer_server.py`. Decoding is unchanged. SHA-256 of the copies used for the runs (first 16 hex digits):
`slayer_lm.py` 7ecb6a7ae7fdbfee, `slayer_package.py` 8af3ef886e0ab557, `slayer_batch.py` 26bc985d53e0c9f3,
`slayer_server.py` 021c6dc8e7b488f0.

Run the server from this directory, so that its imports resolve to these files and not to `research/common/`:

```bash
cd research/common/slayer_serving
python slayer_package.py --out <package dir>
python slayer_server.py --pkg <package dir> --port 8001 --log <log dir> --limit-mode fixed --batch 32
```
