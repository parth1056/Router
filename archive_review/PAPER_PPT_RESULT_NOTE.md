# LAYA result for later manuscript and presentation updates

Suggested factual wording:

"We fine-tuned the English LAYA decision model for BASE/DEEPFAKE routing using 2,000 AI-reviewed synthetic training examples and selected the checkpoint on 200 development examples. On a frozen 300-example synthetic test comprising 105 scenario groups, accuracy increased from 61.0% for the original pretrained checkpoint to 98.0%, and macro-F1 increased from 0.6068 to 0.9787. False specialist activations decreased from 108 to 2 among 186 BASE-labelled requests. The paired macro-F1 improvement was 0.3719, with a scenario-group bootstrap interval of [0.3017, 0.4394]."

Required scope alongside these numbers: one seed42 run, template-assisted synthetic data and Codex-AI-adjudicated labels; no independent human/production evaluation. Six disagreements cluster in 16 indirect requests, and a few of their frozen labels are ambiguous/inconsistent with analogous training cases. Therefore describe agreement on this benchmark, not 98% real-world routing accuracy. Do not rewrite the scored test to improve the result. No automatic paper/PPT edits have been made.

Method details: English checkpoint revision e333cb7c823cd1787276228260f56d02fbf5180b; SDK commit 80a1da1fa5448ea12163f4d977935625a0aea670; encoder+head soft-CE; effective batch16; selected epoch4 after seven completed epochs; primary training 893.96s on RTX A5000; max allocated7.78GiB. Identical runtime inputs/questions/raw argmax for original and trained; no fitted temperature or test-driven threshold. Canonical metadata-based readiness is distinct from intent; no other domain routes in this experiment.

See routing/reviews/Router_Results/CODEX_REVIEW.md, CODEX_VERIFICATION.json and preserved original capsule for full provenance. The trained checkpoint is exported on the college PC and has not been integrated or independently tested on real application traffic here.
