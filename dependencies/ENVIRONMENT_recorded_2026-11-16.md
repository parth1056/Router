# Environment receipt — Round 1 and its repair

Recorded 2026-11-16 on the college PC. Everything below was measured on this machine. Values that
were **not** verified are listed in section 9 rather than implied. Sections 5 and 7 were corrected
after Codex review (see `RETURN_SUMMARY_REPAIR.md`, entries on temperature, imports and tokens).

## 1. Hardware

| Item | Value |
|---|---|
| OS | Windows 10.0.26300 (64-bit) |
| CPU | GenuineIntel, family 6 model 85, **24 logical cores** |
| RAM | **127.7 GB** total, 111.1 GB free at record time |
| GPU | **NVIDIA RTX A5000**, 24,564 MiB, compute capability 8.6, 23,329 MiB free |
| Driver | 596.71 (reports CUDA 13.2) |
| Disk | workspace on `E:`, **288.0 GB** free |

## 2. Python environment (isolated, project-local)

```
py -3.11 -m venv .venv                    # Python 3.11.9
.venv/Scripts/python.exe -m pip install "torch==2.13.0+cu130" --index-url .../whl/cu130
.venv/Scripts/python.exe -m pip install -e vendor/laya
.venv/Scripts/python.exe -m pip freeze > requirements.lock.txt
```

The system Python 3.11 has a CPU-only torch (`cuda.is_available() == False`) and is never used.
Verified GPU path in `.venv`:

```
torch 2.13.0+cu130 cuda 13.0 avail True
tensor op sum on cuda: 4.0
device: NVIDIA RTX A5000
```

No OS change, no driver change, no WSL, and the installed environment was preserved through the
repair — no package was downgraded on the strength of version numbers alone.

## 3. Pinned LAYA SDK

| Item | Value |
|---|---|
| Source | `https://github.com/NandhaKishorM/laya` |
| Commit | `80a1da1fa5448ea12163f4d977935625a0aea670` (`rev-parse HEAD`) |
| Version | `laya 0.4.34`, editable install |
| Lockfile | `requirements.lock.txt` (SHA-256 `53ddd1a41b51…` before the repair) |

Verified present and signature-compatible: `TrainConfig`, `load_checkpoint`, `items_from_rows`,
`train_model`, `calibration_records`, `save_checkpoint`, `LOSSES = ("soft-ce","rlcd")`,
`QTYPES = {"choice","score","noul"}`, option layouts `("sequential","parallel")`, plus
`laya.common.build_sequence` / `build_head` used by the token audit.

## 4. Pinned English checkpoint

| Item | Value |
|---|---|
| Repo | `convaiinnovations/laya` (root only) |
| **Revision** | `e333cb7c823cd1787276228260f56d02fbf5180b` |
| Payload | 807.0 MB, 5 payload files |
| Tensors | 206, **421.3M parameters**, 205 × F16 + 1 × F32 |
| Weights SHA-256 | `891102d372688fc2…` (local only, not shipped) |

Config: `max_len = 512`, `head_max_len = 192` (both match `config/policy.json`), with
`temperature = [1.6369, 1.2514, 1.9834]` and six `temperature_by_options` buckets inherited from
the checkpoint.

**Corrected statement (Codex point 5).** `calibration_records` runs the model's raw forward pass
and does **not** apply the saved runtime temperature. For a fixed binary choice, a positive shared
scalar temperature changes the probabilities but not the argmax label, so this receipt no longer
claims that raw development argmax would necessarily be contaminated. Resetting the inherited
runtime temperature and per-option overrides is still the right thing when exporting an
uncalibrated candidate and when preventing double scaling; external calibration stays external.

## 5. Token budget — measured on the SDK-assembled sequence

`build_sequence` puts the question head first and clamps the state to the remaining room, so raw
state length is not the question. Values below come from `laya.common.build_sequence` with
`max_len=512`, `head_max_len=192`, over the 100 repaired pilot rows.

| Measurement | Result |
|---|---|
| Assembled sequence tokens | p50 **206**, p95 **289**, max **301** |
| Rows with state tokens dropped | **0** |
| Head tokens (policy `route` question) | **137** of 192 budget, 2 distinct option markers |
| Markers inside `max_len` | 100/100 |
| Visibility of message / every history turn / asset block / stored evidence | 100/100 |
| Deliberately overlength fixture | **rejected** — 545 state tokens dropped, sequence clamped to 512, message no longer visible |

Successful item construction is *not* treated as proof of visibility; the span checks and the
negative fixture are what establish it.

## 6. Dependency drift vs. the SDK floor

SDK floors: `torch>=2.0`, `transformers>=4.48`, `huggingface_hub>=0.20`. Resolved:
`transformers 5.23.0`, `tokenizers 0.23.3`, `huggingface_hub 2.4.0`, `numpy 2.4.6`,
`safetensors 0.8.0`, `vegaml 0.16.3`, `cryptography 50.0.2`, `filelock 4.2.4`.

Tokenization and packing are proven under these versions by section 5. Training-time numerics
under `transformers 5.x` are **not** verified; that is the later explicit GPU smoke.

## 7. What was actually run

Round 1 (original pilot, superseded but preserved):

| Command | Result |
|---|---|
| manifest verification | 28/28 SHA-256 and sizes match |
| `python -m pipeline.alloc` (v1) | 100 rows / 57 slot groups / 40 contextual slots |
| `python -m pipeline.generate` (v1) | 100 accepted / 0 rejected |
| `python tools/validate_dataset.py --data data/pilot/train_pilot_r1.jsonl` | **passes** from the project root |

The import claim in the first plan was wrong and has been removed: running the validator by path
from the project root works because Python puts the script's directory on `sys.path`. The
`cwd=tools` form is an alternative, not a workaround for a defect, and no helper import was
changed.

Round 1 repair (current evidence):

| Command | Result |
|---|---|
| `python -m pipeline.alloc` | 49 semantic families, 100 declared variants, 10 controlled pairs (those 10 are the mixed-label families in the pilot); full plan 4000/600/400 with quotas exact |
| `python -m pipeline.generate --candidates data/pilot/candidates_r1_repair/batch_0*.json` | **100 accepted / 0 rejected**, 100/100 declared variants filled, 43 history-necessary rows |
| `python tools/validate_dataset.py --data data/pilot/train_pilot_r1_repair.jsonl` | **passes** (non-strict) |
| `python tools/validate_dataset.py --data … --strict` | **fails**: `Unaccepted row: r1r_train_0001` — expected while rows are pending |
| `python tools/self_check.py` | PASS |
| `python -m pipeline.audit` | **14/14** checks pass; 10/10 pairs; 0 review-required duplicates; no single-feature shortcut |
| `python -m pipeline.token_audit` | **passes**; overlength fixture fails as required |
| `python -m pipeline.verify_packet build` | 100 opaque IDs, packet SHA-256 `a1ab11ec…`, private mapping frozen separately |
| `python -m pipeline.regressions` | **14/14 probes behave as required** |
| `python -m pipeline.reporting` | before/after table + source patch (5 changed files) |

## 8. Files and receipts

`models/model_revision.json`, `models/download_receipt.json` (per-file SHA-256),
`reports/SHA256SUMS_round1.txt` (original capsule), `reports/manifest_round1.json`,
`logs/generation_manifest_r1_repair.json`, `logs/asset_id_map_r1_repair.json`,
`reports/round1r_audit.json`, `reports/round1r_token_audit.json`,
`reports/regressions_r1_repair.json`, `reports/round1r_allocation_summary.json`,
`reports/pilot_before_after_r1_repair.json`, `reports/source_diff_r1_repair.patch`.

## 9. Not verified here

- Loading the 421M-parameter weights and running inference (later GPU smoke / baselines).
- Any optimiser step, gradient, memory measurement or training behaviour.
- Temperature fitting or threshold selection.
- Independent blind verification (packet built; must run in a different-family session).
- Human review of the 100 candidate rows; the 600-case human test set.
- `transformers 5.x` training numerics.

## 10. Reproduction

```bash
py -3.11 -m venv .venv
.venv/Scripts/python.exe -m pip install "torch==2.13.0+cu130" --index-url https://download.pytorch.org/whl/cu130
git clone https://github.com/NandhaKishorM/laya vendor/laya
git -C vendor/laya checkout 80a1da1fa5448ea12163f4d977935625a0aea670
.venv/Scripts/python.exe -m pip install -e vendor/laya
.venv/Scripts/python.exe -m pipeline.fetch_model
.venv/Scripts/python.exe -m pipeline.alloc
.venv/Scripts/python.exe -m pipeline.generate --candidates data/pilot/candidates_r1_repair/batch_01.json \
    data/pilot/candidates_r1_repair/batch_02.json data/pilot/candidates_r1_repair/batch_03.json \
    data/pilot/candidates_r1_repair/batch_04.json data/pilot/candidates_r1_repair/batch_05.json
.venv/Scripts/python.exe tools/validate_dataset.py --data data/pilot/train_pilot_r1_repair.jsonl
.venv/Scripts/python.exe -m pipeline.audit
.venv/Scripts/python.exe -m pipeline.token_audit
.venv/Scripts/python.exe -m pipeline.verify_packet build
.venv/Scripts/python.exe -m pipeline.regressions
.venv/Scripts/python.exe -m pipeline.reporting
.venv/Scripts/python.exe -m pipeline.capsule --label repair
```
