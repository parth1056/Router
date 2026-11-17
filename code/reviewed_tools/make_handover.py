"""Build one complete handover archive: fine-tuned weights, reviewed data, all evidence and code."""
import hashlib, json, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]          # LAYA_Router_2000/reviewed
PACK = HERE.parent                                   # LAYA_Router_2000
ROOT = HERE.parents[1]                               # LAYA_Routing_Handover
RUN = HERE / 'runs/reviewed_router'
ART = RUN / 'trained_laya_router'
CAP = HERE / 'capsule'
BUNDLE = PACK / 'bundle'
OUT = HERE / 'LAYA_FineTuned_Router_Handover_2026-11-17.zip'
PREFIX = 'LAYA_FineTuned_Router_Handover_2026-11-17'

files = []          # (source path, archive name)


def add(src, arc):
    p = Path(src)
    if not p.is_file():
        print('MISSING', p)
    elif arc not in {a for _, a in files}:
        files.append((p, arc))


def add_tree(root, prefix, skip_suffix=('.pyc',), skip_dirs=('__pycache__',)):
    root = Path(root)
    for p in sorted(root.rglob('*')):
        if not p.is_file() or p.suffix in skip_suffix:
            continue
        if any(part in skip_dirs for part in p.relative_to(root).parts):
            continue
        arc = prefix + '/' + p.relative_to(root).as_posix()
        if arc not in {a for _, a in files}:
            files.append((p, arc))


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def main():
    # 1. fine-tuned model
    add_tree(ART, 'model/trained_laya_router')
    # 2. reviewed dataset + review provenance (the pack as supplied)
    add_tree(HERE / 'data', 'data')
    add_tree(HERE / 'review', 'review')
    add_tree(HERE / 'config', 'config')
    add_tree(HERE / 'qa', 'qa')
    for name in ('APPROVAL.json', 'REVIEW_LOCK.json', 'RUN_REVIEWED_DATA.md',
                 'PASTE_IN_FREEBUFF.txt', 'data/FREEZE.json'):
        add(HERE / name, name)
    # the review pack's own file manifest; the archive manifest occupies the root name
    add(HERE / 'MANIFEST.json', 'review_pack/MANIFEST.json')
    # 3. results
    for name in ('FINISHED.json', 'comparison.json', 'comparison.md', 'FINAL_EVAL_FREEZE.json',
                 'RELOAD_RECEIPT.json', 'commands.json', 'baseline_test.jsonl',
                 'trained_test.jsonl', 'baseline_test.receipt.json', 'trained_test.receipt.json',
                 'primary/selection.json', 'primary/history.json', 'primary/baseline_dev.json',
                 'primary/training_receipt.json'):
        add(RUN / name, 'results/' + name)
    # 4. task logs (full, they are small text)
    for name in ('primary_training.log', 'baseline_test.log', 'trained_test.log',
                 'comparison.log', 'freeze_selection.log'):
        add(RUN / name, 'results/logs/' + name)
    add_tree(CAP, 'results/capsule')
    # 5. code that produced and evaluated everything
    add_tree(HERE / 'tools', 'code/reviewed_tools')
    add_tree(HERE / 'reference', 'code/reference')
    for name in ('plan_2000.py', 'run_2000.py', 'bundle_2000.py', 'laya_core.py'):
        add(PACK / 'tools' / name, 'code/generation/' + name)
    for name in ('PLAN_SUMMARY.json', 'recipes.json'):
        add(PACK / 'data/corpus2' / name, 'code/generation/' + name)
    add(PACK / 'reference/pair_renderer.py', 'code/generation/pair_renderer.py')
    add(PACK / 'reference/state_recipes.py', 'code/generation/state_recipes.py')
    add(PACK / 'seed/pair_recipe_bank.json', 'code/generation/pair_recipe_bank.json')
    add(PACK / 'seed/input_schema.json', 'code/generation/input_schema.json')
    add(PACK / 'data_plan/models.json', 'code/generation/models.json')
    # 6. pre-review dataset evidence (2,500 rows with critic views)
    for name in ('REVIEW_ROWS.jsonl', 'manifest.json', 'REVIEW_SUMMARY.md', 'README.md',
                 'failed_slots.jsonl'):
        add(BUNDLE / name, 'dataset_evidence/' + name)
    add_tree(BUNDLE / 'candidates', 'dataset_evidence/candidates')
    # 7. project status
    add(ROOT / 'STATUS.md', 'STATUS.md')

    man = json.loads((HERE / 'MANIFEST.json').read_text(encoding='utf-8'))
    rev = json.loads((ROOT / 'models/model_revision.json').read_text(encoding='utf-8'))
    final = json.loads((RUN / 'FINISHED.json').read_text(encoding='utf-8'))
    comp = final['comparison']
    env = json.loads((CAP / 'environment.json').read_text(encoding='utf-8'))
    weights = sha(ART / 'model.safetensors')

    readme = f"""# LAYA routing fine-tune: complete evidence archive

Built 17 November 2026. One seed42 supervised fit of the pinned English LAYA checkpoint on
2,000 Codex-reviewed synthetic routing rows, development-selected checkpoint, fixed-test
comparison against the pristine original, exported and reload-verified.

**This is a synthetic pilot result.** It is not human-test, production or multi-seed evidence,
and no human review is claimed for any row.

## The claim, in numbers

| | original pretrained | routing fine-tuned |
|---|---:|---:|
| accuracy | {comp['baseline']['accuracy']:.4f} | {comp['trained']['accuracy']:.4f} |
| macro-F1 | {comp['baseline']['macro_f1']:.4f} | {comp['trained']['macro_f1']:.4f} |
| DEEPFAKE precision | {comp['baseline']['deepfake_precision']:.4f} | {comp['trained']['deepfake_precision']:.4f} |
| DEEPFAKE recall | {comp['baseline']['deepfake_recall']:.4f} | {comp['trained']['deepfake_recall']:.4f} |
| BASE false activation | {comp['baseline']['base_false_activation_rate']:.4f} | {comp['trained']['base_false_activation_rate']:.4f} |
| NLL | {comp['baseline']['nll']:.4f} | {comp['trained']['nll']:.4f} |

Accuracy {comp['delta_accuracy_pp']:+.2f} percentage points, macro-F1 {comp['delta_macro_f1']:+.4f},
paired corrections {comp['paired_wrong_to_right']}, paired regressions {comp['paired_right_to_wrong']},
group-bootstrap 95% interval for the macro-F1 delta
[{comp['group_bootstrap_delta_macro_f1_95pct'][0]:.4f}, {comp['group_bootstrap_delta_macro_f1_95pct'][1]:.4f}]
over {comp['bootstrap_groups']} groups. Majority-BASE reference accuracy {comp['majority_BASE']['accuracy']:.2f}.

## What is inside

| path | contents |
|---|---|
| `model/trained_laya_router/` | the fine-tuned checkpoint: `model.safetensors` ({weights[:16]}…), encoder config, tokenizer, `questions.json`, `input_serializer.py`, `comparison_provenance.json` |
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

- checkpoint revision `{rev['revision']}`, SDK commit `{rev['sdk_commit']}`
- frozen test data SHA-256 `{final['test_sha256']}`; all split hashes in `data/FREEZE.json`
- questions / serializer hashes bound in `results/FINAL_EVAL_FREEZE.json`
- training: {env['gpu']}, torch {env['torch']}, transformers {env['transformers']}, CUDA {env['cuda']}

## Honest limits

- One seed42 run; the test is a frozen group-held-out synthetic benchmark of 300 rows in 105
  comparison groups, written by the same generator pipeline as training and reviewed by AI.
- The gain is large because the original checkpoint over-fires DEEPFAKE (BASE false activation
  {comp['baseline']['base_false_activation_rate']:.4f} on this test). Other scenarios, other seeds,
  real app traffic and human raters remain untested.
- Labels are Codex AI adjudications, not human annotation; `human_reviewed` is false and
  `accepted_for_training` keeps its original meaning.
"""
    checks = []
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for src, arc in files:
            ctype = zipfile.ZIP_STORED if src.suffix == '.safetensors' else zipfile.ZIP_DEFLATED
            z.write(src, PREFIX + '/' + arc, compress_type=ctype)
            checks.append((sha(src), 'sha256', PREFIX + '/' + arc))
        z.writestr(PREFIX + '/README.md', readme)
        checks.append((hashlib.sha256(readme.encode()).hexdigest(), 'sha256', PREFIX + '/README.md'))
        sums = ''.join('%s  %s\n' % (h, n) for h, _, n in checks)
        z.writestr(PREFIX + '/SHA256SUMS.txt', sums)
        payload = {'archive': OUT.name, 'built': '2026-11-17', 'files': len(checks),
                   'weights_sha256': weights,
                   'baseline_checkpoint': {'repo': rev['repo'], 'revision': rev['revision'],
                                           'sdk_commit': rev['sdk_commit'],
                                           'weights_sha256': env['source_weights_sha256'],
                                           'bundled': False},
                   'comparison': {'baseline': comp['baseline'], 'trained': comp['trained'],
                                  'delta_accuracy_pp': comp['delta_accuracy_pp'],
                                  'delta_macro_f1': comp['delta_macro_f1']},
                   'sha256sums_entries': len(checks),
                   'note': 'SHA256SUMS.txt covers every file except itself and this manifest.'}
        z.writestr(PREFIX + '/MANIFEST.json', json.dumps(payload, indent=2) + '\n')
    print(json.dumps({'archive': str(OUT), 'sha256': sha(OUT),
                      'bytes': OUT.stat().st_size, 'files': len(checks) + 2}, indent=2))


if __name__ == '__main__':
    main()
