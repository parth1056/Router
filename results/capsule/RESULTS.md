# LAYA router: fine-tuned routing pilot result

Status: fitted, development-selected, evaluated against the pristine original on the same frozen synthetic test, exported and reload-verified. **Nothing was published and no human review is claimed.**

## Fixed test comparison (300 rows, 105 groups, unchanged)

| metric | original pretrained | routing fine-tuned |
|---|---:|---:|
| accuracy | 0.6100 | 0.9800 |
| macro_f1 | 0.6068 | 0.9787 |
| deepfake_precision | 0.4930 | 0.9821 |
| deepfake_recall | 0.9211 | 0.9649 |
| base_false_activation_rate | 0.5806 | 0.0108 |
| nll | 0.6340 | 0.1587 |
| brier | 0.2228 | 0.0199 |

| | original | fine-tuned |
|---|---:|---:|
| TP / TN / FP / FN | 105 / 78 / 108 / 9 | 110 / 184 / 2 / 4 |

Accuracy +37.00 percentage points; macro-F1 +0.3719; paired corrections 115, paired regressions 4; group-bootstrap 95% interval for the macro-F1 delta [0.3017, 0.4394] over 105 groups. Majority-BASE reference accuracy 0.62.

## Fit

| | |
|---|---|
| selection | development macro-F1, then lower BASE false activation, then lower NLL, then earlier epoch |
| selected epoch | 4 (checkpoint `epoch_04`) |
| epochs completed | 7 / 8, Development patience reached after minimum four epochs |
| train seconds | 894.0 |
| planned optimiser updates | 875 |
| peak torch allocated | 7.78 GiB |
| encoder / head weight deltas | 0.001235 / 0.006014 |
| test opened during fitting | False |

| epoch | train loss | dev macro-F1 | dev accuracy | BASE false activation |
|---|---:|---:|---:|---:|
| 1 | 0.2169 | 0.9324 | 0.9350 | 0.1032 |
| 2 | 0.0877 | 0.9674 | 0.9700 | 0.0079 |
| 3 | 0.0429 | 0.9734 | 0.9750 | 0.0317 |
| 4 | 0.0107 | 0.9785 | 0.9800 | 0.0159 |
| 5 | 0.0001 | 0.9785 | 0.9800 | 0.0159 |
| 6 | 0.0000 | 0.9785 | 0.9800 | 0.0159 |
| 7 | 0.0000 | 0.9785 | 0.9800 | 0.0159 |

Development baseline macro-F1 0.5806, accuracy 0.5900, BASE false activation 0.6508. The optional head-only recovery did not run: the primary fit already beat the baseline on development.

## Artifact

- Local checkpoint: `E:\ly project c 68\Polyvalent_LAYA_Freebuff_Handover\LAYA_Routing_Handover\LAYA_Router_2000\reviewed\runs\reviewed_router\primary\epoch_04`
- Release copy: `E:\ly project c 68\Polyvalent_LAYA_Freebuff_Handover\LAYA_Routing_Handover\LAYA_Router_2000\reviewed\runs\reviewed_router\trained_laya_router`
- Full archive (kept locally, not uploaded): `E:\ly project c 68\Polyvalent_LAYA_Freebuff_Handover\LAYA_Routing_Handover\LAYA_Router_2000\reviewed\runs\reviewed_router\trained_laya_router.zip`
- Weights SHA-256 `cbca78ad4c27a037ecf6d5caae6c427e9cc7312f2bd0eadce66a07eb659597e8`; archive SHA-256 `1eaaa973ff0bb5d158ee02df9484652d9a579e1c81756ccf07b5aabb283103c6`.
- Reload check: 24 frozen test inputs re-scored from a fresh process, predictions identical to stored: True.

## Inputs and freezes

- Data: 2,000 / 200 / 300 reviewed rows, test SHA-256 `b20ed45253dcae4f58915846ea8ae14ad0a9b9df6338e3e9f80639cae556b511`.
- Tokenizer check: no dropped state tokens, two distinct option markers, no split overlap, max assembled 314 tokens (`data/FREEZE.json`).
- Questions and serializer hashes are bound in `FINAL_EVAL_FREEZE.json`.
- Both checkpoints scored with identical inputs, questions, serializer and raw-argmax scoring; no temperature or threshold tuning; exact ties BASE.

## Limits

- One seed42 run on synthetic, template-assisted data; the test is a frozen group-held-out synthetic benchmark, not human-test or production evidence.
- The improvement is large because the original checkpoint over-fires DEEPFAKE (BASE false activation 0.5806 on this test). Further scenarios, other seeds and real app traffic are untested.
- Human review is not claimed anywhere; the labels are Codex AI adjudications.
