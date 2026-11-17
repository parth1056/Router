"""Assemble the small results capsule (metrics, predictions, hashes; no weights)."""
import json, platform, shutil, subprocess, sys, zipfile, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
RUN = HERE / 'runs/reviewed_router'
OUT = HERE / 'capsule'


def sha(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


ITEMS = [
    (RUN / 'FINISHED.json', 'FINISHED.json'),
    (RUN / 'comparison.json', 'comparison.json'),
    (RUN / 'comparison.md', 'comparison.md'),
    (RUN / 'FINAL_EVAL_FREEZE.json', 'FINAL_EVAL_FREEZE.json'),
    (RUN / 'RELOAD_RECEIPT.json', 'RELOAD_RECEIPT.json'),
    (RUN / 'baseline_test.jsonl', 'predictions/baseline_test.jsonl'),
    (RUN / 'trained_test.jsonl', 'predictions/trained_test.jsonl'),
    (RUN / 'baseline_test.receipt.json', 'predictions/baseline_test.receipt.json'),
    (RUN / 'trained_test.receipt.json', 'predictions/trained_test.receipt.json'),
    (RUN / 'commands.json', 'commands.json'),
    (RUN / 'primary/selection.json', 'training/selection.json'),
    (RUN / 'primary/history.json', 'training/history.json'),
    (RUN / 'primary/baseline_dev.json', 'training/baseline_dev.json'),
    (RUN / 'primary/training_receipt.json', 'training/training_receipt.json'),
    (HERE / 'data/FREEZE.json', 'data/FREEZE.json'),
    (HERE / 'reviewed/../data/FREEZE.json', 'data/FREEZE.json'),
]
LOG_TAIL = 40


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / 'predictions').mkdir(parents=True)
    (OUT / 'training').mkdir(parents=True)
    (OUT / 'data').mkdir(parents=True)
    (OUT / 'logs').mkdir(parents=True)
    done = set()
    for src, dst in ITEMS:
        if dst in done or not Path(src).exists():
            continue
        shutil.copyfile(src, OUT / dst)
        done.add(dst)
    for name in ('primary_training.log', 'baseline_test.log', 'trained_test.log',
                 'comparison.log', 'freeze_selection.log'):
        src = RUN / name
        if src.exists():
            lines = src.read_text(encoding='utf-8', errors='replace').splitlines()
            (OUT / 'logs' / name).write_text('\n'.join(lines[-LOG_TAIL:]) + '\n',
                                             encoding='utf-8')
    import torch, transformers
    env = {'python': sys.version.split()[0], 'platform': platform.platform(),
           'torch': torch.__version__, 'transformers': transformers.__version__,
           'cuda': torch.version.cuda, 'cuda_available': torch.cuda.is_available(),
           'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
           'gpu_total_memory_bytes': torch.cuda.get_device_properties(0).total_memory
           if torch.cuda.is_available() else None,
           'laya_sdk_commit': json.loads((HERE.parent.parent / 'models/model_revision.json')
                                         .read_text(encoding='utf-8'))['sdk_commit'],
           'checkpoint_revision': json.loads((HERE.parent.parent / 'models/model_revision.json')
                                             .read_text(encoding='utf-8'))['revision'],
           'source_weights_sha256': sha(HERE.parent.parent / 'models/laya-english/model.safetensors'),
           'captured_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (OUT / 'environment.json').write_text(json.dumps(env, indent=2) + '\n', encoding='utf-8')
    final = json.loads((RUN / 'FINISHED.json').read_text(encoding='utf-8'))
    comp = final['comparison']
    selection = json.loads((RUN / 'primary/selection.json').read_text(encoding='utf-8'))
    receipt = json.loads((RUN / 'primary/training_receipt.json').read_text(encoding='utf-8'))
    reload_receipt = json.loads((RUN / 'RELOAD_RECEIPT.json').read_text(encoding='utf-8'))
    md = ['# LAYA router: fine-tuned routing pilot result', '',
          'Status: fitted, development-selected, evaluated against the pristine original on the '
          'same frozen synthetic test, exported and reload-verified. **Nothing was published and '
          'no human review is claimed.**', '',
          '## Fixed test comparison (300 rows, 105 groups, unchanged)', '',
          '| metric | original pretrained | routing fine-tuned |', '|---|---:|---:|']
    for k in ('accuracy', 'macro_f1', 'deepfake_precision', 'deepfake_recall',
              'base_false_activation_rate', 'nll', 'brier'):
        md.append('| %s | %.4f | %.4f |' % (k, comp['baseline'][k], comp['trained'][k]))
    md += ['', '| | original | fine-tuned |', '|---|---:|---:|',
           '| TP / TN / FP / FN | %d / %d / %d / %d | %d / %d / %d / %d |' % (
               comp['baseline']['tp'], comp['baseline']['tn'], comp['baseline']['fp'],
               comp['baseline']['fn'], comp['trained']['tp'], comp['trained']['tn'],
               comp['trained']['fp'], comp['trained']['fn']),
           '', 'Accuracy %+.2f percentage points; macro-F1 %+.4f; paired corrections %d, '
           'paired regressions %d; group-bootstrap 95%% interval for the macro-F1 delta '
           '[%.4f, %.4f] over %d groups. Majority-BASE reference accuracy %.2f.' % (
               comp['delta_accuracy_pp'], comp['delta_macro_f1'],
               comp['paired_wrong_to_right'], comp['paired_right_to_wrong'],
               comp['group_bootstrap_delta_macro_f1_95pct'][0],
               comp['group_bootstrap_delta_macro_f1_95pct'][1], comp['bootstrap_groups'],
               comp['majority_BASE']['accuracy']), '',
          '## Fit', '',
          '| | |', '|---|---|',
          '| selection | development macro-F1, then lower BASE false activation, then lower NLL, '
          'then earlier epoch |',
          '| selected epoch | %d (checkpoint `%s`) |' % (selection['selected_epoch'],
                                                        Path(selection['selected_checkpoint']).name),
          '| epochs completed | %d / 8, %s |' % (receipt['epochs_completed'],
                                                 receipt['stop_reason']),
          '| train seconds | %.1f |' % receipt['seconds'],
          '| planned optimiser updates | %d |' % receipt[
              'planned_optimizer_updates_for_completed_epochs'],
          '| peak torch allocated | %.2f GiB |' % (receipt['peak_torch_allocated_bytes'] / 2**30),
          '| encoder / head weight deltas | %.6f / %.6f |' % (
              receipt['weight_probe_changes']['encoder_max_probe_delta'],
              receipt['weight_probe_changes']['head_max_probe_delta']),
          '| test opened during fitting | %s |' % receipt['test_opened'], '',
          '| epoch | train loss | dev macro-F1 | dev accuracy | BASE false activation |',
          '|---|---:|---:|---:|---:|']
    for h in json.loads((RUN / 'primary/history.json').read_text(encoding='utf-8')):
        md.append('| %d | %.4f | %.4f | %.4f | %.4f |' % (
            h['epoch'], h['train_loss'], h['dev']['macro_f1'], h['dev']['accuracy'],
            h['dev']['base_false_activation_rate']))
    md += ['', 'Development baseline macro-F1 %.4f, accuracy %.4f, BASE false activation %.4f. '
           'The optional head-only recovery did not run: the primary fit already beat the '
           'baseline on development.' % (selection['baseline_dev']['macro_f1'],
                                         selection['baseline_dev']['accuracy'],
                                         selection['baseline_dev']['base_false_activation_rate']),
           '', '## Artifact', '',
           '- Local checkpoint: `%s`' % selection['selected_checkpoint'],
           '- Release copy: `%s`' % final['release_dir'],
           '- Full archive (kept locally, not uploaded): `%s`' % final['full_model_archive'],
           '- Weights SHA-256 `%s`; archive SHA-256 `%s`.' % (
               reload_receipt['weights_sha256'], final['archive_sha256']),
           '- Reload check: %d frozen test inputs re-scored from a fresh process, predictions '
           'identical to stored: %s.' % (reload_receipt['reloaded_rows'],
                                         reload_receipt['predictions_identical_to_stored']),
           '', '## Inputs and freezes', '',
           '- Data: 2,000 / 200 / 300 reviewed rows, test SHA-256 `%s`.' % final['test_sha256'],
           '- Tokenizer check: no dropped state tokens, two distinct option markers, no split '
           'overlap, max assembled 314 tokens (`data/FREEZE.json`).',
           '- Questions and serializer hashes are bound in `FINAL_EVAL_FREEZE.json`.',
           '- Both checkpoints scored with identical inputs, questions, serializer and raw-argmax '
           'scoring; no temperature or threshold tuning; exact ties BASE.', '',
           '## Limits', '',
           '- One seed42 run on synthetic, template-assisted data; the test is a frozen '
           'group-held-out synthetic benchmark, not human-test or production evidence.',
           '- The improvement is large because the original checkpoint over-fires DEEPFAKE '
           '(BASE false activation %.4f on this test). Further scenarios, other seeds and real '
           'app traffic are untested.' % comp['baseline']['base_false_activation_rate'],
           '- Human review is not claimed anywhere; the labels are Codex AI adjudications.']
    (OUT / 'RESULTS.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    files = {}
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name != 'MANIFEST.json':
            files[str(p.relative_to(OUT)).replace('\\', '/')] = {'sha256': sha(p),
                                                                'bytes': p.stat().st_size}
    manifest = {'capsule': 'LAYA_Reviewed_Router_Results_2026-11-17',
                'status': final['status'], 'test_sha256': final['test_sha256'],
                'weights_sha256': reload_receipt['weights_sha256'],
                'archive_sha256': final['archive_sha256'],
                'counts': {'test_rows': comp['baseline']['n'],
                           'bootstrap_groups': comp['bootstrap_groups']},
                'metrics': {'baseline': comp['baseline'], 'trained': comp['trained'],
                            'delta_accuracy_pp': comp['delta_accuracy_pp'],
                            'delta_macro_f1': comp['delta_macro_f1']},
                'excluded': ['model weights', 'venv', 'caches', 'secrets'],
                'files': files}
    (OUT / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    archive = HERE / 'LAYA_Reviewed_Router_Results_2026-11-17.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(OUT).as_posix())
    print(json.dumps({'capsule': str(archive), 'sha256': sha(archive),
                      'files': len(files), 'bytes': archive.stat().st_size}, indent=2))


if __name__ == '__main__':
    main()
