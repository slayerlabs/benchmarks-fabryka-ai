"""Scoring of the pinned task: the lm-eval `ifeval` functions, with the model's thinking cut off first.

Bielik 11B v3.1 sometimes writes its reasoning into the answer and ends it with `</think>` (the Fabryka API
cannot switch thinking off; see README, "Deviations"). Only the text after the last `</think>` is scored, as
with an API that returns reasoning in a separate field. A response without `</think>` is scored unchanged.
The raw response stays in the lm-eval sample log (`resps`).
"""

from lm_eval.tasks.ifeval.utils import agg_inst_level_acc  # noqa: F401
from lm_eval.tasks.ifeval.utils import process_results as _process_results

THINK_END = "</think>"


def strip_thinking(response):
    if THINK_END not in response:
        return response
    return response.rsplit(THINK_END, 1)[1].lstrip()


def process_results(doc, results):
    return _process_results(doc, [strip_thinking(results[0])])
