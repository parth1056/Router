# LAYA routing fine-tuning: fixed synthetic-test comparison

| Metric | Original pretrained LAYA | Routing fine-tuned LAYA |
|---|---:|---:|
| accuracy | 0.6100 | 0.9800 |
| macro_f1 | 0.6068 | 0.9787 |
| deepfake_precision | 0.4930 | 0.9821 |
| deepfake_recall | 0.9211 | 0.9649 |
| base_false_activation_rate | 0.5806 | 0.0108 |

Accuracy difference: +37.00 percentage points.
Macro-F1 difference: +0.3719.
Paired corrections/regressions: 115 / 4.

Observed result on a frozen synthetic test, one selected seed42 run; not human-test or production-accuracy evidence. Bootstrap groups must represent shared scenario/template dependence.
