# LAYA routing pilot — result review, 17 November 2026

Decision: the requested dataset / fine-tuning / original-versus-trained synthetic-test comparison milestone is COMPLETE. The returned evidence supports the reported large improvement. The exported checkpoint is a candidate for app integration; no app deployment or real-traffic validation is established here. No additional training or test tuning was performed during this review.

## Verified result

The supplied 44,010-byte capsule has SHA-256 c29b803201a027a152cadb29356866932b78247c40b1f97e318dd8bba0f4206d. Its 22 manifest entries (23 ZIP entries including the manifest) all verify. Returned train/dev/test hashes exactly match the previously locked reviewed files (2000/200/300); question and serializer hashes match too. The inference question hash differs from the freeze question-file hash only because one hashes sorted parsed JSON and the other hashes raw file bytes; both resolve correctly.

Checked all 600 returned predictions against actual test IDs, labels, family/group IDs, raw-logit argmax and softmax probabilities. Independently recomputed confusion counts, accuracy, macro-F1, DEEPFAKE precision/recall, false activation, NLL and Brier; reproduced the paired comparison and 105-group bootstrap interval (only floating-point summation roundoff in a few probability metrics). Original vs trained: accuracy 61.00% / 98.00%; macro-F1 0.6068 / 0.9787; false DEEPFAKE activations 108/186 (58.06%) / 2/186 (1.08%); TP/TN/FP/FN 105/78/108/9 vs 110/184/2/4. There are 115 paired corrections and 4 regressions. Always-BASE accuracy is 62%, so the original pretrained model is slightly below that simple accuracy reference; fine-tuning is far above both.

History verifies epoch 4 selection under the predeclared development macro-F1, false activation, NLL and earlier-epoch order. Epochs 5–7 tie its F1 and false activation but have higher NLL, so epoch 4 is the correct selected checkpoint. Seven epochs completed in 893.96 seconds; 875 planned optimizer updates across the executed run, 500 planned by the selected epoch. Actual AMP optimizer steps were not instrumented. Both encoder and head probes changed. No optional head recovery appears in commands. Full pipeline receipt is 958.63 seconds.

Memory-unit correction: 8,352,930,304 peak allocated bytes = 8.35 decimal GB = 7.78 GiB, not 8.35 GiB. GPU memory reported here is torch allocated memory, not necessarily total process/device occupancy. Approximately 5.8 seconds for each 300-row batched test is not a measured interactive per-request latency.

Pristine source weights hash 891102d372688fc2a094dac56a384bc537b87c63f21f9f3dac0be2b7cbc8d86c; trained weights cbca78ad4c27a037ecf6d5caae6c427e9cc7312f2bd0eadce66a07eb659597e8; full model archive 1eaaa973ff0bb5d158ee02df9484652d9a579e1c81756ccf07b5aabb283103c6. Remote 24-item fresh-process release reload receipt is internally consistent. Weights are on the college PC, absent from this small capsule; this review did not independently reload them locally.

## Error analysis and a prior label-review limitation

All six remaining test disagreements occur in the 16-item indirect_authenticity category: 10/16 agreement there, versus 284/284 on the other included categories. All 120 controlled contextual rows are correct under the frozen labels. These small, synthetic slices are descriptive, not population estimates.

Some indirect-request gold labels are ambiguous or inconsistent with the conservative boundary used in the earlier Codex data review. Specifically, test_s099_1 ("Something looks off ... Can you check it?") is DEEPFAKE, while closely analogous vague training requests were changed to BASE; test_s102_2 ("not sure ... double-check") has the same issue. Conversely, test_s100_4 ("a legitimate shot") is BASE whereas similar legitimacy questions elsewhere were treated as authenticity intent. Other disagreements include an explicit authenticity concern (test_s099_2) and ambiguous naturalness/second-opinion wording. This is a limitation of Codex's earlier label adjudication, not exclusively a model failure. The six disagreeing predictions are generally highly confident, so softmax confidence alone would not resolve this ambiguity.

Do not change any scored test input or label, silently relabel these as correct, or recompute a more flattering headline. Keep 98% as measured agreement with this locked AI-labelled synthetic benchmark. A later genuinely independent application check can clarify natural wording prospectively. The large overall gain remains supported, but the result does not establish 98% real-world accuracy or universal understanding of indirect requests.

## Completion and next use

No new model qualification or dataset round is required to finish this bounded experiment. Preserve the selected epoch_04 release and original evidence. The next product step is integration using the identical five-field input serializer and BASE/DEEPFAKE labels, retaining readiness checks and stored-evidence handling. Do not confuse LAYA routing probability with the deepfake detector's REAL/FAKE confidence. Further domain/frontend work or training is outside this completed run unless requested.

Source: returned/; machine-readable verification: CODEX_VERIFICATION.json; all six error inputs/predictions: TEST_ERRORS.jsonl; rerunnable verification: verify_results.py. One seed, template-assisted synthetic data, AI-reviewed labels and 105 test clusters remain explicit limitations. No human annotation, production deployment or publication is claimed.
