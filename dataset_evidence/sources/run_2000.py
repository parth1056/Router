"""Generate and blind-critique the approved corpus.

Code owns the runtime state, the speaker roles, the operative offer and the neutral current
message. The pinned generator writes user utterances only. Batched jobs keep the number of model
calls small; every slot is assembled on its own so one bad response cannot damage another job.
"""
import argparse
import collections
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import laya_core as L  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'data/corpus2'
GEN = ROOT / 'runs/corpus2_generation'
RETRY = ROOT / 'runs/corpus2_retry'
REVIEW = ROOT / 'runs/corpus2_review'
SPLITS = ('train', 'dev', 'test')
BATCH = 8

ASSISTANT_SPEECH = [
    'would you like me to', 'shall i ', 'should i run', 'i can analyze', 'i can analyse',
    'i can run', 'i can check', 'i can help you', 'i will analyze', 'i will analyse',
    "i'll run", "i'll check", 'one moment', 'i have analyzed', 'i have analysed',
]

PROMPT = """You write natural English end-user requests for a two-route image router dataset.

You write USER utterances only. The runtime state, asset IDs, availability, support, the selected
image, the stored result, both speaker roles, the assistant turn and the neutral current message
are fixed by code. Never output an assistant line, an offer, or any state field.

Rules:
- One request per declared slot, under 28 words, natural for the scenario and the stated context.
- Vary the wording across slots: short, casual and polite forms. Do not write formal requests with
  "real or fake" every time, and do not make every refusal or negative sound casual.
- The user must never offer a service or speak as an assistant ("I can analyse that for you",
  "Would you like me to...", "Let me run it").
- Never repeat the fixed current message, and never add a second user or assistant turn.
- For a context-pair slot, your request is the EARLIER user turn that the fixed assistant turn
  replies to, so it must make that assistant turn a natural answer.
- Do not mention asset IDs, provenance, fixtures, labels or metadata.
- No markdown and no category names.

writer_route_readback is your own reading of the finished row (earlier request, fixed assistant
turn, current message). It is not ground truth; report disagreement honestly rather than forcing
agreement with the stated generation condition.
"""


def load_plan():
    jobs = []
    for split in SPLITS:
        for j in json.loads((PLAN / ('%s_jobs.json' % split)).read_text(encoding='utf-8')):
            j['split'] = split
            jobs.append(j)
    return jobs


def context_note(job, spec):
    """What the user can see, without asset IDs, labels or metadata field names."""
    state = job['runtime_state'] if job['mode'] == 'context_pair' else spec['runtime_state']
    ids = [a['id'] for a in state['assets']]
    if not ids:
        return 'No image is attached in this conversation.'
    if len(ids) > 1:
        selection = 'the attached image is selected' if state['active_image_id'] else \
            'two images are attached and neither is selected'
        note = 'Two images are attached; ' + selection + '.'
    else:
        a = state['assets'][0]
        if a['kind'] != 'image':
            note = 'The attachment is a %s, not an image.' % a['kind']
        elif a['availability'] == 'missing':
            note = 'The image the user refers to is no longer available.'
        elif a['availability'] == 'expired':
            note = 'The image the user refers to has expired.'
        elif a['support'] == 'unsupported':
            note = 'The attached image is not supported by the image check.'
        elif a['support'] == 'unknown':
            note = 'It is unknown whether the attached image is supported.'
        else:
            note = 'One attached image, available and supported.'
    la = state['last_analysis']
    if la is not None:
        note += ' An earlier check was recorded with verdict %s.' % la['verdict']
    return note


def pack(jobs):
    """Group plan jobs into requests of at most BATCH slots."""
    slots = []
    for job in jobs:
        for spec in job['variants']:
            entry = {'job': job, 'spec': spec}
            slots.append(entry)
    out = []
    for i in range(0, len(slots), BATCH):
        out.append(slots[i:i + BATCH])
    return out


def batch_payload(chunk):
    rows = []
    for e in chunk:
        job, spec = e['job'], e['spec']
        row = {'slot_id': spec['slot_id'], 'scene': job['scene'], 'category': spec['category'],
               'intended_route': spec['intended_route'], 'brief': spec['request_brief'],
               'context': context_note(job, spec)}
        if job['mode'] == 'context_pair':
            row['earlier_request_expected_to_precede'] = spec['assistant_reply']
            row['current_message_fixed_by_code'] = job['fixed_current_message']
        rows.append(row)
    ids = [r['slot_id'] for r in rows]
    schema = {'type': 'object', 'additionalProperties': False, 'required': ['variants'],
              'properties': {'variants': {
                  'type': 'array', 'minItems': len(ids), 'maxItems': len(ids),
                  'items': {'type': 'object', 'additionalProperties': False,
                            'required': ['slot_id', 'request', 'writer_route_readback'],
                            'properties': {'slot_id': {'enum': ids},
                                           'request': {'type': 'string', 'minLength': 1,
                                                       'maxLength': 300},
                                           'writer_route_readback': {'enum': ['BASE', 'DEEPFAKE']}}}}}}
    return {'model': None, 'users': rows, 'schema': schema}


def generation_request(model, chunk, index):
    payload = batch_payload(chunk)
    request = {'model': model,
               'messages': [{'role': 'system', 'content': PROMPT},
                            {'role': 'user', 'content': 'Write the user utterances for these slots.\n'
                                                        + L.canonical({'slots': payload['users']})}],
               'format': payload['schema'], 'stream': False, 'keep_alive': '5m',
               'options': L.options(True, index), 'think': False}
    return request


def slot_problems(request_text, job, spec):
    errs = []
    text = request_text.strip()
    low = ' ' + L.norm_text(text) + ' '
    if not text:
        errs.append('empty_request')
    if len(text) > 300:
        errs.append('request_too_long')
    for pat in ASSISTANT_SPEECH:
        if pat in low:
            errs.append('user_speaks_as_assistant')
            break
    state = job['runtime_state'] if job['mode'] == 'context_pair' else spec['runtime_state']
    for a in state['assets']:
        if a['id'] in text:
            errs.append('asset_id_in_user_text')
            break
    if job['mode'] == 'context_pair' and \
            L.norm_text(job['fixed_current_message']) == L.norm_text(text):
        errs.append('request_repeats_current_message')
    return errs


def assemble(job, spec, text):
    state = job['runtime_state'] if job['mode'] == 'context_pair' else spec['runtime_state']
    out = {'message': job['fixed_current_message'] if job['mode'] == 'context_pair' else text,
           'history': ([{'role': 'user', 'content': text},
                        {'role': 'assistant', 'content': spec['assistant_reply']}]
                       if job['mode'] == 'context_pair' else []),
           'assets': copy.deepcopy(state['assets']),
           'active_image_id': state['active_image_id'],
           'last_analysis': copy.deepcopy(state['last_analysis'])}
    L.check(out, L.input_schema())
    ids = [a['id'] for a in out['assets']]
    if len(ids) != len(set(ids)) or any(not i.strip() for i in ids):
        raise ValueError('empty or duplicate asset ID')
    if out['active_image_id'] is not None and out['active_image_id'] not in ids:
        raise ValueError('active image is not a declared asset')
    if job['mode'] == 'context_pair':
        if [t['role'] for t in out['history']] != ['user', 'assistant']:
            raise ValueError('pair roles must be user then assistant')
        if out['history'][1]['content'] != spec['assistant_reply']:
            raise ValueError('assistant turn is not the code-owned reply')
    elif out['history']:
        raise ValueError('single rows must have empty history')
    return out


def row_record(job, spec, state, pid, model, digest, req_sha):
    return {'id': spec['slot_id'], 'slot_id': spec['slot_id'], 'packet_id': pid,
            'family_id': job['family_id'], 'job_id': job['job_id'], 'split': job['split'],
            'scenario': job['scene'], 'recipe_group': job['recipe_group'], 'mode': job['mode'],
            'category': spec['category'], 'proposed_route': spec['intended_route'],
            'label_source': 'generation_condition_ai_check_pending',
            'input': state,
            'label_reason': '%s / %s generation condition; %s' % (
                job['recipe_group'], spec['category'],
                'code-owned offer, roles and neutral continuation' if job['mode'] == 'context_pair'
                else 'code-owned state; model-written user request'),
            'provenance': {'generator': model, 'generator_digest': digest,
                           'generation_request_sha256': req_sha, 'split': job['split'],
                           'family_id': job['family_id'], 'source_slot': spec['slot_id'],
                           'assistant_turn_owner': 'code' if job['mode'] == 'context_pair' else 'n/a'},
            'status': 'raw_candidate_unaccepted', 'human_reviewed': False}


def generate(model, out, limit=None):
    if model != L.CONFIG['generator_candidate']:
        raise ValueError('only the pinned generator may run')
    client = L.Client()
    pin = client.pin(model)
    if L.CONFIG['expected_digests'].get(model) != pin['digest']:
        raise RuntimeError('digest differs from the pinned value')
    jobs = load_plan()
    chunks = pack(jobs)
    if limit:
        chunks = chunks[:limit]
    manifest = {'mode': 'corpus2_user_utterances', 'model': model, 'model_digest': pin['digest'],
                'model_metadata': pin,
                'plan_sha256': {s: L.sha((PLAN / ('%s_jobs.json' % s)).read_bytes()) for s in SPLITS},
                'prompt_sha256': L.sha(PROMPT.encode()),
                'policy_sha256': L.sha((ROOT / 'config/routing_policy.md').read_bytes()),
                'runner_sha256': L.sha(Path(__file__).read_bytes()),
                'options_template': L.options(True), 'batch_slots': BATCH,
                'seed_rule': 'qualification_seed + zero-based request index',
                'slots_planned': sum(len(j['variants']) for j in jobs)}
    out, completed = L.init_run(out, manifest)
    rows, failures, raw = [], [], []
    for index, chunk in enumerate(chunks):
        case_id = 'batch_%04d' % index
        req = generation_request(model, chunk, index)
        req_sha = L.sha(L.canonical(req).encode())
        saved = completed.get(case_id)
        if saved and saved['request_sha256'] != req_sha:
            raise RuntimeError('saved request differs for ' + case_id)
        e = saved or L.execute(client, out, req, case_id, pin['digest'])
        raw.append({'batch': case_id, 'valid': bool(e.get('valid')), 'error': e.get('error'),
                    'request_sha256': e['request_sha256'],
                    'content': e.get('response', {}).get('message', {}).get('content', '')})
        got = {}
        if e.get('valid'):
            got = {v['slot_id']: v for v in e['parsed']['variants']}
        for entry in chunk:
            job, spec = entry['job'], entry['spec']
            slot = got.get(spec['slot_id'])
            if slot is None:
                failures.append({'slot_id': spec['slot_id'], 'family_id': job['family_id'],
                                 'split': job['split'],
                                 'error': 'job_invalid: %s' % e.get('error') if not e.get('valid')
                                 else 'missing slot in response'})
                continue
            errs = slot_problems(slot['request'], job, spec)
            if errs:
                failures.append({'slot_id': spec['slot_id'], 'family_id': job['family_id'],
                                 'split': job['split'], 'error': ';'.join(sorted(set(errs)))})
                continue
            try:
                state = assemble(job, spec, slot['request'])
            except (ValueError, KeyError, TypeError) as exc:
                failures.append({'slot_id': spec['slot_id'], 'family_id': job['family_id'],
                                 'split': job['split'], 'error': str(exc)})
                continue
            pid = 'pkt_' + L.sha((pin['digest'] + '|' + spec['slot_id']).encode())[:16]
            rec = row_record(job, spec, state, pid, model, pin['digest'], req_sha)
            rec['writer'] = {'writer_route_readback': slot['writer_route_readback']}
            rows.append(rec)
    rows.sort(key=lambda r: r['id'])
    L.dump_rows(out / 'generated_rows.jsonl', rows)
    L.dump_rows(out / 'raw_writer_outputs.jsonl', raw)
    failed = sorted({f['slot_id'] for f in failures})
    per_split = {}
    for split in SPLITS:
        cs = [r for r in rows if r['split'] == split]
        per_split[split] = {'rows': len(cs),
                            'BASE': sum(r['proposed_route'] == 'BASE' for r in cs),
                            'DEEPFAKE': sum(r['proposed_route'] == 'DEEPFAKE' for r in cs)}
    receipt = {'model': model, 'digest': pin['digest'], 'requests': len(chunks),
               'slots_planned': manifest['slots_planned'], 'rows': len(rows),
               'slots_failed': len(failed), 'failed_slot_ids': failed,
               'failure_records': failures, 'per_split': per_split,
               'accepted': 0, 'status': 'raw_candidate_unaccepted'}
    L.write_json(out / 'receipt.json', receipt)
    print(json.dumps({k: receipt[k] for k in ('requests', 'slots_planned', 'rows', 'slots_failed')},
                     indent=2))
    return receipt


def retry(model, out, failed, attempts=4):
    """Re-sample specific rejected slots with a fresh seed; nothing else is touched."""
    client = L.Client()
    pin = client.pin(model)
    if L.CONFIG['expected_digests'].get(model) != pin['digest']:
        raise RuntimeError('digest differs from the pinned value')
    jobs = {j['job_id']: j for j in load_plan()}
    by_slot = {}
    for j in jobs.values():
        for s in j['variants']:
            by_slot[s['slot_id']] = (j, s)
    manifest = {'mode': 'corpus2_targeted_retry', 'model': model, 'model_digest': pin['digest'],
                'model_metadata': pin, 'retried_slots': failed,
                'options_template': L.options(True), 'batch_slots': 1,
                'runner_sha256': L.sha(Path(__file__).read_bytes())}
    out, completed = L.init_run(out, manifest)
    rows, still = [], []
    for n, (slot_id, reason) in enumerate(sorted(failed.items())):
        job, spec = by_slot[slot_id]
        rec = None
        for attempt in range(attempts):
            case_id = 'retry_%s_a%d' % (slot_id, attempt)
            req = generation_request(model, [{'job': job, 'spec': spec}], 10000 + n * 10 + attempt)
            e = completed.get(case_id) or L.execute(client, out, req, case_id, pin['digest'])
            if not e.get('valid'):
                continue
            got = {v['slot_id']: v for v in e['parsed']['variants']}.get(slot_id)
            if got is None:
                continue
            errs = slot_problems(got['request'], job, spec)
            if errs:
                continue
            try:
                state = assemble(job, spec, got['request'])
            except (ValueError, KeyError, TypeError):
                continue
            pid = 'pkt_' + L.sha((pin['digest'] + '|' + slot_id).encode())[:16]
            rec = row_record(job, spec, state, pid, model, pin['digest'], e['request_sha256'])
            rec['writer'] = {'writer_route_readback': got['writer_route_readback']}
            rec['provenance']['replaces'] = {'slot_id': slot_id, 'first_failure': reason}
            rec['provenance']['retry_attempts'] = attempt + 1
            break
        if rec is None:
            still.append(slot_id)
        else:
            rows.append(rec)
    L.dump_rows(out / 'generated_rows.jsonl', rows)
    receipt = {'model': model, 'digest': pin['digest'], 'requested': len(failed),
               'recovered': len(rows), 'still_missing': still, 'rows_by_split': dict(
                   collections.Counter(r['split'] for r in rows))}
    L.write_json(out / 'receipt.json', receipt)
    print(json.dumps(receipt, indent=2))
    return receipt


def all_generated():
    """First-pass rows plus the targeted retries, one row per slot."""
    rows = {r['id']: r for r in L.read_rows(GEN / 'generated_rows.jsonl')}
    if (RETRY / 'generated_rows.jsonl').exists():
        for r in L.read_rows(RETRY / 'generated_rows.jsonl'):
            rows[r['id']] = r
    return sorted(rows.values(), key=lambda r: r['id'])


def select_for_critique(train_sample=600, include_seeds=True):
    """Every evaluation row, a stratified training sample and the curated seeds."""
    rows = all_generated()
    evals = [r for r in rows if r['split'] in ('dev', 'test')]
    train = [r for r in rows if r['split'] == 'train']
    by_cat = collections.defaultdict(list)
    for r in train:
        by_cat[(r['category'], r['proposed_route'])].append(r)
    sample = []
    keys = sorted(by_cat)
    per = max(1, train_sample // max(1, len(keys)))
    for k in keys:
        sample.extend(sorted(by_cat[k], key=lambda r: r['id'])[:per])
    chosen = [(r, r['packet_id']) for r in evals + sample[:train_sample]]
    if include_seeds:
        for r in L.read_rows(ROOT / 'seed/seed100_ai_reviewed_candidates.jsonl'):
            chosen.append(({'id': r['id'], 'input': r['input'], 'split': 'train',
                            'family_id': r['family_id'], 'origin': 'curated_seed'},
                           'pkt_' + L.sha((L.CONFIG['verifier_candidate'] + '|seed|'
                                           + r['id']).encode())[:16]))
    chosen.sort(key=lambda x: x[1])
    return chosen


def judge(model, out, train_sample=600):
    client = L.Client()
    pin = client.pin(model)
    if L.CONFIG['expected_digests'].get(model) != pin['digest']:
        raise RuntimeError('digest differs from the pinned value')
    chosen = select_for_critique(train_sample)
    L.dump_rows(GEN / 'blind_inputs.jsonl',
                [{'packet_id': pid, 'input': r['input']} for r, pid in chosen])
    L.write_json(GEN / 'private_mapping.json', {
        'packet_id_to_candidate_id': {pid: r['id'] for r, pid in chosen},
        'candidate_data_sha256': L.sha(L.canonical(all_generated()).encode()),
        'seed_sha256': L.sha((ROOT / 'seed/seed100_ai_reviewed_candidates.jsonl').read_bytes()),
        'blind_inputs_sha256': L.sha((GEN / 'blind_inputs.jsonl').read_bytes()),
        'critic_coverage': {'rows': len(chosen),
                            'dev': sum(r['split'] == 'dev' for r, _ in chosen),
                            'test': sum(r['split'] == 'test' for r, _ in chosen),
                            'train_sample': sum(r['split'] == 'train' and not r.get('origin')
                                                for r, _ in chosen),
                            'curated_seeds': sum(bool(r.get('origin')) for r, _ in chosen)},
        'note': 'Mappings and condition fields are never sent to the critic.'})
    policy = (ROOT / 'config/routing_policy.md').read_text(encoding='utf-8')
    manifest = {'mode': 'corpus2_blind_critic', 'model': model, 'model_digest': pin['digest'],
                'model_metadata': pin,
                'inputs_sha256': L.sha((GEN / 'blind_inputs.jsonl').read_bytes()),
                'policy_sha256': L.sha(policy.encode()), 'options': L.options(),
                'labels_supplied': False, 'runner_sha256': L.sha(Path(__file__).read_bytes())}
    out, completed = L.init_run(out, manifest)
    for r in L.read_rows(GEN / 'blind_inputs.jsonl'):
        req = L.judge_request(model, r, policy)
        if r['packet_id'] in completed:
            if completed[r['packet_id']]['request_sha256'] != L.sha(L.canonical(req).encode()):
                raise RuntimeError('saved critic request differs')
            continue
        completed[r['packet_id']] = L.execute(client, out, req, r['packet_id'], pin['digest'])
    packets = [r['packet_id'] for r in L.read_rows(GEN / 'blind_inputs.jsonl')]
    valid = []
    for pid in packets:
        entry = completed[pid]
        if entry.get('valid'):
            valid.append(dict(entry['parsed'], packet_id=pid))
    L.dump_rows(out / 'judgements.jsonl', valid)
    receipt = {'model': model, 'digest': pin['digest'], 'requested': len(completed),
               'valid': len(valid), 'BASE': sum(v['route'] == 'BASE' for v in valid),
               'DEEPFAKE': sum(v['route'] == 'DEEPFAKE' for v in valid),
               'ambiguous': sum(bool(v['ambiguous']) for v in valid),
               'inputs_sha256': manifest['inputs_sha256'],
               'limits': 'A fallible opinion for inspection, not a label or a gate.'}
    L.write_json(out / 'receipt.json', receipt)
    print(json.dumps(receipt, indent=2))
    return receipt


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='action', required=True)
    g = sub.add_parser('generate')
    g.add_argument('--model', required=True)
    g.add_argument('--out', default=str(GEN))
    g.add_argument('--limit', type=int)
    r = sub.add_parser('retry')
    r.add_argument('--model', required=True)
    r.add_argument('--out', default=str(ROOT / 'runs/corpus2_retry'))
    r.add_argument('--from-receipt', default=str(GEN / 'receipt.json'))
    j = sub.add_parser('judge')
    j.add_argument('--model', required=True)
    j.add_argument('--out', default=str(REVIEW))
    j.add_argument('--train-sample', type=int, default=600)
    a = p.parse_args()
    if a.action == 'generate':
        generate(a.model, Path(a.out), a.limit)
    elif a.action == 'retry':
        failed = {f['slot_id']: f['error'] for f in json.loads(
            Path(a.from_receipt).read_text(encoding='utf-8'))['failure_records']}
        retry(a.model, Path(a.out), failed)
    else:
        judge(a.model, Path(a.out), a.train_sample)


if __name__ == '__main__':
    main()
