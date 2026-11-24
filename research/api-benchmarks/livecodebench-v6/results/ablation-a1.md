| run | repetition_penalty | top_k | pass@1 (file) | pass@1 (paired) |
|---|---|---|---|---|
| lfm3-1.7b | 1.1 | 50 | 72.04 | 72.04 |
| lfm3-1.7b-cardsampling | 1.0 | 0 | 73.08 | 73.08 |

| Δ (original − ablation), pp | paired SE | 90% CI | TOST p | verdict | n | excluded |
|---|---|---|---|---|---|---|
| -1.04 | 0.94 | [-2.59, +0.51] | 0.155 | not shown equivalent (margin ±2 pt) | 1055 | 0 |

McNemar (descriptive): passed only with repetition_penalty 1.1 / top_k 50: 44; only with the card's sampling: 55; exact two-sided p = 0.315

A1 not shown equivalent: both numbers are reported (lfm3-1.7b 72.04, lfm3-1.7b-cardsampling 73.08); the card-sampling one is the headline for comparisons with the card's 73.46
