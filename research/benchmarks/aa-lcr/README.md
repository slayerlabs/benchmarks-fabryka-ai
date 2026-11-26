# AA-LCR

Artificial Analysis Long Context Reasoning: 100 questions that need reasoning across several real documents, with about
100k input tokens per question, scored by an LLM equality checker. Refs #305. The measurement plan, written before any
model output, is [PROTOCOL.md](PROTOCOL.md).

- Dataset: [ArtificialAnalysis/AA-LCR](https://huggingface.co/datasets/ArtificialAnalysis/AA-LCR) @
  `9a77ef56b717057ade24ceab4d273712a0b4f19e` (v1.1, 2026-09-04): `AA-LCR_Dataset.csv` sha256
  `aea5198982436fa774f616964bbeb34716de9e94368a123275b9355765c9b73b`, `AA-LCR_extracted-text.zip` sha256
  `5e839249826f6b9bd5324f0d139089c9dc481ccb3f212a6dfad00c51045d9d8a`. The card documents the prompt template, document order and
  scoring; there is no harness repository.
- Metric: share of the 100 questions answered correctly, judged by GPT-5.6 Luna (medium) with the v1.1 system and user
  prompts (card, "Scoring Approach"), in percent. For pass/fail tasks `stderr = sqrt(p (1 - p) / n)`.
- Reference: [LiquidAI/LFM3-1.7B](https://huggingface.co/LiquidAI/LFM3-1.7B) @ `1da06bec6a819da10b54c67e5c90972b46d81871`,
  AA-LCR 52.83. The card states no AA-LCR version, judge, repeats or handling of unfinished outputs (PROTOCOL.md).
- Settings: the card's v1.1 prompt template, one user message, documents in the order of `data_source_filenames`.
- Extra services: the Fabryka AI API (`https://fabryka.ai/v1/chat/completions`) for the window probe only. The judge,
  GPT-5.6 Luna, is a paid API and is not used.

## Results

| model | score | stderr | n | date |
|---|---|---|---|---|
| Slayer 1B 1.09, update 70 000 (`slayer1b-1.09-k70000`) | null: the 4096-token window does not hold any AA-LCR prompt (shortest 85211 tokens) | - | - | 2026-11-23 |
| Bielik 11B v3.1 (`bielik-11b-v3.1`), Fabryka AI API | null: the 32768-token window does not hold any AA-LCR prompt (shortest 100913 tokens) | - | - | 2026-11-23 |
| LFM3-1.7B, model card | 52.83 | - | - | card |

Both are `score: null`, not zero: the benchmark is not cut down to fit, and no request was scored. There is no
`.jsonl.gz` in `results/` because nothing was generated or judged. No model answered a question, so there is no output to
read, and a random or majority baseline is not defined without a judge run.

### Prompt length against the windows

Tokens of the full prompt (template, all documents, question), 100 questions, from `results/lengths.json`
(`python measure_lengths.py`):

| count | min | median | max | prompts that fit |
|---|---|---|---|---|
| `cl100k_base` (the dataset's own count) | 71691 | 95288 | 114563 | - |
| Bielik tokenizer, raw text | 99861 | 121225.5 | 140467 | - |
| Bielik tokenizer with chat template (as the API counts it) | 100913 | 122277.5 | 141519 | 0 of 100 for a 32768 window |
| Slayer tokenizer plus BOS | 85211 | 115685 | 135882 | 0 of 100 for a 4096 window |

The `cl100k_base` count equals the published `input_tokens` for 95 of 100 questions; 5 differ by 2 to 5 tokens (cause not
investigated; the dataset history has a later fix of the question text encoding), which changes nothing here. Bielik's tokenizer needs about
27 percent more tokens than `cl100k_base` for the same text.

### Bielik's window through the API

`GET /v1/models` lists `context_length` 32768. `probe_window.py` checked it (`results/api-window.json`, 2026-11-23): with
`max_tokens` 1, templated prompts of 1052, 16000, 30000, 32000, 32700 and 32767 tokens were accepted (HTTP 200) and 32768,
32769, 33000, 40000, 65536 and the shortest real AA-LCR prompt (100913) were rejected (HTTP 400, "The model rejected this
request", with no detail). So the window is 32768 tokens in total, inferred from the boundary since the error text is
generic; the server's `usage.prompt_tokens` matched the local count at every accepted size. The model's own
`max_position_embeddings` is 32768. The shortest AA-LCR prompt is 3.1 times the window.

## Deviations

None from the dataset card's setup; the benchmark could not be run on these models. Not run: the judge (paid API), and
LFM3-1.7B (the card's number is quoted). Comparability notes: the card's AA-LCR version is unknown, and the card says v1.0.0
and v1.1 scores are not directly comparable.

## If part of the set fit

It does not. If a longer-context serving of either model appears, PROTOCOL.md requires the full-benchmark result to stay
`null` for the current serving and a subset to be reported as extra information only; deciding to run it is Dario's.

## Reproduce

```bash
bash run.sh bielik-11b-v3.1            # downloads the pinned dataset, counts tokens, writes the null result, stops
bash run.sh slayer1b-1.09-k70000 --limit 5   # smoke test, writes to out/
python measure_lengths.py              # needs the venv from run.sh: results/lengths.json
FABRYKA_API_KEY=... python probe_window.py   # results/api-window.json (about 12 requests, max_tokens 1)
```

No API key is needed for `run.sh`. Files: `common.py` (dataset, prompt template, zip file names decoded as UTF-8: the
archive stores them without the UTF-8 flag), `fit_check.py`, `measure_lengths.py`, `probe_window.py`. The repo holds no
dataset text; it is downloaded to `.cache/` (git-ignored).

## Provenance

Dataset sha256, tokenizer revisions and the date are in `results/lengths.json` and every `results/<model-id>.json`.
Generated by commit of this directory; no generation ran, so there is no generation provenance. Tokenizers: Bielik at
`d6e755d3` (revision pinned above); Slayer's `tokenizer.json` from `SlayerLab/Slayer1B-1.08` @ `5f854a0c`, sha256
`0640d3bd3674d7a6e59c540d945a2ad275a12e1bcaeb6007c37a90751f9815dd` (equal to `tokenizer_sha256` in its config).
