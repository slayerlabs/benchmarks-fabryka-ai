# Protokół Space: części, których używa PIQA (T06)

Wyciąg z dwóch plików Space `SlayerLab/Slayer1B-Benchmarks` w rewizji
`2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9`, odczytanych na instancji GPU 2026-11-01 (`piqa.py fetch`):

- https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks/blob/2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9/METHOD.md
- https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks/blob/2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9/tasks_50.json

Tekst METHOD.md skopiowany dosłownie z wyjścia terminala instancji; wpis T06 tak, jak wypisał go tam `json.dumps(entry, indent=1)` (te same klucze i wartości, białe znaki oryginalnego pliku nie są
zachowane). sha256 w rewizji `2d3d73f5`: METHOD.md `8709632a394a3d69fa56567404e6543f7305d49fc97c9d381fbfad46d86628ae`,
tasks_50.json `fcfc45d805243e7ea4aa12bf836940ea086ecafe9fe3e592bf8850890ca8cf6b`. `METHOD.md` Space ma wersję
v0.3.1. Skopiowane są tu tylko sekcje 2, 3 i 8 oraz wpis T06.

## METHOD.md, sekcja 2 (Harness and runtime)

- Evaluation harness: EleutherAI lm-evaluation-harness, English tasks at commit `6d2abda4fd171e68a8789330c4149e37c1ca0bda`; Polish tasks from the OpenPL fork at `21d0ea9cf4fd6153dfff4d84d6ad0aab5488f302`. Separate environments, hash-locked dependencies.
- Settings: float32, batch size 1, maximum context 4096 tokens (longer inputs are rejected, never truncated), no chat template, greedy decoding. BOS follows each model's own tokenizer convention (for Hugging Face models `add_bos_token` from the pinned tokenizer files; recorded per run), with exactly one leading BOS per request; for empty contexts and rolling perplexity the BOS is an unscored prefix. This avoids the duplicate scored BOS that the pinned harness produces in those two paths when `add_bos_token` is true. Harness seeds (python, numpy, torch, fewshot) = (0, 1234, 1234, 1234).
- Offline: no network during evaluation; datasets, metric modules and NLTK data are pinned and staged before the run. Dataset loading scripts are never executed (see section 8).
- Before any benchmark is scored on a model, the runtime is calibrated on that model against the original harness forward: summed log-likelihood difference per target token ≤ 2e-5, full-vocabulary logits bitwise equal, rolling windows count each token once, greedy generation identical.

## METHOD.md, sekcja 3 (Unit and sampling (panel200))

- Unit = one source document after the task's own `process_docs`. Identity = benchmark, source task, and the document's native id or, if none, the SHA-256 of the canonical document; byte-identical documents without an id get an ordinal in pinned file order (section 8).
- Per benchmark, `min(200, N_eligible)` documents are selected before any model is run, by SHA-256 of `20261028|benchmark_id|member_task|source_id`. All models are scored on the same documents.
- Groups: the 200 slots are per benchmark, not per member. Every member gets `min(2, N_i)` documents first; remaining slots go to the member with the largest deficit against `budget × source_weight`. BLiMP members are weighted equally; MMLU, MATH and BBH proportionally to member population. Member scores are re-aggregated with these fixed weights.
- WikiText-2 is scored on the full test stream with byte perplexity.
- `fullB` is a separate full-split run of the same primary protocols, without the 200 cap.

## METHOD.md, sekcja 8 (Clarifications in v0.3.1), pierwsze dwa punkty

- **Script-only datasets** (PIQA, WSC273, LogiQA, MathQA, PubMedQA, Social IQa, PoQuAD, PolQA): benchmark identity stays at the pinned revision; data are read from the Hugging Face auto-converted parquet at the listed `refs/convert/parquet` commit. Columns must match what the task reads, otherwise the benchmark is blocked. PubMedQA additionally requires the parquet test split to equal the labeled test set of the pinned revision by id and label.
- **Duplicate documents** without a native id: identity = document hash + ordinal in pinned file order; bootstrap resamples identical documents as one cluster; counts are reported.

## tasks_50.json, wpis T06

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

## Jak PIQA się do tego mapuje

- `benchmark_id` = `piqa`, `member_task` = `piqa` (jeden członek, więc bez przydziału w grupie).
- Wiersze PIQA nie mają natywnego id, więc id źródła to SHA-256 wiersza kanonicznego. METHOD.md nie definiuje
  postaci kanonicznej; używamy JSON z posortowanymi kluczami i separatorami `,` i `:` (na BLiMP takie odczytanie dało
  wartość Space co do wszystkich wypisanych cyfr, ale żaden format nie odtworzył `source_id_digest` Space,
  `benchmarks/blimp/results/BLIMP.md`). Split walidacyjny nie ma wierszy identycznych bajtowo, więc bez ordinala.
- tasks_50.json nie podaje commita `refs/convert/parquet`; użyliśmy `142c51238b3ca2bc61e9a075913871b8b600e8e1`.
