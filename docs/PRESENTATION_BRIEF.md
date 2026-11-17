# Presentation narrative for this completed component

1. Problem: an image upload does not automatically mean an authenticity request. Route casual visual questions and discussion of prior results to BASE; activate the specialist only for a fresh image-authenticity verdict on a valid target.
2. Approach: English LAYA (ModernBERT-large encoder plus decision head), taking message/history/trusted image-state/prior-result metadata. Encoder and head fine-tuned; the image-authenticity specialist is unchanged by this experiment. Use figures/router_architecture.svg.
3. Data:2000 train/200 dev/300 test, synthetic/template-assisted and AI-reviewed. Code-controlled state/context, Qwen-generated user wording, blind Gemma critique, Codex adjudication, grouped splits and locked evaluation. Do not call it a human-labelled dataset.
4. Fit: one seed42 soft-CE run, batch16 effective, dev-selected epoch4 after seven completed epochs, about15 minutes on RTX A5000. No test-driven tuning.
5. Result:61%->98% accuracy; macro-F1 .6068->.9787; unnecessary specialist activations108->2. Compare against the original on the SAME300 frozen examples. Use routing_comparison/routing_confusion_matrices; quote percentages with their synthetic-test scope.
6. Honest boundary: all six disagreements sit in16 indirect requests and some prior gold labels are ambiguous/inconsistent. No scored label was edited. App integration and natural real-user validation are separate from the completed training/comparison.

Exact numbers and exportable tables: tables/. Method details, source hashes and captions: docs/ and archive_review/. This is supporting material, not an automatically edited main presentation.
