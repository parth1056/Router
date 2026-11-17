# Reviewed LAYA data: proceed to fitting and comparison

Decision: APPROVED_FOR_FITTING_AFTER_PINNED_TOKENIZER_INPUT_CHECKS. The single Codex data-review checkpoint is complete. This pack replaces the original proposed-label data for this run. No further generation, teacher qualification, blind critique or data-only return is needed. Work in the SAME Freebuff project and existing environment. Nothing has been trained in this pack.

## What was reviewed and changed

All 2,500 actual inputs were reviewed, including inherited review of 100 unchanged curated seed inputs. Original capsule SHA-256: 3bec2683239192f24fd8594e579abf29787a292305ca988ec1712511c1b4833c. All 39 internal hashes, 1,200 blind inputs/judgements and the 300 generation / 12 retry / 1,200 critic request-response records checked. Critic figures 95/700, 16/200, 18/300 are DISAGREEMENTS, not agreement counts.

92 label corrections: 78 train, 6 development, 8 test. Examples: vague oddness alone is BASE clarification; location/date provenance is not image-manipulation detection; asking how to verify an image or whether a tool exists is answered with BASE; a literal request to run an authenticity check remains DEEPFAKE even when its command name is in quotation marks. A stored verdict does not override the most recent OCR/caption/explanation task.

Removed 24 malformed training exchanges in which the user's earlier line copied the assistant result verbatim, plus 60 remaining normalised duplicate training inputs. Added exactly 84 distinct, disclosed CODEX-AI-authored training cases covering ordinary intent, actual manipulation requests, target readiness/selection and contextual continuations. They are not Qwen output or human-authored data. No development/test input was rewritten or replaced. Only their pre-scoring label corrections changed. Original evidence stays unchanged on both machines.

Final working dataset:

| Split | Rows | BASE | DEEPFAKE |
|---|---:|---:|---:|
| Train | 2000 | 1177 | 823 |
| Development | 200 | 126 | 74 |
| Test | 300 | 186 | 114 |

Training has 730 source family IDs (max four rows per family) and 725 conservative scenario/dialogue clusters; history is present on 748 training rows (not a claim that every history is necessary). Development/test have 60/105 conservative comparison groups. Repeated dialogue across state contrasts is clustered. This is template-assisted synthetic evaluation, not 300 independent human users, a production certification or a guarantee of improvement. Exact 60/40 balance is not required; do not force the corrected labels back to a quota.

## Files to use

Use data/train.laya.jsonl, data/dev.laya.jsonl, data/test.laya.jsonl AS SUPPLIED. They are already exported using the same existing serializer/questions. The reviewed source rows carry explicit pilot_label and pilot_label_source. The historical proposed_route is retained for traceability and must NEVER overwrite pilot_label. human_reviewed=false and accepted_for_training=false retain their original meanings; APPROVAL.json explicitly authorises this AI-labelled exploratory fit. Review data must never appear in the serialized runtime state except the five input fields; labels are targets only.

REVIEW_LOCK.json binds canonical inputs, source rows, questions and serializer. review/ROW_DECISIONS.jsonl records every source-row decision and addition, with input hashes and reasons. review/curate_review.py and audit_review.py are provenance/reproduction sources referring to the preserved original return under their original review layout; do not rerun them to regenerate the reviewed data. No further synthesis is necessary.

## Execute now

Find the already downloaded pinned English LAYA checkpoint and the existing venv on the college PC; substitute those actual paths below. Keep SDK commit 80a1da1fa5448ea12163f4d977935625a0aea670 and checkpoint revision e333cb7c823cd1787276228260f56d02fbf5180b. No new checkpoint downloads, environment reinstall or unrelated process changes. Unload task-owned Ollama models before fitting.

```powershell
& "../.venv/Scripts/python.exe" qa/verify_pack.py
& "../.venv/Scripts/python.exe" qa/self_check.py
& "../.venv/Scripts/python.exe" qa/check_reviewed_data.py
& "../.venv/Scripts/python.exe" tools/check_and_freeze.py --train data/train.laya.jsonl --dev data/dev.laya.jsonl --test data/test.laya.jsonl --model "../models/laya-english" --out data/FREEZE.json
& "../.venv/Scripts/python.exe" tools/run_training_and_comparison.py --model "../models/laya-english" --train data/train.laya.jsonl --dev data/dev.laya.jsonl --test data/test.laya.jsonl --freeze data/FREEZE.json --out runs/reviewed_router
```

The actual pinned tokenizer check is still required on the college PC. It must report no dropped state tokens and two distinct option markers; never silently truncate meaningful history. Input-only checks may inspect test inputs; no test predictions before candidate selection. Use the supplied original and trained questions, serializer and raw-argmax scoring identically.

Primary: seed42, full-encoder soft-CE fit, effective batch16, up to eight epochs, best development-selected checkpoint (at most 1,000 planned updates). Preserve the implemented optional ONE development-only head recovery when its condition is met. No test-driven tuning, repeated qualification or perfect-score gate. If a mechanical execution error occurs, fix it with a recorded diff and resume the failed stage; preserve trained artifacts instead of restarting successful work. If a genuine input defect blocks the frozen-data check, report its actual row and error; do not silently alter held-out data or make up completion.

Finish fitting, freeze checkpoint selection, evaluate pristine original and trained checkpoints separately on the SAME unchanged test, compare paired per-item predictions, and export a reloadable trained artifact. Return the small results capsule with metrics, confusion matrices, class precision/recall, per-item raw predictions, train/dev history, errors, commands, versions, weights hashes and timing. Keep full model weights locally in the exported model archive; no automatic upload/publication. A negative or inconclusive comparison is an honest result, not permission to change the test.
