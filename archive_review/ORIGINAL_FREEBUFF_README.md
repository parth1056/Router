# LAYA routing fine-tune: complete evidence archive

Built 17 November 2026. One seed42 supervised fit of the pinned English LAYA checkpoint on
2,000 Codex-reviewed synthetic routing rows, development-selected checkpoint, fixed-test
comparison against the pristine original, exported and reload-verified.

**This is a synthetic pilot result.** It is not human-test, production or multi-seed evidence,
and no human review is claimed for any row.

## The claim, in numbers

| | original pretrained | routing fine-tuned |
|---|---:|---:|
| accuracy | 0.6100 | 0.9800 |
| macro-F1 | 0.6068 | 0.9787 |
| DEEPFAKE precision | 0.4930 | 0.9821 |
| DEEPFAKE recall | 0.9211 | 0.9649 |
| BASE false activation | 0.5806 | 0.0108 |
| NLL | 0.6340 | 0.1587 |

Accuracy +37.00 percentage points, macro-F1 +0.3719,
paired corrections 115, paired regressions 4,
group-bootstrap 95% interval for the macro-F1 delta
[0.3017, 0.4394]
over 105 groups. Majority-BASE reference accuracy 0.62.

## What is inside

| path | contents |
|---|---|
| `model/trained_laya_router/` | the fine-tuned checkpoint: `model.safetensors` (cbca78ad4c27a037…), encoder config, tokenizer, `questions.json`, `input_serializer.py`, `comparison_provenance.json` |
| `data/` | reviewed `train/dev/test.laya.jsonl` plus the reviewed source rows, `FREEZE.json` with split hashes and tokenizer-check results |
| `review/` | every row decision, exclusion, added case, review receipt and the curating scripts |
| `dataset_evidence/` | the pre-review 2,500-row bundle (`REVIEW_ROWS.jsonl`), its manifest, critic coverage and summary |
| `results/` | comparison JSON/MD, per-item predictions with raw logits for both checkpoints, dev history, training receipt, reload receipt, logs |
| `code/` | the exact generation, review-export, training, evaluation and comparison code |
| `environment.json` | Python/torch/transformers/CUDA/GPU versions, SDK commit, checkpoint revision |
| `STATUS.md` | project status at handover |
| `SHA256SUMS.txt` + `MANIFEST.json` | hash of every file in this archive |

## How to verify the claim

```powershell
# 1. hashes
& "<venv>/Scripts/python.exe" -c "import hashlib,pathlib; ..."   # or: sha256sum -c SHA256SUMS.txt
# 2. the checkpoint reloads and reproduces stored predictions
& "<venv>/Scripts/python.exe" code/reviewed_tools/reload_check.py
# 3. re-run the fixed-test scoring from scratch (baseline and trained, same inputs)
& "<venv>/Scripts/python.exe" code/reviewed_tools/evaluate_laya.py --model model/trained_laya_router --data data/test.laya.jsonl --out <new>.jsonl
```

The original checkpoint is not bundled (842 MB, public, pinned): the exact revision,
source-weights SHA-256 and download receipt are in `environment.json` and
`review/REVIEW_RECEIPT.json`.

## Pinned inputs

- checkpoint revision `e333cb7c823cd1787276228260f56d02fbf5180b`, SDK commit `80a1da1fa5448ea12163f4d977935625a0aea670`
- frozen test data SHA-256 `b20ed45253dcae4f58915846ea8ae14ad0a9b9df6338e3e9f80639cae556b511`; all split hashes in `data/FREEZE.json`
- questions / serializer hashes bound in `results/FINAL_EVAL_FREEZE.json`
- training: NVIDIA RTX A5000, torch 2.13.0+cu130, transformers 5.23.0, CUDA 13.0

## Honest limits

- One seed42 run; the test is a frozen group-held-out synthetic benchmark of 300 rows in 105
  comparison groups, written by the same generator pipeline as training and reviewed by AI.
- The gain is large because the original checkpoint over-fires DEEPFAKE (BASE false activation
  0.5806 on this test). Other scenarios, other seeds,
  real app traffic and human raters remain untested.
- Labels are Codex AI adjudications, not human annotation; `human_reviewed` is false and
  `accepted_for_training` keeps its original meaning.
