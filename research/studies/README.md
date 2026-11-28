# Studies

A study is one wave of work with one question: a set of tasks on the board, the models they measure, the benchmarks
they use, and what we learned. Benchmarks live in their own directories and are shared by studies; a study only says
which ones it uses and why. When priorities change, a study is closed or a new one starts; no benchmark moves. The
exception is the first study, `2026-10-lm-eval-benchmarks`: its 55 benchmarks predate this layout and stay inside it,
frozen.

## All studies

| study | question | state |
|---|---|---|
| [`2026-10-lm-eval-benchmarks`](2026-10-lm-eval-benchmarks/README.md) | how small base models score on 55 established benchmarks run through lm-eval, measured the same way | finished, frozen |
| [`2026-10-answer-format`](2026-10-answer-format/README.md) | does a small model fail multiple-choice tests because of the letter format rather than knowledge | finished, frozen |
| [`2026-11-small-vs-large`](2026-11-small-vs-large/README.md) | can a small model (LFM3-1.7B, Slayer 1B) match Bielik 11B v3.1 on 25 generative and agentic benchmarks | in progress |

## Starting a study

A new wave of tasks (for example a new list from CodeSOTA) gets a new directory, `studies/<YYYY-MM>-<short-name>/`,
with the month it starts. Its `README.md` has these sections, written before the first measurement of the study:

1. **Question**: one sentence, and what answer would change a decision.
2. **Models**: each with its configuration from the [evaluation methodology](../../benchmarks/docs/methodology.md).
3. **Benchmarks**: one row each, with a link to its directory and its state (planned, running, done, dropped with the
   reason and date). A benchmark that does not exist yet gets its directory as
   [`research/benchmarks/README.md`](../benchmarks/README.md) says.
4. **Hypotheses and thresholds**: what result confirms or refutes the answer, written before the results, as the
   commit history shows. A hypothesis added after a result is marked exploratory.
5. **Board**: the label of the study's tasks, `study:<short-name>`.
6. **Conclusion**: written when the study ends, with links to the result files; numbers are not copied by hand.

A study holds no copies of benchmark code or results. Analysis code that spans several benchmarks of the study, and
its outputs, may live in the study's directory.

## Closing a study

Write the conclusion, set the state to finished, and from then on change the directory only to fix an error. A
benchmark dropped from a study keeps its directory; the study says why it was dropped.
