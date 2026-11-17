"""Dataset Batch 100 runner: code owns runtime state and fixed pair messages, Qwen writes dialogue.

Local-only orchestration for the reviewed 100-candidate batch. Stdlib only. No model is
installed or downloaded here, and no example is accepted by this code. Adapted from
reference/local_runner.py (Pilot 1): the 20-slot guard and the full-input generation format
are replaced by the contract in GENERATION_CONTRACT.md.
"""
import argparse
import collections
import copy
import datetime
import hashlib
import json
import math
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'data_plan/models.json').read_text(encoding='utf-8'))
URL = CONFIG['base_url']
MODELS = {CONFIG['generator_candidate'], CONFIG['verifier_candidate']}
PLAN_PATH = ROOT / 'config/family_plan.json'
INPUT_SCHEMA_PATH = ROOT / 'seed/input_schema.json'
GEN_DIR = ROOT / 'runs/corpus2_generation'
REVIEW_DIR = ROOT / 'runs/corpus2_review'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def read_rows(p):
    return [json.loads(s) for s in Path(p).read_text(encoding='utf-8').splitlines() if s.strip()]


def dump_rows(p, rows):
    Path(p).write_text(''.join(canonical(r) + '\n' for r in rows), encoding='utf-8')


def write_json(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    tmp.replace(p)


def append(p, obj):
    with Path(p).open('a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False, allow_nan=False) + '\n')


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def norm_text(text):
    return ' '.join(str(text).lower().split())


def gpu_snapshot():
    try:
        r = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.used,memory.total,utilization.gpu',
                            '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=10)
        return {'stdout': r.stdout.strip(), 'stderr': r.stderr.strip(), 'returncode': r.returncode,
                'measurement': 'snapshot, not peak'}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {'error': str(e)}


def check(value, s, path='$'):
    """Validate the explicit schema subset used in this pack. No general JSON Schema claim."""
    ts = s.get('type', [])
    ts = ts if isinstance(ts, list) else [ts]
    kinds = {'object': lambda: isinstance(value, dict), 'array': lambda: isinstance(value, list),
             'string': lambda: isinstance(value, str), 'boolean': lambda: type(value) is bool,
             'null': lambda: value is None,
             'number': lambda: type(value) in (int, float) and math.isfinite(value)}
    if ts and not any(kinds[t]() for t in ts):
        raise ValueError(path + ': invalid type')
    if 'enum' in s and value not in s['enum']:
        raise ValueError(path + ': invalid enum')
    if 'const' in s and value != s['const']:
        raise ValueError(path + ': wrong constant')
    if isinstance(value, dict):
        if set(s.get('required', [])) - set(value):
            raise ValueError(path + ': missing fields')
        props = s.get('properties', {})
        if s.get('additionalProperties') is False and set(value) - set(props):
            raise ValueError(path + ': extra fields')
        for k, v in value.items():
            if k in props:
                check(v, props[k], path + '.' + k)
    if isinstance(value, list):
        if not s.get('minItems', 0) <= len(value) <= s.get('maxItems', float('inf')):
            raise ValueError(path + ': wrong item count')
        if s.get('uniqueItems') and any(value[i] in value[:i] for i in range(len(value))):
            raise ValueError(path + ': repeated items')
        for i, v in enumerate(value):
            if 'items' in s:
                check(v, s['items'], path + '[%d]' % i)
    if isinstance(value, str) and len(value) < s.get('minLength', 0):
        raise ValueError(path + ': empty/short text')
    if type(value) in (int, float) and not s.get('minimum', -float('inf')) <= value <= s.get('maximum', float('inf')):
        raise ValueError(path + ': invalid range')


def input_schema():
    return json.loads(INPUT_SCHEMA_PATH.read_text(encoding='utf-8'))


def load_plan():
    """Read the authoritative plan and refuse anything outside the declared batch shape."""
    jobs = json.loads(PLAN_PATH.read_text(encoding='utf-8'))
    slots = [v for j in jobs for v in j['variants']]
    if len(jobs) != 80:
        raise RuntimeError('Plan must declare 80 families; found %d' % len(jobs))
    if len(slots) != len({v['slot_id'] for v in slots}):
        raise RuntimeError('Duplicate slot IDs in the plan')
    if len(slots) > CONFIG['maximum_raw_slots']:
        raise RuntimeError('Plan exceeds the authorised raw-slot maximum')
    if len({j['family_id'] for j in jobs}) != 80:
        raise RuntimeError('Family IDs are not unique')
    if collections.Counter(v['intended_route'] for v in slots) != {'BASE': 60, 'DEEPFAKE': 40}:
        raise RuntimeError('Plan must be desired 60 BASE / 40 DEEPFAKE')
    if set(collections.Counter(v['category'] for v in slots).values()) != {10}:
        raise RuntimeError('Plan must be 10 rows per category')
    if sum(len(j['variants']) for j in jobs if j['mode'] == 'context_pair') != 40:
        raise RuntimeError('Plan must declare 40 paired rows')
    for j in jobs:
        state = j['runtime_state']
        preview = dict(state, message=j['fixed_current_message'] or '', history=[])
        check(preview, input_schema())
        ids = [a['id'] for a in state['assets']]
        if len(ids) != len(set(ids)) or not all(ids):
            raise RuntimeError(j['job_id'] + ': empty or duplicate asset ID in plan')
        if state['active_image_id'] is not None and state['active_image_id'] not in ids:
            raise RuntimeError(j['job_id'] + ': active image is not a declared asset')
        if state['last_analysis'] is not None and not state['last_analysis']['asset_id']:
            raise RuntimeError(j['job_id'] + ': stored analysis has an empty asset ID')
        if j['mode'] == 'context_pair':
            if len(j['variants']) != 2 or j['fixed_current_message'] is None:
                raise RuntimeError(j['job_id'] + ': pair needs two variants and a code-fixed message')
            if {v['intended_route'] for v in j['variants']} != {'BASE', 'DEEPFAKE'}:
                raise RuntimeError(j['job_id'] + ': pair must be one BASE and one DEEPFAKE condition')
    return jobs


def slot_specs(jobs):
    out = {}
    for job in jobs:
        for v in job['variants']:
            out[v['slot_id']] = {'job': job, 'variant': v}
    return out


def require_scope(model, digest):
    if CONFIG.get('authorisation') != 'DATASET_BATCH_100_ONLY':
        raise RuntimeError('Wrong round scope; this runner is only for the 100-candidate batch')
    if CONFIG.get('expected_digests', {}).get(model) != digest:
        raise RuntimeError('Model digest differs from the reviewed pin; no silent substitution')
    if CONFIG.get('maximum_raw_slots') != 100:
        raise RuntimeError('Raw-slot maximum is not the authorised 100')
    load_plan()


def route_schema(pid):
    fields = {'packet_id': {'type': 'string', 'const': pid}, 'route': {'enum': ['BASE', 'DEEPFAKE']},
              'ambiguous': {'type': 'boolean'}, 'reason_code': {'type': 'string', 'minLength': 1},
              'explanation': {'type': 'string', 'minLength': 1}}
    return {'type': 'object', 'properties': fields, 'required': list(fields), 'additionalProperties': False}


def identity(tags, model):
    if model not in MODELS:
        raise ValueError('Unapproved model tag; no automatic substitution')
    found = [r for r in tags.get('models', []) if r.get('name') == model or r.get('model') == model]
    if len(found) != 1:
        raise ValueError('Expected exactly one installed model for ' + model)
    r = found[0]
    digest = r.get('digest', '')
    if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest.lower()):
        raise ValueError('Full model digest absent')
    if r.get('details', {}).get('quantization_level') != 'Q4_K_M':
        raise ValueError('Unexpected quantisation; report instead of substituting')
    expected_family = 'qwen3' if model.startswith('qwen3:') else 'gemma3'
    if r.get('details', {}).get('family') != expected_family:
        raise ValueError('Unexpected model family; do not trust the tag alone')
    return r


class Client:
    def __init__(self, transport=None):
        self.transport = transport or self.http

    def http(self, path, body=None):
        req = urllib.request.Request(URL + path, data=None if body is None else canonical(body).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=900) as r:
            return json.loads(r.read().decode('utf-8'))

    def pin(self, model):
        return identity(self.transport('/api/tags'), model)

    def assert_pin(self, model, digest):
        if self.pin(model)['digest'] != digest:
            raise RuntimeError('Model digest changed; use a new reviewed run')


def options(generation=False, index=0):
    return {'temperature': .8 if generation else 0.,
            'seed': CONFIG['qualification_seed'] + (index if generation else 0),
            'num_ctx': CONFIG['num_ctx'],
            'num_predict': CONFIG['generation_num_predict'] if generation else CONFIG['route_num_predict'],
            'top_p': .95 if generation else .9,
            'repeat_penalty': 1.05 if generation else 1.}


def parse_response(response, schema, model):
    if response.get('model') != model:
        raise ValueError('Runtime returned a different model name')
    if response.get('done') is not True:
        raise ValueError('Incomplete response')
    if response.get('done_reason') in ('length', 'max_tokens'):
        raise ValueError('Output token budget exhausted')
    data = json.loads(response['message']['content'])
    check(data, schema)
    return data


def init_run(out, manifest):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    p = out / 'run_manifest.json'
    if p.exists():
        existing = json.loads(p.read_text(encoding='utf-8'))
        if existing != manifest:
            raise RuntimeError('Resume configuration differs; preserve the old run and use a new directory')
    else:
        write_json(p, manifest)
    seen = {}
    if (out / 'events.jsonl').exists():
        for e in read_rows(out / 'events.jsonl'):
            if e['kind'] == 'finished':
                if e['case_id'] in seen:
                    raise ValueError('Multiple completed records for one case')
                seen[e['case_id']] = e
    return out, seen


def execute(client, out, request, case_id, digest):
    # No expected labels, family manifests or filesystem tools are passed to /api/chat.
    client.assert_pin(request['model'], digest)
    start = utc()
    request_sha = sha(canonical(request).encode())
    before = gpu_snapshot()
    t = time.perf_counter()
    append(out / 'events.jsonl', {'kind': 'started', 'case_id': case_id, 'started_at': start,
                                  'request_sha256': request_sha, 'request': request,
                                  'gpu_before': before, 'attempt': 1})
    response = client.transport('/api/chat', request)
    elapsed = time.perf_counter() - t
    result = {'kind': 'finished', 'case_id': case_id, 'started_at': start, 'finished_at': utc(),
              'request_sha256': request_sha, 'response': response, 'wall_seconds': elapsed,
              'gpu_after': gpu_snapshot(), 'residency': client.transport('/api/ps')}
    try:
        result['parsed'] = parse_response(response, request['format'], request['model'])
        result['valid'] = True
    except (ValueError, KeyError, TypeError) as e:
        result.update(valid=False, error=str(e))
    append(out / 'events.jsonl', result)
    client.assert_pin(request['model'], digest)
    return result


# ---------------------------------------------------------------------------
# Generation: dialogue only
# ---------------------------------------------------------------------------

def generation_payload(job):
    fixed = job['fixed_current_message']
    p = {'job_id': job['job_id'], 'family_id': job['family_id'], 'scenario': job['scenario'],
         'mode': job['mode'], 'template_lineage': job['template_lineage'],
         'runtime_state': copy.deepcopy(job['runtime_state'])}
    if fixed is not None:
        p['fixed_current_message'] = fixed
        p['current_message_rule'] = ('This current message is fixed by code. Do not output any message field; '
                                     'write the prior history only. The runtime state is also fixed by code.')
    else:
        p['current_message_rule'] = ('Write the current request text in the variant message field. The runtime '
                                     'state and asset IDs are fixed by code and must not be restated or altered.')
    if job['mode'] == 'context_pair':
        p['history_rule'] = ('Exactly two history turns: user then assistant. The last assistant turn is the one '
                             'the fixed current message replies to.')
    elif any(v['category'] == 'clarify_or_unsupported' for v in job['variants']):
        p['history_rule'] = 'Empty history []. The current request must stand alone with no prior consent.'
    else:
        p['history_rule'] = ('Zero, two or four history turns: user first, alternating, ending with an assistant '
                             'turn. No user request may be left pending at the end.')
    p['variants'] = [{k: v[k] for k in ('slot_id', 'category', 'intended_route', 'prior_intent_requirement')}
                     for v in job['variants']]
    return p


def job_schema(job):
    ids = [v['slot_id'] for v in job['variants']]
    item_props = {
        'slot_id': {'enum': ids},
        'history': {'type': 'array', 'maxItems': 4,
                    'items': {'type': 'object', 'additionalProperties': False,
                              'required': ['role', 'content'],
                              'properties': {'role': {'enum': ['user', 'assistant']},
                                             'content': {'type': 'string', 'minLength': 1}}}},
        'boundary_rationale': {'type': 'string', 'minLength': 1},
        'writer_route_readback': {'enum': ['BASE', 'DEEPFAKE']},
    }
    required = ['slot_id', 'history', 'boundary_rationale', 'writer_route_readback']
    if job['fixed_current_message'] is None:
        item_props['message'] = {'type': 'string', 'minLength': 1}
        required.append('message')
    return {'type': 'object', 'additionalProperties': False, 'required': ['variants'],
            'properties': {'variants': {'type': 'array', 'minItems': len(ids), 'maxItems': len(ids),
                                        'items': {'type': 'object', 'additionalProperties': False,
                                                  'required': required, 'properties': item_props}}}}


def generation_request(model, job, index):
    prompt = (ROOT / 'prompts/routing_policy.md').read_text(encoding='utf-8') + '\n\n' + \
             (ROOT / 'prompts/generation.md').read_text(encoding='utf-8')
    req = {'model': model,
           'messages': [{'role': 'system', 'content': prompt},
                        {'role': 'user', 'content': 'Generate this bounded job only.\n' + canonical(generation_payload(job))}],
           'format': job_schema(job), 'stream': False, 'keep_alive': '5m', 'options': options(True, index)}
    if model.startswith('qwen3:'):
        req['think'] = False
    return req


def variant_errors(v, job, spec):
    """Structural rules on the model's dialogue. Empty means the variant may be assembled."""
    errs = []
    turns = v['history']
    roles = [t['role'] for t in turns]
    if len(turns) > 4:
        errs.append('history_longer_than_four_turns')
    if roles and roles[0] != 'user':
        errs.append('history_starts_with_assistant')
    for i, r in enumerate(roles):
        if r != ('user' if i % 2 == 0 else 'assistant'):
            errs.append('history_roles_not_alternating')
            break
    if roles and roles[-1] != 'assistant':
        errs.append('history_does_not_end_with_assistant')
    if job['mode'] == 'context_pair':
        if len(turns) != 2:
            errs.append('pair_history_not_exactly_two_turns')
    else:
        if len(turns) not in (0, 2, 4):
            errs.append('single_history_not_0_2_or_4_turns')
        if spec['category'] == 'clarify_or_unsupported' and turns:
            errs.append('clarify_single_history_not_empty')
    if any(not t['content'].strip() for t in turns):
        errs.append('empty_history_content')
    fixed = job['fixed_current_message']
    msg = fixed if fixed is not None else v.get('message')
    if msg and any(t['role'] == 'user' and norm_text(t['content']) == norm_text(msg) for t in turns):
        errs.append('history_repeats_current_message')
    if v.get('message') is not None and fixed is not None:
        errs.append('model_supplied_fixed_message')
    return errs


def assert_state(job, state, spec):
    """Cross-field invariants before a state may become a raw candidate."""
    check(state, input_schema())
    declared = job['runtime_state']
    if state['assets'] != declared['assets']:
        raise ValueError('assets differ from the code-owned state')
    if state['active_image_id'] != declared['active_image_id']:
        raise ValueError('active_image_id differs from the code-owned state')
    if state['last_analysis'] != declared['last_analysis']:
        raise ValueError('last_analysis differs from the code-owned state')
    ids = [a['id'] for a in state['assets']]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate asset IDs')
    if any(not isinstance(i, str) or not i.strip() for i in ids):
        raise ValueError('empty asset ID')
    if state['active_image_id'] is not None and state['active_image_id'] not in ids:
        raise ValueError('active_image_id is not a declared asset')
    if job['fixed_current_message'] is not None and state['message'] != job['fixed_current_message']:
        raise ValueError('fixed current message was not preserved')
    if job['mode'] == 'single' and job['fixed_current_message'] is None and not state['message']:
        raise ValueError('generated current message is empty')
    return True


def assemble(job, v, spec):
    state = copy.deepcopy(job['runtime_state'])
    state = {'message': job['fixed_current_message'] if job['fixed_current_message'] is not None else v['message'],
             'history': copy.deepcopy(v['history']),
             'assets': state['assets'], 'active_image_id': state['active_image_id'],
             'last_analysis': state['last_analysis']}
    assert_state(job, state, spec)
    return state


def candidate_record(job, v, spec, state, pid, model, digest, request_sha):
    rec = {'candidate_id': 'cand_' + spec['slot_id'], 'slot_id': spec['slot_id'],
           'packet_id': pid, 'job_id': job['job_id'], 'family_id': job['family_id'],
           'scenario': job['scenario'], 'template_lineage': job['template_lineage'], 'mode': job['mode'],
           'category': spec['category'], 'intended_route': spec['intended_route'],
           'prior_intent_requirement': spec['prior_intent_requirement'],
           'message_source': 'code_fixed' if job['fixed_current_message'] is not None else 'model',
           'history_source': 'model',
           'input': state,
           'writer': {'boundary_rationale': v['boundary_rationale'],
                      'writer_route_readback': v['writer_route_readback']},
           'provenance': {'generator': model, 'generator_digest': digest,
                          'generation_request_sha256': request_sha, 'source_slot': spec['slot_id'],
                          'assembled_by': 'tools/local_runner.py', 'attempt': 1}}
    rec['status'] = 'raw_candidate_unaccepted'
    rec['human_reviewed'] = False
    rec['candidate_sha256'] = sha(canonical(rec).encode())
    return rec


def packet_id(digest, slot_id):
    return 'pkt_' + sha((digest + '|' + slot_id).encode())[:16]


def process_job(job, parsed, request_sha, model, digest):
    records, failures = [], []
    specs = {v['slot_id']: v for v in job['variants']}
    variants = parsed['variants']
    seen = collections.Counter(v['slot_id'] for v in variants)
    for sid, n in seen.items():
        if n > 1:
            failures.append({'slot_id': sid, 'job_id': job['job_id'], 'error': 'duplicate_slot_in_response'})
    for spec in job['variants']:
        hits = [v for v in variants if v['slot_id'] == spec['slot_id']]
        if len(hits) != 1:
            failures.append({'slot_id': spec['slot_id'], 'job_id': job['job_id'], 'error': 'missing_slot_in_response'})
            continue
        v = hits[0]
        spec_full = {'slot_id': spec['slot_id'], 'category': spec['category'],
                     'intended_route': spec['intended_route'],
                     'prior_intent_requirement': spec['prior_intent_requirement']}
        errs = variant_errors(v, job, spec_full)
        if errs:
            failures.append({'slot_id': spec['slot_id'], 'job_id': job['job_id'],
                             'error': ';'.join(sorted(set(errs)))})
            continue
        try:
            state = assemble(job, v, spec_full)
        except (ValueError, KeyError, TypeError) as e:
            failures.append({'slot_id': spec['slot_id'], 'job_id': job['job_id'], 'error': str(e)})
            continue
        pid = packet_id(digest, spec['slot_id'])
        records.append(candidate_record(job, v, spec_full, state, pid, model, digest, request_sha))
    return records, failures


def check_pair_structure(records, jobs):
    """Mechanical pair equality after assembly; semantic dependence is reviewed separately."""
    by_family = collections.defaultdict(list)
    for r in records:
        by_family[r['family_id']].append(r)
    findings = []
    for job in jobs:
        if job['mode'] != 'context_pair':
            continue
        rows = by_family.get(job['family_id'], [])
        entry = {'family_id': job['family_id'], 'job_id': job['job_id'], 'usable_members': len(rows),
                 'slot_ids': [r['slot_id'] for r in rows]}
        if len(rows) == 2:
            a, b = rows[0]['input'], rows[1]['input']
            v = job['runtime_state']
            entry.update(same_message=a['message'] == b['message'],
                         same_assets=a['assets'] == b['assets'],
                         same_active=a['active_image_id'] == b['active_image_id'],
                         same_last_analysis=a['last_analysis'] == b['last_analysis'],
                         message_matches_code_fixed=a['message'] == job['fixed_current_message'],
                         state_matches_code_owned=(a['assets'] == v['assets'] and
                                                   a['active_image_id'] == v['active_image_id'] and
                                                   a['last_analysis'] == v['last_analysis']),
                         history_differs=a['history'] != b['history'],
                         history_turn_counts=[len(a['history']), len(b['history'])])
            entry['mechanical_pair_ok'] = all([entry['same_message'], entry['same_assets'], entry['same_active'],
                                               entry['same_last_analysis'], entry['message_matches_code_fixed'],
                                               entry['history_differs']])
        else:
            entry['mechanical_pair_ok'] = False
            entry['failure'] = 'incomplete pair after assembly'
        findings.append(entry)
    return findings


def run_generate(model, out, client=None):
    if model != CONFIG['generator_candidate']:
        raise ValueError('Only the reviewed generator is authorised')
    client = client or Client()
    pin = client.pin(model)
    require_scope(model, pin['digest'])
    jobs = load_plan()
    manifest = {'mode': 'unaccepted_batch100_dialogue_only', 'model': model, 'model_digest': pin['digest'],
                'model_metadata': pin, 'plan_sha256': sha(PLAN_PATH.read_bytes()),
                'prompt_sha256': sha((ROOT / 'prompts/generation.md').read_bytes()),
                'policy_sha256': sha((ROOT / 'prompts/routing_policy.md').read_bytes()),
                'schema_sha256': sha(INPUT_SCHEMA_PATH.read_bytes()),
                'runner_sha256': sha(Path(__file__).read_bytes()),
                'options_template': options(True), 'seed_rule': 'qualification_seed + zero-based family-job index',
                'thinking': False, 'contract': 'GENERATION_CONTRACT.md',
                'slots_planned': sum(len(j['variants']) for j in jobs), 'jobs_planned': len(jobs)}
    out, completed = init_run(out, manifest)
    candidates, failures, raw_rows = [], [], []
    for index, job in enumerate(jobs):
        req = generation_request(model, job, index)
        req_sha = sha(canonical(req).encode())
        saved = completed.get(job['job_id'])
        if saved and saved['request_sha256'] != req_sha:
            raise RuntimeError('Saved generation request differs for ' + job['job_id'])
        e = saved or execute(client, out, req, job['job_id'], pin['digest'])
        raw_rows.append({'job_id': job['job_id'], 'valid': bool(e.get('valid')),
                         'error': e.get('error'), 'request_sha256': e['request_sha256'],
                         'content': '' if 'response' not in e else
                         e['response'].get('message', {}).get('content', '')})
        if not e.get('valid'):
            for spec in job['variants']:
                failures.append({'slot_id': spec['slot_id'], 'job_id': job['job_id'],
                                 'error': 'job_invalid: ' + str(e.get('error'))})
            continue
        recs, fails = process_job(job, e['parsed'], e['request_sha256'], model, pin['digest'])
        candidates.extend(recs)
        failures.extend(fails)
    candidates.sort(key=lambda r: r['slot_id'])
    dump_rows(out / 'assembled_candidates_private.jsonl', candidates)
    dump_rows(out / 'blind_inputs.jsonl', [{'packet_id': r['packet_id'], 'input': r['input']} for r in candidates])
    dump_rows(out / 'raw_writer_outputs.jsonl', raw_rows)
    mapping = {'packet_id_to_candidate_id': {r['packet_id']: r['candidate_id'] for r in candidates},
               'slot_id_to_packet_id': {r['slot_id']: r['packet_id'] for r in candidates},
               'candidate_data_sha256': sha((out / 'assembled_candidates_private.jsonl').read_bytes()),
               'blind_inputs_sha256': sha((out / 'blind_inputs.jsonl').read_bytes()),
               'generator_digest': pin['digest'],
               'note': 'Never include this mapping, candidate IDs, categories or routes in critic requests.'}
    write_json(out / 'private_mapping.json', mapping)
    pairs = check_pair_structure(candidates, jobs)
    write_json(out / 'pair_structure.json', pairs)
    usable_ids = {c['slot_id'] for c in candidates}
    failed_ids = sorted({f['slot_id'] for f in failures} - usable_ids)
    receipt = {'model': model, 'digest': pin['digest'], 'jobs_requested': len(jobs),
               'slots_planned': manifest['slots_planned'], 'slots_usable': len(candidates),
               'slots_failed': len(failed_ids), 'failed_slot_ids': failed_ids,
               'failure_records': len(failures), 'failures': failures,
               'complete_pairs': sum(1 for p in pairs if p['mechanical_pair_ok']),
               'pairs_planned': len(pairs),
               'semantic_validation': 'NOT_PERFORMED_BY_GENERATOR', 'accepted_training_rows': 0,
               'status': 'raw_candidate_unaccepted'}
    write_json(out / 'receipt.json', receipt)
    print('Wrote %d usable raw slots; %d failed (%d records); %d/%d mechanical pairs complete. '
          'No row is accepted.'
          % (len(candidates), len(failed_ids), len(failures), receipt['complete_pairs'], len(pairs)))


# ---------------------------------------------------------------------------
# Blind critique
# ---------------------------------------------------------------------------

def judge_request(model, record, policy):
    if set(record) - {'packet_id', 'input'}:
        raise ValueError('Do not pass candidate annotations to a judge')
    check(record['input'], input_schema())
    data = {'packet_id': record['packet_id'], 'input': record['input']}
    request = {'model': model,
               'messages': [{'role': 'system', 'content': policy},
                            {'role': 'user', 'content': 'Classify only the CURRENT task in this structured state. '
                                                        'Return the required JSON object.\n' + canonical(data)}],
               'format': route_schema(record['packet_id']), 'stream': False, 'keep_alive': '5m',
               'options': options()}
    if model.startswith('qwen3:'):
        request['think'] = False
    return request


def verify_bindings():
    """The blind packet and the candidate file must still match the private mapping."""
    mapping = json.loads((GEN_DIR / 'private_mapping.json').read_text(encoding='utf-8'))
    blind = GEN_DIR / 'blind_inputs.jsonl'
    cands = GEN_DIR / 'assembled_candidates_private.jsonl'
    if sha(blind.read_bytes()) != mapping['blind_inputs_sha256']:
        raise RuntimeError('Blind packet hash does not match the private mapping')
    if sha(cands.read_bytes()) != mapping['candidate_data_sha256']:
        raise RuntimeError('Candidate file hash does not match the private mapping')
    rows = read_rows(blind)
    recorded = read_rows(cands)
    ids = [r['packet_id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise RuntimeError('Duplicate packet IDs')
    if set(ids) != set(mapping['packet_id_to_candidate_id']):
        raise RuntimeError('Packet/candidate mapping is not a bijection')
    if {r['packet_id'] for r in recorded} != set(ids):
        raise RuntimeError('Candidate rows and blind rows are not the same set')
    for r in rows:
        if set(r) != {'packet_id', 'input'}:
            raise RuntimeError('Blind record carries fields beyond packet_id/input')
    for r in recorded:
        expect = next(x for x in rows if x['packet_id'] == r['packet_id'])
        if canonical(expect['input']) != canonical(r['input']):
            raise RuntimeError('Blind input differs from the assembled candidate state')
    return rows, recorded, mapping


def run_judge(model, out, client=None):
    client = client or Client()
    pin = client.pin(model)
    require_scope(model, pin['digest'])
    if model != CONFIG['verifier_candidate']:
        raise RuntimeError('Only Gemma reviews these assembled states')
    rows, recorded, mapping = verify_bindings()
    policy = (ROOT / 'prompts/routing_policy.md').read_text(encoding='utf-8')
    manifest = {'mode': 'blind_critic_batch100', 'model': model, 'model_digest': pin['digest'],
                'model_metadata': pin,
                'inputs_sha256': sha((GEN_DIR / 'blind_inputs.jsonl').read_bytes()),
                'candidates_sha256': mapping['candidate_data_sha256'],
                'policy_sha256': sha(policy.encode()), 'options': options(),
                'runner_sha256': sha(Path(__file__).read_bytes()),
                'thinking': 'not_requested', 'labels_supplied': False}
    out, completed = init_run(out, manifest)
    for r in rows:
        request = judge_request(model, r, policy)
        if r['packet_id'] in completed:
            if completed[r['packet_id']]['request_sha256'] != sha(canonical(request).encode()):
                raise RuntimeError('Saved request differs')
            continue
        completed[r['packet_id']] = execute(client, out, request, r['packet_id'], pin['digest'])
    ids = [r['packet_id'] for r in rows]
    valid = [completed[i]['parsed'] for i in ids if completed[i].get('valid')]
    dump_rows(out / 'judgements.jsonl', valid)
    receipt = {'model': model, 'digest': pin['digest'], 'requested': len(rows), 'valid': len(valid),
               'invalid': len(rows) - len(valid),
               'BASE': sum(v['route'] == 'BASE' for v in valid),
               'DEEPFAKE': sum(v['route'] == 'DEEPFAKE' for v in valid),
               'ambiguous': sum(v['ambiguous'] for v in valid),
               'inputs_sha256': manifest['inputs_sha256'],
               'policy_sha256': manifest['policy_sha256'],
               'limits': 'Counts are mechanical. Correctness, model quality, peak VRAM and full GPU residency '
                         'require separate review.'}
    write_json(out / 'receipt.json', receipt)
    print(json.dumps(receipt, indent=2))


# ---------------------------------------------------------------------------
# Local service helpers
# ---------------------------------------------------------------------------

def inventory(out, client=None):
    client = client or Client()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    data = {'recorded_at': utc(), 'version': client.transport('/api/version'),
            'installed': client.transport('/api/tags'), 'loaded': client.transport('/api/ps'),
            'gpu': gpu_snapshot(), 'models': {}}
    for model in sorted(MODELS):
        try:
            data['models'][model] = {'identity': client.pin(model),
                                     'show': client.transport('/api/show', {'model': model})}
        except (OSError, ValueError) as e:
            data['models'][model] = {'error': str(e)}
    write_json(out / 'inventory.json', data)
    print(json.dumps({k: data[k] for k in ('recorded_at', 'version', 'loaded', 'gpu')}, indent=2))


def unload(model, client=None):
    client = client or Client()
    client.transport('/api/generate', {'model': model, 'keep_alive': 0})
    time.sleep(2)
    ps = client.transport('/api/ps')
    loaded = [m.get('name') or m.get('model') for m in ps.get('models', [])]
    write_json(ROOT / 'runs' / ('unload_' + model.replace(':', '_') + '.json'),
               {'at': utc(), 'model': model, 'ps_after': ps, 'loaded_after': loaded,
                'gpu_after': gpu_snapshot()})
    print(json.dumps({'model': model, 'loaded_after': loaded, 'gpu': gpu_snapshot()}, indent=2))
    if loaded:
        raise RuntimeError('Models still resident after unload: ' + ', '.join(loaded))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='action', required=True)
    i = sub.add_parser('inventory')
    i.add_argument('--out', required=True)
    g = sub.add_parser('generate')
    g.add_argument('--model', required=True)
    g.add_argument('--out', required=True)
    j = sub.add_parser('judge')
    j.add_argument('--model', required=True)
    j.add_argument('--out', required=True)
    u = sub.add_parser('unload')
    u.add_argument('--model', required=True)
    a = p.parse_args()
    if a.action == 'inventory':
        inventory(a.out)
    elif a.action == 'generate':
        run_generate(a.model, a.out)
    elif a.action == 'judge':
        run_judge(a.model, a.out)
    else:
        unload(a.model)


if __name__ == '__main__':
    main()
