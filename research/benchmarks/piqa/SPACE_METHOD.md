# Space protocol: the parts that PIQA (T06) uses

Excerpt of two files of the Space `SlayerLab/Slayer1B-Benchmarks` at revision
`2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9`, read on the GPU instance on 2026-11-01 (`piqa.py fetch`):

- https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks/blob/2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9/METHOD.md
- https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks/blob/2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9/tasks_50.json

METHOD.md text copied verbatim from the instance's terminal output; the T06 entry as printed there by
`json.dumps(entry, indent=1)` (same keys and values, whitespace of the original file not kept). The sha256 of the
full files was not recorded. The Space's
`METHOD.md` is version v0.3.1. Only sections 2, 3 and 8 and the T06 entry are copied here.

## METHOD.md, section 2 (Harness and runtime)

- Evaluation harness: EleutherAI lm-evaluation-harness, English tasks at commit `6d2abda4fd171e68a8789330c4149e37c1ca0bda`; Polish tasks from the OpenPL fork at `21d0ea9cf4fd6153dfff4d84d6ad0aab5488f302`. Separate environments, hash-locked dependencies.
- Settings: float32, batch size 1, maximum context 4096 tokens (longer inputs are rejected, never truncated), no chat template, greedy decoding. BOS follows each model's own tokenizer convention (for Hugging Face models `add_bos_token` from the pinned tokenizer files; recorded per run), with exactly one leading BOS per request; for empty contexts and rolling perplexity the BOS is an unscored prefix. This avoids the duplicate scored BOS that the pinned harness produces in those two paths when `add_bos_token` is true. Harness seeds (python, numpy, torch, fewshot) = (0, 1234, 1234, 1234).
- Offline: no network during evaluation; datasets, metric modules and NLTK data are pinned and staged before the run. Dataset loading scripts are never executed (see section 8).
- Before any benchmark is scored on a model, the runtime is calibrated on that model against the original harness forward: summed log-likelihood difference per target token ≤ 2e-5, full-vocabulary logits bitwise equal, rolling windows count each token once, greedy generation identical.

## METHOD.md, section 3 (Unit and sampling (panel200))

- Unit = one source document after the task's own `process_docs`. Identity = benchmark, source task, and the document's native id or, if none, the SHA-256 of the canonical document; byte-identical documents without an id get an ordinal in pinned file order (section 8).
- Per benchmark, `min(200, N_eligible)` documents are selected before any model is run, by SHA-256 of `20261028|benchmark_id|member_task|source_id`. All models are scored on the same documents.
- Groups: the 200 slots are per benchmark, not per member. Every member gets `min(2, N_i)` documents first; remaining slots go to the member with the largest deficit against `budget × source_weight`. BLiMP members are weighted equally; MMLU, MATH and BBH proportionally to member population. Member scores are re-aggregated with these fixed weights.
- WikiText-2 is scored on the full test stream with byte perplexity.
- `fullB` is a separate full-split run of the same primary protocols, without the 200 cap.

## METHOD.md, section 8 (Clarifications in v0.3.1), first two points

- **Script-only datasets** (PIQA, WSC273, LogiQA, MathQA, PubMedQA, Social IQa, PoQuAD, PolQA): benchmark identity stays at the pinned revision; data are read from the Hugging Face auto-converted parquet at the listed `refs/convert/parquet` commit. Columns must match what the task reads, otherwise the benchmark is blocked. PubMedQA additionally requires the parquet test split to equal the labeled test set of the pinned revision by id and label.
- **Duplicate documents** without a native id: identity = document hash + ordinal in pinned file order; bootstrap resamples identical documents as one cluster; counts are reported.

## tasks_50.json, entry T06

```json
{
  "id": "T06",
  "benchmark_id": "piqa",
  "task": "piqa",
  "name": "PIQA",
  "language": "EN",
  "family": "piqa",
  "domain": "physical_reasoning",
  "metric": "acc_norm,none",
  "unit": "score",
  "higher_is_better": true,
  "instrument": "lm_eval_0.4.8",
  "entrypoint_kind": "task",
  "split": "validation",
  "shots": 0,
  "rationale": "physical reasoning",
  "member_count": 1,
  "source_record": "piqa",
  "license": {
   "declared_tags": [
    "unknown"
   ],
   "basis": "revision-bound dataset-card metadata, not legal or execution approval",
   "source_revisions": [
    {
     "repo_id": "ybisk/piqa",
     "revision": "2e8ac2dffd59bac8c3c6714948f4c551a0848bb0",
     "metadata_source": "https://huggingface.co/api/datasets/ybisk/piqa/revision/2e8ac2dffd59bac8c3c6714948f4c551a0848bb0"
    }
   ]
  },
  "data_gate": "required_before_evaluation",
  "notes": [
   "Undeclared/umbrella data terms are a gate, not an inferred permissive licence."
  ],
  "definition": "lm_eval/tasks/piqa/piqa.yaml"
}
```

## How PIQA maps to it

- `benchmark_id` = `piqa`, `member_task` = `piqa` (one member, so no group allocation).
- PIQA rows have no native id, so the source id is the SHA-256 of the canonical row. The canonical form is not
  defined in METHOD.md; we use JSON with sorted keys and separators `,` and `:` (the reading that matched the Space
  value on BLiMP, `benchmarks/blimp/results/BLIMP.md`). The validation split has no byte-identical rows, so no ordinal.
- tasks_50.json does not list the `refs/convert/parquet` commit; we used `142c51238b3ca2bc61e9a075913871b8b600e8e1`.
