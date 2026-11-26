# Audit of the 55 benchmarks (26.11.2026)

Which benchmarks of this study are worth carrying forward into the CodeSOTA runner, measured on more models, and
which go to the archive. **Status: preliminary.** One refutation round by an independent reviewer changed 12
verdicts; the signal numbers were re-run and match, but no second independent verification has run yet. An archive
verdict is a recommendation until the team lead decides it.

## How the verdicts were made

The criteria and the decision rule were written before any number was computed:

- **K1 data validity**: a published audit with more than 10% wrong items, or a construction artifact that makes the
  score meaningless, is a serious problem.
- **K2 signal in our scale**: for the 15 benchmarks of the full run, the SNR of the panel of
  [METODOLOGIA, "Panel SNR"](METODOLOGIA.md) (the six reference base models of the run, without Slayer, Bielik-11B and
  LFM3-1.7B Instruct): the smallest SNR without one model must be at least 2. Computed by
  [`audit/k2_signal.py`](audit/k2_signal.py) from the full-run files; output in [`audit/k2_signal.json`](audit/k2_signal.json)
  (panel `M`; panel `C` is `M` without LFM2.5-1.2B-Base, whose full-run results disagree with the central run on the
  same weights). For the other 40, published evidence that models up to 2B score clearly above chance.
- **K3** contamination and saturation, **K4** readiness in the repo, **K5** redundancy with a kept benchmark of the
  same construct and higher signal, **K6** role for the team (Polish, a skill no other kept test covers).

| verdict | meaning |
|---|---|
| core | no serious K1 problem, K2 met, not redundant: port to the runner and measure on every model |
| informative | Polish or the only test of a skill, weaker or unknown signal: measured, outside averages and rankings |
| generative | needs generation; belongs to `research/benchmarks/`, not the log-likelihood runner |
| archive | serious K1 problem, no signal for any model class we measure, or redundant with a core test |
| undecided | the evidence does not decide; the decisive check is named |

## Verdicts

| benchmark | verdict | why |
|---|---|---|
| arc-easy | core | K2 met on both panels; reference reproduced (`verified` in the runner) |
| hellaswag | core | strongest signal of the run. The K1 claim did not hold: the label-error audits ([GoldenSwag, arXiv 2504.07825](https://arxiv.org/abs/2504.07825)) find about 1% wrong labels in the strict sense; their wider categories failed human validation, and a vendor blog sampled 300 rows without agreement measures |
| lambada | core | K2 met on both panels; `verified` |
| mathqa | core | K2 met on both panels; small models near the majority baseline, so read with the paired comparison to b |
| medmcqa | core | K2 met on both panels; in letter format Slayer picks "A" almost always, so report a cloze or BPB variant next to it ([answer-format study](../2026-10-answer-format/README.md)) |
| multiblimp-pl | core | K2 met; the only Polish grammar test. Caveats: Slayer's possible leak (#36) keeps Slayer out of its ranking, and Bielik-11B is near the ceiling |
| wikitext-2 | core until UncheatableEval replaces it | K2 met; Wikipedia is in most training data ([GPT-3, §3.1.1](https://arxiv.org/abs/2005.14165)) |
| winogrande | core, weak | K2 met on panel `M`, not on `C` |
| ewok | core, weak | K2 met on panel `M`, not on `C`; the only world-knowledge test; the dataset needs consent on Hugging Face |
| mmlu | core as cloze only | letter format is at chance for models up to about 1B; the cloze variant gives signal ([OLMES, arXiv 2406.08446](https://arxiv.org/abs/2406.08446)); label errors below the K1 threshold ([MMLU-Redux, arXiv 2406.04127](https://arxiv.org/abs/2406.04127)). The current task (letters, 5-shot) is archived |
| record | core | log-likelihood, published signal for models from 125M; risk of a ceiling at 11B |
| 8tags | core | every small Polish model above b, monotonic with size (Open PL LLM Leaderboard) |
| blimp | informative (diagnostic per paradigm) | no K2 signal: all models score alike, all clearly above chance; the only English grammar test left |
| sst2 | informative | the only sentiment test; Slayer gives one constant answer |
| polemo2, belebele-pl, ppc, llmzszl | informative (Polish) | only part of the small models above b; try cloze or BPB first |
| psc, klej-ner | informative (Polish) | signal only at 11B; klej-ner is sentence classification, not NER |
| gsm8k, math, bbh, coqa, triviaqa | generative | need generation; coqa and triviaqa show signal for small models |
| nq-open, polqa, poquad | generative | open-answer QA; polqa is open-book, so the passage overlap with Slayer's data does not decide it |
| arc-challenge | archive by the rule (dissent noted) | K2 met, but it is the same ARC dataset as arc-easy with lower signal (K5). Keeping it needs a rule change; the runner already has it, so cost is low |
| wsc273 | archive | same task as WinoGrande with lower signal; small set |
| openbookqa | archive | same construct as arc-easy with lower signal ([Signal and Noise, arXiv 2508.13144](https://arxiv.org/abs/2508.13144)); license unknown |
| cb | archive | 56 items, 5 of one class; models answer with one constant label |
| anli-r3 | archive | at chance for every model up to 20B |
| squad2 | archive | a third of items wrong or mislabeled in the platinum audit ([arXiv 2502.03461](https://arxiv.org/abs/2502.03461)) |
| drop | archive | many wrong items and a scoring bug that removed it from the Open LLM Leaderboard |
| ifeval | archive this copy | the live, generative IFEval is [`research/benchmarks/ifeval`](../../benchmarks/ifeval/README.md) |
| piqa | undecided | K2 fails without one model; rerun on a wider panel |
| social-iqa, pubmedqa | undecided | K2 fails on panel `M`; rerun on a wider panel, add BPB |
| boolq | undecided | below the "always yes" baseline at small scale; BPB on the panel decides |
| copa, sciq | undecided | the K1 claims did not hold; copa has 100 items, sciq is near saturation; a panel run decides |
| prost, logiqa, race | undecided | near chance in published results; a panel run decides |
| blimp-supplement, cola, wic, rte, paws-en, truthfulqa | undecided | no signal up to 2B; Bielik 11B (and the authors' binary TruthfulQA) decides |
| uncheatable-eval | undecided, candidate for core | fresh texts; needs its stage B and a run with standard errors |
| dyk, ewok-pl, cbd | undecided | dyk: F1 rewards a "yes" bias, AUC of log P(yes) decides; ewok-pl: translation not reviewed; cbd: the current task uses an undocumented 6-class column, a binary variant may work |

## What decides the undecided ones

Most need the same thing: the core and undecided benchmarks measured in the CodeSOTA runner on a wider panel (the
six reference models again, without the broken LFM2.5 run, plus Bielik 11B base and more small models), with a
probability metric (BPB or cloze) next to accuracy. What the runner lacks for that today:

1. one command for a list of models (today `--model` takes one; the model list lives only in
   `research/tools/przebieg_centralny.sh`);
2. a loader for Slayer (its `config.json` has no `model_type`; the research pipeline uses `research/common/slayer_lm.py`);
3. an environment that loads Qwen3.5 and LFM3 (they need newer transformers and lm-eval than the runner pins);
4. runner results on the results page (today the page reads only this study's full run and the API IFEval results);
5. per benchmark: the integration of each core benchmark not in the catalog yet (`benchmarks/docs/contributing.md`,
   section 5), and few-shot and corpus-F1 support for the Polish ones.

## Limits

- The K2 interval could not be bootstrapped: per-question samples of the reference models are not in the repository.
- The panel has six models; one broken result (LFM2.5 in this run) moves several verdicts.
- The decision rule does not use K3: wikitext-2 and multiblimp-pl pass although contamination or saturation is
  known. Their caveats are written above instead.
