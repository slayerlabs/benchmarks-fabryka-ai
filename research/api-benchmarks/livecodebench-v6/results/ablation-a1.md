| run | repetition_penalty | top_k | pass@1 (file) | pass@1 (paired) |
|---|---|---|---|---|
| lfm3-1.7b | 1.1 | 50 | 72.23 | 72.23 |
| lfm3-1.7b-cardsampling | 1.0 | 0 | 72.89 | 72.89 |

| Δ (original − ablation), pp | paired SE | 90% CI | TOST p | verdict | n | excluded |
|---|---|---|---|---|---|---|
| -0.66 | 0.93 | [-2.20, +0.87] | 0.0762 | not shown equivalent (margin ±2 pt) | 1055 | 0 |

McNemar (descriptive): passed only with repetition_penalty 1.1 / top_k 50: 45; only with the card's sampling: 52; exact two-sided p = 0.543

A1 not shown equivalent: both numbers are reported (lfm3-1.7b 72.23, lfm3-1.7b-cardsampling 72.89); the card-sampling one is the headline for comparisons with the card's 73.46
