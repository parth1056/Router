# Reproduction and use from the extracted archive root

## 1. Verify the saved experiment using only Python

```powershell
python qa/verify_pack.py
python qa/self_check.py
python qa/check_reviewed_data.py
python qa/verify_results.py
```

The first checks every archived payload against MANIFEST.json, including the842.6MB model. The next two check code/serialization/metrics and the locked2,500 canonical/source rows. The final recomputes predictions' argmax/softmax agreement, metrics, group bootstrap and development selection from saved records. It writes verification_output/, and performs no inference/training. The historical manifests under review_pack/ and archive_review/ describe their original layouts; root MANIFEST.json is authoritative for this consolidated package. dataset_evidence/manifest.json and results/capsule/MANIFEST.json remain complete original sub-archives.

## 2. Runtime setup

Use Python3.11.9 and a suitable PyTorch runtime. The measured fit used NVIDIA RTX A5000, torch2.13.0+cu130, CUDA13.0, transformers5.23.0 and SDK commit80a1da1fa5448ea12163f4d977935625a0aea670. The exact SDK zip and licence are in dependencies/. A reference setup on a compatible CUDA13 machine is:

```powershell
py -3.11 -m venv .venv
& ".venv/Scripts/python.exe" -m pip install "torch==2.13.0+cu130" --index-url https://download.pytorch.org/whl/cu130
& ".venv/Scripts/python.exe" -m pip install "transformers==5.23.0"
& ".venv/Scripts/python.exe" -m pip install "dependencies/laya-sdk-80a1da1fa5448ea12163f4d977935625a0aea670.zip"
```

Use dependencies/requirements_recorded_2026-11-16.txt as the dated full resolution reference (including NumPy, tokenizers, safetensors and the pinned editable SDK line), not proof of a newly captured fit-time environment. Installing that file unchanged would fetch the editable Git SDK separately; the bundled zip is the same source commit. Installation/retraining commands were NOT executed on this laptop. Hardware/library changes can change low-level numerics. Reuse the existing compatible college environment where possible.

## 3. Reload the actual bundled trained model

```powershell
& ".venv/Scripts/python.exe" tools/reload_model.py --model model/trained_laya_router --device cuda --count 24 --out verification_output/fresh_reload.json
```

A CPU-compatible PyTorch installation can use --device cpu (slower); no CUDA is required for that helper. It compares class predictions to the stored results, not exact floating-point logits. This fresh check does not fit or tune anything. Model-loading dependencies must be installed; the stdlib archive check alone cannot prove neural-runtime compatibility.

For all300 stored test examples with the original CUDA evaluation code, use a NEW output path:

```powershell
& ".venv/Scripts/python.exe" tools/evaluate_laya.py --model model/trained_laya_router --data data/test.laya.jsonl --out verification_output/trained_rescore.jsonl
```

## 4. Optional pristine baseline retrieval and re-scoring

```powershell
python tools/fetch_pristine_baseline.py --dest retrieved_baseline/laya-english
& ".venv/Scripts/python.exe" tools/evaluate_laya.py --model retrieved_baseline/laya-english --data data/test.laya.jsonl --out verification_output/baseline_rescore.jsonl
```

Retrieval downloads about846MB from the pinned public Hugging Face revision and verifies the original five file hashes; it requires internet and does not run automatically. The baseline source weight SHA-256 must be891102d372688fc2a094dac56a384bc537b87c63f21f9f3dac0be2b7cbc8d86c. Keep original results unchanged. Recomputed scores can be inspected with the stored labels/grouping, but they are not permission to tune against or relabel the test.

## 5. Optional retraining reproduction (not required to conclude this run)

The exact original project scripts are at root tools/, where their config/approval paths resolve. Use pristine weights and NEW output/freeze paths; never overwrite the completed run/model/data. The preserved original commands and hardware are in results/commands.json and environment.json.

```powershell
& ".venv/Scripts/python.exe" tools/check_and_freeze.py --train data/train.laya.jsonl --dev data/dev.laya.jsonl --test data/test.laya.jsonl --model retrieved_baseline/laya-english --out verification_output/reproduction_FREEZE.json
& ".venv/Scripts/python.exe" tools/run_training_and_comparison.py --model retrieved_baseline/laya-english --train data/train.laya.jsonl --dev data/dev.laya.jsonl --test data/test.laya.jsonl --freeze verification_output/reproduction_FREEZE.json --out new_runs/reproduction
```

This is the predeclared seed42 recipe, not a guarantee of bit-identical training on another stack. The original comparison is already complete. Generation sources are historical scripts tied to their original project layout; actual raw outputs/prompts/plans and all final reviewed data are preserved, so no synthesis is necessary for scoring/retraining. Reconstructing their original generator workspace is distinct from reproducing the saved supervised fit.

## 6. What must remain unchanged

No scored input/label, no model weight, no prior raw evidence or source provenance was changed by consolidation. Use the same five-field serializer and route question for live integration. Return only BASE/DEEPFAKE; the deepfake specialist's REAL/FAKE judgement is a separate output. The result remains a single-seed synthetic benchmark with an acknowledged indirect-label ambiguity limitation.
