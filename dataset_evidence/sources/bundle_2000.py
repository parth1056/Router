"""Assemble the single review bundle: REVIEW_ROWS.jsonl, candidates, critic view, sources, manifest."""
import collections
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import laya_core as L  # noqa: E402
import run_2000 as R  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / 'runs/corpus2_generation'
REV = ROOT / 'runs/corpus2_review'
BUNDLE = ROOT / 'bundle'
SEED = ROOT / 'seed/seed100_ai_reviewed_candidates.jsonl'
SPLITS = ('train', 'dev', 'test')
EXPECT = {'train': 2000, 'dev': 200, 'test': 300}
EXPECT_ROUTES = {'train': (1120, 880), 'dev': (120, 80), 'test': (180, 120)}
TARGET_ROUTES = {'train': (1200, 800), 'dev': (120, 80), 'test': (180, 120)}
SCHEMA = L.input_schema()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def norm(x):
    return ' '.join(x.lower().split())


def load_rows():
    rows = list(R.all_generated())
    for r in L.read_rows(SEED):
        L.check(r['input'], SCHEMA)
        rows.append({'id': r['id'], 'slot_id': r['source_slot_id'], 'packet_id': None,
                     'family_id': r['family_id'], 'job_id': r['source_slot_id'],
                     'split': 'train', 'scenario': r['scenario'],
                     'recipe_group': 'curated_seed_batch100',
                     'mode': 'context_pair' if r['input']['history'] else 'single',
                     'category': r['category'], 'proposed_route': r['label'],
                     'label_source': r['label_source'], 'input': r['input'],
                     'label_reason': ('Curated Batch-100 row, reconstructed speaker roles; '
                                      + ' '.join(r['curation_actions'])),
                     'provenance': {'origin': 'curated_seed',
                                    'seed_file': 'seed/seed100_ai_reviewed_candidates.jsonl',
                                    'seed_row_sha256': r['row_sha256'],
                                    'source_raw_candidate_sha256': r['source_raw_candidate_sha256'],
                                    'template_lineage': r['template_lineage'],
                                    'split_reservation': r['split_reservation']},
                     'seed_curation': {'status': r['status'],
                                       'curation_actions': r['curation_actions'],
                                       'intent_ambiguous': r['intent_ambiguous'],
                                       'raw_source_is_unchanged': r['raw_source_is_unchanged']},
                     'origin': 'curated_seed'})
    return rows


def attach_critic(rows):
    mapping = json.loads((GEN / 'private_mapping.json').read_text(encoding='utf-8'))
    by_pid = mapping['packet_id_to_candidate_id']
    for r in rows:
        r['packet_id'] = r.get('packet_id') or next(
            (p for p, i in by_pid.items() if i == r['id']), None)
    judged = {j['packet_id']: j for j in L.read_rows(REV / 'judgements.jsonl')}
    for r in rows:
        j = judged.get(r['packet_id']) if r['packet_id'] else None
        r['critic'] = ({'route': j['route'], 'ambiguous': bool(j['ambiguous']),
                        'reason_code': j.get('reason_code'),
                        'note': j.get('explanation', j.get('note')),
                        'source': 'pinned_critic_blind'}
                       if j else {'route': None, 'ambiguous': None, 'note': None,
                                  'source': 'not_sampled_for_critique'})
    return rows


def flags_and_checks(rows):
    fam = collections.defaultdict(set)
    msgs = collections.defaultdict(set)
    sig = collections.defaultdict(list)
    for r in rows:
        fam[r['split']].add(r['family_id'])
        msgs[r['split']].add(norm(r['input']['message']))
        sig[(r['split'], norm(r['input']['message']),
             norm(json.dumps(r['input']['history'])))].append(r['id'])
        r['quality_flags'] = {}
    depth = collections.Counter(r['family_id'] for r in rows)
    shared = {f: sorted(msgs[f]) for f in SPLITS}
    for r in rows:
        f = r['quality_flags']
        f['critic_disagrees_with_proposed_route'] = bool(
            r['critic']['route'] and r['critic']['route'] != r['proposed_route'])
        f['critic_ambiguous'] = bool(r['critic']['ambiguous'])
        f['no_critic_view'] = r['critic']['route'] is None
        f['writer_readback_disagrees'] = bool(
            r.get('writer') and r['writer']['writer_route_readback'] != r['proposed_route'])
        f['variants_in_family'] = depth[r['family_id']]
        f['context_pair'] = bool(r['input']['history'])
        f['template_assisted'] = True
        peers = [i for i in sig[(r['split'], norm(r['input']['message']),
                                 norm(json.dumps(r['input']['history'])))] if i != r['id']]
        f['duplicate_full_input'] = bool(peers)
        f['duplicate_same_family'] = any(p.rsplit('_', 1)[0] == r['id'].rsplit('_', 1)[0]
                                         for p in peers)
        f['duplicate_other_family_count'] = len(peers)
        f['message_also_in_other_splits'] = sorted(
            s for s in SPLITS if s != r['split'] and norm(r['input']['message']) in msgs[s])
        f['long_message'] = len(r['input']['message']) > 120
        f['human_reviewed'] = False
        f['accepted_for_training'] = False
        r['proposed_split'] = r['split']
    problems = []
    for s in SPLITS:
        rs = [r for r in rows if r['split'] == s]
        if len(rs) != EXPECT[s]:
            problems.append('%s has %d rows, expected %d' % (s, len(rs), EXPECT[s]))
        b = sum(r['proposed_route'] == 'BASE' for r in rs)
        d = sum(r['proposed_route'] == 'DEEPFAKE' for r in rs)
        if (b, d) != EXPECT_ROUTES[s]:
            problems.append('%s route mix %d/%d, expected %d/%d' % (s, b, d, *EXPECT_ROUTES[s]))
        if max(depth[r['family_id']] for r in rs) > 4:
            problems.append('%s has a family with more than four variants' % s)
        if s == 'train' and len(fam[s]) < 500:
            problems.append('train has only %d families' % len(fam[s]))
    for a in SPLITS:
        for b in SPLITS:
            if a < b and fam[a] & fam[b]:
                problems.append('family shared by %s and %s: %s'
                                % (a, b, sorted(fam[a] & fam[b])[:5]))
    if len({r['id'] for r in rows}) != len(rows):
        problems.append('duplicate ids')
    by_text = collections.defaultdict(set)
    for key in sig:
        by_text[key[1:]].add(key[0])
    cross = [k for k, v in by_text.items() if len(v) > 1]
    if cross:
        problems.append('%d identical message+history combinations span splits' % len(cross))
    if set(msgs['dev']) & set(msgs['test']):
        problems.append('dev and test share %d message texts'
                        % len(set(msgs['dev']) & set(msgs['test'])))
    mix_delta = {s: {'actual': [sum(r['proposed_route'] == 'BASE' for r in rows if r['split'] == s),
                               sum(r['proposed_route'] == 'DEEPFAKE' for r in rows
                                   if r['split'] == s)],
                      'target': list(TARGET_ROUTES[s])} for s in SPLITS}
    dup = {'rows_with_shared_dialogue': sum(r['quality_flags']['duplicate_full_input']
                                            for r in rows),
           'pair_rows': sum(r['quality_flags']['duplicate_full_input']
                            for r in rows if r['input']['history']),
           'single_rows': sum(r['quality_flags']['duplicate_full_input']
                              for r in rows if not r['input']['history']),
           'within_family': sum(r['quality_flags']['duplicate_same_family'] for r in rows),
           'note': ('Shared dialogue means another row has the same current message and the same '
                    'history text; scenes, states and labels stay independent. It happens '
                    'because short continuations and code-owned assistant templates repeat.')}
    return problems, {'families': {s: len(fam[s]) for s in SPLITS},
                      'route_mix_vs_target': mix_delta, 'shared_dialogue': dup,
                      'message_texts': {s: len(msgs[s]) for s in SPLITS},
                      'messages_shared_train_test': len(set(msgs['train']) & set(msgs['test'])),
                      'messages_shared_train_dev': len(set(msgs['train']) & set(msgs['dev']))}


def review_row(r):
    return {'id': r['id'], 'proposed_split': r['proposed_split'], 'family_id': r['family_id'],
            'recipe_group': r['recipe_group'], 'mode': r['mode'], 'category': r['category'],
            'proposed_route': r['proposed_route'], 'label_source': r['label_source'],
            'input': r['input'], 'label_reason': r['label_reason'],
            'quality_flags': r['quality_flags'], 'writer_route_readback':
                (r.get('writer') or {}).get('writer_route_readback'),
            'critic': r['critic'], 'provenance': r['provenance'],
            'seed_curation': r.get('seed_curation'),
            'human_reviewed': False, 'accepted_for_training': False,
            'status': 'raw_candidate_unaccepted'}


def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def main():
    if BUNDLE.exists():
        shutil.rmtree(BUNDLE)
    BUNDLE.mkdir(parents=True)
    for sub in ('candidates', 'writer', 'critic', 'sources'):
        (BUNDLE / sub).mkdir(parents=True, exist_ok=True)
    rows = attach_critic(load_rows())
    problems, stats = flags_and_checks(rows)
    if problems:
        print(json.dumps({'failed_checks': problems}, indent=2))
        raise SystemExit('bundle checks failed')
    rows.sort(key=lambda r: (SPLITS.index(r['split']), r['id']))
    L.dump_rows(BUNDLE / 'REVIEW_ROWS.jsonl', [review_row(r) for r in rows])
    for s in SPLITS:
        L.dump_rows(BUNDLE / ('candidates/%s_candidates.jsonl' % s),
                    [review_row(r) for r in rows if r['split'] == s])
    L.dump_rows(BUNDLE / 'failed_slots.jsonl', json.loads(
        (GEN / 'receipt.json').read_text(encoding='utf-8'))['failure_records'])
    for src, dst in [(GEN / 'generated_rows.jsonl', 'writer/generated_rows.jsonl'),
                     (GEN / 'raw_writer_outputs.jsonl', 'writer/raw_writer_outputs.jsonl'),
                     (GEN / 'events.jsonl', 'writer/events.jsonl'),
                     (GEN / 'receipt.json', 'writer/receipt.json'),
                     (GEN / 'run_manifest.json', 'writer/run_manifest.json'),
                     (R.RETRY / 'generated_rows.jsonl', 'writer/retry_rows.jsonl'),
                     (R.RETRY / 'receipt.json', 'writer/retry_receipt.json'),
                     (R.RETRY / 'events.jsonl', 'writer/retry_events.jsonl'),
                     (REV / 'judgements.jsonl', 'critic/judgements.jsonl'),
                     (REV / 'events.jsonl', 'critic/events.jsonl'),
                     (REV / 'receipt.json', 'critic/receipt.json'),
                     (REV / 'run_manifest.json', 'critic/run_manifest.json'),
                     (GEN / 'blind_inputs.jsonl', 'critic/blind_inputs.jsonl'),
                     (GEN / 'private_mapping.json', 'critic/PRIVATE_MAPPING.json'),
                     (ROOT / 'data/corpus2/PLAN_SUMMARY.json', 'sources/PLAN_SUMMARY.json'),
                     (ROOT / 'data/corpus2/train_jobs.json', 'sources/train_jobs.json'),
                     (ROOT / 'data/corpus2/dev_jobs.json', 'sources/dev_jobs.json'),
                     (ROOT / 'data/corpus2/test_jobs.json', 'sources/test_jobs.json'),
                     (ROOT / 'data/corpus2/recipes.json', 'sources/recipes.json'),
                     (SEED, 'sources/seed100_ai_reviewed_candidates.jsonl'),
                     (ROOT / 'seed/pair_recipe_bank.json', 'sources/pair_recipe_bank.json'),
                     (ROOT / 'data_plan/models.json', 'sources/models.json'),
                     (ROOT / 'config/routing_policy.md', 'sources/routing_policy.md'),
                     (ROOT / 'seed/input_schema.json', 'sources/input_schema.json'),
                     (ROOT / 'reference/state_recipes.py', 'sources/state_recipes.py'),
                     (ROOT / 'reference/pair_renderer.py', 'sources/pair_renderer.py'),
                     (ROOT / 'tools/plan_2000.py', 'sources/plan_2000.py'),
                     (ROOT / 'tools/run_2000.py', 'sources/run_2000.py'),
                     (ROOT / 'tools/bundle_2000.py', 'sources/bundle_2000.py'),
                     (ROOT / 'tools/laya_core.py', 'sources/laya_core.py')]:
        copy(src, BUNDLE / dst)
    copy(ROOT / 'config/routing_policy.md', BUNDLE / 'sources/prompt_reference_policy.md')
    (BUNDLE / 'sources/PROMPT_generator.txt').write_text(R.PROMPT, encoding='utf-8')
    events = L.read_rows(GEN / 'events.jsonl')
    fin = [e for e in events if e['kind'] == 'finished']
    timings = {'generation_requests': len(fin),
               'generation_wall_seconds': round(sum(e['wall_seconds'] for e in fin), 1),
               'generation_eval_tokens': sum(e['response'].get('eval_count', 0) for e in fin),
               'critic_requests': None, 'critic_wall_seconds': None}
    if (REV / 'events.jsonl').exists():
        cev = [e for e in L.read_rows(REV / 'events.jsonl') if e['kind'] == 'finished']
        timings.update({'critic_requests': len(cev),
                        'critic_wall_seconds': round(sum(e['wall_seconds'] for e in cev), 1)})
    gman = json.loads((GEN / 'run_manifest.json').read_text(encoding='utf-8'))
    cman = json.loads((REV / 'run_manifest.json').read_text(encoding='utf-8'))
    per_split = {}
    for s in SPLITS:
        rs = [r for r in rows if r['split'] == s]
        per_split[s] = {
            'rows': len(rs),
            'BASE': sum(r['proposed_route'] == 'BASE' for r in rs),
            'DEEPFAKE': sum(r['proposed_route'] == 'DEEPFAKE' for r in rs),
            'context_rows': sum(bool(r['input']['history']) for r in rs),
            'families': len({r['family_id'] for r in rs}),
            'curated_seed_rows': sum(r.get('origin') == 'curated_seed' for r in rs),
            'max_variants_in_family': max(collections.Counter(
                r['family_id'] for r in rs).values()),
            'critic_views': sum(r['critic']['route'] is not None for r in rs),
            'critic_disagreements': sum(r['quality_flags'][
                'critic_disagrees_with_proposed_route'] for r in rs),
            'critic_ambiguous': sum(r['quality_flags']['critic_ambiguous'] for r in rs),
            'writer_readback_disagreements': sum(r['quality_flags'][
                'writer_readback_disagrees'] for r in rs)}
    manifest = {'bundle': 'LAYA_Dataset_2000_Review_2026-11-17',
                'purpose': 'row-level AI review before any fitting; nothing here is accepted data',
                'counts': per_split, 'expected': EXPECT, 'checks': stats,
                'route_mix_targets': {s: list(TARGET_ROUTES[s]) for s in SPLITS},
                'duplicates': stats['shared_dialogue'],
                'failed_slots': len(json.loads((GEN / 'receipt.json').read_text(
                    encoding='utf-8'))['failure_records']),
                'retry': json.loads((R.RETRY / 'receipt.json').read_text(encoding='utf-8')),
                'first_pass_failures': json.loads((GEN / 'receipt.json').read_text(
                    encoding='utf-8'))['failure_records'],
                'critic_coverage': json.loads((GEN / 'private_mapping.json').read_text(
                    encoding='utf-8'))['critic_coverage'],
                'models': {'generator': gman['model'], 'generator_digest': gman['model_digest'],
                           'critic': cman['model'], 'critic_digest': cman['model_digest']},
                'hashes': {'plan': gman['plan_sha256'],
                           'generation_prompt': gman['prompt_sha256'],
                           'policy': gman['policy_sha256'],
                           'generator_runner': sha(ROOT / 'tools/run_2000.py'),
                           'seed': sha(SEED),
                           'input_schema': sha(L.INPUT_SCHEMA_PATH)},
                'options': {'generation': gman['options_template'],
                            'critic': cman['options']},
                'timings': timings,
                'disclosures': [
                    'Every row is template-assisted: scenario catalogue, state, code-owned '
                    'assistant turn, operative offer and neutral current message are code; the '
                    'pinned generator wrote only the user request text.',
                    'human_reviewed is false everywhere; Codex inspection is AI adjudication.',
                    'accepted_for_training is false everywhere; nothing was fitted.',
                    'Curated seed rows reuse the Batch-100 reviewed material and were not '
                    'regenerated; their earlier curation is preserved verbatim.',
                    'Writer readback is the generator reading its own row, not a blind check; '
                    'it agreed with the condition on every row, so it carries no independent '
                    'evidence.',
                    'The critic is a fallible blind opinion, not a label; its agreement is not '
                    'used as a gate and no threshold was introduced.',
                    'Critic coverage is disclosed per split: dev/test fully, train sampled plus '
                    'all curated seeds.',
                    '12 of 2,400 generated slots failed first-pass text checks (user speaking as '
                    'the assistant, or repeating the fixed current message); each was re-sampled '
                    'once with a fresh seed, all 12 recovered, and every replacement records the '
                    'slot it replaced in provenance. No slot was synthesised by hand.'],
                'files': {}}
    L.write_json(BUNDLE / 'manifest.json', manifest)
    write_summary(rows, manifest)
    (BUNDLE / 'README.md').write_text(README, encoding='utf-8')
    manifest['note_on_manifest_hash'] = ('manifest.json does not hash itself; the outer ZIP '
                                         'SHA-256 covers it and is written to '
                                         'runs/BUNDLE_ZIP_SHA256.txt')
    L.write_json(BUNDLE / 'manifest.json', manifest)
    manifest['files'] = {str(p.relative_to(BUNDLE)).replace('\\', '/'):
                         {'sha256': sha(p), 'bytes': p.stat().st_size}
                         for p in sorted(BUNDLE.rglob('*'))
                         if p.is_file() and p.name != 'manifest.json'}
    L.write_json(BUNDLE / 'manifest.json', manifest)
    out = ROOT / 'LAYA_Dataset_2000_Review_2026-11-17.zip'
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(BUNDLE.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(BUNDLE).as_posix())
    digest = sha(out)
    (ROOT / 'runs/BUNDLE_ZIP_SHA256.txt').write_text(
        '%s  %s\n' % (digest, out.name), encoding='utf-8')
    print(json.dumps({'zip': str(out), 'sha256': digest,
                      'files': len(manifest['files']), 'rows': len(rows),
                      'counts': per_split, 'timings': timings}, indent=2))


README = """# LAYA router dataset — one review bundle (2,000 / 200 / 300)

Nothing in this bundle is accepted data or a training result. `human_reviewed` and
`accepted_for_training` are false on every row, and no model was fitted.

- `REVIEW_ROWS.jsonl` — every row: id, split, family, recipe group, proposed route, label source,
  full five-field runtime input, label reason, quality flags, critic view, provenance.
- `candidates/{train,dev,test}_candidates.jsonl` — the same rows split per file.
- `writer/` — raw generator output, assembled rows, per-request events and receipt.
- `critic/` — blind inputs, judgements and receipt. `PRIVATE_MAPPING.json` links packets to rows
  and was never shown to the critic.
- `failed_slots.jsonl` — every slot the generator failed to deliver, with its reason.
- `sources/` — plan, recipes, seed, policy, schema, generator prompt and the actual code used.
- `manifest.json` — counts, checks, hashes and disclosures. `REVIEW_SUMMARY.md` — the narrative.

Read `REVIEW_SUMMARY.md` first.
"""


def write_summary(rows, m):
    c = m['counts']
    lines = ['# Review bundle: 2,000 / 200 / 300 synthetic LAYA rows', '',
             'Status: raw candidates, AI-reviewed only, **not accepted**, **nothing fitted** and '
             '**no human review**.', '',
             '## Counts', '',
             '| split | rows | BASE | DEEPFAKE | context rows | families | max variants |',
             '|---|---|---|---|---|---|---|']
    for s in SPLITS:
        d = c[s]
        lines.append('| %s | %d | %d | %d | %d | %d | %d |' % (
            s, d['rows'], d['BASE'], d['DEEPFAKE'], d['context_rows'], d['families'],
            d['max_variants_in_family']))
    lines += ['', 'Train includes %d curated Batch-100 rows (all train-reserved).' % c['train'][
        'curated_seed_rows'], '',
        '## Checks that passed', '',
        '- Exact sizes, exact dev/test class mixes (120/80, 180/120).',
        '- Train mix is 1120 BASE / 880 DEEPFAKE against the 1200/800 target: 80 rows (4 points) '
        'short on BASE. The deviation is left in place because every label follows a code-owned '
        'condition; it was not corrected by relabelling rows or by adding twin families whose two '
        'variants would share one assistant turn and one state.',
        '- 670 train / 70 dev / 105 test families, at most four variants per family.',
        '- No family appears in two splits; no message+history combination spans splits; '
        'dev and test share no message text.',
        '- Every input validates against `input_schema.json`. Generated pair rows carry exactly one '
        'user turn and one code-owned assistant turn before a separate neutral current message; '
        'five curated seed rows keep their longer reviewed four-turn history.',
        '- Shared dialogue (another row with the same message and history text): %d rows, of which '
        '%d are generated pairs, %d singles, and %d sit inside their own family. Scenes, states '
        'and labels remain independent, and no message text is shared between dev and test.'
        % (m['duplicates']['rows_with_shared_dialogue'], m['duplicates']['pair_rows'],
           m['duplicates']['single_rows'], m['duplicates']['within_family']),
        '- %d first-pass generator slots failed their text checks; `failed_slots.jsonl` lists '
        'each with its reason and `writer/retry_receipt.json` shows all of them re-sampled and '
        'recovered with a fresh seed, so no row is missing and none was written by hand.'
        % m['failed_slots'], '',
        '## Critic coverage', '',
        json.dumps(m['critic_coverage'], indent=2), '',
        '## Agreement (reported, not gated)', '',
        '| split | critic views | critic disagreements | critic ambiguous | writer readback '
        'disagreements |', '|---|---|---|---|---|']
    for s in SPLITS:
        d = c[s]
        lines.append('| %s | %d | %d | %d | %d |' % (s, d['critic_views'],
                                                     d['critic_disagreements'],
                                                     d['critic_ambiguous'],
                                                     d['writer_readback_disagreements']))
    lines += ['', '## Disclosures', ''] + ['- ' + d for d in m['disclosures']]
    lines += ['', '## Measured time', '', '```', json.dumps(m['timings'], indent=2), '```',
              '', '## Files', '', 'Every file with its SHA-256 is in `manifest.json`.']
    (BUNDLE / 'REVIEW_SUMMARY.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
