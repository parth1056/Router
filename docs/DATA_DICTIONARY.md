# Data and file dictionary

Every JSONL line is one example. The three *_reviewed.jsonl files contain complete runtime input, proposed and reviewed labels, reasoning and provenance. The three *.laya.jsonl files are the exact canonical exports consumed by the completed run (2000 train/200 dev/300 test), bound by REVIEW_LOCK.json and data/FREEZE.json.

## Readable records

- input.message: current request.
- input.history: ordered recent user/assistant turns (empty when unnecessary).
- input.assets: file IDs, image/video/document/audio kind, available/missing/expired status and supported/unsupported/unknown support.
- input.active_image_id: selected target or null. Other explicit unambiguous references can resolve the requested target.
- input.last_analysis: earlier image verdict/evidence/confidence or null. These fixtures describe prior conversation state; LAYA produces route labels, not new authenticity verdicts.
- pilot_label: FINAL AI-reviewed target actually used by the fit. pilot_label_source/reason explain its origin.
- proposed_route/source_proposed_route and label_reason/label_source: earlier generation-stage suggestions. These can be stale or disagree with pilot_label; never train using them in place of pilot_label.
- id: row identifier. family_id: related source cases. template_group_id: conservative scenario/dialogue clustering used as group_id in exported records.
- category/recipe_group/mode: coverage and construction metadata, not runtime features or ground truth.
- provenance/source_input_sha256/review_decision: traceability to actual generation/curation.
- ai_reviewed=true and human_reviewed=false: Codex AI review, not human annotation.
- accepted_for_training=false/status: retained historical workflow/final-acceptance flags. They do NOT exclude these records from this already completed exploratory fit. Explicit pilot labels and APPROVAL.json authorised the run. Flags were preserved rather than rewritten to claim a kind of acceptance/review that never occurred.

## Canonical exports

state is a JSON string containing only the five runtime fields. Escaped quotes are normal JSON-within-JSON formatting. questions.route defines a typed choice with the fixed BASE and DEEPFAKE descriptions. gold.route.label and one-hot probabilities are supervised targets, not observed model confidence. IDs, source labels, grouping, reviewer explanations and provenance remain outside state. At inference only state/questions are supplied; gold is not an input.

## Evidence and results

review/ROW_DECISIONS.jsonl records every original-row decision and all84 additions; review/EXCLUSIONS.jsonl records84 removed training slots. dataset_evidence/ is the COMPLETE original2,500-row pre-review return including raw writer/critic evidence; its own manifest is now fully satisfiable. results/ contains actual predictions, receipts, run history and freezes; results/capsule/ preserves the original small results capsule verbatim, including historical truncated logs. Root results/logs contains the longer logs supplied by Freebuff. Neither is silently substituted for the other.

model/trained_laya_router is the actual exported selected checkpoint, tokenizer, configs, routing question and serializer. No actual image dataset or deepfake specialist weights are needed for this text/state routing experiment. The pristine public LAYA baseline weights are not duplicated; exact retrieval hashes and a helper are supplied.
