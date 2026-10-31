# AutoEval inspection boundary — frontend contract proposal

Status: documentation only. No inspection endpoint, worker, queue or evaluation service is implemented or connected. “Prepare inspection” checks one repository identifier locally; it never makes a network request. The disabled inspection action explicitly describes the missing service.

## What the supplied prototype actually contains

Static review of uploaded files, not executed validation:

| Component | Available behavior | Remaining limitation |
| --- | --- | --- |
| hf-worker.py:inspect | Queries HF model metadata, resolves info.sha, reads config, lists safetensors filenames/sizes, flags some custom architectures/code, proposes a checkpoint | Architecture detection is heuristic. Multiple files may be shards or alternative checkpoints; selecting model.safetensors/highest numbered compatible file is not proof of an unambiguous complete artifact set |
| hf-worker.py:download_selected/load_selected | Downloads selected assets and uses standard HF or GoLLeM loader; local-only model loading, finite-logit startup check, parameter counting | CUDA required; custom loader imports repository Python. This is not safe isolation and is not an official general-purpose worker |
| local-bench.js | inspect/start/submit/status/cancel/history routes, subprocess JSON events, local resource guards | Hosted target is unavailable; inherited environment and subprocess execution do not establish sandboxing or safe multi-user operation |
| benchmarks/registry.py | Selectable MultiBLiMP and ARC-PL, sequential ALL bundle retaining separate results | Supplied tests reference TextOps/chain/atomic/cloze entries absent from this registry and require missing modules/task files; no coherent release revision was supplied |
| multiblimp.py / arc_easy_pl.py / engine/model.py | Actual likelihood/scoring source is present and was inspected | Native Track and prototype semantics differ. Some inputs resolve dynamically; calibration, full offline tests and runtime parity remain unverified |
| public/app.js / index.html | Inspection/checkpoint interaction, local progress/history, explicit unapproved results | Decorative agent, countdown and multi-field technical configuration are not the new product UX |

No missing engine/task files are assumed to exist. TextOps and other experiments are not restored merely to satisfy mismatched tests. The inspection concepts are useful; copying this service into the application would not meet the official execution contract.

## Proposed future service contract

These are requirements for a later reviewed backend, not routes added by this correction.

1. **Inspection request:** schema version, normalized HF repository ID, optional explicit revision only when required by a user's choice, and an idempotency key. No credentials or executable code in the browser payload.
2. **Resolution:** backend resolves an immutable repository commit before planning; all future requests bind to that commit, never a moving main branch.
3. **Inspection result:** request/inspection ID, resolved commit, reviewed architecture/loader identity, tokenizer artifact identities, complete checkpoint artifact sets (including shards/index/config), hashes and sizes, candidate selection reasons and warnings.
4. **Compatibility/resource assessment:** exact versioned benchmark/suite IDs with supported/unsupported/unknown reasons; expected resource envelope and limits. Do not infer eligibility from model names or metadata estimates alone.
5. **Necessary choices only:** return a discriminated needs_choice response when architecture/complete checkpoint/artifact policy is genuinely ambiguous. Present the smallest required choice, not a blank technical form. Unsupported/custom-code cases can require review or rejection rather than consent-based execution.
6. **Execution request:** reference the immutable approved inspection, selected complete artifact set and exact protocol versions; pin the canonical package/runtime. Execution occurs only in an isolated runner with bounded resources/network and no production credentials. No automatic compute policy or paid-resource authorization is established by this document.
7. **Execution result:** complete versioned scientific manifest, metrics/counters/coverage, dataset and software revisions, numerical settings, artifact evidence and sanitized logs. Partial, failed or nonfinite results do not silently become eligible rankings.
8. **Publication:** independently validate checkpoint identity, protocol compatibility, benchmark coverage, eligibility and issuer/review authority before ranking. Completed never means officially verified.

A changed artifact/revision invalidates the old inspection plan. Retry/cancellation, failure and review outcomes need explicit IDs/reasons; resource cleanup must not erase results or turn failed execution into success.

## Attribution and status

Frontend provenance UI v2 uses independent fields:

- data source: synthetic fixture (not an evaluation origin);
- submissionSource: autoeval, imported, manually_reported, or unknown/null;
- executionStatus: independently known lifecycle state, or unknown/null;
- verificationStatus: unreviewed, reviewed, awaiting_review, officially_verified, or unknown/null;
- leaderboardCategory: EN/PL/PL+EN view; measured suite ID/version remain separate.

Existing fixture origin is unknown, so submissionSource remains null. A reported trust badge does not prove manual submission; a measured badge does not prove an AutoEval job. The one-input screen records no submission at all.

## Frontend acceptance now

Repository ID or root HTTPS HF URL is parsed locally; malformed input is explained accessibly. After a valid format check, the UI shows the normalized requested repository and a blocked/unavailable service state. Resolved revision, selected checkpoint, compatible suites, validation, execution, verification, results and manifests remain unavailable.

Individual benchmark catalog facts derive from the inspected Track commit 73026f45a5350b15e006c15d4341805a73f568e4, its pinned benchmark map and uploaded prototype files. Catalog IDs identify UI entries, not new approved protocols. Missing licenses/checksums are unknown; no result provenance is populated from generic catalog facts.

The factory SVG and warm paper/rust navigation follow the same pinned Track brand source. Only the local visual asset is reused; the original repository, application and infrastructure are unchanged.
