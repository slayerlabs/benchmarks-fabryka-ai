"""Scoring without a model: two log-likelihoods, shared continuation, earlier option wins a tie."""


def gold_index(doc):
    """Dataset answer \"1\" or \"2\" -> 0 or 1, as lm-eval `doc_to_text` does."""
    return int(doc["answer"]) - 1


def continuation(doc):
    idx = doc["sentence"].index("_") + 1
    return doc["sentence"][idx:].strip()


def contexts(doc):
    idx = doc["sentence"].index("_")
    return [doc["sentence"][:idx] + doc[opt] for opt in ("option1", "option2")]


def predict(logliki):
    """Index of the higher log-likelihood. A tie takes the earlier option, as lm-eval argmax does."""
    return max(range(len(logliki)), key=lambda i: logliki[i])


def acc(doc, logliki):
    return float(predict(logliki) == gold_index(doc))
