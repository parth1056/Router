"""Reload the exported trained artifact and confirm it reproduces the stored predictions."""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pilot_metrics import read_rows, predictions, file_sha, write_json

RUN = Path(__file__).resolve().parents[1] / 'runs/reviewed_router'
ART = RUN / 'trained_laya_router'


def main():
    import torch
    from laya.train import load_checkpoint, items_from_rows, calibration_records
    from laya.common import uses_parallel_layout

    rows = read_rows(Path(__file__).resolve().parents[1] / 'data/test.laya.jsonl')[:24]
    model, tok, cfg = load_checkpoint(str(ART))
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device).eval()
    items, skipped = items_from_rows(tok, rows, 512, 192)
    if any(skipped.values()) or len(items) != len(rows):
        raise ValueError('reload items mismatch %s' % skipped)
    records = calibration_records(model, tok, items, device, 512, 192, batch_size=8,
                                  parallel=uses_parallel_layout(cfg))
    fresh = predictions(records, rows)
    stored = {json.loads(l)['id']: json.loads(l)
              for l in (RUN / 'trained_test.jsonl').read_text(encoding='utf-8').splitlines()}
    wrong = [f['id'] for f in fresh
             if f['prediction'] != stored[f['id']]['prediction']
             or abs(f['p_deepfake'] - stored[f['id']]['p_deepfake']) > 1e-6]
    receipt = {'artifact': str(ART), 'reloaded_rows': len(fresh),
               'weights_sha256': file_sha(ART / 'model.safetensors'),
               'predictions_identical_to_stored': not wrong, 'mismatched_ids': wrong,
               'device': str(device),
               'tokenizer_files': sorted(p.name for p in (ART / 'tokenizer').iterdir()),
               'has_questions': (ART / 'questions.json').exists(),
               'has_serializer': (ART / 'input_serializer.py').exists(),
               'comparison_provenance_sha256': file_sha(ART / 'comparison_provenance.json'),
               'note': 'Fresh process, fresh checkpoint load, same 24 frozen test inputs.'}
    write_json(RUN / 'RELOAD_RECEIPT.json', receipt)
    print(json.dumps(receipt, indent=2))
    if wrong:
        raise SystemExit('reloaded artifact disagrees with stored predictions')


if __name__ == '__main__':
    main()
