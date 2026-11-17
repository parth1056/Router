# Router approach, dataset and experimental method

## Purpose and boundary

Polyvalent's general-chat interface needs to choose BASE or the DEEPFAKE specialist. This experiment concerns only these two routes, in English. LAYA consumes text and trusted application state; it does not inspect image pixels or determine the actual REAL/FAKE image verdict.

DEEPFAKE requires a current request for a new/repeated image-authenticity judgement and a uniquely resolvable available supported image. Ordinary appearance/content/OCR/caption requests, general deepfake discussion, methods/capability questions, explanations of saved results, and unclear/unavailable/unsupported targets use BASE. Interpret neutral continuations using the immediately relevant operation or offer; previous authenticity results do not make the route sticky. Other project domains are outside this routing experiment.

## Runtime representation and architecture

Input contains exactly message, history, assets, active_image_id and last_analysis. Asset records contain id, kind, availability and support. The stored analysis contains the earlier target, verdict and optional evidence/confidence; these are simulated conversation fixtures, not new forensic measurements. The serializer converts those five fields to text. The SDK packs the fixed typed-choice question head first, followed by the serialized state. English LAYA uses a ModernBERT-large encoder and its typed decision head. Encoder and head parameters were updated. The saved weight file contains 421,293,830 tensor elements across 206 tensors; config and actual tensors are included. See figures/router_architecture.svg.

The two choice descriptions are in config/questions.json. Raw logits are compared; exact ties select BASE. Model softmax is a routing probability, distinct from a deepfake detector's image-authenticity confidence. Application adapter loading and real-user integration were not evaluated here.

## Synthetic data and review

Code fixes attachment state, actor roles, assistant operation/offer and neutral current messages in controlled context pairs. Pinned local Qwen3-32B Q4_K_M writes natural user utterances; pinned Gemma3-27B Q4_K_M supplies blind, fallible critique. Model digests, prompts, actual plans/recipes, per-request events, raw outputs, twelve replacement attempts and critic private mapping are in dataset_evidence/. The models ran sequentially on the college RTX A5000 at context4096. The 2,500-row pre-review return includes100 previously curated seed inputs;2,400 other slots were generated. Twelve first-pass text failures were re-sampled once, with original failures retained. Writer readback agreed with every condition and has no independent evidentiary value.

Codex reviewed actual inputs, inherited the earlier review for100 verified unchanged seeds, and corrected92 labels:78 train,6 dev,8 test.24 copied user-as-assistant result exchanges and60 further normalised duplicate training inputs were excluded.84 separately disclosed Codex-AI-authored TRAIN-ONLY examples cover practical intent, target readiness and context gaps; they are not Qwen or human output. ROW_DECISIONS, EXCLUSIONS and ADDED_TRAINING_CASES record this lineage. Critic figures95/700 train,16/200 dev and18/300 test are DISAGREEMENTS, not agreements. No vote or class-balance quota overrides actual task meaning.

Final splits:

| Split | N | BASE | DEEPFAKE | Source family IDs | Comparison groups |
|---|---:|---:|---:|---:|---:|
| Train |2000|1177|823|730|725|
| Development |200|126|74|70|60|
| Test |300|186|114|105|105|

Each training source family has at most four variants. Family, conservative group and normalised full-input overlaps across splits are absent; repeated dialogue/state contrasts remain grouped. History is present in748 training rows, not necessarily required by every one. Controlled context pairs and scenario templates make this synthetic/template-assisted data, not2,500 independent natural users. Dev/test runtime inputs were not edited during final review; only their recorded pre-scoring labels changed. Human annotation is not claimed. Historical accepted_for_training=false flags are explained in DATA_DICTIONARY.md; explicit pilot_label and APPROVAL.json governed the actual authorised exploratory fit.

The fixed tokenizer check found two distinct option markers, no dropped state tokens and maximum assembled sequence314 tokens (train314/dev279/test275), against a512 total and192 head limit.

## Training configuration

| Setting | Value |
|---|---|
| English source checkpoint | convaiinnovations/laya, e333cb7c823cd1787276228260f56d02fbf5180b |
| SDK commit |80a1da1fa5448ea12163f4d977935625a0aea670|
| Optimisation |AdamW, encoder+head, soft cross-entropy|
| Learning rates |encoder2.5e-5; head1e-4|
| SDK defaults used |weight decay0.01; gradient clip1.0; minimum LR1e-6; cosine annealing; label smoothing0|
| Seed |42, one run|
| Micro-batch / accumulation |4 /4, effective batch16|
| Choice ordering |choice-option shuffling during fitting; canonical ordering for scoring|
| Epoch budget |maximum8; minimum4 before patience3 can stop|
| Model selection |dev macro-F1, lower BASE false activation, lower NLL, earlier epoch|
| Calibration |none; exported identity temperatures; raw-logit scoring|
| Runtime |Python3.11.9; torch2.13.0+cu130; transformers5.23.0; CUDA13.0; RTX A5000|

Defaults are recoverable from the bundled pinned SDK, and explicit overrides are in tools/train_laya.py/config/run.json. Seven epochs completed; epoch4 was selected. Epochs5-7 tied F1 but had worse NLL. There were875 planned optimizer updates across seven completed epochs and500 planned by the selected checkpoint; actual AMP-executed step count was not separately instrumented. Training elapsed893.96s; pipeline receipt958.63s; peak torch allocation8,352,930,304 bytes=7.78GiB=8.35GB. The optional dev-only head recovery was not triggered. No test-driven tuning or fitted test threshold occurred.

## Evaluation and result

Compare the pristine source checkpoint with the dev-selected saved checkpoint on the identical frozen300-row synthetic test, same questions, serializer and raw argmax. Corrected labels were locked before scoring. Per-item logits/predictions are in results/; selected weights and comparison provenance are in model/. Accuracy61%->98%, macro-F1.6068->.9787, BASE false activations108->2 among186 BASE rows, DEEPFAKE precision.4930->.9821 and recall.9211->.9649. Paired corrections115/regressions4. The105-group1000-resample bootstrap (seed42) gives a macro-F1 difference interval[.3017,.4394]. It measures uncertainty within this fixed synthetic cohort, not variability across training seeds or users. Always-BASE accuracy is62%.

## Limitations needed in a paper or presentation

One seed, synthetic/template-assisted cases, shared generation pipeline and AI-reviewed labels. Six remaining disagreements all fall in16 indirect requests (10/16 agreement there). Some prior labels for similar vague prompts are inconsistent; archive_review/RESULTS_CODEX_REVIEW.md identifies these. No scored input/label was changed to improve the result.98% is agreement with this locked benchmark, not established real-world accuracy. Several wrong or debatable decisions have high softmax confidence; confidence alone does not resolve intent ambiguity. No production deployment, human evaluation, multilingual result or domain-adapter retraining is established by this run.

## Source and citation locations

Exact public SDK source and licence are bundled under dependencies/; model repository and revision are in dependencies/baseline_revision.json. Upstream software: https://github.com/NandhaKishorM/laya/tree/80a1da1fa5448ea12163f4d977935625a0aea670 ; model checkpoint: https://huggingface.co/convaiinnovations/laya/tree/e333cb7c823cd1787276228260f56d02fbf5180b . Consult the upstream source/model citation instructions when incorporating this result into the main paper. This archive supplements evidence; it does not automatically edit the existing manuscript/PPT.
