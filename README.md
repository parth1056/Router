# Polyvalent BASE/DEEPFAKE router: complete experiment archive

The router fine-tuning and frozen synthetic-test comparison are complete. This archive preserves the actual selected model, complete reviewed dataset, generation/review evidence, exact project code, pinned upstream SDK source, run records and paper/presentation material. It is self-contained as an experiment record and trained-checkpoint handover; installing runtime dependencies or optionally retrieving the pristine public baseline still requires the documented environment/public files.

## Download everything, including the trained model

Install Git LFS first, then clone this repository:

```bash
git lfs install
git clone https://github.com/parth1056/Router.git
cd Router
git lfs pull
python qa/verify_pack.py
```

The model weights use Git LFS. A web download or a clone that skips LFS may contain only a small pointer; use the commands above to obtain the actual842.6MB weight file. The complete extracted experiment contents are in this repository. No extra Drive archive is needed. Python dependencies for inference are described in docs/REPRODUCE.md.

## Start here

- docs/APPROACH_AND_METHODS.md: motivation, routing boundary, actual model/data-generation approach, training settings, evaluation and limitations.
- docs/DATA_DICTIONARY.md: what every dataset structure/label/legacy flag means.
- docs/REPRODUCE.md: working verification/reload/evaluation/retraining commands and environment setup.
- archive_review/RESULTS_CODEX_REVIEW.md: independently checked results plus all six disagreements and the prior label-ambiguity issue.
- figures/ and tables/: reusable architecture/result/learning-curve SVG+PNG and numeric CSV tables; captions in docs/FIGURE_CAPTIONS.md.

## Preserved result

| Metric | Original pretrained | Fine-tuned |
|---|---:|---:|
| Accuracy |61.00%|98.00%|
| Macro-F1 |0.6068|0.9787|
| DEEPFAKE precision |49.30%|98.21%|
| DEEPFAKE recall |92.11%|96.49%|
| Incorrect DEEPFAKE activations |108/186|2/186|
| Missed DEEPFAKE requests |9/114|4/114|

2,000 train /200 dev /300 frozen synthetic test;105 test groups. One seed42 encoder+head fit, development-selected epoch4, seven epochs completed. The full result and bootstrap are in results/comparison.json. No claim of98% production accuracy: the data are template-assisted and AI-labelled. All six disagreements fall in16 indirect requests; some of their frozen labels are ambiguous/inconsistent. Those scored labels and predictions are unchanged.

## Actual model and evidence

model/trained_laya_router/ contains the actual selected weights, tokenizer, encoder/agent configs, question definitions, serializer and comparison provenance. The weight SHA-256 cbca78ad4c27a037ecf6d5caae6c427e9cc7312f2bd0eadce66a07eb659597e8 matches the selected checkpoint and remote reload receipt. Its safetensors structure was independently checked on this laptop. No new model fitting occurred while assembling this archive.

data/ contains all three canonical files actually used and their reviewed readable source files; exact hashes are bound by REVIEW_LOCK.json and data/FREEZE.json. Use pilot_label, not historical proposed_route. Old accepted_for_training=false flags preserve historical/final-acceptance semantics; explicit reviewed pilot labels and APPROVAL.json governed the completed authorised fit. No human annotation is claimed.

dataset_evidence/ now contains the ENTIRE original pre-review return: raw writer/retry events, blind critic inputs/judgements/private mapping, original plans, prompts, recipes and seed; its original manifest fully verifies. review/ contains the final decision/exclusion/addition records. results/ includes actual predictions and longer training logs; results/capsule/ preserves the original23-entry results capsule verbatim. archive_review/ preserves the original handover README/manifests and Codex review/verification notes.

tools/ contains unchanged copies of the exact reviewed fitting/evaluation scripts in a runnable layout. code/ retains Freebuff's original archived layout and generation scripts for provenance. The old README's root environment path has been supplied. Historical instruction files (STATUS.md, PASTE_IN_FREEBUFF.txt, RUN_REVIEWED_DATA.md and code/generation models.json) describe earlier workflow stages; they are evidence, not permission or instructions to regenerate/retrain anything now.

## Verify without models or GPU

From this extracted archive's ROOT, with standard Python:

```powershell
python qa/verify_pack.py
python qa/self_check.py
python qa/check_reviewed_data.py
python qa/verify_results.py
```

These check the complete archive hashes (including weights), canonical data/labels/split separation and all600 stored raw predictions/metrics. They do not load a model or change scored data. Output reports go to verification_output/ and are not new training results. A model reload needs installed LAYA/PyTorch dependencies; see docs/REPRODUCE.md. This laptop's new check did not independently run neural inference; the college fresh-process24-item reload receipt remains preserved.

## External prerequisites, deliberately explicit

The pristine public baseline's842.6MB weight file is not duplicated. Its exact revision and five payload hashes are in dependencies/baseline_revision.json and baseline_download_receipt.json; tools/fetch_pristine_baseline.py retrieves/verifies it only when explicitly run. The trained model is fully bundled.

The exact public SDK source snapshot and licence are bundled in dependencies/. Fit-time core runtime versions are in environment.json; the dated16-November full college pip record is retained under dependencies/ with its provenance. A fresh full pip-freeze at the exact fit moment was not supplied, so this is not a bit-for-bit offline Python/CUDA environment image. No credentials, virtual environments or model caches are included.

The fine-tuning/comparison milestone is concluded. Application integration, real-user/human validation, other languages and further seeds are separate unperformed work; no extra generation or training is needed merely to preserve or present this completed result. The existing main research paper/PPT were not silently edited by this archive assembly.
