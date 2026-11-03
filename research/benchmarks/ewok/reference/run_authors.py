"""Stage B: the EWoK authors' code in LOGPROBS mode, their code unchanged.

Calls `ewok.evaluate.model.Model` and `ewok.evaluate.evaluator.Evaluator._evaluate_logprobs` from
`ewok-core/ewok-paper` @ 9e40d30e on the datasets in `analyses/data.zip` (5 versions, 11 `testsuite-*.csv` files
each). Writes results as their `__main__.py` does: one `results-<domain>.csv` per dataset file. Those files contain
record text, so keep them outside the repo (EWoK TERMS_OF_USE).

`outlines` (0.0.13) is needed only by the choice and likert modes and does not install next to a torch for RTX 50xx.
It is replaced by empty modules; the code that computes logprobs does not use them.

  python run_authors.py --ewok-paper <ewok-paper clone> --model <gpt2-xl dir> --data <unpacked data.zip> \
      --out <dir outside the repo> [--precision bf16|fp32] [--versions 0,1,2,3,4]
"""
import argparse
import pathlib
import sys
import types


def stub_outlines():
    for m in ["outlines", "outlines.models", "outlines.models.transformers", "outlines.text",
              "outlines.text.generate", "outlines.text.generate.sample"]:
        sys.modules[m] = types.ModuleType(m)
    sys.modules["outlines.models.transformers"].Transformer = None
    sys.modules["outlines.models.transformers"].TransformerTokenizer = None
    sys.modules["outlines.text"].generate = None
    sys.modules["outlines.text.generate.sample"].greedy = None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ewok-paper", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--data", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--precision", default="bf16")  # default `hf_precision` in ewok/evaluate/args.py
    p.add_argument("--versions", default="0,1,2,3,4")
    a = p.parse_args()

    stub_outlines()
    sys.path.insert(0, a.ewok_paper)
    import pandas as pd
    from ewok.evaluate.evaluator import Evaluator
    from ewok.evaluate.model import Model

    # other arguments as the defaults in args.py: no optimisation, no trust_remote_code; Evaluator: batch 1
    model = Model(a.model, a.precision, False, False, "\n\n", 20)
    ev = Evaluator("logprobs", batch_size=1)
    datasets = pathlib.Path(a.data) / "data" / "outputs_20240429" / "dataset" / "ewok1.0"
    for v in map(int, a.versions.split(",")):
        cfg = next(datasets.glob(f"dataset-cfg=*__vers={v}"))
        for f in sorted(cfg.glob("testsuite-*.csv")):
            # the first line of the file is the EWoK canary (the authors' analysis reads with skip=1)
            suite = types.SimpleNamespace(samples=pd.read_csv(f, skiprows=1), identifier=f.stem)
            result = ev._evaluate_logprobs(suite, model)
            o = pathlib.Path(a.out) / f"vers={v}" / f"results-{f.stem.removeprefix('testsuite-')}.csv"
            o.parent.mkdir(parents=True, exist_ok=True)
            result._df.to_csv(o, index=False)
            print(v, f.stem, flush=True)


if __name__ == "__main__":
    main()
